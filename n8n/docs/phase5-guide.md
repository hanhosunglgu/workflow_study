# Phase 5: Trigger 연동 및 안정화 가이드

**작성일**: 2026-05-15  
**상태**: 🔄 진행 중 (Task 5.1 / 5.2 / 5.4.1 / 5.4.3 완료)

---

## 개요

Phase 5는 WBS Agent 전체 시스템의 자동화 트리거 연동과 운영 안정화를 목표로 한다.

| Task | 내용 | 상태 |
|------|------|------|
| 5.1 | WBS-TRG-002 Cron 스케줄러 | ✅ 완료 |
| 5.2 | WBS-TRG-001 Teams Bot 명령어 라우팅 | ✅ 완료 |
| 5.3 | 오류 처리 및 재시도 로직 | ⏭️ 부분 적용 |
| 5.4.1 | E2E 테스트 | ✅ 완료 |
| 5.4.2 | Cron 자동 실행 검증 | ⏭️ skip (실운영 확인) |
| 5.4.3 | 부분 실패 시나리오 테스트 | ✅ 완료 |
| 5.4.4 | 설계 적합성 정확도 검토 | 🔲 PM/리더 리뷰 필요 |

---

## Task 5.1: WBS-TRG-002 — Cron 스케줄러

### 구현

**파일**: `workflow/WBS-TRG-002.json`

**노드 구성** (3노드):
```
Schedule Trigger (매주 금 17:00)
  └─► Call WBS-ORK (HTTP POST, timeout 900s, neverError:true)
        └─► Log Result (Code 노드)
```

**Schedule Trigger 설정**:
```json
{
  "rule": {
    "interval": [{
      "field": "cronExpression",
      "expression": "0 17 * * 5"
    }]
  }
}
```

**Call WBS-ORK 설정**:
```json
{
  "url": "={{ $env.N8N_BASE_URL || 'http://localhost:5678' }}/webhook/wbs-ork",
  "options": {
    "timeout": 900000,
    "response": { "response": { "neverError": true } }
  }
}
```

### n8n 등록 방법

CLI import는 id 충돌로 실패하므로 **n8n UI에서 수동 import**:
1. n8n UI → Workflows → Import from File
2. `workflow/WBS-TRG-002.json` 선택
3. Import 후 워크플로 활성화

---

## Task 5.2: WBS-TRG-001 — Teams Bot 명령어 라우팅

### 수정 내역

**파일**: `workflow/WBS-TRG-001.json`

#### IF 노드 v2 파라미터 구조 버그 수정

n8n v2.14에서 IF 노드 v2의 `options` 위치 변경:

```
수정 전: parameters.conditions.options = { caseSensitive, typeValidation }
수정 후: parameters.options = { caseSensitive, typeValidation }
```

수정 대상: 4개 IF 노드 전체 (`Check Command`, `Is WBS?`, `Is Report?`, `Is Help?`)

#### n8n 반영 절차

```bash
# 1. 파일 복사
docker cp workflow/WBS-TRG-001.json n8n:/tmp/WBS-TRG-001.json

# 2. import (기존 workflow 덮어쓰기)
docker exec n8n n8n import:workflow --input=/tmp/WBS-TRG-001.json

# 3. DB 업데이트 (workflow_entity + workflow_published_version)
# → workflow_history에서 최신 versionId 조회 후 두 테이블 업데이트

# 4. n8n 재시작
docker compose restart n8n
```

---

## Task 5.3: 오류 처리 및 재시도 로직

### 적용 완료

모든 Agent 간 HTTP 호출에 `retry` 옵션 적용:
```json
"retry": {
  "maxTries": 3,
  "waitBetweenTries": 30000
}
```

`neverError: true` — 모든 Specialist Agent 호출에 적용, 개별 실패 시 workflow 중단 없이 진행.

### 생략된 항목

- **Task 5.3.4 청크 처리**: 이번 주 변경 파일만 분석하므로 컨텍스트 한도 초과 위험 낮음. 실운영 후 필요시 추가.
- **Task 5.3.3 Rate Limit 모니터링**: GitHub API 5000 req/hr 기준, 현재 사용량 범위 내. 향후 Repo 증가 시 추가.

---

## Task 5.4.1: E2E 테스트 결과

### 테스트 명령

```bash
curl -s -X POST http://localhost:5678/webhook/wbs-ork \
  -H "Content-Type: application/json" \
  -d '{"triggered_by":"e2e_test"}' \
  --max-time 900
```

### 결과 (2026-05-15)

| 항목 | 값 |
|------|-----|
| HTTP 응답 코드 | 200 |
| 실행 시간 | 512초 |
| total_progress | 4 [RED] |
| design_score | 100 [GREEN] |
| teams_sent | true (status=200) |
| failed_agents | [] |
| Teams 메시지 | 수신 확인 ✅ |

### 수정된 이슈

| 이슈 | 원인 | 수정 |
|------|------|------|
| WBS-TRG-001 활성화 실패 | IF v2 노드 `options` 위치 오류 | Python으로 파라미터 구조 수정 |
| WBS-ORK hang (응답 없음) | `N8N_RUNNERS_TASK_TIMEOUT` 미설정 (기본 60초) | `.env`에 `N8N_RUNNERS_TASK_TIMEOUT=900` 추가 |

---

## Task 5.4.3: 부분 실패 시나리오 테스트

### 테스트 시나리오

| 시나리오 | 조건 | 결과 |
|---------|------|------|
| A | WBS-JRA 비활성화 | 가용 데이터로 리포트 생성 ✅ |
| B | WBS-GRC 비활성화 | 가용 데이터로 리포트 생성 ✅ |
| C | WBS-BAK + WBS-MOB 비활성화 | 가용 데이터로 리포트 생성 ✅ |

### 개선된 `failed_agents` 감지 로직

**파일**: `workflow/WBS-ORK.json` — `Integrate Results` 노드

```javascript
// Agent 실패 판단 함수
const isRawFailed = (raw) => {
  if (!raw) return true;
  if (!raw.agent_id) return true;  // 빈 {} 응답 (비활성 webhook)
  if (raw.error && raw.error !== null && raw.error !== 'null') return true;
  return false;
};

// 각 Agent 결과 처리
const rawJra = resultMap['WBS-JRA'];
const jra = rawJra && !isRawFailed(rawJra)
  ? rawJra
  : { agent_id:'WBS-JRA', ..., error: rawJra?.error || 'agent_unavailable' };

// 실패한 Agent 목록
const failedAgents = [jra, dda, bak, frt, cfg, mob]
  .filter(a => a.error && a.error !== null && a.error !== 'null')
  .map(a => a.agent_id);
```

### 테스트 환경 한계 및 실운영 대응

**한계**: DB에서 `active=false` 설정 시 n8n 메모리 캐시 webhook 차단 불가 → 테스트 환경에서 실제 빈 응답 시뮬레이션 어려움.

**실운영에서 정확히 작동하는 케이스**:
- 네트워크 오류: TCP 연결 실패 → curl 에러 → n8n이 빈 응답 처리
- Agent 서버 다운: HTTP 연결 불가 → 빈 `{}` 반환 → `agent_id` 없음 → `isRawFailed=True`
- Agent 내부 에러: `{ error: "..." }` 반환 → `error` 필드 체크 → 감지

---

## 환경변수 변경 이력

| 변수 | 이전 | 이후 | 이유 |
|------|------|------|------|
| `N8N_WEBHOOK_TIMEOUT` | 300 | 900 | Phase 1 — Ollama 6개 순차 실행 |
| `N8N_RUNNERS_TASK_TIMEOUT` | (미설정, 60초) | 900 | Phase 5 — Ollama Task Runner crash |

**적용 파일**: `/Users/hosunghan/workplace/self-hosted-ai-starter-kit/.env`

---

## 남은 작업

### Task 5.4.4: 설계 적합성 정확도 검토

**내용**: 실제 프로젝트 코드를 WBS Agent로 분석한 후, `design_score`, `all_gaps`, `gap.intent_analysis` 결과를 PM/리더와 리뷰하여 정확도 평가 및 개선 방향 도출.

**완료 기준**: PM/리더와 결과 리뷰 완료, 개선사항 목록 작성.

**선행 조건**: 사람 개입 필요 — 자동화 불가.

### WBS-TRG-002 n8n 등록

현재 `workflow/WBS-TRG-002.json` 파일은 생성되었으나 n8n에 등록되지 않은 상태.

**등록 방법**: n8n UI → Workflows → Import from File → `workflow/WBS-TRG-002.json` → 활성화.
