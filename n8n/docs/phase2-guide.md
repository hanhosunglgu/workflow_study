# Phase 2 개발 가이드 — 진척률 수집 (WBS-JRA, WBS-GRC 확장)

> n8n을 처음 접하는 분들을 위해 워크플로 구조부터 각 노드의 역할까지 상세히 설명합니다.

---

## 목차

1. [n8n 기본 개념](#1-n8n-기본-개념)
2. [Phase 2 개요](#2-phase-2-개요)
3. [WBS-JRA — Jira Agent](#3-wbs-jra--jira-agent)
4. [WBS-GRC — GitHub Repo Classifier (확장)](#4-wbs-grc--github-repo-classifier-확장)
5. [두 워크플로의 연결 관계](#5-두-워크플로의-연결-관계)
6. [n8n 임포트 및 테스트 방법](#6-n8n-임포트-및-테스트-방법)

---

## 1. n8n 기본 개념

Phase 2 코드를 읽기 전에 알아야 할 n8n 핵심 개념입니다.

### 1.1 워크플로(Workflow)란?

n8n에서 워크플로는 **노드(Node)들을 연결한 자동화 파이프라인**입니다. 마치 엑셀의 함수들을 순서대로 연결해 놓은 것처럼, 각 노드가 데이터를 받아 처리하고 다음 노드로 넘깁니다.

```
[시작] → [노드A] → [노드B] → [노드C] → [끝]
           ↓ 데이터 흐름 ↓
```

### 1.2 노드(Node)란?

노드는 워크플로를 구성하는 **하나의 작업 단위**입니다. 예를 들어:
- "Jira API를 호출한다" → HTTP Request 노드
- "데이터를 가공한다" → Code 노드
- "조건에 따라 분기한다" → IF 노드

### 1.3 데이터 구조: Items

n8n에서 노드 간에 전달되는 데이터는 **아이템(Item) 배열** 형태입니다. 각 아이템은 `{ json: { ... } }` 형태를 가집니다.

```javascript
// 노드 A가 노드 B에게 전달하는 데이터 예시
[
  { json: { repo: "api-server", type: "backend" } },
  { json: { repo: "web-app",    type: "frontend" } }
]
```

### 1.4 n8n 표현식 문법

노드 설정값 안에서 `{{ }}` 또는 `={{ }}` 를 사용하면 이전 노드의 데이터를 참조할 수 있습니다.

| 표현식 | 의미 |
|--------|------|
| `{{ $json.boardId }}` | 현재 아이템의 `boardId` 필드 |
| `$('노드이름').first().json` | 특정 노드의 첫 번째 출력 데이터 |
| `$input.first().json` | 바로 이전 노드의 첫 번째 출력 |
| `$input.all()` | 바로 이전 노드의 모든 출력 아이템 |
| `$vars.변수명` | n8n Variables에 등록된 환경변수 |

### 1.5 Credential(자격증명)이란?

API 호출에 필요한 **인증 정보(토큰, 비밀번호 등)를 n8n이 암호화해서 저장하는 공간**입니다.

- 코드에 직접 토큰을 쓰지 않고, n8n Credential을 참조합니다.
- Phase 2에서 사용하는 Credential:
  - `Jira API Token` — Jira Cloud 인증
  - `GitHub PAT` — GitHub API 인증

### 1.6 SplitInBatches 노드의 포트 순서

n8n에서 가장 헷갈리는 부분 중 하나입니다.

```
SplitInBatches
├── 포트 0 (위쪽/Done): 모든 배치 처리가 끝난 후 → 다음 단계로
└── 포트 1 (아래쪽/Loop): 각 배치 아이템 처리 중 → 처리 로직으로
```

직관과 반대처럼 느껴지지만, **0번이 "완료 후 출구"이고 1번이 "반복 처리 입구"** 입니다.

---

## 2. Phase 2 개요

### 목적

Phase 1에서 코드 품질(설계 적합성)을 분석했다면, Phase 2는 **진척률 데이터를 수집**합니다.

| 수집 항목 | 담당 워크플로 | 데이터 원천 |
|-----------|--------------|-------------|
| 티켓 상태, Story Point 소진률 | WBS-JRA (신규) | Jira Cloud API |
| 주간 Commit 수, 활성 개발일 | WBS-GRC (확장) | GitHub API |
| 이번 주 Merge된 PR 수 | WBS-GRC (확장) | GitHub API |

### 수집 데이터가 최종적으로 쓰이는 곳

Phase 3의 WBS-ORK(Orchestrator)가 두 워크플로의 결과를 받아 아래 공식으로 **전체 진척률**을 계산합니다.

```
전체 진척률 = (Jira 티켓 완료율 × 40%)
            + (Story Point 소진률 × 40%)
            + (GitHub Commit 활성 일수 / 5일 × 20%)
```

---

## 3. WBS-JRA — Jira Agent

**파일**: `workflow/WBS-JRA.json`  
**역할**: Jira의 활성 Sprint에서 티켓 상태와 Story Point를 수집하고, GitHub Commit 메시지와 연결합니다.

### 3.1 전체 흐름 요약

```
외부 호출 (POST /webhook/wbs-jra)
    │
    ▼
[1] Webhook             — HTTP 요청을 받아 워크플로 시작
    │
    ▼
[2] Init Params         — 입력값 파싱 (board_id, commit_messages 등)
    │
    ▼
[3] GET Active Sprint   — Jira에서 현재 진행 중인 Sprint 조회
    │
    ▼
[4] Extract Sprint ID   — Sprint ID, 이름, 기간 추출
    │
    ▼
[5] Init Pagination     — 페이지 조회를 위한 초기값 설정 (startAt=0)
    │
    ▼
[6] Pagination Loop ◄────────────────────────────────┐
    │ (아직 처리할 페이지 있음)                        │
    ▼                                                 │
[7] GET Sprint Issues   — Jira에서 이슈 100개씩 조회   │
    │                                                 │
    ▼                                                 │
[8] Accumulate Issues   — 조회한 이슈를 누적 저장       │
    │                                                 │
    ▼                                                 │
[9] Has More Pages?     — 더 조회할 이슈가 있나?        │
    │ YES ────────────────────────────────────────────┘
    │ NO
    ▼
[10] Aggregate Status   — 상태별 카운트 + SP 소진률 계산
    │
    ▼
[11] Map Commits to Jira — Commit 메시지 ↔ Jira 티켓 키 매핑
    │
    ▼
[12] Build Output        — 표준 출력 스키마 조립
    │
    ▼
[13] Respond to Webhook  — JSON 응답 반환
```

### 3.2 노드별 상세 설명

---

#### 노드 1: Webhook

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.webhook` |
| 역할 | 워크플로의 진입점. 외부에서 HTTP POST 요청이 오면 워크플로를 시작합니다. |
| URL | `POST http://localhost:5678/webhook/wbs-jra` |
| 설정 | `responseMode: "responseNode"` — 응답은 맨 마지막 Respond to Webhook 노드에서 직접 보냄 |

**호출 예시:**
```bash
curl -X POST http://localhost:5678/webhook/wbs-jra \
  -H "Content-Type: application/json" \
  -d '{
    "board_id": "8207",
    "commit_messages": [
      "feat: WBS-101 로그인 API 구현",
      "fix: WBS-102 토큰 갱신 버그 수정"
    ]
  }'
```

---

#### 노드 2: Init Params

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.code` |
| 역할 | Webhook으로 받은 요청 본문을 파싱하고, 설정값이 없으면 n8n Variables에서 기본값을 가져옵니다. |

**입력 → 출력 변환:**
```javascript
// 입력 (Webhook 요청 본문)
{ "board_id": "8207", "commit_messages": ["feat: WBS-101 ..."] }

// 출력 (다음 노드로 전달)
{
  "boardId": "8207",
  "baseUrl": "https://lgucorp.atlassian.net",  // $vars.JIRA_BASE_URL 참조
  "projectKeys": ["WBS"],                       // $vars.JIRA_PROJECT_KEYS 참조
  "commitMessages": ["feat: WBS-101 ..."]
}
```

**핵심 코드 설명:**
```javascript
// "input.body || input" 패턴 — Webhook vs Execute Workflow 두 방식 모두 지원
const body = input.body || input;

// n8n Variables에서 기본값 가져오기
const boardId = body.board_id || $vars.JIRA_BOARD_ID || '8207';
```

---

#### 노드 3: GET Active Sprint

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.httpRequest` |
| 역할 | Jira Agile API를 호출하여 현재 진행 중인(active) Sprint를 조회합니다. |
| API | `GET {baseUrl}/rest/agile/1.0/board/{boardId}/sprint?state=active&maxResults=1` |
| 인증 | Credential `Jira API Token` (HTTP Header 방식: `Authorization: Basic base64(email:token)`) |
| `neverError: true` | API가 4xx/5xx를 반환해도 워크플로를 중단하지 않고 다음 노드로 진행 |

**Jira API 응답 구조:**
```json
{
  "values": [
    {
      "id": 42,
      "name": "Sprint 12",
      "state": "active",
      "startDate": "2026-05-11T09:00:00.000Z",
      "endDate": "2026-05-25T09:00:00.000Z"
    }
  ]
}
```

---

#### 노드 4: Extract Sprint ID

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.code` |
| 역할 | GET Active Sprint 응답에서 Sprint ID와 기간 정보를 꺼내고, Init Params 데이터와 합칩니다. |

**핵심 처리:**
```javascript
const sprints = sprintData.values || [];
if (!sprints.length) {
  throw new Error('활성 Sprint가 없습니다.');  // 에러 발생 → 워크플로 중단
}
const sprint = sprints[0];
// sprint.id, sprint.name, sprint.startDate, sprint.endDate 추출
```

> **왜 Init Params 데이터를 다시 붙이나?**
> n8n에서 데이터는 직전 노드에서만 자동으로 흘러옵니다. GET Active Sprint 응답에는 boardId나 commitMessages가 없으므로, `$('Init Params').first().json`으로 앞 노드 데이터를 직접 참조해서 함께 전달합니다.

---

#### 노드 5: Init Pagination

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.code` |
| 역할 | 페이지네이션 루프에 필요한 초기 상태값을 설정합니다. |

Jira API는 한 번에 최대 100개 이슈만 반환합니다. Sprint에 이슈가 100개를 초과하면 여러 번 나눠 요청해야 합니다. 이 노드는 그 반복을 시작하기 위한 초기값을 세팅합니다.

```javascript
{
  startAt: 0,      // 첫 번째 요청은 0번 이슈부터
  maxResults: 100, // 한 번에 100개씩 요청
  allIssues: []    // 누적 저장소 (처음엔 빈 배열)
}
```

---

#### 노드 6: Pagination Loop

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.splitInBatches` |
| 역할 | 페이지네이션 루프의 제어 노드입니다. "모든 페이지 처리 완료"와 "다음 페이지 처리 중" 두 경로로 분기합니다. |
| `batchSize` | 1 — 아이템 1개씩 처리 |

**포트 연결:**
```
포트 0 (Done — 루프 완료) → Aggregate Status   (모든 이슈 수집 후 집계)
포트 1 (Loop — 반복 중)  → GET Sprint Issues  (다음 페이지 API 호출)
```

> **중요**: SplitInBatches는 들어오는 아이템 수만큼 반복합니다. 여기서는 아이템이 항상 1개이므로 실질적으로 "루프 제어 스위치" 역할을 합니다. 루프 반복은 `Build Repo Stats → Loop Over Repos`처럼 마지막 처리 노드가 다시 이 노드를 가리키는 방식으로 구현됩니다.

---

#### 노드 7: GET Sprint Issues

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.httpRequest` |
| 역할 | Sprint의 이슈 목록을 페이지 단위로 조회합니다. |
| API | `GET {baseUrl}/rest/agile/1.0/sprint/{sprintId}/issue?startAt={N}&maxResults=100` |

**요청 URL에서 `startAt` 이 매번 달라지는 이유:**
- 첫 번째 요청: `startAt=0` (0~99번 이슈)
- 두 번째 요청: `startAt=100` (100~199번 이슈)
- 세 번째 요청: `startAt=200` (200~299번 이슈)

**조회하는 필드 (`fields` 파라미터):**
- `summary` — 이슈 제목
- `status` — 현재 상태 (To Do, In Progress, Done 등)
- `customfield_10016` — Story Points (Jira Cloud의 SP 필드 ID)
- `assignee` — 담당자
- `issuetype` — 이슈 유형 (Story, Task, Bug 등)

---

#### 노드 8: Accumulate Issues

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.code` |
| 역할 | 이번 페이지 이슈를 이전까지 누적된 이슈 목록에 더합니다. 다음 페이지가 있는지 판단합니다. |

**핵심 처리:**
```javascript
// Pagination Loop 노드에서 루프 상태 참조
const loopState = $('Pagination Loop').first().json;

// 이번 페이지 이슈를 기존 누적 목록에 추가
const accumulated = (loopState.allIssues || []).concat(
  issues.map(issue => ({
    key: issue.key,                                    // "WBS-101"
    summary: issue.fields?.summary || '',              // 이슈 제목
    status: issue.fields?.status?.name || 'Unknown',  // "In Progress"
    storyPoints: issue.fields?.customfield_10016,      // 5
    issueType: issue.fields?.issuetype?.name || 'Task' // "Story"
  }))
);

// 다음 페이지 필요 여부 계산
const nextStart = loopState.startAt + issues.length;
const hasMore = nextStart < total && issues.length > 0;
```

---

#### 노드 9: Has More Pages?

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.if` |
| 역할 | `hasMore` 값이 true면 Pagination Loop로 돌아가고, false면 집계 단계로 넘어갑니다. |

**포트 연결:**
```
조건 true  (포트 0) → Pagination Loop  (다음 페이지 요청)
조건 false (포트 1) → Aggregate Status (전체 이슈 집계 시작)
```

**조건 설정:**
```
leftValue:  $json.hasMore
operator:   equals
rightValue: true
```

---

#### 노드 10: Aggregate Status

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.code` |
| 역할 | 전체 이슈를 상태별로 분류하고, Story Point 소진률을 계산합니다. |

**상태 분류 규칙 (Jira 커스텀 상태 포함):**

| 분류 | 해당 상태값 |
|------|------------|
| `done` | statusCategory=done, "Done", "Closed", "Resolved" |
| `in_review` | 상태명에 "review", "pr", "testing", "qa" 포함 |
| `in_progress` | statusCategory=indeterminate, "progress", "doing", "dev", "wip" 포함 |
| `todo` | statusCategory=new, "To Do", "Open", "Backlog" |

**Story Point 소진률 계산:**
```javascript
// 전체 SP 합산 (SP가 null인 이슈는 제외)
const spTotal = allSP.reduce((acc, sp) => acc + (Number(sp) || 0), 0);

// Done 상태 이슈의 SP만 합산
const doneSP = doneIssues.reduce((acc, i) => acc + (Number(i.storyPoints) || 0), 0);

// 소진률 (0~100%)
const spBurnedRate = spTotal > 0 ? Math.round((doneSP / spTotal) * 100) : 0;
```

---

#### 노드 11: Map Commits to Jira

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.code` |
| 역할 | GitHub Commit 메시지에서 Jira 이슈 키를 추출하여 연결 관계를 만듭니다. |

**Jira 키 추출 정규식:**
```javascript
const jiraKeyPattern = /\b([A-Z][A-Z0-9]+-\d+)\b/g;
// 매칭 예: "WBS-101", "PROJ-42", "ABC123-5"
```

**분류 결과:**

| 필드 | 내용 |
|------|------|
| `jira_commit_map` | `{ "WBS-101": ["feat: WBS-101 로그인 구현"] }` — 키 → 커밋 메시지 목록 |
| `linked_ticket_count` | Commit에서 언급된 Sprint 티켓 수 |
| `orphan_commit_keys` | Commit에서 나왔지만 현재 Sprint에 없는 이슈 키 |
| `no_commit_issues` | Sprint에 있지만 관련 Commit이 없는 미완료 티켓 목록 |

---

#### 노드 12: Build Output

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.code` |
| 역할 | 앞 노드들의 결과를 표준 출력 스키마로 조립합니다. |

**최종 출력 JSON:**
```json
{
  "agent_id": "WBS-JRA",
  "repo": "jira",
  "repo_type": "jira",
  "sprint_id": 42,
  "sprint_name": "Sprint 12",
  "sprint_start_date": "2026-05-11T09:00:00.000Z",
  "sprint_end_date": "2026-05-25T09:00:00.000Z",
  "total_tickets": 24,
  "done": 10,
  "in_review": 3,
  "in_progress": 7,
  "todo": 4,
  "sp_total": 48,
  "sp_burned": 20,
  "sp_burned_rate": 42,
  "ticket_done_rate": 42,
  "done_tickets": ["WBS-101 로그인 API 구현", "WBS-102 ..."],
  "incomplete_tickets": ["WBS-105 결제 모듈", "WBS-107 ..."],
  "jira_commit_map": { "WBS-101": ["feat: WBS-101 로그인 구현"] },
  "linked_ticket_count": 3,
  "orphan_commit_keys": ["WBS-999"],
  "no_commit_issues": ["WBS-105", "WBS-107"],
  "call_flow": [],
  "design_gaps": [],
  "commit_count": 0,
  "active_days": 0,
  "error": null
}
```

> `call_flow`, `design_gaps`, `commit_count`, `active_days`는 Phase 1 에이전트 공통 스키마와의 호환성을 위해 포함되며, WBS-JRA에서는 해당 없으므로 빈 값입니다.

---

#### 노드 13: Respond to Webhook

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.respondToWebhook` |
| 역할 | 워크플로 처리 결과를 HTTP 200 응답으로 반환합니다. |

Webhook 노드의 `responseMode: "responseNode"` 설정과 쌍을 이룹니다. 이 노드가 없으면 응답이 반환되지 않습니다.

---

## 4. WBS-GRC — GitHub Repo Classifier (확장)

**파일**: `workflow/WBS-GRC.json`  
**역할**: GitHub Repo를 유형별로 분류하는 기존 기능에 더해, **이번 주 Commit 통계와 Merge된 PR 목록을 수집**합니다.

### 4.1 Phase 1 대비 변경 사항

Phase 1의 WBS-GRC는 Repo 분류만 했습니다. Phase 2에서 아래 6개 노드가 추가되었습니다.

| 구분 | Phase 1 | Phase 2 (추가) |
|------|---------|----------------|
| 노드 수 | 10개 | **16개** |
| Commit 수집 | 없음 | GET Commits This Week |
| PR 수집 | 없음 | GET Merged PRs |
| 데이터 병합 | 없음 | Merge Commit & PR |
| 통계 조립 | 없음 | Aggregate Commits, Aggregate PRs, Build Repo Stats |

### 4.2 전체 흐름 요약

```
외부 호출 (POST /webhook/wbs-grc)
    │
    ▼
[1] Webhook                 — 워크플로 시작
    │
    ▼
[2] Init Params             — 입력값 파싱 + 이번 주 since/until 계산
    │
    ▼
[3] GET User Repos          — GitHub에서 owner의 전체 Repo 목록 조회
    │
    ▼
[4] Filter & Split Repos    — 분석 대상 Repo만 필터링 (1개씩 분리)
    │
    ▼
[5] Loop Over Repos ◄───────────────────────────────────────┐
    │ (아직 처리할 Repo 있음)                                │
    ▼                                                       │
[6] GET Root Contents       — Repo의 루트 파일 목록 조회     │
    │                                                       │
    ▼                                                       │
[7] Attach Repo Info        — 파일 목록에 Repo 메타 정보 추가 │
    │                                                       │
    ├──→ [8] GET Commits This Week — 이번 주 Commit 조회     │
    │         │                                             │
    │         ▼                                             │
    │    [10] Aggregate Commits — commit_count, active_days  │
    │         │                                             │
    │         ▼                                             │
    ├──→ [9] GET Merged PRs  — closed PR 목록 조회           │
    │         │                                             │
    │         ▼                                             │
    │    [11] Aggregate PRs  — 이번 주 merge 필터링          │
    │                                                       │
    ▼                                                       │
[12] Merge Commit & PR      — 두 경로 결과 합산             │
    │                                                       │
    ▼                                                       │
[13] Build Repo Stats       — Repo별 최종 통계 조립 ─────────┘
    
    (모든 Repo 처리 완료 후)
    ▼
[14] Classify Repos         — 파일 패턴으로 Repo 유형 분류
    │
    ▼
[15] Build Output           — 표준 출력 스키마 조립
    │
    ▼
[16] Respond to Webhook     — JSON 응답 반환
```

### 4.3 노드별 상세 설명

---

#### 노드 1: Webhook

WBS-JRA와 동일한 구조입니다. 경로만 다릅니다.

| 항목 | 내용 |
|------|------|
| URL | `POST http://localhost:5678/webhook/wbs-grc` |

---

#### 노드 2: Init Params *(Phase 2에서 확장)*

Phase 1 대비 **이번 주 날짜 범위 계산 로직이 추가**되었습니다.

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.code` |
| 추가 역할 | 이번 주 월요일 00:00 UTC ~ 현재 시각을 ISO 8601 형식으로 계산 |

**날짜 계산 로직:**
```javascript
const now = new Date();
const dayOfWeek = now.getUTCDay(); // 일=0, 월=1, ..., 토=6

// 오늘로부터 이번 주 월요일까지의 일 수 계산
const daysFromMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;

const monday = new Date(now);
monday.setUTCDate(now.getUTCDate() - daysFromMonday);
monday.setUTCHours(0, 0, 0, 0);

// 결과: "2026-05-11T00:00:00.000Z" 형태
const since = monday.toISOString();
const until = now.toISOString();
```

---

#### 노드 3: GET User Repos

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.httpRequest` |
| 역할 | GitHub owner의 모든 Repo 목록을 가져옵니다. |
| API | `GET https://api.github.com/users/{owner}/repos?per_page=100&type=all` |
| 인증 | Credential `GitHub PAT` |

---

#### 노드 4: Filter & Split Repos *(Phase 2에서 since/until 전달 추가)*

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.code` |
| 역할 | `GITHUB_REPOS` 환경변수에 지정된 Repo만 필터링하고, 1개 Repo = 1개 아이템으로 분리합니다. |

Phase 2에서는 `since`, `until`도 각 아이템에 포함시켜 이후 Commit 조회에 활용합니다.

```javascript
return filtered.map(r => ({
  json: {
    owner: initItem.owner,
    repo: r.name,
    full_name: r.full_name,    // "hanhosunglgu/WBS_Check"
    since: initItem.since,     // ← Phase 2 추가
    until: initItem.until      // ← Phase 2 추가
  }
}));
```

---

#### 노드 5: Loop Over Repos

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.splitInBatches` |
| 역할 | Repo 목록을 1개씩 처리하는 반복 루프의 제어 노드 |
| `batchSize` | 1 |

**포트 연결:**
```
포트 0 (Done) → Classify Repos     (모든 Repo 처리 완료 → 분류 단계)
포트 1 (Loop) → GET Root Contents  (각 Repo 처리 중 → 루트 파일 조회)
```

---

#### 노드 6: GET Root Contents

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.httpRequest` |
| 역할 | Repo의 루트 디렉터리에 있는 파일/폴더 목록을 조회합니다. |
| API | `GET https://api.github.com/repos/{full_name}/contents/` |
| `neverError: true` | Repo가 비어있거나 404여도 워크플로 중단 없이 진행 |

루트 파일 목록을 보면 어떤 프로젝트인지 알 수 있습니다:
- `vite.config.ts` → 프론트엔드 (Vite)
- `pom.xml` → 백엔드 (Java/Spring)
- `pubspec.yaml` → 모바일 (Flutter)

---

#### 노드 7: Attach Repo Info *(Phase 2에서 since/until 전달 추가)*

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.code` |
| 역할 | GET Root Contents 응답(파일 목록)에 Repo 이름, since/until 등 메타 정보를 붙입니다. |

이 노드부터 **분기**가 시작됩니다. 하나의 출력이 두 방향으로 동시에 흘러갑니다:
- 출력 0 → GET Commits This Week
- 출력 1 → GET Merged PRs

---

#### 노드 8: GET Commits This Week *(Phase 2 신규)*

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.httpRequest` |
| 역할 | 이번 주(월~현재)에 해당 Repo에 push된 Commit 목록을 조회합니다. |
| API | `GET https://api.github.com/repos/{full_name}/commits?since={since}&until={until}&per_page=100` |

**`since`/`until` 예시:**
```
since = "2026-05-11T00:00:00.000Z"  (이번 주 월요일 자정)
until = "2026-05-14T15:30:00.000Z"  (현재 시각)
```

---

#### 노드 9: GET Merged PRs *(Phase 2 신규)*

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.httpRequest` |
| 역할 | Repo에서 closed(닫힌) PR 목록을 최신순으로 조회합니다. |
| API | `GET https://api.github.com/repos/{full_name}/pulls?state=closed&sort=updated&direction=desc&per_page=50` |

> 이번 주 merge 여부 필터링은 API 파라미터가 아니라 다음의 Aggregate PRs 노드(Code 노드)에서 `merged_at` 날짜를 비교하여 수행합니다.

---

#### 노드 10: Aggregate Commits *(Phase 2 신규)*

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.code` |
| 역할 | Commit 목록에서 `commit_count`, `active_days`, `commit_messages`를 계산합니다. |

**active_days 계산 (주말 제외):**
```javascript
// 각 Commit의 날짜(YYYY-MM-DD)를 Set으로 중복 제거
const activeDaySet = new Set(
  commits.map(c => c.commit?.author?.date.substring(0, 10))
);

// 주말(토=6, 일=0)은 제외하고 평일만 카운트
const weekdaySet = new Set(
  [...activeDaySet].filter(d => {
    const day = new Date(d).getUTCDay();
    return day >= 1 && day <= 5;  // 월(1) ~ 금(5)
  })
);
// weekdaySet.size = 활성 개발일 수 (최대 5)
```

---

#### 노드 11: Aggregate PRs *(Phase 2 신규)*

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.code` |
| 역할 | PR 목록 중 `merged_at`이 이번 주 월요일 이후인 것만 필터링합니다. |

```javascript
const mergedThisWeek = prs.filter(pr =>
  pr.merged_at && new Date(pr.merged_at) >= sinceDate
);
```

또한 이 노드는 `Aggregate Commits`의 결과(`$('Aggregate Commits').first().json`)를 참조하여, Commit 통계 데이터도 함께 출력에 포함시킵니다. 이렇게 하면 이후 Merge 노드에서 두 경로의 데이터를 합칠 수 있습니다.

---

#### 노드 12: Merge Commit & PR *(Phase 2 신규)*

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.merge` |
| 역할 | 두 개의 병렬 경로(Commit 집계, PR 집계)의 결과를 하나로 합칩니다. |
| `numberInputs` | 2 — 입력 포트 2개 |

```
입력 포트 0 ← Aggregate Commits
입력 포트 1 ← Aggregate PRs
    │
    ▼
출력: 두 아이템이 순서대로 하나의 배열로 합산됨
```

> **왜 병렬로 처리하나?** Commit API와 PR API는 서로 독립적입니다. 순서대로 처리하면 시간이 2배 걸리지만, 병렬 분기 후 Merge하면 더 빠릅니다.

---

#### 노드 13: Build Repo Stats *(Phase 2 신규)*

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.code` |
| 역할 | Merge 노드의 두 아이템(Commit 데이터, PR 데이터)을 하나의 Repo 통계 객체로 조립합니다. 그리고 Loop Over Repos 노드로 다시 돌아가 다음 Repo 처리를 시작합니다. |

**출력 구조:**
```javascript
{
  owner: "hanhosunglgu",
  repo: "WBS_Check",
  full_name: "hanhosunglgu/WBS_Check",
  since: "2026-05-11T00:00:00.000Z",
  until: "2026-05-14T15:30:00.000Z",
  file_names: ["vite.config.ts", "package.json", ...],
  commit_count: 8,
  active_days: 3,
  commit_messages: ["feat: WBS-101 로그인", ...],
  merged_pr_count: 2,
  merged_prs: [{ number: 12, title: "...", merged_at: "...", user: "..." }]
}
```

이 데이터가 Loop Over Repos 노드의 입력 포트(포트 0)로 다시 들어가면서, 다음 Repo 처리가 시작됩니다.

---

#### 노드 14: Classify Repos *(Phase 2에서 commit_stats 추가)*

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.code` |
| 역할 | 루트 파일 패턴으로 각 Repo의 유형을 판단하고, 모든 Repo의 Commit 통계를 `commit_stats` 객체로 취합합니다. |

**Repo 유형 판단 우선순위:**

| 우선순위 | 판단 기준 파일 | 분류 |
|----------|--------------|------|
| 1 | `Podfile`, `pubspec.yaml`, `Package.swift` | mobile |
| 2 | `build.gradle` (package.json 없음) | mobile |
| 3 | `*.tf`, `helmfile.yaml`, `k8s/`, `terraform/` | config |
| 4 | `pom.xml`, `requirements.txt`, `go.mod` 등 | backend |
| 5 | `vite.config.*`, `next.config.*`, `angular.json` 등 | frontend |
| 6 | `package.json` (위 조건 미해당) | frontend |

---

#### 노드 15: Build Output *(Phase 2에서 commit 관련 필드 추가)*

| 항목 | 내용 |
|------|------|
| 타입 | `n8n-nodes-base.code` |
| 역할 | 분류 결과와 Commit 통계를 최종 출력 스키마로 조립합니다. |

**최종 출력 JSON:**
```json
{
  "agent_id": "WBS-GRC",
  "backend": [],
  "frontend": ["WBS_Check"],
  "config": [],
  "mobile": [],
  "unknown": [],
  "_classified_detail": [
    { "repo": "WBS_Check", "type": "frontend", "reason": "Vite" }
  ],
  "commit_stats": {
    "WBS_Check": {
      "commit_count": 8,
      "active_days": 3,
      "commit_messages": ["feat: WBS-101 로그인 API 구현", "fix: ..."],
      "merged_pr_count": 2,
      "merged_prs": [{ "number": 12, "title": "feat: 로그인 구현", "merged_at": "...", "user": "dev1" }]
    }
  },
  "total_commit_count": 8,
  "max_active_days": 3,
  "all_commit_messages": ["feat: WBS-101 로그인 API 구현", "fix: ..."],
  "error": null
}
```

> `all_commit_messages`는 WBS-JRA의 `commit_messages` 입력값으로 바로 사용할 수 있습니다. WBS-ORK(Orchestrator)가 WBS-GRC 결과의 `all_commit_messages`를 WBS-JRA에 전달하여 Commit ↔ Jira 매핑을 완성합니다.

---

#### 노드 16: Respond to Webhook

WBS-JRA와 동일합니다.

---

## 5. 두 워크플로의 연결 관계

WBS-GRC와 WBS-JRA는 독립적으로도 동작하지만, Phase 3의 WBS-ORK가 조율하면 아래처럼 연결됩니다.

```
WBS-ORK (Orchestrator)
    │
    ├── WBS-GRC 호출 → 결과: all_commit_messages, commit_stats
    │                              │
    │               ┌─────────────┘
    │               ▼
    └── WBS-JRA 호출 (commit_messages 전달)
              → 결과: jira_commit_map, sp_burned_rate, ticket_done_rate
```

**데이터 흐름 예시:**
```
WBS-GRC 결과:
  all_commit_messages: ["feat: WBS-101 로그인", "fix: WBS-102 버그"]

↓ WBS-ORK가 이 값을 WBS-JRA에 전달

WBS-JRA 입력:
  commit_messages: ["feat: WBS-101 로그인", "fix: WBS-102 버그"]

WBS-JRA 결과:
  jira_commit_map: { "WBS-101": ["feat: WBS-101 로그인"] }
  no_commit_issues: ["WBS-105", "WBS-107"]  ← Commit이 없는 미완료 티켓
```

---

## 6. n8n 임포트 및 테스트 방법

### 6.1 워크플로 임포트

1. n8n UI 접속: `http://localhost:5678`
2. 좌측 메뉴 **Workflows** 클릭
3. 우상단 **+** 버튼 → **Import from File** 선택
4. `workflow/WBS-JRA.json` 또는 `workflow/WBS-GRC.json` 파일 선택
5. 임포트 후 우상단 **Activate** 토글 ON

> WBS-GRC는 Phase 1에서 이미 임포트했다면 **덮어쓰기(Import and overwrite)** 로 업데이트하면 됩니다.

### 6.2 WBS-JRA 테스트

```bash
# 기본 테스트 (board_id만 전달)
curl -X POST http://localhost:5678/webhook/wbs-jra \
  -H "Content-Type: application/json" \
  -d '{"board_id": "8207"}'

# Commit 매핑 포함 테스트
curl -X POST http://localhost:5678/webhook/wbs-jra \
  -H "Content-Type: application/json" \
  -d '{
    "board_id": "8207",
    "commit_messages": [
      "feat: WBS-101 로그인 API 구현 완료",
      "fix: WBS-102 토큰 만료 버그 수정",
      "chore: 코드 정리"
    ]
  }'
```

**정상 응답 확인 포인트:**
- `sprint_id` 값이 있음 → Sprint 조회 성공
- `total_tickets` > 0 → 이슈 조회 성공
- `sp_burned_rate` 0~100 → SP 계산 성공

### 6.3 WBS-GRC 테스트

```bash
# GITHUB_REPOS 환경변수에 등록된 Repo 분석
curl -X POST http://localhost:5678/webhook/wbs-grc \
  -H "Content-Type: application/json" \
  -d '{}'

# 특정 Repo 지정
curl -X POST http://localhost:5678/webhook/wbs-grc \
  -H "Content-Type: application/json" \
  -d '{"owner": "hanhosunglgu", "repos": ["WBS_Check"]}'
```

**정상 응답 확인 포인트:**
- `frontend` 또는 `backend` 배열에 Repo 이름이 있음 → 분류 성공
- `commit_stats.WBS_Check.commit_count` > 0 → Commit 수집 성공 (이번 주 Commit이 있는 경우)
- `all_commit_messages` 배열에 Commit 메시지가 있음

### 6.4 오류 발생 시 확인 사항

| 증상 | 원인 | 해결 |
|------|------|------|
| `활성 Sprint가 없습니다` | Board에 active Sprint가 없음 | Jira에서 Sprint 시작 여부 확인 |
| `GITHUB_OWNER가 설정되지 않았습니다` | n8n Variables 미등록 | Settings → Variables에서 `GITHUB_OWNER` 등록 |
| HTTP 401 응답 | Credential 인증 실패 | n8n Credentials에서 `Jira API Token` / `GitHub PAT` 재확인 |
| `분석 대상 Repo 없음` | `GITHUB_REPOS` 값이 실제 Repo명과 불일치 | n8n Variables의 `GITHUB_REPOS` 값 확인 |
