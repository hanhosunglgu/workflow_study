# Guardrail 설계 원칙

**카테고리**: concepts  
**태그**: guardrail, 보안, PII, moderation, 안전레이어  
**최종 수정**: 2026-05-18  
**관련 페이지**: [[pll-guardrail]], [[moderation-guardrail]], [[port-color-rules]], [[flow-guardrail]]

---

## 두 Guardrail의 역할

| 노드 | 역할 | 파라미터 |
|------|------|---------|
| [[pll-guardrail]] | 개인정보(PII) 감지·마스킹 | 없음 (연결만으로 동작) |
| [[moderation-guardrail]] | 유해 콘텐츠 필터링 | Hate / SelfHarm / Sexual / Violence (슬라이더 1~7) |

슬라이더 의미: **1 = 가장 엄격 (거의 모두 차단)**, **7 = 가장 관대 (대부분 허용)**

---

## 연결 제약 (UI 검증 사실)

Guardrail 노드의 Input은 다음 4개만 연결 가능:
- Agent
- Language Model
- PLL Guardrail
- Moderation Guardrail

**Chat Input, Template Message, KMS Retriever 등은 직접 연결 불가.**

### 올바른 배치 패턴

```
✅ 권장:
Chat Input → Language Model → PLL Guardrail → Moderation Guardrail → KMS Retriever ...

✅ 또는:
Chat Input → Agent → PLL Guardrail → ...

❌ 잘못된 배치:
Chat Input → PLL Guardrail  (직접 연결 불가)
```

> ❓ 미확인: 실제 배포 환경에서 Chat Input → Language Model(dummy) → Guardrail 패턴이  
> 성능 측면에서 합리적인지 추가 검토 필요.

---

## 이중 Guardrail 패턴 (권장)

입력과 출력 양쪽에 적용:

```
[Chat Input]
     ↓
[Language Model 또는 Agent]  ← 입력 전처리
     ↓
[PLL Guardrail]              ← 입력 개인정보 마스킹
     ↓
[Moderation Guardrail]       ← 입력 유해 콘텐츠 차단
     ↓
[... 처리 노드 ...]
     ↓
[Moderation Guardrail]       ← 출력 유해 콘텐츠 재검사 (출력은 더 엄격하게)
     ↓
[Chat Output]
```

---

## 서비스 유형별 적용 기준

| 서비스 유형 | PLL | Moderation | 비고 |
|-----------|-----|-----------|------|
| 외부 고객 대응 | 필수 | 필수 | 입출력 이중 적용 |
| 사내 임직원 전용 | 권장 | 선택 | 내부 컴플라이언스 |
| 연구/분석 도구 | 선택 | 불필요 | 관대한 설정 |
| 시스템 간 자동화 | 불필요 | 불필요 | 사람 입력 없음 |

---

## Guardrail 실패 시 처리

> ❓ 미확인: 필터 통과 실패 시 플로우 중단 vs 에러 메시지 분기 동작 방식 스펙 확인 필요.  
> 권장 설계: 실패 시 Language Model("죄송합니다. 해당 질문에 답변드릴 수 없습니다.") → Chat Output

---

## Moderation 민감도 가이드

| 카테고리 | 고객 대응 (입력) | 고객 대응 (출력) | 사내 업무용 | 연구/분석용 |
|---------|---------------|---------------|-----------|-----------|
| Hate | 3 | 2 | 4 | 5 |
| SelfHarm | 2 | 1 | 3 | 4 |
| Sexual | 2 | 1 | 3 | 5 |
| Violence | 3 | 2 | 4 | 5 |
