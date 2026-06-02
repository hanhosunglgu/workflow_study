# ixi-enterprise 워크플로우 n8n 대체 구현 — 보완점 검토

**작성일**: 2026-05-15  
**최종 수정**: 2026-06-02  
**작성 목적**: ixi-enterprise로 구성된 8개 워크플로우를 n8n으로 동등하게 구현하는 방법을 검토하고, 그 과정에서 드러나는 ixi-enterprise의 보완점(포트 연결 제약, 디버깅 불가, 예외처리 수단 부재)을 분석한다. n8n이 어떤 방식으로 이를 해소하는지 비교함으로써 ixi-enterprise에 추가되어야 할 기능을 도출하는 것이 목표다.

---

## 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                  n8n Self-hosted (Docker)                    │
│  워크플로 A : 문서 인제스트                                    │
│  워크플로 1-1: 문서 Q&A 챗봇                                  │
│  워크플로 1-2: 문서 요약                                      │
│  워크플로 2-1: 리서치 Agent                                   │
│  워크플로 2-2: 사내 시스템 연동 Agent                         │
│  워크플로 3-1: AI Router 라우팅                               │
│  워크플로 3-2: Human Choice 라우팅                            │
│  워크플로 4-2: Human Approval 승인 플로우                     │
│  워크플로 6-1: MCP 통합 Agent                                 │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
  [Qdrant Docker]    [Azure OpenAI API]    [MCP Servers]
  Vector Store        LLM + Embeddings     Context7/GitHub/Atlassian
```

---

## ixi 노드 → n8n 노드 전체 대체 매핑

| ixi 노드 | n8n 대응 노드 | 패키지 | ixi 디버깅 한계 | n8n 우위 |
|----------|--------------|--------|---------------|---------|
| Chat Input | `chatTrigger` | `@n8n/n8n-nodes-langchain` | 입력값 확인 불가 | Output 탭에서 chatInput, sessionId 즉시 확인 |
| Chat Output | Chat Trigger 자동응답 | built-in | 최종 응답만 표시, 중간 과정 불투명 | 각 노드 Output에서 단계별 추적 가능 |
| Language Model | `chainLlm` | `@n8n/n8n-nodes-langchain` | LLM 호출 결과/토큰 수 확인 불가 | Output 탭에서 text, usage.tokens 확인 |
| Agent | `agent` (Tools Agent) | `@n8n/n8n-nodes-langchain` | ReAct 루프 내부 Tool 호출 과정 불투명 | Output 탭에서 중간 추론 단계 확인 가능 |
| AI Router | `chainLlm` + `Switch` 조합 | 커스텀 | 어떤 조건으로 분기했는지 확인 불가 | LLM 분류 결과를 Output 탭에서 확인 후 Switch 동작 추적 |
| Human Choice | `Wait` + `Form Trigger` | built-in | 선택 결과 확인 불가 | Wait 노드 Output에서 formData 필드 확인 |
| KMS Retriever | `vectorStoreQdrant` (retrieve) | `@n8n/n8n-nodes-langchain` | 검색된 문서 내용/점수 확인 불가 | Output 탭에서 pageContent, metadata, score 확인 |
| Document Formatter | `Code` 노드 (JS) | built-in | 포매팅 결과 확인 불가 | Output 탭에서 context 문자열 직접 확인 |
| Human Approval | `Wait` + `Form Trigger` | built-in | 승인/거절 결과 및 의견 확인 불가 | Wait 노드 Output에서 approval, comment 필드 확인 |
| Template Message | `Set` 노드 | built-in | 변수 치환 결과 확인 불가 | Output 탭에서 치환된 prompt 문자열 확인 |
| PLL Guardrail | `httpRequest` → Azure PII Detection API | `n8n-nodes-base` | 마스킹된 항목/결과 확인 불가, 실패 시 플로우 중단만 | Output 탭에서 entities, maskedText 확인. neverError로 실패 시 폴백 처리 가능 |
| Moderation Guardrail | `httpRequest` → Azure Content Safety API | `n8n-nodes-base` | 차단 이유/점수 확인 불가, 실패 시 플로우 중단만 | Output 탭에서 category, severity 확인. 조건별 분기 처리 가능 |
| Web Search Tool | `toolSerpApi` / `toolWikipedia` | `@n8n/n8n-nodes-langchain` | 검색 결과 내용 확인 불가 | Tool Output을 Agent Output 탭에서 확인 |
| Youtube Search Tool | `httpRequest` → YouTube Data API v3 | `n8n-nodes-base` | 검색 결과 확인 불가 | Output 탭에서 items[], snippet 확인 |
| KOSIS Statistics Tool | `httpRequest` → KOSIS OpenAPI | `n8n-nodes-base` | 통계 데이터 확인 불가 | Output 탭에서 raw 데이터 확인 후 파싱 |
| API Request (일반) | `httpRequest` | `n8n-nodes-base` | 응답 statusCode/body 확인 불가 | Output 탭에서 statusCode, headers, body 전체 확인 |
| API Request (Tool) | `httpRequest` Tool 모드 | `n8n-nodes-base` | Tool 호출 결과 확인 불가 | Agent Output에서 Tool 호출 결과 추적 가능 |
| MCP Connection Tool | `mcpClientTool` (n8n v1.88+) | `@n8n/n8n-nodes-langchain` | MCP 서버 응답 확인 불가 | Agent Output에서 MCP Tool 응답 추적 가능 |
| Simple Calculator | `toolCalculator` | `@n8n/n8n-nodes-langchain` | 계산 결과 확인 불가 | Agent Output에서 계산 과정/결과 확인 |

---

## 워크플로우별 노드 대체 상세

### 워크플로 A — 문서 인제스트 (KMS Retriever 사전 준비)

ixi는 KMS 지식베이스를 플랫폼 내 UI에서 파일을 업로드해 관리한다.  
n8n은 동등한 기능을 아래 파이프라인으로 직접 구성한다.

```
[Webhook / Schedule Trigger]
         │
         ▼
[Extract From File]          ← ixi KMS 파일 업로드 대체
  PDF / DOCX / TXT 텍스트 추출
         │
         ▼
[Code 노드] — 청킹 + 메타데이터
  Chunk Size: 500 / Overlap: 50
  { text, source: filename, uploaded_at }
         │
         ▼
[Embeddings Azure OpenAI]    ← ixi KMS 내부 임베딩 엔진 대체
  Model: text-embedding-3-small
         │
         ▼
[Qdrant Vector Store]        ← ixi KMS 내부 벡터 DB 대체
  Mode: Insert
  Collection: ixi-kms
```

**ixi 대비 n8n 우위:**

| 항목 | ixi KMS | n8n + Qdrant |
|------|---------|-------------|
| 청킹 결과 확인 | 불가 | Code 노드 Output 탭에서 청크 배열 직접 확인 |
| 임베딩 모델 선택 | 플랫폼 고정 | text-embedding-3-small / ada-002 / large 선택 가능 |
| 인제스트 실패 시 | 플랫폼 UI 오류만 표시 | neverError + Error Workflow로 실패 항목 추적 |
| 청크 수/소요시간 확인 | 불가 | Qdrant Insert Output에서 확인 가능 |

---

### 워크플로 1-1 — 문서 Q&A 챗봇

**ixi → n8n 노드 대체**

| ixi 노드 | n8n 노드 | 대체 시 고려사항 |
|---------|---------|--------------|
| Chat Input | `chatTrigger` | sessionId 자동 발급 — 멀티턴 세션 기본 지원 |
| KMS Retriever | `vectorStoreQdrant` (retrieve, Top K: 5) | 검색 결과 Output 탭에서 pageContent/score 확인 가능 |
| Document Formatter | `Code` 노드 | 포매팅 결과를 Output 탭에서 확인 후 프롬프트 조정 가능 |
| Language Model | `chainLlm` | System Prompt 변수로 context 삽입. Output 탭에서 text/tokens 확인 |
| Chat Output | Chat Trigger 자동응답 | 별도 노드 불필요 |

**ixi 디버깅 한계 & n8n 대응:**

```
ixi에서 막히는 상황:
  - KMS가 엉뚱한 문서를 검색해도 무슨 내용인지 확인 불가
  - LLM이 "모르겠습니다"를 반환해도 어느 단계 문제인지 추적 불가

n8n 대응:
  1. KMS Retriever Output 탭: 검색된 pageContent, score 즉시 확인
  2. Code 노드(Document Formatter) Output 탭: LLM에 전달되는 context 문자열 확인
  3. chainLlm Output 탭: 최종 text, usage.prompt_tokens 확인
```

**예외처리 구현 (ixi에서 불가능한 부분):**

```javascript
// ixi: 검색 결과 0건이면 Document Formatter에서 빈 입력 → LLM 오동작
// n8n: Code 노드에서 검색 결과 0건 조기 감지

const docs = $input.all();
if (!docs.length || !docs[0].json.pageContent) {
  return [{ json: {
    context: '',
    isEmpty: true,
    fallback: '관련 문서를 찾을 수 없습니다. 질문을 구체적으로 다시 입력해주세요.'
  }}];
}
// 이후 IF 노드: isEmpty === true → Chat Trigger 자동응답(fallback 메시지)
```

---

### 워크플로 1-2 — 문서 요약

1-1과 구조 동일. Language Model → Agent로 교체 시 차이점만 기술한다.

**ixi → n8n 노드 대체 (차이점)**

| ixi 노드 | n8n 노드 | 대체 시 고려사항 |
|---------|---------|--------------|
| Agent (Tools 미연결) | `agent` (Tools 미연결) | Tools 없이도 ReAct 동작. LLM Chain보다 오버헤드 있음 |
| Agent context 포트 | chatTrigger의 memory 자동 연결 | n8n chatTrigger는 sessionId 기반으로 대화 히스토리 자동 관리 |

**ixi 디버깅 한계 & n8n 대응:**

```
ixi에서 막히는 상황:
  - Agent가 요약을 했는데 결과가 이상해도 어떤 context가 전달됐는지 확인 불가
  - Tools 미연결인데 ReAct 루프를 돌고 있는지 LLM Chain으로 동작하는지 구분 불가

n8n 대응:
  - agent Output 탭: intermediateSteps에서 ReAct 루프 단계별 추론 과정 확인
  - 단순 요약이면 chainLlm으로 교체 → 오버헤드 제거 + Output 탭에서 토큰 확인
```

---

### 워크플로 2-1 — 리서치 Agent

**ixi → n8n 노드 대체**

| ixi 노드 | n8n 노드 | 대체 시 고려사항 |
|---------|---------|--------------|
| Chat Input | `chatTrigger` | - |
| Language Model (PLL 패스스루) | `Code` 노드 + `httpRequest` (Azure PII Detection) | ixi는 LM 패스스루 강제. n8n은 Code 노드로 직접 전처리 |
| PLL Guardrail | `httpRequest` → Azure PII Detection API | API Key 필수. neverError로 실패 시 폴백 가능 |
| Agent | `agent` (Tools Agent) | - |
| Web Search Tool | `toolSerpApi` | Agent의 tools 배열로 연결 |
| Youtube Search Tool | `httpRequest` Tool 모드 → YouTube Data API v3 | Tool 모드로 Agent에 연결 |
| KOSIS Statistics Tool | `httpRequest` Tool 모드 → KOSIS OpenAPI | Tool 모드로 Agent에 연결 |
| Chat Output | Chat Trigger 자동응답 | - |

**ixi 디버깅 한계 & n8n 대응:**

```
ixi에서 막히는 상황:
  - PLL Guardrail이 어떤 정보를 마스킹했는지 확인 불가
    → Azure API Key 미등록이면 401 오류 후 플로우 중단. 폴백 없음
  - Agent가 Web/Youtube/KOSIS 중 어떤 Tool을 왜 선택했는지 확인 불가
  - Tool 호출 결과가 빈값이어도 Agent가 계속 루프를 도는지 알 수 없음

n8n 대응:
  1. httpRequest(PII) Output 탭: entities[] 배열에서 감지된 개인정보 항목/위치 확인
  2. agent Output 탭: intermediateSteps에서 Tool 선택 이유, 호출 파라미터, 응답 전체 확인
  3. neverError: true → PII API 실패 시 원문 그대로 진행하는 폴백 Code 노드 연결 가능
```

**예외처리 구현 (ixi에서 불가능한 부분):**

```javascript
// PII API 응답 파싱 + 실패 폴백
const resp = $input.first().json;

// Azure PII API 실패 시 (neverError: true로 수신된 경우)
if (resp.statusCode >= 400) {
  // ixi: 이 시점에서 플로우 중단. n8n: 폴백으로 진행
  return [{ json: { maskedInput: $('Chat Trigger').first().json.chatInput, piiSkipped: true } }];
}

const entities = resp.results?.documents?.[0]?.entities || [];
let maskedText = $('Chat Trigger').first().json.chatInput;
const sorted = entities.sort((a, b) => b.offset - a.offset);
for (const e of sorted) {
  maskedText = maskedText.slice(0, e.offset) + `[${e.category}]` + maskedText.slice(e.offset + e.length);
}
return [{ json: { maskedInput: maskedText, piiSkipped: false, detectedEntities: entities.length } }];
```

---

### 워크플로 2-2 — 사내 시스템 연동 Agent

**ixi → n8n 노드 대체**

| ixi 노드 | n8n 노드 | 대체 시 고려사항 |
|---------|---------|--------------|
| Chat Input | `chatTrigger` | - |
| Agent | `agent` | - |
| API Request Tool (ISMS) | `httpRequest` Tool 모드 | URL, Method, Header, Timeout 파라미터 동일하게 설정 |
| Chat Output | Chat Trigger 자동응답 | - |

**ixi 디버깅 한계 & n8n 대응:**

```
ixi에서 막히는 상황:
  - ISMS API 응답이 어떤 JSON 구조인지 확인 불가 → Agent 프롬프트 조정 불가
  - API 호출이 성공했는지 실패했는지 statusCode 확인 불가
  - Connect Timeout(1000ms) 초과 시 플로우 중단, 재시도 없음

n8n 대응:
  1. httpRequest Output 탭: statusCode, headers, body 전체 구조 확인 가능
  2. fullResponse: true → statusCode 필드 Output에 포함
  3. retryOnFail: true, maxTries: 3, waitBetweenTries: 1000ms 설정
  4. neverError: true → 4xx/5xx 응답도 다음 노드(Code)에서 처리
```

**예외처리 구현 (ixi에서 불가능한 부분):**

```javascript
// ISMS API 응답 처리 + 실패 분기
const resp = $input.first().json;

if (resp.statusCode === 401) {
  return [{ json: { error: true, message: 'ISMS 인증이 만료되었습니다. 관리자에게 문의하세요.' } }];
}
if (resp.statusCode === 503 || !resp.body) {
  return [{ json: { error: true, message: 'ISMS 시스템이 응답하지 않습니다. 잠시 후 다시 시도해주세요.' } }];
}
// 정상: body 파싱 후 전달
return [{ json: { error: false, data: resp.body } }];
// 이후 IF 노드: error === true → Chat Trigger 자동응답(에러 메시지)
```

---

### 워크플로 3-1 — AI Router 라우팅

ixi의 AI Router 전용 노드를 n8n에서 `chainLlm + Switch` 조합으로 구현한다.

**ixi → n8n 노드 대체**

| ixi 노드 | n8n 노드 | 대체 시 고려사항 |
|---------|---------|--------------|
| Chat Input | `chatTrigger` | - |
| AI Router | `chainLlm` (분류기) + `Code` (파싱) + `Switch` | ixi는 전용 노드. n8n은 3개 노드로 동등 구현 |
| 경로별 KMS + LM | `vectorStoreQdrant` + `chainLlm` | 경로마다 독립 구성 |
| 경로별 Agent | `agent` | 경로마다 독립 구성 |
| Chat Output | Chat Trigger 자동응답 | - |

**ixi 디버깅 한계 & n8n 대응:**

```
ixi에서 막히는 상황:
  - AI Router가 "문서 관련 질문"으로 분류했는지 "웹 검색 질문"으로 분류했는지 확인 불가
  - 분류 오류가 발생해도 어떤 조건에 해당했는지 알 수 없음
  - else 경로가 실행됐을 때 왜 조건에 해당하지 않았는지 근거 없음

n8n 대응:
  1. chainLlm(분류기) Output 탭: LLM이 반환한 분류 결과 JSON 직접 확인
  2. Code 노드(파싱) Output 탭: 파싱된 category 값 확인
  3. Switch 노드 Output 탭: 어떤 포트로 분기됐는지 확인
  → 분류 오류 발생 시 chainLlm 프롬프트 수정 → Pin Data로 재실행 → 즉시 결과 확인
```

**예외처리 구현 (ixi에서 불가능한 부분):**

```javascript
// AI Router 역할: LLM 분류 결과 방어적 파싱
const raw = $input.first().json.text || '';
let category = 'general'; // ixi else 경로 역할 — 기본 폴백

try {
  const match = raw.match(/\{[\s\S]*\}/);
  if (match) {
    const parsed = JSON.parse(match[0]);
    category = parsed.category || 'general';
  }
} catch {
  // ixi: 파싱 실패 시 플로우 중단. n8n: general로 폴백 진행
}

const valid = ['docs_qa', 'research', 'calculation', 'internal_api', 'general'];
if (!valid.includes(category)) category = 'general';

return [{ json: { category, chatInput: $('Chat Trigger').first().json.chatInput } }];
// Switch 노드: category 값으로 분기
// fallbackOutput: true → 매칭 없으면 general 경로로 자동 진행
```

---

### 워크플로 3-2 — Human Choice 라우팅

**ixi → n8n 노드 대체**

| ixi 노드 | n8n 노드 | 대체 시 고려사항 |
|---------|---------|--------------|
| Chat Input | `chatTrigger` | - |
| Human Choice | `Wait` (Form Submission) | 사람이 폼에서 직접 경로 선택 |
| 경로별 처리 노드 | Switch + 각 경로 노드 | Human Choice와 동일하게 분기 |
| Chat Output | Chat Trigger 자동응답 | - |

**ixi 디버깅 한계 & n8n 대응:**

```
ixi에서 막히는 상황:
  - Human Choice 폼에 어떤 선택지가 표시됐는지 확인 불가
  - 사용자가 어떤 경로를 선택했는지 이력 확인 불가
  - 폼 타임아웃 처리 수단 없음 → 사용자가 응답 안 하면 플로우 영구 중단

n8n 대응:
  1. Wait 노드 Output 탭: formData.choice 값 확인
  2. 타임아웃 설정: limitWaitTime: true, 600초 후 자동 진행
  3. 타임아웃 시 Set 노드로 기본 경로(general) 자동 선택
```

---

### 워크플로 4-2 — Human Approval 승인 플로우

**ixi → n8n 노드 대체**

| ixi 노드 | n8n 노드 | 대체 시 고려사항 |
|---------|---------|--------------|
| Chat Input | `chatTrigger` | - |
| Template Message | `Set` 노드 | 변수 치환 로직을 Expression으로 직접 작성. Output 탭에서 치환 결과 즉시 확인 |
| Agent (초안 생성) | `agent` | Output 탭에서 생성된 초안 텍스트 확인 가능 |
| Human Approval | `Wait` (Form Submission) | 승인/거절 폼 + 수정 의견 필드 |
| Language Model (경유) | `Code` 노드 | ixi는 LM 경유 강제. n8n은 Code 노드로 메시지 조립 가능 — LLM 토큰 낭비 없음 |
| PLL Guardrail | `httpRequest` → Azure PII Detection | neverError + 폴백 처리 가능 |
| Chat Output | Chat Trigger 자동응답 | - |

**ixi 디버깅 한계 & n8n 대응:**

```
ixi에서 막히는 상황:
  - Template Message의 변수 치환 결과 확인 불가 (어떤 텍스트가 Agent에 전달됐는지)
  - Agent가 생성한 초안 텍스트가 Human Approval 폼에 제대로 표시됐는지 확인 불가
  - Human Approval 승인/거절 결과가 Language Model에 어떻게 전달됐는지 확인 불가
  - 승인 대기 중 사용자가 응답 안 하면 타임아웃 처리 수단 없음

n8n 대응:
  1. Set 노드 Output 탭: 치환된 prompt 문자열 즉시 확인
  2. agent Output 탭: 생성된 초안 텍스트 확인 후 System Prompt 조정
  3. Wait 노드 Output 탭: formData.approval, formData.comment 값 확인
  4. limitWaitTime: 86400초(24시간) 후 자동 만료 처리
```

**예외처리 구현 (ixi에서 불가능한 부분):**

```javascript
// Human Approval 결과 처리 + 타임아웃 분기
const formData = $input.first().json.formData || {};
const approval = formData.approval;
const comment = formData.comment || '';

// Wait 노드 타임아웃으로 formData가 비어있는 경우
if (!approval) {
  return [{ json: {
    status: 'timeout',
    message: '승인 기한(24시간)이 초과되었습니다. 담당자에게 다시 요청해주세요.'
  }}];
}

if (approval === '승인') {
  return [{ json: { status: 'approved', message: '승인되었습니다. 문서를 최종 처리합니다.', comment } }];
} else {
  return [{ json: { status: 'rejected', message: `거절되었습니다. 수정 의견: ${comment || '없음'}` } }];
}
// 이후 Switch 노드: status 값으로 approved / rejected / timeout 3경로 분기
```

---

### 워크플로 6-1 — MCP 통합 Agent

**ixi → n8n 노드 대체**

| ixi 노드 | n8n 노드 | 대체 시 고려사항 |
|---------|---------|--------------|
| Chat Input | `chatTrigger` | - |
| Agent | `agent` | - |
| MCP Connection Tool (Context7) | `mcpClientTool` (Stdio, npx -y @upstash/context7-mcp) | n8n v1.88+ 필요 |
| MCP Connection Tool (GitHub) | `mcpClientTool` (Stdio, npx -y @modelcontextprotocol/server-github) | GITHUB_PERSONAL_ACCESS_TOKEN 환경변수 필요 |
| MCP Connection Tool (Atlassian) | `mcpClientTool` (Stdio, npx -y @modelcontextprotocol/server-atlassian) | JIRA_URL / JIRA_USERNAME / JIRA_API_TOKEN 환경변수 필요 |
| Chat Output | Chat Trigger 자동응답 | - |

**ixi 디버깅 한계 & n8n 대응:**

```
ixi에서 막히는 상황:
  - MCP 서버가 제공하는 Tool 목록이 어떤 것들인지 확인 불가
  - Agent가 Context7 / GitHub / Atlassian 중 어떤 MCP를 왜 호출했는지 확인 불가
  - MCP 서버 응답이 어떤 데이터 구조로 왔는지 확인 불가 → Agent 프롬프트 조정 불가
  - MCP 서버 프로세스 기동 실패 시 오류 내용 확인 불가

n8n 대응:
  1. mcpClientTool의 Tool List 새로고침 버튼: 서버가 제공하는 Tool 목록 즉시 확인
  2. agent Output 탭: intermediateSteps에서 MCP Tool 호출 파라미터, 응답 데이터 전체 확인
  3. agent 노드 On Error → Error Workflow: MCP 기동 실패 시 Teams 알림 + 에러 로그
```

**예외처리 구현 (ixi에서 불가능한 부분):**

```javascript
// Agent On Error → Error Workflow에서 MCP 실패 처리
// (ixi: MCP 실패 시 플로우 중단. n8n: 에러 캐치 후 사용자 안내)

const error = $input.first().json.error?.message || '';

let userMessage = '요청 처리 중 오류가 발생했습니다.';
if (error.includes('ENOENT') || error.includes('npx')) {
  userMessage = 'MCP 서버를 시작할 수 없습니다. 서버 설정을 확인해주세요.';
} else if (error.includes('401') || error.includes('Unauthorized')) {
  userMessage = 'MCP 서버 인증이 만료되었습니다. API 토큰을 갱신해주세요.';
} else if (error.includes('429') || error.includes('rate limit')) {
  userMessage = '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.';
}
return [{ json: { fallbackMessage: userMessage } }];
```

---

## ixi 제약 & n8n 대체 종합 비교

### 포트 연결 제약

| ixi 제약 | 개발 영향 | n8n 구현 방법 |
|---------|---------|------------|
| Chat Input → Guardrail 직접 연결 불가 | LM 패스스루 강제 (불필요한 토큰 낭비) | Code 노드 전처리 후 httpRequest(PII API) 직결 |
| Human Approval → Chat Output 직접 연결 불가 | 승인 결과에도 LLM 호출 강제 | Wait → Code(메시지 조립) → Chat Trigger 자동응답 |
| AI Router else → Chat Output 직접 연결 불가 | 단순 안내 메시지에도 LLM 호출 강제 | Switch default → Set → Chat Trigger 자동응답 |
| Tool 노드 → Agent에만 연결 가능 | LLM Chain + Tool 조합 불가, Agent 오버헤드 강제 | httpRequest(일반 노드)로 Tool 기능 대체 후 chainLlm에 연결 |
| JSON Output ↔ Chat Output 상호 배타 | JSON 추출 + 자연어 응답 동시 불가 | n8n 분기로 두 출력 동시 처리 |
| Structured Output → Document Formatter 런타임 오류 | UI 연결은 되지만 실행 시 타입 오류 | Code 노드로 LangChain Document 형식 직접 생성 |
| Template Message 단독 플로우 시작 불가 | 배치/스케줄 자동화 불가 | Schedule Trigger + Set 노드 |
| 플로우 간 데이터 연계 없음 | 복잡한 플로우 단일 캔버스 집중, 재사용 불가 | Execute Workflow 노드로 Sub-workflow 호출 |

### 디버깅 & 예외처리 구조 비교

| 항목 | ixi-enterprise | n8n |
|------|--------------|-----|
| 노드 실행 후 데이터 확인 | ❌ 불가 — 블랙박스 | ✅ INPUT / OUTPUT 탭에서 JSON 즉시 확인 |
| 특정 노드만 재실행 | ❌ 불가 — 플로우 전체 재실행 | ✅ Pin Data + Test Step으로 단일 노드 반복 테스트 |
| 오류 발생 위치 추적 | ❌ 불가 — 어느 노드인지 모름 | ✅ 오류 노드 하이라이트 + 스택 트레이스 |
| 노드별 재시도 설정 | ❌ 없음 | ✅ retryOnFail: 횟수/간격 설정 |
| API 실패 시 폴백 처리 | ❌ 플로우 즉시 중단 | ✅ neverError + IF 노드 + 폴백 경로 |
| 타임아웃 설정 | ❌ 없음 | ✅ 노드별 timeout(ms) 설정 |
| 승인 대기 만료 처리 | ❌ 영구 중단 | ✅ Wait 노드 limitWaitTime + 만료 경로 분기 |
| 전역 에러 알림 | ❌ 없음 | ✅ Error Workflow → Teams/Slack 알림 |
| 노드 간 데이터 스키마 파악 | ❌ 문서 없음, 실행해봐야 확인 | ✅ Output 탭 자동완성으로 필드 탐색 |

---

## ixi의 구조적 한계 — 디버깅 불가 & 예외처리 방어 수단 없음

ixi-enterprise가 가진 근본적인 두 가지 한계를 정리한다.  
이 한계들은 단순 기능 부재가 아니라 **복잡한 플로우를 운영 수준으로 개발하기 어렵게 만드는 구조적 문제**다.

---

### 한계 1 — 노드별 Input/Output 데이터 확인 불가

ixi는 플로우를 실행한 후 각 노드에서 어떤 데이터가 들어오고 나갔는지 확인할 수 없다.  
노드를 클릭하면 파라미터 설정 패널만 열릴 뿐, 실제 실행 중의 데이터 스냅샷은 노출되지 않는다.

**이로 인해 막히는 상황들:**

| 상황 | ixi에서의 문제 |
|------|-------------|
| KMS가 어떤 문서를 몇 개 검색했는지 확인 | Documents 포트 출력값 확인 불가 |
| Document Formatter가 텍스트를 어떻게 합쳤는지 확인 | Result 포트 출력값 확인 불가 |
| Agent가 Tool을 몇 번 호출했고 어떤 결과를 받았는지 확인 | ReAct 내부 루프 과정 블랙박스 |
| PLL Guardrail이 어떤 정보를 마스킹했는지 확인 | Response 포트 마스킹 결과 확인 불가 |
| AI Router가 어떤 조건으로 분기 판단했는지 확인 | 분기 근거 확인 불가 |
| LLM이 빈 응답을 반환하거나 오류가 난 위치 특정 | 어느 노드인지 추적 불가 |
| 플로우 전체가 실패했을 때 원인 노드 파악 | 전체 재실행 → 결과 비교만 가능 |

**n8n의 차이:**

n8n은 모든 노드 실행 후 INPUT / OUTPUT 탭에서 실제 JSON 데이터를 직접 확인한다.

```
n8n 캔버스에서 KMS Retriever 노드 클릭 시:

  ┌─ INPUT ──────────────────────┐   ┌─ OUTPUT ──────────────────────────────┐
  │ {                            │   │ [                                     │
  │   "chatInput": "연차 규정"    │   │   {                                   │
  │ }                            │   │     "pageContent": "제5조 연차...",    │
  └──────────────────────────────┘   │     "metadata": { "source": "사규.pdf" },│
                                     │     "score": 0.91                     │
                                     │   },                                  │
                                     │   { ... }                             │
                                     │ ]                                     │
                                     └───────────────────────────────────────┘
```

- `Pin Data`: 노드 출력을 고정해 하위 노드만 반복 테스트 → LLM 토큰 낭비 없이 이터레이션
- `Test Step`: 단일 노드만 독립 실행해 결과 즉시 확인
- 표현식 에디터에서 이전 노드 출력 필드를 자동완성으로 탐색하며 파라미터 작성:
  ```
  ={{ $('KMS Retriever').item.json.pageContent }}
  ```

---

### 한계 2 — 예외처리 방어 수단 없음

ixi는 노드 실행이 실패하면 플로우 전체가 즉시 중단된다.  
개별 노드에 재시도, 폴백, 에러 분기, 타임아웃 설정 등을 지정하는 수단이 없다.

**이로 인해 막히는 상황들:**

| 상황 | ixi에서의 결과 |
|------|-------------|
| KMS 검색 결과가 0건인 경우 | Document Formatter에서 빈 입력 → LLM이 엉뚱한 응답 또는 오류 |
| LLM 호출이 타임아웃되거나 Azure 할당량 초과 | 플로우 전체 중단, 사용자에게 아무 응답 없음 |
| PLL Guardrail Azure API Key 미등록 | `401 Access denied` 오류 후 즉시 중단 (마스킹 없이 진행하는 폴백 불가) |
| ISMS/EMS API 서버 다운 | 플로우 중단, 재시도 없음 |
| AI Router가 정의된 조건 외의 입력을 받을 경우 | else 경로가 없거나 LLM 판단 실패 시 중단 |
| Human Approval 승인 대기 중 세션 만료 | 만료 처리 로직 없음, 플로우 영구 중단 |
| Structured Output이 JSON 파싱 실패 | 오류 후 즉시 중단, 폴백 응답 불가 |

**n8n의 차이:**

n8n은 노드마다 예외처리를 세밀하게 제어한다.

```
각 HTTP Request 노드 설정에서:
  - Retry on Fail: ON (3회, 간격 1000ms)
  - On Error: Continue (다음 노드로 진행)
  - neverError: true (4xx/5xx도 Output으로 전달)
  - timeout: 10000ms (무한 대기 방지)

각 분기점에 IF 노드 추가:
  - KMS 검색 결과 0건 → "관련 문서를 찾을 수 없습니다" 즉시 반환
  - LLM 응답 비어있음 → 폴백 메시지 반환
  - API statusCode >= 400 → 에러 메시지 분기 처리

전체 워크플로에 Error Workflow 연결:
  - 어떤 노드에서든 처리 불가 오류 발생 시 Teams/Slack 알림
```

---

### 한계 3 — 플로우 분리 및 재사용 구조 없음

ixi는 모든 노드를 하나의 플로우 캔버스 안에서만 구성할 수 있다.  
플로우가 복잡해질수록 단일 캔버스에 노드가 집중되고, 공통 로직을 별도로 분리하거나 다른 플로우에서 재사용하는 수단이 없다.

**이로 인해 막히는 상황들:**

| 상황 | ixi에서의 결과 |
|------|-------------|
| PII 필터 + KMS 검색 조합을 여러 플로우에서 공통으로 쓰고 싶을 때 | 플로우마다 동일한 노드 패턴을 중복 구성해야 함 |
| 복잡한 플로우를 역할 단위로 나눠 개발하고 싶을 때 | 단일 캔버스에 모든 노드가 집중 — 유지보수 어려움 |
| 특정 구간(예: KMS 검색 ~ LLM 호출)만 독립적으로 테스트하고 싶을 때 | 플로우 전체를 처음부터 실행해야 해당 구간 도달 가능 |
| 승인 플로우, 리서치 Agent 등을 독립 단위로 관리하고 싶을 때 | 단일 플로우 내에서만 관리 — 변경 시 전체에 영향 |

**n8n의 차이:**

n8n은 `Execute Workflow` 노드로 다른 워크플로를 Sub-workflow로 호출할 수 있으며,  
`AI Agent` 노드 안에 별도 Agent를 Sub-agent로 중첩해 역할을 분리할 수 있다.  
이 구조는 WBS Agent 프로젝트에서 이미 검증된 패턴이다.

**Sub-workflow 활용 예시 (WBS Agent에서 검증)**

```
[WBS-ORK: 오케스트레이터 워크플로]
     │
     ├─ Execute Workflow → [WBS-GRC: GitHub Repo 분류기]
     ├─ Execute Workflow → [WBS-JRA: Jira Sprint 분석기]
     ├─ Execute Workflow → [WBS-DDA: 설계 문서 분석기]
     ├─ Execute Workflow → [WBS-BAK: Backend 코드 분석기]
     └─ Execute Workflow → [WBS-RPT: 리포트 발송]

→ 각 Sub-workflow는 독립적으로 개발/테스트/수정 가능
→ WBS-ORK는 결과 수렴 역할만 담당 — 단일 책임 유지
```

**ixi 워크플로우에 적용했을 때 예시**

```
[통합 리서치 플로우 — ixi 단일 캔버스 방식]
  Chat Input → PLL Guardrail → Agent(Web+Youtube+KOSIS) → Chat Output
  (PLL 로직, Agent 로직, Tool 로직이 하나의 플로우에 혼재)

[통합 리서치 플로우 — n8n Sub-workflow 분리 방식]
  Chat Trigger
       │
       ├─ Execute Workflow → [PII 필터 공통 플로우]   ← 다른 플로우에서도 재사용
       │        │ maskedInput
       ├─ Execute Workflow → [리서치 Agent 플로우]    ← 독립 테스트 가능
       │        │ researchResult
       └─ Chat Trigger 자동응답
```

**단일 워크플로에서의 디버깅 이점**

Sub-workflow로 분리하면 각 플로우를 **단독으로 실행해 디버깅**할 수 있다.

```
예: PII 필터 공통 플로우만 단독 실행

  [Manual Trigger] → [Code: 테스트 입력값 설정]
                          │ { chatInput: "홍길동 010-1234-5678" }
                          ▼
                  [HTTP Request: Azure PII API]
                          │ Output 탭에서 entities[] 확인
                          ▼
                  [Code: 마스킹 처리]
                          │ Output 탭에서 maskedInput 확인

→ 전체 플로우를 실행하지 않고도 PII 필터만 독립 검증 가능
→ 문제 발생 시 해당 Sub-workflow만 수정 후 재실행
→ 수정이 다른 플로우에 영향을 주지 않음 (변경 격리)
```

**ixi 개선 제안**

> **제안**: Sub-flow(플로우 호출) 노드 추가 — 다른 플로우를 노드처럼 삽입해 실행

공통 로직(PII 필터, KMS 검색, 승인 게이트)을 별도 플로우로 분리하고 여러 플로우에서 공유하는 구조가 가능해지면, 플로우 유지보수성과 개발 생산성이 크게 향상된다.  
특히 복잡한 엔터프라이즈 플로우를 역할 단위로 나눠 팀이 병렬로 개발할 수 있게 된다.
