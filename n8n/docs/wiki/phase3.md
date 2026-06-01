# Phase 3 — Orchestration Agent (WBS-ORK) 개발 내역

**완료일**: 2026-05-14  
**담당 Workflow**: `workflow/WBS-ORK.json`  
**노드 수**: 25노드 (기능 노드 17 + Sticky Note 1 + 트리거 3 + 경유 노드 4)

---

## 1. 개요

WBS-ORK는 Phase 1(Specialist Agent)과 Phase 2(JRA/GRC)에서 구현한 모든 Agent를 조율하는 Orchestration Agent다.

**핵심 역할**:
1. 6개 Specialist Agent를 병렬로 호출하고 결과를 수집
2. Call Flow를 레이어별로 재구성하고 설계 문서와 비교
3. 전체 Design Gap을 통합하여 Ollama로 의도 분석
4. Jira 티켓 완료율 × GitHub Commit 빈도 × SP 소진률로 진척률 계산
5. 계산된 지표를 JSON으로 반환 (Phase 4 WBS-RPT 입력 데이터)

---

## 2. 노드 구성 (25노드)

### 트리거 (3개)

| 노드명 | 유형 | 설명 |
|--------|------|------|
| Webhook | Webhook | POST `/webhook/wbs-ork` — Teams Bot 또는 curl 수동 호출 |
| Schedule Trigger | scheduleTrigger | Cron `0 17 * * 5` — 매주 금요일 17:00 자동 실행 |
| Manual Trigger | manualTrigger | n8n UI에서 직접 실행 (테스트용) |

### 초기화 및 GRC 호출 (3개)

| 노드명 | 유형 | 설명 |
|--------|------|------|
| Init Params | Code | 이번 주 월요일 00:00 UTC 계산, 환경변수 읽기 |
| Call WBS-GRC | HTTP Request | POST `/webhook/wbs-grc` — Repo 분류 + Commit 집계 |
| Parse GRC Result | Code | GRC 결과 파싱, backend/frontend/config/mobile 분류 |

### 병렬 Agent 호출 (6개)

| 노드명 | 호출 대상 | Timeout |
|--------|-----------|---------|
| Call WBS-JRA | `/webhook/wbs-jra` | 300초 |
| Call WBS-DDA | `/webhook/wbs-dda` | 600초 |
| Call WBS-BAK | `/webhook/wbs-bak` | 600초 |
| Call WBS-FRT | `/webhook/wbs-frt` | 600초 |
| Call WBS-CFG | `/webhook/wbs-cfg` | 600초 |
| Call WBS-MOB | `/webhook/wbs-mob` | 600초 |

6개 노드 모두 `neverError: true` 설정 — 개별 Agent 실패 시 워크플로 중단 없이 계속 진행.

### 결과 취합 및 분석 (9개)

| 노드명 | 유형 | 설명 |
|--------|------|------|
| Merge All Results | Merge | `numberInputs: 6` — 6개 입력 모두 수렴 후 다음 노드 진행 |
| Integrate Results | Code | agent_id 기준 resultMap 구성, 부분 실패 기본값 대체 |
| Build Call Flow Map | Code | Mobile/Frontend/Backend 레이어 정렬, 엔드포인트 비교 |
| Merge Design Gaps | Code | 4개 Agent Gap 통합, 중복 제거, Call Flow 불일치 추가 |
| Build Gap Analysis Prompt | Code | Ollama 프롬프트 구성, Gap 없으면 `_skip_ollama: true` |
| Has Gaps? | IF | `_skip_ollama` 분기 — 있으면 Ollama 호출, 없으면 No Gaps Pass |
| Ollama Gap Analysis | HTTP Request | Ollama `qwen2.5-coder:7b` 호출 — 의도 분류 |
| Parse Gap Analysis | Code | Ollama JSON 응답 파싱, intent_analysis 필드 추가 |
| No Gaps Pass | Code | Gap 없는 경우 — 빈 all_gaps로 다음 단계 진행 |

### 점수 계산 및 출력 (4개)

| 노드명 | 유형 | 설명 |
|--------|------|------|
| Calc Design Score | Code | 설계 적합성 점수 계산, 등급 분류 |
| Calc Progress Score | Code | 진척률 최종 계산, 등급 분류, 전체 Output 구성 |
| Respond to Webhook | respondToWebhook | Webhook 호출 시 JSON 응답 반환 |
| Log Final Result | Code | Manual/Schedule 실행 시 콘솔 출력 |

---

## 3. 핵심 계산 로직

### 진척률 공식 (Calc Progress Score)

```
진척률 = (Jira 티켓 완료율 × 0.4) + (SP 소진률 × 0.4) + (Commit 활성일률 × 0.2)

Commit 활성일률 = min(100, max_active_days / 5 × 100)
SP 데이터 없으면 → SP 소진률 = Jira 티켓 완료율로 대체
```

**등급 기준**:
- GREEN: 70% 이상
- YELLOW: 40% 이상
- RED: 40% 미만

### 설계 적합성 공식 (Calc Design Score)

```
설계 적합성 = (설계 항목 수 - High Gap 수) / 설계 항목 수 × 100

설계 항목 = DDA endpoints 수 + tables 수 + sequences 수
설계 항목이 0이면 → Gap 없으면 100점, High Gap 1건당 15점 차감
```

**등급 기준**:
- GREEN: 90% 이상
- YELLOW: 70% 이상
- RED: 70% 미만

### 부분 실패 처리 (Integrate Results)

```javascript
const resultMap = {};
for (const item of items) {
  const id = item.json.agent_id || 'unknown';
  resultMap[id] = item.json;
}

const jra = resultMap['WBS-JRA'] || { total_tickets: 0, error: 'skipped', ... };
const dda = resultMap['WBS-DDA'] || { endpoints: [], error: 'skipped', ... };
// ... BAK, FRT, CFG, MOB 동일 패턴

const failedAgents = [jra,dda,bak,frt,cfg,mob]
  .filter(a => a.error && a.error !== null)
  .map(a => a.agent_id);
```

---

## 4. Output 스키마

WBS-ORK 최종 출력 (`Calc Progress Score` 노드):

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
  "sprint_id": 15902,
  "sprint_name": "WBS 1 스프린트",
  "total_tickets": 4,
  "done_tickets": 0,
  "in_progress_tickets": 2,
  "in_review_tickets": 0,
  "todo_tickets": 2,
  "sp_total": 0,
  "sp_burned": 0,
  "sp_burned_rate": 0,
  "ticket_done_rate": 0,
  "total_commits": 8,
  "max_active_days": 1,
  "active_day_rate": 20,
  "design_score": 70,
  "design_grade": "YELLOW",
  "design_items_total": 0,
  "high_gap_count": 2,
  "medium_gap_count": 0,
  "low_gap_count": 0,
  "gap_count": 2,
  "all_gaps": [...],
  "integrated_flow": { "design_sequences": [], "mobile_flows": [...], ... },
  "endpoint_match_rate": 100,
  "missing_in_actual": [],
  "extra_in_actual": [],
  "failed_agents": ["WBS-DDA"],
  "error": null
}
```

---

## 5. 이슈 해결 내역

### 이슈 1: Webhook 404 "not registered for POST requests"

**원인**: Webhook 노드에 `httpMethod` 파라미터 없음 → n8n 기본값 GET으로 등록.

**해결**: Webhook 노드 파라미터 추가:
```json
{
  "httpMethod": "POST",
  "responseMode": "responseNode",
  "typeVersion": 2
}
```

**학습**: n8n Webhook 노드는 `typeVersion: 2` + `httpMethod` 명시 필수. `responseMode: "responseNode"`로 설정해야 Respond to Webhook 노드가 응답 제어권 가짐.

---

### 이슈 2: failed_agents 3개 (1차 테스트)

**원인**: WBS-DDA, WBS-CFG, WBS-MOB 워크플로 비활성화 상태 — 404 반환.

**해결**: n8n Workflows 탭에서 3개 수동 활성화.

**왜 워크플로가 멈추지 않았나**: 모든 Agent 호출 노드에 `neverError: true` 설정 → 4xx/5xx도 정상 응답으로 처리, error 필드에 내용 기록.

---

### 이슈 3: WBS-DDA timeout (2차 테스트 — 지속 이슈)

**현상**: `failed_agents: ["WBS-DDA"]` 지속.

**원인**: Ollama `qwen2.5-coder:7b`가 대용량 설계 문서 분석 시 응답 시간이 n8n Webhook timeout 초과.

**상태**: Phase 1부터 알려진 환경 이슈. `N8N_WEBHOOK_TIMEOUT=900`으로 완화했으나 문서 크기에 따라 재발 가능.

**판정**: WBS-ORK 로직 자체는 정상 — failed_agents 목록에 기록하고 나머지 데이터로 계속 진행.

---

## 6. 테스트 결과

### 1차 테스트 — 부분 실패 케이스

**조건**: WBS-DDA/CFG/MOB 비활성화 상태

```
total_progress: 4  [RED]
design_score:   70 [YELLOW]
failed_agents:  ["WBS-DDA", "WBS-CFG", "WBS-MOB"]
```

**확인 사항**: 3개 Agent 실패에도 JRA/BAK/FRT 데이터로 진척률 계산 정상 완료.

### 2차 테스트 — 정상 케이스

**조건**: 전체 Agent 활성화 (DDA는 Ollama timeout으로 실패)

```
total_progress:      4%    [RED]    — 완료 티켓 0개 / 전체 4개
design_score:       70%   [YELLOW] — High Gap 2건 (MOB 컨트롤러 초기화)
failed_agents:  ["WBS-DDA"]        — Ollama timeout 환경 이슈
total_commits:       8
max_active_days:     1
active_day_rate:    20%
```

**판정**: **PASS** — WBS-ORK 로직 정상 동작 확인. DDA timeout은 Ollama 환경 이슈로 별도 추적.

---

## 7. Phase 4 연동 인터페이스

WBS-RPT(Phase 4)는 WBS-ORK의 Webhook을 POST 호출하고 응답 JSON을 사용한다.

```bash
# WBS-RPT가 WBS-ORK를 호출하는 방식
POST http://localhost:5678/webhook/wbs-ork
Content-Type: application/json
{}

# 응답: WBS-ORK Output 스키마 전체
```

**WBS-RPT에서 사용할 핵심 필드**:

| 필드 | 용도 |
|------|------|
| `total_progress`, `progress_grade` | Teams 메시지 헤더 진척률 표시 |
| `done_tickets`, `total_tickets`, `incomplete_tickets` | Teams 메시지 Jira 현황 섹션 |
| `design_score`, `design_grade`, `all_gaps` | Teams 메시지 설계 적합성 섹션 |
| `total_commits`, `max_active_days` | Teams 메시지 GitHub 활동 섹션 |
| `week_start`, `week_end` | 주차 구분 |
