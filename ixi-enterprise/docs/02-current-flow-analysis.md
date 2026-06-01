# 현재 동작 플로우 분석

**작성일**: 2026-05-15  
**최종 수정**: 2026-05-18 (노드 카탈로그 포트 검증 결과 반영 — 모델 표기 통일, context 포트 오류 수정, Tools 포트 선택/필수 오류 수정, Guardrail/Human Approval 연결 제약 반영)  
**기준**: 개발 버전 스크린샷 (2026-05-15 오후 2:24)  
**상태**: 동작 확인 (PPT → KMS RAG → 요약 플로우)

---

## 플로우 구성도

```
[Chat Input]
     │
     │ User Message
     ▼
[KMS Retriever]
  Knowledge: "국내서비 마냥" (PPT 업로드된 지식베이스)
     │
     │ Documents
     ▼
[Document Formatter]
     │
     │ Result
     ▼
[Agent]
  System Prompt: "Role: You are an AI assistant focused on Question~"
  Jailbreak Check: OFF
  Model: azure_openai:gpt-4.1-mini
  Tools: 미연결 (빨간 포트)
  context: 미연결
     │
     │ Response
     ▼
[Chat Output]
```

---

## 노드별 설정 상세

### Chat Input
- **역할**: 사용자 질문/요약 요청 수신
- **출력**: `User Message` → KMS Retriever의 Query로 연결

### KMS Retriever
- **Knowledge**: `국내서비 마냥` (사전에 PPT 파일을 KMS에 업로드한 지식베이스)
- **Query**: Chat Input의 `User Message` 직결
- **동작**: 입력 쿼리와 유사한 PPT 청크를 벡터 유사도로 검색

### Document Formatter
- **입력**: KMS Retriever의 `Documents`
- **출력**: `Result` — 검색된 문서 청크를 프롬프트 삽입 가능한 문자열로 변환

### Agent
| 파라미터 | 값 |
|---------|-----|
| Input | Document Formatter의 Result |
| Tools | **미연결** (빨간 점 포트 — 선택사항이나 현재 비어있음) |
| System Prompt | `Role: You are an AI assistant focused on Question~` |
| Jailbreak Check | OFF |
| Model | `azure_openai:gpt-4.1-mini` |

### Chat Output
- **입력**: Agent의 `Response`
- **역할**: 요약 결과를 사용자에게 표시

---

## 데이터 흐름 상세

```
1. 사용자 입력: "이 문서 요약해줘" 또는 특정 질문
      ↓
2. KMS Retriever: "이 문서 요약해줘" 로 PPT 청크 검색 (top-k 결과)
      ↓
3. Document Formatter: 검색된 청크들을 하나의 텍스트 블록으로 합산
      예) "[문서1]\n...내용...\n\n[문서2]\n...내용..."
      ↓
4. Agent: 시스템 프롬프트 + 포매팅된 문서 + 사용자 질문 → LLM 호출
      ↓
5. Chat Output: 요약 결과 출력
```

---

## 현재 플로우의 문제점 / 개선 포인트

### 문제 1: Agent에 Tools 미연결
- `Tools` 포트(빨간 점 — 선택 포트)에 아무 Tool도 연결되지 않음
- Agent는 내부적으로 Tool 호출 루프(ReAct)를 실행하는 구조
- Tool 없이 동작하지만 불필요한 오버헤드 발생
- **개선안**: 단순 요약 용도라면 `Language Model` 노드로 교체가 더 적합

### 문제 2: Query Rewriting 없음
- Chat Input의 사용자 입력 원문이 그대로 KMS 검색 쿼리로 사용
- 사용자가 "저번에 말한 거 다시 설명해줘" 같은 대화체 입력 시 검색 품질 저하
- **개선안**: KMS Retriever 앞에 `Language Model` 노드를 추가해 쿼리 재작성(Query Rewriting) 처리

### 문제 3: 멀티턴 대화 히스토리 없음
- Agent 노드에는 `Input *`과 `Tools` 포트만 존재 (별도 context 포트 없음)
- 현재 플로우에서 이전 대화 내용이 누적되지 않음
- **개선안**: Chat Input의 세션 기반 대화 히스토리 활용 또는 외부 메모리 Tool(MCP) 연결 검토

### 문제 4: 입력 안전장치 없음
- 사용자 입력이 Guardrail 없이 바로 KMS 검색 및 LLM에 전달
- 사내향이라도 PLL Guardrail(개인정보 필터) 최소 적용 권장
- **개선안**: Guardrail Input 포트는 Agent / Language Model / Guardrail만 허용 — Chat Input 직접 연결 불가. `Chat Input → Language Model(패스스루) → PLL Guardrail` 순서로 배치해야 함
- ⚠️ PLL Guardrail 사용 시 Azure Language Service API Key 등록 필수 — 미등록 시 `401 Access denied` 오류 발생

### 문제 5: 시스템 프롬프트 미완성
- 현재 확인된 프롬프트: `"Role: You are an AI assistant focused on Question~"`
- 요약 작업에 특화된 지시문이 충분히 작성되어 있지 않을 가능성
- **개선안**: 문서 요약 전용 프롬프트 작성 (포맷, 언어, 길이 지정)

---

## 모델 정보

| 항목 | 값 |
|------|-----|
| 제공자 | Azure OpenAI |
| 모델 | `azure_openai:gpt-4.1-mini` |
| 연결 방식 | Azure 엔드포인트 (사내 Azure 구독 기반) |
| 특징 | 비용 효율적, 빠른 응답 / 복잡한 멀티스텝 추론에는 한계 |

---

## 개선된 플로우 제안

### 단기 개선 (현재 플로우 유지, 문제점만 수정)

```
[Chat Input]
     ↓
[Language Model]         ← 패스스루 — Chat Input은 Guardrail에 직접 연결 불가
  System Prompt: 없음 (입력 그대로 전달)
     ↓
[PLL Guardrail]          ← 개인정보 필터 추가
                           ⚠️ Azure Language Service API Key 등록 필수
     ↓
[Language Model]         ← Query Rewriting
  System Prompt: "사용자 질문을 검색에 최적화된 단어로 재작성하세요"
     ↓
[KMS Retriever]
     ↓
[Document Formatter]
     ↓
[Language Model]         ← Agent → Language Model 교체 (Tool 불필요)
  System Prompt: "다음 문서를 한국어로 요약하세요. 핵심 내용 3가지를 bullet point로 정리하세요."
     ↓
[Chat Output]
```

### 장기 개선 (Agent 활용)

```
[Chat Input]
     ↓
[Agent]                  ← Agent는 Chat Input 직접 연결 가능
     ↓
[PLL Guardrail] → [Moderation Guardrail]   ← Agent 이후 Guardrail 배치
     ↓
[AI Router]              ← 요약 / 질의응답 / 검색 분기
                           ⚠️ AI Router Input은 Guardrail Response 연결 가능
     ├─ 요약 요청  → [KMS Retriever] → [Document Formatter] → [Language Model] → [Chat Output]
     ├─ 특정 질문  → [KMS Retriever] → [Language Model] → [Chat Output]
     └─ else(OFF) → [Language Model] → [Chat Output]
                    ⚠️ AI Router else는 Chat Output 직접 연결 불가 — Language Model 경유 필수
```

> ⚠️ **Human Approval 추가 시 주의**: Human Approval 출력은 Chat Output에 직접 연결 불가 — Agent 또는 Language Model 경유 필수.  
> 예: `[Human Approval] → [Language Model] ("승인되었습니다.") → [Chat Output]`
