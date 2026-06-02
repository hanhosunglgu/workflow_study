# 플로우 카테고리 1: RAG / 지식 검색 기반

**작성일**: 2026-05-15  
**최종 수정**: 2026-05-18 (01-node-catalog.md UI 검증 결과 반영)  
**포함 플로우**: 1-1 문서 Q&A 챗봇 / 1-2 문서 요약+구조화 추출 / 1-3 멀티 KMS 비교 분석

---

## 1-1. 문서 Q&A 챗봇

### 개요

| 항목 | 내용 |
|------|------|
| 난이도 | ⭐ 쉬움 |
| 핵심 노드 | Chat Input → KMS Retriever → Document Formatter → Language Model → Chat Output |
| 구현 예상 시간 | 0.5일 |
| 현재 상태 | ✅ 개발 버전 동작 중 |

### 플로우 구성도

```
[Chat Input]
     │ User Message
     ▼
[KMS Retriever]
  Query: 사용자 입력 원문
  Knowledge: 대상 지식베이스 선택
     │ Documents
     ▼
[Document Formatter]
  검색된 청크 → 프롬프트 삽입 가능한 문자열로 변환
     │ Result
     ▼
[Language Model]
  System Prompt: "아래 문서를 바탕으로 질문에 답변하세요."
  Model: azure_openai:gpt-4.1-mini
     │ Response
     ▼
[Chat Output]
```

### 사내 활용 예시

| 활용 분야 | 예시 질문 |
|----------|----------|
| 사규/정책 검색 | "연차 휴가 규정이 어떻게 되나요?" |
| 제품 매뉴얼 Q&A | "장치 초기화 방법을 알려주세요" |
| 회의록 검색 | "지난 주 회의에서 결정된 사항이 뭔가요?" |
| 계약서 검토 | "이 계약서의 해지 조건이 뭔가요?" |

### 개선 포인트

- **Query Rewriting 추가**: 대화체 질문을 검색 최적화 쿼리로 변환
  ```
  Chat Input → Language Model (쿼리 재작성) → KMS Retriever → ...
  ```
- **멀티턴 대화**: Agent에 별도 context 포트가 없으므로 MCP 메모리 Tool 또는 외부 세션 관리 방식 검토 필요

---

## 1-2. 문서 요약 + 구조화 추출

### 개요

| 항목 | 내용 |
|------|------|
| 난이도 | ⭐⭐ 보통 |
| 핵심 노드 | Chat Input → KMS Retriever → Document Formatter → Language Model → Structured Output → JSON Output |
| 구현 예상 시간 | 0.5~1일 |
| 현재 상태 | 🔲 미구현 |

### 플로우 구성도

```
[Chat Input]
     │ User Message ("이 문서 요약해줘")
     ▼
[KMS Retriever]
  Knowledge: 대상 지식베이스
     │ Documents (주황)
     ▼
[Document Formatter]
     │ Result (초록)
     ▼
[Language Model]
  System Prompt: "아래 문서를 바탕으로 요청한 정보를 추출하세요."
  Model: azure_openai:gpt-4.1-mini
     │ Response (파란)
     ▼
[Structured Output]    ← JSON 구조화 추출
  스키마 이름: document_summary (영문+숫자+_만 허용 — 한글/공백 시 Error 400)
  속성: title(String), summary(String),
        key_points(Array), action_items(Array), keywords(Array)
  Model: azure_openai:gpt-4.1-mini
     │ Result (주황)
     ▼
[JSON Output]          ← JSON 구조화 출력 (Chat Output과 상호 배타적)
```

> ⚠️ **JSON Output ↔ Chat Output 상호 배타적 (2026-05-18 확인)**  
> 플로우에 JSON Output을 추가하면 Chat Output이 비활성화됨. 동시 사용 불가.  
> 구조화 추출(JSON Output)과 채팅 출력(Chat Output)이 모두 필요하면 **별도 플로우로 분리**할 것.
>
> ⚠️ **Structured Output → Document Formatter 연결 금지**  
> 포트 색상이 동일(주황)해도 데이터 타입이 다름.  
> Structured Output Result는 JSON 문자열, Document Formatter는 KMS Retriever의 Document 객체 배열을 기대함.  
> 연결 시 `'str' object has no attribute 'page_content'` 런타임 오류 발생.

### 사내 활용 예시

| 활용 분야 | 추출 스키마 |
|----------|-----------|
| 회의록 요약 | `{ summary, decisions[], action_items[], attendees[] }` |
| 보고서 요약 | `{ title, summary, key_points[], recommendations[] }` |
| 계약서 분석 | `{ parties[], terms[], penalties[], expiry_date }` |
| 제안서 검토 | `{ overview, budget, timeline, risks[] }` |

### 1-1과의 차이점

| 항목 | 1-1 문서 Q&A | 1-2 구조화 추출 |
|------|-------------|----------------|
| 출력 노드 | Chat Output | JSON Output only (Chat Output 사용 불가) |
| 출력 형태 | 자유 텍스트 응답 | 구조화된 JSON 데이터 |
| LM 위치 | KMS → DocFormatter → **LM** → Chat Output | KMS → DocFormatter → **LM** → Structured Output → JSON Output |
| 용도 | 대화형 질의응답 | 데이터 추출 및 저장 |
| 후처리 | 불필요 | 추출된 JSON을 DB 저장 가능 |

---

## 1-3. 멀티 KMS 비교 분석

### 개요

| 항목 | 내용 |
|------|------|
| 난이도 | ⭐⭐ 보통 |
| 핵심 노드 | Chat Input → KMS Retriever×2 → Document Formatter → Language Model → Chat Output |
| 구현 예상 시간 | 1일 |
| 현재 상태 | 🔲 미구현 |

### 플로우 구성도

```
[Chat Input]
     │ User Message ("두 문서를 비교해줘")
     ├────────────────────────────────────┐
     ▼                                   ▼
[KMS Retriever A]               [KMS Retriever B]
  Knowledge: 지식베이스 A          Knowledge: 지식베이스 B
  (예: 구 버전 사규)               (예: 신 버전 사규)
     │ Documents A                       │ Documents B
     ▼                                   ▼
[Document Formatter A]          [Document Formatter B]
     │ Result A                          │ Result B
     └────────────────┬──────────────────┘
                      ▼
              [Language Model]
  System Prompt:
    "아래 두 문서를 비교하여 차이점을 정리하세요.
     [문서 A]: {{ Result A }}
     [문서 B]: {{ Result B }}"
  Model: azure_openai:gpt-4.1-mini
                      │ Response
                      ▼
               [Chat Output]
```

### 사내 활용 예시

| 활용 분야 | 지식베이스 A | 지식베이스 B |
|----------|------------|------------|
| 정책 개정 비교 | 구 사규 | 신 사규 |
| 계약서 버전 비교 | 초안 계약서 | 최종 계약서 |
| 제품 스펙 비교 | v1.0 매뉴얼 | v2.0 매뉴얼 |
| 경쟁사 분석 | 자사 제품 문서 | 경쟁사 제품 문서 |

### 구현 시 주의사항

- KMS Retriever 두 개의 결과를 하나의 Language Model에 합산하는 방식으로 연결
- 두 문서의 컨텍스트 길이 합산이 LLM 컨텍스트 윈도우 초과 가능 → 청크 수(`top_k`) 조정 필요
- 비교 기준을 System Prompt에 명확히 지정할 것 (차이점 위주, 공통점 위주 등)

---

## RAG 플로우 공통 설계 원칙

### KMS 검색 품질 향상 팁

```
1. top_k 설정
   - 단순 Q&A: top_k = 3~5
   - 요약/분석: top_k = 7~10 (더 많은 청크 참조)

2. Query 전처리
   - 짧은 키워드보다 완전한 문장이 검색 정확도 높음
   - "연차" 보다 "연차 휴가 일수와 신청 방법을 알고 싶습니다" 가 더 정확

3. Document Formatter 역할
   - 단순 텍스트 연결이 아닌 출처 정보(문서명, 페이지) 포함 권장
   - "[출처: 사규_2026.pdf] 내용..." 형태로 포매팅
```

### 공통 System Prompt 패턴

```
Role: 당신은 [회사명] 사내 문서 전문 AI 어시스턴트입니다.

규칙:
1. 반드시 제공된 문서 내용을 바탕으로만 답변하세요.
2. 문서에 없는 내용은 "해당 내용을 문서에서 찾을 수 없습니다"라고 답변하세요.
3. 답변은 한국어로 작성하세요.
4. 출처 문서명을 답변 하단에 명시하세요.

[참고 문서]
{{ document_context }}
```
