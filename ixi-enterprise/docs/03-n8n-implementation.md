# n8n 구현 방안

**작성일**: 2026-05-15  
**최종 수정**: 2026-05-18 (ixi-enterprise UI 검증 결과 반영 — Guardrail/Human Approval 연결 제약, JSON Output 제약 추가)  
**전제**: KMS API 없음, n8n 자체 기능으로 RAG 파이프라인 구축

---

## 전체 아키텍처 전략

ixi-enterprise의 KMS 역할(문서 업로드 → 임베딩 → 검색)을 n8n + Qdrant(Vector DB)로 대체한다.

```
┌─────────────────────────────────────────────────────┐
│               n8n Self-hosted (Docker)               │
│                                                     │
│  워크플로 1: 문서 인제스트 (1회성 / 주기적)            │
│  PPTX → 텍스트 추출 → 청킹 → 임베딩 → Qdrant 저장   │
│                                                     │
│  워크플로 2: 채팅 RAG (실시간)                        │
│  Chat → 검색 → 포매팅 → LLM → 응답                  │
└─────────────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
  [Qdrant Docker]    [Azure OpenAI API]
  Vector Store        LLM + Embeddings
```

---

## 워크플로 1: 문서 인제스트

### 플로우 구성

```
[Webhook] POST /ingest-doc  또는  [Schedule Trigger]
     ↓ (binary: PPTX 파일)
     ↓
[Execute Command] — LibreOffice 변환
  libreoffice --headless --convert-to pdf {file}
     ↓ (PDF binary)
     ↓
[Extract From File]
  Operation: Extract Text
  Format: PDF
     ↓ text (전체 텍스트)
     ↓
[Code 노드] — 메타데이터 첨부
  { text, source: "파일명", uploaded_at: now() }
     ↓
[Recursive Character Text Splitter]
  Chunk Size: 500
  Chunk Overlap: 50
     ↓ chunks[]
     ↓
[Embeddings Azure OpenAI]
  Model: text-embedding-3-small
     ↓ vectors[]
     ↓
[Qdrant Vector Store]
  Mode: Insert
  Collection: ixi-kms
  URL: http://qdrant:6333
```

### PPTX 처리 현실적 옵션

| 방법 | 난이도 | 안정성 | 비고 |
|------|--------|--------|------|
| LibreOffice → PDF → Extract | 중간 | 높음 | Docker 사이드카 필요 |
| .txt/.md 수동 변환 후 업로드 | 낮음 | 높음 | **POC 1단계 추천** |
| Azure Document Intelligence | 낮음 | 높음 | 외부 API, 비용 발생 |
| n8n Extract From File (PPTX 직접) | 낮음 | 낮음 | PPTX 지원 불안정 |

---

## 워크플로 2: 채팅 RAG

### 플로우 구성

```
[Chat Trigger]
  public: true, mode: webhook
     ↓ chatInput
     ↓
[Qdrant Vector Store Retriever]
  Mode: Retrieve
  Collection: ixi-kms
  Top K: 5
  Query: ={{ $json.chatInput }}
     ↓ documents[]
     ↓
[Code 노드] — Document Formatter
  documents 배열 → 프롬프트용 문자열 변환
     ↓ { context, chatInput }
     ↓
[LLM Chain 또는 AI Agent]
  System Prompt:
    "당신은 문서 요약 전문 AI 어시스턴트입니다.
     아래 문서 내용을 바탕으로 사용자의 질문에 답변하세요.
     문서에 없는 내용은 추측하지 마세요.

     [참고 문서]
     {{ $json.context }}"
  Model: azure_openai:gpt-4.1-mini
     ↓ output
     ↓
[Chat Trigger 자동 응답]
```

---

## Vector Store 선택 비교

| 옵션 | 장점 | 단점 | 권장 상황 |
|------|------|------|----------|
| **Qdrant** (Docker) | 완전 로컬, 사내망 가능, 무료 | 별도 컨테이너 운영 | **사내향 운영 추천** |
| **In-Memory** | 설치 불필요 | n8n 재시작 시 데이터 소멸 | POC/테스트 전용 |
| **Supabase** | SQL+Vector 통합, 관리 편의 | 외부 SaaS | 빠른 구축이 목표일 때 |
| **Pinecone** | 관리형, 스케일 우수 | 외부 SaaS, 유료 | 대용량 문서 처리 |

**결론**: 사내향 보안 요구 + 이미 Docker 운영 중 → **Qdrant 추천**

---

## docker-compose 설정

기존 n8n docker-compose.yml에 Qdrant 서비스 추가:

```yaml
services:
  n8n:
    image: n8nio/n8n:latest
    # ... 기존 설정 ...
    environment:
      - N8N_RUNNERS_TASK_TIMEOUT=900
      - N8N_WEBHOOK_TIMEOUT=900

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

  # PPTX 변환용 (선택)
  libreoffice:
    image: linuxserver/libreoffice:latest
    ports:
      - "3001:3000"
    restart: unless-stopped

volumes:
  qdrant_data:
```

---

## 핵심 노드 JSON 스니펫

### Chat Trigger

```json
{
  "type": "@n8n/n8n-nodes-langchain.chatTrigger",
  "parameters": {
    "public": true,
    "mode": "webhook",
    "options": {}
  }
}
```

### Qdrant Vector Store Retriever

```json
{
  "type": "@n8n/n8n-nodes-langchain.vectorStoreQdrant",
  "parameters": {
    "mode": "retrieve",
    "qdrantCollection": {
      "value": "ixi-kms"
    },
    "topK": 5
  }
}
```

### Document Formatter (Code 노드)

```javascript
const docs = $input.all();
const chatInput = $('Chat Trigger').first().json.chatInput;

const context = docs
  .map((item, i) => {
    const content = item.json.pageContent || item.json.text || '';
    const source = item.json.metadata?.source || `문서 ${i + 1}`;
    return `[${source}]\n${content}`;
  })
  .join('\n\n---\n\n');

return [{
  json: {
    context,
    chatInput
  }
}];
```

### LLM Chain (요약)

```json
{
  "type": "@n8n/n8n-nodes-langchain.chainLlm",
  "parameters": {
    "promptType": "define",
    "text": "={{ $json.chatInput }}",
    "messages": {
      "messageValues": [
        {
          "type": "SystemMessagePromptTemplate",
          "message": "당신은 문서 요약 전문 AI 어시스턴트입니다.\n아래 문서 내용을 바탕으로 사용자의 질문에 답변하세요.\n문서에 없는 내용은 추측하지 마세요.\n\n[참고 문서]\n{{ $json.context }}"
        }
      ]
    }
  }
}
```

### Embeddings (Azure OpenAI)

```json
{
  "type": "@n8n/n8n-nodes-langchain.embeddingsAzureOpenAi",
  "parameters": {
    "model": "text-embedding-3-small"
  },
  "credentials": {
    "azureOpenAiApi": {
      "id": "<credential_id>",
      "name": "Azure OpenAI"
    }
  }
}
```

---

## n8n Credential 등록 필요 항목

| Credential | 유형 | 필요 정보 |
|-----------|------|----------|
| Azure OpenAI | Azure OpenAI API | Resource Name, API Key, API Version |
| Qdrant | Qdrant API | URL (`http://qdrant:6333`) |

---

## 구현 단계별 로드맵

### 1단계: POC (1~2일)
- PPT 텍스트를 수동으로 `.txt`로 변환
- **In-Memory Vector Store** 사용
- 워크플로 2(채팅 RAG)만 구현 → 동작 확인

```
목표: Chat 입력 → 문서 검색 → LLM 응답 전체 흐름 동작 확인
```

### 2단계: 안정화 (3~5일)
- **Qdrant Docker** 추가 (영구 저장)
- 워크플로 1(인제스트) 구현
- PPTX → txt 변환 자동화 또는 LibreOffice 연동

```
목표: 문서 업로드부터 채팅까지 완전 자동화
```

### 3단계: 운영화 (1주)
- 인제스트 자동화 (파일 감시 또는 주기적 스캔)
- Guardrail 추가 (PLL / Moderation)
- Human Approval 게이트 적용
- 멀티턴 대화 히스토리 관리
- Query Rewriting 추가

```
목표: ixi-enterprise 플로우와 기능적으로 동등한 수준 달성
```

> ⚠️ **ixi-enterprise 포트 제약 — 3단계 구현 시 주의사항**
>
> **Guardrail 연결 순서**:
> - PLL / Moderation Guardrail Input은 Agent / Language Model / Guardrail만 허용
> - Chat Input → Guardrail 직접 연결 불가 → `Chat Input → Language Model(패스스루) → PLL Guardrail` 순서 필수
> - PLL Guardrail 사용 시 Azure Language Service API Key 등록 필수 (미등록 시 `401 Access denied`)
>
> **Human Approval 연결**:
> - Human Approval 출력 → Chat Output 직접 연결 불가
> - `Human Approval → Language Model → Chat Output` 또는 `Human Approval → Agent → Chat Output` 경유 필수
>
> **JSON Output 제약**:
> - 플로우에 JSON Output 추가 시 Chat Output이 비활성화됨 (상호 배타적)
> - 구조화 추출(JSON Output)과 채팅 출력(Chat Output)은 동일 플로우에서 동시 사용 불가

---

## ixi-enterprise 노드 ↔ n8n 노드 최종 매핑표

| ixi 노드 | n8n 대응 노드 | 패키지 |
|----------|--------------|--------|
| Chat Input | `chatTrigger` | `@n8n/n8n-nodes-langchain` |
| Chat Output | Chat Trigger 자동응답 | built-in |
| Template Message | `Set` 노드 또는 프롬프트 직접 작성 | built-in |
| Language Model | `chainLlm` | `@n8n/n8n-nodes-langchain` |
| Agent | `agent` | `@n8n/n8n-nodes-langchain` |
| AI Router | `agent` + Switch 노드 조합 | 커스텀 구성 |
| Structured Output | `chainLlm` + JSON 파서 Code 노드 | 커스텀 구성 |
| Simple Calculator Tool | `toolCalculator` | `@n8n/n8n-nodes-langchain` |
| Web Search Tool | `toolSerpApi` / `toolWikipedia` | `@n8n/n8n-nodes-langchain` |
| Youtube Search Tool | HTTP Request → YouTube Data API | `n8n-nodes-base` |
| MCP Connection Tool | `mcpClientTool` (n8n v1.88+) | `@n8n/n8n-nodes-langchain` |
| KOSIS Statistics Tool | HTTP Request → KOSIS OpenAPI | `n8n-nodes-base` |
| API Request | `httpRequest` | `n8n-nodes-base` |
| KMS Retriever | `vectorStoreQdrant` (retrieve mode) | `@n8n/n8n-nodes-langchain` |
| Document Formatter | `Code` 노드 (JS) | built-in |
| Human Approval | `Wait` 노드 + `Form Trigger` | built-in |
| Human Choice | `Wait` 노드 + `Form Trigger` | built-in |
| Moderation Guardrail | HTTP Request → Azure Content Safety API | `n8n-nodes-base` |
| PLL Guardrail | HTTP Request → Azure PII Detection API | `n8n-nodes-base` |
