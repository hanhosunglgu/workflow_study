# 환경 설정

---

## n8n Variables (Settings → Variables)

Workflow에서 `$vars.KEY_NAME` 으로 참조.

| Key | Value | 상태 | 용도 |
|-----|-------|------|------|
| `GITHUB_OWNER` | `hanhosunglgu` | ✅ 확정 | GitHub Username |
| `GITHUB_REPOS` | `["WBS_Check"]` | ✅ 확정 | 분석 대상 Repo 목록 |
| `JIRA_BASE_URL` | `https://lgucorp.atlassian.net` | ✅ 확정 | Jira Cloud URL |
| `JIRA_PROJECT_KEYS` | `["WBS"]` | ✅ 확정 | 모니터링 프로젝트 키 |
| `JIRA_BOARD_ID` | `8207` | ✅ 확정 | Sprint 조회용 Board ID |
| `DESIGN_DOC_REPO` | `hanhosunglgu/WBS_Check` | ✅ 확정 | 설계 문서 저장 Repo |
| `DESIGN_DOC_PATH` | `WBS_Check/docs/design` | ✅ 확정 | 설계 문서 디렉토리 경로 |

> ⚠️ **미완료 액션**: n8n UI(Settings → Variables)에 위 7개 값 직접 입력 필요.

---

## n8n Credentials

Workflow에서 HTTP Request 노드의 인증에 사용. n8n UI: **Settings → Credentials**.

| Credential | 유형 | 용도 | 상태 |
|-----------|------|------|------|
| Teams Bot OAuth2 | HTTP Header Auth | Microsoft Bot Framework Token 발급 | ✅ 완료 |
| GitHub PAT | HTTP Header Auth | GitHub REST API 인증 | ✅ 완료 |
| Jira API Token | Basic Auth | Jira Cloud API 인증 | ✅ 완료 |
| Ollama (로컬) | HTTP Request | `http://ollama:11434/api/generate` | ✅ 완료 |

---

## 환경변수 (.env / docker-compose)

n8n 서버 프로세스 환경변수. `$env.VAR_NAME` 으로 참조.

```env
# Teams Bot (Task 0.2.1 — 보안 이관 완료)
TEAMS_TENANT_ID=dbebe70a-4a50-48cc-b5a1-e047510c68a9
TEAMS_CLIENT_ID=5708513a-9c38-4991-b5f4-bf66c6996889
TEAMS_CLIENT_SECRET=<secret>

# GitHub
GITHUB_PAT=<PAT>
GITHUB_OWNER=hanhosunglgu
GITHUB_REPOS=["WBS_Check"]

# Jira
JIRA_BASE_URL=https://lgucorp.atlassian.net
JIRA_USER_EMAIL=<email>
JIRA_API_TOKEN=<token>
JIRA_PROJECT_KEYS=["WBS"]

# Ollama
OLLAMA_HOST=ollama:11434
OLLAMA_MODEL=qwen2.5-coder:7b

# 설계 문서
DESIGN_DOC_REPO=hanhosunglgu/WBS_Check
DESIGN_DOC_PATH=WBS_Check/docs/design

# n8n 타임아웃 설정
N8N_WEBHOOK_TIMEOUT=900           # Phase 1: 300 → 900초 증가
N8N_RUNNERS_TASK_TIMEOUT=900      # Phase 5: 미설정(기본 60초) → 900초, WBS-ORK hang 해결

# Teams (Phase 4)
TEAMS_WEBHOOK_URL=<Power Automate 웹훅 URL>
```

> ⚠️ `.env` 파일은 반드시 `.gitignore`에 포함. `client_secret`, `api_token` 등 민감값은 버전 관리 절대 금지.

---

## n8n Workflow 현황

| Workflow명 | 상태 | 비고 |
|-----------|------|------|
| `WBS-TRG-001` | ✅ Phase 5 완료 | `workflow/WBS-TRG-001.json` — Teams Bot 명령어 라우팅 (IF 노드 v2 버그 수정 포함) |
| `WBS-TRG-002` | ✅ Phase 5 완료 | `workflow/WBS-TRG-002.json` — 3노드 Cron 스케줄러 (매주 금 17:00) |
| `WBS-ERR` | ✅ Phase 5 완료 | `workflow/WBS-ERR.json` — 4노드 전역 Error Workflow (Teams 에러 알림) |
| `WBS-ORK` | ✅ Phase 3 완료 | `workflow/WBS-ORK.json` — 26노드, isRawFailed 로직 포함, E2E 512초 PASS |
| `WBS-RPT` | ✅ Phase 4 완료 | `workflow/WBS-RPT.json` — 11노드, Teams Adaptive Card 전송 확인 |
| `WBS-JRA` | ✅ Phase 2 완료 | `workflow/WBS-JRA.json` — 13노드, simple 보드 대응, 한글 상태명 매핑 |
| `WBS-GRC` | ✅ Phase 1 완료 | `workflow/WBS-GRC.json` — Repo 분류 + Commit/PR 집계 (16노드) |
| `WBS-DDA` | ✅ Phase 1 완료 | `workflow/WBS-DDA.json` — 설계 문서 파싱, endpoints=5, tables=2, sequences=2 |
| `WBS-BAK` | ✅ Phase 1 완료 | `workflow/WBS-BAK.json` — Backend 분석, 5개 엔드포인트 추출 |
| `WBS-FRT` | ✅ Phase 1 완료 | `workflow/WBS-FRT.json` — Frontend 분석, 5개 API 호출 추출 |
| `WBS-CFG` | ✅ Phase 1 완료 | `workflow/WBS-CFG.json` — Config/IaC 분석, design_gaps 3건 추출 |
| `WBS-MOB` | ✅ Phase 1 완료 | `workflow/WBS-MOB.json` — Mobile 분석, screen_flow=1, api_calls=1 |
| `WBS-INT` | ✅ Phase 1 완료 | `workflow/WBS-INT.json` — 57노드 통합 테스트용, 6/6 ALL_PASS |

---

## Ollama LLM 설정

| 항목 | 값 |
|------|----|
| 모델 | `qwen2.5-coder:7b` |
| 엔드포인트 | `http://ollama:11434/api/generate` |
| 실행 환경 | 로컬 Docker 컨테이너 |
| 호출 Agent | WBS-BAK, WBS-FRT, WBS-CFG, WBS-MOB, WBS-DDA, WBS-ORK |
| HTTP Request 설정 | `timeout: 600000`, `neverError: true` 필수 |
| JSON Body 패턴 | `JSON.stringify({ model: $json.model, prompt: $json.prompt, stream: $json.stream })` |
| 컨텍스트 한도 대응 | 대용량 파일 청크 분할 처리 (Task 5.3.4) |

**Ollama 웜업 커맨드** (첫 실행 전 필수 — CPU 모델 로드에 약 109초 소요):
```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-coder:7b","prompt":"hi","stream":false}'
```

---

## Teams 챗봇 외부 노출 (cloudflared)

Teams Bot Framework는 외부에서 접근 가능한 URL이 필요. 사내 네트워크에서 ngrok TLS 차단 시 cloudflared 사용.

```bash
# 터널 실행 (포트 5678 → 외부 HTTPS URL 발급)
cloudflared tunnel --url http://localhost:5678 --no-autoupdate &

# 발급된 URL 확인
grep -o 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' /tmp/cloudflared.log | head -1
```

**Azure Bot 등록**: Azure Portal → Azure Bot → Configuration → Messaging endpoint:
```
https://[발급된URL]/webhook/teams-trigger
```

**주의사항**:
- 무료 터널은 세션(터미널) 유지 중에만 동작
- 재시작 시 URL 변경 → Azure Bot Messaging Endpoint 재등록 필요
- 장기 운영 시 고정 IP/도메인 또는 cloudflared 유료 플랜 권장

---

## n8n 핵심 구현 패턴

Phase 1에서 확립한 표준 패턴.

### _meta 패턴

```javascript
// Build Ollama Request 노드
return [{ json: {
  model: 'qwen2.5-coder:7b',
  prompt: prompt,
  stream: false,
  _meta: { repo, commit_count, active_days }  // Ollama payload 외부에 저장
}}];

// Parse & Build Output 노드
const meta = $('XXX Build Ollama Request').first().json._meta;
```

### SplitInBatches 포트 순서

```
index 0 → Done 브랜치 (루프 완료 후 다음 단계)
index 1 → Loop 브랜치 (배치 아이템 처리)
```

### Webhook 입력 처리

```javascript
const input = $input.first().json;
const body = input.body || input;  // Webhook: .body, Execute Workflow: flat JSON
```
