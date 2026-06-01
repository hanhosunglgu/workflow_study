# E2E 최종 테스트 매뉴얼

**대상**: n8n을 처음 접하는 초보자  
**목표**: Teams 챗봇으로 명령 → WEB_Check 채널에 주간 진척률 리포트 게시 확인  
**작성일**: 2026-05-15

---

## 이 매뉴얼의 흐름

```
사전 준비
  ↓
[Step 1] n8n 서버 상태 확인
  ↓
[Step 2] TEAMS_WEBHOOK_URL 설정 (처음 1회)
  ↓
[Step 3] n8n Workflow 등록 및 활성화
  ↓
[Step 4] WBS-RPT 단독 테스트 (채널 연동 확인)
  ↓
[Step 5] WBS-ORK 전체 통합 테스트 (실제 데이터)
  ↓
[Step 6] Teams 챗봇으로 최종 E2E 테스트
  ↓
결과 확인 및 문제 해결
```

> 각 Step은 이전 Step이 성공해야 다음으로 진행하세요.

---

## 사전 준비 — 필요한 것 확인

| 항목 | 확인 방법 |
|------|----------|
| n8n이 실행 중 | 브라우저에서 `http://localhost:5678` 접속 가능 여부 |
| Teams 접근 가능 | Microsoft Teams 앱 또는 웹 로그인 상태 |
| 터미널(Terminal) | macOS: `터미널.app` 또는 `iTerm` |
| `.env` 파일 위치 | n8n Docker가 실행 중인 폴더 (`docker-compose.yml`이 있는 폴더) |

---

## Step 1 — n8n 서버 상태 확인

### 1-1. n8n이 실행 중인지 확인

터미널을 열고 아래 명령을 실행합니다.

```bash
curl -s http://localhost:5678/healthz
```

**정상 응답 예시:**
```
{"status":"ok"}
```

**응답이 없거나 오류가 나면** n8n을 시작합니다:

```bash
# docker-compose.yml이 있는 폴더로 이동한 뒤 실행
docker compose up -d n8n
```

### 1-2. n8n 브라우저 접속 확인

브라우저에서 `http://localhost:5678` 을 열었을 때 n8n 로그인 화면이 뜨면 정상입니다.

---

## Step 2 — TEAMS_WEBHOOK_URL 설정 (처음 1회만)

> 이미 `.env`에 `TEAMS_WEBHOOK_URL`이 설정되어 있으면 **Step 3으로 건너뜁니다**.

### 2-1. Teams에서 Webhook URL 생성

Teams의 `WEB_Check` 채널에서 아래 순서로 진행합니다.

1. `WEB_Check` 채널 이름 옆 `···` (더보기) 클릭
2. **워크플로** 선택
3. 검색창에 `웹후크` 입력 → **"채널에 웹후크 알림 보내기"** 템플릿 선택
4. **추가** 클릭 → 워크플로 이름 입력 (예: `WBS Agent 리포트`) → **다음**
5. 채널이 `WEB_Check`로 되어 있는지 확인 → **워크플로 추가**
6. 생성된 **URL을 복사** (매우 긴 URL, `https://prod-xx.westus.logic.azure.com/...`)

> URL은 한 번 닫으면 다시 보기 어렵습니다. 복사 후 메모장에 임시 저장하세요.

### 2-2. .env 파일에 URL 추가

터미널에서 `.env` 파일을 엽니다.

```bash
# .env 파일 위치 예시 (실제 경로는 다를 수 있음)
nano ~/.n8n/.env
# 또는
nano /path/to/your/project/.env
```

파일 안에 아래 줄을 추가합니다 (기존에 있으면 값만 변경):

```env
TEAMS_WEBHOOK_URL=https://prod-xx.westus.logic.azure.com/여기에_복사한_URL
```

저장: `Ctrl + O` → `Enter` → `Ctrl + X`

### 2-3. n8n 재시작 (환경변수 적용)

> `restart`는 환경변수를 적용하지 않습니다. 반드시 아래 명령을 사용하세요.

```bash
docker compose up -d n8n
```

### 2-4. 환경변수 적용 확인

n8n 브라우저(`http://localhost:5678`)에서:

1. 아무 Workflow 열기
2. 빈 **Code 노드** 추가
3. 노드 내 Expression 입력창에 `{{ $env.TEAMS_WEBHOOK_URL }}` 입력
4. 값이 URL로 출력되면 성공

확인 후 해당 테스트 Code 노드는 삭제합니다.

---

## Step 3 — n8n Workflow 등록 및 활성화

> 이미 n8n에 Workflow가 등록되어 있다면 **Activate 상태만 확인**하고 Step 4로 넘어갑니다.

### 3-1. 등록할 Workflow 파일 목록

| 파일 경로 | Workflow 이름 | 용도 |
|-----------|--------------|------|
| `workflow/WBS-RPT.json` | WBS-RPT | Teams 채널로 메시지 전송 |
| `workflow/WBS-ORK.json` | WBS-ORK | 전체 오케스트레이터 |
| `workflow/WBS-TRG-001.json` | WBS-TRG-001 | Teams 챗봇 명령 수신 |
| `workflow/WBS-JRA.json` | WBS-JRA | Jira 데이터 수집 |
| `workflow/WBS-GRC.json` | WBS-GRC | GitHub Repo 분류 |
| `workflow/WBS-DDA.json` | WBS-DDA | 설계 문서 파싱 |
| `workflow/WBS-BAK.json` | WBS-BAK | Backend 코드 분석 |
| `workflow/WBS-FRT.json` | WBS-FRT | Frontend 코드 분석 |
| `workflow/WBS-CFG.json` | WBS-CFG | Config/IaC 분석 |
| `workflow/WBS-MOB.json` | WBS-MOB | Mobile 코드 분석 |
| `workflow/WBS-ERR.json` | WBS-ERR | 에러 알림 |

### 3-2. Workflow 가져오기 (Import)

n8n 브라우저에서:

1. 왼쪽 메뉴 **Workflows** 클릭
2. 오른쪽 상단 **Add Workflow** → **Import from File** 클릭
3. 위 표의 파일을 하나씩 업로드

### 3-3. Activate 켜기

각 Workflow를 열고 우측 상단의 **Inactive** 토글을 클릭해 **Active** 로 변경합니다.

**활성화 필수 확인 목록:**

| Workflow | Active 여부 |
|----------|------------|
| WBS-RPT | ✅ Active |
| WBS-ORK | ✅ Active |
| WBS-TRG-001 | ✅ Active |
| 나머지 Specialist Agent | ✅ Active |

---

## Step 4 — WBS-RPT 단독 테스트

> 이 단계는 **Teams 채널 연동이 동작하는지**만 확인합니다.  
> 실제 Jira/GitHub 데이터 없이 가짜 데이터로 테스트합니다.

### 4-1. curl 명령 실행

터미널에서 아래 명령을 복사해 그대로 실행합니다.

```bash
curl -X POST http://localhost:5678/webhook/wbs-rpt \
  -H "Content-Type: application/json" \
  -d '{
    "week_start": "2026-05-11",
    "week_end": "2026-05-15",
    "total_progress": 73,
    "progress_grade": "YELLOW",
    "design_score": 87,
    "design_grade": "GREEN",
    "total_tickets": 12,
    "done_tickets": 6,
    "in_progress_tickets": 4,
    "todo_tickets": 2,
    "sp_total": 40,
    "sp_burned": 24,
    "sp_burned_rate": 60,
    "total_commits": 23,
    "max_active_days": 4,
    "gap_count": 1,
    "high_gap_count": 1,
    "medium_gap_count": 0,
    "low_gap_count": 0,
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

### 4-2. 기대 응답 (터미널)

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

### 4-3. 기대 결과 (Teams)

`WEB_Check` 채널에 아래와 같은 카드 메시지가 올라옵니다:

```
📊 WBS Agent 주간 개발 진척률 리포트
📅 2026-05-11 (월) ~ 2026-05-15 (금)

🎯 전체 진척률: 73% 🟡 주의  |  🔍 설계 적합성: 87% 🟢

📋 Jira 티켓 현황
  전체: 12개 / 완료: 6개 / 진행중: 4개 / 미착수: 2개
  Story Point: 24 / 40 (60%)

💻 GitHub 활동
  Commit: 23회 / 활성 개발일: 4/5일

📌 미완료 티켓
  • [PROJ-45] 로그인 API 구현 (In Progress, 홍길동)
  • [PROJ-48] 단위 테스트 작성 (To Do, 미배정)

🔍 설계 Gap: 총 1건 (🔴 1 🟡 0 🟢 0)
  • WBS-BAK: POST /api/user/register
```

> `teams_sent: true`인데 Teams에 메시지가 없다면 → **문제 해결 섹션** 참조

---

## Step 5 — WBS-ORK 전체 통합 테스트

> 이 단계는 실제 Jira, GitHub, Ollama 연동이 모두 동작합니다.  
> **Step 4가 성공한 후**에만 진행하세요.  
> 실행 시간: 약 5~10분 (Ollama LLM 분석 포함)

### 5-1. curl 명령 실행

```bash
curl -X POST http://localhost:5678/webhook/wbs-ork \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 5-2. 진행 상황 모니터링

n8n 브라우저에서 WBS-ORK Workflow를 열면 노드별 실행 상태를 실시간으로 볼 수 있습니다.

- 노드에 **초록 체크(✅)** = 정상 완료
- 노드에 **빨간 X(❌)** = 오류 발생 → 해당 노드 클릭해 오류 메시지 확인

### 5-3. 기대 결과

1. 터미널에 JSON 응답 수신 (total_progress, design_score 등 포함)
2. Teams `WEB_Check` 채널에 실제 Jira/GitHub 데이터 기반 리포트 게시

---

## Step 6 — Teams 챗봇으로 최종 E2E 테스트

> Teams 챗봇(`WBS-TRG-001`)을 통해 명령을 보내면 WBS-ORK가 실행되고  
> 최종적으로 `WEB_Check` 채널에 리포트가 게시됩니다.

### 6-1. Teams에서 WBS Agent 봇 찾기

Teams 검색창에서 등록된 Bot 이름(예: `WBSAgent` 또는 `WBS 진척률 봇`)을 검색합니다.

### 6-2. 챗봇에 메시지 보내기

Bot과 1:1 채팅창 또는 Bot이 추가된 채널에서 아래 명령을 입력합니다:

```
진척률
```

또는

```
@WBSAgent 진척률
```

### 6-3. 기대 흐름

```
Teams 챗봇 메시지 전송
  ↓ (WBS-TRG-001 수신)
명령어 파싱 → "진척률" 명령 감지
  ↓
WBS-ORK 호출 (전체 분석 시작)
  ↓ (약 5~10분)
WBS-RPT 호출 → WEB_Check 채널에 리포트 게시
  ↓
챗봇이 "리포트가 WEB_Check 채널에 전송되었습니다" 응답
```

### 6-4. 사용 가능한 챗봇 명령어 목록

| 명령어 | 동작 |
|--------|------|
| `진척률` | 현재 주간 진척률 리포트 전체 실행 |
| `코드검증 [repo명]` | 특정 Repo 설계 적합성 검증 |
| `티켓 [JIRA-ID]` | 특정 Jira 티켓 상태 조회 (예: `티켓 PROJ-45`) |
| `도움말` | 명령어 목록 출력 |

---

## 문제 해결 가이드

### 문제 1: curl 명령 후 아무 응답이 없거나 `Connection refused`

**원인**: WBS-RPT Workflow가 비활성화 상태 또는 n8n이 꺼져 있음

**해결**:
1. `http://localhost:5678` 접속 확인
2. WBS-RPT Workflow가 **Active** 상태인지 확인
3. n8n이 꺼져 있으면 `docker compose up -d n8n` 실행

---

### 문제 2: `teams_sent: true`인데 Teams 채널에 메시지가 없음

**원인 1**: Power Automate 워크플로가 비활성화 상태

**해결**: Teams → **워크플로 앱** → 생성한 워크플로 상태 확인 → 켜기

**원인 2**: TEAMS_WEBHOOK_URL이 잘못 설정됨

**해결**: `.env`에서 URL 확인 → `docker compose up -d n8n` 재시작

**원인 3**: TEAMS_WEBHOOK_URL이 `.env`에 있지만 n8n에 반영 안 됨

**해결**: `restart`가 아닌 `docker compose up -d n8n`으로 완전 재시작

---

### 문제 3: `404 Not Found` 응답

**원인**: Webhook URL 경로가 다름

**해결**: n8n에서 WBS-RPT Workflow를 열고 **Webhook 노드**를 클릭해 실제 URL 확인  
정상 URL: `http://localhost:5678/webhook/wbs-rpt`

---

### 문제 4: WBS-ORK 실행 중 특정 노드에서 빨간 X 표시

**확인 방법**: 빨간 X 노드를 클릭 → 오류 메시지 확인

| 오류 메시지 | 원인 | 해결 |
|------------|------|------|
| `401 Unauthorized` | Jira/GitHub 토큰 만료 | `.env`에서 토큰 재발급 후 재시작 |
| `Connection refused` (Ollama) | Ollama 컨테이너 꺼짐 | `docker compose up -d ollama` |
| `Workflow not found` | Specialist Agent 미등록 | 해당 JSON 파일 n8n에 Import 후 Activate |
| `ECONNRESET` | 외부 API 일시 장애 | 잠시 후 재시도 |

---

### 문제 5: Teams 챗봇에 메시지를 보내도 반응 없음

**원인**: WBS-TRG-001 Workflow 미등록 또는 비활성화

**해결**:
1. n8n에서 WBS-TRG-001 Workflow 확인 → Active 상태로 변경
2. Teams Bot이 채널/채팅에 올바르게 추가되어 있는지 확인
3. Bot의 Webhook URL이 `http://외부접근가능한주소/webhook/teams-trigger`로 등록되어 있는지 확인

> localhost는 Teams 서버에서 접근 불가합니다. ngrok 등으로 외부 노출이 필요합니다.

---

## 전체 Webhook URL 요약

| Workflow | Webhook URL |
|----------|-------------|
| WBS-RPT (리포트 전송) | `POST http://localhost:5678/webhook/wbs-rpt` |
| WBS-ORK (전체 실행) | `POST http://localhost:5678/webhook/wbs-ork` |
| WBS-TRG-001 (Teams 챗봇) | `POST http://[외부IP]:5678/webhook/teams-trigger` |

---

## 테스트 성공 체크리스트

```
[x] Step 1: http://localhost:5678 접속 성공
[x] Step 2: TEAMS_WEBHOOK_URL .env 설정 완료
[x] Step 3: 모든 Workflow Active 상태 확인
[x] Step 4: curl → WBS-RPT 단독 → WEB_Check 채널 메시지 확인
[x] Step 5: curl → WBS-ORK 전체 → WEB_Check 채널 실제 데이터 메시지 확인
[x] Step 6: Teams 챗봇 '진척률' 명령 → WEB_Check 채널 메시지 확인
```

모든 체크리스트가 완료되면 E2E 테스트 성공입니다.

---

## 최종 테스트 결과 (2026-05-15)

**테스트 일시**: 2026-05-15  
**판정**: ✅ PASS

### Step 4 — WBS-RPT 단독 테스트

| 항목 | 결과 |
|------|------|
| HTTP 응답 | 200 |
| teams_sent | true |
| teams_status | 200 |
| WEB_Check 채널 메시지 | ✅ 수신 확인 |

### Step 5 — WBS-ORK 전체 통합 테스트

| 항목 | 결과 |
|------|------|
| HTTP 응답 | 200 |
| total_progress | 4% 🔴 RED |
| design_score | 100% 🟢 GREEN |
| teams_sent | true |
| error | null |
| WEB_Check 채널 메시지 | ✅ 실제 Jira/GitHub 데이터 기반 리포트 수신 확인 |

### Step 6 — Teams 챗봇 E2E 테스트

| 항목 | 결과 |
|------|------|
| 챗봇 연동 방식 | Azure Bot Framework + cloudflared tunnel |
| Webhook URL | `https://expected-underlying-julia-constantly.trycloudflare.com/webhook/teams-trigger` |
| `도움말` 명령 | ✅ 챗봇 명령어 목록 답장 수신 확인 |
| `진척률` 명령 | ✅ WEB_Check 채널에 리포트 게시 확인 |

### 해결된 이슈 (E2E 과정)

| # | 이슈 | 원인 | 해결 |
|---|------|------|------|
| 1 | ngrok TLS 오류 | 사내 네트워크 SSL DPI 차단 | cloudflared tunnel로 대체 |
| 2 | IF 노드 `caseSensitive` 오류 | n8n v2.14 IF 노드 v2 스키마 변경 — options 위치 오류 | `conditions.options` 안으로 이동 |
| 3 | JSON Body 파싱 오류 | replyText 한글/줄바꿈 포함 시 jsonBody 템플릿이 JSON 파괴 | `specifyBody: keypair` 방식으로 변경 |
| 4 | Bot Framework 15초 타임아웃 | WBS-ORK(5~10분) 대기 중 Teams 연결 끊김 | Respond to Webhook을 명령어 파싱 직후로 이동 — 즉시 200 응답 후 WBS-ORK 비동기 호출 |

### 주의사항

- cloudflared tunnel은 세션(터미널) 유지 중에만 동작 — 터미널 종료 시 URL 만료
- 재시작 시 새 URL이 발급되므로 Azure Bot Messaging Endpoint 재등록 필요
- 장기 운영 시 고정 IP/도메인 또는 cloudflared 유료 플랜 권장
