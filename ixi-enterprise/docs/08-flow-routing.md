# 플로우 카테고리 3: 라우팅 / 분기

**작성일**: 2026-05-15  
**최종 수정**: 2026-05-18 (01-node-catalog.md UI 검증 결과 반영)  
**포함 플로우**: 3-1 AI 자동 분류 라우터 / 3-2 사람이 경로를 선택하는 워크플로

---

## 3-1. AI 자동 분류 라우터

### 개요

| 항목 | 내용 |
|------|------|
| 난이도 | ⭐⭐ 보통 |
| 핵심 노드 | Chat Input → AI Router → 다중 경로 → Chat Output |
| 구현 예상 시간 | 1~2일 |
| 현재 상태 | 🔲 미구현 |
| 임팩트 | 🥇 사내향 Top 1 — 하나의 채팅창으로 모든 업무 처리 |

### 플로우 구성도

```
[Web Search Tool]       ─┐
[Youtube Search Tool]   ─┤ Tool 포트(빨간) → 경로 D Agent Tools에 연결
[KOSIS Statistics Tool] ─┤ Tool 포트(빨간) → 경로 C Agent Tools에 연결
[Simple Calculator Tool]─┘ Tool 포트(빨간) → 경로 B/C Agent Tools에 연결

[Chat Input]
     │ User Message
     ▼
[AI Router]
  ⚠️ Chat Input → AI Router 직접 연결 가능 (AI Router Input은 Chat Input 허용)
  Model: azure_openai:gpt-4.1-mini
  else 조건 기본 AI 메시지 사용: OFF
  Conditions:
    - "문서/정책/사규 관련" → 경로 A
    - "계산/수치 관련"       → 경로 B
    - "통계/데이터 관련"     → 경로 C
    - "웹 검색/최신 정보"    → 경로 D
     │
     ├─[경로 A: 문서 Q&A]──────────────────────────────────┐
     │  [KMS Retriever]                                    │
     │       │ Documents (주황)                             │
     │  [Document Formatter]                               │
     │       │ Result (초록)                                │
     │  [Language Model]  ← 문서 기반 답변                  │
     │       │ Response                                     │
     │       ▼                                             │
     │  [Chat Output] ◀───────────────────────────────────┘
     │
     ├─[경로 B: 계산]──────────────────────────────────────┐
     │  [Agent]                                            │
     │    └──(Tool)── [Simple Calculator Tool]             │
     │       │ Response                                    │
     │       ▼                                             │
     │  [Chat Output] ◀───────────────────────────────────┤
     │                                                     │
     ├─[경로 C: 통계]──────────────────────────────────────┤
     │  [Agent]                                            │
     │    ├──(Tool)── [KOSIS Statistics Tool]              │
     │    └──(Tool)── [Simple Calculator Tool]             │
     │       │ Response                                    │
     │       ▼                                             │
     │  [Chat Output] ◀───────────────────────────────────┤
     │                                                     │
     ├─[경로 D: 웹 검색]───────────────────────────────────┤
     │  [Agent]                                            │
     │    ├──(Tool)── [Web Search Tool]                    │
     │    └──(Tool)── [Youtube Search Tool]                │
     │       │ Response                                    │
     │       ▼                                             │
     │  [Chat Output] ◀───────────────────────────────────┤
     │                                                     │
     └─[else: 일반 대화]───────────────────────────────────┤
        ⚠️ AI Router else 포트는 Chat Output 직접 연결 불가
           Language Model 경유 필수
        [Language Model]  ← 일반 답변
               │ Response
               ▼
        [Chat Output] ◀──────────────────────────────────┘
```

> ⚠️ **AI Router else → Chat Output 직접 연결 불가**  
> AI Router else 포트에 연결 가능한 노드: Agent / Language Model / AI Router / Human Approval / Human Choice / KMS Retriever / Structured Output.  
> Chat Output 직접 연결 불가 — else 경로는 반드시 Language Model 또는 Agent를 경유해야 함.

> **PLL Guardrail 미적용 이유**: PLL Guardrail은 Azure Language Service API Key 등록 필요. 미등록 시 `401 Access denied` 오류 발생 (2026-05-18 확인). 필요 시 `AI Router → [각 경로 처리 노드] → PLL Guardrail → Chat Output` 구조로 추가.

### 라우팅 조건 설계 예시

| 사용자 입력 | 감지 키워드/의도 | 라우팅 경로 |
|-----------|----------------|-----------|
| "연차 규정 알려줘" | 사규, 정책, 규정, 문서 | 경로 A (문서 Q&A) |
| "3억 * 1.2 계산해줘" | 계산, 수식, 금액 | 경로 B (계산) |
| "작년 실업률 통계 보여줘" | 통계, 수치, 데이터, KOSIS | 경로 C (통계) |
| "최근 AI 트렌드 알려줘" | 최신, 뉴스, 트렌드, 검색 | 경로 D (웹 검색) |
| "오늘 날씨 어때?" | 위 조건 미해당 | else (일반 대화) |

### 확장 구성 (고급)

```
[AI Router]
  Conditions 추가:
    - "사내 시스템 조회"  → API Request(Tool Mode ON) → Agent
    - "보고서 작성"       → Agent + KMS + Structured Output → JSON Output
    - "승인 요청"         → Language Model → Human Approval → Language Model → Chat Output
```

### AI Router vs Human Choice 비교

| 항목 | AI Router (3-1) | Human Choice (3-2) |
|------|----------------|-------------------|
| 분기 결정자 | LLM이 자동 판단 | 사용자가 직접 선택 |
| 속도 | 빠름 (자동) | 느림 (사람 개입) |
| 정확성 | LLM 판단 오류 가능 | 사용자 의도 명확 |
| 사용 상황 | 명확한 의도 구분 가능 시 | 모호하거나 중요한 분기 시 |

---

## 3-2. 사람이 경로를 선택하는 워크플로

### 개요

| 항목 | 내용 |
|------|------|
| 난이도 | ⭐⭐ 보통 |
| 핵심 노드 | Chat Input → Human Choice → 다중 경로 → Chat Output |
| 구현 예상 시간 | 1~2일 |
| 현재 상태 | 🔲 미구현 |

### 플로우 구성도

```
[Web Search Tool]      ─┐
[Youtube Search Tool]  ─┤ Tool 포트(빨간) → 경로 B Agent Tools에 연결
[KOSIS Statistics Tool]─┘ Tool 포트(빨간) → 경로 C Agent Tools에 연결

[Chat Input]
     │ User Message
     ▼
[Human Choice]
  ⚠️ Chat Input → Human Choice 직접 연결 가능 (Human Choice Input은 Chat Input 허용)
  question: "어떤 작업을 진행하시겠습니까?"
  Model: azure_openai:gpt-4.1-mini
  else 조건 기본 AI 메시지 사용: ON  ← else 포트에 Chat Output 연결 가능
  Conditions:
    - "📄 문서 검색/요약"   → 경로 A
    - "🔍 웹 검색/리서치"   → 경로 B
    - "📊 통계 데이터 조회"  → 경로 C
     │
     ├─[경로 A: 문서]──────────────────────────────────────┐
     │  [KMS Retriever]                                    │
     │       │ Documents (주황)                             │
     │  [Document Formatter]                               │
     │       │ Result (초록)                                │
     │  [Language Model]                                   │
     │       │ Response                                    │
     │       ▼                                             │
     │  [Chat Output] ◀───────────────────────────────────┤
     │                                                     │
     ├─[경로 B: 웹 검색]───────────────────────────────────┤
     │  [Agent]                                            │
     │    ├──(Tool)── [Web Search Tool]                    │
     │    └──(Tool)── [Youtube Search Tool]                │
     │       │ Response                                    │
     │       ▼                                             │
     │  [Chat Output] ◀───────────────────────────────────┤
     │                                                     │
     ├─[경로 C: 통계]──────────────────────────────────────┤
     │  [Agent]                                            │
     │    └──(Tool)── [KOSIS Statistics Tool]              │
     │       │ Response                                    │
     │       ▼                                             │
     │  [Chat Output] ◀───────────────────────────────────┤
     │                                                     │
     └─[else: 일반 대화]───────────────────────────────────┤
        ⚠️ else 토글 ON → Chat Output / PLL Guardrail /    │
                          Moderation Guardrail만 연결 가능  │
        [Chat Output] ◀──────────────────────────────────┘
```

> ⚠️ **Human Choice else 토글 상태별 연결 가능 노드**  
>
> | else 토글 | 연결 가능 노드 |
> |----------|-------------|
> | ON | Chat Output / PLL Guardrail / Moderation Guardrail |
> | OFF | Agent / Language Model / AI Router / Human Approval / Human Choice / KMS Retriever / Structured Output |
>
> else 경로를 Chat Output으로 직접 연결하려면 **토글 ON** 필수.  
> else 경로를 추가 처리(LM, KMS 등)로 보내려면 **토글 OFF**로 변경.

### 사내 활용 예시

```
시나리오: 업무 도우미 메뉴 방식 인터페이스

사용자가 채팅창을 열면:
  "안녕하세요! 무엇을 도와드릴까요?
   ① 📄 사내 문서 검색/요약
   ② 🔍 웹 검색/리서치
   ③ 📊 통계 데이터 조회
   ④ 💬 일반 질문 (else)"

사용자가 "①"을 선택하면:
  → KMS Retriever → Document Formatter → Language Model → Chat Output
  "어떤 문서를 검색할까요?" 추가 질문
```

### 3-1과의 조합 (권장 패턴)

```
복잡한 플로우에서는 AI Router와 Human Choice를 계층적으로 조합:

[Chat Input]
     ↓
[AI Router] ──── 명확한 의도 → 자동 경로 (각 경로 → Chat Output)
     │
     └── else(OFF) → [Human Choice] ──── 사용자 선택 → 각 경로 → Chat Output
                          └── else(ON) → [Chat Output]
```

---

## 라우팅 플로우 공통 설계 원칙

### AI Router 조건 작성 가이드

```
좋은 조건 (명확한 트리거 키워드):
  ✅ "사용자 입력에 '계산', '수식', '%', '곱하기', '나누기'가 포함된 경우"
  ✅ "사용자 입력이 사내 정책이나 규정에 관한 질문인 경우"

나쁜 조건 (모호하여 LLM 판단 오류 발생):
  ❌ "중요한 질문인 경우"
  ❌ "어려운 내용인 경우"
```

### else 조건 처리

| 노드 | else 토글 | 동작 |
|------|----------|------|
| AI Router | OFF (항상) | else 포트 → Language Model / Agent 등으로 연결. Chat Output 직접 연결 불가 |
| Human Choice | ON | else 포트 → Chat Output / PLL Guardrail / Moderation Guardrail만 연결 가능 |
| Human Choice | OFF | else 포트 → Agent / Language Model / AI Router 등으로 연결 |

### 분기 수 권장

| 분기 수 | 평가 |
|--------|------|
| 2~3개 | 최적 — 명확한 분기, 오류 낮음 |
| 4~5개 | 적정 — 충분히 관리 가능 |
| 6개 이상 | 주의 — LLM 판단 오류 가능성 증가, Human Choice 병행 권장 |

### 포트 연결 제약 요약

| 노드 | 입력 | 출력(else) | Chat Output 직접 연결 |
|------|------|-----------|---------------------|
| AI Router | Chat Input 허용 | Language Model / Agent 등 | ❌ 불가 |
| Human Choice | Chat Input 허용 | 토글 ON: Chat Output 가능 / 토글 OFF: LM/Agent 등 | 토글 ON만 가능 |
