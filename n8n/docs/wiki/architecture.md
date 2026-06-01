# 시스템 아키텍처

---

## 전체 구성도

```
┌─────────────────────────────────────────────────────────┐
│                    외부 트리거 레이어                      │
│   [Teams Bot Webhook]      [n8n Cron — 매주 금 17:00]   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              n8n Workflow Engine (Self-hosted)           │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │           WBS-ORK  Orchestration Agent           │   │
│  │  1. Repo 유형 분류 (Backend/Frontend/Config/Mobile)│  │
│  │  2. Specialist Agent 병렬 호출                    │   │
│  │  3. 결과 수집 → 전체 Call Flow 재구성              │   │
│  │  4. 설계 시퀀스 vs 실제 흐름 통합 비교             │   │
│  │  5. 진척률 계산 → 최종 리포트 생성                 │   │
│  └───┬──────────┬──────────┬──────────┬─────────────┘   │
│      │(병렬)    │(병렬)    │(병렬)    │(병렬)            │
│      ▼          ▼          ▼          ▼                  │
│  [WBS-JRA]  [WBS-GRC]  [WBS-DDA]  [WBS-RPT]            │
│  Jira Agent  Repo       Design Doc  Report Agent        │
│              Classifier  Agent                          │
│                  │                                      │
│      ┌───────────┼───────────┬──────────┐               │
│      ▼           ▼           ▼          ▼               │
│  [WBS-BAK]  [WBS-FRT]  [WBS-CFG]  [WBS-MOB]            │
│  Backend    Frontend   Config/IaC  Mobile               │
│  Agent      Agent      Agent       Agent                │
└─────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌──────────────────┐         ┌──────────────────┐
│  외부 데이터 소스 │         │    출력 채널       │
│  • Jira Cloud    │         │  • Teams 채널     │
│  • GitHub API    │         │  • Teams 채널     │
│  • 설계 문서(.md)│         │    (plain text)   │
│  • Ollama LLM    │         └──────────────────┘
└──────────────────┘
```

---

## n8n Workflow 실행 구조

```
[WBS-TRG-001] Teams Webhook  /  [WBS-TRG-002] Cron Scheduler
                          │
                          ▼
              [WBS-ORK] Orchestration Agent
                │
                ├─ Execute Workflow → [WBS-GRC]
                │    └─ 반환: { backend:[...], frontend:[...], config:[...], mobile:[...] }
                │
                ├─ 병렬 Execute Workflow
                │    ├─ [WBS-JRA]  Jira Agent
                │    ├─ [WBS-DDA]  Design Doc Agent
                │    ├─ [WBS-BAK]  Backend Agent
                │    ├─ [WBS-FRT]  Frontend Agent
                │    ├─ [WBS-CFG]  Config/IaC Agent
                │    └─ [WBS-MOB]  Mobile Agent
                │
                ├─ Merge 노드: 전체 결과 취합
                ├─ Code 노드: Call Flow 재구성 (설계 vs 실제)
                ├─ Ollama API: Gap 의도 분석 및 심각도 분류
                ├─ Code 노드: 진척률 계산
                └─ Execute Workflow → [WBS-RPT]
```

---

## 데이터 흐름

```
Trigger
  │
  ▼
[WBS-ORK] Repo 유형 분류
  │
  ├── [WBS-JRA]  Sprint 티켓 수집 ─────────────────────┐
  ├── [WBS-DDA]  설계 문서 파싱 ──────────────────────┤
  ├── [WBS-BAK]  Backend Call Flow 추출 ──────────────┤ 결과
  ├── [WBS-FRT]  Frontend API 호출 흐름 추출 ─────────┤ 취합
  ├── [WBS-CFG]  Config/IaC 설계 vs 실제 비교 ────────┤
  └── [WBS-MOB]  Mobile 화면 흐름 추출 ───────────────┘
                                                      │
  ◄────────────────────────────────────────────────── ┘
  │
  ▼
[WBS-ORK] 통합 분석
  ├─ 설계 시퀀스 vs 실제 흐름 비교
  ├─ Gap 통합 및 심각도 분류
  └─ 진척률 계산
  │
  ▼
[WBS-RPT]
  └─ Teams 채널 메시지 전송
```

---

## Orchestration Agent 내부 노드 구성

```
Webhook / Cron
  → [Set] 실행 파라미터 초기화 (주간 날짜 범위, Repo 목록)
  → [Execute: WBS-GRC] Repo 유형 분류
  → [IF] 각 유형별 분기 (해당 유형 있을 때만 Agent 포함)
  → [Split in Batches] 병렬 Agent 실행
  → [Merge] 전체 결과 수집 대기
  → [Code] Call Flow 재구성 및 Gap 계산
  → [HTTP Request] Ollama API 의도 분석
  → [Code] 진척률 계산 (Jira 40% + SP 40% + Commit 20%)
  → [Execute: WBS-RPT] 리포트 생성 및 전송
```

---

## 사용 API 엔드포인트

### Jira Cloud API

| 기능 | 엔드포인트 |
|------|-----------|
| 활성 Sprint 조회 | `GET /rest/agile/1.0/board/{boardId}/sprint?state=active` |
| Sprint 이슈 조회 | `GET /rest/agile/1.0/sprint/{sprintId}/issue` |
| 이슈 상세 조회 | `GET /rest/api/3/issue/{issueId}` |

### GitHub REST API

| 기능 | 엔드포인트 |
|------|-----------|
| Commit 목록 | `GET /repos/{owner}/{repo}/commits?since={date}&until={date}` |
| Repo 파일 목록 | `GET /repos/{owner}/{repo}/contents/{path}` |
| PR 목록 | `GET /repos/{owner}/{repo}/pulls?state=all&sort=updated` |

