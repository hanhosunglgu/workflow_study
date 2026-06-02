# Agent 명세

---

## Agent 목록

아래 순서는 실행 흐름 순서와 동일하다 (n8n_project-summary.md 섹션 순서 기준).

| Agent ID | 이름 | 유형 | 상태 | 설명 |
|----------|------|------|------|------|
| WBS-TRG-001 | Teams Trigger | Trigger | ✅ Phase 5 완료 | Teams Bot Webhook 수신, 명령어 파싱, 라우팅 |
| WBS-TRG-002 | Scheduler Trigger | Trigger | 🚫 중단 | 매주 금요일 17:00 Cron 실행 |
| WBS-ORK | Orchestration Agent | Orchestrator | ✅ Phase 3 완료 | Repo 분류, 병렬 Agent 조율, 결과 통합, Call Flow 재구성 |
| WBS-GRC | GitHub Repo Classifier | Specialist | ✅ 완료 | Repo 목록 스캔, Backend/Frontend/Config/Mobile 유형 분류, Commit 집계 |
| WBS-JRA | Jira Agent | Specialist | ✅ Phase 2 완료 | Sprint 티켓 수집, 상태 집계, Story Point 소진률 계산 |
| WBS-DDA | Design Doc Agent | Specialist | ✅ 완료 | 설계 문서(.md) 파싱, API 명세/ERD/시퀀스 구조 추출 |
| WBS-BAK | Backend Agent | Specialist | ✅ 완료 | API 라우터/컨트롤러 분석, Call Flow 시퀀스 생성, Gap 추출 |
| WBS-FRT | Frontend Agent | Specialist | ✅ 완료 | 컴포넌트/API 호출 패턴 분석, 화면-API 연결 시퀀스 생성, Gap 추출 |
| WBS-CFG | Config/IaC Agent | Specialist | ✅ 완료 | Terraform/k8s 실제 구성 vs 설계 문서 비교, Gap 추출 |
| WBS-MOB | Mobile Agent | Specialist | ✅ 완료 | iOS/Android/Flutter 화면 흐름 및 API 시퀀스 분석, Gap 추출 |
| WBS-INT | Integration Test | Test | ✅ 완료 | 6개 Agent 인라인 통합 (57노드), Phase 1 통합 테스트용 |
| WBS-RPT | Report Agent | Output | ✅ Phase 4 완료 | Teams 채널 Adaptive Card 메시지 전송 |
| WBS-ERR | Error Workflow | Support | 🚫 중단 | 전역 오류 발생 시 Teams 채널 에러 알림 (4노드) |

---

## 표준 Output 스키마

모든 Specialist Agent는 아래 스키마로 결과를 반환한다. Orchestration Agent가 이 스키마를 기준으로 통합한다.

```json
{
  "agent_id": "WBS-BAK",
  "repo": "WBS_Check",
  "repo_type": "backend",
  "call_flow": [
    {
      "from": "Frontend",
      "to": "POST /api/auth/login",
      "handler": "AuthController.login()",
      "calls": ["AuthService.validate()", "UserRepository.findByEmail()"]
    }
  ],
  "design_gaps": [
    {
      "item": "POST /api/user/register",
      "discrepancy_type": "spec_changed",
      "severity": "high",
      "design": "필드: username, password, email",
      "actual": "필드: user_name, password, email_address"
    }
  ],
  "commit_count": 8,
  "active_days": 3
}
```

---

## Agent별 상세 명세

### WBS-TRG-001 — Teams Trigger ✅ Phase 5 완료

- **기반**: 기존 `Teams Bot - n8n Webhook` Workflow 확장
- **Webhook**: `POST /webhook/teams-trigger`
- **파싱 필드**: `text`, `from.id`, `from.name`, `conversation.id`, `serviceUrl`, `activityId`
- **명령어 분기**: Code 노드(HTML 태그 제거 + 명령어 파싱) → Switch 노드 4분기
  - `진척률` / `코드검증 [repo]` → WBS-ORK 호출 → Teams 결과 답장
  - `티켓 [JIRA-ID]` → Jira 단일 이슈 조회 → Teams 결과 답장
  - `도움말` → 명령어 목록 Teams 답장
  - Unknown → 도움말 메시지 안내
- **Merge 노드**: 5개 분기 결과 수렴 → Token 발급 → Teams 답장 → Respond to Webhook
- **버그 수정**: IF 노드 v2 `parameters.conditions.options` → `parameters.options` 이동 (n8n v2.14 스키마 변경)

---

### WBS-GRC — GitHub Repo Classifier ✅

- **Webhook**: `POST /webhook/wbs-grc`
- **입력**: `{ owner, repos[] }`
- **구성**: 20노드
- **동작**:
  1. `GET /users/{owner}/repos` 전체 Repo 목록 조회. GitHub PAT 인증. 3회 재시도
  2. `Check Rate Limit` — `x-ratelimit-remaining/limit` 헤더 파싱. 사용률 80% 이상이면 Teams 경보 발송 후 계속 실행
  3. `SplitInBatches` 루프로 Repo 1개씩 처리
  4. `GET /repos/{full_name}/contents/` 루트 파일 목록으로 Repo 유형 분류
  5. 이번 주 Commit/PR 집계 (평일만 `active_days` 산출)
- **분류 기준 (우선순위 순)**:
  - `mobile`: `Podfile`, `pubspec.yaml`, `Package.swift`, `build.gradle`
  - `config`: `*.tf`, `helmfile.yaml`, `k8s/`, `infra/`
  - `backend`: `pom.xml`, `requirements.txt`, `go.mod`, `Cargo.toml`
  - `frontend`: `next.config.*`, `vite.config.*`, `angular.json`, `package.json`(서버 엔트리 없는 경우)
- **Rate Limit 80% 경고**: 남은 20%(약 1,000건)로 현재 실행 완료 여유 확보 + 운영자 사전 대응 시간 확보
- **출력**: `{ agent_id:'WBS-GRC', backend[], frontend[], config[], mobile[], commit_stats{} }`
- **실제 테스트 결과**: WBS_Check → `frontend` (Vite 패턴 감지)

---

### WBS-DDA — Design Doc Agent ✅ (2026-05-20 재구현)

- **Webhook**: `POST /webhook/wbs-dda`
- **입력**: `{ owner, repo, path }` ← repos[] 배열 아님
- **노드 수**: 9노드 (Loop 없음)
- **동작**:
  1. GitHub Contents API로 `path` 디렉토리 내 `.md` 파일 목록 조회 (GitHub PAT 인증 필수, `fullResponse:true`, `neverError:true`)
  2. Filter MD Files — 모든 `.md` 파일의 `download_url`을 단일 아이템으로 수집
  3. GET File Content — 첫 번째 파일의 raw 텍스트 직접 fetch
  4. OpenAI API 호출 → 구조화된 설계 정보 추출
- **⚠️ 변경 이력**: SplitInBatches 완전 제거 (typeVersion 3 + 단일 아이템 시 loop body 스킵 버그), Ollama → OpenAI 전환
- **GitHub PAT Credential**: `eLRk8UEJ3iN7jUrm` (name: GitHub PAT)
- **설계 문서 경로**: `hanhosunglgu/WBS_Check` repo의 `docs/design/` (api-design.md, db-schema.md, sequence-design.md)
- **출력**: `{ agent_id:'WBS-DDA', repo_type:'design_doc', endpoints[], tables[], sequences[] }`
- **실제 테스트 결과**: api-design.md에서 endpoints=9 추출 (webhook paths 포함)

---

### WBS-BAK — Backend Agent ✅

- **Webhook**: `POST /webhook/wbs-bak`
- **입력**: `{ owner, repos:['WBS_Check'] }`
- **동작**:
  1. 이번 주 변경 커밋 목록 조회 (`since/until` 날짜 필터)
  2. 최신 커밋(`shas[0]`)의 변경 파일 목록 수집
  3. `routes/`, `controllers/`, `api/`, `handler.` 패턴 우선 필터링 → 없으면 `.js/.ts/.py/.java/.go/.rb` 최대 5개 폴백
  4. OpenAI API → 실제 API 엔드포인트 및 Call Flow 추출 (`gpt-4.1-mini`, stream:false)
  5. `_meta` 패턴으로 repo/커밋 컨텍스트 보존 후 Parse 노드에서 복원
- **출력**: `{ agent_id, repo, repo_type:'backend', extracted_endpoints[], call_flow[], commit_count, active_days }`
- **실제 테스트 결과**: routes/index.js에서 5개 엔드포인트 추출, commits=8
- **노드명 변경**: `Build Ollama Request` → `Build OpenAI Request`, `Ollama Extract Call Flow` → `OpenAI Extract Call Flow`

---

### WBS-FRT — Frontend Agent ✅

- **Webhook**: `POST /webhook/wbs-frt`
- **입력**: `{ owner, repos:['WBS_Check'] }`
- **동작**:
  1. 이번 주 변경 파일 목록 조회
  2. `api/`, `services/`, `hooks/`, `store/`, `pages/`, `views/` 경로 패턴 필터. 확장자: `.js/.ts/.jsx/.tsx/.vue/.svelte`
  3. OpenAI API → API 호출 패턴 및 컴포넌트 흐름 추출 (`gpt-4.1-mini`)
- **출력**: `{ agent_id, repo, repo_type:'frontend', api_calls[], call_flow[] }`
- **실제 테스트 결과**: src/api/authService.js에서 5개 API 호출 추출
- **노드명 변경**: `Build Ollama Request` → `Build OpenAI Request`, `Ollama Extract API Calls` → `OpenAI Extract API Calls`

---

### WBS-CFG — Config/IaC Agent ✅

- **Webhook**: `POST /webhook/wbs-cfg`
- **입력**: `{ owner, repos:['WBS_Check'] }`
- **동작**:
  1. `config/`, `helm/`, `k8s/`, `terraform/` 경로 필터. 확장자: `.yaml/.yml/.json/.toml/.tf/.conf`
  2. OpenAI API → 인프라 config 항목 추출 및 변경사항 분석 (`gpt-4.1-mini`)
- **출력**: `{ agent_id, repo, repo_type:'config', config_items[], call_flow[] }`
- **실제 테스트 결과**: docker-compose.yml에서 2 services + 1 volume, design_gaps 3건 (hardcoded password High)
- **노드명 변경**: `Build Ollama Request` → `Build OpenAI Request`, `Ollama Extract Config` → `OpenAI Extract Config`

---

### WBS-MOB — Mobile Agent ✅

- **Webhook**: `POST /webhook/wbs-mob`
- **입력**: `{ owner, repos:['WBS_Check'] }`
- **동작**:
  1. `screens/`, `pages/`, `navigation/`, `api/`, `services/` 경로 필터. 확장자: `.swift/.kt/.dart/.tsx/.jsx`
  2. OpenAI API → 화면 전환 흐름 및 API 호출 시퀀스 추출 (`gpt-4.1-mini`)
- **출력**: `{ agent_id, repo, repo_type:'mobile', screens[], call_flow[] }`
- **실제 테스트 결과**: screen_flow=1, api_calls=1, design_gaps=2 (lib/screens/login_screen.dart 기준)
- **노드명 변경**: `Build Ollama Request` → `Build OpenAI Request`, `Ollama Extract Screen Flow` → `OpenAI Extract Screen Flow`

---

### WBS-INT — Integration Test Workflow ✅

- **Webhook**: `POST /webhook/wbs-int`
- **입력**: `{ owner, repos:['WBS_Check'], dda_repo:'hanhosunglgu/WBS_Check', dda_path:'docs/design' }`
- **구성**: 6개 Agent 노드 인라인 포함 (57노드 + 8 Sticky Notes = 65 총 노드)
- **노드 네이밍**: 모든 노드명에 agent prefix 적용 (예: `GRC Filter & Split Repos`, `BAK Build Ollama Request`)
- **Build Report 노드**: 6개 Agent 결과를 수집하여 통합 리포트 반환
- **실행시간**: 약 7~8분 (Ollama 6회 순차 호출)
- **테스트 결과**: 6/6 ALL_PASS

---

### WBS-JRA — Jira Agent ✅ Phase 2 완료

- **Webhook**: `POST /webhook/wbs-jra`
- **입력**: `JIRA_BASE_URL`, `JIRA_PROJECT_KEYS`, `JIRA_BOARD_ID`
- **구성**: 13노드
- **동작**:
  1. 활성 Sprint 조회 — `simple` 보드 대응: `?state=active` 제거 후 JS 코드로 필터링
  2. Sprint 이슈 전체 조회 (SplitInBatches + hasMore 루프 페이지네이션)
  3. 상태별 집계 (한글 상태명 포함: `완료`/`진행 중`/`해야 할 일`)
  4. Story Point 소진률 계산 (`customfield_10016`, 미설정 시 sp_total=0)
  5. Commit 메시지에서 `/\b([A-Z][A-Z0-9]+-\d+)\b/g` 패턴 추출 → 티켓 매핑
- **출력**: `{ sprint_id, total_tickets, done, in_progress, todo, sp_burned, sp_total, jira_commit_map, linked_ticket_count, no_commit_issues }`

---

### WBS-TRG-002 — Scheduler Trigger ✅ Phase 5 완료

- **파일**: `workflow/WBS-TRG-002.json`
- **구성**: 3노드 — Schedule Trigger → Call WBS-ORK → Log Result
- **스케줄**: `0 17 * * 5` (매주 금요일 17:00)
- **timeout**: 900,000ms, `neverError:true`
- **Error Workflow**: WBS-ERR 지정
- **등록**: n8n UI에서 수동 import 필요 (CLI import 시 id 충돌)

---

### WBS-ERR — Error Workflow ✅ Phase 5 완료

- **파일**: `workflow/WBS-ERR.json`
- **구성**: 4노드 — Error Trigger → Build Error Message → Token 발급 → Teams 알림
- **역할**: 전체 Workflow에서 오류 발생 시 Teams 채널에 에러 내용 전송
- **연결**: 각 Workflow의 Error Workflow 설정에서 `WBS-ERR` 지정 필요

---

### WBS-ORK — Orchestration Agent ✅ Phase 3 완료

- **Webhook**: `POST /webhook/wbs-ork`
- **구성**: 26노드 (최종 isRawFailed 로직 포함)
- **트리거**: Webhook(`wbs-ork`) / Schedule(`0 17 * * 5`) / Manual Trigger 3종 지원
- **동작**:
  1. 주간 날짜 범위 계산 (이번 주 월요일 00:00 UTC ~ 현재)
  2. WBS-GRC 호출 → Repo 유형 분류
  3. 6개 Agent 병렬 HTTP 호출 (JRA/DDA/BAK/FRT/CFG/MOB)
  4. Merge 노드 (numberInputs:6) → 전체 결과 수렴
  5. isRawFailed() 로직으로 failed_agents 감지
  6. Call Flow 재구성 (Mobile/Frontend → Backend → Config)
  7. design_gaps[] 통합 + 중복 제거 + Ollama 의도 분석
  8. 진척률 계산 (Jira 티켓 40% + SP 40% + Commit 20%)
  9. WBS-RPT 호출 → Teams 전송
- **부분 실패 처리**: `resultMap[agentId] || defaultAgent(...)` 패턴
- **isRawFailed()**: `agent_id` 부재 시 실패 판단 (neverError:true 빈 응답 감지)
- **E2E 테스트 결과**: HTTP 200, 512초, total_progress=4[RED], design_score=100[GREEN]

---

### WBS-RPT — Report Agent ✅ Phase 4 완료

- **Webhook**: `POST /webhook/wbs-rpt`
- **구성**: 11노드
- **출력 포맷**: Microsoft Teams Adaptive Card (version 1.0)
- **카드 구성**: TextBlock + FactSet (Table/ColumnSet 미지원으로 단순화)
- **전송 포맷**:
  ```json
  { "attachments": [{ "contentType": "application/vnd.microsoft.card.adaptive", "content": { ...card } }] }
  ```
- **미완료 티켓**: 최대 5건 표시, 초과 시 "외 N건" 처리
- **Confluence**: `confluence_skipped: true` (조직 정책 비활성화)
- **Teams 메시지 형식**:

```
📊 [WBS Agent] 주간 개발 진척률 리포트
📅 기간: YYYY-MM-DD (월) ~ YYYY-MM-DD (금)

━━━━━━━━━━━━━━━━━━━━━
🎯 전체 진척률: XX% [등급]
━━━━━━━━━━━━━━━━━━━━━

📋 Jira 티켓 현황
  • 전체: N개 | ✅ 완료: N개 | 🔄 진행중: N개 | ⏳ 미착수: N개
  • Story Point: N / N 소진 (N%)

💻 GitHub 활동
  • Commit: N회 | PR: N개 merge | 활성 개발일: N/5일

📌 미완료 티켓 (상위 5건)
  • [WBS-XX] 티켓 제목 - 상태 (담당자)

🔍 설계 적합성: N% (불일치 N건)
  🔴 High: N건 | 🟡 Medium: N건 | 🟢 Low: N건
```
