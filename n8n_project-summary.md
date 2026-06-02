# WBS Check Agent — 프로젝트 요약

> 출처 표기 형식: `📄 파일명:라인번호` — 해당 파일의 원본 라인으로 이동하여 상세 내용 확인 가능

---

## 1. 프로젝트 개요

**프로젝트명**: 3rd WBS Agent  
**엔진**: n8n Self-hosted  
**기간**: 2026-05-08 ~ 2026-05-20 (전 Phase 완료)

팀 리더/PM이 개발팀의 주간 진척률을 **수작업 없이 자동으로 모니터링하고 보고받는** n8n 기반 Multi-Agent 자동화 시스템.  
Jira, GitHub, 설계 문서(.md)를 통합 분석하여 **매주 금요일 17:00에 Teams 채널에 자동 리포트**를 발송하거나, **Teams Bot 명령으로 즉시 조회**한다.

> 📄 [`wiki/project-overview.md:11`](wiki/project-overview.md)

### 핵심 차별점

일반 진척률 집계 도구와 달리 **설계 문서 대비 실제 코드의 적합성을 검증**하는 것이 핵심.

| 기능 | 설명 |
|------|------|
| 설계 적합성 검증 | `.md` 설계 문서(API 명세/ERD/시퀀스)와 실제 소스코드를 비교하여 Gap 자동 추출 |
| LLM 의도 분석 | Gap이 의도적 개선인지, 실수/누락인지 LLM이 판단 |
| Call Flow 재구성 | Frontend → Backend → DB 전체 호출 흐름을 설계 vs 구현 기준으로 비교 |
| 통합 진척률 | Jira 티켓 상태 + Story Point + GitHub Commit 빈도를 가중 합산 |

> 📄 [`wiki/project-overview.md:19`](wiki/project-overview.md)

### Teams Bot 명령어

| 명령어 | 동작 | 상태 |
|--------|------|------|
| `@WBSAgent 진척률` | 현재 시점 진척률 리포트 즉시 생성 | ✅ 구현 완료 |
| `@WBSAgent 도움말` | 명령어 목록 출력 | ✅ 구현 완료 |
| `@WBSAgent 진척률 [repo명]` | 특정 repo 진척률 조회 | ✅ 구현 완료 |
| `@WBSAgent 티켓 [JIRA-ID]` | 특정 Jira 티켓 상태 조회 | ✅ 구현 완료 |
| `@WBSAgent 코드검증 [repo명]` | 특정 repo 설계 적합성 검증 실행 | ✅ 구현 완료 |

> 📄 [`wiki/project-overview.md:40`](wiki/project-overview.md)

### 기술 스택

| 컴포넌트 | 기술 |
|----------|------|
| Workflow Engine | n8n (Self-hosted) |
| Trigger | Microsoft Teams Webhook, n8n Cron |
| 이슈 관리 | Jira Cloud API v3 |
| 소스 관리 | GitHub REST API v3 |
| LLM | OpenAI gpt-4.1-mini (초기 Ollama → 전환) |
| 설계 문서 | `.md` 파일 (GitHub repo 지정 경로) |
| Multi-Agent 프레임워크 | n8n Sub-workflow + Execute Workflow 노드 |

> 📄 [`wiki/project-overview.md:52`](wiki/project-overview.md)

---

## 2. 시스템 아키텍처

```
┌──────────────────────┐   ┌──────────────────────┐
│   WBS-TRG-001        │   │   WBS-TRG-002        │
│   Teams Bot Webhook  │   │   Cron 스케줄러       │
│   (수동 명령 수신)    │   │   (매주 금 17:00)     │
└──────────┬───────────┘   └──────────┬───────────┘
           │                          │
           └──────────┬───────────────┘
                      │
                      ↓
           ┌──────────────────────┐
           │   WBS-ORK            │
           │   Orchestration      │
           │   Agent (26노드)     │
           │                      │
           │  1. 날짜 범위 계산   │
           │  2. WBS-GRC 호출     │
           │  3. Agent 병렬 호출  │
           │  4. 결과 수렴        │
           │  5. 진척률 계산      │
           │  6. WBS-RPT 호출     │
           └──────────┬───────────┘
                      │
          ┌───────────┼────────────┐
          │           │            │
          ↓           ↓            ↓
┌─────────────┐  ┌──────────┐  ┌──────────────────┐
│  WBS-GRC    │  │ WBS-JRA  │  │  WBS-DDA         │
│  GitHub     │  │ Jira     │  │  Design Doc      │
│  Repo 분류  │  │ Sprint   │  │  Agent (9노드)   │
│  + Commit   │  │ Agent    │  │                  │
│  집계       │  │ (13노드) │  │  설계문서 파싱   │
│  (16노드)   │  │          │  │  Gap 탐지        │
└─────────────┘  └──────────┘  └──────────────────┘
          │
          ↓ (분류 결과 기반 병렬 호출)
          │
          ├──────────────────────────────────────┐
          │                                      │
          ↓                                      ↓
┌─────────────────┐                   ┌─────────────────┐
│  WBS-BAK        │                   │  WBS-FRT        │
│  Backend Agent  │                   │  Frontend Agent │
│  (12노드)       │                   │  (12노드)       │
│                 │                   │                 │
│  API 라우터     │                   │  컴포넌트/API   │
│  Call Flow 추출 │                   │  호출 패턴 분석 │
│  Gap 추출       │                   │  Gap 추출       │
└─────────────────┘                   └─────────────────┘
          │
          ↓
┌─────────────────┐                   ┌─────────────────┐
│  WBS-CFG        │                   │  WBS-MOB        │
│  Config/IaC     │                   │  Mobile Agent   │
│  Agent (12노드) │                   │  (12노드)       │
│                 │                   │                 │
│  Terraform/k8s  │                   │  iOS/Android    │
│  실제 구성 분석 │                   │  Flutter 화면   │
│  Gap 추출       │                   │  흐름 분석      │
└─────────────────┘                   └─────────────────┘
          │
          │  (전체 결과 수렴 → WBS-ORK Merge 노드)
          ↓
┌──────────────────────┐
│   WBS-ORK (계속)     │
│                      │
│  isRawFailed() 감지  │
│  Call Flow 재구성    │
│  design_gaps 통합    │
│  진척률 계산         │
└──────────┬───────────┘
           │
           ↓
┌──────────────────────┐
│   WBS-RPT            │
│   Report Agent       │
│   (11노드)           │
│                      │
│   Teams Adaptive     │
│   Card 생성 및 발송  │
└──────────┬───────────┘
           │
           ↓
┌──────────────────────┐
│   Microsoft Teams    │
│   채널               │
│                      │
│   주간 진척률        │
│   리포트 수신        │
└──────────────────────┘

※ 오류 발생 시
┌──────────────────────┐
│   WBS-ERR            │
│   Error Workflow     │
│   (4노드)            │
│                      │
│   Teams 채널에       │
│   에러 알림 발송     │
└──────────────────────┘
```

WBS-ORK 내부 실행 순서:
1. 주간 날짜 범위 계산 (이번 주 월요일 00:00 UTC ~ 현재)
2. WBS-GRC 호출 → Repo 유형 분류
3. 6개 Agent 병렬 HTTP 호출 (JRA/DDA/BAK/FRT/CFG/MOB)
4. Merge 노드(numberInputs:6)로 전체 결과 수렴
5. `isRawFailed()` 로직으로 failed_agents 감지
6. Call Flow 재구성 → design_gaps 통합 → 진척률 계산
7. WBS-RPT 호출 → Teams 전송

> 📄 [`wiki/architecture.md:6`](wiki/architecture.md) — 전체 아키텍처 다이어그램  
> 📄 [`wiki/architecture.md:50`](wiki/architecture.md) — n8n Workflow 실행 구조  
> 📄 [`wiki/agents.md:209`](wiki/agents.md) — WBS-ORK 26노드 상세 동작

---

## 3. Agent 구성 (13개)

| Agent ID | 역할 | 노드 수 | Webhook 경로 | 상태 |
|----------|------|---------|-------------|------|
| **WBS-TRG-001** | Teams Bot 명령 수신·파싱·라우팅 | - | `/webhook/teams-trigger` | ✅ |
| **WBS-TRG-002** | Cron 스케줄러 (매주 금 17:00) | 3 | 내부 트리거 | 🚫 중단 |
| **WBS-ORK** | 전체 오케스트레이터 | 26 | `/webhook/wbs-ork` | ✅ |
| **WBS-GRC** | GitHub Repo 분류 + Commit/PR 집계 | 16 | `/webhook/wbs-grc` | ✅ |
| **WBS-JRA** | Jira Sprint 티켓·SP 수집 | 13 | `/webhook/wbs-jra` | ✅ |
| **WBS-DDA** | 설계 문서 파싱·Gap 탐지 | 9 | `/webhook/wbs-dda` | ✅ |
| **WBS-BAK** | Backend 코드 분석·Call Flow 추출 | 12 | `/webhook/wbs-bak` | ✅ |
| **WBS-FRT** | Frontend API 호출 패턴 분석 | 12 | `/webhook/wbs-frt` | ✅ |
| **WBS-CFG** | IaC/Config 분석·Gap 추출 | 12 | `/webhook/wbs-cfg` | ✅ |
| **WBS-MOB** | Mobile 화면 흐름·API 시퀀스 분석 | 12 | `/webhook/wbs-mob` | ✅ |
| **WBS-INT** | 6개 Agent 인라인 통합 테스트 | 57 | `/webhook/wbs-int` | ✅ |
| **WBS-RPT** | Teams Adaptive Card 리포트 발송 | 11 | `/webhook/wbs-rpt` | ✅ |
| **WBS-ERR** | 전역 오류 발생 시 Teams 에러 알림 | 4 | - | 🚫 중단 |

### Agent별 노드 상세 동작

---

#### WBS-TRG-001 — Teams Bot 트리거 (17노드)

> 📄 [`workflow/WBS-TRG-001.json`](../workflow/WBS-TRG-001.json)

**Webhook Trigger — Teams에서 수신하는 raw JSON 전체 구조**

Teams Bot Framework가 `POST /webhook/teams-trigger`로 전송하는 Activity JSON:

```json
{
  "type": "message",
  "id": "1717318530123",
  "timestamp": "2026-05-19T09:00:00.123Z",
  "localTimestamp": "2026-05-19T18:00:00.123+09:00",
  "localTimezone": "Asia/Seoul",
  "serviceUrl": "https://smba.trafficmanager.net/kr/",
  "channelId": "msteams",
  "from": {
    "id": "29:1BLjP9j3_TM4mubmQZsYEo7jDyLeLf_YVA9sVPVO7KMAFMjJWB_EUGveb9EVDh9LgoNp9qjnzEBy4kgw83Jf1Kg",
    "name": "홍길동",
    "aadObjectId": "976e4d1e-2108-43ee-a092-46a9507c5606"
  },
  "conversation": {
    "isGroup": true,
    "conversationType": "channel",
    "tenantId": "bec8e231-67ad-484e-87f4-3e5438390a77",
    "id": "19:e2e6f321f5b847f3a8e5f2e8c1e9d4b7@thread.tacv2",
    "name": "general"
  },
  "recipient": {
    "id": "28:0d469698-ab9d-479a-b0d8-758b6e6b1235",
    "name": "WBSAgent"
  },
  "text": "<at>WBSAgent</at> 진척률",
  "textFormat": "html",
  "locale": "ko-KR",
  "attachments": [],
  "entities": [
    {
      "type": "mention",
      "mentioned": {
        "id": "28:0d469698-ab9d-479a-b0d8-758b6e6b1235",
        "name": "WBSAgent"
      },
      "text": "<at>WBSAgent</at>"
    },
    {
      "type": "clientInfo",
      "locale": "ko-KR",
      "country": "KR",
      "platform": "Windows",
      "timezone": "Asia/Seoul"
    }
  ],
  "channelData": {
    "channel": {
      "id": "19:e2e6f321f5b847f3a8e5f2e8c1e9d4b7@thread.tacv2"
    },
    "team": {
      "id": "19:abc123def456@thread.skype"
    },
    "tenant": {
      "id": "bec8e231-67ad-484e-87f4-3e5438390a77"
    }
  },
  "importance": "normal",
  "deliveryMode": "default"
}
```

**주요 필드 설명**

| 필드 | 설명 | WBS-TRG-001에서 사용 |
|------|------|---------------------|
| `text` | 사용자 입력 텍스트 (HTML 태그 포함) | `$json.body.text` → `message` |
| `from.id` | 발신자 Bot Framework ID | `$json.body.from.id` → `userId` |
| `from.name` | 발신자 이름 | `$json.body.from.name` → `userName` |
| `conversation.id` | 대화/스레드 ID (Teams 답장 시 필요) | `$json.body.conversation.id` → `convId` |
| `serviceUrl` | 봇이 답장을 보낼 Teams 엔드포인트 | `$json.body.serviceUrl` → `serviceUrl` |
| `id` | Activity 고유 ID | `$json.body.id` → `activityId` |
| `entities[].type=mention` | @멘션 정보 (봇 이름 포함) | 미사용 (Code 노드에서 HTML 태그 제거로 처리) |
| `channelData.tenant.id` | Microsoft Entra 테넌트 ID | 미사용 |

> **`text` 필드 주의**: `<at>WBSAgent</at> 진척률` 형태로 HTML 태그가 포함됨. Code - 명령어 파싱 노드에서 `replace(/<[^>]+>/g, '')` 로 태그 제거 후 `진척률`만 추출

| # | 노드명 | Input | 처리 기능 | Output |
|---|--------|-------|-----------|--------|
| 1 | **Webhook Trigger** | Teams Bot Framework HTTP POST | `/webhook/teams-trigger` 수신. `responseMode: responseNode`로 응답 타이밍을 하위 노드가 제어 | raw HTTP body |
| 2 | **Set - 메시지 파싱** | Webhook raw body | Teams Activity에서 6개 필드 평탄화 추출: `message`, `userId`, `userName`, `convId`, `serviceUrl`, `activityId` | 6개 필드 JSON |
| 3 | **Code - 명령어 파싱** | `message` 필드 | HTML 태그 제거 → 첫 단어를 `keyword`로 추출 → `진척률/코드검증/티켓/도움말/unknown` 매핑 | `command`, `param`, `rawMessage` 추가 |
| 4 | **Respond to Webhook** | 명령어 파싱 결과 | Teams에 즉시 `{"status":"ok"}` HTTP 200 반환 (15초 타임아웃 방지용) | 동일 데이터 하위 전달 |
| 5 | **IF 진척률** | `command` | `command === '진척률'` 분기 | true→Fire WBS-ORK(진척률) / false→IF 코드검증 |
| 6 | **IF 코드검증** | `command` | `command === '코드검증'` 분기 | true→Fire WBS-ORK(코드검증) / false→IF 티켓 |
| 7 | **IF 티켓** | `command` | `command === '티켓'` 분기 | true→HTTP Jira 조회 / false→IF 도움말 |
| 8 | **IF 도움말** | `command` | `command === '도움말'` 분기 | true→Build Reply 도움말 / false→Build Reply Unknown |
| 9 | **Fire WBS-ORK (진척률)** | command='진척률' | `POST /webhook/wbs-ork` 비동기 호출 (timeout 900초, neverError). body: `{trigger, command, requestedBy}` | fire-and-forget (Merge 미연결) |
| 10 | **Fire WBS-ORK (코드검증)** | command='코드검증' | `POST /webhook/wbs-ork` 비동기 호출. body: `{trigger, command, repo_filter, requestedBy}` | fire-and-forget |
| 11 | **HTTP - Jira 이슈 조회** | command='티켓', `param`=이슈키 | `GET {JIRA_BASE_URL}/rest/api/3/issue/{param}` Basic 인증. neverError | Jira 이슈 JSON |
| 12 | **Build Reply - 티켓** | Jira API 응답 | 상태 이모지 매핑(🔲/🔄/🔍/✅) + 담당자/SP/우선순위 포맷 텍스트 생성 | `replyText` → Merge[0] |
| 13 | **Build Reply - 도움말** | command='도움말' | 4개 명령어 안내 텍스트 하드코딩 | `replyText` → Merge[1] |
| 14 | **Build Reply - Unknown** | 미인식 명령어 | `rawMessage` 포함 안내 텍스트 생성 | `replyText` → Merge[2] |
| 15 | **Merge - 응답 통합** | 티켓/도움말/Unknown 3경로 | 3개 분기 결과를 하나의 스트림으로 합류 | `replyText`, `convId`, `serviceUrl` 통합 |
| 16 | **HTTP - Token 발급** | Merge 결과 | `POST login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token` client_credentials로 Bot Framework 토큰 발급 | `access_token` |
| 17 | **HTTP - Teams 답장** | Token + Merge 데이터 | `POST {serviceUrl}v3/conversations/{convId}/activities` Bearer 토큰으로 `replyText` 전송 | Teams 전송 완료 |

---

#### WBS-ORK — 오케스트레이터 (26노드)

> 📄 [`workflow/WBS-ORK.json`](../workflow/WBS-ORK.json)

| # | 노드명 | Input | 처리 기능 | Output |
|---|--------|-------|-----------|--------|
| 1 | **Manual Trigger** | n8n UI 수동 실행 | 테스트·수동용 트리거 | Init Params |
| 2 | **Webhook** | HTTP POST `/webhook/wbs-ork` | 외부 HTTP 트리거 (TRG-001에서 호출) | Init Params |
| 3 | **Schedule Trigger** | cron `0 17 * * 5` | 매주 금요일 17:00 자동 실행 | Init Params |
| 4 | **Init Params** | 세 트리거 중 하나 | **이번 주 월요일 00:00 UTC** `week_start` 계산. 환경변수에서 `GITHUB_OWNER`, `GITHUB_REPOS`, `JIRA_BOARD_ID`, `JIRA_BASE_URL`, `DESIGN_DOC_REPO/PATH` 로드 | `{owner, repos[], boardId, baseUrl, ddaRepo, ddaPath, week_start, week_end}` |
| 5 | **Call WBS-GRC** | `{owner, repos[]}` | `POST /webhook/wbs-grc`. timeout 5분, 3회 재시도 | GRC 분류 결과 |
| 6 | **Parse GRC Result** | GRC 응답 | `backend[]`, `frontend[]`, `config[]`, `mobile[]`, `commit_messages[]`, `max_active_days` 파싱. 실패 시 빈 배열 대체 | 분류 결과 + 커밋 집계 |
| 7 | **Call WBS-JRA** | `{board_id, commit_messages[]}` | `POST /webhook/wbs-jra`. timeout 10분 | Jira 집계 결과 |
| 8 | **Call WBS-DDA** | `{owner, repo:ddaRepo, path:ddaPath}` | `POST /webhook/wbs-dda`. timeout 10분 | 설계 문서 추출 결과 |
| 9 | **Call WBS-BAK** | `{owner, repos[]:backend 우선}` | `POST /webhook/wbs-bak`. timeout 10분 | Backend 분석 결과 |
| 10 | **Call WBS-FRT** | `{owner, repos[]:frontend 우선}` | `POST /webhook/wbs-frt`. timeout 10분 | Frontend 분석 결과 |
| 11 | **Call WBS-CFG** | `{owner, repos[]:config 우선}` | `POST /webhook/wbs-cfg`. timeout 10분 | Config 분석 결과 |
| 12 | **Call WBS-MOB** | `{owner, repos[]:mobile 우선}` | `POST /webhook/wbs-mob`. timeout 10분 | Mobile 분석 결과 |
| 13 | **Merge All Results** | 6개 Agent 결과 (numberInputs:6) | 6개 결과를 하나의 아이템 스트림으로 합류 | 6개 아이템 배열 |
| 14 | **Integrate Results** | Merge 결과 | `agent_id`로 결과 맵 구성. `agent_id` 없으면 실패 판정(`isRawFailed`). 실패 Agent는 기본값(빈 배열/0) 대체. `failed_agents[]` 생성 | `{jra, dda, bak, frt, cfg, mob, failed_agents[]}` |
| 15 | **Build Call Flow Map** | Integrate 결과 | Mobile/Frontend/Backend Call Flow 레이어별 수집. DDA endpoints vs BAK endpoints 비교. `/webhook/` 경로 제외. `missing_in_actual[]`, `extra_in_actual[]`, `endpoint_match_rate` 계산 | `{integrated_flow{}, missing_in_actual[], extra_in_actual[], endpoint_match_rate}` |
| 16 | **Merge Design Gaps** | Call Flow Map 결과 | BAK/FRT/CFG/MOB `design_gaps[]` 수집+통합. Call Flow 불일치 Gap 추가(missing→high, extra→medium). 중복 제거. High/Medium/Low 건수 집계 | `{all_gaps[], gap_count, high/medium/low_gap_count}` |
| 17 | **Build Gap Analysis Prompt** | Gap 목록 | Gap 0개이면 `_skip_ollama:true`. Gap 있으면 최대 15건으로 OpenAI 프롬프트 생성 (intent 분류: `intentional_improvement/oversight/missing_implementation`) | `{_skip_ollama, model, messages[]}` |
| 18 | **Has Gaps?** | `_skip_ollama` | Gap 존재 여부 분기 | true→OpenAI Gap Analysis / false→No Gaps Pass |
| 19 | **OpenAI Gap Analysis** | messages | `POST api.openai.com/v1/chat/completions` Gap별 intent/recommendation 분석. timeout 600초 | OpenAI 응답 |
| 20 | **Parse Gap Analysis** | OpenAI 응답 | JSON 배열 추출. `item` 기준으로 기존 Gap에 `intent_analysis`, `recommendation` 보강 | `{all_gaps:[{...gap, intent_analysis, recommendation}]}` |
| 21 | **No Gaps Pass** | Has Gaps? false | Gap 없음 — `all_gaps:[]` 그대로 통과 | `{all_gaps:[]}` |
| 22 | **Calc Design Score** | Gap 분석 결과 | 설계 항목 수(`DDA.endpoints+tables+sequences`). 공식: `(설계항목-High Gap수)/설계항목×100`. 등급: 90%↑GREEN / 70%↑YELLOW / 미만RED | `{design_score, design_grade, design_items_total}` |
| 23 | **Calc Progress Score** | Design Score 결과 | `Jira완료율×40% + SP소진율×40% + 활성일/5×20%`. 등급: 70%↑GREEN / 40%↑YELLOW / 미만RED | `{agent_id:'WBS-ORK', total_progress, progress_grade, ...전체 최종 결과}` |
| 24 | **Call WBS-RPT** | 전체 최종 결과 | `POST /webhook/wbs-rpt`. timeout 60초, 3회 재시도 | WBS-RPT 응답 |
| 25 | **Respond to Webhook** | WBS-RPT 응답 (Webhook 트리거 경로) | HTTP 200 최종 결과 반환 | — |
| 26 | **Log Final Result** | WBS-RPT 응답 (Manual/Schedule 트리거 경로) | n8n 콘솔에 진척률/설계점수/커밋/Gap 요약 로그 출력 | 로그 기록 |

---

#### WBS-GRC — GitHub Repo 분류기 (20노드)

> 📄 [`workflow/WBS-GRC.json`](../workflow/WBS-GRC.json)

| # | 노드명 | Input | 처리 기능 | Output |
|---|--------|-------|-----------|--------|
| 1 | **Webhook** | HTTP POST `/webhook/wbs-grc` | 요청 수신 (`responseMode: responseNode`) | body (`owner`, `repos[]`) |
| 2 | **Init Params** | body | `owner`/`repos` 추출, **이번 주 월~현재** `since`/`until` 계산 | `{owner, repos[], since, until}` |
| 3 | **GET User Repos** | `owner` | `GET api.github.com/users/{owner}/repos?per_page=100` GitHub PAT 인증. 3회 재시도 | GitHub Repo 목록 (fullResponse) |
| 4 | **Check Rate Limit** | fullResponse | `x-ratelimit-remaining/limit` 헤더 파싱. 사용률 80% 이상이면 `rate_limit_warning:true` | `{repos[], rate_limit{}, rate_limit_warning}` |
| 5 | **IF Rate Limit Warning** | `rate_limit_warning` | 80% 초과 여부 분기 | true→Warn / false→Merge |
| 6 | **Warn Rate Limit** | warning=true | Teams Webhook으로 Rate Limit 경보 Adaptive Card 전송 (사용률%, 남은 요청 수) | Teams 응답 → Merge |
| 7 | **Merge After Rate Check** | 경보/정상 두 경로 | 두 경로 합류 | Repo 목록 |
| 8 | **Filter & Split Repos** | Repo 목록 | `filterList` 있으면 해당 Repo만 필터링. **각 Repo를 별도 item으로 분리** | `{owner, repo, full_name, since, until}` 배열 |
| 9 | **Loop Over Repos** | Repo item들 | `SplitInBatches(batchSize=1)` 루프. output[0]=완료→Classify / output[1]=배치→GET Root | 현재 Repo 1개 |
| 10 | **GET Root Contents** | 현재 Repo | `GET api.github.com/repos/{full_name}/contents/` 루트 파일 목록 조회 | 루트 파일 목록 |
| 11 | **Attach Repo Info** | Root Contents | 파일명 배열 추출, Loop 컨텍스트에서 `owner/since/until` 복원 | `{owner, repo, full_name, since, until, file_names[]}` |
| 12 | **GET Commits This Week** | Repo 정보 | `GET /commits?since={since}&until={until}&per_page=100` 이번 주 커밋 조회 | 커밋 목록 |
| 13 | **GET Merged PRs** | Repo 정보 | `GET /pulls?state=closed&sort=updated&per_page=50` 최근 PR 조회 | PR 목록 |
| 14 | **Aggregate Commits** | 커밋 목록 | 메시지 최대 30개, **평일(월~금)만** `active_days` 산출 | `{commit_count, active_days, commit_messages[]}` |
| 15 | **Aggregate PRs** | PR 목록 | `merged_at >= since` 필터링. PR 번호/제목/작성자 정리 (최대 20개) | `{merged_pr_count, merged_prs[]}` |
| 16 | **Merge Commit & PR** | Commits + PRs | 두 집계 합류 | 2개 아이템 스트림 |
| 17 | **Build Repo Stats** | Merge 결과 | prData/commitData 구분 후 단일 Repo 통계로 병합 → Loop 복귀 | Repo 완성 통계 1개 |
| 18 | **Classify Repos** | 전체 Repo 통계 | 5단계 우선순위 분류: mobile→config→backend→frontend→unknown. 전체 커밋 집계 | `{backend[], frontend[], config[], mobile[], commit_stats{}}` |
| 19 | **Build Output** | Classify 결과 | `agent_id:'WBS-GRC'` 추가, 최종 구조 정규화 | 최종 JSON |
| 20 | **Respond to Webhook** | 최종 JSON | HTTP 200 응답 반환 | — |

**Check Rate Limit — 80% 경고 기준**

GitHub REST API는 인증된 요청 기준 시간당 5,000건 한도가 있으며, 초과 시 `403 Forbidden`으로 모든 호출이 차단된다. WBS-GRC는 Repo당 최소 4건(Repo 목록·루트 파일·커밋·PR)을 호출하므로 Repo가 많을수록 소모량이 빠르게 증가한다.

| 구간 | 상태 | 동작 |
|------|------|------|
| 0~80% | 정상 | 계속 실행 |
| 80% 도달 | ⚠️ 경고 | Teams 경보 발송 후 계속 실행 |
| 100% 초과 | ❌ 차단 | GitHub API 전체 거부 |

80% 시점에 경고를 보내는 이유는 **남은 20%(약 1,000건)로 현재 실행을 완료할 여유를 확보**하면서, 동시에 운영자가 **다음 실행 전에 대응할 시간**을 주기 위해서다. 100%에서 감지하면 이미 API가 막혀 경고 전송 자체도 실패할 수 있다.

**분류 기준 패턴**:
- `mobile`: `Podfile`, `pubspec.yaml`, `Package.swift`, `build.gradle`
- `config`: `*.tf`, `helmfile.yaml`, `k8s/`, `infra/`
- `backend`: `pom.xml`, `requirements.txt`, `go.mod`, `Cargo.toml`
- `frontend`: `next.config.*`, `vite.config.*`, `angular.json`, `package.json`(서버 엔트리 없는 경우)

**GET /repos/{owner}/{repo}/contents/ 응답 구조**

루트 경로(`/`)를 조회하면 파일·디렉토리 항목의 **배열**로 반환된다.

```json
[
  {
    "type": "file",
    "name": "README.md",
    "path": "README.md",
    "sha": "abc123def456...",
    "size": 1234,
    "url": "https://api.github.com/repos/owner/repo/contents/README.md",
    "html_url": "https://github.com/owner/repo/blob/main/README.md",
    "git_url": "https://api.github.com/repos/owner/repo/git/blobs/abc123...",
    "download_url": "https://raw.githubusercontent.com/owner/repo/main/README.md",
    "encoding": null,
    "content": null,
    "_links": {
      "self": "https://api.github.com/repos/owner/repo/contents/README.md",
      "git": "https://api.github.com/repos/owner/repo/git/blobs/abc123...",
      "html": "https://github.com/owner/repo/blob/main/README.md"
    }
  },
  {
    "type": "dir",
    "name": "src",
    "path": "src",
    "sha": "def456abc123...",
    "size": 0,
    "url": "https://api.github.com/repos/owner/repo/contents/src",
    "html_url": "https://github.com/owner/repo/tree/main/src",
    "git_url": "https://api.github.com/repos/owner/repo/git/trees/def456...",
    "download_url": null,
    "_links": { ... }
  }
]
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `type` | string | `"file"` / `"dir"` / `"symlink"` / `"submodule"` |
| `name` | string | 파일 또는 폴더명 (`README.md`, `src`) |
| `path` | string | 루트 기준 전체 경로 (`src/utils/helper.js`) |
| `sha` | string | Git blob/tree SHA |
| `size` | number | 파일 크기(bytes). 디렉토리는 `0` |
| `download_url` | string \| null | 파일 raw 텍스트 직접 다운로드 URL. 디렉토리는 `null` |
| `content` | string \| null | 디렉토리 조회 시 `null`. 단일 파일 조회 시 Base64 인코딩 내용 |
| `encoding` | string \| null | 단일 파일 조회 시 `"base64"`. 디렉토리 조회 시 `null` |

**WBS-GRC에서 사용하는 필드**

`Attach Repo Info` 노드에서 `name` 필드만 추출해 파일명 배열을 만들고, `Classify Repos` 노드의 분류 기준 패턴과 매칭한다.

```
file_names: ["Podfile", "package.json", "requirements.txt", "README.md", ...]
                  ↓
    mobile? → config? → backend? → frontend? 순서로 패턴 매칭
```

**주의사항**
- 디렉토리 조회 시 하위 항목을 재귀적으로 반환하지 않음 — 한 depth만 반환
- 파일이 1MB 초과이면 `download_url`로만 접근 가능, `content` 필드 비어있음
- 비공개 Repo는 GitHub PAT 인증 필수 (WBS-GRC 이슈 #18 원인)

---

#### WBS-JRA — Jira Sprint 분석기 (13노드)

> 📄 [`workflow/WBS-JRA.json`](../workflow/WBS-JRA.json)

| # | 노드명 | Input | 처리 기능 | Output |
|---|--------|-------|-----------|--------|
| 1 | **Webhook** | HTTP POST `/webhook/wbs-jra` | 요청 수신 | body |
| 2 | **Init Params** | body | `board_id`(기본 8207), `base_url`, `project_keys[]`, `commit_messages[]` 추출 | `{boardId, baseUrl, projectKeys[], commitMessages[]}` |
| 3 | **GET Active Sprint** | `{boardId, baseUrl}` | `GET {baseUrl}/rest/agile/1.0/board/{boardId}/sprint?maxResults=50` Jira API Token 인증. 3회 재시도 | 스프린트 목록 |
| 4 | **Extract Sprint ID** | 스프린트 목록 | `state === 'active'` 필터링 (simple 보드 대응). 없으면 에러 throw. `sprintId/Name/State/Start/EndDate` 추출 | 스프린트 정보 |
| 5 | **Init Pagination** | 스프린트 정보 | `startAt:0`, `maxResults:100`, `allIssues:[]` 페이지네이션 초기화 | 페이지네이션 상태 |
| 6 | **Pagination Loop** | 초기값 또는 루프 복귀 | `SplitInBatches(batchSize=1)`. output[0]=완료→Aggregate / output[1]=배치→GET Issues | 현재 페이지 상태 |
| 7 | **GET Sprint Issues** | 페이지 상태 | `GET /sprint/{sprintId}/issue?startAt={n}&maxResults=100&fields=summary,status,customfield_10016,assignee` | 이슈 목록 + total |
| 8 | **Accumulate Issues** | 이슈 목록 | 이슈 누적. `nextStart` 계산. `hasMore = nextStart < total` | `{allIssues[], startAt:nextStart, hasMore}` |
| 9 | **Has More Pages?** | `hasMore` | true→Pagination Loop 복귀 / false→Aggregate Status | 분기 |
| 10 | **Aggregate Status** | 전체 이슈 | 상태 분류: `todo/in_progress/in_review/done/other` (한글 `완료/진행 중/해야 할 일` 포함). SP 소진율/티켓 완료율 계산 | `{total_tickets, done, sp_burned, sp_burned_rate, ticket_done_rate, incomplete_tickets[]}` |

**Accumulate Issues 노드 상세**

Jira Sprint 이슈를 페이지네이션으로 수집한 뒤 상태별로 집계하고 진척 지표를 산출하는 노드. `GET Sprint Issues`의 응답을 받아 루프를 반복하며 이슈를 누적하고, 루프가 끝나면 전체 이슈를 대상으로 분류·계산을 수행한다.

| 처리 단계 | 내용 |
|-----------|------|
| **이슈 누적** | `allIssues[]`에 이번 페이지 이슈를 append. `nextStart = startAt + items.length` 계산. `hasMore = nextStart < total` 로 루프 지속 여부 결정 |
| **상태 분류** | `status` + `statusCategory` 두 필드 조합으로 5개 버킷 분류. 우선순위: `done → in_review → in_progress → todo → other` |
| **done** | `statusCategory`가 `done`/`완료` 또는 `status`가 `done`, `closed`, `resolved`, `완료` |
| **in_review** | `status`에 `review`, `pr`, `testing`, `qa` 포함 |
| **in_progress** | `statusCategory`가 `indeterminate`/`진행 중` 또는 `status`에 `progress`, `doing`, `dev`, `wip` 포함 |
| **todo** | `statusCategory`가 `new`/`해야 할 일` 또는 `status`가 `to do`, `backlog`, `open` 등 |
| **other** | 위 4가지 미해당 케이스 |
| **SP 계산** | `sp_total` = 전체 이슈 SP 합계. `sp_burned` = done 이슈 SP 합계. `sp_burned_rate` = `sp_burned / sp_total × 100` (%) |
| **완료율 계산** | `ticket_done_rate` = `done 건수 / 전체 이슈 수 × 100` (%) |
| **대표 티켓 수집** | `done_tickets` — 완료 이슈 key + summary 앞 40자 (최대 20건). `incomplete_tickets` — in_review + in_progress 이슈 (최대 20건) |

**출력 필드**

| 필드 | 설명 |
|------|------|
| `total_tickets` | 전체 이슈 수 |
| `done` / `in_review` / `in_progress` / `todo` / `other` | 상태별 이슈 카운트 |
| `sp_total` / `sp_burned` / `sp_burned_rate` | Story Point 소진 현황 |
| `ticket_done_rate` | 티켓 기준 완료율 (%) |
| `done_tickets` | 완료 티켓 목록 (key + summary) |
| `incomplete_tickets` | 미완료 티켓 목록 (in_review + in_progress) |
| `allIssues` | 원본 이슈 전체 (하위 노드 재사용용) |
| `boardId`, `sprintId`, `sprintName`, `sprintStartDate`, `sprintEndDate` | 스프린트 식별·기간 정보 (upstream 전달) |
| `commitMessages` | Git 커밋 메시지 (upstream 전달) |
| 11 | **Map Commits to Jira** | Aggregate 결과 | 커밋 메시지에서 `\b([A-Z][A-Z0-9]+-\d+)\b` 패턴으로 이슈 키 추출. `linked_ticket_count`, `no_commit_issues[]` 생성 | `{jira_commit_map, linked_ticket_count, orphan_commit_keys[], no_commit_issues[]}` |
| 12 | **Build Output** | Map 결과 | `agent_id:'WBS-JRA'`, `repo_type:'jira'` 추가, 빈 필드 초기화 | 최종 JSON |
| 13 | **Respond to Webhook** | 최종 JSON | HTTP 200 응답 반환 | — |

---

#### WBS-DDA — 설계 문서 분석기 (9노드)

> 📄 [`workflow/WBS-DDA.json`](../workflow/WBS-DDA.json)

| # | 노드명 | Input | 처리 기능 | Output |
|---|--------|-------|-----------|--------|
| 1 | **Webhook** | HTTP POST `/webhook/wbs-dda` | 요청 수신 | body (`owner`, `repo`, `path`) |
| 2 | **Init Params** | body | `owner`/`repo`/`path` 추출 (환경변수 fallback). 미설정 시 에러 throw | `{owner, repo, path}` |
| 3 | **GET Design Doc List** | `{owner, repo, path}` | `GET api.github.com/repos/{owner}/{repo}/contents/{path}` GitHub PAT 인증. fullResponse | 폴더 내 파일 목록 |
| 4 | **Filter MD Files** | 파일 목록 | `.md` 확장자 + type=file 필터링. 없으면 에러 throw. 모든 `{name, download_url}` 하나의 아이템으로 묶음 | `{files:[{name, download_url}]}` |
| 5 | **GET File Content** | `files[0].download_url` | 첫 번째 `.md` 파일 raw 텍스트 직접 다운로드 (`responseFormat: text`) | md 파일 텍스트 |
| 6 | **Build OpenAI Request** | md 텍스트 | `## {파일명}\n{내용}` 조합 후 **3000자 절단**. 프롬프트: endpoints/tables/sequences JSON 추출 요청. 모델: `gpt-4.1-mini` | `{model, messages[], stream:false}` |
| 7 | **OpenAI Extract Structure** | messages | `POST api.openai.com/v1/chat/completions` Bearer 인증. timeout 600초 | OpenAI 응답 |
| 8 | **Parse & Build Output** | OpenAI 응답 | `choices[0].message.content` 추출. `` ```json `` 블록 또는 순수 JSON 정규식 파싱. 실패 시 빈 구조체 fallback | `{agent_id:'WBS-DDA', repo_type:'design_doc', endpoints[], tables[], sequences[], error}` |
| 9 | **Respond to Webhook** | 파싱 결과 | HTTP 200 응답 반환 | — |

---

#### WBS-BAK — Backend 코드 분석기 (12노드)

> 📄 [`workflow/WBS-BAK.json`](../workflow/WBS-BAK.json)

| # | 노드명 | Input | 처리 기능 | Output |
|---|--------|-------|-----------|--------|
| 1 | **Webhook** | HTTP POST `/webhook/wbs-bak` | 요청 수신 | body |
| 2 | **Init Params** | body | `owner`, `repos[]`, `since`(기본 -7일), `until` 추출. **repos 배열 각 항목을 별도 item으로 분리** | `{owner, repo, since, until}` 배열 |
| 3 | **GET Commits** | Repo 정보 | `GET /repos/{owner}/{repo}/commits?since={since}&until={until}&per_page=50` GitHub PAT. fullResponse | 커밋 목록 |
| 4 | **Wrap Commits** | fullResponse | `resp.body`에서 커밋 배열 추출. 커밋 0개여도 1개 아이템 보장 | `{commits[], owner, repo, since, until}` |
| 5 | **Extract Commit Info** | 커밋 목록 | SHA 최대 5개, 메시지 최대 20개, `active_days` Set 계산. **커밋 0개이면 `_skip_llm:true`** 즉시 반환 | SHA 목록 또는 skip 플래그 |
| 6 | **GET Commit Files** | `shas[0]` | `GET /repos/{owner}/{repo}/commits/{sha}` 최신 커밋 변경 파일+patch 조회 | 변경 파일 목록 |
| 7 | **Build OpenAI Request** | 변경 파일 | 라우터/컨트롤러 파일 우선 필터링(`routes/`, `controllers/`, `api/` 등). patch 800자/전체 2000자 압축. 프롬프트: endpoints+call_flow JSON 추출. 모델: `gpt-4.1-mini` | `{_meta{}, model, messages[], stream}` |
| 8 | **Skip LLM?** | `_skip_llm` | `_skip_llm===true` 분기. true→빈 결과 직행 / false→OpenAI 호출 | 두 경로 |
| 9 | **OpenAI Extract Call Flow** | messages | `POST api.openai.com/v1/chat/completions` Bearer 인증. timeout 600초 | OpenAI 응답 |
| 10 | **Parse & Build Output** | OpenAI 응답 또는 skip | JSON 파싱. `_meta`에서 repo/커밋 정보 복원 | `{agent_id:'WBS-BAK', repo_type:'backend', call_flow[], extracted_endpoints[], commit_count, active_days}` |
| 11 | **Aggregate Results** | 복수 Repo 결과 | 1개면 그대로, 2개 이상이면 `results[]` 배열로 묶음 | 통합 결과 |
| 12 | **Respond to Webhook** | 통합 결과 | HTTP 200 응답 반환 | — |

---

#### WBS-FRT / WBS-CFG / WBS-MOB — 코드 분석기 (각 12노드)

> 📄 [`workflow/WBS-FRT.json`](../workflow/WBS-FRT.json) / [`WBS-CFG.json`](../workflow/WBS-CFG.json) / [`WBS-MOB.json`](../workflow/WBS-MOB.json)

WBS-BAK와 동일한 12노드 구조. Agent별 차이점:

| 항목 | WBS-FRT | WBS-CFG | WBS-MOB |
|------|---------|---------|---------|
| `agent_id` | `WBS-FRT` | `WBS-CFG` | `WBS-MOB` |
| `repo_type` | `frontend` | `config` | `mobile` |
| 파일 필터 경로 | `api/`, `services/`, `hooks/`, `store/`, `pages/`, `views/` | `config/`, `helm/`, `k8s/`, `terraform/` | `screens/`, `pages/`, `navigation/`, `api/`, `services/` |
| 파일 필터 확장자 | `.js/.ts/.jsx/.tsx/.vue/.svelte` | `.yaml/.yml/.json/.toml/.tf/.conf` | `.swift/.kt/.dart/.tsx/.jsx` |
| LLM 추출 목표 | API 호출 패턴 + 컴포넌트 흐름 | 인프라 config 항목 + 변경사항 | 화면 전환 흐름 + API 호출 |
| 빈 결과 키 | `api_calls:[]` | `config_items:[]` | `screens:[]` |
| OpenAI 노드명 | `OpenAI Extract API Calls` | `OpenAI Extract Config` | `OpenAI Extract Screen Flow` |
| LLM 출력 JSON 키 | `{api_calls[], call_flow[]}` | `{config_items[], call_flow[]}` | `{screens[], call_flow[]}` |

---

#### WBS-RPT — 리포트 발송 (7노드)

> 📄 [`workflow/WBS-RPT.json`](../workflow/WBS-RPT.json)

| # | 노드명 | Input | 처리 기능 | Output |
|---|--------|-------|-----------|--------|
| 1 | **Webhook** | HTTP POST `/webhook/wbs-rpt` (WBS-ORK 호출) | WBS-ORK 전체 분석 결과 수신 | WBS-ORK 결과 JSON |
| 2 | **Build Report Data** | WBS-ORK 결과 | 진척률 등급 이모지 매핑(🟢/🟡/🔴). 미완료 티켓 최대 5건 + "외 N건". High Gap 상세 최대 3건. 실패 Agent 경고 문구. 최종 Teams 텍스트 메시지 조립 | `{teams_message, ...보고서 데이터}` |
| 3 | **Build Teams Card** | 보고서 데이터 | Adaptive Card v1.0 구성 (TextBlock+FactSet만 사용 — Table/ColumnSet 미지원). 카드: 제목/기간/진척률/Jira현황/GitHub활동/미완료티켓/Gap요약. payload: `{attachments:[{contentType:'application/vnd.microsoft.card.adaptive', content:card}]}` | `{teams_payload, teams_url}` |
| 4 | **Send Teams Message** | `teams_payload` | `POST {TEAMS_WEBHOOK_URL}` Power Automate Webhook. `Content-Type: application/json`. timeout 30초, neverError | Teams 전송 결과 |
| 5 | **Check Teams Result** | 전송 결과 | statusCode < 400이면 `teams_sent:true`. URL 없으면 `teams_skipped:true`. 보고서 데이터와 병합 | `{teams_sent, teams_skipped, teams_status}` |
| 6 | **Build Final Summary** | Check 결과 | 최종 summary만 추출. `confluence_updated:false`, `confluence_skipped:true` 고정 (조직 정책으로 Confluence API 차단) | `{agent_id:'WBS-RPT', teams_sent, total_progress, design_score, error:null}` |
| 7 | **Respond to Webhook** | 최종 summary | HTTP 200 응답 반환 | — |

> 📄 [`wiki/agents.md:58`](wiki/agents.md) — Agent별 상세 명세 (Webhook 경로·테스트 결과)

---

#### WBS-TRG-002 — Cron 스케줄러 (3노드) 🚫 중단

> 📄 [`workflow/WBS-TRG-002.json`](../workflow/WBS-TRG-002.json)

| # | 노드명 | Input | 처리 기능 | Output |
|---|--------|-------|-----------|--------|
| 1 | **Schedule Trigger** | 시스템 시간 | cron `0 17 * * 5` — 매주 금요일 17:00 자동 실행 | 트리거 신호 |
| 2 | **Call WBS-ORK** | 트리거 신호 | `POST /webhook/wbs-ork` 호출. body: `{trigger:"cron", schedule:"weekly_friday_1700"}`. timeout 900초 | WBS-ORK 전체 결과 JSON |
| 3 | **Log Result** | WBS-ORK 응답 | `total_progress` 존재 여부로 성공/부분성공 판단. 실행 요약 로그 생성 (`cron_fired_at`, `status`, `total_progress`, `design_score`) | 실행 요약 JSON |

---

#### WBS-ERR — 전역 에러 핸들러 (4노드) 🚫 중단

> 📄 [`workflow/WBS-ERR.json`](../workflow/WBS-ERR.json)

| # | 노드명 | Input | 처리 기능 | Output |
|---|--------|-------|-----------|--------|
| 1 | **Error Trigger** | n8n 내부 에러 이벤트 | 다른 워크플로우에서 에러 발생 시 자동 수신. `workflow.name`, `execution.lastNodeExecuted`, `execution.error.*`, `execution.url` 포함 | 에러 컨텍스트 JSON |
| 2 | **Build Error Message** | 에러 컨텍스트 | 워크플로명/노드명/에러 메시지/KST 타임스탬프/실행 로그 URL을 조합한 알림 텍스트 생성 | `text` 필드 포함 JSON |
| 3 | **Get Token** | Build Error Message 결과 | Microsoft OAuth2 client_credentials로 Bot Framework 토큰 발급 (재시도 2회, 10초 간격) | `access_token` |
| 4 | **Send Error to Teams** | Token + 에러 텍스트 | `TEAMS_WEBHOOK_URL`로 Adaptive Card 전송. 헤더: `🚨 WBS Agent 오류 발생` (Attention 색상). 재시도 2회 | Teams 전송 완료 |

---

## 4. 진척률 계산 공식

### 전체 진척률

```
total_progress = (Jira 티켓 완료율 × 0.4) + (SP 소진률 × 0.4) + (Commit 활성일률 × 0.2)

Commit 활성일률 = min(100, active_days / 5 × 100)
SP 데이터 없으면 → SP 소진률 = Jira 티켓 완료율로 대체
```

| 등급 | 기준 |
|------|------|
| 🟢 GREEN | 70% 이상 |
| 🟡 YELLOW | 40% 이상 |
| 🔴 RED | 40% 미만 |

### 설계 적합성 점수

```
design_score = (설계 항목 수 - High Gap 수) / 설계 항목 수 × 100

설계 항목 = DDA endpoints 수 + tables 수 + sequences 수
설계 항목이 0이면 → Gap 없으면 100점, High Gap 1건당 15점 차감
```

| 등급 | 기준 |
|------|------|
| 🟢 GREEN | 90% 이상 |
| 🟡 YELLOW | 70% 이상 |
| 🔴 RED | 70% 미만 |

### 심각도 분류

| 심각도 | 기준 |
|--------|------|
| 🔴 High | 동작이 달라지는 변경 (엔드포인트 삭제, 필수 파라미터 제거) |
| 🟡 Medium | 스펙은 바뀌었으나 기능적으로 유사 (필드명 변경, 타입 변경) |
| 🟢 Low | 설계 외 추가 구현 (새 엔드포인트, 추가 컬럼) |

> 📄 [`wiki/phase3.md:80`](wiki/phase3.md) — 진척률·설계 적합성 공식 코드  
> 📄 [`wiki/phase3.md:108`](wiki/phase3.md) — 부분 실패 처리 `resultMap` 패턴 코드  
> 📄 [`wiki/project-overview.md:66`](wiki/project-overview.md) — 진척률 계산 방식 표

---

## 5. 개발 Phase 요약

### Phase 0 — 환경 준비 ✅

n8n Docker 설치, GitHub·Jira·Teams 자격증명 설정, n8n Variables 7개 등록.

주요 설정값:
- `GITHUB_OWNER`: `hanhosunglgu`
- `GITHUB_REPOS`: `["WBS_Check"]`
- `JIRA_BASE_URL`: `https://lgucorp.atlassian.net`
- `JIRA_BOARD_ID`: `8207`
- `N8N_WEBHOOK_TIMEOUT=900`, `N8N_RUNNERS_TASK_TIMEOUT=900` (타임아웃 방지)

> 📄 [`wiki/environment.md:5`](wiki/environment.md) — n8n Variables 7개 확정값  
> 📄 [`wiki/environment.md:36`](wiki/environment.md) — `.env` 전체 환경변수 목록  
> 📄 [`env-setup.md:80`](env-setup.md) — Docker Compose 적용 방법

---

### Phase 1 — Specialist Agent 구현 ✅

6개 코드 분석 Agent (WBS-GRC, WBS-DDA, WBS-BAK, WBS-FRT, WBS-CFG, WBS-MOB) 구현 및 WBS-INT(57노드) 통합 테스트로 6/6 ALL_PASS 검증.

**확립된 핵심 구현 패턴**:

| 패턴 | 내용 |
|------|------|
| `_meta` 패턴 | 모든 Agent가 공통 메타데이터(`agent_id`, `repo`, `repo_type`)를 출력에 포함 |
| `SplitInBatches` 포트 | `output[0]`=배치 데이터, `output[1]`=완료 신호 (순서 혼동 시 무한루프) |
| Webhook 입력 처리 | `$input.first().json`으로 수신 데이터 참조 |

**주요 이슈 해결**:
- WBS-INT 노드 참조 이름 충돌 → 9개 노드 prefix 적용으로 해결
- Ollama 6개 순차 호출로 7~8분 소요 → `N8N_WEBHOOK_TIMEOUT=900` 설정

> 📄 [`phase1-guide.md:129`](phase1-guide.md) — 공통 노드 패턴 (`_meta`, SplitInBatches, Webhook) 상세  
> 📄 [`wiki/environment.md:141`](wiki/environment.md) — n8n 핵심 구현 패턴 3가지  
> 📄 [`wiki/progress.md:306`](wiki/progress.md) — 이슈 1~3 원인·해결 상세

---

### Phase 2 — 진척률 수집 ✅

WBS-JRA (Jira Sprint 데이터 수집, 13노드)와 WBS-GRC 확장 (GitHub Commit/PR 집계, 6노드 추가) 구현.

**주요 해결 이슈**:

| 이슈 | 원인 | 해결 |
|------|------|------|
| Jira Board `simple` 타입 미지원 | `?state=active` Sprint API 미지원 | JS 코드로 필터링 분기 처리 |
| 한글 상태명 인식 불가 | `완료`/`진행 중` 그대로 반환 | `완료`→`Done` 매핑 테이블 추가 |
| `$vars` 미지원 | n8n Community Edition 제약 | `$env.VAR_NAME` 방식으로 전환 |

> 📄 [`phase2-guide.md:109`](phase2-guide.md) — WBS-JRA 13노드 전체 상세  
> 📄 [`wiki/phase2.md:288`](wiki/phase2.md) — 이슈 1~6 원인·해결 목록

---

### Phase 3 — Orchestration ✅

WBS-ORK 오케스트레이터 26노드 구현. 6개 Agent를 병렬 호출하고 결과를 취합하여 진척률 계산.

**핵심 구현**:

```javascript
// 부분 실패 처리 — resultMap 패턴
const resultMap = {};
for (const item of items) {
  const id = item.json.agent_id || 'unknown';
  resultMap[id] = item.json;
}
const jra = resultMap['WBS-JRA'] || { total_tickets: 0, error: 'skipped' };
const failedAgents = [jra, dda, bak, frt, cfg, mob]
  .filter(a => a.error && a.error !== null)
  .map(a => a.agent_id);
```

- `isRawFailed()`: `neverError:true` 설정 시 빈 응답도 통과하는 문제 → `agent_id` 부재로 실패 판단
- Merge 노드 `numberInputs:6`으로 6개 Agent 결과 동기화

> 📄 [`wiki/phase3.md:78`](wiki/phase3.md) — 진척률·설계 적합성 계산 공식 및 부분 실패 처리 코드  
> 📄 [`phase3-guide.md:114`](phase3-guide.md) — WBS-ORK 25노드 전체 흐름도

---

### Phase 4 — 리포트 출력 ✅

WBS-RPT 11노드 구현. Microsoft Teams Adaptive Card로 리포트 발송.

**Teams 제약 사항 및 해결**:

| 문제 | 원인 | 해결 |
|------|------|------|
| `Property 'type' must be 'AdaptiveCard'` 오류 | 잘못된 wrapper 포맷 | `attachments[].content` 구조로 수정 |
| `unsupported card element` | Teams가 Table/ColumnSet 미지원 | TextBlock + FactSet 조합으로 단순화 |
| Teams 메시지 미수신 | Power Automate 내부 실패 | make.powerautomate.com 실행 이력 직접 확인 |

전송 포맷:
```json
{
  "attachments": [{
    "contentType": "application/vnd.microsoft.card.adaptive",
    "content": { "type": "AdaptiveCard", "version": "1.0", ... }
  }]
}
```

> 📄 [`phase4-guide.md:57`](phase4-guide.md) — Teams 메시지 형식·Adaptive Card 제약 상세  
> 📄 [`wiki/dev-log.md:306`](wiki/dev-log.md) — Phase 4 Teams 포맷 3차 수정 이력

---

### Phase 5 — 트리거 연동 및 안정화 ✅

Cron 스케줄러(WBS-TRG-002), Teams Bot 비동기 처리(WBS-TRG-001), E2E 테스트 PASS.

**주요 해결 이슈**:

| 이슈 | 원인 | 해결 |
|------|------|------|
| IF 노드 v2 활성화 실패 | n8n v2.14에서 `options` 위치 스키마 변경 | Python으로 4개 노드 파라미터 구조 수정 |
| WBS-ORK hang (60초 후 종료) | `N8N_RUNNERS_TASK_TIMEOUT` 기본값 60초 | `900`초로 증가 |
| Bot 15초 타임아웃 | Teams Bot이 15초 내 응답 없으면 타임아웃 | 즉시 `200 OK` 응답 후 비동기 처리 패턴 도입 |
| ngrok TLS 차단 | Teams가 ngrok 도메인 차단 | cloudflared 터널로 대체 |

**E2E 최종 결과 (2026-05-15)**:
- 실행 시간: 512초
- `total_progress: 20% (RED)`, `design_score: 100% (GREEN)`
- `teams_sent: true`, `failed_agents: []`

> 📄 [`phase5-guide.md:125`](phase5-guide.md) — E2E 테스트 결과 상세  
> 📄 [`E2E_Final_test.md:422`](E2E_Final_test.md) — 최종 테스트 PASS 기록

---

## 6. Post-Phase 버그 수정 (2026-05-19~20)

### Ollama → OpenAI 전환

로컬 Ollama(`qwen2.5-coder:7b`) 타임아웃·안정성 문제로 `gpt-4.1-mini`로 전환.
- 내장 OpenAI 노드 + "OpenAI account" Credential 방식 사용
- `OPENAI_API_KEY` 환경변수 미지원(Community Edition) → Credential 오브젝트로 대체

> 📄 [`session-log-2026-05-19.md:1`](session-log-2026-05-19.md) — 전환 세션 전체 기록

---

### WBS-DDA 재구현 (SplitInBatches 완전 제거)

**문제 연쇄**:
1. `SplitInBatches typeVersion 3` + 단일 아이템 → done 포트 즉시 이동, loop body 스킵
2. Loop done 포트에서 `$('Decode Base64').all()` 미실행
3. GitHub API rate limit (PAT 없는 anonymous 요청)

**최종 구조** (9노드, Loop 없음):
```
Webhook → Init Params → GET Design Doc List → Filter MD Files
→ GET File Content (첫 번째 파일만) → Build OpenAI Request
→ OpenAI Extract Structure → Parse & Build Output → Respond to Webhook
```

**생성된 설계 문서** (`hanhosunglgu/WBS_Check/docs/design/`):
- `api-design.md` — 9개 webhook endpoints, 요청/응답 스키마
- `db-schema.md` — n8n DB 테이블, 주간 리포트 JSON 구조
- `sequence-design.md` — 4개 시퀀스 흐름, 에러 처리 테이블

> 📄 [`wiki/dev-log.md:23`](wiki/dev-log.md) — WBS-DDA 재구현 문제 연쇄 및 최종 구조

---

### design_score: 10 버그 수정

**원인**: `api-design.md`에 `/webhook/wbs-ork` 등 n8n 내부 경로 9개가 endpoint로 추출됨  
→ 실제 앱 API 0개 대비 9개 모두 `missing_in_actual` → High severity gap 9건  
→ `(10-9)/10 × 100 = 10`

**수정** (`Build Call Flow Map` 노드):
```javascript
const isWebhookPath = e => toStr(e).includes('/webhook/');
const comparableDesignEndpoints = designEndpoints.filter(e => !isWebhookPath(e));
```

**n8n 캐시 갱신 방법** (DB 직접 수정은 메모리에 미반영):
```bash
curl -X PUT "http://localhost:5678/api/v1/workflows/{id}" \
  -H "X-N8N-API-KEY: {key}" \
  -H "Content-Type: application/json" \
  -d @payload.json
```

**결과**: `design_score: 10 (RED)` → `design_score: 100 (GREEN)`

> 📄 [`wiki/dev-log.md:45`](wiki/dev-log.md) — design_score 버그 원인 분석·수정 코드·캐시 갱신 방법

---

## 7. 주요 기술 이슈 21건 전체 목록

| # | 이슈 | 원인 | 해결 | Phase |
|---|------|------|------|-------|
| 1 | WBS-INT 노드 참조 이름 충돌 | `$('nodeName')` agent prefix 미반영 | 9개 노드 참조 수정 | 1 |
| 2 | WBS-INT Webhook Timeout | Ollama 6개 순차 실행 7~8분 초과 | `N8N_WEBHOOK_TIMEOUT=900` | 1 |
| 3 | WBS-DDA Ollama JSON Body 오류 | `_meta` 포함 전체 `$json` 전송 → streaming | 필요 필드만 명시적 추출 | 1 |
| 4 | WBS-ORK Webhook 404 | `httpMethod`, `responseMode` 파라미터 누락 | 3개 파라미터 추가 | 3 |
| 5 | failed_agents 3개 감지 | WBS-DDA/CFG/MOB n8n 미활성화 | n8n UI에서 수동 활성화 | 3 |
| 6 | Teams 메시지 미수신 | Power Automate 내부 실패 | make.powerautomate.com 실행 이력 확인 | 4 |
| 7 | `Property 'type' must be 'AdaptiveCard'` | 잘못된 wrapper 포맷 | `attachments[].content` 구조로 수정 | 4 |
| 8 | `unsupported card element` | Table/ColumnSet Teams 미지원 | TextBlock + FactSet으로 단순화 | 4 |
| 9 | WBS-TRG-001 활성화 실패 | IF v2 노드 `options` 위치 오류 | Python으로 4개 노드 파라미터 구조 수정 | 5 |
| 10 | WBS-ORK hang | `N8N_RUNNERS_TASK_TIMEOUT` 기본 60초, Ollama 238초 초과 | `N8N_RUNNERS_TASK_TIMEOUT=900` | 5 |
| 11 | `failed_agents` 미감지 | `neverError:true` 빈 응답 시 `agent_id` 없어 통과 | `isRawFailed()` 함수로 `agent_id` 부재 감지 | 5 |
| 12 | SplitInBatches 루프 미진입 | typeVersion 3 + executionOrder v1 충돌 | typeVersion 2 다운그레이드, executionOrder 제거 | DDA 재구현 |
| 13 | Loop done 포트 노드 참조 불가 | n8n이 루프 내부 노드를 done 시점에 미실행 처리 | Store File Content 중간 노드로 누적 후 참조 | DDA 재구현 |
| 14 | OPENAI_API_KEY undefined | Community Edition Variables 미지원 | 내장 OpenAI 노드 + Credential 방식 | DDA/RPT |
| 15 | Teams URL undefined | Community Edition `$vars` 미지원 | TEAMS_WEBHOOK_URL 워크플로 JSON 하드코딩 | RPT |
| 16 | WBS-FRT/CFG/MOB "No Respond to Webhook" | 이전 구조(splitInBatches 포함) | WBS-BAK 템플릿으로 재생성 | Post |
| 17 | WBS-DDA splitInBatches loop 스킵 | typeVersion 3 + 단일 아이템 → done 즉시 | Loop 완전 제거, 첫 파일만 처리 | Post |
| 18 | WBS-DDA GitHub API rate limit | PAT 없는 anonymous 요청 | GitHub PAT credential 추가 | Post |
| 19 | design_score: 10 | `/webhook/` 경로가 endpoint로 추출 → High gap 9건 | `isWebhookPath` 필터로 n8n 내부 경로 제외 | Post |
| 20 | n8n DB 직접 수정 캐시 미반영 | n8n 메모리 캐시는 REST API 이벤트로만 갱신 | `PUT /api/v1/workflows` API 사용 | Post |
| 21 | n8n API 키 Forbidden | scopes 컬럼 null → `scopes.includes()` 에러 | DB에서 scopes JSON 배열로 업데이트 | Post |

> 📄 [`wiki/progress.md:303`](wiki/progress.md) — 이슈 1~11 전체 목록  
> 📄 [`wiki/progress.md:365`](wiki/progress.md) — 이슈 12~21 추가 목록  
> 📄 [`wiki/dev-log.md:1`](wiki/dev-log.md) — 날짜별 상세 개발 기록

---

## 8. 환경 설정 요약

### n8n Variables (7개) — `Settings → Variables`

| Key | Value | 용도 |
|-----|-------|------|
| `GITHUB_OWNER` | `hanhosunglgu` | GitHub Username |
| `GITHUB_REPOS` | `["WBS_Check"]` | 분석 대상 Repo 목록 |
| `JIRA_BASE_URL` | `https://lgucorp.atlassian.net` | Jira Cloud URL |
| `JIRA_PROJECT_KEYS` | `["WBS"]` | 모니터링 프로젝트 키 |
| `JIRA_BOARD_ID` | `8207` | Sprint 조회용 Board ID |
| `DESIGN_DOC_REPO` | `hanhosunglgu/WBS_Check` | 설계 문서 저장 Repo |
| `DESIGN_DOC_PATH` | `WBS_Check/docs/design` | 설계 문서 경로 |

### n8n Credentials (4개) — `Settings → Credentials`

| Credential | 유형 | 용도 |
|-----------|------|------|
| Teams Bot OAuth2 | HTTP Header Auth | Microsoft Bot Framework Token 발급 |
| GitHub PAT | HTTP Header Auth | GitHub REST API 인증 |
| Jira API Token | Basic Auth | Jira Cloud API 인증 |
| OpenAI | API Key | gpt-4.1-mini 호출 |

### 주요 환경변수 (.env)

```env
N8N_WEBHOOK_TIMEOUT=900           # Phase 1 이슈 2 해결
N8N_RUNNERS_TASK_TIMEOUT=900      # Phase 5 이슈 10 해결
TEAMS_WEBHOOK_URL=<Power Automate URL>
GITHUB_PAT=<PAT>
JIRA_API_TOKEN=<token>
```

> 📄 [`wiki/environment.md:5`](wiki/environment.md) — Variables 확정값 전체  
> 📄 [`wiki/environment.md:22`](wiki/environment.md) — Credentials 목록  
> 📄 [`wiki/environment.md:77`](wiki/environment.md) — Workflow 파일명·상태 전체 목록

---

## 9. 사용 노드 요약

이번 프로젝트에서 사용된 n8n 노드 타입을 기준으로 분류·집계한 전체 요약이다.

**전체 노드 수: 147개** (10개 Agent 합산 — TRG-001 17 + ORK 26 + GRC 20 + JRA 13 + DDA 9 + BAK 12 + FRT 12 + CFG 12 + MOB 12 + RPT 7 + TRG-002 3 + ERR 4)

### 노드 타입별 사용 현황

| 노드 타입 | 사용 수 | 역할 |
|-----------|---------|------|
| **Code** | 약 40개 | JS 커스텀 로직 전반 — 데이터 파싱, 프롬프트 조립, 진척률 계산, Gap 분석 등 |
| **HTTP Request** | 약 30개 | 외부 API 호출 — GitHub, Jira, OpenAI, Teams, Microsoft OAuth2 |
| **Webhook** | 9개 | 각 Agent의 Sub-workflow 진입점 (`/webhook/wbs-*`) |
| **Respond to Webhook** | 7개 | 각 Agent의 HTTP 200 응답 반환 |
| **IF** | 7개 | 조건 분기 — 명령어 라우팅, Gap 존재 여부, Rate Limit 경고, Skip LLM 등 |
| **Merge** | 6개 | 복수 경로 합류 — 분기 재합류, 멀티 Agent 결과 수렴 |
| **Set** | 5개 | 필드 평탄화·추출 — Init Params, 메시지 파싱 등 |
| **Schedule Trigger** | 2개 | Cron 기반 자동 실행 — WBS-ORK(매주 금 17:00), WBS-TRG-002 |
| **Manual Trigger** | 1개 | n8n UI 수동 실행 (WBS-ORK 테스트용) |
| **Error Trigger** | 1개 | 다른 워크플로 에러 발생 시 자동 수신 (WBS-ERR) |
| **SplitInBatches** | 1개 | Repo·Sprint 이슈 루프 처리 (WBS-GRC, WBS-JRA) |
| **OpenAI** | 5개 | LLM 호출 — 설계 문서 파싱, Call Flow 추출, Gap intent 분석 |

---

### 노드 타입별 상세

#### Code 노드
프로젝트 전체에서 가장 많이 사용된 노드. n8n 내장 노드만으로 처리하기 어려운 복잡한 로직을 JavaScript로 직접 구현한다.

| 용도 | 사용 Agent | 주요 처리 내용 |
|------|-----------|--------------|
| 파라미터 초기화 | 전체 Agent | 환경변수 로드, 날짜 범위 계산, 기본값 설정 |
| 데이터 파싱 | 전체 Agent | API 응답 정제, JSON 추출, 필드 재구성 |
| 프롬프트 조립 | DDA, BAK, FRT, CFG, MOB, ORK | 파일 내용·코드 diff를 LLM 프롬프트로 변환, 토큰 절단 |
| 진척률 계산 | ORK | Jira 완료율 × 40% + SP 소진율 × 40% + 활성일율 × 20% |
| Gap 분석 | ORK | design_gaps 수집·통합·중복 제거, 심각도 집계 |
| Call Flow 비교 | ORK | DDA endpoints vs BAK endpoints 비교, match_rate 계산 |
| 상태 집계 | JRA | Sprint 이슈 상태 분류(한글 포함), SP 소진율 산출 |
| Repo 분류 | GRC | 루트 파일명 패턴으로 mobile/config/backend/frontend 분류 |
| 보고서 조립 | RPT | 진척률 등급 이모지 매핑, Teams Adaptive Card 페이로드 생성 |
| 명령어 파싱 | TRG-001 | HTML 태그 제거, 명령어 키워드 추출 및 매핑 |
| 에러 메시지 생성 | ERR | 워크플로명·노드명·KST 타임스탬프 조합 알림 텍스트 생성 |

---

#### HTTP Request 노드
외부 서비스와의 모든 통신을 담당한다. n8n 내장 인증(Basic, Bearer, Header) 방식을 활용하며 `neverError`, 재시도 횟수, timeout을 각 호출 특성에 맞게 설정한다.

| 호출 대상 | 사용 Agent | 주요 엔드포인트 |
|-----------|-----------|--------------|
| GitHub REST API | GRC, BAK, FRT, CFG, MOB, DDA | `/users/{owner}/repos`, `/repos/{repo}/commits`, `/repos/{repo}/pulls`, `/repos/{repo}/contents/` |
| Jira Cloud API | JRA, TRG-001 | `/rest/agile/1.0/board/{id}/sprint`, `/rest/api/3/issue/{key}` |
| OpenAI API | DDA, BAK, FRT, CFG, MOB, ORK | `POST /v1/chat/completions` (timeout 600초) |
| Microsoft OAuth2 | TRG-001, ERR | `POST /oauth2/v2.0/token` (client_credentials) |
| Teams Bot Framework | TRG-001, ERR | `POST {serviceUrl}v3/conversations/{convId}/activities` |
| Teams Webhook | GRC, RPT | Power Automate Incoming Webhook (Adaptive Card 전송) |
| Sub-workflow 호출 | ORK, TRG-001, TRG-002 | `POST /webhook/wbs-*` (내부 Agent 간 HTTP 통신) |

---

#### Webhook / Respond to Webhook 노드
각 Sub-workflow의 진입·출구를 담당한다. `responseMode: responseNode`로 설정해 응답 타이밍을 하위 노드가 직접 제어한다.

| Agent | Webhook 경로 | Respond 위치 |
|-------|------------|-------------|
| TRG-001 | `/webhook/teams-trigger` | 노드 #4 (즉시 200 반환 후 비동기 처리) |
| ORK | `/webhook/wbs-ork` | 노드 #25 |
| GRC | `/webhook/wbs-grc` | 노드 #20 |
| JRA | `/webhook/wbs-jra` | 노드 #13 |
| DDA | `/webhook/wbs-dda` | 노드 #9 |
| BAK | `/webhook/wbs-bak` | 노드 #12 |
| RPT | `/webhook/wbs-rpt` | 노드 #7 |

---

#### IF 노드
조건에 따라 워크플로 실행 경로를 분기한다. `true` / `false` 두 출력 포트로 각각 다른 노드에 연결된다.

| 노드명 | 조건 | true 경로 | false 경로 |
|--------|------|----------|-----------|
| IF 진척률 | `command === '진척률'` | Fire WBS-ORK | IF 코드검증 |
| IF 코드검증 | `command === '코드검증'` | Fire WBS-ORK | IF 티켓 |
| IF 티켓 | `command === '티켓'` | HTTP Jira 조회 | IF 도움말 |
| IF 도움말 | `command === '도움말'` | Build Reply 도움말 | Build Reply Unknown |
| IF Rate Limit Warning | `used_pct >= 80` | Warn Rate Limit | Merge |
| Has Gaps? | `_skip_ollama !== true` | OpenAI Gap Analysis | No Gaps Pass |
| Skip LLM? | `_skip_llm === true` | 빈 결과 직행 | OpenAI Extract Call Flow |

---

#### Merge 노드
복수의 분기 경로를 하나의 스트림으로 합류시킨다. `numberInputs` 파라미터로 입력 수를 지정하며, 모든 입력이 도착해야 다음 노드로 진행한다.

| 노드명 | 입력 수 | 합류 경로 |
|--------|--------|---------|
| Merge - 응답 통합 | 3 | 티켓 응답 / 도움말 / Unknown |
| Merge After Rate Check | 2 | Rate Limit 경보 경로 / 정상 경로 |
| Merge Commit & PR | 2 | 커밋 집계 / PR 집계 |
| Merge All Results | 6 | JRA / DDA / BAK / FRT / CFG / MOB 전체 결과 수렴 |
| Merge Design Gaps | 1 | Gap 분석 완료 후 통합 |
| No Gaps Pass | 1 | Gap 없음 패스스루 |

---

#### SplitInBatches 노드
배열 데이터를 1개씩 꺼내 루프를 구성한다. `output[0]`(완료)과 `output[1]`(배치) 두 포트의 순서를 반드시 정확히 연결해야 하며, 잘못 연결하면 무한루프가 발생한다 (이슈 #12 원인).

| 사용 위치 | 루프 대상 | 완료 포트 연결 |
|-----------|---------|-------------|
| GRC - Loop Over Repos | Repo 목록 (1개씩) | Classify Repos |
| JRA - Pagination Loop | Sprint 이슈 페이지 (1페이지씩) | Aggregate Status |

---

#### OpenAI 노드
`POST /v1/chat/completions`를 호출해 LLM 분석을 수행한다. 모든 호출에 `stream: false`를 명시해 n8n의 스트리밍 미지원 문제를 방지한다 (이슈 #3 원인). 모델은 초기 Ollama(`qwen2.5-coder:7b`)에서 `gpt-4.1-mini`로 전환되었다.

| 노드명 | 사용 Agent | 추출 목표 |
|--------|-----------|---------|
| OpenAI Extract Structure | DDA | `endpoints / tables / sequences` (설계 문서 파싱) |
| OpenAI Extract Call Flow | BAK | `endpoints / call_flow` (Backend 코드 분석) |
| OpenAI Extract API Calls | FRT | `api_calls / call_flow` (Frontend 코드 분석) |
| OpenAI Extract Config | CFG | `config_items / call_flow` (IaC 코드 분석) |
| OpenAI Extract Screen Flow | MOB | `screens / call_flow` (Mobile 코드 분석) |
| OpenAI Gap Analysis | ORK | Gap별 `intent_analysis / recommendation` 분류 |

---

#### Schedule Trigger / Manual Trigger / Error Trigger 노드

| 노드 타입 | 사용 위치 | 동작 |
|-----------|---------|------|
| Schedule Trigger | ORK, TRG-002 | cron `0 17 * * 5` — 매주 금요일 17:00 자동 실행 |
| Manual Trigger | ORK | n8n UI에서 수동 실행 (개발·테스트용) |
| Error Trigger | ERR | 다른 워크플로에서 에러 발생 시 자동 수신, Teams 에러 알림 발송 |

---

## 10. 최종 상태 (2026-05-20 기준)

| 항목 | 값 |
|------|-----|
| 전체 Phase | ✅ Phase 0~5 + Post 모두 완료 |
| total_progress | 20% (🔴 RED) |
| design_score | 100% (🟢 GREEN) |
| teams_sent | true |
| failed_agents | [] |
| E2E 실행 시간 | 512초 |
| LLM | OpenAI gpt-4.1-mini |
| 외부 터널 | cloudflared |
| n8n API Key | `n8n_api_36b455be43bb6db0df64f3270f8e9f07be6da9de9b65d226` |
| WBS-ORK Workflow ID | `SC2JB9Z7HpZnbt4F` |

> 📄 [`wiki/README.md:80`](wiki/README.md) — Post-Phase 최종 상태 요약  
> 📄 [`wiki/progress.md:382`](wiki/progress.md) — 2026-05-20 버그 수정 완료 기록  
> 📄 [`E2E_Final_test.md:422`](E2E_Final_test.md) — E2E 최종 테스트 PASS 상세
