# Human Approval / Human Choice 패턴

**카테고리**: concepts  
**태그**: human-in-the-loop, 승인, 분기, 안전  
**최종 수정**: 2026-05-18  
**관련 페이지**: [[human-approval]], [[human-choice]], [[flow-human-loop]], [[flow-security-agent]]

---

## Human Approval vs Human Choice 선택 기준

| 항목 | Human Approval | Human Choice |
|------|---------------|-------------|
| 결정 구조 | Yes / No (2가지) | 조건별 다중 선택 |
| 용도 | 중요 작업 직전 최종 확인 | 사용자가 직접 경로 선택 |
| 거부 시 | 전체 플로우 즉시 종료 | 해당 없음 (선택 후 진행) |
| else 처리 | 없음 | 토글 ON/OFF로 제어 |

---

## Human Approval 동작 방식

```
승인 시: → Human Approval 이후 노드 실행 → 정상 진행
거부 시: → 전체 플로우 즉시 종료 → 이후 노드 실행 없음
```

### 배치 원칙 — 비용/위험이 큰 작업 직전에 배치

```
✅ 외부 발송 (이메일, API 호출) 직전
✅ 데이터 변경/삭제 직전
✅ 금전 처리 직전

❌ 단순 조회 작업 전
❌ 내부 계산 작업 전
❌ 이미 Human Choice로 경로를 선택한 직후
```

### 승인 메시지 권장 포맷

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

---

## Human Choice else 토글 동작 (UI 검증)

`else 조건 기본 AI 메시지 사용` 토글 상태에 따라 else 출력 연결 가능 노드가 달라짐:

| 토글 상태 | 연결 가능 노드 |
|---------|-------------|
| **OFF** | Agent, Language Model, AI Router, Human Approval, Human Choice, KMS Retriever, Structured Output |
| **ON** | Chat Output, PLL Guardrail, Moderation Guardrail |

→ ON 상태에서는 AI가 직접 fallback 메시지를 생성하여 출력 또는 Guardrail로 전달.  
→ `<>` 버튼으로 Markdown 에디터에서 커스텀 fallback 메시지 작성 가능.

---

## 보안 Agent에서의 Human Approval 적용

Human Approval이 필수인 작업:
- 취약점 상태 변경 (SolidStep PATCH)
- 웹쉘 탐지 이벤트 처리 (MetiEye PATCH)
- Prisma CSPM 알림 해제 (Dismiss)
- 개인정보 파일 처리 (Server-i PATCH)

→ [[flow-security-agent]] 참조
