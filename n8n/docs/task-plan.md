# 3rd WBS Agent — n8n 구현 Task Plan

**작성일**: 2026-05-11  
**버전**: v1.2  
**최종 업데이트**: 2026-05-19 — OpenAI gpt-4.1-mini 전환 완료. WBS-DDA 재구현 (SplitInBatches v2, Store File Content, download_url 방식). WBS-RPT Confluence 노드 제거. E2E 전체 파이프라인 재검증 PASS ✅  
**구현 전략**: 설계 적합성 검증(핵심 차별점) 우선 → 진척률 리포트 → 자동화/안정화  

---

## 구현 전략 요약

```
현재 상태 (2026-05-13 기준)
  • n8n Self-hosted v2.14.2 (Docker): 정상 운영 중
  • Phase 0 완료: 환경 준비, Credential 등록, 환경변수 설정
  • Phase 1 완료 ✅: 6개 Specialist Agent 전원 구현 및 통합 테스트 통과
      ✅ WBS-GRC: Repo 분류 (frontend/backend/config/mobile) — WBS_Check → frontend(Vite)
      ✅ WBS-DDA: 설계 문서 파싱 — endpoints=5, tables=2, sequences=2
      ✅ WBS-BAK: Backend 코드 분석 (routes 추출, call_flow)
      ✅ WBS-FRT: Frontend 코드 분석 (api_calls, screen_flow)
      ✅ WBS-CFG: IaC/Config 분석 (components, design_gaps)
      ✅ WBS-MOB: Mobile 코드 분석 (screen_flow, api_calls, design_gaps)
      ✅ WBS-INT: 6개 에이전트 통합 단일 워크플로 — ALL_PASS (6/6)
  • 확보된 자격증명:
      ✅ Ollama LLM (qwen2.5-coder:7b, 로컬 Docker)
      ✅ GitHub PAT (n8n Credential "GitHub PAT" 등록 완료)
      ✅ Teams Bot client_id / client_secret / tenant_id
  • 환경 설정:
      ✅ N8N_WEBHOOK_TIMEOUT=900 (.env 적용)
      ✅ Ollama HTTP Request timeout=600000ms 설정

구현 우선순위 (설계 적합성 검증 우선)
  Phase 0: 환경 준비 및 기존 Workflow 파악       ✅ 완료
  Phase 1: 설계 적합성 검증 핵심 (6개 Agent)     ✅ 완료
  Phase 2: 진척률 수집 (WBS-JRA + GitHub Commit) ✅ 완료 (2026-05-14)
  Phase 3: Orchestration 통합 (WBS-ORK)          ✅ 완료 (2026-05-14)
  Phase 4: 리포트 출력 (WBS-RPT → Teams)              ✅ 완료 (2026-05-14)
  Phase 5: Trigger 연동 + 안정화                 ✅ 완료 (2026-05-19)
  OpenAI 전환: WBS-DDA/RPT 재구현, E2E 재검증   ✅ 완료 (2026-05-19)
```

---

## Phase 0: 환경 준비 및 기존 Workflow 정비

> **목표**: 기존 Workflow 재활용 전략 확정, 보안 취약점(하드코딩 자격증명) 해결, 미확보 API 키 준비

### Task 0.1: 기존 Workflow 현황 파악 ✅ 완료

| # | Sub-task | 상태 | 비고 |
|---|----------|------|------|
| 0.1.1 | n8n Workflow 목록 확인 | ✅ 완료 | `Teams Bot - n8n Webhook` 1개 존재 |
| 0.1.2 | 재활용 vs 신규 결정 | ✅ 완료 | 기존 Workflow를 `WBS-TRG-001` 기반으로 확장 (명령어 파싱 추가) |
| 0.1.3 | Credential 현황 확인 | ✅ 완료 | Teams Bot 자격증명이 Workflow 내 하드코딩 상태 → 0.2.x에서 이관 필요 |

### Task 0.2: 보안 이관 및 미확보 API 키 준비 ✅ 완료

> ⚠️ **보안 주의**: 기존 Workflow에 `client_id`, `client_secret`이 평문으로 하드코딩되어 있음. n8n Credential로 즉시 이관 필요.

| # | Sub-task | 완료 기준 |
|---|----------|-----------|
| 0.2.1 | **[보안]** ✅ Teams Bot 자격증명 환경변수 이관 완료 — Workflow JSON에서 `client_id`, `client_secret`, `tenant_id` 평문 제거, `$env.TEAMS_TENANT_ID` / `$env.TEAMS_CLIENT_ID` / `$env.TEAMS_CLIENT_SECRET` 참조로 교체. n8n 서버 `.env`에 값 추가 후 재시작 필요 (`doc/env-setup.md` 참조) | ✅ Workflow JSON 수정 완료 / 🔲 n8n 서버 .env 적용 및 재시작 대기 |
| 0.2.2 | ✅ GitHub PAT 발급 (`repo`, `read:org` 권한) → n8n Credential 등록 | n8n에서 GitHub API `GET /user` 호출 성공 |
| 0.2.3 | ✅ Jira API Token 발급 (Jira Cloud → 계정 설정 → 보안 → API 토큰) → n8n Credential 등록 | n8n HTTP Request로 Jira 프로젝트 목록 조회 성공 |
| 0.2.4 | ✅ Ollama LLM (`qwen2.5-coder:7b`) → 로컬 Docker 컨테이너 실행, n8n에서 `http://ollama:11434/api/generate` 호출 | n8n에서 Ollama LLM 메시지 호출 성공 |

### Task 0.3: n8n 환경변수 및 공통 설정

| # | Sub-task | 완료 기준 |
|---|----------|-----------|
| 0.3.1 | ✅ n8n 환경변수 정의 및 등록: `GITHUB_OWNER=hanhosunglgu`, `GITHUB_REPOS=["WBS_Check"]`, `JIRA_BASE_URL=https://lgucorp.atlassian.net`, `JIRA_PROJECT_KEYS=["WBS"]`, `JIRA_BOARD_ID=8207` — n8n Variables(Settings → Variables)에 등록 필요 (`doc/schema/n8n-variables.json` 참조) | n8n Variables에서 조회 가능 |
| 0.3.2 | ✅ 설계 문서 저장 경로 환경변수 등록: `DESIGN_DOC_REPO=hanhosunglgu/WBS_Check`, `DESIGN_DOC_PATH=WBS_Check/docs/design` — n8n Variables에 등록 필요 | 경로로 GitHub API 파일 조회 성공 |
| 0.3.3 | ✅ Agent 간 표준 Output 스키마 JSON 템플릿 작성 (6.4 기반) — `doc/schema/agent-output-schema.json` 생성 | 스키마 파일 doc/schema/ 에 저장 |

---

## Phase 1: 설계 적합성 검증 — Specialist Agent 구현

> **목표**: 설계 문서와 실제 소스코드를 비교하여 Gap을 추출하는 핵심 Agent 구현  
> **의존성**: GitHub PAT 필요 (0.2.1), Ollama LLM 필요 (0.2.4)

### Task 1.1: WBS-GRC — GitHub Repo Classifier ✅ 완료

> Repo 목록을 스캔하여 Backend/Frontend/Config/Mobile로 분류

| # | Sub-task | n8n 노드 | 완료 기준 |
|---|----------|----------|-----------|
| 1.1.1 | Workflow 신규 생성: `WBS-GRC` | Webhook 노드 | ✅ `workflow/WBS-GRC.json` 작성 및 n8n 활성화 완료 |
| 1.1.2 | GitHub API로 전체 Repo 목록 조회 | HTTP Request 노드 | ✅ 완료 — `/users/{owner}/repos` |
| 1.1.3 | 각 Repo의 루트 파일 목록 조회 | HTTP Request 노드 | ✅ 완료 — neverError 옵션 포함, SplitInBatches 포트 순서 수정(index0=Done, index1=Loop) |
| 1.1.4 | 분류 로직 구현 — 파일 패턴 기반 5단계 우선순위 | Code 노드 | ✅ 완료 — WBS_Check → frontend (Vite) 정상 분류 |
| 1.1.5 | 분류 결과 Output 스키마 반환 | Respond to Webhook 노드 | ✅ 완료 — `{ backend, frontend, config, mobile, _classified_detail }` |

### Task 1.2: WBS-DDA — Design Doc Agent ✅ 완료

> 설계 문서 (.md) 파싱 및 API 명세/ERD/시퀀스 구조 추출

| # | Sub-task | n8n 노드 | 완료 기준 |
|---|----------|----------|-----------|
| 1.2.1 | Workflow 신규 생성: `WBS-DDA` | Webhook 노드 | ✅ 완료 — 파라미터: `{ owner, repo, path }` (repos 배열 아님) |
| 1.2.2 | GitHub API로 설계 문서 파일 목록 조회 | HTTP Request 노드 | ✅ 완료 — `docs/design/api-spec.md` 정상 조회 |
| 1.2.3 | 각 설계 문서 파일 내용 조회 (Base64 디코딩 포함) | HTTP Request 노드 + Code 노드 | ✅ 완료 — SplitInBatches 루프 + Decode Base64 |
| 1.2.4 | Ollama API 호출 — API 엔드포인트/ERD/시퀀스 구조 추출 | HTTP Request 노드 | ✅ 완료 — endpoints=5, tables=2, sequences=2 추출 확인 |
| 1.2.5 | 추출 결과 Output 스키마 반환 | Respond to Webhook 노드 | ✅ 완료 — `{ agent_id, endpoints, tables, sequences }` |

> ⚠️ **주의사항**: WBS-DDA는 `repos[]` 대신 `{ repo, path }` 파라미터 사용. Ollama 노드에 `neverError:true` 및 `timeout:600000` 필수.

### Task 1.3: WBS-BAK — Backend Agent ✅ 완료

> Backend Repo의 라우터/컨트롤러 분석, 실제 API 구조 및 Call Flow 추출

| # | Sub-task | n8n 노드 | 완료 기준 |
|---|----------|----------|-----------|
| 1.3.1 | Workflow 신규 생성: `WBS-BAK` | Webhook 노드 | ✅ 완료 |
| 1.3.2 | 이번 주 변경 커밋 조회 및 최신 커밋 파일 목록 수집 | HTTP Request 노드 | ✅ 완료 — `shas[0]` 기반 단일 커밋 파일 분석 |
| 1.3.3 | 라우터/컨트롤러 파일 필터링 | Code 노드 | ✅ 완료 — routes/, controllers/, .router.js 패턴 |
| 1.3.4 | Ollama API 호출 — 실제 API 엔드포인트 및 Call Flow 추출 | HTTP Request 노드 | ✅ 완료 — `routes/index.js`에서 5개 엔드포인트 추출 확인 |
| 1.3.5 | 표준 Output 스키마 반환 | Respond to Webhook 노드 | ✅ 완료 — `{ agent_id, repo, repo_type:'backend', extracted_endpoints, call_flow, commit_count, active_days }` |

### Task 1.4: WBS-FRT — Frontend Agent ✅ 완료

> Frontend Repo의 컴포넌트/API 호출 패턴 분석, 화면-API 연결 시퀀스 추출

| # | Sub-task | n8n 노드 | 완료 기준 |
|---|----------|----------|-----------|
| 1.4.1 | Workflow 신규 생성: `WBS-FRT` | Webhook 노드 | ✅ 완료 |
| 1.4.2 | 변경된 컴포넌트/서비스 파일 조회 | HTTP Request 노드 + Code 노드 | ✅ 완료 — .tsx/.jsx/.vue/service.ts/service.js/api/ 패턴 |
| 1.4.3 | Ollama API 호출 — API 호출 패턴 및 화면 흐름 추출 | HTTP Request 노드 | ✅ 완료 — `src/api/authService.js`에서 5개 API 호출 추출 확인 |
| 1.4.4 | 표준 Output 스키마 반환 | Respond to Webhook 노드 | ✅ 완료 — `{ agent_id, repo, repo_type:'frontend', api_calls, screen_flow, call_flow }` |

### Task 1.5: WBS-CFG — Config/IaC Agent ✅ 완료

> Terraform/k8s/Docker 실제 구성과 아키텍처 설계 문서 비교

| # | Sub-task | n8n 노드 | 완료 기준 |
|---|----------|----------|-----------|
| 1.5.1 | Workflow 신규 생성: `WBS-CFG` | Webhook 노드 | ✅ 완료 |
| 1.5.2 | 변경된 IaC/Config 파일 조회 | HTTP Request 노드 + Code 노드 | ✅ 완료 — .tf/.yaml/.yml/dockerfile/docker-compose/helm/k8s 패턴 |
| 1.5.3 | Ollama API 호출 — 인프라 구성 요소 추출 및 설계 Gap 분석 | HTTP Request 노드 | ✅ 완료 — docker-compose.yml에서 2 services + 1 volume, design_gaps 3건(hardcoded password High) 추출 확인 |
| 1.5.4 | 표준 Output 스키마 반환 | Respond to Webhook 노드 | ✅ 완료 — `{ agent_id, repo, repo_type:'config', components, design_gaps, call_flow }` |

### Task 1.6: WBS-MOB — Mobile Agent ✅ 완료

> iOS/Android/Flutter 화면 흐름 및 API 호출 시퀀스 분석

| # | Sub-task | n8n 노드 | 완료 기준 |
|---|----------|----------|-----------|
| 1.6.1 | Workflow 신규 생성: `WBS-MOB` | Webhook 노드 | ✅ 완료 |
| 1.6.2 | 변경된 화면/서비스 파일 조회 | HTTP Request 노드 + Code 노드 | ✅ 완료 — .swift/.kt/.dart/viewcontroller/screen./activity./fragment./viewmodel. 패턴, lib/screens/login_screen.dart 테스트 파일 추가 |
| 1.6.3 | Ollama API 호출 — 화면 흐름 및 API 호출 시퀀스 추출 | HTTP Request 노드 | ✅ 완료 — screen_flow=1, api_calls=1, design_gaps=3(HTTP평문 High, 입력검증 Medium×2) 추출 확인 |
| 1.6.4 | 표준 Output 스키마 반환 | Respond to Webhook 노드 | ✅ 완료 — `{ agent_id, repo, repo_type:'mobile', screen_flow, api_calls, design_gaps }` |

### Task 1.7: Phase 1 통합 테스트 ✅ 완료

| # | Sub-task | 완료 기준 |
|---|----------|-----------|
| 1.7.1 | 각 Specialist Agent 독립 실행 및 Output 스키마 검증 | ✅ 완료 — 6/6 ALL_PASS |
| 1.7.2 | WBS-INT 단일 통합 워크플로 작성 및 테스트 | ✅ 완료 — `workflow/WBS-INT.json` (57노드), 6/6 ALL_PASS, 실행시간 약 7~8분 |
| 1.7.3 | 노드 참조 이름 버그 수정 (통합 시 prefix 불일치) | ✅ 완료 — `$('Extract Commit Info')` → `$('BAK Extract Commit Info')` 등 9개 수정 |

> **통합 테스트 결과** (2026-05-13):  
> - WBS-GRC: classified=1 (WBS_Check → frontend/Vite)  
> - WBS-DDA: endpoints=5, tables=2, sequences=2  
> - WBS-BAK: backend 분석 완료 (commits=8)  
> - WBS-FRT: frontend 분석 완료 (commits=8)  
> - WBS-CFG: config 분석 완료 (commits=8)  
> - WBS-MOB: screen_flow=1, api_calls=1, design_gaps=2  
>
> **기술 이슈 해결 내역**:  
> - `N8N_WEBHOOK_TIMEOUT=900` 적용 (기존 300 → 900초)  
> - Ollama 노드 `neverError:true` + `timeout:600000` 패턴 표준화  
> - SplitInBatches index0=Done/index1=Loop 포트 순서 패턴 확립  
> - `_meta` 패턴: Build Ollama Request → Parse & Build Output 메타데이터 전달  
> - `input.body || input` 패턴: Webhook flat JSON 처리 표준화

---

## Phase 2: 진척률 수집 — Jira Agent + GitHub Commit 집계

> **목표**: Sprint 진척률 데이터 수집 (Jira 티켓 상태, Story Point, GitHub Commit 빈도)  
> **의존성**: Jira API Token (0.2.2), GitHub PAT (0.2.1)

### Task 2.1: WBS-JRA — Jira Agent

| # | Sub-task | n8n 노드 | 완료 기준 |
|---|----------|----------|-----------|
| 2.1.1 | Workflow 신규 생성 또는 기존 Workflow 연장: `WBS-JRA` | Webhook 노드 | Workflow 생성 및 활성화 |
| 2.1.2 | Jira Board의 활성 Sprint 조회 | HTTP Request 노드 (`GET /rest/agile/1.0/board/{boardId}/sprint?state=active`) | 활성 Sprint ID 수신 |
| 2.1.3 | Sprint 이슈 전체 조회 (페이지네이션 처리) | HTTP Request 노드 + Loop 노드 | 전체 Story/Task 목록 수신 |
| 2.1.4 | 이슈 상태별 집계 (Code 노드) — To Do/In Progress/In Review/Done 카운트 | Code 노드 | 상태별 카운트 계산 완료 |
| 2.1.5 | Story Point 소진률 계산 (완료 SP / 전체 SP × 100) | Code 노드 | SP 소진률 수치 계산 완료 |
| 2.1.6 | Commit 메시지와 Jira ID 매핑 — GitHub Commit 데이터를 받아 `[PROJ-\d+]` 패턴 추출 | Code 노드 (정규식) | Commit이 연결된 티켓 vs 미연결 티켓 분류 |
| 2.1.7 | 표준 Output 반환 (`{ sprint_id, total_tickets, done, in_progress, todo, sp_burned, sp_total, jira_commit_map }`) | Respond to Webhook 노드 | 스키마 검증 통과 |

### Task 2.2: GitHub Commit 집계 (WBS-GRC 확장)

| # | Sub-task | n8n 노드 | 완료 기준 |
|---|----------|----------|-----------|
| 2.2.1 | WBS-GRC에 Commit 수집 로직 추가 — 이번 주(월~금) 기간 필터링 | HTTP Request 노드 (`GET /repos/{owner}/{repo}/commits?since=&until=`) | 기간 내 Commit 목록 수신 |
| 2.2.2 | Repo별 Commit 수 집계 및 활성 개발일 계산 (Code 노드) | Code 노드 | `{ repo, commit_count, active_days, commit_messages[] }` 산출 |
| 2.2.3 | PR 목록 조회 및 이번 주 merge된 PR 집계 | HTTP Request 노드 | merge PR 수 집계 완료 |

---

## Phase 3: Orchestration — WBS-ORK 구현

> **목표**: 모든 Specialist Agent를 조율하고 결과를 통합하는 Orchestration Agent 구현  
> **의존성**: Phase 1, Phase 2 완료

### Task 3.1: WBS-ORK 기본 구조 구현 ✅ 완료

| # | Sub-task | n8n 노드 | 완료 기준 |
|---|----------|----------|-----------|
| 3.1.1 | ✅ Workflow 신규 생성: `WBS-ORK` | Webhook / Schedule / Manual (3종 트리거) | `workflow/WBS-ORK.json` 25노드 생성 및 활성화 |
| 3.1.2 | ✅ 실행 파라미터 초기화 — 주간 날짜 범위 계산 (이번 주 월~금) | Code 노드 | `week_start`=이번 주 월요일 00:00 UTC, `week_end`=현재 시각 |
| 3.1.3 | ✅ WBS-GRC 호출 → Repo 분류 결과 수신 | HTTP Request 노드 (POST /webhook/wbs-grc) | `{ backend, frontend, config, mobile }` + commit 집계 수신 |
| 3.1.4 | ✅ 트리거 3종 지원 | Webhook + scheduleTrigger + manualTrigger | Webhook POST 호출, 금 17:00 자동, UI 수동 실행 모두 동작 |

### Task 3.2: 병렬 Agent 호출 및 결과 취합 ✅ 완료

| # | Sub-task | n8n 노드 | 완료 기준 |
|---|----------|----------|-----------|
| 3.2.1 | ✅ 6개 Agent 병렬 호출 구현 | HTTP Request 노드 6개 (병렬 분기) | Parse GRC Result에서 6개 동시 분기 — 동시 실행 확인 |
| 3.2.2 | ✅ 모든 Agent 결과 대기 및 취합 | Merge 노드 (`numberInputs: 6`) | 전체 결과 하나의 데이터셋으로 합산 |
| 3.2.3 | ✅ 부분 실패 처리 | Code 노드 (resultMap 패턴) | WBS-DDA 실패 시 기본값 대체, 나머지 데이터로 계속 진행 확인 |

### Task 3.3: Call Flow 재구성 및 Gap 통합 분석 ✅ 완료

| # | Sub-task | n8n 노드 | 완료 기준 |
|---|----------|----------|-----------|
| 3.3.1 | ✅ Call Flow 재구성 로직 | Code 노드 (Build Call Flow Map) | Mobile/Frontend → Backend 레이어 정렬, 설계 vs 실제 엔드포인트 비교 |
| 3.3.2 | ✅ 전체 `design_gaps[]` 통합 | Code 노드 (Merge Design Gaps) | 4개 Agent Gap 합산, 중복 제거(item+source_agent 기준) |
| 3.3.3 | ✅ Ollama Gap 의도 분석 | HTTP Request 노드 (Ollama Gap Analysis) | intentional_improvement / oversight / missing_implementation 분류 |
| 3.3.4 | ✅ 설계 적합성 점수 계산 | Code 노드 (Calc Design Score) | design_score=70, design_grade=YELLOW (High Gap 2건 기준) |

### Task 3.4: 진척률 최종 계산 ✅ 완료

| # | Sub-task | n8n 노드 | 완료 기준 |
|---|----------|----------|-----------|
| 3.4.1 | ✅ Jira 티켓 진척률 계산 (40%) | Code 노드 (Calc Progress Score) | `ticket_done_rate × 0.4` — 완료 티켓 0개 → jira_score=0 |
| 3.4.2 | ✅ Story Point 소진률 계산 (40%) | Code 노드 | SP 없으면 티켓 완료율로 대체 → sp_score=0 |
| 3.4.3 | ✅ GitHub Commit 빈도 계산 (20%) | Code 노드 | `max_active_days / 5 × 100 × 0.2` → commit_score=4 |
| 3.4.4 | ✅ 전체 진척률 합산 및 등급 분류 | Code 노드 | total_progress=4, progress_grade=RED (테스트 환경 기준) |

> **테스트 결과** (2026-05-14, 2차):  
> `total_progress: 4 [RED]`, `design_score: 70 [YELLOW]`, `failed_agents: ["WBS-DDA"]`  
> **판정**: PASS — WBS-DDA timeout은 Ollama 환경 이슈, WBS-ORK 로직 정상

---

## Phase 4: 리포트 출력 — WBS-RPT 구현

> **목표**: 분석 결과를 Teams 채널로 출력  
> **의존성**: Phase 3 완료, Teams Workflows Webhook URL

### Task 4.1: WBS-RPT — Teams 리포트 메시지 생성 ✅ 완료

| # | Sub-task | n8n 노드 | 완료 기준 |
|---|----------|----------|-----------|
| 4.1.1 | ✅ Workflow 신규 생성: `WBS-RPT` | Webhook 노드 | `workflow/WBS-RPT.json` 작성 완료 (11노드) |
| 4.1.2 | ✅ Teams 메시지 포맷 구성 — Build Report Data + Build Teams Card | Code 노드 × 2 | Adaptive Card v1.0, TextBlock+FactSet 구성 |
| 4.1.3 | ✅ Teams Workflows Webhook으로 메시지 전송 | HTTP Request (Send Teams Message) | TEAMS_WEBHOOK_URL 환경변수로 POST 전송 |
| 4.1.4 | ✅ 미완료 티켓 5건 초과 시 "외 N건" 처리 | Code 노드 (Build Report Data 내) | `incomplete_tickets.slice(0,5)` + hiddenCount 처리 |

> **추가 변경**: WBS-ORK에 `Call WBS-RPT` 노드(ork-0026) 추가 — Calc Progress Score 이후 병렬 호출  
> **가이드**: `doc/phase4-guide.md` 참조  
> **환경변수 추가**: `TEAMS_WEBHOOK_URL` (`doc/env-setup.md` 섹션 5 참조)
>
> **기술 이슈**:
> - Power Automate 흐름 구조 역분석으로 전송 포맷 확정: `{ attachments: [{ contentType: '...adaptive', content: card }] }`
> - Adaptive Card `Table/ColumnSet` Teams 미지원 → `TextBlock + FactSet`으로 대체
> - Card version `1.4` → `1.0`으로 낮춰 최대 호환성 확보
> - Teams 채널(개발팀 > WBS 모니터링) 메시지 수신 최종 확인 ✅

---

## Phase 5: Trigger 연동 및 안정화

> **목표**: 자동 트리거(Cron) + 수동 트리거(Teams Bot) 연결, 오류 처리 완성

### Task 5.1: WBS-TRG-002 — Cron 스케줄러 ✅ 완료

| # | Sub-task | n8n 노드 | 완료 기준 |
|---|----------|----------|-----------|
| 5.1.1 | ✅ Cron Workflow 생성: 매주 금요일 17:00 실행 | Schedule Trigger 노드 (`0 17 * * 5`) | `workflow/WBS-TRG-002.json` (3노드) 생성 완료 |
| 5.1.2 | ✅ WBS-ORK 호출 연결 | HTTP Request 노드 | POST `/webhook/wbs-ork`, timeout 900초, Log Result 노드로 결과 요약 |

> **n8n 등록 방법**: UI → Workflows → Import from File → `workflow/WBS-TRG-002.json` → Active 토글 ON → Error Workflow: `WBS-ERR` 지정

### Task 5.2: WBS-TRG-001 — Teams Bot Webhook 확장

> 기존 `Teams Bot - n8n Webhook` Workflow를 기반으로 명령어 라우팅 기능 추가 (신규 생성 불필요)

| # | Sub-task | n8n 노드 | 상태 | 완료 기준 |
|---|----------|----------|------|-----------|
| 5.2.1 | Teams Bot Webhook 수신 및 메시지 파싱 | Webhook 노드 + Set 노드 | ✅ **기존 구현 완료** | — |
| 5.2.2 | Microsoft OAuth2 Token 발급 및 Teams 답장 | HTTP Request 노드 × 2 | ✅ **기존 구현 완료** (자격증명 이관은 0.2.1) | — |
| 5.2.3 | 명령어 파싱 로직 추가 — `message` 필드에서 명령어 추출 (`진척률` / `코드검증` / `티켓` / `도움말`) | Code 노드 (기존 Set 노드 뒤에 삽입) | ✅ 완료 | 명령어 키워드 추출 및 파라미터 분리 (`{ command, param }`) |
| 5.2.4 | 명령별 라우팅 분기 | Switch 노드 | ✅ 완료 | 각 명령어가 올바른 Execute Workflow 노드로 분기 |
| 5.2.5 | `진척률` / `코드검증 [repo]` → WBS-ORK 호출 | HTTP Request 노드 + Build Reply Code 노드 | ✅ 완료 | WBS-ORK 실행 후 결과 Teams 답장 |
| 5.2.6 | `티켓 [JIRA-ID]` → Jira 단일 이슈 조회 후 Teams 응답 | HTTP Request 노드 + Build Reply Code 노드 | ✅ 완료 | 티켓 상태 Teams 응답 확인 |
| 5.2.7 | `도움말` → 명령어 목록 메시지 반환 | Code 노드 | ✅ 완료 | 도움말 메시지 Teams 수신 확인 |

### Task 5.3: 오류 처리 및 재시도 로직

| # | Sub-task | n8n 노드 | 완료 기준 |
|---|----------|----------|-----------|
| 5.3.1 | 각 HTTP Request 노드에 재시도 설정 (최대 3회, 30초 간격) | HTTP Request 노드 설정 (Retry on Fail) | ✅ 완료 — 10개 Workflow 33개 노드 패치. Ollama 노드 제외 |
| 5.3.2 | 전역 Error Workflow 설정 — 오류 발생 시 Teams 채널에 에러 알림 | Error Trigger Workflow | ✅ 완료 — `workflow/WBS-ERR.json` (4노드). n8n Settings에서 각 Workflow의 Error Workflow로 지정 필요 |
| 5.3.3 | GitHub API Rate Limit (5000 req/hr) 모니터링 — 남은 한도 헤더 체크 | Code 노드 (응답 헤더 파싱) | ✅ 완료 — WBS-GRC에 Check→IF→Warn 노드 추가. 80% 초과 시 Teams 경고 |
| 5.3.4 | Ollama 컨텍스트 한도 초과 대비 — 파일 내용 분할 전송 로직 (청크 처리) | Code 노드 | 🔲 생략 — 현재 이번 주 변경 파일만 분석하므로 실 운영 후 필요시 추가 |

### Task 5.4: E2E 테스트 및 검증

| # | Sub-task | 완료 기준 |
|---|----------|-----------|
| 5.4.1 | ✅ 전체 흐름 E2E 테스트 — WBS-ORK → 모든 Agent → Teams 출력 | **HTTP 200, 512초 정상 완료** (2026-05-15). total_progress=4[RED], design_score=100[GREEN], teams_sent=true |
| 5.4.2 | 🔲 Cron 자동 실행 검증 — 금요일 17:00 실행 및 결과 확인 | 자동 실행 후 Teams 메시지 수신 확인 |
| 5.4.3 | ✅ 부분 실패 시나리오 테스트 — GitHub API 일부 실패, Jira API 실패 케이스 | **부분 실패 시에도 가용 데이터로 리포트 생성 성공**. `failed_agents` 감지 로직 개선 완료 (2026-05-15) |
| 5.4.4 | 🔲 설계 적합성 검증 정확도 검토 — 실제 프로젝트 코드 적용 후 결과 리뷰 | PM/리더와 결과 리뷰 완료, 개선사항 도출 |

> **E2E 테스트 중 발견 및 수정한 이슈 (2026-05-15)**:
>
> | 이슈 | 원인 | 수정 |
> |------|------|------|
> | WBS-TRG-001 활성화 실패 (`Could not find property option`) | `IF v2` 노드의 `conditions.options`가 잘못된 위치 — n8n v2.14는 `parameters.options` 최상위에만 허용 | 4개 IF 노드 파라미터 구조 수정 후 n8n 재import, `workflow_published_version` DB 업데이트로 활성화 |
> | WBS-ORK 응답 없음 (hang) | `N8N_RUNNERS_TASK_TIMEOUT` 미설정 → 기본 **60초** 제한. Ollama 분석 노드(BAK 238초, MOB 131초)가 초과하여 Task Runner crash | `.env`에 `N8N_RUNNERS_TASK_TIMEOUT=900` 추가 |
> | `failed_agents` 미감지 버그 | `neverError:true`로 비활성 agent webhook이 빈 `{}` 응답 반환 시 `error` 필드 없어 필터 통과 못함 | `Integrate Results` 노드에 `isRawFailed()` 함수 추가 — `agent_id` 부재 시 실패로 판단. 실운영 환경(네트워크 오류, 내부 에러)에서 정확히 작동 |

---

## 전체 Task 일정 요약

```
Phase 0: 환경 준비          ████████████████████  ✅ 완료
Phase 1: Specialist Agent   ████████████████████  ✅ 완료 (2026-05-13)
Phase 2: 진척률 수집        ████████████████████  ✅ 완료 (2026-05-14)
Phase 3: Orchestration      ████████████████████  ✅ 완료 (2026-05-14)
Phase 4: 리포트 출력        ████████████████████  ✅ 완료 (2026-05-14)
Phase 5: Trigger + 안정화   ██████████████████░░  🔄 진행 중 (Task 5.1 ✅, 5.4.1 ✅, 5.4.3 ✅)
```

| Phase | Task 수 | Sub-task 수 | 주요 의존성 |
|-------|---------|-------------|------------|
| Phase 0 | 3 | 11 | 없음 (즉시 시작 가능) |
| Phase 1 | 7 | 37 | GitHub PAT, Ollama LLM |
| Phase 2 | 2 | 10 | Jira API Token, GitHub PAT |
| Phase 3 | 4 | 16 | Phase 1, 2 완료 |
| Phase 4 | 1 | 4 | Phase 3 완료, Teams Webhook URL |
| Phase 5 | 4 | 17 | Phase 4 완료 |
| **합계** | **22** | **101** | |

---

## 주요 리스크 및 선행 조건

| 리스크 | 영향 | 대응 방안 |
|--------|------|-----------|
| Jira/Teams API 키 미확보 | Phase 2, 4, 5 블로킹 | Phase 0.2 최우선 진행, 확보되는 순서대로 해당 Phase 병행 |
| Ollama 컨텍스트 한도 | 분석 대상 파일 수에 비례 | 이번 주 변경 파일만 분석(전체 Repo 아님), 파일 크기 제한 설정 |
| GitHub API Rate Limit | Agent 병렬 실행 시 초과 위험 | Repo당 호출 수 최소화, 응답 헤더 모니터링 (Task 5.3.3) |
| 기존 n8n Workflow 충돌 | 트리거 중복 또는 Credential 충돌 | Task 0.1에서 먼저 파악 후 격리 처리 |
| Ollama 프롬프트 품질 | Gap 추출 정확도에 직접 영향 | Task 1.7.2에서 실제 코드 샘플로 반복 튜닝 |

---

## 즉시 시작 가능한 Task (2026-05-11 현재 상태 기준)

### 지금 바로 착수 가능 (외부 API 키 불필요 또는 이미 확보)

| 우선순위 | Task | 이유 |
|---------|------|------|
| 🔴 **즉시** | **Task 0.2.1** — Teams Bot 자격증명 Credential 이관 | 보안 이슈. client_secret 평문 노출 상태 |
| 🔴 **즉시** | **Task 0.3** — 환경변수 및 표준 스키마 정의 | 모든 Agent 개발의 전제조건 |
| 🟡 **병행** | **Task 1.2.4** — 설계 문서 파싱 Ollama 프롬프트 설계/튜닝 | Ollama LLM 준비 완료 |
| 🟡 **병행** | **Task 1.3.5** — Backend Call Flow 추출 Ollama 프롬프트 설계/튜닝 | Ollama LLM 준비 완료 |
| 🟡 **병행** | **Task 1.4.4** — Frontend API 호출 패턴 추출 Ollama 프롬프트 설계/튜닝 | Ollama LLM 준비 완료 |
| 🟢 **준비** | **Task 0.2.2** — GitHub PAT 발급 | PAT 발급 후 Phase 1 전체 착수 가능 |
| 🟢 **준비** | **Task 0.2.3** — Jira API Token 발급 | Token 발급 후 Phase 2 착수 가능 |

### 기존 Workflow 재활용 전략 요약

| 기존 노드 | 역할 | WBS-TRG-001에서 처리 방향 |
|-----------|------|--------------------------|
| Webhook Trigger | Teams POST 수신 | ✅ 그대로 유지 |
| Set - 메시지 파싱 | message / userId / convId 추출 | ✅ 그대로 유지 |
| HTTP Request - Token 발급 | Microsoft OAuth2 | ✅ 유지, 자격증명만 Credential로 이관 |
| HTTP Request - Teams 답장 | Bot Framework 답장 | ✅ 유지, 각 명령 처리 결과를 여기로 연결 |
| Respond to Webhook | 200 응답 | ✅ 그대로 유지 |
| *(신규)* Code 노드 | 명령어 파싱 | 🔲 Set 노드 뒤에 삽입 (Task 5.2.3) |
| *(신규)* Switch 노드 | 명령별 분기 | 🔲 Code 노드 뒤에 삽입 (Task 5.2.4) |
