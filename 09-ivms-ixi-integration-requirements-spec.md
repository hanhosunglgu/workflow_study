# IVMS 연동 미조치 압박 및 AI 조치가이드 생성 플로우 — 요구명세서

**작성일**: 2026-07-09
**작성자**: 보안담당자 인터뷰 기반 (Claude 작성)
**참조 문서**: `08-ivms_openapi_spec.md`(IVMS OpenAPI 규격), `04-ixi-enterprise-node-catalog.md`(노드 카탈로그), `05-ixi-enterprise-flow_analysis.md`(구현 플로우 분석), `07-ixi-enterprise-requirements-spec.md`(ixi-enterprise 플랫폼 자체 개선 요구사항 — 본 문서와는 별개 문서)

---

## 1. 배경 및 목적

IVMS(인프라 취약점 통합 관리 시스템)는 사내 서버를 스캔하여 취약점/보안 점수를 관리하는 시스템으로, OpenAPI를 통해 자산·담당자·진단결과·조치가이드 데이터를 조회할 수 있다. 각 내부 서비스는 개발 담당자가 배정되어 있으나, 담당자가 IVMS 대시보드를 직접 들여다보지 않는 이상 자신의 미조치 취약점 현황을 인지하기 어렵다.

보안담당자는 이를 개선하기 위해 ixi-enterprise 워크플로우로 다음 두 가지를 자동화하고자 한다.

1. **압박(Pressure)**: 담당자별 미조치 취약점 현황을 정리해 조치를 독려하는 메시지 생성
2. **AI 조치가이드**: 각 미조치 항목에 대해 AI가 IVMS의 조치방법(가이드라인) 데이터를 바탕으로 실행 가능한 조치 방안을 분석·요약

인터뷰 결과, 두 요구사항은 **하나의 챗봇 트리거 플로우**로 통합 가능하며, 별도의 스케줄링/알림 인프라 없이 기존 ixi-enterprise 노드만으로 구현 가능한 것으로 확인되었다.

---

## 2. 인터뷰를 통해 확정된 요구사항

| 항목 | 확정 내용 |
|---|---|
| 트리거 방식 | 보안담당자가 챗봇에 **직접 요청**(수동). 스케줄/Cron 트리거 아님 |
| 출력 채널 | **채팅 응답으로만** 확인. Slack/이메일 등 자동 발송 없음. 필요 시 보안담당자가 결과를 복사해 수동 전달 |
| 미조치 판단 기준 | **심각도(severity) + 경과일**의 조합. 경과일 기준은 **단일 값**(예: 전체 항목 공통 7일)으로 적용 — 심각도별 차등 SLA 아님 |
| 분석 대상 범위 | 특정 담당자의 **전체 미조치 항목을 일괄 분석**(단일 자산/단일 항목 단위 아님, 조직 전체 요약도 아님) |
| 대상 지정 방법 | 보안담당자가 **조직명(org 명)**으로 지정 → 해당 조직의 담당자 목록을 시스템이 자동 조회 |
| 출력 단위 | **담당자별 개별** 압박 메시지 + 조치가이드 생성 (조직 전체를 하나로 뭉친 요약 아님) — 조직에 담당자가 N명이면 N개의 결과물 생성 |
| 승인 절차 | **Human Approval 필요**. 단, N명분의 결과물을 **하나로 통합해 1회 승인**(담당자별 개별 승인 아님) |

---

## 3. 전체 플로우 구조

기존 구현 플로우 중 **Workflow 4(2-2, 사내 시스템 연동 Agent)**와 **Workflow 7(4-2, Human Approval 승인 플로우)**의 패턴을 결합하여 구성한다.

```
[Chat Input]
  User Message: "OO팀 미조치 현황 압박 및 조치가이드 생성해줘"
     │
     ▼
[Agent #1: IVMS 데이터 수집 Agent]
  Tools ↓
  ├─ [API Request Tool] GET /ivms/api/orgList
  │     → 조직명으로 orgId 확인
  ├─ [API Request Tool] GET /ivms/api/asstChrgInfo
  │     → orgId 기준 담당자 목록(chrgId, chrgNm, chrgTypeCd) 조회
  ├─ [API Request Tool] POST /ivms/api/mngtListDetail
  │     → 담당자별(rspnMngId) 자산 목록 + SECURITY_SCORE neq 100(취약) 필터
  ├─ [API Request Tool] GET /ivms/api/guidelineCdInfo 또는
  │                       POST /ivms/api/guidelineCdList
  │     → 각 미조치 항목의 진단기준/현황/조치방법(measure) 조회
  System Prompt: "조직명을 입력받아 IVMS API를 순차 호출해
                  담당자별 미조치 자산·항목 목록과 조치가이드 원문을 수집한다."
     │
     ▼ Response (담당자별 원시 데이터 취합)
[Agent #2: 담당자별 압박 메시지 + 조치가이드 생성 Agent]
  Input: Agent #1 → Response
  System Prompt: "심각도(severity) + 경과일(7일 이상)을 기준으로 미조치 항목을
                  선별하고, 담당자별로 (1) 압박 메시지, (2) 조치가이드 요약을
                  각각 생성한다. 담당자가 N명이면 N개 섹션으로 구분해 출력한다."
     │
     ▼ Response (담당자별 결과물 N건이 하나의 텍스트로 통합)
[Human Approval]
  Target Message: Agent #2 → Response (question 포트)
  대기: 보안담당자가 N건 전체를 한 번에 검토 후 승인/거절
     │
     ▼ Human Approval
[Language Model]                  ← Human Approval → Chat Output 직접 연결 불가 (제약)
  Input: Human Approval → Human Approval
  Model: azure_openai:gpt-4.1-mini
     │
     ▼ Response
[Chat Output]
```

### 노드 매핑 근거

| 구성 요소 | 참조 패턴 | 근거 |
|---|---|---|
| `Chat Input → Agent(API Request Tool)` | Workflow 4 (2-2) | 사내 API를 Agent Tool로 호출하는 검증된 패턴 |
| `Agent → Human Approval → Language Model → Chat Output` | Workflow 7 (4-2) | Human Approval 출력이 Chat Output에 직접 연결 불가하므로 Language Model 경유 필수 (`07-ixi-enterprise-requirements-spec.md`의 REQ-002가 해결되면 향후 LM 경유 단계 생략 가능) |
| Agent 2단계 분리(수집 Agent / 생성 Agent) | 신규 설계 | IVMS API 호출(도구 사용)과 담당자별 콘텐츠 생성(추론)의 역할을 분리해 프롬프트 복잡도를 낮춤. 단일 Agent로 통합도 가능하나, Tool 호출 스텝이 많아(4개 API × 담당자 수) 하나의 System Prompt에 모두 지시하면 누락 위험이 있어 2-Agent 구조를 권장 |

---

## 4. IVMS API 호출 시퀀스

| 순서 | API | 메서드 | 역할 | 핵심 필드 |
|---|---|---|---|---|
| 1 | `/ivms/api/orgList` | GET | 조직명 → orgId 확인 | `orgId`, `orgNm`, `pOrgId` |
| 2 | `/ivms/api/asstChrgInfo` | GET | orgId 기준 담당자 목록 조회 | `chrgId`, `chrgNm`, `chrgTypeCd`(CHGR=정담당자/SCHGR=부담당자), `orgIdPath` |
| 3 | `/ivms/api/mngtListDetail` | POST | 담당자별 자산 중 미조치(취약) 자산 필터링 | `filter.xorStr`: `SECURITY_SCORE neq 100`, 응답의 `chrgId`/`securityScore`/`timeEndYmd`(최근 진단일)/`resultId` |
| 4 | `/ivms/api/guidelineCdInfo`, `/ivms/api/guidelineCdList` | GET/POST | 미조치 항목별 조치방법(가이드라인) 조회 | `severity`, `guidelineNm`, `criteria`(진단기준), `analysisInfo`(현황), `measure`/`measureDetailOrigin`(조치방법) |

### 미조치 판단 로직

- API 3(`mngtListDetail`)에서 `SECURITY_SCORE neq 100` 필터로 취약 자산을 1차 선별
- 자산별 최근 진단일(`timeEndYmd`) 기준 **경과일 ≥ 7일**인 항목만 "미조치"로 최종 분류 (7일 미만은 "조치 유예 기간"으로 간주해 압박 대상에서 제외)
- API 4(`guidelineCdInfo`/`guidelineCdList`)의 `severity` 값과 결합해 Agent #2 프롬프트에서 우선순위 정렬(심각도 높은 항목 우선 표기)에 활용

---

## 5. 알려진 제약 및 리스크

### 5.1 스케줄 트리거 부재는 이번 요구사항의 블로커가 아님

`07-ixi-enterprise-requirements-spec.md`의 **REQ-007**에 이미 문서화된 대로, ixi-enterprise는 현재 Schedule Trigger(Cron)/Webhook Trigger 노드가 없고 모든 플로우가 Chat Input에서 시작해야 한다. 인터뷰 결과 이번 요구사항은 **보안담당자가 수동으로 챗봇에 요청**하는 방식으로 확정되었으므로 이 제약은 문제가 되지 않는다.

> **향후 확장 시 주의**: 만약 추후 "매주 자동으로 압박 메시지 생성" 등 스케줄 기반 자동화로 확장하려면, REQ-007(Schedule Trigger 노드 추가)이 ixi-enterprise 플랫폼에 선행 구현되어야 한다. 이 문서의 범위에서는 해당 사항 없음.

### 5.2 외부 발송 노드 부재도 블로커가 아님

ixi-enterprise 노드 카탈로그(`04-ixi-enterprise-node-catalog.md`)상 Slack/이메일/Teams 등 아웃바운드 알림 노드는 존재하지 않는다. 인터뷰 결과 출력은 **채팅 응답까지만**이며 이후 전달은 보안담당자가 수동으로 수행하므로 문제 없음.

> 🔴 **정정(2026-08-20, 실측)**: 위 전제는 사실과 다르다. **`Send Mail Output` 노드가 실재한다**(category=OUTPUT, 필드: `mail_title`/`mail_receiver`/`input`). 본 문서 작성 이후 추가된 것으로 보이며, 04번 노드 카탈로그에도 누락되어 있었다(2026-08-20 반영).
>
> 다만 **실사용은 현재 불가능하다.** 5단계 구현 검증 결과, 메일 본문이 평문이고 그 앞에 필수로 경유해야 하는 Language Model이 입력의 줄바꿈을 보존하지 못해 **수십 건의 목록이 한 문단으로 뭉개져 판독 불가**한 상태로 발송된다. 이에 플로우 A 최종 구성에서는 **메일 발송을 제외하고 Chat Output으로 출력**하도록 결정했다.
>
> → `07-ixi-enterprise-requirements-spec.md` **REQ-019 / REQ-020** 등록. 두 요구사항이 해결되면 발송 기능을 되살릴 수 있다.
>
> 검증 상세: `ixi-enterprise/stage5-test-guide.md` 5.5~5.6절, `ixi-enterprise/docs/ivms-flow-a-build-lessons.md` 5.7절

### 5.3 `guidelineCdInfo`/`guidelineCdList` 파라미터 무관 응답 이슈

`08-ivms_openapi_spec.md`에 실제 curl 테스트로 확인된 내용에 따르면, 이 두 API는 요청 시 `guidelineCd` 파라미터를 지정해도 응답이 해당 코드로 필터링되지 않고 **`resultId`/`aresultNo`/`guidelineIfKey`/`itemCode`/`agentServerNm` 기준으로 관련된 전체 가이드라인 항목을 반환**하는 것으로 보인다.

- **영향**: Agent #1이 특정 미조치 항목 하나의 조치가이드만 콕 집어 요청해도, 응답에는 같은 스캔 결과(resultId)에 속한 다른 가이드라인 항목까지 섞여 들어올 수 있음
- **대응 방안**: Agent #2의 System Prompt에서 "응답에 포함된 가이드라인 항목 중 실제 미조치 대상 항목(guidelineCd 일치)만 선별해 사용하라"는 지시를 명시적으로 추가해야 함. 구현 단계에서 실제 응답 샘플로 재검증 필요

### 5.4 Human Approval → Chat Output 직접 연결 불가

`07-ixi-enterprise-requirements-spec.md`의 **REQ-002**에 문서화된 기존 제약으로, Human Approval 노드는 Chat Output에 직접 연결할 수 없어 Language Model을 경유해야 한다(Workflow 7 패턴 재사용). 이번 플로우에서도 동일하게 적용되며, 경유하는 Language Model에는 별도 System Prompt 없이 승인된 내용을 그대로 전달하는 패스스루 역할만 부여한다.

### 5.5 담당자 수(N) 증가에 따른 단일 응답 길이 문제

조직 규모가 크면 담당자 수가 많아지고, Agent #2가 담당자별 압박 메시지+조치가이드를 모두 하나의 응답에 담아야 하므로 응답 길이가 길어질 수 있다. 이는 LLM 토큰 한도 및 Human Approval 화면에서의 가독성에 영향을 줄 수 있으므로, 조직 규모가 큰 경우(예: 담당자 10명 이상) 결과를 어떻게 분할할지는 구현 단계에서 별도 검토가 필요하다(본 요구명세서 범위 밖).

---

## 6. 향후 확장 여지

- **자동 스케줄링**: `07-ixi-enterprise-requirements-spec.md`의 REQ-007(Schedule Trigger) 구현 후, 본 플로우를 그대로 재사용해 "매주 월요일 자동 압박 메시지 생성" 등으로 확장 가능
- **자동 알림 발송**: ixi-enterprise에 API Request 노드(일반 모드)를 활용해 Slack/이메일 webhook으로 직접 발송하는 것도 현재 노드로 기술적으로는 가능하나, 이번 요구사항에서는 명시적으로 범위 밖으로 확정됨
- **Human Approval 타임아웃**: 승인자가 장기간 미응답 시 플로우가 무한 대기하는 기존 제약(REQ-017)은 본 플로우에도 동일하게 적용되므로, 운영 시 승인 지연에 유의 필요

---

## 7. 요약 — 신규 vs 기존 문서 관계

| 문서 | 대상 독자 | 목적 |
|---|---|---|
| `07-ixi-enterprise-requirements-spec.md` | ixi-enterprise **플랫폼 개발팀** | ixi-enterprise 자체의 기능 격차(트리거/디버깅/예외처리 등) 개선 요청 |
| `09-ivms-ixi-integration-requirements-spec.md`(본 문서) | 이 프로젝트의 **구현 담당자** | IVMS 연동 압박+조치가이드 플로우의 구체적 설계 및 구현 요구사항 |

두 문서는 서로 참조하되 독립적으로 유지한다.

---

## 8. 담당자 조치 확인 E2E 플로우

### 8.1 배경

앞선 1~7절은 **보안담당자**가 조직 단위로 미조치 현황을 압박하고 조치가이드를 생성하는 플로우를 다룬다. 이와 별개로, **서버 개발 담당자 본인**이 자신의 미조치 항목을 확인하고, 조치가이드를 받아 실제로 조치를 수행하며, 실행 과정에서 발생하는 문제를 트러블슈팅하는 전체 여정도 별도의 챗봇 플로우로 정의할 필요가 있다.

이 여정은 다음 두 가지 핵심 제약 위에서 설계된다.

- **온디맨드 재스캔 불가**: IVMS는 서버 부하 문제로 특정 자산/항목을 즉시 재진단하는 API를 제공하지 않는다. 재점검은 **매주 새벽 1회 전체 자산 배치 폴링**으로만 이루어지며, 조치 완료 후에도 다음 배치 전까지는 IVMS 데이터에 반영되지 않는다.
- **대화 메모리 부재**: ixi-enterprise는 세션 간 대화 이력을 누적하는 기능이 없다(`04-ixi-enterprise-node-catalog.md` 전체 노드 명세 기준, Agent 노드에 Memory 파라미터 없음). 따라서 담당자가 여러 차례 재시도할 때마다 이전 시도 내역을 매번 직접 붙여넣어야 한다.

### 8.2 전체 단계 개요

```
[1단계] 담당자가 자신의 미조치 항목 확인
   ↓
[2단계] AI가 조치가이드(명령어 원문) 제공
   ↓
[3단계] 담당자가 서버에서 직접 조치 명령 실행 (오프라인 행위)
   ↓ (실행 결과에 따라 분기)
   ├─ 실행 실패 → [3-A단계] 실패 로그 기반 트러블슈팅 (반복 가능)
   └─ 실행 성공 → [4단계] 다음 배치까지 대기 → 배치 후 재확인
```

### 8.3 [1단계] 담당자 본인의 미조치 항목 확인

```
[Chat Input]
  User Message: "제 미조치 취약점 목록 보여주세요" (담당자 본인 이름/사번 포함)
     │
     ▼
[Agent #1: 담당자 조회 Agent]
  Tools ↓
  ├─ [API Request Tool] GET /ivms/api/asstChrgInfo
  │     → 담당자명 → chrgId 확인
  └─ [API Request Tool] POST /ivms/api/mngtListDetail
        → chrgId 기준 자산 목록 + SECURITY_SCORE neq 100(미조치) 필터
  System Prompt: "담당자 이름으로 자산과 미조치 항목 목록을 조회해
                  자산별로 정리해 제시한다."
     │
     ▼ Response
[Chat Output]
```

2절의 보안담당자용 압박 플로우와 노드 구조는 유사하나, 대상이 **보안담당자가 아닌 서버 개발 담당자 본인**이고 **조직 전체가 아닌 자기 항목만** 조회한다는 점이 다르다.

### 8.4 [2단계] 특정 항목의 조치가이드 요청

```
[Chat Input]
  User Message: "DBM-001 조치 방법 알려주세요"
     │
     ▼
[Agent #2: 조치가이드 조회 Agent]
  Tools ↓
  └─ [API Request Tool] GET /ivms/api/guidelineCdInfo
        → guidelineCd 기준 measure/measureDetailOrigin(조치 명령어 원문) 조회
  System Prompt: "요청한 항목의 조치기준(criteria), 현황(analysisInfo),
                  조치방법(measure) 원문을 그대로 제시한다.
                  응답에 다른 무관한 항목이 섞여 있을 수 있으므로
                  요청한 guidelineCd와 정확히 일치하는 항목만 선별해 사용한다."
     │
     ▼ Response
[Chat Output]
```

5.3절에서 확인된 `guidelineCdInfo`의 "파라미터 무관 응답 이슈"에 대한 방어 지시가 시스템 프롬프트에 반드시 포함되어야 한다.

### 8.5 [3단계] 담당자가 서버에서 명령 실행 → 결과에 따라 분기

이 시점은 담당자가 실제로 서버에서 조치 명령을 실행하는 오프라인 행위이므로 플로우 상에는 나타나지 않으며, 실행 결과에 따라 두 갈래로 이어진다.

#### 8.5.1 [3-A] 명령 실행 자체가 실패한 경우 (즉시 트러블슈팅)

```
[Chat Input]
  User Message: "DBM-001 조치 명령 실행했는데 에러 납니다. 로그: [붙여넣은 에러 로그]"
     │
     ▼
[Agent #3: 실행 오류 분석 Agent]
  Tools ↓
  └─ [API Request Tool] GET /ivms/api/guidelineCdInfo
        → 원래 조치가이드 원문 재조회 (비교 기준)
  System Prompt: "사용자가 제공한 에러 로그와 원래 조치가이드 원문을 비교해
                  실패 원인(권한 부족/문법 오류/OS 버전 차이 등)을 분석하고
                  대안 명령어를 제시한다."
     │
     ▼ Response
[Chat Output]
```

담당자가 대안을 시도했다가 또 실패하면 같은 플로우를 다시 트리거한다. 대화 메모리가 없으므로 담당자가 이전 시도 내역까지 매번 함께 붙여넣어야 이전 제안과 겹치지 않는 새 대안을 받을 수 있다.

#### 8.5.2 [3-B] 명령 실행은 성공했지만 즉시 검증 수단이 없는 경우

명령 자체는 에러 없이 실행됐지만 "진짜로 반영됐는지"는 IVMS 배치 전까지 확인 불가능하다. 이 경우 담당자는 별도 요청 없이 자연스럽게 8.6절([4단계])로 넘어간다.

### 8.6 [4단계] 배치 후 재확인 (온디맨드 재스캔 불가, 주간 배치 전제)

```
[Chat Input]
  User Message: "DBM-001 조치했는데 여전히 FAIL로 나옵니다.
                 조치 완료 시각: 2026-07-05 14:00. 실행 로그: [붙여넣은 로그]"
     │
     ▼
[Agent #4: 배치 시점 판별 Agent]
  Tools ↓
  └─ [API Request Tool] GET /ivms/api/dgnsRslt
        → 해당 자산의 진단 이력 조회, 최근 timeEnd 확인
  System Prompt: "사용자가 제시한 조치 완료 시각과 IVMS의 가장 최근 진단
                  종료 시각(timeEnd)을 비교해 'PENDING_BATCH' 또는
                  'STILL_FAILING' 중 하나로만 분류해 응답한다."
     │
     ▼ Response (정형화된 분류 키워드)
[AI Router]
  Text: ← Agent #4 Response
  Exit Condition:
  ├─ "PENDING_BATCH" (아직 다음 배치 미반영)
  └─ else (= STILL_FAILING, 배치 후에도 FAIL)
     │
     ├─[PENDING_BATCH] → [Language Model]
     │     System Prompt: "다음 정기 배치(매주 새벽)가 지난 뒤
     │                     다시 확인해달라고 안내하고 예상 반영 시점을 안내한다."
     │
     └─[else, STILL_FAILING] → [Agent #5: 실패 원인 재분석 Agent]
           Tools ↓
           └─ [API Request Tool] GET /ivms/api/guidelineCdInfo
                → 원래 조치가이드 원문 재조회
           System Prompt: "배치 반영 이후에도 FAIL이 유지되는 상황이다.
                           사용자가 제공한 실행 로그와 원래 조치가이드를
                           비교해 실패 원인을 분석하고 대안을 제시한다."
                │
                ▼
[Chat Output]  ← (두 경로 모두 여기로 수렴)
```

AI Router의 두 경로가 모두 Chat Output으로 수렴하는 구조는, 각 경로의 최종 노드(Language Model / Agent)가 각각 Chat Output에 연결되는 방식으로 구현한다(AI Router `else`의 Chat Output 직접 연결은 불가하므로 반드시 경유, `04-ixi-enterprise-node-catalog.md` 노드 연결 제약과 동일). Agent #4의 응답을 "PENDING_BATCH"/"STILL_FAILING" 같은 정형화된 키워드로 강제하는 것이 AI Router 분기 신뢰도를 높인다.

### 8.7 전체 흐름 요약도

```
담당자 본인 미조치 확인 (1)
        │
        ▼
   조치가이드 요청 (2)
        │
        ▼
  담당자가 서버에서 명령 실행 (오프라인)
        │
   ┌────┴─────┐
   ▼          ▼
명령 실패     명령 성공
   │          │
   ▼          ▼
실행오류      배치 대기
분석(3-A) ⟲   → 배치 후 재확인 요청(4)
(반복 가능)         │
                ┌───┴────┐
                ▼        ▼
           배치 미반영   배치 후에도 FAIL
           (대기 안내)   → 실패 원인 재분석(3-A와 유사, 5)
                              │
                              ▼
                         (필요 시 3-A로 회귀, 반복)
```

### 8.8 이 플로우에서 재확인되는 핵심 제약 3가지

1. **온디맨드 재스캔 없음** — 8.6절([4단계])은 항상 "지난 배치 결과 기준"으로만 판별 가능하며, 즉시 검증은 불가능하다. (IVMS 개발팀 회신: 서버 부하 문제로 구현 불가)
2. **대화 메모리 없음** — 8.5.1절([3-A])과 8.6절(else 분기)을 반복할 때마다 담당자가 매번 로그와 이전 시도 내역을 직접 붙여넣어야 한다.
3. **`guidelineCd` 파라미터 무관 응답 이슈** — 8.4/8.5.1/8.6절에서 `guidelineCdInfo`를 호출할 때마다 "정확히 일치하는 항목만 선별"하라는 방어 프롬프트가 반복적으로 필요하다(5.3절 참조).
