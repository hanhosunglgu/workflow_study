# Phase 2 — 진척률 수집 개발 내역 및 테스트 결과

**완료일**: 2026-05-14  
**대상 워크플로**: WBS-JRA (신규), WBS-GRC (확장)

---

## 목차

1. [개요](#개요)
2. [Task 2.1 — WBS-JRA Jira Agent](#task-21--wbs-jra-jira-agent)
3. [Task 2.2 — WBS-GRC Commit 집계 확장](#task-22--wbs-grc-commit-집계-확장)
4. [환경변수 및 인프라 변경](#환경변수-및-인프라-변경)
5. [발생 이슈 및 해결](#발생-이슈-및-해결)
6. [테스트 결과](#테스트-결과)

---

## 개요

Phase 2 목표: 스프린트 진척률 데이터를 자동으로 수집한다.

| 항목 | 내용 |
|------|------|
| Jira Sprint 현황 | 활성 Sprint 티켓 상태(해야 할 일/진행 중/완료) 집계 |
| Story Point 소진률 | 완료 SP / 전체 SP × 100 |
| Commit 메시지 매핑 | GitHub Commit → Jira 티켓 키 연결 |
| Commit/PR 집계 | 이번 주(월~금) 커밋 수, 활성 개발일, Merge PR 수 |

Phase 2 완료 후 WBS-ORK(Orchestration)가 두 Agent를 모두 호출하여 진척률 지표를 통합한다.

---

## Task 2.1 — WBS-JRA Jira Agent

### 워크플로 기본 정보

| 항목 | 값 |
|------|----|
| 파일 | `workflow/WBS-JRA.json` |
| Webhook 경로 | `POST /webhook/wbs-jra` |
| 노드 수 | 13개 |
| 입력 파라미터 | `board_id`, `commit_messages[]` (선택) |

### 노드 구성 (13개)

```
Webhook
  └─ Init Params
       └─ GET Active Sprint
            └─ Extract Sprint ID
                 └─ Init Pagination
                      └─ Pagination Loop (SplitInBatches)
                           ├─ [Done] → Build Output
                           │              └─ Map Commits to Jira
                           │                   └─ Respond to Webhook
                           └─ [Loop] → GET Sprint Issues
                                         └─ Accumulate Issues
                                              └─ Has More Pages? (IF)
                                                   ├─ [Yes] → Pagination Loop
                                                   └─ [No]  → Aggregate Status
                                                                └─ Pagination Loop
```

### 핵심 노드별 역할

#### Init Params
환경변수 및 요청 파라미터를 초기화한다.

```javascript
const boardId = body.board_id || $env.JIRA_BOARD_ID || '8207';
const baseUrl  = body.base_url  || $env.JIRA_BASE_URL;
const commitMessages = body.commit_messages || [];
```

#### GET Active Sprint
Jira Agile REST API로 Board의 Sprint 목록을 조회한다.

```
GET /rest/agile/1.0/board/{boardId}/sprint?maxResults=50
```

> **주의**: `?state=active` 필터는 Board type이 `simple`인 경우 동작하지 않는다. 전체 조회 후 코드에서 `state === 'active'`로 필터링한다.

#### Extract Sprint ID
조회된 Sprint 배열에서 active 상태 Sprint를 추출한다.

```javascript
const sprints = allSprints.filter(s => s.state === 'active');
if (!sprints.length) {
  throw new Error('활성 Sprint가 없습니다. Board ID: ' + boardId);
}
```

#### Pagination Loop + GET Sprint Issues
Sprint 이슈를 100개씩 페이지네이션으로 전체 조회한다.

```
GET /rest/agile/1.0/sprint/{sprintId}/issue?startAt=0&maxResults=100
```

`hasMore = (nextStart < total && issues.length > 0)` 조건으로 루프를 제어한다.

#### Aggregate Status
이슈 상태를 집계한다. 한글 상태명(`완료`, `진행 중`, `해야 할 일`)과 영문 상태명 모두 처리한다.

```javascript
const isDone = cat === 'done' || cat === '완료' || s === 'done' || s === '완료';
const isInProgress = cat === 'indeterminate' || cat === '진행 중' || s === '진행 중';
const isTodo = cat === 'new' || cat === '해야 할 일' || s === '해야 할 일' || s === 'to do';
```

#### Map Commits to Jira
commit_messages 배열에서 Jira 키(`[A-Z][A-Z0-9]+-\d+`)를 정규식으로 추출하여 티켓별로 그룹핑한다.

```javascript
const keyPattern = /\b([A-Z][A-Z0-9]+-\d+)\b/g;
```

### 출력 스키마

```json
{
  "agent_id": "WBS-JRA",
  "repo": "jira",
  "repo_type": "jira",
  "sprint_id": 15902,
  "sprint_name": "WBS 1 스프린트",
  "sprint_start_date": "2026-05-14T00:00:00.000Z",
  "sprint_end_date": "2026-05-28T00:00:00.000Z",
  "total_tickets": 4,
  "done": 0,
  "in_review": 0,
  "in_progress": 2,
  "todo": 2,
  "sp_total": 0,
  "sp_burned": 0,
  "sp_burned_rate": 0,
  "ticket_done_rate": 0,
  "done_tickets": [],
  "incomplete_tickets": ["WBS-2 회원가입 API 구현", "WBS-3 프론트엔드 로그인 화면"],
  "jira_commit_map": {
    "WBS-2": ["WBS-2 회원가입 API 엔드포인트 추가", "WBS-2 validation 로직 수정"],
    "WBS-3": ["WBS-3 로그인 화면 UI 구현"]
  },
  "linked_ticket_count": 3,
  "orphan_commit_keys": [],
  "no_commit_issues": ["WBS-5"],
  "error": null
}
```

---

## Task 2.2 — WBS-GRC Commit 집계 확장

### 변경 개요

기존 WBS-GRC(10노드, Repo 분류만 수행)에 Commit/PR 집계 기능 6개 노드를 추가하여 16노드 워크플로로 확장했다.

| 구분 | 노드 수 | 주요 기능 |
|------|---------|-----------|
| 기존 (Phase 1) | 10 | Repo 분류 (frontend/backend/config/mobile) |
| 추가 (Phase 2) | +6 | Commit 집계, PR 집계, 병렬 처리, 결과 병합 |

### 추가된 노드 (6개)

| 노드명 | 역할 |
|--------|------|
| GET Commits This Week | GitHub API로 이번 주(월~금) 커밋 목록 조회 |
| GET Merged PRs | 이번 주 Merge된 PR 목록 조회 |
| Aggregate Commits | 커밋 수, 활성 개발일, 커밋 메시지 집계 |
| Aggregate PRs | Merge PR 수 집계 |
| Merge Commit & PR | 두 결과를 하나로 병합 (numberInputs: 2) |
| Build Repo Stats | 최종 Repo 통계 데이터 구성 |

### 병렬 처리 구조

Attach Repo Info 노드에서 두 경로로 분기하여 Commit API와 PR API를 동시에 호출한다.

```
Attach Repo Info
  ├─ [index 0] → GET Commits This Week → Aggregate Commits ─┐
  └─ [index 1] → GET Merged PRs        → Aggregate PRs     ─┴→ Merge → Build Repo Stats → Loop Over Repos
```

### 이번 주 날짜 계산 로직

```javascript
const dayOfWeek = now.getUTCDay();
const daysFromMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
const monday = new Date(now);
monday.setUTCDate(now.getUTCDate() - daysFromMonday);
monday.setUTCHours(0, 0, 0, 0);
// since = monday ISO8601, until = now ISO8601
```

### 활성 개발일 계산

커밋 날짜에서 평일(월~금)만 추출하여 중복 제거 후 카운트한다.

```javascript
const activeDays = new Set(
  commits
    .filter(c => {
      const d = new Date(c.commit.author.date);
      const day = d.getUTCDay();
      return day >= 1 && day <= 5; // 월~금
    })
    .map(c => c.commit.author.date.substring(0, 10))
);
```

### 추가 출력 필드

WBS-GRC 기존 출력에 다음 필드가 추가됐다.

```json
{
  "commit_stats": {
    "WBS_Check": {
      "commit_count": 8,
      "active_days": 1,
      "merged_pr_count": 0,
      "commit_messages": ["feat: login API", "..."]
    }
  },
  "total_commit_count": 8,
  "max_active_days": 1,
  "all_commit_messages": ["feat: login API", "..."]
}
```

---

## 환경변수 및 인프라 변경

### .env 추가 항목

`/Users/hosunghan/workplace/self-hosted-ai-starter-kit/.env`에 9개 변수 추가:

```env
GITHUB_OWNER=hanhosunglgu
GITHUB_REPOS=["WBS_Check"]
JIRA_BASE_URL=https://lgucorp.atlassian.net
JIRA_PROJECT_KEYS=["WBS"]
JIRA_BOARD_ID=8207
DESIGN_DOC_REPO=hanhosunglgu/WBS_Check
DESIGN_DOC_PATH=WBS_Check/docs/design
```

### docker-compose.yml 추가 항목

`x-n8n` 서비스 블록에 9개 환경변수 pass-through 추가:

```yaml
- GITHUB_OWNER
- GITHUB_REPOS
- JIRA_BASE_URL
- JIRA_PROJECT_KEYS
- JIRA_BOARD_ID
- DESIGN_DOC_REPO
- DESIGN_DOC_PATH
```

### $vars → $env 전역 마이그레이션

n8n Community plan은 Variables 기능을 지원하지 않는다. 8개 워크플로 파일의 `$vars.` 참조를 `$env.`로 전면 교체했다.

```bash
# 적용 명령
sed -i '' 's/\$vars\./\$env./g' workflow/*.json
```

대상 파일: WBS-GRC, WBS-JRA, WBS-BAK, WBS-FRT, WBS-CFG, WBS-MOB, WBS-DDA, WBS-INT

### 컨테이너 재생성

`.env` 변경사항 적용을 위해 `docker compose restart` 대신 `docker compose up -d`로 컨테이너를 재생성했다.

```bash
cd /Users/hosunghan/workplace/self-hosted-ai-starter-kit
docker compose up -d n8n
```

> `restart`는 기존 컨테이너 설정을 유지하므로 환경변수 변경이 반영되지 않는다.

---

## 발생 이슈 및 해결

### 이슈 1: `$vars` 참조 오류

| 항목 | 내용 |
|------|------|
| 증상 | Init Params 노드 실행 시 `$vars.JIRA_BOARD_ID` 참조 오류 |
| 원인 | n8n Community plan은 Variables 기능 미지원 |
| 해결 | 전체 워크플로의 `$vars.` → `$env.` 교체 + .env + docker-compose.yml 업데이트 |

### 이슈 2: Active Sprint 조회 실패 (Board type: simple)

| 항목 | 내용 |
|------|------|
| 증상 | `GET /sprint?state=active` 가 빈 배열 반환 |
| 원인 | Board type이 `simple`이면 `?state=active` 쿼리 파라미터가 동작하지 않음 |
| 해결 | `?state=active` 제거 → 전체 Sprint 조회 후 JavaScript 코드에서 `state === 'active'` 필터링 |

### 이슈 3: 한글 상태명 매핑 실패

| 항목 | 내용 |
|------|------|
| 증상 | `in_progress: 0, todo: 0` — 모든 상태 카운트가 0 |
| 원인 | Jira 프로젝트 상태명이 한글(`진행 중`, `해야 할 일`, `완료`)로 설정됨 |
| 해결 | Aggregate Status 노드에 한글 상태명 매핑 조건 추가 |

### 이슈 4: Story Points 필드 미존재

| 항목 | 내용 |
|------|------|
| 증상 | `sp_total: 0`, `customfield_10016: null` |
| 원인 | WBS 프로젝트의 이슈 스크린에 Story Points 필드가 활성화되지 않음 |
| 해결 | Jira 프로젝트 관리자 설정 필요 (이슈 스크린에 `customfield_10016` 추가). SP 없이 티켓 상태 집계만으로 테스트 완료 처리 |

### 이슈 5: Jira 이슈 생성 시 커스텀 필드 설정 불가

| 항목 | 내용 |
|------|------|
| 증상 | `customfield_10016`, `customfield_10020` — "Field cannot be set. It is not on the appropriate screen" |
| 원인 | 이슈 생성 API에서 SP/Sprint 필드를 직접 설정하려면 해당 필드가 Create 스크린에 추가되어 있어야 함 |
| 해결 | 이슈 생성 → Sprint 추가(`POST /rest/agile/1.0/sprint/{id}/issue`) → SP 업데이트(`PUT /rest/api/3/issue/{key}`) 순서로 분리 |

### 이슈 6: 이슈 타입 ID 불일치

| 항목 | 내용 |
|------|------|
| 증상 | `issuetype: "선택한 이슈 유형이 올바르지 않습니다."` |
| 원인 | WBS 프로젝트의 실제 Story ID는 `19542`, Task ID는 `19540`. 범용 ID(`10001`, `10003`) 사용 불가 |
| 해결 | `GET /rest/api/3/project/WBS/statuses` API로 실제 ID 확인 후 하드코딩 |

---

## 테스트 결과

### 테스트 환경

| 항목 | 값 |
|------|----|
| n8n | v2.14.2 Self-hosted (Docker) |
| Jira | lgucorp.atlassian.net, 프로젝트: WBS, Board: 8207 |
| Sprint | WBS 1 스프린트 (id:15902, 2026-05-14 ~ 2026-05-28) |
| 테스트 이슈 | WBS-2(진행 중), WBS-3(진행 중), WBS-4(해야 할 일), WBS-5(해야 할 일) |

### Step 1: WBS-GRC 단독 테스트

```bash
curl -s -X POST http://localhost:5678/webhook/wbs-grc \
  -H "Content-Type: application/json" \
  -d '{"owner": "hanhosunglgu", "repos": ["WBS_Check"]}'
```

| 검증 항목 | 기대값 | 실제값 | 결과 |
|-----------|--------|--------|------|
| frontend 분류 | WBS_Check | ['WBS_Check'] | ✅ |
| commit_count | >0 | 8 | ✅ |
| active_days | >0 | 1 | ✅ |
| error | null | null | ✅ |

**판정: PASS**

### Step 2: WBS-JRA 단독 테스트

```bash
curl -s -X POST http://localhost:5678/webhook/wbs-jra \
  -H "Content-Type: application/json" \
  -d '{"board_id": "8207"}'
```

| 검증 항목 | 기대값 | 실제값 | 결과 |
|-----------|--------|--------|------|
| sprint_id | 15902 | 15902 | ✅ |
| sprint_name | WBS 1 스프린트 | WBS 1 스프린트 | ✅ |
| total_tickets | 4 | 4 | ✅ |
| in_progress | 2 | 2 | ✅ |
| todo | 2 | 2 | ✅ |
| done | 0 | 0 | ✅ |
| sp_total | - | 0 | ⚠️ Jira 프로젝트 설정 이슈 |
| error | null | null | ✅ |

**판정: PASS** (SP는 Jira 프로젝트 설정 후 검증 예정)

### Step 3: WBS-GRC → WBS-JRA 연동 테스트 (commit_messages 전달)

```bash
curl -s -X POST http://localhost:5678/webhook/wbs-jra \
  -H "Content-Type: application/json" \
  -d '{
    "board_id": "8207",
    "commit_messages": [
      "WBS-2 회원가입 API 엔드포인트 추가",
      "WBS-3 로그인 화면 UI 구현",
      "WBS-2 validation 로직 수정",
      "feat: WBS-4 DB 마이그레이션 스크립트 작성",
      "orphan commit without jira key"
    ]
  }'
```

| 검증 항목 | 기대값 | 실제값 | 결과 |
|-----------|--------|--------|------|
| jira_commit_map[WBS-2] 커밋 수 | 2 | 2 | ✅ |
| jira_commit_map[WBS-3] 커밋 수 | 1 | 1 | ✅ |
| jira_commit_map[WBS-4] 커밋 수 | 1 | 1 | ✅ |
| linked_ticket_count | 3 | 3 | ✅ |
| orphan commit 처리 | 키 없는 커밋 무시 | 정상 무시 | ✅ |
| no_commit_issues | [WBS-5] | [WBS-5] | ✅ |

**판정: PASS**

### 전체 테스트 요약

| 단계 | 항목 | 결과 |
|------|------|------|
| Step 1 | WBS-GRC 단독 (Commit 집계 포함) | ✅ PASS |
| Step 2 | WBS-JRA 단독 (Sprint 조회, 상태 집계) | ✅ PASS |
| Step 3 | WBS-GRC → WBS-JRA 연동 (commit_messages) | ✅ PASS |

**Phase 2 최종 판정: PASS** (SP 집계는 Jira 관리자 설정 후 추가 검증 필요)

---

## Phase 3 연동 인터페이스

WBS-ORK가 Phase 2 결과를 사용하는 방식:

```javascript
// WBS-GRC 호출 결과에서 commit_messages 추출
const commitMessages = grcResult.all_commit_messages || [];

// WBS-JRA 호출 시 commit_messages 전달
const jraInput = {
  board_id: $env.JIRA_BOARD_ID,
  commit_messages: commitMessages
};
```

WBS-JRA 출력의 `jira_commit_map`, `ticket_done_rate`, `sp_burned_rate`가 WBS-ORK의 진척률 계산 입력으로 사용된다.
