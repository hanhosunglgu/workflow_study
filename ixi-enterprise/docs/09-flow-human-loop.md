# 플로우 카테고리 4: Human-in-the-Loop

**작성일**: 2026-05-15  
**최종 수정**: 2026-05-18 (01-node-catalog.md UI 검증 결과 반영)  
**포함 플로우**: 4-1 중요 문서 발송 전 승인 플로우 / 4-2 멀티스텝 승인 워크플로

---

## 4-1. 중요 문서 발송 전 승인 플로우

### 개요

| 항목 | 내용 |
|------|------|
| 난이도 | ⭐⭐ 보통 |
| 핵심 노드 | Chat Input → KMS Retriever → Document Formatter → Language Model → Human Approval → API Request → Language Model → Chat Output |
| 구현 예상 시간 | 1~2일 |
| 현재 상태 | 🔲 미구현 |
| 임팩트 | 🥈 사내향 Top 2 — AI 자동화 + 사람 검토 균형 |

### 플로우 구성도

```
[Chat Input]
     │ User Message ("고객사 A에게 제안서 요약 이메일 작성해줘")
     ▼
[KMS Retriever]
  ⚠️ PLL Guardrail 미적용 — Azure Language Service API Key 미등록 시 401 오류 발생
     Guardrail 필요 시: Language Model(패스스루) → PLL Guardrail → KMS Retriever 순으로 배치
  Knowledge: 제안서 지식베이스
     │ Documents (주황)
     ▼
[Document Formatter]
     │ Result (초록)
     ▼
[Language Model]
  System Prompt: "아래 제안서 내용을 바탕으로 고객사 이메일을 작성하세요."
  Model: azure_openai:gpt-4.1-mini
     │ Response (이메일 초안, 파란)
     ▼
[Human Approval]
  Target Message: Language Model Response 연결
  question: "이 이메일을 발송하시겠습니까?"
  Model: azure_openai:gpt-4.1-mini
     │
     ├─[승인]──────────────────────────────────────────┐
     │  [API Request(일반 모드)]                        │
     │    POST https://mail.company.com/send            │
     │    Body: { to, subject, body }                   │
     │       │ Data (파란)                               │
     │       ▼                                          │
     │  [Language Model]                                │
     │  ⚠️ Human Approval 출력 → Chat Output 직접 연결  │
     │     불가. Language Model 또는 Agent 경유 필수     │
     │    "이메일이 발송되었습니다."                       │
     │       │ Response                                 │
     │       ▼                                          │
     │  [Chat Output] ◀────────────────────────────────┘
     │
     └─[거부]
        플로우 즉시 종료 (이후 노드 실행 없음)
```

> ⚠️ **Human Approval 출력 → Chat Output 직접 연결 불가**  
> Human Approval 출력 포트에 연결 가능한 노드: Agent / Language Model / AI Router / Human Approval / Human Choice / KMS Retriever / Structured Output.  
> API Request(일반 모드) Data 출력 → Language Model → Chat Output 순으로 연결.

### 사내 활용 예시

| 활용 분야 | 트리거 | Human Approval 질문 |
|----------|-------|-------------------|
| 고객사 이메일 발송 | 이메일 초안 생성 | "이 이메일을 발송하시겠습니까?" |
| 사내 공지 발송 | 공지문 작성 | "이 공지를 전체 발송하시겠습니까?" |
| 계약서 전송 | 계약서 초안 생성 | "이 계약서를 상대방에게 전송하시겠습니까?" |
| 보고서 제출 | 보고서 생성 | "이 보고서를 상급자에게 제출하시겠습니까?" |
| API 데이터 변경 | 변경 내용 확인 | "시스템 데이터를 변경하시겠습니까?" |

### Human Approval 동작 방식

```
승인 시:
  → Human Approval 이후 노드(API Request 등) 실행
  → 정상 플로우 계속 진행

거부 시:
  → 전체 플로우 즉시 종료
  → "작업이 취소되었습니다" 메시지 반환
  → 이후 노드 실행 없음
```

### 구현 시 주의사항

- Human Approval의 `Target Message`에는 사용자가 검토할 내용 전체를 전달
- 승인 화면에 표시되는 내용이 명확하고 읽기 쉽게 포매팅 필요
- 타임아웃 설정 권장: 장시간 미응답 시 자동 거부 처리
- API Request 결과를 Chat Output으로 전달하려면 Language Model 경유 필수

---

## 4-2. 멀티스텝 승인 워크플로

### 개요

| 항목 | 내용 |
|------|------|
| 난이도 | ⭐⭐⭐ 복잡 |
| 핵심 노드 | Chat Input → Agent → Human Approval → Agent → Chat Output |
| 구현 예상 시간 | 3~5일 |
| 현재 상태 | 🔲 미구현 |

### 한계점 — JSON Output과 Chat Output 동시 사용 불가

> ❌ **플로우 내 JSON Output 추가 시 Chat Output 비활성화** (2026-05-18 확인)  
> JSON Output과 Chat Output은 상호 배타적 — 하나의 플로우에서 동시 사용 불가.  
>
> **원래 의도했던 구조** (불가):
> ```
> Agent Response
>   ├──→ Structured Output → JSON Output   ← JSON 구조화 저장
>   └──→ Human Approval → ... → Chat Output ← 채팅 출력
> ```
> JSON Output을 추가하는 순간 Chat Output이 비활성화되어 채팅 인터페이스 테스트 불가.
>
> **현재 선택**: Chat Output only — Structured Output / JSON Output 분기 제거.  
> JSON 구조화가 필요한 경우 별도 플로우로 분리하거나, n8n 등 외부 시스템에서 처리 권장.

### 플로우 구성도

```
[Web Search Tool]      ─┐
[KOSIS Statistics Tool]─┤ Tool 포트(빨간) → Agent Tools에 연결
[Simple Calculator Tool]┘

[Chat Input]
  ⚠️ Template Message는 INPUT 컴포넌트로 인식되지 않아
     "단 하나의 INPUT 컴포넌트는 필수입니다" 오류 발생
     Chat Input을 시작점으로 사용해야 함
  예시 입력: "5월 1주의 AI 시장 동향에 대해 알려줘"
     │ User Message (파란)
     ▼
[Agent]
  System Prompt: "주간 시장 동향 리포트 작성 전문가입니다.
                  리포트는 제목, 요약, 핵심 내용, 통계, 결론 순으로 작성하세요."
  Model: azure_openai:gpt-4.1-mini
     │ Response (파란)
     ▼
[Human Approval]
  Target Message: Agent Response 연결
  question: "이 리포트를 확정하시겠습니까?"
  Model: azure_openai:gpt-4.1-mini
     │
     ├─[승인]─────────────────────────────────────┐
     │  [Agent]                                    │
     │  ⚠️ Human Approval 출력은 Chat Output       │
     │     직접 연결 불가 — Agent 경유 필수          │
     │    System Prompt: "승인된 리포트를            │
     │    최종 형식으로 출력하세요."                  │
     │    Model: azure_openai:gpt-4.1-mini         │
     │       │ Response                            │
     │       ▼                                     │
     │  [Chat Output] ◀───────────────────────────┘
     │
     └─[거부]
        플로우 즉시 종료
```

> ⚠️ **Human Approval 출력 → Chat Output 직접 연결 불가**  
> Human Approval 출력 포트 연결 가능 노드: Agent / Language Model / AI Router / Human Approval / Human Choice / KMS Retriever / Structured Output.  
> Agent 또는 Language Model을 경유해야 Chat Output 연결 가능.  
> 단, Language Model Response → Chat Output도 UI상 연결 불가 확인 (2026-05-18) — Agent 경유 권장.

### 단계별 역할 분리

| 단계 | 노드 | 역할 |
|------|------|------|
| 1 | Chat Input | 사용자 요청 입력 (INPUT 컴포넌트 필수) |
| 2 | Agent + Tools | 데이터 수집 및 리포트 초안 작성 |
| 3 | Human Approval | Agent Response 기반 사람이 최종 검토 및 승인 |
| 4 | Agent → Chat Output | 승인된 리포트를 채팅으로 출력 (Human Approval → Chat Output 직접 불가) |

> ⚠️ JSON 구조화 저장이 필요하면 **별도 플로우**로 분리 — JSON Output ↔ Chat Output 동시 사용 불가.

### 사내 활용 예시

| 활용 분야 | Chat Input 예시 | 출력 |
|----------|--------------|------|
| 주간 시장 동향 리포트 | "5월 1주 AI 시장 동향 리포트 작성해줘" | Chat Output |
| 경쟁사 동향 보고서 | "삼성전자 최근 1개월 동향 분석해줘" | Chat Output |
| 기술 트렌드 뉴스레터 | "LLM 기술 트렌드 뉴스레터 작성해줘" | Chat Output |
| 통계 대시보드 업데이트 | "국내 실업률 최신 통계 정리해줘" | Chat Output |

---

## Human-in-the-Loop 공통 설계 원칙

### Human Approval vs Human Choice 선택 기준

| 상황 | 권장 노드 | 이유 |
|------|---------|------|
| Yes/No 단순 승인 | Human Approval | 승인/거부 2가지만 필요 |
| 여러 후속 경로 중 선택 | Human Choice | 3개 이상 선택지 필요 |
| 중요 작업 전 최종 확인 | Human Approval | 거부 시 전체 취소 보장 |
| 작업 방향 결정 | Human Choice | 경로별 다른 처리 필요 |

### 포트 연결 제약 요약

| 노드 | Target Message 입력 | 출력 | Chat Output 직접 연결 |
|------|-------------------|------|---------------------|
| Human Approval | Agent / Language Model / AI Router / Human Approval / Human Choice / API Request / PLL Guardrail / Moderation Guardrail | Human Approval (파란) | ❌ 불가 — Language Model / Agent 경유 필수 |
| Human Choice | Chat Input 포함 대부분 노드 | 조건별 분기 + else | else 토글 ON만 가능 |

### 승인 게이트 배치 원칙

```
비용/위험이 큰 작업 앞에 배치:
  ✅ 외부 발송 (이메일, API 호출) 직전
  ✅ 데이터 변경/삭제 직전
  ✅ 금전 처리 직전

불필요한 위치:
  ❌ 단순 조회 작업 전
  ❌ 내부 계산 작업 전
  ❌ 이미 Human Choice로 경로를 선택한 직후
```

### 승인 메시지 포매팅 권장 형식

```
📋 검토 내용
─────────────────────────
제목: [내용]
수신: [대상]
내용 요약:
  • [핵심 내용 1]
  • [핵심 내용 2]
─────────────────────────
⚠️ 승인 시 즉시 실행됩니다.
```
