# IVMS 연동 워크플로우 — ixi-enterprise 생성 가이드

**작성일**: 2026-07-09
**목적**: `09-ivms-ixi-integration-requirements-spec.md`에서 정의한 요구사항을, `04-ixi-enterprise-node-catalog.md`의 노드 명세대로 ixi-enterprise 캔버스에 실제로 만드는 절차 문서
**대상 독자**: ixi-enterprise 캔버스에서 이 워크플로우를 직접 구성할 개발자
**참조 문서**: `09-ivms-ixi-integration-requirements-spec.md`(요구사항), `04-ixi-enterprise-node-catalog.md`(노드 명세), `08-ivms_openapi_spec.md`(IVMS API 규격)

---

## 0. 전체 구성 개요

09번 문서는 두 개의 독립된 플로우를 정의한다. 각각 별도의 ixi-enterprise 플로우(캔버스)로 생성한다.

| 플로우 번호 | 대응 절 | 플로우명(제안) | 대상 사용자 |
|---|---|---|---|
| **플로우 A** | 09번 문서 2~7절 | `IVMS 미조치 압박 및 조치가이드 생성` | 보안담당자 |
| **플로우 B** | 09번 문서 8절 | `IVMS 담당자 조치 확인 E2E` | 서버 개발 담당자 |

두 플로우는 IVMS API Request Tool 설정을 공유하지만, ixi-enterprise에는 Sub-flow 기능이 없으므로(`07-ixi-enterprise-requirements-spec.md` REQ-008) 각 플로우 내부에 API Request Tool을 개별로 배치해야 한다.

공통으로 준비할 사항은 3번 섹션에서 먼저 다룬다.

---

## 1. 사전 준비 (두 플로우 공통)

### 1.1 Model 선택 기준

모든 Agent / Language Model / AI Router 노드에서 `Model *` 드롭다운은 동일하게 `azure_openai:gpt-4.1-mini`를 기본으로 사용한다(05번 문서에서 검증된 8개 플로우 전부가 이 모델을 사용). Tool 호출 스텝이 많은 Agent(플로우 A의 Agent #1)만 필요 시 `azure_openai:gpt-4.1`로 상향 검토한다.

### 1.2 API Request Tool 사전 정보 정리

두 플로우에서 총 4개의 IVMS API를 Tool로 등록해야 한다. 캔버스에 배치하기 전에 아래 값을 미리 확정해둔다(08번 문서 기준).

| API | Method | URL 패턴 | Tool Mode |
|---|---|---|---|
| `orgList` | GET | `{IVMS_BASE_URL}/ivms/api/orgList` | ON |
| `asstChrgInfo` | GET | `{IVMS_BASE_URL}/ivms/api/asstChrgInfo` | ON |
| `mngtListDetail` | POST | `{IVMS_BASE_URL}/ivms/api/mngtListDetail` | ON |
| `guidelineCdInfo` | GET | `{IVMS_BASE_URL}/ivms/api/guidelineCdInfo` | ON |
| `dgnsRslt` | GET | `{IVMS_BASE_URL}/ivms/api/dgnsRslt` | ON |

`{IVMS_BASE_URL}`은 실제 운영 환경의 IVMS 서버 주소로 치환한다. 모든 API Request Tool은 **Tool Mode ON** 상태로 배치한다(Agent의 Tools 포트에 연결해야 하므로 일반 모드가 아닌 Tool 모드 사용, 04번 문서 "API Request" 항목 참조).

### 1.3 인증/헤더 확인

08번 문서에 인증 헤더(API Key, Bearer Token 등)가 명시되어 있다면 API Request Tool의 `Header` 팝업(기어 아이콘)에 `Header Key`/`Header Value`로 등록한다. 이 문서에서는 08번 문서를 별도 참조하도록 안내만 하며, 구체적인 키 값은 캔버스 구성 시점에 확인한다.

---

## 2. 플로우 A 구성 — IVMS 미조치 압박 및 조치가이드 생성

09번 문서 3절 다이어그램을 그대로 ixi-enterprise 노드로 옮긴다.

### 2.1 캔버스에 노드 배치하기 (순서대로)

1. **Chat Input** 노드를 캔버스에 드래그한다. 파라미터 설정 없음(플로우 시작 노드).
2. **Agent** 노드 1개를 배치한다 — 이름을 `Agent #1: IVMS 데이터 수집`으로 변경(라벨 편집).
3. **API Request** 노드 4개를 Tool Mode ON으로 배치한다:
   - `API Request Tool: orgList`
   - `API Request Tool: asstChrgInfo`
   - `API Request Tool: mngtListDetail`
   - `API Request Tool: guidelineCdInfo`
4. **Agent** 노드 1개를 추가 배치한다 — `Agent #2: 담당자별 압박메시지+조치가이드 생성`.
5. **Human Approval** 노드 1개를 배치한다.
6. **Language Model** 노드 1개를 배치한다(Human Approval 경유용 패스스루).
7. **Chat Output** 노드 1개를 배치한다.

### 2.2 노드 연결 (Edge 연결)

| 순서 | From (출력 포트) | To (입력 포트) | 비고 |
|---|---|---|---|
| 1 | Chat Input → `User Message` | Agent #1 → `Input` | 파란 점선 |
| 2 | API Request Tool(`orgList`) → `Tool` | Agent #1 → `Tools` | 빨간, Tools는 다중 연결 가능 |
| 3 | API Request Tool(`asstChrgInfo`) → `Tool` | Agent #1 → `Tools` | 동일 포트에 추가 연결 |
| 4 | API Request Tool(`mngtListDetail`) → `Tool` | Agent #1 → `Tools` | 동일 포트에 추가 연결 |
| 5 | API Request Tool(`guidelineCdInfo`) → `Tool` | Agent #1 → `Tools` | 동일 포트에 추가 연결 |
| 6 | Agent #1 → `Response` | Agent #2 → `Input` | 파란 점선 |
| 7 | Agent #2 → `Response` | Human Approval → `Target Message` | 파란, 필수 포트 |
| 8 | Human Approval → `Human Approval` | Language Model → `Input` | ⚠️ Human Approval 출력은 Chat Output에 직접 연결 불가(04번 문서 674행 제약) → 반드시 Language Model 경유 |
| 9 | Language Model → `Response` | Chat Output → `Input` | **Chat Output 쪽에서 드래그해 연결 시작할 것** — Language Model Response 포트에서 드래그하면 Chat Output이 목록에 안 뜸(04번 문서 151행 주의사항) |

### 2.3 노드별 파라미터 입력값

**Agent #1: IVMS 데이터 수집**
- `Tools`: 위 4단계에서 연결한 API Request Tool 4개
- `System Prompt Template`:
  ```
  조직명을 입력받아 다음 순서로 IVMS API를 호출한다.
  1. orgList로 조직명 → orgId 확인
  2. asstChrgInfo로 orgId 기준 담당자 목록(chrgId, chrgNm, chrgTypeCd) 조회
  3. mngtListDetail로 담당자별(rspnMngId) 자산 중 SECURITY_SCORE neq 100(미조치) 필터링
  4. guidelineCdInfo로 각 미조치 항목의 조치방법(measure) 조회
  수집한 원시 데이터를 담당자별로 구분해 그대로 다음 단계에 전달한다.
  ```
- `Jailbreak Check`: OFF (내부 API 연동 전용, 05번 문서 워크플로우 4 패턴과 동일)
- `Model`: `azure_openai:gpt-4.1-mini` (Tool 호출 스텝이 4단계로 많다면 `azure_openai:gpt-4.1` 상향 검토)

**Agent #2: 담당자별 압박메시지+조치가이드 생성**
- `Tools`: 연결 없음
- `System Prompt Template`:
  ```
  심각도(severity)와 경과일(7일 이상)을 기준으로 미조치 항목을 선별한다.
  담당자가 N명이면 N개 섹션으로 구분해 각 섹션에
  (1) 압박 메시지, (2) 조치가이드 요약을 생성한다.
  guidelineCdInfo 응답에는 요청과 무관한 다른 가이드라인 항목이
  섞여 들어올 수 있으므로, 실제 미조치 대상 항목(guidelineCd 일치)만
  선별해 사용한다.
  ```
- `Jailbreak Check`: OFF
- `Model`: `azure_openai:gpt-4.1-mini`

**Human Approval**
- `Target Message`: Agent #2 Response 연결(위 표 7행)
- `question`: 기본값 유지 또는 `"N명분 압박메시지+조치가이드를 승인하시겠습니까?"`로 변경
- `Model`: `azure_openai:gpt-4.1-mini`

**Language Model (승인 후 패스스루)**
- `Input`: Human Approval Human Approval 포트 연결(위 표 8행)
- `System Prompt Template`: 비워두거나 `"입력된 승인 결과를 그대로 출력한다."` 정도만 지정 — 별도 가공 없이 통과시키는 역할
- `Model`: `azure_openai:gpt-4.1-mini`

### 2.4 완성된 구조도

```
[Chat Input]
     │ User Message
     ▼
[Agent #1] ←Tools← [API Req: orgList][API Req: asstChrgInfo]
     │              [API Req: mngtListDetail][API Req: guidelineCdInfo]
     │ Response
     ▼
[Agent #2]
     │ Response
     ▼
[Human Approval]
     │ Human Approval
     ▼
[Language Model]  (패스스루)
     │ Response
     ▼
[Chat Output]
```

---

## 3. 플로우 B 구성 — 담당자 조치 확인 E2E

09번 문서 8절의 1~4단계를 **하나의 캔버스**에 순차 배치하되, 담당자가 챗봇을 여러 차례 다른 목적으로 호출하는 구조이므로 **Chat Input에서 AI Router로 먼저 분기**시켜 4개 하위 시나리오(1단계 조회 / 2단계 가이드요청 / 3-A 오류분석 / 4단계 배치재확인)를 한 플로우 안에서 처리하도록 구성한다.

> 09번 문서는 단계별로 별도 Chat Input을 가정해 서술했지만("[Chat Input] User Message: ...”가 8.3~8.6에 각각 등장), 실제 ixi-enterprise는 **플로우 1개당 Chat Input 1개**만 시작점으로 둘 수 있다(Template Message는 INPUT 컴포넌트로 인식되지 않으므로 04번 문서 106행 제약). 따라서 담당자가 매번 다른 요청을 같은 챗봇 창에 입력하는 실제 사용 방식에 맞춰, **AI Router로 요청 유형을 분류한 뒤 4개 경로로 라우팅**하는 단일 플로우로 통합 구성한다.

### 3.1 캔버스에 노드 배치하기 (순서대로)

1. **Chat Input** 노드 1개.
2. **AI Router** 노드 1개 — 요청 유형 분류용.
3. **경로 1(1단계: 미조치 항목 확인)**: Agent 노드 1개 (`Agent #1: 담당자 조회`) + API Request Tool 2개(`asstChrgInfo`, `mngtListDetail`, Tool Mode ON)
4. **경로 2(2단계: 조치가이드 요청)**: Agent 노드 1개 (`Agent #2: 조치가이드 조회`) + API Request Tool 1개(`guidelineCdInfo`, Tool Mode ON)
5. **경로 3(3-A: 실행 오류 분석)**: Agent 노드 1개 (`Agent #3: 실행오류 분석`) + API Request Tool 1개(`guidelineCdInfo` 재사용 — 별도 인스턴스로 배치)
6. **경로 4(4단계: 배치 후 재확인)**: Agent 노드 1개 (`Agent #4: 배치시점 판별`) + API Request Tool 1개(`dgnsRslt`, Tool Mode ON) → **AI Router** 노드 1개(2차 분기) → **Language Model** 노드 1개(대기 안내) / **Agent** 노드 1개(`Agent #5: 실패원인 재분석`) + API Request Tool 1개(`guidelineCdInfo` 재사용)
7. **Chat Output** 노드 1개 (모든 경로가 최종적으로 여기로 수렴)

### 3.2 1차 AI Router 설정 (요청 유형 분류)

- `Input`: Chat Input User Message 연결
- `Edit Conditions` 팝업에서 조건 3개 추가:
  | Condition Name | Condition Description |
  |---|---|
  | `내_미조치_확인` | 담당자 본인의 미조치 취약점 목록을 확인하려는 요청 |
  | `조치가이드_요청` | 특정 취약점 항목의 조치 방법(명령어)을 알고 싶은 요청 |
  | `배치_재확인` | 조치를 완료했고 IVMS에 반영됐는지 확인하려는 요청 |
- `else 조건 기본 AI 메시지 사용`: ON — 위 3개 조건에 해당하지 않으면 (예: 실행 오류 로그를 붙여넣는 경우) else로 분류되어 경로 3(3-A)로 보낸다.
- `Model`: `azure_openai:gpt-4.1-mini`

출력 포트는 `내_미조치_확인` / `조치가이드_요청` / `배치_재확인` / `else` 4개가 생성된다. 각각 아래 경로로 연결한다.

| AI Router 출력 포트 | 연결 대상 |
|---|---|
| `내_미조치_확인` | 경로 1: Agent #1 |
| `조치가이드_요청` | 경로 2: Agent #2 |
| `배치_재확인` | 경로 4: Agent #4 |
| `else` | 경로 3: Agent #3 (실행 오류/트러블슈팅 요청은 정형화된 키워드가 없어 else로 수렴) |

### 3.3 경로 1 — 담당자 본인 미조치 항목 확인 (09번 문서 8.3절)

```
[AI Router: 내_미조치_확인] → [Agent #1] ← Tools ← [API Req: asstChrgInfo][API Req: mngtListDetail]
                                    │ Response
                                    ▼
                              [Chat Output]
```

**Agent #1: 담당자 조회**
- `Tools`: `asstChrgInfo`, `mngtListDetail` API Request Tool 연결
- `System Prompt Template`:
  ```
  사용자 메시지에서 담당자 이름(또는 사번)을 추출한다.
  asstChrgInfo로 chrgId를 확인한 뒤, mngtListDetail로 해당 chrgId 기준
  자산 목록 중 SECURITY_SCORE neq 100(미조치) 항목만 필터링해
  자산별로 정리해 제시한다.
  ```
- `Model`: `azure_openai:gpt-4.1-mini`

### 3.4 경로 2 — 특정 항목 조치가이드 요청 (09번 문서 8.4절)

```
[AI Router: 조치가이드_요청] → [Agent #2] ← Tools ← [API Req: guidelineCdInfo]
                                    │ Response
                                    ▼
                              [Chat Output]
```

**Agent #2: 조치가이드 조회**
- `Tools`: `guidelineCdInfo` API Request Tool 연결
- `System Prompt Template`:
  ```
  사용자가 요청한 guidelineCd(취약점 항목 코드)로 guidelineCdInfo를 호출한다.
  응답에는 요청과 무관한 다른 가이드라인 항목이 섞여 있을 수 있으므로,
  요청한 guidelineCd와 정확히 일치하는 항목만 선별해 사용한다.
  조치기준(criteria), 현황(analysisInfo), 조치방법(measure) 원문을
  가공하지 않고 그대로 제시한다.
  ```
- `Model`: `azure_openai:gpt-4.1-mini`

### 3.5 경로 3 — 실행 오류 분석 (09번 문서 8.5.1절, else 경로)

```
[AI Router: else] → [Agent #3] ← Tools ← [API Req: guidelineCdInfo (재조회용 별도 인스턴스)]
                          │ Response
                          ▼
                    [Chat Output]
```

**Agent #3: 실행오류 분석**
- `Tools`: `guidelineCdInfo` API Request Tool 연결(경로 2와 별개 인스턴스로 배치 — ixi-enterprise는 Sub-flow/Tool 재사용 기능이 없으므로 캔버스에 물리적으로 다시 배치해야 함)
- `System Prompt Template`:
  ```
  사용자가 제공한 에러 로그와, guidelineCdInfo로 재조회한 원래
  조치가이드 원문을 비교해 실패 원인(권한 부족/문법 오류/OS 버전 차이 등)을
  분석하고 대안 명령어를 제시한다.
  ```
- `Model`: `azure_openai:gpt-4.1-mini`

> 이 경로는 대화 메모리가 없으므로(09번 문서 8.1절 제약), 담당자가 재시도 후 또 실패하면 같은 메시지창에 **이전 시도 내역까지 포함해** 다시 입력해야 한다. Agent #3 System Prompt에 이 제약을 사용자 안내 문구로 추가하는 것도 고려할 수 있다(예: "다음 시도에도 실패하면 이번 대안 내용과 새 에러 로그를 함께 붙여넣어 주세요"라는 문장을 응답 끝에 포함하도록 지시).

### 3.6 경로 4 — 배치 후 재확인 (09번 문서 8.6절, 2차 AI Router 포함)

```
[AI Router: 배치_재확인] → [Agent #4] ← Tools ← [API Req: dgnsRslt]
                                 │ Response (PENDING_BATCH | STILL_FAILING)
                                 ▼
                          [AI Router #2]
                          ├─[PENDING_BATCH] → [Language Model] ──┐
                          └─[else/STILL_FAILING] → [Agent #5] ←Tools← [API Req: guidelineCdInfo] ─┐
                                                                                                     ▼
                                                                                              [Chat Output]
```

**Agent #4: 배치시점 판별**
- `Tools`: `dgnsRslt` API Request Tool 연결
- `System Prompt Template`:
  ```
  사용자가 제시한 조치 완료 시각과, dgnsRslt로 조회한 해당 자산의
  가장 최근 진단 종료 시각(timeEnd)을 비교한다.
  조치 완료 시각이 timeEnd보다 이후면 "PENDING_BATCH",
  조치 완료 시각이 timeEnd보다 이전인데도(즉 배치가 이미 돌았는데도)
  여전히 FAIL이면 "STILL_FAILING" — 이 두 키워드 중 하나로만 응답한다.
  ```
- `Model`: `azure_openai:gpt-4.1-mini`

**AI Router #2 (2차 분기)**
- `Input`: Agent #4 Response 연결
- `Edit Conditions`: 조건 1개 추가
  | Condition Name | Condition Description |
  |---|---|
  | `PENDING_BATCH` | 응답이 정확히 PENDING_BATCH인 경우 |
- `else 조건 기본 AI 메시지 사용`: ON — else가 곧 STILL_FAILING 케이스
- `Model`: `azure_openai:gpt-4.1-mini`

**Language Model (PENDING_BATCH 경로)**
- `Input`: AI Router #2 `PENDING_BATCH` 포트 연결
- `System Prompt Template`:
  ```
  다음 정기 배치(매주 새벽)가 지난 뒤 다시 확인해달라고 안내하고
  예상 반영 시점을 안내한다.
  ```
- `Model`: `azure_openai:gpt-4.1-mini`
- `Response` → Chat Output 연결 (⚠️ Chat Output 쪽에서 드래그해 연결 시작)

**Agent #5: 실패원인 재분석 (STILL_FAILING 경로)**
- `Tools`: `guidelineCdInfo` API Request Tool 연결(경로 2, 3과 별개 인스턴스)
- `System Prompt Template`:
  ```
  배치 반영 이후에도 FAIL이 유지되는 상황이다.
  사용자가 제공한 실행 로그와, guidelineCdInfo로 재조회한 원래
  조치가이드를 비교해 실패 원인을 분석하고 대안을 제시한다.
  ```
- `Model`: `azure_openai:gpt-4.1-mini`
- `Response` → Chat Output 연결

> ⚠️ **AI Router else → Chat Output 직접 연결 불가** (04번 문서 680행 제약). AI Router #2의 `else` 포트는 Agent #5로 연결하고, Agent #5의 `Response`를 Chat Output에 연결하는 방식으로 이미 이 제약을 준수하고 있다. `PENDING_BATCH` 조건 포트(else가 아닌 정식 조건 포트)에서 Language Model로 연결하는 것도 동일하게 문제 없다.

### 3.7 Chat Output 통합

경로 1·2·3·4(두 하위 경로 포함) 총 5개의 최종 응답 노드(Agent #1, Agent #2, Agent #3, Language Model, Agent #5)가 모두 **하나의 Chat Output 노드**에 연결된다. Chat Output의 `Input` 포트는 다중 연결을 허용하므로(어느 경로가 실행되든 그 경로의 응답만 출력) 별도 병합 로직 없이 5개 노드 모두를 동일한 Chat Output에 연결하면 된다.

### 3.8 전체 캔버스 구조도

```
[Chat Input]
     │
     ▼
[AI Router #1] ── 내_미조치_확인 ──→ [Agent #1] ←Tools← [asstChrgInfo][mngtListDetail]
     │                                    │
     ├── 조치가이드_요청 ──→ [Agent #2] ←Tools← [guidelineCdInfo]
     │                                    │
     ├── 배치_재확인 ──→ [Agent #4] ←Tools← [dgnsRslt]
     │                        │
     │                        ▼
     │                  [AI Router #2]
     │                  ├─ PENDING_BATCH → [Language Model]
     │                  └─ else ──→ [Agent #5] ←Tools← [guidelineCdInfo]
     │
     └── else ──→ [Agent #3] ←Tools← [guidelineCdInfo]
                        │
                        │
   (Agent#1 / Agent#2 / Agent#3 / Language Model / Agent#5 Response 전부)
                        ▼
                  [Chat Output]
```

---

## 4. 구성 시 주의할 공통 제약 (04번 문서 근거)

| 제약 | 근거 | 이 워크플로우에 미치는 영향 |
|---|---|---|
| Chat Input은 플로우당 1개만 시작점 가능, Template Message는 INPUT 미인식 | 04번 문서 106행 | 플로우 B를 8절처럼 4개 별도 진입점으로 나누지 않고 AI Router 분기 1개 플로우로 통합한 이유 |
| Human Approval 출력 → Chat Output 직접 연결 불가 | 04번 문서 679행 | 플로우 A에서 Language Model 패스스루 노드 필수 |
| Language Model Response → Chat Output 연결 시 Chat Output 쪽에서 드래그해야 함 | 04번 문서 151행, 686행 | 플로우 A 8단계, 플로우 B의 Language Model(PENDING_BATCH) 연결 시 동일하게 적용 |
| AI Router else → Chat Output 직접 연결 불가 | 04번 문서 680행 | 플로우 B의 AI Router #2 else 포트를 Agent #5로 경유시킨 이유 |
| ixi-enterprise에 Sub-flow 기능 없음 | `07-ixi-enterprise-requirements-spec.md` REQ-008 | `guidelineCdInfo` API Request Tool을 경로 2/3/5에서 각각 별도 인스턴스로 3번 배치해야 함(재사용 불가) |
| Agent 노드에 대화 메모리(Memory) 파라미터 없음 | 04번 문서 155~168행(Agent 파라미터 전체) | 플로우 B의 경로 3(실행오류 반복)에서 담당자가 매번 이전 시도 내역을 직접 붙여넣어야 함(09번 문서 8.1절 제약과 동일) |
| API Request는 Tool Mode ON일 때만 Agent Tools 포트에 연결 가능 | 04번 문서 415~442행 | 모든 IVMS API Request 노드는 반드시 Tool Mode ON으로 배치 |

---

## 5. 구성 후 확인 체크리스트

- [ ] 플로우 A: Chat Input → Agent #1(Tools 4개) → Agent #2 → Human Approval → Language Model → Chat Output 연결 완료
- [ ] 플로우 B: Chat Input → AI Router #1(조건 3개 + else) 분기 완료, 4개 경로 각각 독립된 API Request Tool 인스턴스 연결 완료
- [ ] 플로우 B: AI Router #2(PENDING_BATCH 조건 1개 + else) → Language Model / Agent #5 분기 완료
- [ ] 모든 Chat Output 직결 노드가 Chat Output 쪽에서 드래그해 연결됐는지 확인(반대 방향 드래그 시 목록에 안 뜨는 노드 있음)
- [ ] `guidelineCdInfo`를 호출하는 모든 Agent(플로우 B의 Agent #2/#3/#5)의 System Prompt에 "guidelineCd 정확히 일치하는 항목만 선별" 방어 지시 포함 여부
- [ ] 각 API Request Tool의 URL이 `08-ivms_openapi_spec.md` 기준 실제 엔드포인트와 일치하는지, 인증 헤더가 등록됐는지 확인
- [ ] 플로우 A의 Human Approval `question` 문구, 플로우 B의 AI Router 조건 설명 문구가 실제 담당자/보안담당자 입력 패턴과 잘 맞는지 시범 실행으로 검증
