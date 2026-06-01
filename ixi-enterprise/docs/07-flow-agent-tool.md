# 플로우 카테고리 2: Agent + Tool 조합

**작성일**: 2026-05-15  
**최종 수정**: 2026-05-18 (01-node-catalog.md UI 검증 결과 반영)  
**포함 플로우**: 2-1 리서치 Agent / 2-2 사내 시스템 연동 Agent / 2-3 RAG+실시간 검색 하이브리드

---

## 2-1. 리서치 Agent

### 개요

| 항목 | 내용 |
|------|------|
| 난이도 | ⭐⭐ 보통 |
| 핵심 노드 | Chat Input → Agent (Web + Youtube + KOSIS) → Chat Output |
| 구현 예상 시간 | 1~2일 |
| 현재 상태 | 🔲 미구현 |

### 플로우 구성도

```
[Web Search Tool]      ─┐
[Youtube Search Tool]  ─┤ Tool 포트(빨간) → Agent Tools에 연결
[KOSIS Statistics Tool]─┘

[Chat Input]
     │ User Message
     ▼
[Agent]
  System Prompt:
    "당신은 리서치 전문 AI 어시스턴트입니다.
     질문에 답하기 위해 웹 검색, 유튜브, KOSIS 통계를 자율적으로 활용하세요.
     출처를 반드시 명시하세요."
  Jailbreak Check: ON
  Model: azure_openai:gpt-4.1-mini
     │ Response
     ▼
[Chat Output]
```

> **PLL Guardrail 제거 이유**: PLL Guardrail은 Azure PII Detection API Key 및 엔드포인트가 사전 등록되어 있어야 동작함. 미등록 시 `401 Access denied` 오류 발생. 사내 내부 사용자 전용 플로우이므로 Guardrail 없이 `Chat Input → Agent` 직접 연결로 단순화.

### 사내 활용 예시

| 요청 | Agent 동작 |
|------|-----------|
| "국내 AI 시장 규모 알려줘" | KOSIS 통계 조회 + 웹 검색으로 최신 시장 데이터 수집 |
| "경쟁사 최근 동향 분석해줘" | 웹 검색으로 뉴스/블로그 수집 후 요약 |
| "이 기술 관련 유튜브 강의 추천해줘" | Youtube 검색 후 관련 영상 목록 및 요약 제공 |
| "산업별 취업자 수 추이 알려줘" | KOSIS 통계 데이터 조회 + 계산기로 증감률 계산 |

### ReAct 동작 방식

```
사용자: "2025년 국내 클라우드 시장 규모와 성장률 알려줘"

Agent 내부 동작:
  1. Think: "KOSIS에서 통계 데이터를 찾고, 웹에서 최신 기사도 검색해야겠다"
  2. Act: KOSIS Statistics Tool 호출 → 클라우드 관련 통계 조회
  3. Observe: 통계 데이터 수신
  4. Think: "웹에서 더 최신 정보를 보완해야겠다"
  5. Act: Web Search Tool 호출 → "2025 클라우드 시장 규모" 검색
  6. Observe: 검색 결과 수신
  7. Think: "충분한 정보가 모였다. 종합 답변을 작성하자"
  8. Final Answer: 통계 + 웹 정보를 종합한 답변 생성
```

---

## 2-2. 사내 시스템 연동 Agent

### 개요

| 항목 | 내용 |
|------|------|
| 난이도 | ⭐⭐ 보통 |
| 핵심 노드 | Chat Input → Agent (API Request×N) → Chat Output |
| 구현 예상 시간 | 1~2일 (사내 API 스펙 확보 전제) |
| 현재 상태 | 🔲 미구현 |

### 플로우 구성도

```
[API Request(Tool Mode ON)] — ERP 시스템   ─┐
  예산 조회, 구매 요청 상태 확인              │
[API Request(Tool Mode ON)] — HR 시스템    ─┤ Tool 포트(빨간) → Agent Tools에 연결
  연차 현황, 조직도 조회                     │
[API Request(Tool Mode ON)] — 결재 시스템  ─┤
  결재 문서 상태 확인                        │
[Simple Calculator Tool]               ─┘
  계산이 필요한 경우

[Chat Input]
     │ User Message
     ▼
[Agent]
  ⚠️ Guardrail 필요 시 Agent → PLL Guardrail 순으로 배치
     (PLL Guardrail은 Azure PII Detection API Key 등록 필요 — 미등록 시 401 오류)
  System Prompt:
    "당신은 사내 업무 도우미입니다.
     사용자의 요청에 따라 적절한 시스템 API를 호출하여 답변하세요."
  Model: azure_openai:gpt-4.1-mini
     │ Response
     ▼
[Chat Output]
```

> **API Request Tool 모드**: 노드 상단 `Tool Mode` 토글 ON → 출력 포트가 `Data`(파란)에서 `Tool`(빨간)로 전환. Tool 모드에서만 Agent Tools 포트에 연결 가능.

### 사내 활용 예시

| 요청 | 호출 API |
|------|---------|
| "이번 달 팀 예산 집행률 알려줘" | ERP API → 예산 데이터 조회 + Calculator |
| "홍길동 님 남은 연차 조회해줘" | HR API → 연차 현황 조회 |
| "내 결재 대기 문서 목록 보여줘" | 결재 시스템 API → 대기 문서 목록 |
| "작년 대비 비용 증감률 계산해줘" | ERP API + Calculator Tool |

### 구현 시 필요 사항

- 사내 API 엔드포인트 및 인증 방식 확보 (API Key, OAuth 등)
- API Request 노드의 `Header`에 인증 토큰 설정
- 각 API를 Tool로 등록하고 Agent에 연결

---

## 2-3. RAG + 실시간 검색 하이브리드 Agent

### 개요

| 항목 | 내용 |
|------|------|
| 난이도 | ⭐⭐⭐ 복잡 |
| 핵심 노드 | Chat Input → Agent (KMS Retriever + Document Formatter + Web Search) → Chat Output |
| 구현 예상 시간 | 3~5일 |
| 현재 상태 | 🔲 미구현 |

### 플로우 구성도

```
[Web Search Tool] ─── Tool 포트(빨간) → Agent Tools에 연결

[Chat Input]
     │ User Message
     ▼
[Agent]
  ⚠️ KMS Retriever는 Tool 포트가 없음 — Agent Tools에 직접 연결 불가
     대신 Agent Response를 KMS Query 입력으로 연결하는 순차 구조 사용
  System Prompt:
    "당신은 사내 지식과 최신 외부 정보를 모두 활용하는 AI 어시스턴트입니다.
     - 사내 정책/규정 관련 질문은 사내 문서 검색 결과를 바탕으로 답변하세요.
     - 최신 시장/기술 트렌드는 웹 검색을 활용하세요.
     - 두 정보를 비교할 경우 출처를 명확히 구분하세요."
  Jailbreak Check: ON
  Model: azure_openai:gpt-4.1-mini
     │ Response (파란)
     ├──→ [Chat Output]              ← 웹 검색만으로 충분한 경로
     └──→ [KMS Retriever]            ← 사내 문서 검색이 필요한 경로
               │ Documents (주황)
               ▼
          [Document Formatter]
               │ Result (초록)
               ▼
          [Language Model]           ← Document Formatter Result(초록)는 LM에만 연결 가능
            System Prompt:
              "Agent의 분석 결과와 사내 문서를 종합하여 최종 답변을 작성하세요."
            Model: azure_openai:gpt-4.1-mini
               │ Response
               ▼
          [Chat Output]
```

> ⚠️ **KMS Retriever는 Tool 노드가 아님**: KMS Retriever에는 Tool 출력 포트가 없어 Agent Tools에 연결 불가.  
> 사내 RAG + 외부 검색 하이브리드는 Agent를 두 단계로 나누거나, AI Router로 경로를 먼저 분기하는 방식으로 설계해야 함.  
> 단순 구현 시 Agent(웹 검색) → KMS Retriever → Document Formatter → Language Model 순차 파이프라인 권장.

### 사내 활용 예시

| 요청 | KMS 활용 | 웹 검색 활용 |
|------|---------|------------|
| "우리 회사 보안 정책과 최신 법령을 비교해줘" | 사내 보안 정책 문서 | 최신 정보보호 법령 |
| "사내 AI 가이드라인과 글로벌 트렌드 비교해줘" | AI 사용 가이드라인 KMS | 최신 AI 거버넌스 동향 |
| "우리 제품 스펙과 경쟁사 제품 비교해줘" | 사내 제품 문서 | 경쟁사 제품 웹페이지 |

### 1-1 / 2-1 / 2-3 비교

| 항목 | 1-1 문서 Q&A | 2-1 리서치 Agent | 2-3 하이브리드 |
|------|------------|----------------|--------------|
| 정보 소스 | KMS만 | 웹/유튜브/KOSIS | KMS + 웹 |
| 최신성 | 문서 업로드 시점 | 실시간 | 실시간 + 사내 기준 |
| 정확성 | 사내 문서 기준 높음 | 웹 의존 | 균형 |
| 구현 복잡도 | 낮음 | 보통 | 높음 |

---

## Agent 공통 설계 원칙

### System Prompt 구조

```
[Role]
당신은 [역할명]입니다.

[Rules]
1. [규칙 1]
2. [규칙 2]
3. 답변은 반드시 한국어로 작성하세요.
4. 출처를 반드시 명시하세요.
5. 불확실한 정보는 "확인이 필요합니다"라고 답변하세요.

[Tools]
- [Tool 이름]: [언제 사용하는지]
- [Tool 이름]: [언제 사용하는지]
```

### Jailbreak Check 설정 기준

| 상황 | 설정 |
|------|------|
| 사내 내부 사용자 전용 | OFF (성능 우선) |
| 외부 고객 접점 서비스 | ON (보안 우선) |
| 민감 정보 처리 업무 | ON |

### Tool 연결 개수 권장

| 상황 | 권장 Tool 수 |
|------|------------|
| 단순 작업 | 1~2개 |
| 복합 리서치 | 3~4개 |
| 통합 업무 Agent | 5개 이하 (많을수록 판단 오류 위험) |
