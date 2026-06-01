# ixi-enterprise vs n8n 비교 분석 레포트

**작성일**: 2026-05-21  
**분석 기준 프로젝트**: WBS Check Agent (n8n 구현체)  
**분석 대상**: ixi-enterprise AI Flow 플랫폼  
**목적**: n8n 대비 ixi-enterprise의 개선점 및 향후 개발 방향성 도출  
**인터뷰**: 2026-05-21 실시 (실행 히스토리, Multi-Agent, 예외처리, 오류 피드백 등 확인)

---

## 1. 프로젝트 개요

### n8n 구현 프로젝트 — WBS Check Agent

팀 리더/PM이 개발팀의 주간 진척률을 자동 모니터링하는 Multi-Agent 시스템.  
Jira + GitHub + 설계 문서(.md)를 통합 분석해 매주 금 17:00 Teams에 리포트를 전송한다.

| 항목 | 내용 |
|------|------|
| Workflow 수 | 13개 (Trigger 2, Error 1, Specialist Agent 8, Orchestrator 1, Report 1) |
| 핵심 패턴 | Multi-Agent Orchestration — 6개 Specialist Agent 병렬 실행 + 결과 수렴 |
| 외부 연동 | Jira Cloud API, GitHub REST API, Microsoft Teams Bot, Ollama(LLM), OpenAI |
| 트리거 | Cron(매주 금 17:00), Teams Webhook, Manual |
| 에러처리 | Error Trigger Workflow(WBS-ERR), neverError, retry, 부분 실패 허용 패턴 |

### ixi-enterprise

시각적 AI Flow Builder 플랫폼. 노드를 캔버스에 배치·연결해 LLM 기반 플로우를 구성한다.

| 항목 | 내용 |
|------|------|
| 노드 수 | 21종 (I/O 4, AI/LLM 4, Tools 5, RAG 2, Human-in-the-Loop 2, Guardrail 2) |
| 지원 LLM | Azure OpenAI (gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-4o) |
| 주요 강점 | AI-First 노드 (Guardrail, Human Approval, AI Router, KMS Retriever) |
| 실제 활용 범위 | 단순 채팅 기반 AI (RAG, 요약, Guardrail 적용 플로우) |

---

## 2. 종합 비교

| 관점 | n8n | ixi-enterprise | 비고 |
|------|-----|----------------|------|
| 플랫폼 성격 | 범용 자동화 워크플로 | AI 특화 Flow Builder | ixi는 AI 플로우에 집중 |
| 타겟 사용자 | 개발자/기술자 | 비개발자 포함 | ixi는 낮은 진입 장벽 목표 |
| Multi-Agent | 병렬 Sub-workflow 호출 + Merge | 단일 플로우 내 직렬 체이닝만 가능 | n8n이 압도적 우위 |
| 외부 연동 | 400+ 내장 인티그레이션 | API Request + MCP | n8n이 훨씬 풍부 |
| 디버깅 | 실행 히스토리 + Pin Data + 노드별 인스펙션 | 채팅 출력 문자열만 확인 가능 | n8n이 구조적 우위 |
| 예외처리 | Error Trigger, neverError, retry, 조건 분기 | 없음 — 오류 시 플로우 즉시 중단 | n8n이 구조적 우위 |
| Cron 스케줄러 | 워크플로 내부에 Schedule Trigger 노드로 내장 | 별도 스케줄 관리 화면에서 플로우 ID 지정 연결. 간편 설정(빈도+시간 드롭다운) + 고급 설정(Cron 표현식) 모두 지원 | 기능 동등, 관리 방식 차이 |
| 코드 실행 | Code 노드 (JS/Python) | 없음 | n8n 우위 |
| Guardrail | HTTP 요청으로 직접 구현 | 전용 노드 내장 | ixi 우위 |
| Human-in-the-Loop | Wait + Form Trigger 수동 조합 | 전용 노드 내장 | ixi 우위 |
| RAG | Qdrant + Embeddings 수동 구성 | KMS Retriever + Document Formatter | ixi 우위 |
| AI Router | Agent + Switch 노드 수동 조합 | 전용 노드 내장 | ixi 우위 |

**결론**: ixi-enterprise는 "채팅 기반 단순 AI 플로우" 영역에서 UX 우위를 가지지만, 자동화·오케스트레이션·디버깅·예외처리 측면에서 n8n 대비 대규모 격차가 있다.

---

## 3. 노드 비교: n8n 기준 ixi-enterprise 부재 노드

### 3-1. WBS Check Agent에서 사용한 n8n 노드 목록

| 노드명 | 카테고리 | WBS에서의 역할 | ixi-enterprise 대응 |
|--------|----------|---------------|---------------------|
| `scheduleTrigger` | Trigger | 매주 금 17:00 자동 실행 | ✅ 스케줄 관리 화면에서 Cron 표현식으로 동일하게 설정 가능 (`0 17 * * 5`) |
| `webhookTrigger` | Trigger | Teams Bot 메시지 수신, Agent 진입점 | ❌ 없음 (Chat Input만 존재) |
| `errorTrigger` | Trigger | 전역 오류 발생 시 Teams 에러 알림 | ❌ 없음 |
| `manualTrigger` | Trigger | 개발/테스트 수동 실행 | ❌ 없음 |
| `executeWorkflow` | Orchestration | Sub-workflow 호출 (병렬 Agent 실행) | ❌ 없음 |
| `merge` | Orchestration | 병렬 Agent 결과 수렴 (6개 입력) | ❌ 없음 |
| `splitInBatches` | Loop | GitHub 파일 목록 순회, Jira 페이지네이션 | ❌ 없음 |
| `code` | Logic | JS로 진척률 계산, Call Flow 비교, 데이터 파싱 | ❌ 없음 |
| `switch` | Logic | 4개 명령어 분기 (진척률/코드검증/티켓/도움말) | △ AI Router로 부분 대체 (LLM 비용 발생) |
| `if` | Logic | 조건 분기 (명령어 유형별, 데이터 유형별) | △ AI Router로 부분 대체 |
| `filter` | Logic | GitHub API 응답에서 .md 파일만 추출 | ❌ 없음 |
| `set` | Logic | 변수 초기화, 데이터 매핑 | ❌ 없음 |
| `httpRequest` | Action | GitHub/Jira/Ollama/Teams API 호출 | △ API Request 노드 (단순 버전) |
| `respondToWebhook` | Response | Webhook 즉시 응답 반환 | ❌ 없음 |
| `stickyNote` | UX | 워크플로 문서화 | ❌ 없음 |

---

### 3-2. 부재 노드별 영향 — WBS 프로젝트 예시

#### (A) Trigger 계층 부재

**Webhook Trigger 없음**

n8n에서 WBS-TRG-001은 Teams Bot 메시지를 직접 수신해 명령어를 파싱한다.

```
[Webhook: POST /webhook/teams-trigger]
  → HTML 태그 제거 + 명령어 파싱
  → Switch: 진척률 / 코드검증 / 티켓 / 도움말 / Unknown
```

ixi-enterprise의 Chat Input은 채팅 UI 안에서만 동작하며, 외부 시스템(Teams Bot, GitHub Webhook, Slack 등)이 직접 플로우를 호출하는 것이 불가능하다.

**Error Trigger 없음**

n8n에서 WBS-ERR은 어느 워크플로에서든 오류가 발생하면 자동으로 Teams에 알림을 전송한다.

```json
// WBS-ERR: Error Trigger → Build Error Message → Get Token → Send Error to Teams
{
  "워크플로": "WBS-ORK",
  "마지막 노드": "Integrate Results",
  "오류": "Cannot read properties of undefined",
  "실행 로그": "https://n8n.internal/executions/12345"
}
```

ixi-enterprise에는 전역 에러 핸들러 개념이 없다. 오류 발생 시 사용자에게 채팅 출력으로 에러 문구가 표시되는 것이 전부이며, 관리자에게 자동 알림이 가지 않는다.

---

#### (B) 오케스트레이션 계층 부재

**Execute Workflow + Merge 없음**

WBS-ORK는 6개 Specialist Agent를 병렬로 호출하고, 전체 결과를 Merge 노드로 수렴한다.

```
WBS-ORK
  ├── [HTTP → WBS-JRA]  Jira 티켓 분석
  ├── [HTTP → WBS-DDA]  설계 문서 파싱      ← 병렬 실행
  ├── [HTTP → WBS-BAK]  Backend 코드 분석
  ├── [HTTP → WBS-FRT]  Frontend 코드 분석
  ├── [HTTP → WBS-CFG]  Config/IaC 분석
  └── [HTTP → WBS-MOB]  Mobile 코드 분석
        ↓
  [Merge: numberInputs=6]  ← 전체 결과 수렴
        ↓
  [Code: Call Flow 재구성 + 진척률 계산]
```

인터뷰 확인 결과, ixi-enterprise에서 Multi-Agent는 "단일 플로우 내 Agent 노드를 직렬 체이닝"만 가능하다. 병렬 실행, Sub-flow 호출, 결과 수렴 개념 자체가 없다.

WBS 수준의 Multi-Agent 오케스트레이션은 ixi-enterprise로 구현 불가능하다.

**SplitInBatches (Loop) 없음**

WBS-JRA에서 Jira Sprint 이슈 전체를 페이지네이션으로 가져오는 로직:

```
[HTTP: GET Sprint Issues (page 1)]
  → [SplitInBatches + hasMore 조건]  ← 루프
      → [HTTP: GET Sprint Issues (page 2, 3, ...)]
  → [Aggregate: 전체 이슈 배열 수집]
```

ixi-enterprise의 API Request 노드는 단일 HTTP 호출만 가능하다. 수백 건의 이슈가 있어도 첫 번째 페이지만 처리할 수 있다.

---

#### (C) 로직 계층 부재

**Code 노드 없음**

WBS-ORK의 핵심 비즈니스 로직은 JS Code 노드에 있다.

```javascript
// 진척률 계산 (가중 합산)
const jiraScore = (done / total) * 100 * 0.40;     // Jira 40%
const spScore = (spBurned / spTotal) * 100 * 0.40; // Story Point 40%
const commitScore = (activeDays / 5) * 100 * 0.20; // Commit 20%
const totalProgress = Math.round(jiraScore + spScore + commitScore);

// 설계 적합성 계산
const missingInActual = designEndpoints.filter(e => !actualSet.has(e));
const designScore = Math.round((total - missing) / total * 100);
```

ixi-enterprise에는 이런 결정론적 계산을 수행할 노드가 없다. LLM에 "진척률을 계산해줘"라고 프롬프트를 넣으면 매번 다른 수치가 나올 수 있다. 진척률처럼 정확성이 요구되는 계산에는 LLM이 적합하지 않다.

**Switch/IF 노드 — AI Router로의 불완전 대체**

WBS-TRG-001의 명령어 분기는 문자열 완전 일치(`진척률`, `코드검증`, `티켓`, `도움말`)를 기준으로 한다.

```
[Switch: command]
  "진척률"   → WBS-ORK 호출
  "코드검증"  → WBS-ORK 호출 (repo 지정)
  "티켓"     → Jira 단일 이슈 조회
  "도움말"   → 명령어 목록 응답
  else       → 도움말 안내
```

ixi-enterprise의 AI Router는 LLM이 의미를 판단해서 라우팅한다. 이는 두 가지 문제를 발생시킨다.

1. **비용**: 단순 문자열 비교에 매번 LLM 호출 비용이 발생한다.
2. **비결정성**: "진척률 알려줘"와 "progress report" 중 어느 경로로 라우팅될지 보장할 수 없다.

---

## 4. 디버깅 방법 비교

### 4-1. n8n의 디버깅 체계

n8n은 개발 과정에서 다음 디버깅 수단을 제공한다.

| 기능 | 설명 | WBS 활용 예시 |
|------|------|--------------|
| **실행 히스토리** | 모든 실행을 타임스탬프·상태·노드별 입출력과 함께 저장 | 이슈 #10: execution_data에서 `"Task request timed out after 60 seconds"` 확인 → N8N_RUNNERS_TASK_TIMEOUT 원인 특정 |
| **노드별 데이터 인스펙션** | 각 노드 클릭 시 실제 JSON 데이터 확인 | WBS-BAK 개발 중 GitHub API 응답 구조를 노드 클릭으로 즉시 확인 |
| **Pin Data (입력 고정)** | 특정 노드 입력을 고정값으로 설정해 해당 노드부터 재실행 | Ollama 응답을 핀으로 고정 후 파싱 로직만 반복 테스트 |
| **Manual Trigger** | Chat Input 없이 워크플로를 직접 수동 실행 | 각 Specialist Agent를 개별 단위 테스트 |
| **neverError + 빈 데이터 추적** | 에러 억제 후 빈 응답을 히스토리에서 추적 | 이슈 #11: neverError=true 상태에서 빈 `{}` 응답이 어느 Agent에서 왔는지 히스토리로 확인 |
| **Sticky Note** | 캔버스에 메모 노드 배치 (문서화) | WBS-INT(65노드) 구간 설명 |
| **REST API 직접 수정** | `PUT /api/v1/workflows/{id}`로 코드 레벨 수정 후 캐시 즉시 갱신 | 이슈 #20: DB 직접 수정은 메모리 캐시 미반영 → REST API로 해결 |
| **curl 단위 테스트** | 각 Webhook URL을 curl로 직접 호출해 개별 검증 | WBS-ORK, WBS-RPT 등 각 Agent를 독립 검증 |

#### n8n 디버깅의 핵심 원칙: 결정론적 재현

n8n은 "이전 실행 데이터를 현재 노드에 주입"하는 방식으로 동작한다. 동일 입력 → 동일 출력이 보장되므로 문제를 재현하고 수정을 검증하는 사이클이 명확하다.

```
오류 발생
  → 실행 히스토리에서 실패 노드·입력 데이터 확인
  → Pin Data로 해당 입력 고정
  → 해당 노드만 재실행
  → 수정 검증 완료
```

---

### 4-2. ixi-enterprise의 디버깅 현황 및 부재 항목

**인터뷰 확인 결과**: 실행 히스토리 없음. 오류 발생 시 채팅 출력에 마크다운 에러 문구가 표시되는 것이 전부.

| n8n 기능 | ixi-enterprise 현황 | 문제점 |
|----------|---------------------|--------|
| **실행 히스토리** | ❌ 없음 | 오류 발생 시 어느 노드에서 실패했는지 추적 불가 |
| **노드별 데이터 인스펙션** | ❌ 없음 | 중간 노드에서 데이터가 올바르게 전달됐는지 확인 방법 없음 |
| **Pin Data (입력 고정)** | ❌ 없음 | 특정 노드부터 재실행 불가. 매번 Chat Input에서 처음부터 실행해야 함 |
| **Manual Trigger** | ❌ 없음 | Chat Input 없이 플로우를 개발 목적으로 실행할 수 없음 |
| **오류 위치 표시** | △ 채팅 출력에 에러 문구만 표시 | 어느 노드에서 발생했는지 캔버스에서 시각적으로 확인 불가 |
| **curl / API 단위 테스트** | ❌ 없음 | 플로우를 외부에서 독립 호출해 테스트할 방법 없음 |

#### 실제 사례: Structured Output → Document Formatter 오류

ixi-enterprise에서 Document Formatter에 Structured Output을 연결하면 `'str' object has no attribute 'page_content'` 오류가 발생한다. 문제는 **UI에서 연결 자체는 허용된다**는 점이다.

- n8n이라면: Pin Data로 Structured Output 출력을 고정 → Document Formatter만 재실행 → 즉시 재현·수정
- ixi-enterprise에서는: 매번 Chat Input에서 플로우 전체를 처음부터 실행해야 오류를 재현할 수 있음

이처럼 "UI에서 연결이 되지만 런타임에서 실패하는" 유형의 버그는 디버깅 도구가 없으면 원인 파악에 과도한 시간이 소요된다.

---

## 5. 예외처리 방법 비교

### 5-1. n8n의 예외처리 체계

n8n은 세 레이어로 예외처리를 구성한다.

```
레이어 1 — 전역: Error Trigger Workflow
  └─ 모든 워크플로 오류 → WBS-ERR → Teams 자동 알림

레이어 2 — 워크플로: neverError + 부분 실패 허용
  └─ 개별 노드 실패 → 빈 데이터로 계속 진행
  └─ 실패 Agent → 기본값으로 대체 후 리포트 계속 생성

레이어 3 — 노드: retry + timeout
  └─ 일시적 네트워크 오류 → 자동 재시도
  └─ 장시간 실행 → 타임아웃 격리
```

| 방법 | 설명 | WBS 활용 예시 |
|------|------|--------------|
| **Error Trigger (전역)** | 어느 워크플로에서든 오류 시 Error Workflow 자동 실행 | WBS-ERR: 워크플로명·노드명·에러 메시지·실행 URL을 Teams에 자동 전송 |
| **neverError:true (에러 억제)** | HTTP 오류를 예외로 처리하지 않고 빈 데이터로 계속 진행 | Agent webhook 비활성(404) 시에도 WBS-ORK 전체 실행 유지 |
| **retry** | HTTP 요청 실패 시 자동 재시도 | WBS-ERR Teams 알림: `maxTries:2, waitBetweenTries:10000ms` |
| **isRawFailed() 패턴** | `agent_id` 부재로 빈 응답({})을 실패로 감지 | 이슈 #11: neverError=true 상태에서 빈 응답이 정상 응답과 혼동되는 문제 해결 |
| **부분 실패 허용** | `resultMap[agentId] \|\| defaultValues`로 실패 Agent를 기본값으로 대체 | 6개 Agent 중 WBS-DDA 실패 시에도 나머지 5개 결과로 리포트 생성 |
| **노드별 timeout** | 노드별 독립 타임아웃 설정 | WBS-DDA: 600초, WBS-JRA: 300초 (처리 시간 차이 반영) |
| **비동기 실행** | 즉시 Respond 후 백그라운드 실행 | Teams Bot 15초 제한 우회: 200 즉시 반환 → WBS-ORK 비동기 실행 |
| **IF 노드 에러 분기** | HTTP 응답 코드·에러 필드를 조건으로 실패 경로 분기 | WBS-ORK: 성공/실패 Agent별 처리 경로 분리 |

---

### 5-2. ixi-enterprise의 예외처리 현황 및 부재 항목

**인터뷰 확인 결과**: 예외처리 방법 없음. 오류 발생 시 플로우가 그냥 중단됨.

| n8n 기능 | ixi-enterprise 현황 | 문제점 |
|----------|---------------------|--------|
| **Error Trigger (전역 핸들러)** | ❌ 없음 | LLM 호출 실패, API 오류 시 사용자에게 아무 피드백 없이 플로우 종료 |
| **neverError (에러 억제)** | ❌ 없음 | 외부 API 1개 실패 시 전체 플로우 중단 |
| **retry (자동 재시도)** | ❌ 없음 | 일시적 네트워크 오류에도 재시도 없이 즉시 실패 |
| **부분 실패 허용** | ❌ 없음 | 노드 하나 실패 시 그 이후 모든 노드 실행 중단 |
| **timeout 설정** | △ MCP Connection Tool만 일부 지원 (기본 5000ms) | LLM 호출이 수십 초 걸릴 때 중간에 끊기거나 무한 대기 |
| **에러 분기 라우팅** | ❌ 없음 | 오류 발생 경로와 정상 경로를 구분하는 노드 없음 |
| **비동기 실행** | ❌ 없음 | 장시간 처리 시 응답 대기 강제 (타임아웃 위험) |

#### 실제 사례: PLL Guardrail 인증 실패

ixi-enterprise에서 PLL Guardrail은 Azure Language Service API Key 미등록 시 `401 Access denied`로 플로우 전체가 중단된다.

- n8n이라면: `neverError:true` + IF 노드로 "인증 실패 시 Guardrail 우회" 경로를 구성
- ixi-enterprise에서는: 플로우 중단. 사용자 채팅 출력에 에러 문구 표시

더 심각한 문제는 ixi 자체 문서에도 다음과 같이 기록되어 있다는 점이다.

> "❓ 미확인: 필터 통과 실패 시 플로우 중단 vs 에러 메시지 분기 동작 방식 스펙 확인 필요."

자체 플랫폼에서 Guardrail 실패 시 어떤 동작이 일어나는지 스펙이 정의되지 않았다. 이는 예외처리 설계가 플랫폼 레벨에서 체계적으로 수립되지 않았음을 방증한다.

---

## 6. 개선 방향성 및 우선순위

인터뷰 결과, 현재 ixi-enterprise는 "단순 채팅 기반 AI(RAG, 요약)" 수준에서 활용되고 있으며, WBS 수준의 자동화를 구현하면 Cron + Multi-Agent + Code 로직이 모두 진입 장벽이 된다는 것이 확인됐다.

### P1 — 디버깅 기반 구축 (가장 시급)

현재 채팅 출력으로만 결과를 확인할 수 있어 개발 생산성이 매우 낮다.

| 개선 항목 | 설명 |
|-----------|------|
| **실행 히스토리** | 플로우 실행 이력을 노드별 입출력 데이터와 함께 기록·조회 |
| **노드별 데이터 인스펙션** | 실행 후 캔버스에서 각 노드 클릭 시 실제 JSON 확인 |
| **부분 재실행 (Pin Data 상당)** | 중간 노드 입력을 고정하고 해당 노드부터 재실행 |
| **오류 노드 시각화** | 실패한 노드를 캔버스에서 빨간색 등으로 하이라이트 |

### P2 — 예외처리 체계 수립

오류 발생 시 플로우가 그냥 중단되는 현재 구조는 프로덕션 운영에 부적합하다.

| 개선 항목 | 설명 |
|-----------|------|
| **Error Handler 연결** | 각 플로우에 에러 발생 시 실행될 핸들러 플로우를 지정 |
| **노드별 에러 억제 옵션** | 오류 발생 시 빈 데이터로 계속 진행하는 neverError 상당 기능 |
| **retry 설정** | HTTP/API 노드에 재시도 횟수·대기 시간 설정 |
| **에러 출력 포트** | 성공 포트 외 별도 에러 포트를 통한 실패 경로 라우팅 |
| **Guardrail 실패 스펙 명문화** | 필터 실패 시 중단 vs 분기 동작을 명확히 정의하고 구현 |

### P3 — 오케스트레이션 노드 추가

단순 채팅 AI를 넘어서 자동화 시스템을 구축하려면 아래 노드가 필수다.

| 추가 노드 | 설명 | WBS 대응 |
|----------|------|---------|
| **Webhook Trigger** | 외부 시스템 이벤트 수신 | Teams Bot, GitHub Webhook 수신 |
| **Sub-Flow Call** | 다른 플로우를 호출·조합 | 6개 Specialist Agent 병렬 호출 |
| **Loop / SplitInBatches** | 배열 데이터 순회 처리 | Jira 이슈 페이지네이션 |
| **Merge** | 복수 브랜치 결과 수렴 | 6개 Agent 결과 통합 |

### P4 — 로직 노드 추가

| 추가 노드 | 설명 |
|----------|------|
| **Code 노드 (JS/Python)** | 결정론적 계산, 데이터 변환, 커스텀 파싱 |
| **Filter 노드** | 배열에서 조건을 만족하는 항목만 추출 |
| **Set / Variable 노드** | 플로우 내 변수 선언 및 조작 |
| **조건 분기 (IF/Switch)** | LLM 비용 없는 규칙 기반 분기 |

---

## 7. 요약

| 영역 | 현황 | 핵심 격차 |
|------|------|----------|
| **디버깅** | 채팅 출력 문자열만 확인 가능 | 실행 히스토리, 노드별 인스펙션, 부분 재실행 전무 |
| **예외처리** | 오류 시 플로우 즉시 중단 | Error Handler, retry, neverError, 에러 분기 전무 |
| **오케스트레이션** | 단일 플로우 내 직렬 체이닝만 가능 | Webhook Trigger, Sub-Flow, Loop, Merge 전무 |
| **로직 처리** | LLM에 의존 | 결정론적 Code 실행, Filter, Variable 노드 전무 |
| **ixi 강점** | Guardrail, Human-in-the-Loop, RAG, AI Router | 이 영역은 n8n 대비 UX 우위 유지 |

ixi-enterprise는 "AI 노드를 쉽게 연결하는 UX"에서 강점을 보이지만, 실제 엔터프라이즈 자동화 시스템을 구축하기 위해서는 디버깅 체계·예외처리·오케스트레이션 레이어가 반드시 보완되어야 한다.

---

*인터뷰 기반 확인 항목: 실행 히스토리(없음), Multi-Agent 구현 방법(직렬 체이닝만 가능), 오류 피드백(채팅 출력 문자열), 예외처리 방법(없음/플로우 중단), 주 활용 범위(단순 채팅 AI)*
