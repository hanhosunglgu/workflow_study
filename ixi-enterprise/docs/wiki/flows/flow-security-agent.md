# 보안 통합 Agent 플로우

**카테고리**: flows  
**태그**: 보안, mock서버, human-approval, 사내시스템  
**최종 수정**: 2026-05-18  
**관련 페이지**: [[human-approval-pattern]], [[api-request]], [[agent]], [[flow-agent-tool]]

---

## 개요

ixi-enterprise 2-2 사내 시스템 연동 Agent 패턴 기반.  
5개 보안 솔루션을 통합 조회·상태 변경하는 AI Agent.  
실제 솔루션 대신 **Python FastAPI Mock 서버**로 개발·검증.

---

## 연동 대상 솔루션

| 솔루션 | 카테고리 | 포트 | 인증 |
|--------|---------|------|------|
| SolidStep | CCE 취약점 진단 | 8001 | API Key: `ss-test-key-001` |
| MetiEye | 웹쉘 탐지/차단 | 8002 | API Key: `me-test-key-001` |
| Prisma CSPM | 클라우드 보안 태세 | 8003 | JWT (POST /login) |
| CCE | KISA 취약점 기준 관리 | 8004 | API Key: `cce-test-key-001` |
| Server-i | 서버 DLP / 개인정보 보호 | 8005 | API Key: `si-test-key-001` |

---

## 플로우 구성

```
[API Request Tool] × 5  ← Tool Mode ON (빨간 Tool 포트 → Agent Tools에 연결)
  SolidStep :8001 / MetiEye :8002 / Prisma :8003 / CCE :8004 / Server-i :8005

[Chat Input]
     ↓
[Agent]
  Model: azure_openai:gpt-4.1-mini
  System Prompt: 통합 보안 어시스턴트
  Tools: 위 5개 API Request Tool
     ↓ (상태 변경 작업 시)
[Human Approval]  ← 상태 변경 시에만 배치
     ↓ (승인 시)
[Agent]  ← ⚠️ Human Approval → Chat Output 직접 연결 불가
            "승인된 작업을 실행하고 결과를 요약하세요"
     ↓
[Chat Output]

거부 시: 플로우 즉시 종료
```

> ⚠️ **Human Approval → Chat Output 직접 연결 불가** (양방향 모두): Agent 또는 Language Model 경유 필수.  
> ⚠️ **API Request Tool Mode**: 토글 ON 상태에서만 Tool 출력(빨간)이 Agent Tools 포트에 연결 가능.  
> → [[human-approval-pattern]] 참조

---

## Human Approval 적용 기준

| 작업 | Human Approval |
|------|---------------|
| 취약점 상태 변경 (OPEN → IN_PROGRESS 등) | ✅ 필수 |
| 웹쉘 탐지 이벤트 처리 (CONFIRM_THREAT, DELETE_FILE) | ✅ 필수 |
| Prisma CSPM 알림 해제 (Dismiss) | ✅ 필수 |
| 개인정보 파일 처리 (MASK, DELETE, ENCRYPT) | ✅ 필수 |
| 취약점/탐지 목록 조회 | ❌ 불필요 |
| 컴플라이언스 현황 조회 | ❌ 불필요 |

---

## Human Approval 메시지 포맷

```
📋 변경 내용 확인
─────────────────────────
시스템: [솔루션명]
대상: [ID / 서버명 / 파일명]
작업: [변경 내용]
사유: [AI가 분석한 요청 사유]
─────────────────────────
⚠️ 승인 시 즉시 실행됩니다.
```

---

## Mock 서버 구조

```
ixi-enterprise/mock-servers/
├── common/auth.py, models.py
├── solidstep/main.py (8001), routes.py, seed_data.py
├── metieye/main.py (8002), routes.py, seed_data.py
├── prisma_cspm/main.py (8003), routes.py, seed_data.py
├── cce/main.py (8004), routes.py, seed_data.py
└── server_i/main.py (8005), routes.py, seed_data.py
```

실행:
```bash
uvicorn solidstep_mock:app --port 8001 --reload
```

---

## Prisma CSPM 특이사항

> ⚠️ JWT 인증: POST /login → Bearer Token 발급 (유효기간 10분)  
> n8n에서 JWT 자동 갱신 로직 구현 필요 — [[n8n-mapping]] 미확인 사항

---

## 구현 로드맵

| Phase | 기간 | 목표 |
|-------|------|------|
| Phase 1 | 1~2일 | Mock 서버 + 조회 API + n8n Agent 연동 |
| Phase 2 | 1~2일 | PATCH API + Human Approval 연결 |
| Phase 3 | 선택 | Guardrail, 리포트 자동생성, JWT 갱신 처리 |
