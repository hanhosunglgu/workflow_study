# 자동화 플로우 아이디어 전체 목록

**작성일**: 2026-05-15  
**최종 수정**: 2026-05-18 (01-node-catalog.md UI 검증 결과 반영 — 포트 연결 제약 기준 플로우 재구성)  
**기준**: ixi-enterprise 노드 카탈로그 (20개 노드) 조합 분석

---

## 플로우 목록 한눈에 보기

| # | 플로우명 | 카테고리 | 난이도 | 핵심 노드 | 문서 |
|---|---------|----------|--------|----------|------|
| 1-1 | 문서 Q&A 챗봇 | RAG | ⭐ | Chat + KMS + LM | [06-flow-rag.md](./06-flow-rag.md) |
| 1-2 | 문서 요약 + 구조화 추출 | RAG | ⭐⭐ | Chat + KMS + LM + Structured Output + JSON Output | [06-flow-rag.md](./06-flow-rag.md) |
| 1-3 | 멀티 KMS 비교 분석 | RAG | ⭐⭐ | Chat + KMS×2 + LM | [06-flow-rag.md](./06-flow-rag.md) |
| 2-1 | 리서치 Agent | Agent+Tool | ⭐⭐ | Agent + Web + Youtube + KOSIS | [07-flow-agent-tool.md](./07-flow-agent-tool.md) |
| 2-2 | 사내 시스템 연동 Agent | Agent+Tool | ⭐⭐ | Agent + API Request(Tool모드) | [07-flow-agent-tool.md](./07-flow-agent-tool.md) |
| 2-3 | RAG + 실시간 검색 하이브리드 | Agent+Tool | ⭐⭐⭐ | Agent + KMS + Web | [07-flow-agent-tool.md](./07-flow-agent-tool.md) |
| 3-1 | AI 자동 분류 라우터 | 라우팅 | ⭐⭐ | AI Router + 다중 경로 | [08-flow-routing.md](./08-flow-routing.md) |
| 3-2 | 사람이 경로를 선택하는 워크플로 | 라우팅 | ⭐⭐ | Human Choice + 다중 경로 | [08-flow-routing.md](./08-flow-routing.md) |
| 4-1 | 중요 문서 발송 전 승인 플로우 | Human-in-the-Loop | ⭐⭐ | LM + Human Approval + API | [09-flow-human-loop.md](./09-flow-human-loop.md) |
| 4-2 | 멀티스텝 승인 워크플로 | Human-in-the-Loop | ⭐⭐⭐ | Agent + Human Approval + Agent + Chat Output | [09-flow-human-loop.md](./09-flow-human-loop.md) |
| 5-1 | 안전한 고객 대응 챗봇 | Guardrail | ⭐⭐ | LM + PLL + Moderation + KMS | [10-flow-guardrail.md](./10-flow-guardrail.md) |
| 5-2 | 개인정보 비식별화 처리 | Guardrail | ⭐ | LM + PLL | [10-flow-guardrail.md](./10-flow-guardrail.md) |
| 6-1 | MCP 연결 통합 Agent | MCP 확장 | ⭐⭐⭐ | Agent + MCP + Web + API | [11-flow-mcp.md](./11-flow-mcp.md) |

---

## 플로우별 핵심 구성도

> ⚠️ 포트 연결 제약 (UI 검증 기준):
> - **Guardrail Input**: Agent / Language Model / PLL Guardrail / Moderation Guardrail만 연결 가능 — Chat Input 직접 연결 불가
> - **Chat Output Input**: Agent / Language Model / PLL Guardrail / Moderation Guardrail만 연결 가능
> - **Structured Output Result** (주황): JSON Output / Document Formatter만 연결 가능
> - **Document Formatter Result** (초록): Language Model / Human Approval / Human Choice / KMS Retriever만 연결 가능
> - **AI Router else / Human Choice else**: Chat Output 직접 연결 불가 — Language Model 경유 필요 (토글 OFF 기준)
> - **Tool 노드 출력** (빨간): Agent Tools 포트에만 연결 가능

### 1-1 문서 Q&A 챗봇

```
[Chat Input]
     ↓
[KMS Retriever]   ← Knowledge: 지식베이스 선택
     ↓
[Document Formatter]
     ↓
[Language Model]  ← System Prompt: "다음 문서를 참고하여 질문에 답변하세요"
                    Model: azure_openai:gpt-4.1-mini
     ↓
[Chat Output]
```

### 1-2 문서 요약 + 구조화 추출

```
[Chat Input]
     ↓
[KMS Retriever]
     ↓
[Document Formatter]
     ↓
[Language Model]     ← "아래 문서에서 핵심 정보를 추출하세요"
     ↓
[Structured Output]  ← 스키마 이름 영문만 허용 (한글/공백 불가 — Error 400)
     ↓
[JSON Output]        ← Structured Output Result(주황)는 JSON Output에만 연결 가능
```

> ⚠️ **JSON Output ↔ Chat Output 상호 배타적**: JSON Output을 추가하면 Chat Output이 비활성화됨 — 동시 사용 불가. 구조화 추출(JSON Output)과 채팅 출력(Chat Output)은 별도 플로우로 분리할 것.  
> ⚠️ **Structured Output → Document Formatter 연결 불가**: 포트 색상이 같은 주황이어도 런타임에서 `'str' object has no attribute 'page_content'` 오류 발생 — JSON Output으로만 연결할 것.

### 1-3 멀티 KMS 비교 분석

```
[Chat Input]
     ├──→ [KMS Retriever A]  ← Knowledge: 지식베이스 A
     │         ↓
     │    [Document Formatter A]
     │         ↓
     └──→ [KMS Retriever B]  ← Knowledge: 지식베이스 B
               ↓
          [Document Formatter B]
               ↓
          [Language Model]  ← "두 문서를 비교 분석하여 차이점을 정리하세요"
               ↓
          [Chat Output]
```

> ⚠️ 실제 구현 시 Chat Input에서 두 KMS로 분기는 별도 연결 검증 필요.
> Document Formatter Result(초록)는 Language Model Input에만 연결 가능.

---

### 2-1 리서치 Agent

```
[Web Search Tool]    ─┐
[Youtube Search Tool]─┤ (Tool 포트 빨간 → Agent Tools에 연결)
[KOSIS Statistics Tool]┘

[Chat Input]
     ↓
[Agent]  ← Tools: 위 3개 / Model: azure_openai:gpt-4.1-mini
            System Prompt: "사용자 요청을 분석하여 적절한 검색 도구를 선택하세요"
     ↓
[Chat Output]
```

### 2-2 사내 시스템 연동 Agent

```
[API Request]×N  ← Tool Mode ON (빨간 Tool 포트 → Agent Tools에 연결)
  각 솔루션 엔드포인트 설정

[Chat Input]
     ↓
[Agent]  ← Tools: API Request들 / Model: azure_openai:gpt-4.1-mini
            System Prompt: "사내 시스템 연동 어시스턴트"
     ↓
[Human Approval]  ← 상태 변경 시에만 (조회는 바로 Chat Output)
     ↓
[Language Model]  ← "승인된 작업을 실행하고 결과를 요약하세요"
     ↓
[Chat Output]
```

> ⚠️ Human Approval 출력은 Language Model / Agent / AI Router 등으로 연결 가능.
> Chat Output에 연결하려면 Language Model 또는 Agent를 경유해야 함.

### 2-3 RAG + 실시간 검색 하이브리드

```
[Web Search Tool] ─┐ (Tool 포트 빨간 → Agent Tools)

[Chat Input]
     ↓
[Agent]  ← Tools: Web Search Tool / Model: azure_openai:gpt-4.1-mini
            System Prompt: "먼저 사내 지식을 검색하고, 부족하면 웹 검색으로 보완하세요"
     ↓
[KMS Retriever]   ← Agent Response → KMS Query 연결
     ↓
[Document Formatter]
     ↓
[Language Model]  ← Document Formatter Result(초록) → LM Input 연결
     ↓
[Chat Output]
```

---

### 3-1 AI 자동 분류 라우터

```
[Chat Input]
     ↓
[AI Router]  ← Conditions: 업무유형별 분기 (문서검색 / 계산 / 외부조회 / 일반대화)
               Model: azure_openai:gpt-4.1-mini
     ├──[문서검색]──→ [KMS Retriever] → [Document Formatter] → [Language Model] → [Chat Output]
     ├──[계산]──────→ [Language Model] → [Chat Output]
     ├──[외부조회]──→ [API Request(일반모드)] → [Language Model] → [Chat Output]
     └──[else]──────→ [Language Model] → [Chat Output]
                      ⚠️ else는 Chat Output 직접 연결 불가 — Language Model 경유 필수
```

### 3-2 사람이 경로를 선택하는 워크플로

```
[Chat Input]
     ↓
[Human Choice]  ← Conditions: 처리방식 선택지 (문서검색 / 계산 / 일반대화)
                  else 조건 토글: OFF → Agent/LM/AI Router로 연결 가능
                               ON  → Chat Output/PLL/Moderation만 연결 가능
     ├──[문서검색]──→ [KMS Retriever] → [Document Formatter] → [Language Model] → [Chat Output]
     ├──[계산]──────→ [Language Model] → [Chat Output]
     └──[else(OFF)]─→ [Language Model] → [Chat Output]
```

---

### 4-1 중요 문서 발송 전 승인 플로우

```
[Chat Input]
     ↓
[Language Model]  ← "입력 내용을 바탕으로 발송할 문서 초안을 작성하세요"
     ↓
[Human Approval]  ← Target Message: LM 응답 연결
                    question: "위 내용으로 발송하시겠습니까?"
     ↓ (승인 시)
[API Request(일반모드)]  ← 실제 발송 API 호출
     ↓
[Language Model]  ← "발송 완료 결과를 요약하세요"
     ↓
[Chat Output]
```

### 4-2 멀티스텝 승인 워크플로

```
[Web Search Tool]      ─┐
[KOSIS Statistics Tool]─┤ Tool 포트(빨간) → Agent Tools에 연결
[Simple Calculator Tool]┘

[Chat Input]
     ↓
[Agent]  ← Tools: 위 3개 / System Prompt: "주간 시장 동향 리포트 작성 전문가"
            Model: azure_openai:gpt-4.1-mini
     ↓
[Human Approval]  ← Target Message: Agent 응답
                    question: "이 리포트를 확정하시겠습니까?"
     ↓ (승인 시)
[Agent]  ← System Prompt: "승인된 리포트를 최종 형식으로 출력하세요"
            Model: azure_openai:gpt-4.1-mini
     ↓
[Chat Output]
     
거부 시: 플로우 즉시 종료
```

> ⚠️ **한계점 — JSON Output과 Chat Output 동시 사용 불가**: 원래 Structured Output → JSON Output 분기를 병렬로 구성하려 했으나, JSON Output 추가 시 Chat Output이 비활성화됨. Chat Output only로 설계.  
> ⚠️ **Human Approval → Chat Output 직접 연결 불가**: Agent 또는 Language Model 경유 필수.

---

### 5-1 안전한 고객 대응 챗봇

```
[Chat Input]
     ↓
[Language Model]   ← ⚠️ Guardrail Input은 Chat Input 직접 연결 불가
                       Query Rewriting 역할 겸 Guardrail 진입 전처리
                       "사용자 질문을 검색에 최적화된 단어로 재작성하세요"
     ↓
[PLL Guardrail]    ← Language Model Response → PLL Input 연결 (개인정보 필터)
     ↓
[Moderation Guardrail]  ← PLL Response → Moderation Input 연결 (유해 콘텐츠 필터)
     ↓
[KMS Retriever]    ← Moderation Response → KMS Query 연결
     ↓
[Document Formatter]
     ↓
[Language Model]   ← Document Formatter Result(초록) → LM Input
                     "다음 문서를 참고하여 안전하게 답변하세요"
     ↓
[Chat Output]
```

### 5-2 개인정보 비식별화 처리

```
[Chat Input]
     ↓
[Language Model]   ← ⚠️ Guardrail Input은 Chat Input 직접 연결 불가
                       "입력 텍스트를 그대로 전달하세요" (패스스루 역할)
     ↓
[PLL Guardrail]    ← Language Model Response → PLL Input (개인정보 마스킹)
                    ⚠️ Azure Language Service API Key 등록 필수 — 미등록 시 401 오류
     ↓
[Language Model]   ← "개인정보는 이미 마스킹 처리되었습니다. 마스킹 정보를 복원하지 마세요"
     ↓
[Chat Output]
```

---

### 6-1 MCP 연결 통합 Agent

```
[MCP Connection Tool]×N  ← Stdio 또는 Streamable-HTTP 모드
  (Atlassian, Notion, GitHub, Fetch 등 MCP 서버별 설정)
  Tool 포트(빨간) → Agent Tools에 연결

[Web Search Tool]  ─┐
[API Request(Tool모드)]─┘ (빨간 Tool 포트 → Agent Tools)

[Chat Input]
     ↓
[Agent]  ← Tools: MCP×N + Web + API / Model: azure_openai:gpt-4.1-mini
            System Prompt: "연결된 모든 도구를 활용하여 사용자 요청을 처리하세요"
     ↓
[Chat Output]
```

---

## 난이도 기준

| 난이도 | 기준 | 구현 예상 시간 |
|--------|------|--------------|
| ⭐ 쉬움 | 노드 3~4개, 단일 경로 | 0.5~1일 |
| ⭐⭐ 보통 | 노드 5~7개, 분기 또는 Tool 포함 | 1~2일 |
| ⭐⭐⭐ 복잡 | 노드 8개 이상, 멀티 경로 + 조건 처리 | 3~5일 |

---

## 사내향 임팩트 Top 3

| 순위 | 플로우 | 이유 |
|------|--------|------|
| 🥇 1위 | **3-1 AI 자동 분류 라우터** | 하나의 채팅창으로 모든 업무 처리 가능. 사용자가 별도 도구 선택 불필요 |
| 🥈 2위 | **4-1 발송 전 승인 플로우** | AI 자동화 + 사람 검토 균형. 실수 방지 및 신뢰성 확보 |
| 🥉 3위 | **5-1 안전한 고객 대응 챗봇** | 사내 컴플라이언스 요건 충족 + 실용성 높음 |

---

## 노드 활용 빈도

| 노드 | 활용 플로우 수 | 비고 |
|------|-------------|------|
| Chat Input | 13/13 | 거의 모든 플로우의 진입점 |
| Chat Output | 12/13 | 대부분 플로우의 종료점 (1-2는 JSON Output only) |
| Language Model | 13/13 | 기본 LLM 처리 + Guardrail 진입 전처리(패스스루) + Human Approval 후처리 역할 |
| KMS Retriever | 5/13 | RAG 기반 플로우 |
| Document Formatter | 5/13 | KMS와 항상 쌍으로 사용 |
| Agent | 5/13 | Tool 조합 플로우 |
| API Request | 5/13 | 외부 시스템 연동 |
| Web Search Tool | 3/13 | 리서치/하이브리드 플로우 |
| PLL Guardrail | 3/13 | 안전 레이어 (LM 경유 후 연결) |
| Moderation Guardrail | 1/13 | 안전 레이어 |
| Human Approval | 2/13 | 승인 게이트 |
| Human Choice | 1/13 | 수동 분기 |
| AI Router | 1/13 | 자동 분기 |
| Structured Output | 2/13 | 구조화 데이터 추출 |
| JSON Output | 1/13 | 1-2 플로우 전용 — 플로우에 추가 시 Chat Output 비활성화됨 (상호 배타적) |
| KOSIS Statistics Tool | 1/13 | 통계 데이터 |
| Youtube Search Tool | 1/13 | 영상 검색 |
| MCP Connection Tool | 1/13 | 외부 MCP 서버 |
| Template Message | 0/13 | ⚠️ INPUT 컴포넌트로 인식되지 않아 단독 사용 불가 — Chat Input으로 대체 |
