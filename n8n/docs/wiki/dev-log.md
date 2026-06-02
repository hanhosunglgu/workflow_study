# 개발 이력

개발 과정에서의 주요 결정 사항, 이슈 및 해결 내용을 기록한다.

---

## 2026-06-02 — n8n_project-summary.md 보강 및 workflow Sticky Note 추가

### n8n_project-summary.md 변경사항

#### 노드명 일괄 변경 — Ollama → OpenAI

WBS-BAK / WBS-FRT / WBS-CFG / WBS-MOB 4개 Agent의 노드명에서 `Ollama`를 `OpenAI`로 변경.
이전 LLM 엔진(Ollama)에서 전환된 실제 구현(gpt-4.1-mini)을 정확히 반영.

| 변경 전 | 변경 후 |
|---------|---------|
| `Build Ollama Request` | `Build OpenAI Request` |
| `Ollama Extract Call Flow` | `OpenAI Extract Call Flow` |
| `Ollama Extract API Calls` | `OpenAI Extract API Calls` |
| `Ollama Extract Config` | `OpenAI Extract Config` |
| `Ollama Extract Screen Flow` | `OpenAI Extract Screen Flow` |

#### WBS-GRC 섹션 보강

- `Check Rate Limit` 노드 소스코드 분석 및 80% 경고 기준 설명 추가
- `GET /repos/{owner}/{repo}/contents/` API 응답 구조 상세 추가 (필드 설명 표, WBS-GRC 활용 방식, 주의사항)

#### Agent 섹션 순서 변경

실행 흐름 기준으로 WBS-GRC를 WBS-ORK 바로 아래로 이동.

| 변경 전 순서 | 변경 후 순서 |
|------------|------------|
| TRG-001 → ORK → JRA → DDA → BAK → FRT/CFG/MOB → **GRC** → RPT | TRG-001 → ORK → **GRC** → JRA → DDA → BAK → FRT/CFG/MOB → RPT |

3. Agent 구성(13개) 표의 행 순서도 동일하게 정렬.

#### 9번 섹션 전면 교체 — Agent Output 표준 스키마 → 사용 노드 요약

| 항목 | 내용 |
|------|------|
| 전체 노드 수 | **147개** (10개 Agent + 3개 트리거/지원 워크플로) |
| 노드 타입별 현황 표 | Code(약 40) / HTTP Request(약 30) / Webhook(9) / Respond(7) / IF(7) / Merge(6) 등 |
| 타입별 상세 섹션 | Code / HTTP Request / Webhook / IF / Merge / SplitInBatches / OpenAI / Trigger 각각 상세 |

### workflow JSON Sticky Note 추가

13개 workflow JSON 파일 전체에 n8n Sticky Note 노드 추가.  
WBS-ORK, WBS-RPT, WBS-INT는 기존 Sticky Note 유지. 나머지 10개 신규 추가.

| 파일 | 주요 내용 |
|------|---------|
| WBS-TRG-001.json | 17노드 전체 처리 Job 표, Teams Bot Framework 비동기 패턴 |
| WBS-TRG-002.json | 3노드 Cron 스케줄러 역할 |
| WBS-GRC.json | 20노드 처리 Job 표, Rate Limit 80% 기준, 분류 패턴 |
| WBS-JRA.json | 13노드 처리 Job 표, 페이지네이션 루프, 한글 상태 집계 |
| WBS-DDA.json | 9노드 처리 Job 표, SplitInBatches 제거 이유, 3000자 절단 |
| WBS-BAK.json | 12노드 처리 Job 표, 파일 필터 우선순위, _meta 패턴 |
| WBS-FRT.json | 12노드 처리 Job 표, Frontend 경로/확장자 필터 |
| WBS-CFG.json | 12노드 처리 Job 표, IaC 경로/확장자 필터 |
| WBS-MOB.json | 12노드 처리 Job 표, Mobile 경로/확장자 필터 |
| WBS-ERR.json | 4노드 에러 핸들러 역할 |

### docs 업데이트

- `agents.md`: Agent 목록 순서 정렬, WBS-TRG-002/ERR 🚫 중단 표시, WBS-GRC 상세 보강, BAK/FRT/CFG/MOB 노드명·파일 필터 정확화
- `dev-log.md`: 이번 세션 변경사항 기록

---

## 2026-06-02 — 프로젝트 정리 및 GitHub 초기 커밋

### 프로젝트 폴더명 변경

- `WBSCheckAgent` → `workflow_study` 로 변경
- 메모리 폴더 이동: `.claude/projects/-Users-hosunghan-workplace-mvp-WBSCheckAgent/` → `.claude/projects/-Users-hosunghan-workplace-mvp-workflow_study/`
- 프로젝트 전체 `WBSCheckAgent` 텍스트 → `workflow_study` 일괄 치환 (docs, wiki, n8n_project-summary.md 포함)

### Prisma Cloud API 연동 정보 정리

ixi-enterprise 보안 에이전트 시스템에서 Prisma CSPM 실제 API 연동 시 필요한 정보:
- **Access Key ID + Secret Key**: Prisma Cloud 콘솔 → Settings → Access Keys에서 발급
- **API Base URL**: 콘솔 → Settings → Profile → API Endpoint (리전별 상이, 예: `api.prismacloud.io`)
- JWT 유효시간 10분 → n8n에서 자동 갱신 로직 필요

### n8n_project-summary.md Accumulate Issues 노드 상세 추가

WBS-JRA 워크플로의 `Aggregate Status` 노드 소스코드 분석 내용을 문서화:
- 이슈 상태 5개 버킷 분류 로직 (done/in_review/in_progress/todo/other)
- SP(Story Point) 소진율 및 티켓 완료율 계산 공식
- 출력 필드 전체 정리

### GitHub 초기 커밋 및 Push

- remote: `[MASKED_EMAIL]:enterprise-dev-lab/workflow_study.git`
- 브랜치: `master`
- 커밋 메시지: `ixi-Enterprise workflow 의 이해를 위한 N8N 프로젝트 개발기`
- 포함 파일: 69개 (ixi-enterprise docs, n8n workflow JSON 13개, n8n docs/wiki 전체)
- Push Protection 차단 이슈: `env-setup.md:16` TEAMS_CLIENT_SECRET 평문 노출 → `<your-client-secret>` 플레이스홀더로 교체 후 `--amend` 재커밋

### README.md 작성

프로젝트 루트에 README.md 신규 작성:
- 프로젝트 구성 트리
- WBS Check Agent 개요 및 Agent 목록 표
- 진척률 계산 공식
- ixi-enterprise 플로우 카탈로그 분석 문서 목록
- 기술 스택 및 개발 기간

---

## 2026-06-02 — 문서화 세션 (n8n 가이드 및 프로젝트 요약 작성)

### 생성/수정된 문서

| 파일 | 위치 | 내용 |
|------|------|------|
| `n8n_vs_ai_agent.md` | 프로젝트 루트 | n8n vs AI Agent 토큰 사용량 비교, 장단점, 하이브리드 전략 |
| `n8n_guide.md` | 프로젝트 루트 | n8n 완전 가이드 (배포 방식, 인증, LLM 모델, 노드 종류, MCP, Claude Code 연동) |
| `n8n_project-summary.md` | 프로젝트 루트 | WBS Agent 프로젝트 전체 요약 (Agent별 노드 상세, 이슈 목록, 환경설정) |

### n8n_vs_ai_agent.md 주요 수정

토큰 관점 정확도 검토 및 섹션별 수정:
- 2.1 실시간 이벤트 트리거: AI Agent 폴링으로 가능하나 토큰/운영 비용 추가 명시
- 2.2 400+ API 통합: 토큰 우위 → 개발·운영 비용 우위로 프레임 수정 (바이브코딩으로 직접 구현 가능)
- 2.3 장기 실행: 외부 메모리(Vector DB, Redis)로 AI Agent도 가능하나 구현 복잡도·토큰 차이 명시
- 2.6 컴플라이언스: 중앙 로그 서버로 AI Agent도 가능하나 의사결정 근거 기록 불가 명시

### n8n_guide.md 주요 내용

- 배포 방식 3가지 분류: A.오픈소스 직접 설치 / B.Railway 등 PaaS 원클릭 / C.n8n 공식 클라우드 SaaS
- AI Agent 연동 DB: SQL(PostgreSQL/MySQL 등), NoSQL(MongoDB/Redis 등), SaaS(Supabase/Airtable 등) 추가
- Tool 노드 최신화: SerpAPI Deprecated → 공식 커뮤니티 노드 대체, Think Tool 없음 정정, MCP Client Tool 2025.04 신규 명시
- 노드별 상세 사용법 및 🔴 많이 쓰는 노드 표시
- MCP Server/Client 역할 방향 정정: n8n=MCP 서버(도구 제공), AI에이전트=MCP 클라이언트(도구 호출)
- n8n-MCP 브릿지 역할 상세 설명 (없을 때 vs 있을 때 비교, 동작 구조 다이어그램)

### n8n_project-summary.md 주요 내용

- 시스템 아키텍처 전체 노드 box 형태 세로 다이어그램으로 재작성
- Agent별 노드 상세 동작: 모든 workflow JSON 직접 읽어 Input/처리기능/Output 표로 작성
- WBS-TRG-001: Teams Bot Framework raw JSON 전체 구조 추가 (Activity 전체 필드, HTTP 헤더, JWT 구조)
- Teams Bot 명령어 상태: 모두 ✅ 구현 완료로 업데이트
- WBS-TRG-002, WBS-ERR 🚫 중단 표시
- Agent 섹션 순서 재정렬: TRG-001 → ORK → JRA → DDA → BAK → FRT/CFG/MOB → GRC → RPT → TRG-002 → ERR

### workflow 폴더 정리

불필요한 임시/테스트 파일 9개 삭제:
- TEMP-Check-Fields/IssueTypes/Sprint/Jira-Setup.json (Jira API 탐색용 디버깅)
- TEST-Confluence/GitHub-PAT/Jira/Ollama.json (자격증명 검증용)
- Teams Bot - n8n Webhook.json (WBS-TRG-001 이전 초기 버전)

**정리 후 남은 파일**: WBS-BAK/CFG/DDA/ERR/FRT/GRC/INT/JRA/MOB/ORK/RPT/TRG-001/TRG-002 (13개)

---

## 2026-05-20 — Post-Phase 버그 수정 / design_score 정상화

### WBS-FRT / WBS-CFG / WBS-MOB 재작성

**문제**: import 후 실행 시 "No Respond to Webhook" 오류  
**원인**: 이전 버전 구조에 splitInBatches, 잘못된 연결 포함  
**해결**: WBS-BAK 템플릿 기반으로 재생성 (올바른 12노드 + 11연결 구조)

| Agent | Webhook Path | repo_type | LLM 노드명 | endpoint_output_key |
|-------|-------------|-----------|-----------|---------------------|
| WBS-FRT | wbs-frt | frontend | Ollama Extract API Calls | api_calls |
| WBS-CFG | wbs-cfg | config | Ollama Extract Config | config_items |
| WBS-MOB | wbs-mob | mobile | Ollama Extract Screen Flow | screens |

---

### WBS-DDA 재구현 (splitInBatches 완전 제거)

**문제 연쇄**:
1. `DESIGN_DOC_PATH` 미설정 → request body의 `path` 파라미터로 해결
2. GitHub API rate limit (인증 없음) → GitHub PAT credential 추가
3. `docs/design/` 폴더 없음 → 설계 문서 3개 생성 및 GitHub push
4. splitInBatches typeVersion 3 + 단일 아이템 → done port 즉시 이동, loop body 스킵

**최종 구조** (9노드, Loop 없음):
```
Webhook → Init Params → GET Design Doc List → Filter MD Files
→ GET File Content (첫 번째 파일만) → Build OpenAI Request
→ OpenAI Extract Structure → Parse & Build Output → Respond to Webhook
```

**생성된 설계 문서** (`hanhosunglgu/WBS_Check/docs/design/`):
- `api-design.md` — 9개 webhook endpoints, 요청/응답 스키마, Call Flow
- `db-schema.md` — n8n DB 테이블, 주간 리포트 JSON 구조, 점수 계산식
- `sequence-design.md` — 4개 시퀀스 흐름, 에러 처리 테이블

---

### design_score: 10 버그 수정

**원인 분석**:
- `api-design.md`에 `/webhook/wbs-ork` 등 9개 n8n webhook 경로가 endpoints로 추출됨
- BAK `extracted_endpoints`는 실제 앱 API (이번 주 커밋 있으나 router 파일 없어 빈 배열)
- `Build Call Flow Map`에서 9개 모두 `missing_in_actual` → Merge Design Gaps에서 9개 high severity gap
- `(10-9)/10 × 100 = 10`

**수정** (`Build Call Flow Map` 노드):
```javascript
// /webhook/ 포함 경로는 n8n 내부 경로 — 실제 코드와 비교 불가
const isWebhookPath = e => toStr(e).includes('/webhook/');
const comparableDesignEndpoints = designEndpoints.filter(e => !isWebhookPath(e));
const skipEndpointComparison = noCommitsThisWeek || comparableDesignEndpoints.length === 0;

const missingInActual = skipEndpointComparison ? [] : [...designSet].filter(e => !actualSet.has(e));
```

**n8n 캐시 갱신**:
- DB 직접 수정은 n8n 메모리에 미반영 → REST API PUT 필요
- API 키 `scopes` null 이슈 → DB에서 JSON 배열로 업데이트
- `PUT /api/v1/workflows/SC2JB9Z7HpZnbt4F` 성공 → 캐시 즉시 갱신

**결과**: `design_score: 10 (RED)` → `design_score: 100 (GREEN)`

---

### n8n REST API 패턴 확립

n8n 워크플로 코드를 변경할 때 DB 직접 수정은 효과 없음. 반드시 REST API 사용:

```bash
# 1. API 키 scopes 확인 (최초 1회)
docker exec self-hosted-ai-starter-kit-postgres-1 psql -U root -d n8n \
  -c "SELECT id, \"apiKey\", scopes FROM user_api_keys;"

# 2. 워크플로 가져오기
curl -s "http://localhost:5678/api/v1/workflows/{id}" \
  -H "X-N8N-API-KEY: {key}" > current.json

# 3. 업데이트 payload 구성 (settings는 executionOrder만)
# 4. PUT으로 업데이트
curl -X PUT "http://localhost:5678/api/v1/workflows/{id}" \
  -H "X-N8N-API-KEY: {key}" \
  -H "Content-Type: application/json" \
  -d @payload.json
```

**API 키 정보**:
- Value: `n8n_api_36b455be43bb6db0df64f3270f8e9f07be6da9de9b65d226`
- WBS-ORK Workflow ID: `SC2JB9Z7HpZnbt4F`

---

### 이슈 목록 추가

| # | 이슈 | 원인 | 해결 |
|---|------|------|------|
| 16 | WBS-FRT/CFG/MOB "No Respond to Webhook" | 이전 버전 구조 (splitInBatches 포함) | WBS-BAK 템플릿으로 재생성 |
| 17 | WBS-DDA splitInBatches loop 스킵 | typeVersion 3 + 단일 아이템 → done port 즉시 이동 | Loop 완전 제거, 첫 파일만 처리 |
| 18 | WBS-DDA GitHub API rate limit | PAT 없는 anonymous 요청 | GitHub PAT credential 추가 |
| 19 | design_score: 10 | api-design.md의 /webhook/ 경로가 endpoint로 추출 → 9개 high gap | isWebhookPath 필터로 n8n 내부 경로 비교 제외 |
| 20 | n8n DB 직접 수정 캐시 미반영 | n8n 메모리 캐시는 REST API 이벤트로만 갱신 | PUT /api/v1/workflows API 사용 |
| 21 | n8n API 키 Forbidden | scopes 컬럼 null → scopes.includes() 에러 | DB에서 scopes JSON 배열로 업데이트 |

---

## 2026-05-15 — Phase 5 완료 / E2E 최종 테스트 성공

### Task 5.5: Teams 챗봇 E2E 최종 테스트 ✅

**테스트 목표**: Teams 챗봇에서 `진척률` 명령 → WEB_Check 채널에 리포트 게시

**테스트 결과**: PASS

---

#### 이슈 12: ngrok TLS 오류 (사내 네트워크)

**증상**: `ngrok config add-authtoken` 후 `failed to send authentication request: tls: failed to verify certificate: x509: certificate signed by unknown authority`

**원인**: 사내 네트워크(LGU+) SSL DPI(Deep Packet Inspection)가 ngrok TLS 연결 차단.

**해결**: `cloudflared tunnel --url http://localhost:5678` 로 대체. 발급 URL: `https://expected-underlying-julia-constantly.trycloudflare.com`

**주의**: cloudflared 무료 터널은 세션 유지 중에만 동작. 재시작 시 URL 변경 → Azure Bot Messaging Endpoint 재등록 필요.

---

#### 이슈 13: IF 노드 `caseSensitive` 오류

**증상**: `NodeOperationError: Cannot read properties of undefined (reading 'caseSensitive')`

**원인**: WBS-TRG-001.json의 IF 노드 v2에서 `parameters.conditions.options` 위치 오류. n8n v2.14에서 `options`는 `conditions` 객체 안에 위치해야 함.

**수정**:
```json
// 수정 전
"conditions": { "conditions": [...], "combinator": "and" },
"options": { "caseSensitive": true, "typeValidation": "strict" }

// 수정 후
"conditions": { "conditions": [...], "combinator": "and", "options": { "caseSensitive": true, "typeValidation": "strict" } },
"options": {}
```

**대상**: IF 진척률 / IF 코드검증 / IF 티켓 / IF 도움말 — 4개 노드 모두 수정.

---

#### 이슈 14: HTTP Request JSON Body 파싱 오류

**증상**: `NodeOperationError: The value in the "JSON Body" field is not valid JSON` — HTTP Request - Teams 답장 노드

**원인**: `specifyBody: "json"` + `jsonBody` 템플릿에서 `replyText`에 포함된 한글, 줄바꿈(`\n`), 마크다운(`**`) 문자가 JSON 문자열을 파괴.

**해결**: `specifyBody: "keypair"` + `bodyParameters` 방식으로 변경. Expression이 JSON 문자열에 직접 삽입되지 않으므로 특수문자 안전.

```json
"specifyBody": "keypair",
"bodyParameters": {
  "parameters": [
    { "name": "type", "value": "message" },
    { "name": "text", "value": "={{ $('Merge - 응답 통합').item.json.replyText }}" }
  ]
}
```

---

#### 이슈 15: Bot Framework 15초 타임아웃으로 연결 끊김

**증상**: `진척률` 명령 후 `Incoming request ended abruptly: context canceled` — cloudflared 로그

**원인**: Microsoft Bot Framework는 Webhook 수신 후 15초 내 응답이 없으면 연결을 강제 종료. WBS-ORK 실행(5~10분) 동안 응답 대기 중 타임아웃 발생.

**해결**: WBS-TRG-001 구조 변경 — **즉시 응답 후 비동기 실행** 패턴 적용.

```
변경 전: Webhook → 파싱 → WBS-ORK 호출(10분) → Token발급 → Teams답장 → Respond
변경 후: Webhook → 파싱 → Respond(즉시 200) → IF분기 → WBS-ORK 호출(비동기, 응답 무시)
         진척률/코드검증: WEB_Check 채널로만 결과 전달
         티켓/도움말/Unknown: Token발급 → Teams 챗봇 직접 답장
```

**Merge 노드 입력 수**: 5개 → 3개 (진척률/코드검증은 답장 경로에서 제거)

---

### 최종 E2E 테스트 결과

| 단계 | 명령 | 결과 |
|------|------|------|
| Step 4 | `curl WBS-RPT` (가짜 데이터) | ✅ WEB_Check 채널 메시지 수신 |
| Step 5 | `curl WBS-ORK {}` (실제 데이터) | ✅ total_progress=4[RED], design_score=100[GREEN], teams_sent=true |
| Step 6 | Teams 챗봇 `도움말` | ✅ 챗봇 명령어 목록 답장 |
| Step 6 | Teams 챗봇 `진척률` | ✅ WEB_Check 채널 리포트 게시 확인 |

---

## 2026-05-15 — Phase 5 진행 중 (Task 5.1 / 5.2 / 5.4.1 / 5.4.3 완료)

### Task 5.1: WBS-TRG-002 Cron 스케줄러 구현

**구현 내역**: `workflow/WBS-TRG-002.json` 생성
- 3노드: Schedule Trigger(매주 금 17:00, `0 17 * * 5`) → Call WBS-ORK → Log Result
- timeout 900,000ms, `neverError:true`, errorWorkflow: WBS-ERR

**n8n 등록 시 주의**: CLI `n8n import:workflow`로 import 시 id 충돌 발생 → n8n UI에서 수동 import 필요.

---

### 이슈 9: WBS-TRG-001 활성화 오류 `Could not find property option`

**증상**: n8n에서 WBS-TRG-001 활성화 시 오류 발생, webhook `/webhook/teams-trigger` HTTP 404 반환.

**원인**: IF 노드 v2의 파라미터 스키마 변경. n8n v2.14에서 `parameters.conditions.options`는 유효하지 않으며, `parameters.options` 최상위에만 허용됨.

**수정**:
```python
for node in wf['nodes']:
    if node['type'] == 'n8n-nodes-base.if' and node.get('typeVersion') == 2:
        params = node['parameters']
        conds = params.get('conditions', {})
        if 'options' in conds:
            inner_opts = conds.pop('options')
            inner_opts.pop('leftValue', None)
            params['options'] = inner_opts
```

**n8n 반영**: `docker cp` → `n8n import:workflow` → DB에서 `workflow_entity.activeVersionId`와 `workflow_published_version.publishedVersionId` 최신 versionId로 업데이트 → docker restart.

**결과**: `Activated workflow "WBS-TRG-001"` ✅, HTTP 200 확인.

---

### 이슈 10: WBS-ORK hang (응답 없음)

**증상**: `POST /webhook/wbs-ork` 호출 후 응답 없이 300초 타임아웃.

**원인 분석**:
1. n8n 로그: `"Task request timed out after 60 seconds"` — Task Runner 60초 기본 제한 초과
2. Ollama 분석 노드 소요 시간: BAK 238초, MOB 131초, FRT 70초
3. `execution_data`에서 `"Workflow did not finish, possible out-of-memory issue"` 확인

**근본 원인**: `N8N_RUNNERS_TASK_TIMEOUT` 환경변수 미설정 → 기본값 60초 → Code 노드를 실행하는 Task Runner가 crash.

**수정**: `.env`에 `N8N_RUNNERS_TASK_TIMEOUT=900` 추가 → `docker compose up -d n8n`.

**결과**: E2E 테스트 HTTP 200, 512초 정상 완료 ✅.

---

### Task 5.4.1: E2E 테스트 완료

**테스트 명령**:
```bash
curl -s -X POST http://localhost:5678/webhook/wbs-ork \
  -H "Content-Type: application/json" -d '{}' --max-time 900
```

**결과**:
```
HTTP: 200
실행 시간: 512초
total_progress: 4 [RED]
design_score: 100 [GREEN]
teams_sent: true (status=200)
failed_agents: []
```

**판정**: PASS

---

### 이슈 11: `failed_agents` 미감지 버그

**증상**: Agent webhook 비활성화 후 WBS-ORK 호출 시 `failed_agents: []` 반환 — 실패한 Agent 미감지.

**원인**: `neverError:true` 설정으로 비활성 webhook(404)을 빈 `{}` JSON으로 수신. 기존 로직은 `error` 필드 유무만 확인하므로 `agent_id` 없는 빈 응답은 통과.

**수정**: `Integrate Results` 노드에 `isRawFailed()` 함수 추가:
```javascript
const isRawFailed = (raw) => {
  if (!raw) return true;
  if (!raw.agent_id) return true;  // 빈 {} 응답 → 실패
  if (raw.error && raw.error !== null && raw.error !== 'null') return true;
  return false;
};
```

**반영**: Python으로 WBS-ORK.json 수정 → workflow_history에 새 버전 INSERT → workflow_entity/workflow_published_version 업데이트 → n8n restart.

**단위 테스트 검증**:
- 빈 `{}` 응답 → `isRawFailed=True` → `failed_agents=['WBS-JRA']` ✅
- `None` (resultMap에 없음) → `isRawFailed=True` → 감지 ✅
- 정상 응답(`agent_id` 포함) → `isRawFailed=False` → 미감지 ✅

**테스트 환경 한계**: DB `active=false`로는 n8n 메모리 캐시 webhook 차단 불가. 실운영 환경(네트워크 오류)에서 실제 빈 응답이 발생하므로 로직 자체는 정확함.

---

## 2026-05-14 — Phase 4 완료

### Phase 4 WBS-RPT Report Agent 구현 및 Teams 메시지 전송 완료

**구현 내역**:
- `workflow/WBS-RPT.json` — 11노드 Report Agent
- Power Automate 흐름 구조 역분석으로 올바른 전송 포맷 확정

**테스트 명령**:
```bash
curl -s -X POST http://localhost:5678/webhook/wbs-rpt \
  -H "Content-Type: application/json" \
  -d '{"total_progress":73,"progress_grade":"YELLOW","design_score":87,"design_grade":"GREEN","week_start":"2026-05-11","week_end":"2026-05-14","total_tickets":12,"done_tickets":6,"in_progress_tickets":4,"todo_tickets":2,"sp_burned":24,"sp_total":40,"sp_burned_rate":60,"total_commits":23,"max_active_days":4,"gap_count":5,"high_gap_count":1,"medium_gap_count":2,"low_gap_count":2,"all_gaps":[{"severity":"high","source_agent":"WBS-MOB","item":"POST /api/auth/login"}],"incomplete_tickets":[{"key":"WBS-45","summary":"로그인 API 구현","status":"In Progress","assignee":"홍길동"}],"failed_agents":[]}'
```

**테스트 결과**:
```json
{ "agent_id": "WBS-RPT", "teams_sent": true, "teams_status": 200, "teams_error": null, "confluence_skipped": true }
```

**판정**: PASS — Teams WBS 모니터링 채널에 Adaptive Card 메시지 수신 확인.

---

### 이슈 6: Teams 메시지 미수신 (teams_status:200인데 채널 비어있음)

**증상**: WBS-RPT가 `teams_status: 200` 반환하나 Teams 채널에 메시지 없음.

**원인**: Power Automate Webhook은 항상 200을 반환하지만, 내부 흐름 실행은 별도로 실패 가능. Power Automate 실행 이력에서 실제 오류 확인 필요.

**확인 방법**: make.powerautomate.com → 내 흐름 → "WBS 모니터링에 웹후크 경고 보내기" → 28일 실행 기록

---

### 이슈 7: `Property 'type' must be 'AdaptiveCard'`

**증상**: Power Automate 오류: `Property 'type' must be 'AdaptiveCard'`

**원인**: `{ type: 'message', attachments: [...] }` 형식으로 전송 → Power Automate `Post card in a chat or channel` 액션이 이 형식을 Adaptive Card로 인식 못함.

**해결**: Power Automate 흐름 내부 구조를 역분석:
- `Initialize variable (Body)` = `triggerBody()` 전체
- `Initialize variable (Attachments)` = `{}` 초기화
- `Attachments is null` 조건 → False 분기 → `For each(Attachments)` → `@item()?['content']` 로 카드 게시

따라서 웹훅 body에 `attachments` 배열이 있어야 하며, 각 항목은 `contentType` + `content` 필드 필요:
```json
{
  "attachments": [{
    "contentType": "application/vnd.microsoft.card.adaptive",
    "content": { "type": "AdaptiveCard", ... }
  }]
}
```

---

### 이슈 8: `unsupported card element` (BadRequest 400)

**증상**: 올바른 포맷으로 전송했으나 `Payload is incorrect: unsupported card element` 오류.

**원인**: Adaptive Card에 Teams가 지원하지 않는 요소 사용:
- `Table`, `TableRow`, `TableCell` — Teams 미지원
- `ColumnSet`, `Column` — Teams 환경에 따라 미지원

**해결**: 카드 요소를 `TextBlock` + `FactSet`만 사용하도록 단순화. Adaptive Card 버전도 `1.4` → `1.0`으로 낮춤.

**확정 패턴**:
```javascript
const card = {
  type: 'AdaptiveCard',
  version: '1.0',         // 최소 버전으로 최대 호환
  body: [
    { type: 'TextBlock', ... },  // 텍스트
    { type: 'FactSet', facts: [...] },  // key-value 목록
    // Table/ColumnSet 절대 사용 금지
  ]
};
```

---

## 2026-05-14 — Phase 3 완료

### Phase 3 WBS-ORK Orchestration Agent 구현 및 테스트 완료

**구현 내역**:
- `workflow/WBS-ORK.json` — 25노드 Orchestration Agent
- 트리거 3종: Webhook(`wbs-ork`), Schedule(`0 17 * * 5`), Manual Trigger
- 6개 Agent 병렬 호출 → Merge(numberInputs:6) → 통합 분석 → 진척률 계산

**테스트 명령**:
```bash
curl -X POST http://localhost:5678/webhook/wbs-ork \
  -H "Content-Type: application/json" \
  -d '{}' \
  --max-time 1800
```

**1차 테스트 결과** (WBS-DDA/CFG/MOB 미활성화 상태):
```json
{ "failed_agents": ["WBS-DDA","WBS-CFG","WBS-MOB"], "total_progress": 4, "design_score": 70 }
```

**2차 테스트 결과** (전체 활성화 후):
```json
{ "failed_agents": ["WBS-DDA"], "total_progress": 4, "design_score": 70, "progress_grade": "RED", "design_grade": "YELLOW" }
```

**판정**: PASS — WBS-DDA timeout은 Ollama 환경 이슈(Phase 1부터 알려진 문제), WBS-ORK 로직 정상.

---

### 이슈 4: WBS-ORK Webhook 404 오류

**증상**: `POST http://localhost:5678/webhook/wbs-ork` → 404 `"The requested webhook "wbs-ork" is not registered for POST requests"`

**원인**: Webhook 노드에 `httpMethod` 파라미터 누락 — n8n은 기본값이 GET이므로 POST 등록이 안 됨.

**해결**: Webhook 노드에 아래 3개 파라미터 추가:
```json
{ "httpMethod": "POST", "responseMode": "responseNode", "typeVersion": 2 }
```

---

### 이슈 5: failed_agents 3개 (WBS-DDA/CFG/MOB)

**증상**: 1차 테스트에서 `failed_agents: ["WBS-DDA","WBS-CFG","WBS-MOB"]`

**원인**: WBS-DDA, WBS-CFG, WBS-MOB 워크플로가 n8n에서 비활성화 상태 — Webhook 호출 시 404 반환, `neverError:true`로 인해 워크플로는 멈추지 않고 error 필드에 기록됨.

**해결**: n8n UI에서 3개 워크플로 수동 활성화.

---

### 아키텍처 결정: Orchestration 패턴

WBS-ORK는 Specialist Agent를 **HTTP Webhook 호출** 방식으로 조율한다 (Execute Workflow 노드 아님).

**이유**:
1. 각 Agent가 독립 배포 가능한 단위로 유지됨
2. 네트워크 timeout 독립 설정 가능 (DDA는 600초, JRA는 300초)
3. 실패 Agent를 `neverError:true`로 격리, 나머지 계속 실행 가능

**부분 실패 처리 패턴**:
```javascript
const resultMap = {};
for (const item of items) {
  resultMap[item.json.agent_id] = item.json;
}
const jra = resultMap['WBS-JRA'] || { ...defaultJraValues };
```

---

## 2026-05-13 — Phase 1 완료

### Phase 1 통합 테스트 완료 (Task 1.7)

WBS-INT 단일 통합 워크플로(57노드) 기준 6/6 ALL_PASS.

**테스트 명령**:
```bash
curl -X POST http://localhost:5678/webhook/wbs-int \
  -H "Content-Type: application/json" \
  -d '{"owner":"hanhosunglgu","repos":["WBS_Check"],"dda_repo":"hanhosunglgu/WBS_Check","dda_path":"docs/design"}' \
  --max-time 1800
```

**결과**:
- WBS-GRC: classified=1 (WBS_Check → frontend/Vite)
- WBS-DDA: endpoints=5, tables=2, sequences=2
- WBS-BAK: backend 분석 완료 (commits=8)
- WBS-FRT: frontend 분석 완료 (commits=8)
- WBS-CFG: config 분석 완료 (commits=8)
- WBS-MOB: screen_flow=1, api_calls=1, design_gaps=2

---

### 이슈 1: WBS-INT 노드 참조 이름 충돌

**증상**: `Cannot assign to read only property 'name' of object 'Error: Referenced node doesn't exist'` — BAK Build Ollama Request 노드에서 발생.

**원인**: 6개 Agent를 하나의 워크플로로 합칠 때 모든 노드명에 agent prefix를 추가했으나, Code 노드 내부의 `$('nodeName')` 참조는 수정하지 않음.

**수정 목록** (총 9개):
| 노드 | 변경 전 | 변경 후 |
|------|---------|---------|
| BAK/FRT/CFG/MOB Build Ollama Request | `$('Extract Commit Info')` | `$('XXX Extract Commit Info')` |
| BAK/FRT/CFG/MOB Parse & Build Output | `$('Build Ollama Request')` | `$('XXX Build Ollama Request')` |
| GRC Attach Repo Info | `$('Filter & Split Repos')` | `$('GRC Filter & Split Repos')` |

**패턴 확립**: 통합 워크플로 작성 시 모든 `$('nodeName')` 참조를 agent prefix 기준으로 사전 검증 필수.

---

### 이슈 2: WBS-INT Webhook Timeout

**증상**: HTTP 200 응답이지만 body가 비어 있음 (0.04s에 응답).

**원인**: `N8N_WEBHOOK_TIMEOUT=300`으로 설정된 상태에서 6개 Ollama 호출을 순차 실행하면 총 실행시간이 7~8분으로 timeout 초과.

**해결**: `.env`에서 `N8N_WEBHOOK_TIMEOUT=300` → `N8N_WEBHOOK_TIMEOUT=900`으로 변경 후 n8n 재시작.

---

### 이슈 3: WBS-DDA Ollama JSON Body 오류

**증상**: Ollama 호출 후 빈 응답 또는 parse 실패.

**원인**: Ollama HTTP Request 노드의 `jsonBody`가 `JSON.stringify($json)` 형태로 `_meta` 필드와 기타 필드를 모두 포함 → Ollama가 NDJSON streaming 반환.

**해결**:
```
변경 전: "jsonBody": "={{ JSON.stringify($json) }}"
변경 후: "jsonBody": "={{ JSON.stringify({ model: $json.model, prompt: $json.prompt, stream: $json.stream }) }}"
```
또한 `neverError: true` 추가하여 Ollama 오류 시 워크플로 중단 방지.

---

### WBS-MOB 테스트 파일 추가

테스트를 위해 GitHub repo `hanhosunglgu/WBS_Check`에 Flutter 테스트 파일 추가:
- `lib/screens/login_screen.dart` — Flutter 화면 파일, WBS-MOB 파일 필터 패턴 검증용

---

## 2026-05-13 (오전) — Task 0.3.1 / 0.3.2

### n8n Variables 값 확정

**확정된 값**:

| Key | Value |
|-----|-------|
| `GITHUB_OWNER` | `hanhosunglgu` |
| `GITHUB_REPOS` | `["WBS_Check"]` |
| `JIRA_BASE_URL` | `https://lgucorp.atlassian.net` |
| `JIRA_PROJECT_KEYS` | `["WBS"]` |
| `JIRA_BOARD_ID` | `8207` |
| `DESIGN_DOC_REPO` | `hanhosunglgu/WBS_Check` |
| `DESIGN_DOC_PATH` | `WBS_Check/docs/design` |

**결정 사항**:
- `JIRA_BOARD_ID=8207` — Jira URL(`/boards/8207`)에서 추출. Task 2.1.2 Sprint 조회 시 필요.
- `DESIGN_DOC_PATH=WBS_Check/docs/design` — Repo 이름이 경로 앞에 포함된 형태로 확정.

**다음 액션**: n8n UI(Settings → Variables)에 7개 변수 직접 입력 필요.

---

## 2026-05-11 — Phase 0 초기 설정

### Task 0.1 — 기존 Workflow 파악

- n8n에 `Teams Bot - n8n Webhook` Workflow 1개 존재 및 활성화 중 확인.
- 기존 Workflow가 Teams Webhook 수신, OAuth2 Token 발급, Teams 답장까지 구현되어 있어 신규 생성 없이 확장 방식으로 결정.

### Task 0.2 — 보안 이관

- 기존 Workflow JSON에 `client_id`, `client_secret`, `tenant_id`가 평문으로 하드코딩되어 있었음.
- `$env.TEAMS_TENANT_ID`, `$env.TEAMS_CLIENT_ID`, `$env.TEAMS_CLIENT_SECRET` 참조로 교체 완료.

### Task 0.2 — API 키 확보

- GitHub PAT (`repo`, `read:org` 권한) 발급 및 n8n Credential 등록 완료.
- Jira API Token 발급 및 등록 완료.
- Ollama `qwen2.5-coder:7b` 로컬 Docker 실행, n8n에서 `http://ollama:11434/api/generate` 호출 확인.

### Task 0.3.3 — Output 스키마 정의

- `doc/schema/agent-output-schema.json` 생성. 모든 Specialist Agent가 동일한 스키마로 결과 반환하도록 표준화.

---

## 주요 아키텍처 결정

### 기존 Workflow 재활용 전략

신규 WBS-TRG-001 Workflow를 새로 만들지 않고 기존 `Teams Bot - n8n Webhook`을 확장한다.

**이유**: 기존 Workflow에 Teams Webhook 수신, OAuth2 Token 발급, 답장 전송이 이미 구현되어 있어 재작성 비용 대비 효과 없음.

**방식**: 기존 Set 노드(메시지 파싱) 뒤에 Code 노드(명령어 파싱)와 Switch 노드(분기)를 삽입.

### WBS-INT 통합 전략 — HTTP 체인 vs 인라인 병합

초기에는 WBS-INT가 각 Agent의 Webhook을 순차로 HTTP 호출하는 체인 방식으로 설계했으나, 6개 순차 실행 시 총 시간이 외부 Webhook timeout을 초과.

**해결**: 6개 Agent 노드를 하나의 워크플로에 직접 인라인 — HTTP 오버헤드 제거, 단일 timeout 설정으로 관리.

**WBS-INT 구성**: 57개 처리 노드 + 8개 Sticky Note = 65개 총 노드. 노드명 전체에 agent prefix 적용 (예: `BAK Extract Commit Info`).

### Specialist Agent 병렬 실행

WBS-ORK에서 WBS-JRA, WBS-DDA, WBS-BAK, WBS-FRT, WBS-CFG, WBS-MOB를 병렬로 Execute Workflow 노드로 호출.

**이유**: 각 Agent가 독립적인 데이터 소스(Jira, GitHub)에서 데이터를 수집하므로 순차 실행 불필요.

### Ollama LLM 역할 분리

- **Specialist Agent (WBS-BAK/FRT/CFG/MOB/DDA)**: 소스코드/설계 문서 → Call Flow 추출, `design_gaps[]` 1차 생성
- **Orchestration Agent (WBS-ORK)**: 전체 Gap 통합 → 의도 분석 (개선/실수/누락), 심각도 분류 (High/Medium/Low)

**이유**: 각 Agent가 자신의 도메인 코드만 분석하고, 최종 의도 판단은 전체 컨텍스트를 가진 Orchestrator에서 수행.

### DDA 파라미터 설계

WBS-DDA는 다른 Specialist Agent와 달리 `repos[]` 배열 대신 `{ repo, path }` 파라미터를 사용한다.

**이유**: 설계 문서는 특정 Repo의 특정 경로에 고정되어 있어 Repo 분류(WBS-GRC) 결과를 기다릴 필요 없이 직접 경로를 지정하는 것이 단순.

**WBS-INT에서의 처리**: `dda_repo`와 `dda_path`를 입력 파라미터로 별도 수신.

---

## 2026-05-19 — OpenAI 전환 완료 및 WBS-DDA/RPT 재구현

### 배경

이전 세션(2026-05-19 오전)에서 Ollama → OpenAI gpt-4.1-mini 전환 작업 중 WBS-DDA가 "No Respond to Webhook node found" 오류로 미해결 상태였음. 이번 세션에서 근본 원인 파악 및 완전 해결.

---

### WBS-DDA 재구현

#### 문제 1: SplitInBatches typeVersion 3 + executionOrder v1 충돌

**증상**: Loop Over Files가 입력 아이템이 있어도 즉시 done 포트(port 1)로 빠짐 → GET File Content, Store File Content가 한 번도 실행 안 됨.

**원인**: n8n 2.14.2에서 SplitInBatches v3와 `executionOrder: v1` 설정이 충돌. 루프 진입 없이 종료.

**해결**: `typeVersion: 3 → 2`, `settings.executionOrder` 제거.

#### 문제 2: Loop done 포트에서 `$('NodeName').all()` 미실행 오류

**증상**: `Build Ollama Request` 노드에서 `$('Decode Base64').all()` 호출 시 `Cannot assign to read only property 'name' of object 'Error: Node 'Decode Base64' hasn't been executed'`.

**원인**: n8n은 Loop done 포트 진입 시점에 루프 내부 노드를 "미실행" 상태로 간주. `$('NodeName').all()` 참조 불가.

**해결**: 루프 내에 `Store File Content` 노드를 두어 결과를 누적 저장 → done 포트에서 `$('Store File Content').all()` 참조.

#### 문제 3: GitHub API base64 디코딩 불필요

**개선**: contents API URL 대신 `download_url` (raw 텍스트 직접 fetch) 사용 → base64 decode 노드 제거, 워크플로 단순화.

#### 문제 4: n8n Community Edition Variables 미지원

**증상**: `$vars.OPENAI_API_KEY` → undefined.

**원인**: n8n 2.14.2 Community Edition은 Variables 기능 미지원 (Enterprise 전용).

**해결**: n8n 내장 `@n8n/n8n-nodes-langchain.openAi` 노드 + "OpenAI account" Credential 사용.

#### 최종 WBS-DDA 노드 구조 (8노드)

```
Webhook → Init Params → GET Design Doc List → Filter MD Files
  → Loop Over Files (typeVersion: 2)
      port0 → GET File Content (download_url) → Store File Content → Loop Over Files
      port1 → Build OpenAI Request → OpenAI Extract Structure → Parse & Build Output → Respond to Webhook
```

**테스트 결과**: endpoints=5, tables=2, sequences=2 정상 추출 ✅

---

### WBS-RPT 수정

#### 수정 내용
- `$env` → `$vars` 일괄 변경 (Community Edition에서 $vars도 미지원이므로 하드코딩으로 최종 처리)
- `TEAMS_WEBHOOK_URL` 워크플로 JSON에 직접 하드코딩
- Confluence 관련 노드 4개 완전 제거 (Get/Parse/Build/Update Confluence Page) — 조직 정책으로 API Token 차단
- `Send Teams Message` retry 옵션 제거 (30초×3회 블로킹 방지)
- `executionOrder: v1` 제거

#### 최종 WBS-RPT 노드 구조 (7노드 + Sticky Note)

```
Webhook → Build Report Data → Build Teams Card → Send Teams Message
  → Check Teams Result → Build Final Summary → Respond to Webhook
```

**테스트 결과**: teams_sent=true, Teams 채널 메시지 수신 ✅

---

### E2E 전체 파이프라인 테스트

**실행 명령**:
```bash
curl -X POST http://localhost:5678/webhook/wbs-ork \
  -H "Content-Type: application/json" \
  -d '{"triggered_by":"e2e_test"}' \
  --max-time 900
```

**결과**:
| 항목 | 값 |
|------|-----|
| agent_id | WBS-RPT |
| total_progress | 0% (RED) |
| design_score | 56% (RED) |
| teams_sent | true |
| teams_status | 200 |
| error | null |
| Teams 메시지 | 수신 확인 ✅ |

---

### 발견된 n8n 패턴 (추가)

| # | 패턴 | 내용 |
|---|------|------|
| 7 | SplitInBatches 버전 | 반드시 typeVersion: 2 사용. v3는 executionOrder v1과 충돌 |
| 8 | Loop done 포트 참조 | 루프 내 노드는 done 포트에서 `$()` 참조 불가. Store 노드로 누적 후 참조 |
| 9 | OpenAI 호출 | 내장 OpenAI 노드 + Credential 방식 사용. HTTP Request 직접 호출 시 API Key 주입 불가 (Community Edition) |
| 10 | Variables 대체 | Community Edition: $vars 미지원. URL/키는 JSON 하드코딩 또는 Webhook body 주입 |

---

## 2026-05-19 — Teams Bot 진척률 명령 실동작 검증

### WBS-TRG-001 Teams Bot 엔드투엔드 검증

**실행 흐름**:
```
Teams 채널 → Bot ("진척률") → WBS-TRG-001 수신
  → Set 메시지 파싱 ($json.body.text)
  → Code 명령어 파싱 (keyword === '진척률' → command = '진척률')
  → IF 진척률 (true 분기)
  → Respond to Webhook 즉시 200 응답
  → Fire WBS-ORK (진척률) — 비동기 호출
    → WBS-ORK 전체 파이프라인 실행
    → WBS-RPT → Teams 채널 리포트 전송
```

**확인 사항**:
- `Set - 메시지 파싱` 노드: `$json.body.text` 에서 메시지 추출 (curl 테스트 시 `body.text` 형태로 전송 필요)
- 비동기 패턴: Respond to Webhook 즉시 응답 후 WBS-ORK 백그라운드 실행 → Bot 15초 타임아웃 우회
- Teams 채널 리포트 수신 확인 ✅

**테스트 결과**: WBS-TRG-001 SUCCESS, WBS-ORK SUCCESS, Teams 채널 리포트 도착 ✅

### curl 테스트 방법 (WBS-TRG-001)

```bash
curl -X POST http://localhost:5678/webhook/teams-trigger \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "text": "진척률",
      "from": {"id": "user-id", "name": "홍길동"},
      "conversation": {"id": "conv-id"},
      "serviceUrl": "https://smba.trafficmanager.net/kr/",
      "id": "activity-id"
    }
  }'
```

> `body.text` 필드 필수. `conversation.id` 없으면 Teams 답장 URL 조립 실패 (Teams 실동작에서는 자동 제공됨).
