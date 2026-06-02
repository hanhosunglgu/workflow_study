# 구현 워크플로우 분석

**작성일**: 2026-06-02  
**기준**: 실제 구현 스크린샷 (2026-06-02 오후)  
**상태**: 8개 워크플로우 구현 완료

---

## 구현 워크플로우 전체 목록

docs에서 제안한 플로우 카탈로그 기준으로 아래 8개를 구현했다.

| # | 플로우 ID | 플로우명 | 핵심 노드 | 참조 문서 |
|---|----------|---------|----------|---------|
| 1 | 1-1 | 문서 Q&A 챗봇 | Chat Input → KMS → Document Formatter → Language Model → Chat Output | [06-flow-rag.md](./06-flow-rag.md) |
| 2 | 1-2 | 문서 요약 | Chat Input → KMS → Document Formatter → Agent → Chat Output | [06-flow-rag.md](./06-flow-rag.md) |
| 3 | 2-1 | 리서치 Agent | Chat Input → Language Model → PLL Guardrail → Agent(Web/Youtube/KOSIS) → Chat Output | [07-flow-agent-tool.md](./07-flow-agent-tool.md) |
| 4 | 2-2 | 사내 시스템 연동 Agent | Chat Input → Agent(API Request Tool) → Chat Output | [07-flow-agent-tool.md](./07-flow-agent-tool.md) |
| 5 | 3-1 | AI Router 라우팅 | Chat Input → AI Router → 다중 경로(Agent×3 + Language Model) → Chat Output | [08-flow-routing.md](./08-flow-routing.md) |
| 6 | 3-2 | Human Choice 라우팅 | Chat Input → Human Choice → 다중 경로(KMS+LM, Agent, LM) → Chat Output | [08-flow-routing.md](./08-flow-routing.md) |
| 7 | 4-2 | Human Approval 승인 플로우 | Chat Input → Template Message → Agent → Human Approval → Language Model → PLL Guardrail → Chat Output | [09-flow-human-loop.md](./09-flow-human-loop.md) |
| 8 | 6-1 | MCP 통합 Agent | Chat Input → Agent(MCP×3: Context7/GitHub/Atlassian) → Chat Output | [11-flow-mcp.md](./11-flow-mcp.md) |

---

## 워크플로우 1 — 문서 Q&A 챗봇 (1-1)

### 구성도

```
[Chat Input]
  User Message: "이 문서 요약해줘."
     │
     ▼
[KMS Retriever]
  Knowledge: 국책과제 매뉴얼
  Query: ← Chat Input User Message
     │
     ▼ Documents
[Document Formatter]
     │
     ▼ Result
[Language Model]
  System Prompt: "아래 문서를 바탕으로 요약한 정보를 추출해줘."
  Model: azure_openai:gpt-4.1-mini
     │
     ▼ Response
[Chat Output]
```

### 노드 설정

| 노드 | 파라미터 | 값 |
|------|---------|-----|
| Chat Input | - | 기본 설정 |
| KMS Retriever | Knowledge | 국책과제 매뉴얼 |
| KMS Retriever | Query | Chat Input → User Message |
| Document Formatter | Documents | KMS Retriever → Documents |
| Language Model | Input | Document Formatter → Result |
| Language Model | System Prompt | "아래 문서를 바탕으로 요약한 정보를 추출해줘." |
| Language Model | Model | azure_openai:gpt-4.1-mini |
| Chat Output | Input | Language Model → Response |

### 특징 및 적용 패턴

- **가장 기본적인 RAG 패턴**: KMS 검색 → Document Formatter → Language Model 직선 파이프라인
- 기존 `02-current-flow-analysis.md`(2026-05-15)의 초기 플로우에서 **Agent → Language Model로 교체** 적용
  - 이전: Agent 노드 사용 (Tool 미연결, 불필요한 ReAct 오버헤드)
  - 현재: Language Model 노드로 단순화 (Tool 불필요한 요약 용도에 적합)
- KMS Knowledge가 `국내서비 마냥` → `국책과제 매뉴얼`로 변경

---

## 워크플로우 2 — 문서 요약 (1-2)

### 구성도

```
[Chat Input]
  User Message
     │
     ├────────────────────────────────────┐
     ▼                                    │
[KMS Retriever]                           │
  Knowledge: 국책과제 매뉴얼              │
     │                                    │
     ▼ Documents                          │
[Document Formatter]                      │
     │                                    │
     ▼ Result                             │
[Agent]  ◄───────────────────────────────┘
  Input: Document Formatter → Result
         + Chat Input → User Message (context)
  Tools: 미연결
  System Prompt: "# Role\nYou are an AI assistant\nfocused on Questions~"
  Jailbreak Check: OFF
  Model: azure_openai:gpt-4.1-mini
     │
     ▼ Response
[Chat Output]
```

### 노드 설정

| 노드 | 파라미터 | 값 |
|------|---------|-----|
| Chat Input | - | 기본 설정 |
| KMS Retriever | Knowledge | 국책과제 매뉴얼 |
| Document Formatter | Documents | KMS → Documents |
| Agent | Input | Document Formatter → Result |
| Agent | Tools | 미연결 (선택 포트) |
| Agent | System Prompt | "# Role\nYou are an AI assistant focused on Questions~" |
| Agent | Jailbreak Check | OFF |
| Agent | Model | azure_openai:gpt-4.1-mini |
| Chat Output | Input | Agent → Response |

### 특징 및 적용 패턴

- **1-1과의 차이**: Language Model 대신 Agent 사용 — 향후 Tool 추가 확장을 고려한 구조
- Chat Input이 KMS Retriever와 Agent 양쪽에 연결되어 원본 사용자 질문이 Agent context에도 전달됨
- Tools 포트는 현재 미연결 상태 — 필요 시 Web Search Tool 등 추가 가능

---

## 워크플로우 3 — 리서치 Agent (2-1)

### 구성도

```
[Chat Input]
  User Message
     │
     ▼
[Language Model]                   ← 패스스루 (Chat Input은 Guardrail에 직접 연결 불가)
  System Prompt: "입력 메시지, 사용자 이름 입력해주세요."
  Model: azure_openai:gpt-4.1-mini
     │
     ▼ Response
[PLL Guardrail]
  PLL Guardrail 컴포넌트
     │
     ▼ Response
[Agent]
  Input: PLL Guardrail → Response
  Tools ↓
  ├─ [Web Search Tool]    (웹 검색 도구)
  ├─ [Youtube Search Tool] (YouTube 검색 도구)
  └─ [KOSIS Statistics Tool] (KOSIS 통계 도구)
  System Prompt: "당신은 전문 리서치 어시스턴트입니다.\n사용자의 질문에 따라 웹/유튜브/통계 데이터를 검색하여 답변합니다."
  Jailbreak Check: ON
  Model: azure_openai:gpt-4.1-mini
     │
     ▼ Response
[Chat Output]
```

### 노드 설정

| 노드 | 파라미터 | 값 |
|------|---------|-----|
| Language Model (패스스루) | System Prompt | "입력 메시지, 사용자 이름 입력해주세요." |
| Language Model (패스스루) | Model | azure_openai:gpt-4.1-mini |
| PLL Guardrail | Input | Language Model → Response |
| Agent | Input | PLL Guardrail → Response |
| Agent | Tools | Web Search Tool / Youtube Search Tool / KOSIS Statistics Tool |
| Agent | Jailbreak Check | ON |
| Agent | Model | azure_openai:gpt-4.1-mini |

### 특징 및 적용 패턴

- **PLL Guardrail 패턴 적용**: `Chat Input → Language Model(패스스루) → PLL Guardrail` — Chat Input을 Guardrail에 직접 연결 불가 제약을 우회
- **3개 Tool 병렬 연결**: Web Search / Youtube Search / KOSIS Statistics — Agent가 질문 유형에 따라 적절한 Tool 선택
- Jailbreak Check **ON** — 외부 검색 포함 플로우이므로 보안 강화
- `docs/07-flow-agent-tool.md` 2-1 리서치 Agent 패턴 직접 구현

---

## 워크플로우 4 — 사내 시스템 연동 Agent (2-2)

### 구성도

```
[Chat Input]
  User Message
     │
     ▼
[Agent]
  Input: Chat Input → User Message
  Tools ↓
  └─ [API Request Tool]
       방법: GET
       URL: https://isms.lgplus.co.kr/ems/ap/assertSource/Template
       Connect Timeout: 1000ms
       Read Timeout: 3000ms
  System Prompt: "API 정보를 조회할 수 있는 에이전트입니다."
  Jailbreak Check: OFF
  Model: azure_openai:gpt-4.1-mini
     │
     ▼ Response
[Chat Output]
```

### 노드 설정

| 노드 | 파라미터 | 값 |
|------|---------|-----|
| Agent | Input | Chat Input → User Message |
| API Request Tool | 방법 | GET |
| API Request Tool | URL | `https://isms.lgplus.co.kr/ems/ap/assertSource/Template` |
| API Request Tool | Connect Timeout | 1000ms |
| API Request Tool | Read Timeout | 3000ms |
| Agent | System Prompt | "API 정보를 조회할 수 있는 에이전트입니다." |
| Agent | Jailbreak Check | OFF |
| Agent | Model | azure_openai:gpt-4.1-mini |

### 특징 및 적용 패턴

- **API Request Tool 모드**: 일반 HTTP Request가 아닌 Agent의 Tool로 등록 — Agent가 필요할 때 직접 호출
- 사내 ISMS/EMS 시스템(`lgplus.co.kr`) 연동 — 내부 API 조회 에이전트 패턴
- `docs/07-flow-agent-tool.md` 2-2 사내 시스템 연동 Agent 패턴 구현
- MCP 연결 없이 단순 REST API 연동 시 API Request Tool 활용이 가장 간단한 접근

---

## 워크플로우 5 — AI Router 라우팅 (3-1)

### 구성도

```
[Chat Input]
  User Message
     │
     ▼
[AI Router]
  Text: ← Chat Input → User Message
  Exit Condition:
  ├─ 국민건강보험 관련 질문
  ├─ 블로그/마케팅 글쓰기
  ├─ 할 일 목록 작성
  └─ else (OFF)
     │
     ├─ [경로 1] KMS 관련 →
     │    [KMS Retriever] → [Document Formatter]
     │         ↓
     │    [Language Model]  (System Prompt: 문서 기반 답변)
     │         ↓
     │
     ├─ [경로 2] 검색/리서치 →
     │    [Agent]  (Tools: Web Search 등)
     │         ↓
     │
     ├─ [경로 3] 단순 생성 →
     │    [Agent]  (System Prompt: 특화)
     │         ↓
     │
     └─ [경로 else] →
          [Agent]  (기본 응답)
               ↓
          [Chat Output]
```

### 특징 및 적용 패턴

- **AI Router 자동 분류**: 사용자 입력 내용을 LLM이 분석해 자동으로 적절한 처리 경로로 라우팅
- 각 경로마다 목적에 특화된 Agent/Language Model 배치
- `else` 경로는 Chat Output에 직접 연결 불가 — Agent/Language Model 경유 필수 (UI 검증 확인 사항)
- `docs/08-flow-routing.md` 3-1 AI 자동 분류 라우터 패턴 구현

---

## 워크플로우 6 — Human Choice 라우팅 (3-2)

### 구성도

```
[Chat Input]
  User Message
     │
     ▼
[AI Router]  또는  [Human Choice]
  Text: ← Chat Input → User Message
  Exit Condition:
  ├─ 국민건강보험 관련 질문 (Yes 조건 1)
  ├─ 할 일 목록 작성 (Yes 조건 2)
  ├─ 기타 조건
  └─ else (OFF)
     │
     ├─ [경로 1] →
     │    [KMS Retriever] → [Document Formatter]
     │         ↓
     │    [Language Model]
     │         ↓
     │
     ├─ [경로 2] →
     │    [Agent]  (Jailbreak Check: OFF, Tools 미연결)
     │         ↓
     │
     ├─ [경로 3] →
     │    [Language Model]  (단순 생성)
     │         ↓
     │
     └─ [경로 else] →
          [Agent]
               ↓
          [Chat Output]
```

### 특징 및 적용 패턴

- **조건 기반 분기 라우팅**: AI Router와 유사하나 더 명시적인 조건 설정 패턴
- 3-1과 구조적으로 유사하나 라우팅 노드 종류와 조건 표현 방식이 다름
- KMS 경로, Agent 경로, 단순 LM 경로를 모두 포함한 풀 구성
- `docs/08-flow-routing.md` 3-2 Human Choice 라우터 패턴 구현

---

## 워크플로우 7 — Human Approval 승인 플로우 (4-2)

### 구성도

```
[Chat Input]
  User Message
     │
     ▼
[Template Message]
  Template: "[{{event}}] {{Date}} 이후 발생된 보안 이벤트 및 조치 사항을 정리해주세요."
  User Message: ← Chat Input
     │
     ▼ User Message
[Agent]
  Input: Template Message → User Message
  Tools: 미연결
  System Prompt: "주간 사전 동의서 작성 전문 에이전트입니다."
  Jailbreak Check: OFF (토글)
  Model: azure_openai:gpt-4.1-mini
     │
     ▼ Response
[Human Approval]
  Target Message: question ← Agent → Response
  대기: 승인자가 검토 후 승인/거절
     │
     ▼ Human Approval
[Language Model]                   ← Human Approval은 Chat Output 직접 연결 불가 → LM 경유
  Input: Human Approval → Human Approval
  System Prompt: (없음 또는 포맷 지시)
  Model: azure_openai:gpt-4.1-mini
     │
     ▼ Response
[PLL Guardrail]
  Input: Language Model → Response
     │
     ▼ Response
[Chat Output]
```

### 노드 설정

| 노드 | 파라미터 | 값 |
|------|---------|-----|
| Template Message | Template | `[{{event}}] {{Date}} 이후 발생된 보안 이벤트 및 조치 사항을 정리해주세요.` |
| Agent | System Prompt | "주간 사전 동의서 작성 전문 에이전트입니다." |
| Agent | Jailbreak Check | OFF |
| Agent | Model | azure_openai:gpt-4.1-mini |
| Human Approval | Target Message | Agent → Response (question 포트) |
| Language Model | Input | Human Approval → Human Approval |
| Language Model | Model | azure_openai:gpt-4.1-mini |
| PLL Guardrail | Input | Language Model → Response |

### 특징 및 적용 패턴

- **Template Message 활용**: 사용자 입력을 구조화된 프롬프트 템플릿으로 변환 후 Agent에 전달
- **Human Approval 패턴**: Agent가 생성한 초안을 승인자가 검토 후 승인해야 다음 단계 진행
- **Human Approval → LM 경유 패턴 적용**: Human Approval 출력은 Chat Output에 직접 연결 불가 — `Language Model` 경유 필수 (UI 검증 확인 제약)
- 출력 전 PLL Guardrail로 개인정보 필터링 추가
- `docs/09-flow-human-loop.md` 4-2 멀티스텝 승인 워크플로 패턴 구현

---

## 워크플로우 8 — MCP 통합 Agent (6-1)

### 구성도

```
[Chat Input]
  User Message
     │
     ▼
[Agent]
  Input: Chat Input → User Message
  Tools ↓
  ├─ [MCP Connection Tool #1]    Mode: Stdio / Streamable-HTTP
  │    MCP Server: (미설정)
  │
  ├─ [MCP Connection Tool #2]    Mode: Stdio / Streamable-HTTP
  │    MCP Server: Context7
  │
  └─ [MCP Connection Tool #3]    Mode: Stdio / Streamable-HTTP
       MCP Server: Github
       (세 번째: Atlassian)
  System Prompt: "당신은 여러 외부 도구를 사용할 수 있는 AI 어시스턴트입니다."
  Model: azure_openai:gpt-4.1-mini
     │
     ▼ Response
[Chat Output]
```

### MCP 서버 구성

| # | MCP Server | 용도 |
|---|-----------|------|
| 1 | Context7 | 라이브러리/프레임워크 공식 문서 조회 |
| 2 | GitHub | Repo 탐색, 코드 검색, Issue/PR 조회 |
| 3 | Atlassian | Jira 티켓 조회, Confluence 문서 검색 |

### 특징 및 적용 패턴

- **MCP Connection Tool 3개 병렬 연결**: Agent가 질문 내용에 따라 적절한 MCP 서버 도구를 선택해 호출
- `Stdio` / `Streamable-HTTP` 두 모드 지원 — 서버 타입에 맞게 선택
- `docs/11-flow-mcp.md`에서 제안한 테스트 권장 3선(Context7 / GitHub / Atlassian) 그대로 구현
- 가장 확장성이 높은 패턴 — MCP 서버 추가만으로 에이전트 능력 확장 가능

---

## 구현 플로우 종합 분석

### docs 제안 대비 구현 현황

| docs 플로우 ID | 플로우명 | 구현 여부 | 비고 |
|--------------|---------|---------|------|
| 1-1 | 문서 Q&A 챗봇 | ✅ 구현 | Language Model 사용 |
| 1-2 | 문서 요약 + 구조화 추출 | ✅ 구현 | Agent 사용 (구조화 미포함) |
| 1-3 | 멀티 KMS 비교 분석 | - 미구현 | |
| 2-1 | 리서치 Agent | ✅ 구현 | PLL Guardrail 포함 |
| 2-2 | 사내 시스템 연동 Agent | ✅ 구현 | ISMS/EMS API 연동 |
| 2-3 | RAG + 실시간 검색 하이브리드 | - 미구현 | |
| 3-1 | AI 자동 분류 라우터 | ✅ 구현 | |
| 3-2 | Human Choice 라우터 | ✅ 구현 | |
| 4-1 | 중요 문서 발송 전 승인 | - 미구현 | |
| 4-2 | 멀티스텝 승인 워크플로 | ✅ 구현 | Template Message + PLL 추가 |
| 5-1 | 안전한 고객 대응 챗봇 | - 미구현 | |
| 5-2 | 개인정보 비식별화 처리 | - 미구현 | |
| 6-1 | MCP 연결 통합 Agent | ✅ 구현 | Context7/GitHub/Atlassian 3선 |

### 주요 적용 패턴 검증 현황

| 패턴 | 적용 워크플로우 | 검증 결과 |
|------|--------------|---------|
| Chat Input → LM 패스스루 → PLL Guardrail | 2-1 | ✅ 정상 적용 |
| Human Approval → LM 경유 → Chat Output | 4-2 | ✅ 정상 적용 |
| Agent Tools 다중 연결 | 2-1, 6-1 | ✅ 정상 동작 |
| MCP Connection Tool × 3 | 6-1 | ✅ 정상 연결 |
| AI Router 다중 경로 | 3-1, 3-2 | ✅ 정상 구성 |
| else 경로 → Agent/LM 경유 | 3-1, 3-2 | ✅ 직접 연결 불가 제약 준수 |

### 노드 사용 빈도

| 노드 | 사용 수 | 사용 워크플로우 |
|------|--------|--------------|
| Agent | 8+ | 1-2, 2-1, 2-2, 3-1, 3-2, 4-2, 6-1 |
| Chat Input | 8 | 전체 |
| Chat Output | 8 | 전체 |
| Language Model | 4 | 1-1, 2-1(패스스루), 3-1/3-2(경로), 4-2 |
| KMS Retriever | 3 | 1-1, 1-2, 3-1/3-2 |
| Document Formatter | 3 | 1-1, 1-2, 3-1/3-2 |
| PLL Guardrail | 2 | 2-1, 4-2 |
| Human Approval | 1 | 4-2 |
| MCP Connection Tool | 3 | 6-1 |
| API Request Tool | 1 | 2-2 |
| Template Message | 1 | 4-2 |
| AI Router / Human Choice | 2 | 3-1, 3-2 |
| Web Search Tool | 1 | 2-1 |
| Youtube Search Tool | 1 | 2-1 |
| KOSIS Statistics Tool | 1 | 2-1 |
