# 라우팅 패턴

**카테고리**: concepts  
**태그**: 라우팅, ai-router, human-choice, 분기  
**최종 수정**: 2026-05-18  
**관련 페이지**: [[ai-router]], [[human-choice]], [[flow-routing]], [[human-approval-pattern]]

---

## AI Router vs Human Choice

| 항목 | AI Router | Human Choice |
|------|-----------|-------------|
| 분기 결정자 | LLM이 자동 판단 | 사용자가 직접 선택 |
| 속도 | 빠름 (자동) | 느림 (사람 개입 대기) |
| 정확성 | LLM 판단 오류 가능 | 사용자 의도 명확 |
| 사용 상황 | 의도가 명확히 구분되는 경우 | 모호하거나 중요한 분기 |
| else 처리 | AI가 직접 답변 또는 else 경로 | 토글 ON/OFF로 동작 방식 선택 |

---

## AI Router 조건 작성 가이드

```
✅ 좋은 조건 (명확한 트리거):
"사용자 입력에 '계산', '수식', '%', '곱하기'가 포함된 경우"
"사용자 입력이 사내 정책이나 규정에 관한 질문인 경우"

❌ 나쁜 조건 (모호):
"중요한 질문인 경우"
"어려운 내용인 경우"
```

### Edit Conditions 구조

AI Router와 Human Choice 모두 동일:
- **Condition Name**: 조건 이름 (분기 레이블)
- **Condition Description**: LLM이 판단할 조건 설명

---

## 권장 분기 수

| 분기 수 | 평가 |
|--------|------|
| 2~3개 | 최적 — 명확, 오류 낮음 |
| 4~5개 | 적정 — 관리 가능 |
| 6개 이상 | 주의 — LLM 판단 오류 가능성 증가, Human Choice 병행 권장 |

---

## 계층적 조합 패턴 (권장)

```
[Chat Input]
     ↓
[AI Router] ──── 명확한 의도 → 자동 경로 실행
     │
     └── else (모호한 경우) → [Human Choice] ──── 사용자 선택 → 경로 실행
```

---

## else 조건 처리

- `else 조건 기본 AI 메시지 사용: ON` → 어느 조건도 해당 없을 때 LLM이 직접 답변 (fallback 안전망)
- `else 조건 기본 AI 메시지 사용: OFF` → else 경로로 연결된 노드가 처리
- **권장**: ON 설정으로 fallback 확보

---

## 통합 업무 라우터 예시 (사내향 Top 1 플로우)

```
[Chat Input]
     ↓
[Language Model]  ← ⚠️ 패스스루: Chat Input은 PLL Guardrail에 직접 연결 불가
     ↓
[PLL Guardrail]
     ↓
[AI Router]
  ├─ 문서/정책/사규    → KMS Retriever → Document Formatter → Language Model
  ├─ 계산/수치         → Agent + Simple Calculator Tool
  ├─ 통계/데이터       → Agent + KOSIS Statistics Tool + Calculator
  ├─ 웹 검색/최신 정보 → Agent + Web Search Tool + Youtube Search Tool
  └─ else(OFF)         → Language Model (일반 대화)
                              ↓
                         [Chat Output]
```

> ⚠️ AI Router else → Chat Output 직접 연결 불가 (else 토글 OFF 기준). Language Model 경유 필수.  
> → [[guardrail-design]], [[port-color-rules]] 참조
