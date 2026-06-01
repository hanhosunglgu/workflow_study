# Phase 4 가이드 — WBS-RPT (Report Agent)

**작성일**: 2026-05-14  
**대상**: Phase 3(WBS-ORK) 완료 후 Teams 리포트 출력 구현

---

## 1. 구현 완료 사항

### 1.1 WBS-RPT Workflow (`workflow/WBS-RPT.json`)

| 노드 ID | 노드명 | 역할 |
|---------|--------|------|
| rpt-0001 | Webhook | POST /webhook/wbs-rpt 수신 |
| rpt-0002 | Build Report Data | ORK 출력 파싱, 메시지 텍스트 조립, 미완료 티켓 5건 처리 |
| rpt-0003 | Build Teams Card | Adaptive Card v1.0 payload 구성 (`TextBlock + FactSet`) |
| rpt-0004 | Send Teams Message | TEAMS_WEBHOOK_URL로 POST |
| rpt-0006 | Check Teams Result | 전송 성공/실패 판정 |
| rpt-0010 | Build Final Summary | 최종 응답 구성 |
| rpt-0011 | Respond to Webhook | 200 응답 |

> 노드 rpt-0005, rpt-0007, rpt-0008, rpt-0009 (Confluence 관련)는 워크플로우 내에 존재하나 비연결 상태.

### 1.2 WBS-ORK 변경 (`workflow/WBS-ORK.json`)

- **노드 추가**: `Call WBS-RPT` (ork-0026) — Calc Progress Score 이후 병렬 분기
- **연결 추가**: Calc Progress Score → Call WBS-RPT (기존 Respond + Log에 추가)

---

## 2. n8n 등록 절차

### 2.1 WBS-RPT Workflow 등록

1. n8n UI → Workflows → Import from File
2. `workflow/WBS-RPT.json` 업로드
3. **Activate** 토글 ON
4. Webhook URL 확인: `http://localhost:5678/webhook/wbs-rpt`

### 2.2 WBS-ORK Workflow 재등록

1. 기존 WBS-ORK Workflow 비활성화
2. `workflow/WBS-ORK.json` 재업로드 (또는 노드 수동 추가)
3. Activate

### 2.3 환경변수 설정 (`.env`)

```env
# Teams Workflows Webhook URL
# 설정: Teams 채널 → 워크플로 앱 → "채널에 웹후크 알림 보내기" 템플릿 → URL 복사
TEAMS_WEBHOOK_URL=https://prod-xx.westus.logic.azure.com/<your_url>
```

> 참고: `doc/env-setup.md` 섹션 5 참조

---

## 3. Teams 메시지 형식

### 3.1 전송 포맷 (Power Automate Webhook 호환)

Power Automate 흐름이 `triggerBody()?['attachments']` 배열을 읽어 `For each → @item()?['content']`로 카드를 게시한다.

```json
{
  "attachments": [{
    "contentType": "application/vnd.microsoft.card.adaptive",
    "content": { "type": "AdaptiveCard", "version": "1.0", "body": [...] }
  }]
}
```

### 3.2 Adaptive Card 제약사항 (Teams)

| 요소 | 지원 여부 |
|------|----------|
| `TextBlock` | ✅ 지원 |
| `FactSet` | ✅ 지원 |
| `ColumnSet` / `Column` | ❌ 미지원 (BadRequest) |
| `Table` / `TableRow` / `TableCell` | ❌ 미지원 (BadRequest) |
| Card version `1.0` | ✅ 권장 (최대 호환) |
| Card version `1.4` | ❌ 미지원 환경 있음 |

### 3.3 메시지 구조 (Adaptive Card 섹션)

```
[TextBlock] 📊 WBS Agent 주간 개발 진척률 리포트
[TextBlock] 📅 2026-05-11 (월) ~ 2026-05-14 (금)
[TextBlock] 🎯 전체 진척률: 73% 🟡 주의  |  🔍 설계 적합성: 87% 🟢 정상
[TextBlock] 📋 Jira 티켓 현황
[FactSet]   전체:12개 / 완료:6개 / 진행중:4개 / 미착수:2개 / SP:24/40
[TextBlock] 💻 GitHub 활동
[FactSet]   Commit:23회 / 활성 개발일:4/5일
[TextBlock] 📌 미완료 티켓  (있는 경우)
[TextBlock] • [WBS-45] 로그인 API 구현 (In Progress, 홍길동)
[TextBlock] 🔍 설계 Gap  (있는 경우)
[TextBlock] • WBS-MOB: POST /api/auth/login
[TextBlock] ⚠️ 데이터 미수집  (있는 경우)
```

### 3.2 미완료 티켓 처리 규칙

- WBS-ORK의 `incomplete_tickets[]` 배열 기준
- 최대 5건 표시 → 초과 시 "외 N건" 문구 추가

---

## 4. 테스트 방법

### 4.1 단독 테스트 (ORK 없이 직접 호출)

```bash
curl -X POST http://localhost:5678/webhook/wbs-rpt \
  -H "Content-Type: application/json" \
  -d '{
    "week_start": "2026-05-11",
    "week_end": "2026-05-15",
    "total_progress": 73,
    "progress_grade": "YELLOW",
    "design_score": 87,
    "design_grade": "YELLOW",
    "total_tickets": 12,
    "done_tickets": 6,
    "in_progress_tickets": 4,
    "todo_tickets": 2,
    "sp_total": 40,
    "sp_burned": 24,
    "sp_burned_rate": 60,
    "total_commits": 23,
    "max_active_days": 4,
    "gap_count": 5,
    "high_gap_count": 1,
    "medium_gap_count": 2,
    "low_gap_count": 2,
    "all_gaps": [
      {"severity": "high", "source_agent": "WBS-BAK", "item": "POST /api/user/register", "description": "파라미터 스펙 변경"}
    ],
    "incomplete_tickets": [
      {"key": "PROJ-45", "summary": "로그인 API 구현", "status": "In Progress", "assignee": "홍길동"},
      {"key": "PROJ-48", "summary": "단위 테스트 작성", "status": "To Do", "assignee": null}
    ],
    "failed_agents": []
  }'
```

### 4.2 기대 결과

```json
{
  "agent_id": "WBS-RPT",
  "teams_sent": true,
  "teams_status": 200,
  "confluence_updated": false,
  "confluence_skipped": true,
  "confluence_error": null,
  "error": null
}
```

### 4.3 통합 테스트 (ORK → RPT 전체 흐름)

```bash
curl -X POST http://localhost:5678/webhook/wbs-ork \
  -H "Content-Type: application/json" \
  -d '{}'
```

Teams 채널에 메시지 수신 확인.

---

## 5. 알려진 제한 및 주의사항

| 항목 | 내용 |
|------|------|
| Adaptive Card 요소 제한 | Teams는 `Table`, `ColumnSet` 미지원 → `TextBlock + FactSet`만 사용 |
| Card 버전 | `version: '1.0'` 고정 — 높은 버전은 일부 Teams 환경에서 `unsupported card element` 오류 |
| teams_status: 200 ≠ 전송 성공 | Power Automate Webhook은 항상 200 반환. 실제 성공 여부는 Power Automate 실행 이력 확인 필요 |
| TEAMS_WEBHOOK_URL | `.env` 설정 후 `docker compose up -d n8n` 필수 (`restart`만으로는 환경변수 미적용) |
| Teams 메시지 길이 | 매우 긴 메시지는 Teams에서 잘릴 수 있음 |
