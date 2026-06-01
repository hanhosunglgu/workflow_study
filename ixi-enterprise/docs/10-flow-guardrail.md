# 플로우 카테고리 5: Guardrail (안전 레이어)

**작성일**: 2026-05-15  
**최종 수정**: 2026-05-18 (01-node-catalog.md UI 검증 결과 반영)  
**포함 플로우**: 5-1 안전한 고객 대응 챗봇 / 5-2 개인정보 비식별화 처리

---

## 5-1. 안전한 고객 대응 챗봇

### 개요

| 항목 | 내용 |
|------|------|
| 난이도 | ⭐⭐ 보통 |
| 핵심 노드 | Chat Input → Language Model(패스스루) → PLL Guardrail → Moderation Guardrail → KMS Retriever → Document Formatter → Language Model → Moderation Guardrail → Chat Output |
| 구현 예상 시간 | 1~2일 |
| 현재 상태 | 🔲 미구현 |
| 임팩트 | 🥉 사내향 Top 3 — 컴플라이언스 요건 충족 |

### 플로우 구성도

```
[Chat Input]
     │ User Message (파란)
     ▼
[Language Model]             ← 패스스루 — Chat Input은 Guardrail에 직접 연결 불가
  System Prompt: 없음 (입력 그대로 전달)
  Model: azure_openai:gpt-4.1-mini
  ⚠️ Guardrail Input 포트는 Agent / Language Model / PLL Guardrail /
     Moderation Guardrail만 허용 — Chat Input 직접 연결 불가
     │ Response (파란)
     ▼
[PLL Guardrail]              ← 입력 개인정보 마스킹
  ⚠️ Azure Language Service API Key 등록 필수 — 미등록 시 401 Access denied 오류
  개인정보 감지 및 처리
     │ Response (마스킹된 입력, 파란)
     ▼
[Moderation Guardrail]       ← 입력 유해 콘텐츠 차단
  Hate: 3, SelfHarm: 2, Sexual: 2, Violence: 3
     │ Response (검증된 입력, 파란)
     ▼
[KMS Retriever]
  Knowledge: 고객 대응 지식베이스
     │ Documents (주황)
     ▼
[Document Formatter]
     │ Result (초록)
     ▼
[Language Model]
  System Prompt:
    "당신은 [회사명] 고객 응대 AI입니다.
     친절하고 전문적으로 답변하세요.
     문서에 없는 내용은 답변하지 마세요."
  Model: azure_openai:gpt-4.1-mini
     │ Response (AI 답변, 파란)
     ▼
[Moderation Guardrail]       ← 출력 유해 콘텐츠 재검사
  Hate: 2, SelfHarm: 1, Sexual: 1, Violence: 2
  (출력은 더 엄격하게 설정)
     │ Response (검증된 출력, 파란)
     ▼
[Chat Output]
```

> ⚠️ **Guardrail 입력 포트 제약**  
> PLL Guardrail / Moderation Guardrail의 Input 포트에 연결 가능한 노드: Agent / Language Model / PLL Guardrail / Moderation Guardrail.  
> Chat Input을 Guardrail에 직접 연결 불가 — Language Model(패스스루)을 앞에 배치해야 함.

> ⚠️ **PLL Guardrail 사전 조건**  
> Azure Language Service API Key 및 엔드포인트를 ixi-enterprise Settings에 등록 필요.  
> 미등록 시 `401 Access denied` 오류 발생. 등록 방법은 `04-open-questions.md` 항목 13 참조.

### Moderation 민감도 설정 가이드

슬라이더 값 1~7 의미: **1 = 가장 엄격 (거의 모두 차단)**, **7 = 가장 관대 (대부분 허용)**

| 카테고리 | 고객 대응 (입력) | 고객 대응 (출력) | 사내 업무용 | 연구/분석용 |
|---------|---------------|---------------|-----------|-----------|
| Hate | 3 | 2 | 4 | 5 |
| SelfHarm | 2 | 1 | 3 | 4 |
| Sexual | 2 | 1 | 3 | 5 |
| Violence | 3 | 2 | 4 | 5 |

### 사내 활용 예시

| 활용 분야 | KMS 지식베이스 | 특이 설정 |
|----------|-------------|---------|
| 고객 서비스 챗봇 | 제품 FAQ, 서비스 정책 | 출력 Moderation 더 엄격하게 |
| 사내 HR 헬프데스크 | 인사 규정, 복리후생 | PLL 필수 (급여/인사 정보) |
| IT 지원 챗봇 | 시스템 매뉴얼, 보안 정책 | Jailbreak Check ON |
| 법무 검토 보조 | 계약서 템플릿, 법령 | 출력 Human Approval 추가 권장 |

### Guardrail 실패 시 처리 방안 (미확인 — 추후 확인 필요)

```
현재 확인된 사항:
  - 통과 시: Response 포트로 정상 출력
  - 실패 시: 플로우 중단 또는 에러 메시지 반환 (스펙 확인 필요)

권장 설계:
  [Moderation Guardrail]
       ├── 통과 → 다음 노드 진행
       └── 실패 → Language Model ("죄송합니다. 해당 질문에는 답변드릴 수 없습니다.")
                  → Chat Output
```

---

## 5-2. 개인정보 비식별화 처리

### 개요

| 항목 | 내용 |
|------|------|
| 난이도 | ⭐ 쉬움 |
| 핵심 노드 | Chat Input → Language Model(패스스루) → PLL Guardrail → Language Model → Chat Output |
| 구현 예상 시간 | 0.5일 |
| 현재 상태 | 🔲 미구현 |

### 플로우 구성도

```
[Chat Input]
     │ User Message (파란)
     │ (개인정보 포함 문서 붙여넣기)
     │ 예: "홍길동(010-1234-5678)의 계약 내용은..."
     ▼
[Language Model]             ← 패스스루 — Chat Input은 PLL Guardrail에 직접 연결 불가
  System Prompt: 없음 (입력 그대로 전달)
  Model: azure_openai:gpt-4.1-mini
     │ Response (파란)
     ▼
[PLL Guardrail]
  ⚠️ Azure Language Service API Key 등록 필수 — 미등록 시 401 Access denied 오류
  개인정보 감지 및 마스킹
  예: "OOO(***-****-****)의 계약 내용은..."
     │ Response (마스킹된 텍스트, 파란)
     ▼
[Language Model]
  System Prompt:
    "아래 텍스트를 분석하세요.
     개인정보는 이미 마스킹 처리되었습니다.
     마스킹된 정보를 복원하거나 추론하지 마세요."
  Model: azure_openai:gpt-4.1-mini
     │ Response (파란)
     ▼
[Chat Output]
```

> ⚠️ **Chat Input → PLL Guardrail 직접 연결 불가**  
> PLL Guardrail Input은 Agent / Language Model / PLL Guardrail / Moderation Guardrail만 허용.  
> Chat Input을 먼저 Language Model(패스스루)에 연결한 후 PLL Guardrail로 전달해야 함.

### PLL Guardrail 감지 대상 (예상)

| 개인정보 유형 | 예시 | 마스킹 예시 |
|------------|------|-----------|
| 이름 | 홍길동 | OOO |
| 전화번호 | 010-1234-5678 | ***-****-**** |
| 이메일 | hong@company.com | ***@***.*** |
| 주민등록번호 | 900101-1234567 | ******-******* |
| 주소 | 서울시 강남구 역삼동 | [주소 마스킹] |
| 계좌번호 | 110-123-456789 | ***-***-****** |

> ⚠️ **미확인 사항**: PLL Guardrail의 실제 감지 항목 및 마스킹 방식은 ixi-enterprise 스펙 확인 필요

### 사내 활용 예시

| 활용 분야 | 처리 내용 |
|----------|---------|
| 고객 상담 내역 분석 | 고객 개인정보 마스킹 후 패턴 분석 |
| 계약서 검토 요청 | 당사자 정보 마스킹 후 계약 조항 분석 |
| 설문 응답 분석 | 응답자 식별 정보 제거 후 내용 분석 |
| 의료 기록 처리 | 환자 정보 마스킹 후 의료 내용 요약 |
| HR 데이터 분석 | 직원 개인정보 마스킹 후 패턴 분석 |

---

## Guardrail 공통 설계 원칙

### 연결 순서 — 필수 패턴

```
❌ 잘못된 구성 (Chat Input → Guardrail 직접 연결 불가):
  [Chat Input] → [PLL Guardrail] → ...

✅ 올바른 구성 (Language Model 패스스루 경유):
  [Chat Input] → [Language Model(패스스루)] → [PLL Guardrail] → ...

✅ Agent 경유도 가능:
  [Chat Input] → [Agent] → [PLL Guardrail] → ...
```

### 이중 Guardrail 패턴 (권장)

```
입력 검사:                                  출력 검사:
LM(패스스루) → PLL → Moderation → [처리] → Moderation → Chat Output

이유:
  - 입력 단계: 악의적 프롬프트 및 개인정보 유입 차단
  - 출력 단계: AI가 생성한 콘텐츠의 안전성 최종 확인
  - 두 단계 모두 적용 시 컴플라이언스 요건 충족 가능
```

### Guardrail 배치 위치

```
✅ 권장 위치:
  [Chat Input] → [LM(패스스루)] → [PLL] → [Moderation] → ... → [Moderation] → [Chat Output]

❌ 비효율적 위치:
  [Chat Input] → ... → [Language Model] → [PLL]
  (개인정보가 이미 LLM에 전달된 후 필터링 — 의미 없음)
```

### 포트 연결 제약 요약

| 노드 | Input 허용 노드 | Output | Chat Output 직접 연결 |
|------|--------------|-------|---------------------|
| PLL Guardrail | Agent / Language Model / PLL Guardrail / Moderation Guardrail | Response (파란) | ❌ — Language Model 또는 Agent 경유 |
| Moderation Guardrail | Agent / Language Model / PLL Guardrail / Moderation Guardrail | Response (파란) | ✅ 직접 연결 가능 |

> ⚠️ **KMS Retriever → Guardrail 연결 가능**  
> Guardrail Response(파란)는 KMS Retriever Query 포트에 연결 가능.  
> `LM(패스스루) → PLL Guardrail → KMS Retriever` 순서로 배치하면 개인정보 마스킹 후 검색 가능.

### 사내향 Guardrail 적용 기준

| 서비스 유형 | PLL | Moderation | 비고 |
|-----------|-----|-----------|------|
| 외부 고객 대응 | ✅ 필수 | ✅ 필수 | 입출력 이중 적용 |
| 사내 임직원 전용 | ✅ 권장 | ⚠️ 선택 | 내부 컴플라이언스 |
| 연구/분석 도구 | ⚠️ 선택 | ❌ 불필요 | 관대한 설정 |
| 시스템 간 자동화 | ❌ 불필요 | ❌ 불필요 | 사람 입력 없음 |
