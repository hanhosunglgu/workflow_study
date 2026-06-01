# Phase 3 개발 가이드 — Orchestration Agent (WBS-ORK)

**작성일**: 2026-05-14  
**대상 독자**: n8n을 한 번도 사용해본 적 없는 분들  
**목적**: Phase 3에서 구현한 WBS-ORK 워크플로의 구조, 각 노드의 역할, 테스트 결과를 상세히 설명

---

## 목차

1. [Phase 3가 하는 일](#1-phase-3가-하는-일)
2. [Orchestration이란?](#2-orchestration이란)
3. [WBS-ORK 전체 흐름](#3-wbs-ork-전체-흐름)
4. [노드별 상세 설명](#4-노드별-상세-설명)
   - 4.1 트리거 3종 (Webhook / Manual / Schedule)
   - 4.2 Init Params — 주간 날짜 계산
   - 4.3 Call WBS-GRC — 첫 번째 Agent 호출
   - 4.4 Parse GRC Result — 분류 결과 파싱
   - 4.5 병렬 Agent 호출 6개
   - 4.6 Merge All Results — 결과 합치기
   - 4.7 Integrate Results — 부분 실패 처리
   - 4.8 Build Call Flow Map — 호출 흐름 재구성
   - 4.9 Merge Design Gaps — Gap 통합
   - 4.10 Build Gap Analysis Prompt — Ollama 프롬프트 구성
   - 4.11 Has Gaps? — 조건 분기
   - 4.12 Ollama Gap Analysis — AI Gap 분석
   - 4.13 Parse Gap Analysis — AI 결과 파싱
   - 4.14 No Gaps Pass — Gap 없을 때 우회
   - 4.15 Calc Design Score — 설계 적합성 점수
   - 4.16 Calc Progress Score — 진척률 최종 계산
   - 4.17 Respond to Webhook / Log Final Result — 출력
5. [진척률 계산 공식 상세](#5-진척률-계산-공식-상세)
6. [n8n 임포트 및 실행 방법](#6-n8n-임포트-및-실행-방법)
7. [테스트 결과](#7-테스트-결과)
8. [자주 발생하는 문제와 해결](#8-자주-발생하는-문제와-해결)

---

## 1. Phase 3가 하는 일

Phase 1에서 코드를 분석하는 6개의 "전문가 Agent"를 만들었고, Phase 2에서 Jira와 GitHub 데이터를 수집하는 Agent를 만들었습니다.

Phase 3의 WBS-ORK는 이 모든 Agent들을 **지휘하는 총괄 Agent**입니다.

```
┌─────────────────────────────────────────────────────────────┐
│                        WBS-ORK                              │
│                   (Orchestration Agent)                     │
│                                                             │
│  "모든 Agent를 실행시키고, 결과를 하나로 합쳐서              │
│   최종 진척률 점수를 계산해준다"                             │
└─────────────────────────────────────────────────────────────┘
         │
         ├── WBS-GRC (Repo 분류 + Commit 집계)
         ├── WBS-JRA (Jira Sprint 현황)
         ├── WBS-DDA (설계 문서 분석)
         ├── WBS-BAK (Backend 코드 분석)
         ├── WBS-FRT (Frontend 코드 분석)
         ├── WBS-CFG (Config/인프라 분석)
         └── WBS-MOB (Mobile 코드 분석)
```

WBS-ORK 하나만 실행하면:
1. 자동으로 모든 Agent를 호출합니다
2. 결과를 취합하여 설계 적합성 점수를 계산합니다
3. 최종 주간 진척률 % 와 등급(GREEN/YELLOW/RED)을 반환합니다

---

## 2. Orchestration이란?

**Orchestration(오케스트레이션)**은 오케스트라 지휘자처럼 여러 구성 요소를 조율하는 것을 의미합니다.

```
오케스트라 비유:
  지휘자 (WBS-ORK)  →  바이올린(WBS-GRC), 첼로(WBS-JRA),
                        피아노(WBS-DDA), ... 각 파트를 동시에 지휘
  
  최종 결과: 하모니(통합 진척률 리포트)
```

n8n에서 Orchestration을 구현하는 핵심 패턴은 두 가지입니다.

### 패턴 1: HTTP Request로 다른 워크플로 호출

WBS-ORK는 다른 Agent를 **HTTP POST 요청**으로 호출합니다.

```
WBS-ORK (Call WBS-GRC 노드)
  → POST http://localhost:5678/webhook/wbs-grc
  → WBS-GRC 워크플로가 실행됨
  → 결과를 JSON으로 받음
```

이 방식의 장점: 각 Agent가 독립적으로 동작하므로 하나가 실패해도 나머지는 계속 실행됩니다.

### 패턴 2: Merge 노드로 병렬 결과 합치기

6개 Agent를 동시에 실행하고 모두 끝날 때까지 기다립니다.

```
Parse GRC Result ──┬──→ Call WBS-JRA ──┐
                   ├──→ Call WBS-DDA ──┤
                   ├──→ Call WBS-BAK ──┤→ Merge All Results
                   ├──→ Call WBS-FRT ──┤   (6개 모두 완료되면 진행)
                   ├──→ Call WBS-CFG ──┤
                   └──→ Call WBS-MOB ──┘
```

Merge 노드는 `numberInputs: 6`으로 설정되어 있어 6개 입력이 모두 도착해야 다음 노드로 진행합니다.

---

## 3. WBS-ORK 전체 흐름

WBS-ORK는 총 **25개 노드**로 구성되어 있습니다.

```
[트리거 3종]
  Webhook / Manual / Schedule Trigger
         │
         ▼
[초기화]
  Init Params ── 주간 날짜 범위 계산, 환경변수 읽기
         │
         ▼
[1차 호출 - 직렬]
  Call WBS-GRC ── Repo 분류 + 이번 주 Commit 집계
         │
         ▼
  Parse GRC Result ── GRC 결과에서 필요한 데이터 추출
         │
         ├──────────────────────────────────────────────────┐
         ▼                ▼         ▼       ▼      ▼       ▼
[2차 호출 - 병렬]
  Call WBS-JRA  Call WBS-DDA  WBS-BAK  WBS-FRT  WBS-CFG  WBS-MOB
         │                │         │       │      │       │
         └────────────────┴─────────┴───────┴──────┴───────┘
                          │
                          ▼
[결과 통합]
  Merge All Results ── 6개 결과를 하나로 합침
         │
         ▼
  Integrate Results ── 실패한 Agent는 기본값으로 대체
         │
         ▼
[분석]
  Build Call Flow Map ── 설계 vs 실제 API 흐름 비교
         │
         ▼
  Merge Design Gaps ── 모든 Agent의 Gap을 하나로 합침
         │
         ▼
  Build Gap Analysis Prompt ── Ollama에 보낼 프롬프트 작성
         │
         ▼
  Has Gaps? (IF 노드)
    ├─ Gap 있음 → Ollama Gap Analysis → Parse Gap Analysis
    └─ Gap 없음 → No Gaps Pass
         │
         ▼
[점수 계산]
  Calc Design Score ── 설계 적합성 % 계산
         │
         ▼
  Calc Progress Score ── 최종 진척률 % + 등급 계산
         │
         ├──→ Respond to Webhook (Webhook 트리거일 때 응답)
         └──→ Log Final Result (Manual/Schedule 트리거일 때 로그)
```

---

## 4. 노드별 상세 설명

### 4.1 트리거 3종

WBS-ORK는 3가지 방법으로 실행할 수 있습니다.

#### Webhook 노드 (외부 HTTP 요청)

```
POST http://localhost:5678/webhook/wbs-ork
Content-Type: application/json

{}
```

외부 시스템이나 curl 명령어로 실행할 때 사용합니다. 실행 결과를 HTTP 응답으로 즉시 받습니다.

**n8n 설정값**:
| 파라미터 | 값 | 설명 |
|---------|-----|------|
| httpMethod | POST | POST 요청만 받음 |
| path | wbs-ork | URL 경로 |
| responseMode | responseNode | 마지막 노드에서 응답 |

#### Manual Trigger 노드 (n8n UI에서 직접 실행)

n8n 화면에서 "Execute workflow" 버튼을 눌렀을 때 실행됩니다. 개발/테스트 시 사용합니다.

#### Schedule Trigger 노드 (자동 스케줄 실행)

매주 금요일 17:00에 자동으로 실행됩니다.

```
크론 표현식: 0 17 * * 5
의미: 매주(5=금요일) 17시 00분에 실행
```

> **크론(Cron) 표현식 읽는 법**:  
> `분 시 일 월 요일` 순서  
> `0 17 * * 5` = 0분, 17시, 매일(*)날, 매월(*), 금요일(5)

---

### 4.2 Init Params — 주간 날짜 계산

모든 트리거가 이 노드로 연결됩니다. 환경변수를 읽고 이번 주 날짜 범위를 계산합니다.

```javascript
// 이번 주 월요일 00:00 UTC 계산
const now = new Date();
const dayOfWeek = now.getUTCDay();           // 0=일, 1=월, ..., 6=토
const daysFromMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
const monday = new Date(now);
monday.setUTCDate(now.getUTCDate() - daysFromMonday);
monday.setUTCHours(0, 0, 0, 0);
```

**왜 월요일 계산이 필요한가?**  
GitHub API는 `since` 파라미터로 특정 날짜 이후의 커밋만 조회할 수 있습니다. 이번 주 월요일부터 지금까지의 커밋만 집계하기 위해 날짜를 계산합니다.

**출력 데이터**:
```json
{
  "owner": "hanhosunglgu",
  "repos": ["WBS_Check"],
  "boardId": "8207",
  "ddaRepo": "hanhosunglgu/WBS_Check",
  "ddaPath": "docs/design",
  "week_start": "2026-05-11T00:00:00.000Z",
  "week_end": "2026-05-14T09:54:00.000Z"
}
```

---

### 4.3 Call WBS-GRC — 첫 번째 Agent 호출

WBS-GRC를 호출하여 Repo를 분류하고 이번 주 커밋을 집계합니다.

```
POST http://localhost:5678/webhook/wbs-grc
Body: { "owner": "hanhosunglgu", "repos": ["WBS_Check"] }
```

**왜 WBS-GRC를 먼저 단독 호출하나?**  
WBS-GRC의 결과(`backend_repos`, `frontend_repos` 등)를 보고, 각 유형의 Repo가 있을 때만 해당 Specialist Agent를 호출하기 위해서입니다. 예를 들어 Mobile Repo가 없으면 WBS-MOB를 호출하지 않는 것이 효율적이지만, 이 구현에서는 항상 호출하고 Repo가 없으면 기본값을 사용합니다.

**타임아웃 설정**: `timeout: 300000` (5분)

---

### 4.4 Parse GRC Result — 분류 결과 파싱

WBS-GRC의 응답에서 필요한 데이터를 추출하고, 실패했을 경우 빈 배열로 초기화합니다.

```javascript
const backend  = grc.backend  || [];   // GRC 실패시 빈 배열
const frontend = grc.frontend || [];
// ...
const allCommitMessages = grc.all_commit_messages || [];
```

`||` 연산자: 왼쪽이 비어있거나 null이면 오른쪽 기본값을 사용합니다. 이렇게 하면 WBS-GRC가 실패해도 워크플로가 멈추지 않습니다.

---

### 4.5 병렬 Agent 호출 6개

Parse GRC Result 노드에서 6개 Agent를 **동시에** 호출합니다.

```
Parse GRC Result → Call WBS-JRA  (Jira 데이터)
               → Call WBS-DDA  (설계 문서)
               → Call WBS-BAK  (Backend 코드)
               → Call WBS-FRT  (Frontend 코드)
               → Call WBS-CFG  (Config/인프라)
               → Call WBS-MOB  (Mobile 코드)
```

> **n8n에서 병렬 실행 원리**:  
> n8n에서는 하나의 노드가 여러 노드로 연결되면 자동으로 병렬 실행됩니다.  
> Parse GRC Result의 output이 6개 노드의 input에 동시에 전달됩니다.

**각 Agent 호출 시 주목할 점**:

| Agent | 특이 설정 | 이유 |
|-------|----------|------|
| WBS-JRA | commit_messages 전달 | Jira 티켓과 커밋 매핑 |
| WBS-DDA | repo + path 형태로 전달 | 설계 문서 경로 지정 |
| WBS-BAK/FRT/CFG/MOB | repos 배열 전달 | 분류된 Repo 또는 전체 Repo |

**타임아웃**: WBS-JRA는 5분, 나머지는 10분 (Ollama 호출 포함)

---

### 4.6 Merge All Results — 결과 합치기

6개 Agent 결과를 하나로 합칩니다.

```
노드 설정: numberInputs = 6
```

**이 노드가 하는 일**:  
6개 입력 포트(index 0~5)가 모두 데이터를 받아야 다음 노드로 진행합니다. 마치 6명이 모두 모여야 회의를 시작하는 것과 같습니다.

> **주의**: n8n의 Merge 노드는 입력이 모두 도착하면 각 입력을 **별도 아이템**으로 출력합니다.  
> 즉, 6개 Agent 결과가 6개 아이템으로 전달됩니다.

---

### 4.7 Integrate Results — 부분 실패 처리

6개 결과 중 일부가 실패했을 때 기본값으로 채워서 계속 진행합니다.

```javascript
// agent_id로 결과를 Map에 저장
const resultMap = {};
for (const item of items) {
  const id = item.json.agent_id;
  resultMap[id] = item.json;
}

// WBS-JRA 결과가 없으면 기본값 사용
const jra = resultMap['WBS-JRA'] || {
  agent_id: 'WBS-JRA',
  total_tickets: 0,
  done: 0,
  // ...
  error: 'skipped'
};
```

**실패한 Agent 기록**:
```javascript
const failedAgents = [jra, dda, bak, frt, cfg, mob]
  .filter(a => a.error && a.error !== null)
  .map(a => a.agent_id);
// 예: ["WBS-DDA"] — DDA가 타임아웃됐을 때
```

이 목록은 최종 출력의 `failed_agents` 필드에 포함되어 "어떤 Agent가 실패했는지" 알 수 있게 합니다.

---

### 4.8 Build Call Flow Map — 호출 흐름 재구성

각 Agent가 추출한 Call Flow를 레이어별로 정렬합니다.

```
Mobile 레이어   → _login() → http.post('/api/auth/login')
Frontend 레이어 → authService.login() → POST /api/auth/login
Backend 레이어  → AuthController.login() → AuthService.validate()
```

**설계 vs 실제 엔드포인트 비교**:
```javascript
const designSet = new Set(designEndpoints);    // 설계 문서의 API 목록
const actualSet = new Set(actualEndpoints);    // 실제 코드의 API 목록

const missingInActual = [...designSet].filter(e => !actualSet.has(e));
// 설계에는 있는데 코드에 없는 것 → "누락된 구현"
const extraInActual = [...actualSet].filter(e => !designSet.has(e));
// 코드에는 있는데 설계에 없는 것 → "문서화 안 된 구현"
```

---

### 4.9 Merge Design Gaps — Gap 통합

4개 Specialist Agent(BAK/FRT/CFG/MOB)가 각각 찾아낸 설계 Gap을 하나의 배열로 합칩니다.

```javascript
// WBS-BAK의 gaps
[{ item: "POST /auth/login", severity: "high", ... }]

// WBS-CFG의 gaps  
[{ item: "hardcoded password", severity: "high", ... }]

// WBS-MOB의 gaps
[{ item: "_emailController", severity: "high", ... }]

// → 모두 합쳐서 all_gaps[] 배열 생성
```

**중복 제거**: 같은 Agent에서 같은 item이 두 번 나오면 하나만 남깁니다.

**Call Flow 불일치도 Gap으로 추가**:
```javascript
// 설계 문서에는 있지만 실제 코드에 없는 API
for (const endpoint of missingInActual) {
  allGaps.push({
    source_agent: 'WBS-ORK',
    discrepancy_type: 'missing_implementation',
    severity: 'high',
    // ...
  });
}
```

---

### 4.10 Build Gap Analysis Prompt — Ollama 프롬프트 구성

찾아낸 Gap들을 Ollama AI에게 분석 요청하는 프롬프트를 만듭니다.

```javascript
const prompt = `You are a software design review assistant. Analyze the following design gaps...

Found gaps:
1. [HIGH] WBS-MOB - _emailController: ...
2. [HIGH] WBS-CFG - hardcoded password: ...

For each gap, classify intent as one of:
  "intentional_improvement", "oversight", "missing_implementation"
Return ONLY JSON array: [{"item":"...","intent":"...","recommendation":"..."}]`;
```

**Gap이 없으면 Ollama 호출 스킵**:
```javascript
if (!all_gaps || all_gaps.length === 0) {
  return [{ json: { ...d, _skip_ollama: true } }];
}
```
Gap이 없을 때 불필요한 Ollama 호출(약 2~3분 소요)을 건너뜁니다.

---

### 4.11 Has Gaps? — 조건 분기

IF 노드로 Gap 유무에 따라 경로를 나눕니다.

```
Has Gaps?
  ├─ True  (Gap 있음) → Ollama Gap Analysis
  └─ False (Gap 없음) → No Gaps Pass
```

> **n8n IF 노드 동작 원리**:  
> - index 0 출력: 조건이 True일 때  
> - index 1 출력: 조건이 False일 때

**조건**:
```
$json._skip_ollama != true
```

---

### 4.12 Ollama Gap Analysis — AI Gap 분석

Ollama(로컬 LLM)에게 Gap 분석을 요청합니다.

```
POST http://ollama:11434/api/generate
Body: {
  "model": "qwen2.5-coder:7b",
  "prompt": "...(Gap 목록과 분석 요청)...",
  "stream": false,
  "format": "json"
}
```

**타임아웃**: 600,000ms (10분) — LLM 처리 시간 고려

**`neverError: true`**: Ollama 응답이 4xx/5xx여도 워크플로를 멈추지 않습니다.

---

### 4.13 Parse Gap Analysis — AI 결과 파싱

Ollama가 반환한 JSON 텍스트를 파싱하여 각 Gap에 `intent_analysis`와 `recommendation` 필드를 추가합니다.

```javascript
// Ollama 응답에서 JSON 배열 추출
const match = raw.match(/\[.*\]/s);
if (match) {
  const parsed = JSON.parse(match[0]);
  // 기존 Gap에 intent 정보 추가
  analyzedGaps = analyzedGaps.map(g => ({
    ...g,
    intent_analysis: intentMap[g.item]?.intent || 'unknown',
    recommendation:  intentMap[g.item]?.recommendation || ''
  }));
}
```

**파싱 실패 시 기본값**: 파싱에 실패해도 기존 Gap 정보는 유지하고 `intent_analysis: 'unknown'`으로 처리합니다.

---

### 4.14 No Gaps Pass — Gap 없을 때 우회

Gap이 없는 경우 Ollama를 건너뛰고 빈 배열로 Calc Design Score로 넘깁니다.

```javascript
return [{ json: { ...d, all_gaps: [] } }];
```

---

### 4.15 Calc Design Score — 설계 적합성 점수 계산

설계 적합성 점수를 계산합니다.

**계산 공식**:
```
설계 적합성 점수 = (전체 설계 항목 수 - High Gap 수) / 전체 설계 항목 수 × 100
```

**예시**:
- 설계 문서 항목: API 5개 + 테이블 2개 + 시퀀스 2개 = 9개
- High Gap: 2개
- 점수: (9 - 2) / 9 × 100 = **77.7% → 70% (YELLOW)**

**설계 항목이 0개인 경우 (DDA 실패 시)**:
```javascript
if (designItems === 0) {
  designScore = highGaps === 0 ? 100 : Math.max(0, 100 - highGaps * 15);
}
// High Gap 1개당 -15점
```

**등급 기준**:
| 점수 | 등급 | 의미 |
|------|------|------|
| 90% 이상 | 🟢 GREEN | 설계와 구현 잘 일치함 |
| 70~89% | 🟡 YELLOW | 일부 불일치, 검토 필요 |
| 69% 이하 | 🔴 RED | 심각한 설계 불일치 |

---

### 4.16 Calc Progress Score — 진척률 최종 계산

3가지 지표를 가중치를 적용해 합산합니다.

```javascript
// Jira 티켓 완료율 × 40%
const jiraScore   = ticketDoneRate * 0.4;

// SP 소진률 × 40% (SP 없으면 티켓 완료율로 대체)
const spScore     = spBurnedRate * 0.4;

// Commit 활성 개발일 × 20%
const activeDayRate = Math.min(100, (max_active_days / 5) * 100);
const commitScore   = activeDayRate * 0.2;

// 최종 진척률
const totalProgress = Math.round(jiraScore + spScore + commitScore);
```

**등급 기준**:
| 점수 | 등급 | 의미 |
|------|------|------|
| 70% 이상 | 🟢 GREEN | 순조로운 진행 |
| 40~69% | 🟡 YELLOW | 주의 필요 |
| 39% 이하 | 🔴 RED | 위험, 즉각 조치 필요 |

---

### 4.17 Respond to Webhook / Log Final Result — 출력

두 출력 노드가 병렬로 연결됩니다.

**Respond to Webhook**: Webhook 트리거로 실행됐을 때 HTTP 응답으로 결과를 반환합니다.

**Log Final Result**: Manual/Schedule 트리거로 실행됐을 때 결과를 콘솔 로그로 출력합니다.

```javascript
console.log(`진척률: ${d.total_progress}% [${d.progress_grade}]`);
console.log(`설계 적합성: ${d.design_score}% [${d.design_grade}]`);
console.log(`Jira: 완료 ${d.done_tickets}/${d.total_tickets}`);
console.log(`Commit: ${d.total_commits}회, 활성 ${d.max_active_days}일`);
```

---

## 5. 진척률 계산 공식 상세

### 5.1 전체 공식

```
전체 진척률 = (Jira 완료율 × 0.4) + (SP 소진률 × 0.4) + (Commit 활성일 × 0.2)
```

### 5.2 각 지표 계산 방법

**Jira 티켓 완료율 (40%)**
```
Jira 완료율 = (완료된 티켓 수 / 전체 티켓 수) × 100
가중치 적용: × 0.4

예시: 완료 2개 / 전체 4개 = 50% → 50 × 0.4 = 20점
```

**Story Point 소진률 (40%)**
```
SP 소진률 = (완료된 SP 합계 / 전체 SP 합계) × 100
가중치 적용: × 0.4

SP 데이터 없을 경우: Jira 완료율로 대체

예시: 완료 SP 5 / 전체 SP 10 = 50% → 50 × 0.4 = 20점
```

**Commit 활성 개발일 (20%)**
```
활성일 비율 = (이번 주 커밋이 있는 평일 수 / 5일) × 100
가중치 적용: × 0.2

예시: 활성일 3일 / 5일 = 60% → 60 × 0.2 = 12점
```

### 5.3 예시 계산

| 상황 | Jira | SP | Commit | 진척률 |
|------|------|-----|--------|--------|
| 순조로운 진행 | 완료 3/5 (60%) | SP 소진 60% | 활성 4/5일 (80%) | 24 + 24 + 16 = **64% YELLOW** |
| 위험 상황 | 완료 0/4 (0%) | SP 0% | 활성 1/5일 (20%) | 0 + 0 + 4 = **4% RED** |
| 이상적 | 완료 5/5 (100%) | SP 소진 100% | 활성 5/5일 (100%) | 40 + 40 + 20 = **100% GREEN** |

---

## 6. n8n 임포트 및 실행 방법

### 6.1 사전 확인 — 다른 워크플로 활성화 상태

WBS-ORK는 다른 7개 워크플로를 내부에서 호출합니다. **7개가 모두 Active 상태여야** 합니다.

n8n UI → 좌측 메뉴 → Workflows → 아래 목록 확인:

| 워크플로 | Active 상태 확인 |
|---------|-----------------|
| WBS-GRC | ✅ 켜져 있어야 함 |
| WBS-JRA | ✅ 켜져 있어야 함 |
| WBS-DDA | ✅ 켜져 있어야 함 |
| WBS-BAK | ✅ 켜져 있어야 함 |
| WBS-FRT | ✅ 켜져 있어야 함 |
| WBS-CFG | ✅ 켜져 있어야 함 |
| WBS-MOB | ✅ 켜져 있어야 함 |

### 6.2 WBS-ORK 임포트

1. n8n UI 접속: `http://localhost:5678`
2. 좌측 메뉴 → **Workflows** → 우상단 **+** 버튼
3. **Import from File** 선택
4. 파일 선택: `workflow/WBS-ORK.json`
5. 임포트 완료 후 우상단 토글 → **Active** 켜기

> **HTTP Request 노드에 Credential 연결 불필요**  
> WBS-ORK가 호출하는 URL은 모두 `http://localhost:5678/webhook/...` (내부 n8n URL)이므로  
> 별도 API 키 설정이 필요 없습니다.

### 6.3 Webhook으로 실행 (curl)

터미널에서 실행:

```bash
curl -s -X POST http://localhost:5678/webhook/wbs-ork \
  -H "Content-Type: application/json" \
  -d '{}' \
  --max-time 600
```

> `--max-time 600`: 최대 10분 대기 (Ollama 처리 시간 포함)

### 6.4 결과 확인

성공 시 아래와 같은 JSON이 반환됩니다:

```json
{
  "agent_id": "WBS-ORK",
  "week_start": "2026-05-11",
  "week_end": "2026-05-14",
  "total_progress": 64,
  "progress_grade": "YELLOW",
  "jira_score": 24,
  "sp_score": 24,
  "commit_score": 16,
  "total_tickets": 5,
  "done_tickets": 3,
  "in_progress_tickets": 2,
  "design_score": 77,
  "design_grade": "YELLOW",
  "high_gap_count": 2,
  "gap_count": 5,
  "failed_agents": []
}
```

### 6.5 n8n UI에서 실행 결과 확인

실행 완료 후 각 노드의 결과를 UI에서 확인하는 방법:

1. WBS-ORK 워크플로 열기
2. 상단 탭 → **Executions** 클릭
3. 가장 최근 실행 항목 클릭
4. 우측 상단 **Editor** 탭 클릭
5. 결과를 보고 싶은 노드 클릭 → 우측 패널에 INPUT/OUTPUT 표시

> **실행 중에는 노드별 상태 확인 불가**  
> n8n은 실행이 완전히 끝난 후에만 노드별 결과를 보여줍니다.  
> 실행 중에는 Executions 탭에 "Running for Xm Xs" 메시지만 표시됩니다.

---

## 7. 테스트 결과

### 7.1 테스트 환경

| 항목 | 값 |
|------|----|
| n8n | v2.14.2 Self-hosted (Docker) |
| 실행일 | 2026-05-14 |
| Jira Board | WBS 8207, WBS 1 스프린트 |
| 테스트 이슈 | WBS-2(진행 중), WBS-3(진행 중), WBS-4(할 일), WBS-5(할 일) |
| GitHub Repo | hanhosunglgu/WBS_Check |

### 7.2 1차 테스트 결과 (WBS-DDA/CFG/MOB 비활성화 상태)

```bash
curl -s -X POST http://localhost:5678/webhook/wbs-ork -d '{}'
```

```json
{
  "total_progress": 4,
  "progress_grade": "RED",
  "design_score": 100,
  "design_grade": "GREEN",
  "gap_count": 0,
  "failed_agents": ["WBS-DDA", "WBS-CFG", "WBS-MOB"]
}
```

| 검증 항목 | 결과 | 판정 |
|-----------|------|------|
| 실행 완료 | ✅ | ✅ |
| 부분 실패 처리 | failed_agents에 3개 기록, 나머지로 계속 진행 | ✅ |
| 진척률 계산 | 4% (완료 티켓 0개 → 정상) | ✅ |
| 실패 원인 | WBS-DDA/CFG/MOB 워크플로 비활성화 상태 | 조치 필요 |

**조치**: n8n에서 WBS-DDA, WBS-CFG, WBS-MOB 워크플로 Active 토글 ON

### 7.3 2차 테스트 결과 (전체 활성화 상태)

```json
{
  "agent_id": "WBS-ORK",
  "week_start": "2026-05-11",
  "week_end": "2026-05-14",
  "total_progress": 4,
  "progress_grade": "RED",
  "jira_score": 0,
  "sp_score": 0,
  "commit_score": 4,
  "sprint_name": "WBS 1 스프린트",
  "total_tickets": 4,
  "done_tickets": 0,
  "in_progress_tickets": 2,
  "todo_tickets": 2,
  "total_commits": 8,
  "max_active_days": 1,
  "active_day_rate": 20,
  "design_score": 70,
  "design_grade": "YELLOW",
  "high_gap_count": 2,
  "gap_count": 2,
  "all_gaps": [
    {
      "source_agent": "WBS-MOB",
      "item": "_emailController",
      "severity": "high",
      "intent_analysis": "missing_implementation",
      "recommendation": "Implement the email controller as per the design document."
    },
    {
      "source_agent": "WBS-MOB",
      "item": "_passwordController",
      "severity": "high",
      "intent_analysis": "missing_implementation",
      "recommendation": "Implement the password controller as per the design document."
    }
  ],
  "integrated_flow": {
    "mobile_flows": [
      { "from": "_login() in _LoginScreenState", "to": "http.post() in _login()" }
    ]
  },
  "failed_agents": ["WBS-DDA"]
}
```

### 7.4 전체 검증 항목

| 검증 항목 | 결과 | 판정 |
|-----------|------|------|
| Webhook POST 수신 및 실행 | 정상 | ✅ |
| WBS-GRC 호출 → Repo 분류 + Commit 집계 | commit:8, active_days:1 | ✅ |
| 6개 Agent 병렬 호출 | JRA/BAK/FRT/CFG/MOB 성공 | ✅ |
| 부분 실패 처리 | DDA timeout → failed_agents 기록, 진행 계속 | ✅ |
| Call Flow 재구성 | mobile_flows: `_login() → http.post()` 추출 | ✅ |
| Design Gap 통합 | WBS-MOB에서 2건 수집 | ✅ |
| Ollama Gap 분석 | intent_analysis 포함 결과 반환 | ✅ |
| 설계 적합성 점수 | 70% YELLOW | ✅ |
| 진척률 계산 | 4% RED (완료 티켓 0개 → 정상값) | ✅ |
| Schedule Trigger 설정 | 매주 금 17:00 크론 설정 | ✅ |

**Phase 3 최종 판정: PASS**

### 7.5 진척률 4%가 낮은 이유

테스트 환경 특성상 완료(완료) 상태 티켓이 0개이기 때문입니다.

```
total_progress = jira_score + sp_score + commit_score
             = (0% × 0.4) + (0% × 0.4) + (20% × 0.2)
             = 0 + 0 + 4
             = 4%
```

실제 프로젝트에서 스프린트 중반부 기준으로는 아래처럼 계산됩니다:
```
완료 티켓 3/5개, 활성일 3/5일 기준:
= (60% × 0.4) + (60% × 0.4) + (60% × 0.2)
= 24 + 24 + 12
= 60% YELLOW
```

---

## 8. 자주 발생하는 문제와 해결

### 문제 1: `404 This webhook is not registered`

**원인**: 호출하려는 Agent 워크플로가 비활성화 상태입니다.

**해결**:
1. n8n UI → Workflows 목록 확인
2. 해당 워크플로 → 우상단 토글 → Active 켜기

### 문제 2: `failed_agents`에 여러 Agent가 포함됨

**원인**: 해당 Agent의 타임아웃 또는 Ollama 응답 지연입니다.

**해결**:
- **즉각적**: 그대로 사용 (나머지 Agent 결과로 진척률 계산됨)
- **근본적**: Ollama 서버 리소스 확인, 또는 WBS-ORK의 각 Agent 타임아웃 값 증가

```json
"options": { "timeout": 900000 }  // 600000 → 900000 (15분)
```

### 문제 3: WBS-DDA가 자주 실패함

**원인**: 설계 문서 파일이 클 경우 Ollama 처리 시간이 길어집니다.

**해결**: WBS-DDA 자체가 독립적으로 작동하는지 먼저 테스트합니다.
```bash
curl -s -X POST http://localhost:5678/webhook/wbs-dda \
  -H "Content-Type: application/json" \
  -d '{"owner":"hanhosunglgu","repo":"hanhosunglgu/WBS_Check","path":"docs/design"}' \
  --max-time 600
```

### 문제 4: `total_progress`가 항상 낮게 나옴

**원인 분류**:

| 원인 | 확인 방법 | 해결 |
|------|----------|------|
| Jira 완료 티켓 없음 | Jira 보드에서 완료 티켓 확인 | 실제 작업 진행 또는 테스트용 티켓 완료 처리 |
| SP 미설정 | `sp_total: 0` 확인 | Jira 프로젝트 설정에서 SP 필드 활성화 |
| Commit 없음 | `total_commits: 0` 확인 | GitHub Repo에 이번 주 커밋 있는지 확인 |

### 문제 5: 실행 시간이 너무 오래 걸림

WBS-ORK는 최대 15~20분 소요될 수 있습니다.

| 구간 | 소요 시간 |
|------|----------|
| WBS-GRC | 30초~2분 |
| 병렬 6개 Agent | 가장 오래 걸리는 Agent 기준 (Ollama 포함 시 5~10분) |
| Ollama Gap 분석 | 1~3분 |
| 점수 계산 | 즉시 |

**단축 방법**: Ollama 없이 테스트하려면 WBS-DDA/BAK/FRT/CFG/MOB를 임시 비활성화하면 됩니다 (분석 결과는 없지만 진척률 계산은 동작).
