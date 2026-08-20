# 플로우 A 노드별 상세 구성 — IVMS 미조치 압박 및 조치가이드 생성

**작성일**: 2026-07-10
**목적**: `10-ivms-ixi-workflow-build-guide.md` 2절(플로우 A)을 실제 ixi-enterprise 캔버스에 구성할 수 있도록, 각 노드의 System Prompt 전체 원문과 API Request Tool의 URL/Method/Header/Query Params/Body를 실전 투입 가능한 수준으로 확정한 문서.
**참조 문서**: `08-ivms_openapi_spec.md`(IVMS API 실제 스펙), `09-ivms-ixi-integration-requirements-spec.md`(요구사항), `10-ivms-ixi-workflow-build-guide.md`(캔버스 구성 절차), `04-ixi-enterprise-node-catalog.md`(노드 파라미터 명세)

---

## 0. 중요 — API 체이닝 재설계 안내 (반드시 확인)

`09`/`10`번 문서는 플로우 A의 API 호출 순서를 **orgList → asstChrgInfo → mngtListDetail → guidelineCdInfo** 4단계로 서술하고 있으나, `08-ivms_openapi_spec.md`의 실제 검증된 스펙을 대조한 결과 아래 2가지 불일치가 발견되어 본 문서에서 바로잡았다.

| 항목 | 09/10번 문서의 가정 | 08번 문서의 실제 스펙 | 조치 |
|---|---|---|---|
| `asstChrgInfo`의 역할 | "orgId 기준 담당자 목록 조회" — 조직 단위 조회 API로 가정 | 실제로는 **자산 단위** 조회 API (`asstId`+`asstVer` 필수, `orgId` 입력 파라미터 자체가 없음 — 08번 문서 2.4절) | 조직 기준 담당자 목록은 `mngtListDetail` 응답의 `chrgId`/`chrgNm`(자산 레코드에 이미 포함, 08번 문서 2.2절 `assetList[].chrgId`)으로 획득. `asstChrgInfo`는 **보조 확인용**(자산 1건의 정담당자/부담당자 상세를 재조회하고 싶을 때)으로 역할을 재정의하고, 플로우 A의 필수 체인에서는 제외
| `guidelineCdInfo` 호출 전제 | `mngtListDetail` 응답만으로 바로 호출 가능하다고 가정 | `guidelineCdInfo`는 `aresultNo`+`guidelineIfKey`+`itemCode`+`agentServerNm` 4개 파라미터가 **모두 필수**(08번 문서 4.5절)인데, 이 값들은 `mngtListDetail` 응답에 **없음**. `scanResultCodeMngtDetail`(08번 문서 4.2절) 응답의 `scanRsltCodeList[]`에만 `guidelineIfKey`/`itemCode`/`agentServerNm`/`resultIfKey`가 존재 | `mngtListDetail`과 `guidelineCdInfo` 사이에 **`scanResultCodeMngtDetail` 호출을 추가**해야 정상적으로 체이닝됨

**재설계된 플로우 A의 실제 API 체이닝(4단계 → 4단계, 구성은 동일하나 2/3번째 API가 교체됨):**

```
1. orgList         (GET)  조직명 → orgId 확인 (하위 조직 목록 조회, 필요 시 재귀 순회)
2. mngtListDetail  (POST) orgId(mgmtOrgId) 기준 자산 목록 조회 + SECURITY_SCORE neq 100(미조치) 필터
                          → 이 응답에서 chrgId/chrgNm(담당자 정보)과 asstCode 목록을 동시에 획득
3. scanResultCodeMngtDetail (POST) 자산별 항목별 상세 조회, resultStatusCdListStr=["FAIL"]로 취약 항목만 필터
                          → guidelineIfKey/itemCode/agentServerNm/resultIfKey/guidelineCd 확보
4. guidelineCdInfo (GET)  위 3번 응답의 4개 키로 각 미조치 항목의 조치방법(measure) 조회
```

이에 따라 **Agent #1의 Tools는 4개(orgList, mngtListDetail, scanResultCodeMngtDetail, guidelineCdInfo)**로 구성하며, `10`번 문서에 있던 `asstChrgInfo` API Request Tool은 플로우 A에서 제외한다. (필요 시 부담당자 확인용으로 5번째 Tool로 추가할 수 있으나 필수 체인은 아니므로 본 문서의 기본 구성에서는 제외했다.)

> **개정 이력(2026-07-14, Agent 분할)**: 위 구성대로 실제 캔버스에서 Agent #1 하나에 orgList/assetSsrcceTemplate/assetCategory/mngtListDetail/scanResultCodeMngtDetail 5개 Tool을 모두 연결해 실행한 결과, `context limit exceeded: estimated 120032 tokens > budget 100000` 오류가 발생했다. 이는 n8n 표준 오류가 아니라 ixi-enterprise 플랫폼이 LLM 호출 전 프롬프트+컨텍스트 총 토큰 수를 추정해 사전 차단하는 자체 가드레일이다. 자산 건수가 많은 조직(예: 1000건 이상)을 조회하면 `mngtListDetail`/`scanResultCodeMngtDetail`의 페이지네이션 반복 호출마다 응답 원본이 Agent #1의 컨텍스트에 누적되어 예산을 초과한다. ixi-enterprise에는 Function/Code/Merge 등 응답을 사전 가공할 노드가 없으므로(`04-ixi-enterprise-node-catalog.md` 1~32행), 유일한 해법은 **Agent를 분할해 각 Agent가 자신의 Tool 원본 응답을 자기 컨텍스트 안에서만 다루고, 다음 Agent에는 요약된 텍스트만 넘기는 것**이다. Agent→Agent 연결(Response→Input)은 `04-ixi-enterprise-node-catalog.md` 155~206행에서 지원이 확인됐다.
>
> 이에 따라 Agent #1을 **Agent #1A(orgList, assetSsrcceTemplate, assetCategory) → Agent #1B(mngtListDetail) → Agent #1C(scanResultCodeMngtDetail)** 3개로 분할했다(2-6~2-8절). `guidelineCdInfo`(4단계, 7.4절)는 아직 미검증 상태이므로 이번 분할에는 포함하지 않았다 — 추후 추가 시 Agent #1C에 얹을지 별도 Agent #1D로 뺄지는 그 시점의 컨텍스트 사용량을 보고 판단한다.
>
> **개정 이력(2026-07-14, 2차 — Agent 분할 후에도 재발)**: 위 3-Agent 분할을 실제 캔버스에 반영해 재실행한 결과, 이번에는 **Agent #1B(`mngtListDetail`) 실행 단계**에서 `context limit exceeded: estimated 109508 tokens > budget 100000` 오류가 재발했다. Agent 분할은 "서로 다른 Tool들의 응답을 별도 컨텍스트로 분리"하는 데는 효과가 있었지만, **같은 Tool을 여러 페이지에 걸쳐 반복 호출하는 문제 자체는 해결하지 못한다** — 한 Agent 안에서는 모든 페이지 호출 응답이 그 Agent의 컨텍스트에 계속 누적되기 때문이다. 근본 원인은 2-7절 System Prompt의 `pageSize=10` 기본값이다. 미조치 자산이 많은 조직(1000건 이상)을 조회하면 `pageSize=10` 기준 100회 이상 반복 호출이 필요해지고, 매 호출마다 `assetList[]` 원본이 쌓여 예산을 초과한다. → **대응**: 2-7절/7.2절 System Prompt의 `pageSize`를 `10`→`200`으로 상향하고, 반복 호출 상한(3회, 총 600건)을 두어 그 이상은 "일부만 조회했음"을 명시하고 중단하도록 개정했다(2-7절 참고). `scanResultCodeMngtDetail`을 쓰는 Agent #1C도 동일한 구조적 위험이 있으므로 페이지네이션 반복 시 동일한 상한 적용을 검토해야 한다(2-8절).
>
> **개정 이력(2026-07-14, 3차 — pageSize 상향 후에도 재발, Agent 분할의 근본적 한계 확인)**: `pageSize=200` + 반복상한(3회, 600건) 대응을 실제 캔버스에 반영해 재실행했으나, 자산 건수가 더 많은 조직에서 Agent #1B(`mngtListDetail`) 단계의 `context limit exceeded` 오류가 다시 재발했다. 이는 **Agent를 아무리 쪼개도 "같은 Tool을 여러 페이지에 걸쳐 반복 호출할 때 그 응답이 한 Agent의 컨텍스트 안에 계속 누적되는" 구조적 문제 자체는 해결되지 않는다**는 것을 재확인시켰다 — `pageSize` 상향은 반복 횟수를 줄이는 미봉책일 뿐, 자산이 더 많은 조직이 오면 다시 예산을 초과한다. `04-ixi-enterprise-node-catalog.md`를 재확인한 결과 Loop/Iterate 노드, Function/Code/Merge 등 응답을 사전 축약할 노드가 없어 캔버스 구조만으로 페이지 응답을 줄일 방법이 없음을 재확인했다.
>
> 이에 따라 근본적으로 다른 접근(서버 필터 강화 / 담당자 단위 스코프 축소 / 외부 배치 스크립트 분리) 중 **"서버 필터 강화"**를 채택해 `08-ivms_openapi_spec.md`를 재조사했다. 그 결과 날짜/기간 기반 서버 필터는 스펙상 존재하지 않지만(`filter/xorStr`는 `SECURITY_SCORE`, `AGENT_STATE`만 지원), `mngtListDetail`에 **`rspnMngId`(담당자ID)** 파라미터가 이미 선택값으로 존재함을 확인했다(08번 문서 2.2절). 담당자 1인 단위로 호출을 좁히면 응답 건수가 조직 전체보다 훨씬 작아져 페이지네이션 반복이 크게 줄어든다.
>
> 다만 담당자 ID 목록을 사전에 알아야 하며, `asstChrgInfo`는 자산 단위 API(0절 상단 표 참고)라 조직의 담당자 목록을 사전에 추출하는 용도로는 쓸 수 없다. 따라서 **Agent #1B를 2단계로 재분할**했다: **Agent #1B(경량 스캔)**가 `mngtListDetail`을 `mgmtOrgId`만으로 훑되 응답에서 `chrgId`/`chrgNm`(담당자 정보)만 추출해 자산 상세는 버리고 유니크 집합만 누적하며, 뒤이은 **Agent #1B-2(담당자별 정밀조회)**가 그 담당자 목록을 순회하며 `rspnMngId`를 채워 `mngtListDetail`을 재호출해 담당자 단위로 자산 상세를 수집한다(2-7절/2-7-2절 참고).
>
> ⚠️ **이 2단계 구조도 완전한 근본 해결은 아니다** — Agent #1B의 1차 경량 스캔 자체는 여전히 조직 전체를 페이지네이션으로 훑어야 하므로, 담당자 수 자체가 매우 많은 조직에서는 1차 스캔 단계에서 다시 컨텍스트 예산 문제가 재발할 수 있다. 다만 자산 상세 필드를 버리고 담당자 ID만 누적하므로 페이지당 컨텍스트 사용량은 크게 줄어든다. 이 완화책으로도 재발할 경우 방법 3(외부 배치 스크립트로 IVMS API 호출과 페이지네이션 자체를 캔버스 밖에서 처리)을 검토해야 한다.

---

## 1. 인증/헤더 관련 사전 확인 사항

08번 문서 「공통 인증 헤더」절은 `X-Global-Transaction-ID`/`X-APP-NAME`/`X-AuthorizationTime`/`X-Header-Authorization` 4종을 **필수(Y)**로 기재하고 있으나, **실제 캔버스 테스트 결과 이 4종을 모두 빈 값으로 두어도 API가 정상 응답값을 반환하는 것이 확인되었다(2026-08-18)**. 따라서 플로우 A 구성 시 인증 헤더 값 확보는 선행 조건이 아니다.

| Header Key | 캔버스 설정값 | 비고 |
|---|---|---|
| `X-Global-Transaction-ID` | 빈 값 | 빈 값으로 정상 응답 확인(2026-08-18) |
| `X-APP-NAME` | 빈 값 | 빈 값으로 정상 응답 확인(2026-08-18) |
| `X-AuthorizationTime` | 빈 값 | 빈 값으로 정상 응답 확인(2026-08-18) |
| `X-Header-Authorization` | 빈 값 | 빈 값으로 정상 응답 확인(2026-08-18) |
| `Content-Type` | `application/json` | POST(`mngtListDetail`, `scanResultCodeMngtDetail`) 요청에만 필요 |

> **개정 이력(2026-08-18)**: 이 절은 원래 `Authorization: Bearer {IVMS_API_TOKEN}` 플레이스홀더를 두고 "IVMS 운영팀 확인 후 실제 값으로 교체해야 한다"고 서술했으나, 실제 캔버스 실행에서 헤더 4종이 모두 빈 값인 상태로 API가 정상 응답값을 반환함을 확인해 위 표로 교체했다. 이로써 7.2절 3차 개정 이력에서 한때 `msgCd: E` 실패의 원인으로 의심했던 `X-Header-Authorization` 서명 만료 가설은 **완전히 배제**된다 — 해당 실패의 실제 원인은 Query Params 잔존과 Read Timeout 부족이었음이 확정됐다.
>
> ⚠️ **단, 헤더 키 자체는 빈 값으로 남겨둘 것**(캔버스에서 키를 삭제하지 않는다). 또한 이 확인은 현재 테스트를 수행한 네트워크 환경 기준이므로, **배포 환경이 바뀌면(사내망 → 외부, 다른 IP 대역 등) 인증 요구가 달라질 수 있다.** 08번 문서 스펙표는 여전히 4종을 필수로 기재하고 있어, 서버가 헤더를 검증하지 않는 것인지 현재 호출 경로가 네트워크 레벨에서 이미 인가된 것인지는 구분되지 않았다.

> ⚠️ **IVMS 운영팀 확인 필요(잔여)**: 실제 배포 전 (1) `{IVMS_BASE_URL}` 실제 도메인, (2) IP 화이트리스트 등록 필요 여부, (3) 배포 환경 변경 시 인증 헤더 요구 여부를 확인할 것. (인증 헤더 방식 자체는 위와 같이 현 환경에서 불필요함이 확인되어 확인 항목에서 제외)

모든 API Request Tool 노드 공통 설정:
- **Tool Mode**: ON (Agent의 Tools 포트에 연결하려면 필수)
- **Connect Timeout**: 1000~3000ms
- **Read Timeout**: GET 계열(`orgList`, `assetSsrcceTemplate`, `assetCategory` 등)은 10000ms. **POST+Body 계열(`mngtListDetail`, `scanResultCodeMngtDetail`)은 30000ms로 설정**(2026-07-14 실제 캔버스 테스트 결과: 10000ms 이하에서는 응답이 오기 전에 타임아웃되어 실패 처리됨 — 이전에 인증 서명 만료로 추정했던 실패의 실제 원인 중 하나였음)
- **Query Params**: POST+Body 계열 Tool은 Query Params를 반드시 비워둘 것(값이 남아있으면 URL에 불필요한 쿼리스트링이 붙어 요청이 실패함 — 2026-07-14 실제 확인)

---

## 2. 노드별 상세 구성

### 2-1. Chat Input

- **파라미터**: 없음(플로우 시작 노드)
- **연결**: `User Message` → Agent #1A `Input`
- **예상 사용자 입력 예시**: `"Enterprise SW프로덕트개발팀 미조치 현황 압박 및 조치가이드 생성해줘"`

---

### 2-2. API Request Tool #1 — orgList

**용도**: 사용자가 입력한 조직명을 `orgId`로 변환한다.

**실제 curl 테스트 원본(사용자 검증 완료, IF-API-098005)**

```bash
curl -X GET -k -i "https://ivms.lguplus.co.kr/ivms/api/orgList?orgType=1&pOrgId=org_000001" \
  -H "X-Global-Transaction-ID: test" \
  -H "X-APP-NAME: IVMS" \
  -H "X-AuthorizationTime: 20250804T145618+0900" \
  -H "X-Header-Authorization: kzS7dQYRUHWC7sZb1W1Q+4OzPQEwjJ1fGVMehFOEOMjXbk22ntCbdOICw7JP15d5H4fDC4fI73hOiL0SuOgGdW=="
```

이 curl로 실제 IVMS 운영 서버(`https://ivms.lguplus.co.kr`) 호출이 검증되었으므로, 아래 노드 설정은 **플레이스홀더가 아닌 실제 확정 값**을 기준으로 작성한다(1절의 `{IVMS_BASE_URL}`/`{IVMS_API_TOKEN}` 플레이스홀더 방식에서 이 노드만 예외).

| 항목 | 값 |
|---|---|
| 노드 라벨 | `API Request Tool: orgList` |
| Tool Mode | ON |
| 툴 설명 | `조직명으로 하위 조직 목록을 조회해 orgId를 확인하는 도구. pOrgId(상위 조직 ID)를 입력받아 그 하위 조직 목록을 반환한다. 최상위 조직부터 조회하려면 pOrgId="org_000001"로 시작한다.` |
| URL | `https://ivms.lguplus.co.kr/ivms/api/orgList` (curl로 검증된 실제 운영 도메인 — `{IVMS_BASE_URL}` 대신 이 값을 그대로 사용) |
| Method | GET |
| Connect Timeout | 3000ms |
| Read Timeout | 10000ms |

**Header** (curl `-H` 옵션 4개를 그대로 노드의 Header 팝업에 등록 — Header Key/Header Value 각각 입력)

| Header Key | Header Value | 필수 | 설명 |
|---|---|---|---|
| `X-Global-Transaction-ID` | 빈 값 | N(실측) | 08번 문서 스펙표는 필수(Y)로 기재하나, **빈 값으로도 정상 응답이 확인됨(2026-08-18)**. 호출별 고유 ID 채번이나 동적 생성(Function 노드 부재로 캔버스 구현 불가) 문제는 발생하지 않음 |
| `X-APP-NAME` | 빈 값 | N(실측) | 08번 문서 스펙표는 필수(Y), 고정값 `IVMS`로 기재하나, **빈 값으로도 정상 응답이 확인됨(2026-08-18)** |
| `X-AuthorizationTime` | 빈 값 | N(실측) | 08번 문서 스펙표는 필수(Y)로 기재하나, **빈 값으로도 정상 응답이 확인됨(2026-08-18)**. 캡처값(`20250804T145618+0900`)을 그대로 넣을 필요 없음 — 아래 개정 이력 참고 |
| `X-Header-Authorization` | 빈 값 | N(실측) | 08번 문서 스펙표는 필수(Y)로 기재하나, **빈 값으로도 정상 응답이 확인됨(2026-08-18)**. 서명 만료·재계산 문제는 발생하지 않음 — 아래 개정 이력 참고 |

> **개정 이력(2026-08-18)**: 위 두 헤더는 원래 "curl 캡처 당시 시각의 스냅샷이라 만료됐을 수 있으므로 매 호출 시 재계산이 필요할 가능성이 높다"고 서술하고 그 값을 그대로 넣도록 안내했으나, **실제 캔버스 테스트에서 인증 헤더 4종을 모두 빈 값으로 두어도 API가 정상 응답값을 반환함이 확인**되어 빈 값 기준으로 교체했다(1절 참고). 이에 따라 이 문서 곳곳에서 실패 원인으로 의심했던 "서명/시각 만료" 가설은 모두 배제된다. 단 헤더 키 자체는 삭제하지 말고 빈 값으로 유지하며, 배포 환경이 바뀌면 인증 요구가 달라질 수 있다는 점은 1절 경고를 참고한다.

> ✅ **해소됨(2026-08-18)**: 이 자리에는 원래 "`X-AuthorizationTime`/`X-Header-Authorization`이 시각 기반 서명이라면 고정값 입력 시 실 운영에서 만료로 인증 실패할 수 있고, ixi-enterprise는 Header Value에 정적 문자열만 지원하므로 매 호출 갱신 방법을 운영팀에 확인해야 한다"는 핵심 리스크 경고가 있었다. **실제로는 인증 헤더 4종을 모두 빈 값으로 두어도 API가 정상 응답값을 반환**하므로(1절 참고), 서명 갱신 메커니즘을 캔버스에서 구현해야 하는 문제 자체가 발생하지 않는다. 이 리스크는 해소된 것으로 처리한다.
>
> 나머지 3개 API Request Tool(`mngtListDetail`, `scanResultCodeMngtDetail`, `guidelineCdInfo`)에도 위 4개 헤더(`X-Global-Transaction-ID`, `X-APP-NAME`, `X-AuthorizationTime`, `X-Header-Authorization`)를 동일하게 등록해야 한다(POST 요청은 추가로 `Content-Type: application/json` 필요). 아래 2-3~2-5절의 Header 표도 이 4개 공통 헤더 기준으로 갱신 필요 — 상세는 각 절 참고.

**Query Params** (Tool 모드 — Agent가 채워 넣을 파라미터, curl의 `?orgType=1&pOrgId=org_000001` 부분)

| Query Param 이름 | 타입 | 필수 | curl 샘플 값 | 설명 |
|---|---|---|---|---|
| `orgType` | string | Y | `1` | 조직 타입. "1"=부문, "2"=그룹, "3"=담당, "4"=팀(08번 문서 1.6절). curl 캡처는 최상위 조회를 위해 `1`(부문)로 호출함. 하위 조직을 탐색할 때는 다음 레벨의 타입 값을 순차적으로 시도한다(부문→그룹→담당→팀). |
| `pOrgId` | string | Y | `org_000001` | 상위 부서 ID. curl 캡처는 최상위 루트값 `org_000001`로 호출함. 사용자가 언급한 조직명이 나올 때까지 응답의 `orgId`를 다시 `pOrgId`로 사용해 재귀 조회한다. |

**요청 예시(curl과 동일한 값)**

```
GET https://ivms.lguplus.co.kr/ivms/api/orgList?orgType=1&pOrgId=org_000001
```

**응답 예시(08번 문서 1.6절 기준 — curl 실제 검증 응답)**

```json
{
  "result": {
    "orgList": [
      { "orgId": "org_000001", "orgNm": "직속", "useYn": "Y", "pOrgId": "", "pAffltId": "org_000001" },
      { "orgId": "org_001953", "orgNm": "CSEO", "useYn": "Y", "pOrgId": "org_000001", "pAffltId": "org_000001" },
      { "orgId": "org_001199", "orgNm": "CHO", "useYn": "Y", "pOrgId": "org_000001", "pAffltId": "org_000001" },
      { "orgId": "org_000991", "orgNm": "Enterprise SW프로덕트개발팀", "useYn": "Y", "pOrgId": "org_000001", "pAffltId": "org_000001" }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

---

### 2-2-2. API Request Tool #1-2 — assetSsrcceTemplate

> **개정 이력(2026-07-14, 재작성)**: 이 Tool은 Agent #1A의 3개 Tool 중 하나로 2-6절에 언급되어 있었으나 정식 스펙 서브섹션이 없어 7.2절에만 값이 존재했다. 이번 재작성에서 2절로 정식 이관했다.

**용도**: 진단 템플릿 목록을 조회해 `atemplateNo`(진단템플릿 번호)를 확인한다. Agent #1A가 orgId 확정 뒤 이어서 호출한다.

**실제 스펙(08번 문서 1.2절, IF-API-098001)**

| 항목 | 값 |
|---|---|
| 노드 라벨 | `API Request Tool: assetSsrcceTemplate` |
| Tool Mode | ON |
| URL | `https://ivms.lguplus.co.kr/ivms/api/assetSsrcceTemplate` |
| Method | GET |
| Connect Timeout / Read Timeout | 3000ms / 10000ms |
| Header | 공통 인증 헤더 4종(2-2절 102~113행과 동일 — `X-Global-Transaction-ID`/`X-APP-NAME`/`X-AuthorizationTime`/`X-Header-Authorization`) |
| Query Params | `userId`(string, Y — 예: `admin`) |
| 툴 설명 | `진단 템플릿 목록을 조회하는 도구. 응답의 result.templateList[]에 atemplateNo(진단템플릿 번호), templateName(진단템플릿명)이 담겨 있다. 첫 번째 항목의 atemplateNo를 다음 단계의 templateNo로 사용한다.` |

**요청 예시**

```
GET https://ivms.lguplus.co.kr/ivms/api/assetSsrcceTemplate?userId=admin
```

**응답 예시(08번 문서 1.2절 기준)**

```json
{
  "result": {
    "templateList": [
      { "atemplateNo": "2", "templateName": "SSR_기준항목" }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

---

### 2-2-3. API Request Tool #1-3 — assetCategory

> **개정 이력(2026-07-14, 재작성)**: `assetSsrcceTemplate`과 동일하게 2-6절에 언급만 되어 있고 정식 스펙이 없던 Tool이라 이번 재작성에서 2절로 정식 이관했다.

**용도**: 자산 분류 목록을 조회해 `asstType`(자산타입)을 확인한다. Agent #1A가 `assetSsrcceTemplate` 다음으로 호출한다.

**실제 스펙(08번 문서 1.3절, IF-API-098002)**

| 항목 | 값 |
|---|---|
| 노드 라벨 | `API Request Tool: assetCategory` |
| Tool Mode | ON |
| URL | `https://ivms.lguplus.co.kr/ivms/api/assetCategory` |
| Method | GET |
| Connect Timeout / Read Timeout | 3000ms / 10000ms |
| Header | 공통 인증 헤더 4종(2-2절 102~113행과 동일) |
| Query Params | `userId`(string, Y — 예: `admin`), `asstCtgrLevel`(string, Y — `L`/`M`/`S` 중 대분류 조회 시 `L`) |
| 툴 설명 | `자산분류 목록을 조회하는 도구. 응답의 result.asstCtgrList[]에 asstCtgrId(자산분류ID), asstCtgrNm(자산분류명), asstType(자산타입)이 담겨 있다. asstCtgrLevel="L"로 대분류부터 조회하며, 여러 건이 반환되면 첫 번째 항목의 asstType 값을 사용한다.` |

**요청 예시**

```
GET https://ivms.lguplus.co.kr/ivms/api/assetCategory?userId=admin&asstCtgrLevel=L
```

**응답 예시(08번 문서 1.3절 기준, 일부 필드 생략)**

```json
{
  "result": {
    "asstCtgrList": [
      {
        "affltId": "org_000001",
        "asstCtgrId": "AT_0004356",
        "asstCtgrNm": "HYPERVISOR",
        "asstCtgrLevel": "L",
        "asstType": "SSRCCE"
      }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> ⚠️ **응답에 `selectedCategory` 필드는 없다.** 항상 `result.asstCtgrList[]` 배열로 반환되므로, Agent System Prompt는 이 배열에서 `asstType` 값을 확인하도록 지시해야 한다(2-6절 System Prompt 참고 — 이번 재작성에서 이 배열 파싱 방식으로 통일했다).

---

### 2-3. API Request Tool #2 — mngtListDetail

**용도**: 확인된 `orgId`를 `mgmtOrgId`로 사용해 해당 조직의 자산 목록 중 미조치(SECURITY_SCORE ≠ 100) 자산만 필터링 조회한다. 이 응답에는 담당자 정보(`chrgId`, `chrgNm`, `subChrgId`, `subChrgNm`)가 자산 레코드마다 포함되어 있으므로, 별도의 담당자 조회 API 없이 여기서 담당자 목록까지 동시에 획득한다.

| 항목 | 값 |
|---|---|
| 노드 라벨 | `API Request Tool: mngtListDetail` |
| Tool Mode | ON |
| 툴 설명 | `조직 ID(mgmtOrgId) 기준으로 관리 자산 목록을 조회하는 도구. filter.xorStr에 SECURITY_SCORE neq 100 조건을 넣으면 미조치(취약) 자산만 필터링된다. 응답의 각 자산 레코드에는 담당자 ID/명(chrgId, chrgNm)이 포함되어 있다.` |
| URL | `https://ivms.lguplus.co.kr/ivms/api/mngtListDetail` (orgList와 동일 도메인 — `{IVMS_BASE_URL}` 대신 실제 확정 도메인 사용) |
| Method | POST |
| Connect Timeout | 3000ms |
| Read Timeout | 10000ms |

**Header** (2-2절 `orgList`에서 curl로 검증된 공통 헤더 4종 + POST 전용 `Content-Type` 추가)

| Header Key | Header Value | 필수 |
|---|---|---|
| `X-Global-Transaction-ID` | `test` | Y |
| `X-APP-NAME` | `IVMS` | Y |
| `X-AuthorizationTime` | `20250804T145618+0900` (요청마다 값이 달라짐 — 아래 "실제 curl 검증 결과" 참고) | Y (⚠️ 시각 종속 가능성 — 2-2절 주의사항 참고) |
| `X-Header-Authorization` | `kzS7dQYRUHWC7sZb1W1Q+4OzPQEwjJ1fGVMehFOEOMjXbk22ntCbdOICw7JP15d5H4fDC4fI73hOiL0SuOgGdW==` (요청마다 값이 달라짐) | Y (⚠️ 시각 종속 가능성 — 2-2절 주의사항 참고) |
| `Content-Type` | `application/json` | Y (POST 요청이므로 필수 — GET인 `orgList`/`guidelineCdInfo`에는 불필요) |

**Body** — 이 API는 실제로 두 가지 조회 방식이 확인되었다. Agent의 System Prompt에서 상황에 맞는 방식을 선택하도록 안내한다.

**방식 A. `asstLCtgrId`(자산분류 대) 기준 조회 — 실제 curl로 검증됨**

```bash
curl -X POST -k -i \
  -H "Content-Type: application/json" \
  -H "X-Global-Transaction-ID: test" \
  -H "X-APP-NAME: IVMS" \
  -H "X-AuthorizationTime: 20250804T152412+0900" \
  -H "X-Header-Authorization: JXfEIbjsgS4ZabBqrv7XXAre5W6uU2HjhAkdV05BbGkyCW4D4Z4CycbrCOvt0DB7nTTE2z0fIW5hKdqmqJPFb7VQ==" \
  -d "{\"userId\":\"jwyoon21\",\"asstType\":\"SSRCCE\",\"templateNo\":\"151\",\"diagYear\":\"2025\",\"asstLCtgrId\":\"AT_0005382\"}" \
  "https://ivms.lguplus.co.kr/ivms/api/mngtListDetail"
```

| Body 필드 | 설명 |
|---|---|
| `userId` | 요청 사용자 ID. curl 샘플은 `"jwyoon21"`(개인 계정으로 추정) — 실 운영 시 서비스 계정 ID 사용 검토 필요(운영팀 확인). |
| `asstType` | 자산타입. `"SSRCCE"` 고정. |
| `templateNo` | 진단템플릿 번호. curl 샘플 `"151"`. |
| `diagYear` | 기준연도. curl 샘플 `"2025"`. |
| `asstLCtgrId` | 자산분류(대) ID. curl 샘플 `"AT_0005382"` — 대시보드에서 이동 시 값이 달라진다(08번 문서 494행 비고). 이 값을 어떻게 확보하는지는 별도 확인 필요(orgList 응답에는 포함되지 않음). |

> ⚠️ **이 방식에는 미조치(SECURITY_SCORE neq 100) 필터가 포함되어 있지 않다.** 이 curl은 자산분류 대 카테고리 기준 **전체 조회**를 검증한 것으로, 응답에 정상/미조치 자산이 모두 섞여 반환될 가능성이 높다. Agent #1의 System Prompt에서 응답을 받은 뒤 `securityScore` 필드로 별도 후처리 필터링을 수행하도록 지시가 필요하다.

**방식 B. `mgmtOrgId` + `filter.xorStr` 기준 미조치 필터링 조회 — 08번 문서 스펙 기준 설계, 실제 curl로 미검증**

| Body 필드 | 설명 |
|---|---|
| `mgmtOrgId` | 부서 ID. 2-2단계(`orgList`)에서 확인한 `orgId` 값을 그대로 사용한다. |
| `asstType` | 자산타입. 기본값 `"SSRCCE"`를 사용한다. |
| `filter` | 미조치 필터 객체. 아래 고정 형식을 사용한다:<br>`{"xorStr": {"logic": "and", "filters": [{"field": "SECURITY_SCORE", "operator": "neq", "value": 100}]}}` |
| `page` | 현재 페이지. 기본값 `1`. |
| `pageSize` | 페이지당 항목 수. 기본값 `50`. 조직 규모가 크면 Agent가 다음 페이지를 순차 호출하도록 System Prompt에서 안내한다. |

```json
{
  "mgmtOrgId": "org_000991",
  "asstType": "SSRCCE",
  "filter": {
    "xorStr": {
      "logic": "and",
      "filters": [
        { "field": "SECURITY_SCORE", "operator": "neq", "value": 100 }
      ]
    }
  },
  "page": 1,
  "pageSize": 50
}
```

> ⚠️ **미검증**: 방식 B는 08번 문서(480~523행)의 스펙 서술과 `filter/xorStr` 조건표(525행 이하)를 근거로 설계했으나, 실제 curl 테스트로 확인된 적은 없다. `mgmtOrgId` 필드가 실제로 존재하고 정상 동작하는지, `filter` 객체 구조가 문서 서술과 정확히 일치하는지는 **IVMS 운영팀 확인 또는 별도 curl 검증이 필요**하다. 방식 A만 실증되었으므로, 캔버스 구성 시 우선 방식 A로 조회한 뒤 Agent가 `securityScore` 기준 후처리 필터링하는 접근을 권장한다.

**응답 핵심 필드(08번 문서 2.2절 기준)**: `assetList[].asstId`, `asstCode`, `chrgId`, `chrgNm`, `subChrgId`, `subChrgNm`, `mgmtOrgId`, `mgmtOrgNm`, `securityScore`, `timeEndYmd`(최근 진단일), `agentServerNm`, `hostNm`, `ipAddrStr`

---

### 2-4. API Request Tool #3 — scanResultCodeMngtDetail

> **endpoint 실제 curl로 검증 완료(2026-07-10)**: 이전에 두 차례 "검증용"이라며 제공된 curl은 모두 실제 요청 URL이 `/ivms/api/mngtListDetail`로 캡처되어(2-3절 curl이 실수로 재제출됨) endpoint 확정이 두 차례 번복되었었다. 이번에 새로 캡처된 curl은 요청 URL이 정확히 `https://ivms.lguplus.co.kr/ivms/api/scanResultCodeMngtDetail`이었고, 응답도 `scanRsltCodeList[]` 구조(총 6건)로 정상 반환되어 **`/scanResultCodeMngtDetail`이 실제 별도 endpoint임이 최종 확정됨**(08번 문서 4.2절/2115행 동일 반영). 아래 Header/Body/요청·응답 예시를 모두 이번 실제 캡처 기준으로 갱신했다.

**용도**: 2-3단계에서 확보한 자산 목록의 각 자산에 대해, 항목별(guideline별) 진단 결과 상세를 조회한다. `resultStatusCdListStr`로 `FAIL`(취약) 항목만 필터링하며, 이 응답에서 `guidelineIfKey`/`itemCode`/`agentServerNm`/`resultIfKey`/`guidelineCd`를 확보해야 다음 단계(`guidelineCdInfo`)를 호출할 수 있다.

| 항목 | 값 |
|---|---|
| 노드 라벨 | `API Request Tool: scanResultCodeMngtDetail` |
| Tool Mode | ON |
| 툴 설명 | `자산 코드(asstCode) 기준으로 취약점 항목별 상세 진단 결과를 조회하는 도구. resultStatusCdListStr에 ["FAIL"]을 지정하면 취약(미조치) 항목만 반환된다. 이 응답의 guidelineIfKey/itemCode/agentServerNm 값이 있어야 조치가이드(guidelineCdInfo)를 조회할 수 있다.` |
| URL | `https://ivms.lguplus.co.kr/ivms/api/scanResultCodeMngtDetail` (orgList와 동일 도메인) |
| Method | POST |
| Connect Timeout | 3000ms |
| Read Timeout | 10000ms |

**Header** (2-2절 `orgList`에서 curl로 검증된 공통 헤더 4종 + POST 전용 `Content-Type` 추가)

| Header Key | Header Value | 필수 |
|---|---|---|
| `X-Global-Transaction-ID` | `test` | Y |
| `X-APP-NAME` | `IVMS` | Y |
| `X-AuthorizationTime` | `20250822T135140+0900` (예시값, ⚠️ 시각 종속 — 2-2절 주의사항 참고) | Y |
| `X-Header-Authorization` | `HXm6wJzb29kQBtyWNA4bL8XInInx/jjqNJEjewosVa8JUxIbLTkmAEGC/WgrKUYLIO0w86aNIEAFcFpRUpxSWg==` (예시값, ⚠️ 시각 종속 — 2-2절 주의사항 참고) | Y |
| `Content-Type` | `application/json` | Y (POST 요청이므로 필수) |

**Body** (Tool 모드, 이번 실제 curl 캡처로 확정된 필드만 수록)

| Body 필드 | 설명 |
|---|---|
| `userId` | 요청 사용자 ID. 이번 캡처값 `"admin"`. |
| `asstCode` | 자산코드 **배열**. 이번 캡처값 `["SSRCCE3-000747", "SSRCCE3-000492"]` — 2-3단계(`mngtListDetail`) 응답의 `assetList[].asstCode` 값들을 배열로 담아 전달. |
| `hostNm` | 호스트명 **배열**. 이번 캡처값 `["lbsh1", "absdb1"]` — `asstCode`와 병행 전달됨(08번 문서 스펙에는 명시되지 않았으나 실제 호출에 사용됨이 확인됨). |
| `resultStatusCdListStr` | 점검결과 필터. 문자열로 직렬화된 배열 `"[\"FAIL\"]"` — 미조치 항목만 조회할 때 사용. |
| `vadaYn` | 자산타입 VADA 여부. 이번 캡처값 `"N"`. |
| `severity` | 취약도. 이번 캡처값 `"4"`(문자열). |
| `asstType` | 자산타입. 이번 캡처값 `"SSRCCE"`. |
| `atemplateNo` | 진단템플릿 번호. 이번 캡처값 `"151"`(문자열). |
| `page` | 현재 페이지. 이번 캡처값 `1`. |
| `pageSize` | 페이지당 항목 수. 이번 캡처값 `50`. |

> **08번 문서 스펙에는 있으나 이번 실제 호출에서는 사용되지 않은 필드**: `guidelineCdList`, `ipAddrStr`, `asstLCtgrId`/`asstMCtgrId`/`asstSCtgrId`, `asstLGroupId`/`asstMGroupId`/`asstSGroupId`, `mgmtOrgId`, `rspnMngId`, `profileNm`, `chartDashboardYn`, `guidelineCd` 등. 스펙 정의표에는 존재하지만 이번 실제 호출 예시에서는 요청 Body에 포함되지 않았음 — 필요 시 캔버스 구성 후 실제 응답을 보며 추가 필터링 파라미터로 검토.

**요청 예시(2026-07-10 실제 curl 캡처 기준)**

```json
{
  "userId": "admin",
  "asstCode": ["SSRCCE3-000747", "SSRCCE3-000492"],
  "hostNm": ["lbsh1", "absdb1"],
  "resultStatusCdListStr": "[\"FAIL\"]",
  "vadaYn": "N",
  "severity": "4",
  "asstType": "SSRCCE",
  "atemplateNo": "151",
  "page": 1,
  "pageSize": 50
}
```

**응답 예시(2026-07-10 실제 캡처, 총 6건 중 1건)**

```json
{
  "result": {
    "scanRsltCodeList": [
      {
        "asstId": "ASST_000000000104147",
        "asstCode": "SSRCCE3-000747",
        "mgmtOrgId": "org_000979",
        "asstNm": "absdb1",
        "hostNm": "absdb1",
        "asstType": "SSRCCE",
        "asstLCtgrNm": "DB",
        "asstMCtgrNm": "ALTIBASE",
        "scanIfKey": "10000001563918357",
        "resultIfKey": "156395",
        "ifKey": "7421364",
        "assetIfKey": 747,
        "profileIfKey": 1837,
        "guidelineIfKey": 81348,
        "agentServerNm": "CCE3",
        "profileNm": "2025년_점검(신규)",
        "regulationNm": "LG유플러스-기준항목(신규)",
        "guidelineCd": "ALT-203",
        "createdTime": "2025-04-07 17:08:27",
        "atemplateNo": "151",
        "itemCode": "ALT1203",
        "guidelineNm": "SYSDBA 원격 접속 제한",
        "subjectType": "DB",
        "subjectSubType": "Altibase",
        "severity": "5",
        "result": "FAIL",
        "resultNm": "취약",
        "vadaYn": "Y"
      }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

**응답 핵심 필드(2026-07-10 실제 캡처 기준)**: `scanRsltCodeList[].asstId`, `asstCode`, `guidelineIfKey`, `itemCode`, `agentServerNm`, `resultIfKey`, `guidelineCd`, `guidelineNm`, `severity`, `result`("FAIL"), `resultNm`("취약")

> 실제 응답에는 위 예시 외에도 동일 `asstCode`에 대해 `guidelineCd: ALT-E5.1`/`ALT-5.1`(둘 다 "보안 패치 적용") 등 여러 취약 항목이 `scanRsltCodeList[]` 배열에 함께 반환됨(총 6건). 다음 단계(`guidelineCdInfo`) 호출 시 이 배열의 각 항목에서 `guidelineIfKey`/`itemCode`/`agentServerNm`/`resultIfKey`를 개별적으로 추출해야 한다.

---

### 2-5. API Request Tool #4 — guidelineCdInfo

**용도**: 2-4단계에서 확보한 4개 키(`aresultNo`, `guidelineIfKey`, `itemCode`, `agentServerNm`)로 해당 미조치 항목의 조치방법(`measure`) 원문을 조회한다.

| 항목 | 값 |
|---|---|
| 노드 라벨 | `API Request Tool: guidelineCdInfo` |
| Tool Mode | ON |
| 툴 설명 | `취약점 항목의 상세 조치가이드(진단기준/현황/조치방법)를 조회하는 도구. aresultNo, guidelineIfKey, itemCode, agentServerNm 4개 값이 모두 있어야 정확한 항목이 조회된다. 이 4개 값은 scanResultCodeMngtDetail 응답에서 얻는다. 주의: 응답이 요청한 guidelineCd와 무관하게 다른 항목을 반환하는 경우가 있으므로, 응답의 guidelineCd가 원래 요청한 항목과 일치하는지 반드시 재확인해야 한다.` |
| URL | `https://ivms.lguplus.co.kr/ivms/api/guidelineCdInfo` (orgList와 동일 도메인) |
| Method | GET |
| Connect Timeout | 3000ms |
| Read Timeout | 10000ms |

**Header** (2-2절 `orgList`에서 curl로 검증된 공통 헤더 4종 — GET이므로 `Content-Type` 불필요)

| Header Key | Header Value | 필수 |
|---|---|---|
| `X-Global-Transaction-ID` | `test` | Y |
| `X-APP-NAME` | `IVMS` | Y |
| `X-AuthorizationTime` | `20250804T145618+0900` | Y (⚠️ 시각 종속 가능성 — 2-2절 주의사항 참고) |
| `X-Header-Authorization` | `kzS7dQYRUHWC7sZb1W1Q+4OzPQEwjJ1fGVMehFOEOMjXbk22ntCbdOICw7JP15d5H4fDC4fI73hOiL0SuOgGdW==` | Y (⚠️ 시각 종속 가능성 — 2-2절 주의사항 참고) |

**Query Params** (Tool 모드)

| Query Param 이름 | Query Param 설명 |
|---|---|
| `aresultNo` | 진단결과 번호(integer). 2-4단계(`scanResultCodeMngtDetail`) 응답의 `resultIfKey` 값을 사용한다. |
| `guidelineIfKey` | 항목 인터페이스키(integer). 2-4단계 응답의 `guidelineIfKey` 값을 그대로 사용한다. |
| `guidelineCd` | 항목코드(string). 2-4단계 응답의 `guidelineCd` 값을 사용한다(단, 08번 문서 4.5절 확인 결과 이 값이 응답 필터링에 실제로는 영향을 주지 않을 수 있음 — 아래 주의사항 참고). |
| `itemCode` | 시스템코드(string). 2-4단계 응답의 `itemCode` 값을 사용한다. |
| `agentServerNm` | 에이전트 서버명(string). 2-4단계 응답의 `agentServerNm` 값을 사용한다. |

**요청 예시**

```json
{
  "aresultNo": 1761644,
  "guidelineIfKey": 27741,
  "guidelineCd": "U-103",
  "itemCode": "U5110",
  "agentServerNm": "CCE1"
}
```

**응답 핵심 필드(08번 문서 4.5절 기준)**: `guidelineCdInfo.guidelineCd`, `category`, `subjectType`, `subjectSubType`, `severity`, `guidelineNm`, `criteria`(진단기준 원문), `analysisInfo`(현황 원문), `measure`(조치방법 원문), `measureDetailOrigin`(세부설정 원문)

> ⚠️ **08번 문서 4.5절에서 실제 curl 테스트로 확정된 중대 이슈**: 요청 파라미터의 `guidelineCd`를 지정해도 응답이 그 코드로 필터링되지 않고, `aresultNo`+`guidelineIfKey`+`itemCode`+`agentServerNm` 조합 기준으로 응답이 결정되는 것으로 확인됨(같은 조건 재확인 시 동일 결과 재현되어 캡처 오류가 아님을 확정). 따라서 **Agent #1의 System Prompt에 "응답의 `guidelineCdInfo.guidelineCd`가 요청한 항목과 실제로 일치하는지 재확인하라"는 방어 지시가 반드시 필요**하다(아래 2-6절 반영됨).

---

### 2-6. Agent #1A: 조직/템플릿/분류 확인

> **개정 이력(2026-07-14, Agent 분할)**: 이 절은 원래 "Agent #1: IVMS 데이터 수집" 하나로 orgList~scanResultCodeMngtDetail 5개 Tool을 모두 담고 있었으나, 컨텍스트 예산 초과(`context limit exceeded: estimated 120032 tokens > budget 100000`)로 3개 Agent(#1A/#1B/#1C)로 분할했다(0절 개정 이력 참고). 이번 절은 그중 첫 번째로, 자산 목록/취약점 상세처럼 응답 건수가 큰 Tool은 다루지 않고 조직·템플릿·분류 확인만 담당한다.
>
> **개정 이력(2026-07-14, 재작성 — 전체 일관성 점검)**: 이 절의 System Prompt가 7.2절("2단계 전용" 버전)과 `userId` 값(`hhosung` vs `admin`)·`assetCategory` 응답 파싱 방식(`selectedCategory.asstType` vs `asstCtgrList[]`)에서 서로 달랐던 불일치를 발견해 **7.2절 버전(`userId="admin"`, `asstCtgrList[]` 파싱)으로 통일**했다 — 08번 문서 1.3절 실제 스펙에 `selectedCategory` 필드가 없고 응답이 항상 `asstCtgrList[]` 배열이므로 이 쪽이 맞다(2-2-3절 참고). 아울러 이 절에서만 언급되고 정식 스펙이 없던 `assetSsrcceTemplate`/`assetCategory` 두 Tool의 URL/Method/Header/Query Params는 2-2-2절/2-2-3절로 신설 이관했다.

| 항목 | 값 |
|---|---|
| 노드 라벨 | `Agent #1A: 조직/템플릿/분류 확인` |
| Input | Chat Input `User Message` 연결 |
| Tools | API Request Tool(orgList, 2-2절), API Request Tool(assetSsrcceTemplate, 2-2-2절), API Request Tool(assetCategory, 2-2-3절) — 3개 연결 |
| Jailbreak Check | OFF (내부 API 연동 전용) |
| Model | `azure_openai:gpt-4.1-mini` (Tool 3개, 응답 크기가 작아 상향 불필요) |

**System Prompt Template (전체 원문)**

```
사용자가 입력한 조직명과 일치하는 조직을 찾을 때까지 orgList를 호출한다.
- 처음에는 pOrgId="org_000001"(최상위)로 시작해 orgType을 "1"(부문)부터 순차 조회한다.
- 응답의 orgList[].orgNm이 사용자가 언급한 조직명과 일치하면 그 orgList[].orgId를 확정한다.
- 일치하는 조직이 없으면 응답의 orgId를 다음 pOrgId로 사용해 하위 레벨(orgType "2"→"3"→"4")로
  재귀 조회한다. 최대 4단계(부문→그룹→담당→팀)까지만 순회하고, 그래도 없으면
  "해당 조직명을 찾을 수 없습니다: "라고 쓰고 바로 뒤에 사용자가 입력한 조직명을 이어서 응답한다.
- 여러 개의 유사한 조직명이 나오면 사용자에게 확인을 요청하지 말고, 가장 정확히 일치하는
  1건을 선택한다(모호하면 정확 일치 우선, 없으면 부분 일치 중 첫 번째).

조직의 orgId를 확정했으면 이어서 assetSsrcceTemplate과 assetCategory를 호출한다.
- assetSsrcceTemplate은 userId="admin"으로 호출해 templateList[]를 받는다. 첫 번째
  항목의 atemplateNo를 templateNo로 사용한다.
- assetCategory는 userId="admin", asstCtgrLevel="L"로 호출해 asstCtgrList[]를 받는다.
  이 목록에서 asstType 값을 확인한다(여러 개면 첫 번째 값을 사용).
- templateNo와 asstType은 반드시 이 두 API의 응답값을 사용한다. 임의로 지어내거나
  생략하지 않는다.

마지막으로 확정한 값을 다음 형식으로 명확히 출력한다(각 줄의 콜론 뒤에 실제 확정된
값을 그대로 적는다). 다른 설명은 덧붙이지 않는다.

orgId: (확정된 orgId 값)
templateNo: (확정된 templateNo 값)
asstType: (확정된 asstType 값)
```

---

### 2-7. Agent #1B: 담당자 목록 경량 스캔

> **2026-07-14 3차 개정**: 기존에는 이 Agent가 자산 상세까지 한 번에 수집했으나, 자산 건수가 많은 조직에서 페이지네이션 반복 누적으로 컨텍스트 예산을 초과하는 문제가 재발했다. 이에 따라 이 Agent는 **"담당자 목록만 가볍게 추출"**하는 역할로 재정의하고, 자산 상세 수집은 뒤이은 **Agent #1B-2**(2-7-2절)로 분리했다.

| 항목 | 값 |
|---|---|
| 노드 라벨 | `Agent #1B: 담당자 목록 경량 스캔` |
| Input | Agent #1A `Response` 연결 |
| Tools | API Request Tool(mngtListDetail) — 1개 연결 |
| Jailbreak Check | OFF (내부 API 연동 전용) |
| Model | `azure_openai:gpt-4.1` (페이지네이션 반복 호출 필요, 응답 다수) |

**System Prompt Template (전체 원문)**

```
입력으로 이전 단계가 확정한 orgId, templateNo, asstType 값을 텍스트로 받는다. 이 값을
그대로 파싱해 사용하고, 임의로 다른 값을 지어내거나 재확인을 위해 orgList 등을 다시
호출하지 않는다.

이 단계의 목적은 자산 상세가 아니라 "담당자 목록"만 가볍게 추출하는 것이다. 받은 orgId,
templateNo, asstType으로 mngtListDetail을 호출한다.
- mngtListDetail 호출 시 userId, asstType, templateNo, asstLCtgrId, diagYear, page,
  pageSize, mgmtOrgId, filter 9개 파라미터만 사용한다. page는 숫자 1, pageSize는 숫자 200으로
  integer 타입으로 넣는다(⚠️ 반드시 200 이상 큰 값을 사용 — 작은 값을 쓰면 자산 건수가 많은
  조직에서 페이지 반복 호출 횟수가 급증해 컨텍스트 예산 초과가 발생한다). mgmtOrgId는
  입력받은 orgId 값을 그대로 사용한다.
- ⚠️ 응답 assetList[]에서 반드시 chrgId, chrgNm(담당자 정보) 두 필드만 추출한다. asstNm,
  asstCode, hostNm, securityScore, timeEndYmd 등 자산 상세 필드는 절대 응답에 포함하거나
  기억하지 않는다(다음 페이지 처리 후 즉시 버린다) — 이 필드들을 누적하면 이전과 동일하게
  컨텍스트 예산을 초과하므로, 오직 "담당자가 누구인지"만 남긴다.
- chrgId 값이 이미 수집한 목록에 있으면 다시 추가하지 않고, 새로운 chrgId만 (chrgId, chrgNm)
  쌍으로 유니크 목록에 누적한다.
- 응답 건수가 pageSize(200)와 같으면 다음 페이지가 있을 수 있으므로, page를 1씩 증가시켜
  전체 자산을 모두 훑을 때까지 반복 호출한다. 단, 반복 호출 5회(총 1000건)를 넘어서면 더 이상
  반복하지 말고, 그때까지 수집한 담당자 목록만으로 응답을 구성하며 응답 맨 앞에
  "⚠️ 자산 건수가 많아 일부 담당자만 스캔했습니다(최대 1000건)"라고 명시한다.
- chrgId, chrgNm이 둘 다 비어 있는 자산이 하나라도 있으면, 담당자 목록과는 별도로
  "담당자 미배정 자산 존재" 플래그를 응답에 포함한다(그 자산의 상세는 이 단계에서 다루지 않는다).

마지막으로 수집한 담당자 목록(chrgId, chrgNm 쌍의 표)과 "담당자 미배정 자산 존재 여부"를
출력한다. orgId, templateNo, asstType 값도 다음 단계에서 필요하므로 응답 맨 앞에 그대로
포함한다(다음 형식으로 각 줄에 실제 값을 적는다: "orgId: (값)", "templateNo: (값)",
"asstType: (값)"). 자산 상세 필드는 어떤 경우에도 이 응답에 포함하지 않는다.
```

---

### 2-7-2. Agent #1B-2: 담당자별 자산 정밀조회

> **2026-07-14 3차 개정 신설**: Agent #1B가 넘긴 담당자 목록을 순회하며, 담당자 1인 단위로 `mngtListDetail`을 `rspnMngId`로 좁혀 재호출한다. 담당자 단위로 스코프를 좁히면 1회 호출당 응답 건수가 조직 전체보다 훨씬 작아 페이지네이션 반복이 크게 줄어든다.
>
> ⚠️ **확인 필요**: 이 API Request Tool(`mngtListDetail`) 노드를 Agent #1B와 Agent #1B-2가 동일 노드로 공유 연결할 수 있는지, 아니면 별도로 복제 배치해야 하는지 `04-ixi-enterprise-node-catalog.md`로 명확히 확정되지 않았다. 캔버스에서 실제로 시도해보고, 공유 연결이 되지 않으면 동일한 URL/Method/Header/Body 스펙으로 Tool 노드를 하나 더 복제해 이 Agent에 연결한다.

| 항목 | 값 |
|---|---|
| 노드 라벨 | `Agent #1B-2: 담당자별 자산 정밀조회` |
| Input | Agent #1B `Response` 연결 |
| Tools | API Request Tool(mngtListDetail) — 1개 연결(Agent #1B와 공유 또는 복제, 위 확인 필요 참고) |
| Jailbreak Check | OFF (내부 API 연동 전용) |
| Model | `azure_openai:gpt-4.1` (담당자 단위로 스코프가 좁아 #1B보다는 가볍지만, 페이지네이션 반복 가능성은 여전히 있음) |

**System Prompt Template (전체 원문)**

```
입력으로 이전 단계가 정리한 담당자 목록(chrgId, chrgNm 쌍의 표), "담당자 미배정 자산
존재 여부", orgId, templateNo, asstType 값을 텍스트로 받는다. 이 값을 그대로 파싱해
사용하고, 임의로 다른 값을 지어내거나 이전 단계를 다시 호출하지 않는다.

받은 담당자 목록을 순회하며, 담당자별로 mngtListDetail을 호출해 그 담당자 소유 자산의
상세를 수집한다.
- mngtListDetail 호출 시 userId, asstType, templateNo, asstLCtgrId, diagYear, page,
  pageSize, mgmtOrgId, rspnMngId, filter 10개 파라미터를 사용한다. mgmtOrgId는 입력받은
  orgId 값을 그대로 사용하고, rspnMngId에는 현재 순회 중인 담당자의 chrgId 값을 넣는다.
  page는 숫자 1, pageSize는 숫자 200으로 integer 타입으로 넣는다.
- 응답 assetList[] 중 asstNm, asstCode, hostNm, securityScore, timeEndYmd를 추출해 현재
  담당자(chrgId, chrgNm)의 자산 목록으로 정리한다.
- 한 담당자의 응답 건수가 pageSize(200)와 같으면 다음 페이지가 있을 수 있으므로, page를
  1씩 증가시켜 그 담당자의 자산을 모두 수집할 때까지 반복한다. 단, 한 담당자당 반복 호출
  3회(총 600건)를 넘어서면 더 이상 반복하지 말고, 그 담당자 항목 옆에 "⚠️ 이 담당자의 자산
  건수가 많아 일부만 조회했습니다(최대 600건)"라고 명시한 뒤 다음 담당자로 넘어간다.
- ⚠️ 서버가 rspnMngId/mgmtOrgId 필터를 완벽히 적용하지 않을 수 있다. assetList[] 각 항목의
  mgmtOrgId가 요청에 사용한 mgmtOrgId 값과 다르거나 비어 있으면, 그 자산은 이후 단계
  (scanResultCodeMngtDetail 호출 및 최종 출력)에서 제외한다. 임의로 값을 채우거나 추측하지 않는다.
- 담당자 목록을 모두 순회한 뒤, 이전 단계에서 "담당자 미배정 자산 존재"로 표시되었다면
  rspnMngId 파라미터 없이 mgmtOrgId만으로 mngtListDetail을 1회 더 호출하고, 응답 assetList[]
  중 chrgId와 chrgNm이 둘 다 비어 있는 자산만 걸러내 "담당자 미배정"이라는 별도 그룹으로
  포함한다. 이 추가 호출도 page 반복 시 3회(총 600건) 상한을 동일하게 적용한다.

마지막으로 담당자별로 asstNm, asstCode, hostNm, securityScore, timeEndYmd를 표 형식으로
정리해 출력한다(담당자 미배정 그룹 포함). orgId, templateNo, asstType 값도 다음 단계에서
필요하므로 응답 맨 앞에 그대로 포함한다(다음 형식으로 각 줄에 실제 값을 적는다:
"orgId: (값)", "templateNo: (값)", "asstType: (값)").
```

---

### 2-8. Agent #1C: 취약점 상세 수집

| 항목 | 값 |
|---|---|
| 노드 라벨 | `Agent #1C: 취약점 상세 수집` |
| Input | Agent #1B-2 `Response` 연결 |
| Tools | API Request Tool(scanResultCodeMngtDetail) — 1개 연결 |
| Jailbreak Check | OFF (내부 API 연동 전용) |
| Model | `azure_openai:gpt-4.1` (페이지네이션 반복 호출 필요, 응답 다수) |

**System Prompt Template (전체 원문)**

```
입력으로 이전 단계가 정리한 담당자별 자산 표(asstNm, asstCode, hostNm, securityScore,
timeEndYmd)와 orgId, templateNo, asstType 값을 텍스트로 받는다. 이 값을 그대로 파싱해
사용하고, 임의로 다른 값을 지어내거나 이전 단계를 다시 호출하지 않는다.

담당자별 자산 목록에서 asstCode와 hostNm을 각각 배열로 추출해 scanResultCodeMngtDetail을
호출한다.
- asstCode와 hostNm은 반드시 같은 순서로 대응하도록 함께 전달한다(asstCode만 또는
  hostNm만 전달하지 않는다).
- resultStatusCdListStr은 반드시 문자열 "[\"FAIL\"]"로 지정해 취약(미조치) 항목만 조회한다.
- asstType은 입력받은 값을 그대로 사용하고, vadaYn은 "N"으로 고정한다.
- severity는 "4", atemplateNo는 입력받은 templateNo 값을 그대로 사용한다.
- userId는 "hhosung", page는 숫자 1, pageSize는 숫자 200으로 integer 타입으로 넣는다(⚠️ 반드시
  200 이상 큰 값을 사용 — 작은 값을 쓰면 항목 수가 많을 때 페이지 반복 호출 횟수가 급증해
  컨텍스트 예산 초과가 발생한다. 2026-07-14 Agent #1B에서 실제 확인된 오류 원인과 동일한
  구조적 위험이므로 Agent #1C에도 동일하게 적용).
- 응답 scanRsltCodeList[]에서 asstId, asstCode, guidelineIfKey, itemCode, agentServerNm,
  resultIfKey, guidelineCd, guidelineNm, severity, result를 반드시 추출해 보관한다.
- ⚠️ severity="4"로 요청했지만 응답에 severity가 다른 값인 항목이 포함될 수 있다. 응답
  scanRsltCodeList[]에서 severity가 "4"가 아닌 항목은 최종 결과에서 제외한다. 임의로
  값을 수정하거나 포함시키지 않는다.
- 자산 수가 많아 한 번에 조회되지 않으면 asstCode/hostNm을 나누어 여러 번 호출한다(page를
  늘려가며 반복). 단, 반복 호출 3회(총 600건)를 넘어서면 더 이상 반복하지 말고, 그때까지
  수집한 항목만으로 응답을 구성하며 응답 맨 앞에 "⚠️ 항목 수가 많아 일부만 조회했습니다
  (최대 600건)"라고 명시한다(전체를 다 모으려다 컨텍스트 예산을 다시 초과하는 것을 방지).
- 조치가이드 조회는 이번 단계에서 하지 않는다.

마지막으로 담당자별로 asstId, asstCode, guidelineIfKey, itemCode, agentServerNm,
resultIfKey, guidelineCd, guidelineNm, severity, result를 표로 정리해 출력한다.
담당자 배정 정보(asstNm, hostNm, securityScore, timeEndYmd 등 이전 단계에서 넘어온 항목)도
함께 유지해 다음 Agent가 자산-취약점을 매핑할 수 있게 한다.
```

---

### 2-9. Agent #2: 담당자별 압박메시지+조치가이드 생성

| 항목 | 값 |
|---|---|
| 노드 라벨 | `Agent #2: 담당자별 압박메시지+조치가이드 생성` |
| Input | Agent #1C `Response` 연결 |
| Tools | 연결 없음 |
| Jailbreak Check | OFF |
| Model | `azure_openai:gpt-4.1-mini` |

**System Prompt Template (전체 원문)**

> **개정 이력(2026-07-14)**: 최초 원문은 출력 형식을 `{hostNm}`, `{담당자명}` 같은 중괄호
> 표현으로 지시했다. 그런데 04번 문서(Template Message 노드, 91~93행)의 "중괄호 안에
> 변수명을 넣으면 프롬프트 변수로 인식된다"는 규칙이 Agent 노드의 System Prompt Template에도
> 동일하게 적용되어, 캔버스에서 이 표현들이 실제 입력 슬롯(hostNm, ipAddrStr, guidelineCd,
> guidelineNm, severity 등)으로 자동 생성되는 것이 실제 확인되었다. 이 슬롯을 비워둔 채
> 실행하면 System Prompt 자체가 빈 값으로 렌더링되어, Agent #2가 Agent #1C의 실제 Input
> 데이터를 무시하고 "원시 데이터가 필요하다"고 응답하는 오류로 이어졌다. 아래 원문은
> 중괄호 표현을 모두 서술형으로 치환해 이 문제를 제거한 버전이다.

```
당신은 IVMS 미조치 취약점 데이터를 바탕으로, 담당자별 압박 메시지와 조치가이드
요약을 작성하는 에이전트다. 입력으로 Agent #1C가 수집한 담당자별 원시 데이터를 받는다.

【미조치 판단 및 선별 기준】
- 최근진단일(timeEndYmd) 기준 오늘 날짜와 비교해 경과일이 7일 이상인 항목만
  "압박 대상 미조치 항목"으로 선별한다. 경과일이 7일 미만인 항목은
  "조치 유예 기간"으로 간주해 이번 메시지에서 제외한다(단, 완전히 숨기지 않고
  "유예 기간 중" 항목 수만 별도로 한 줄 언급한다).
- severity(취약도: 1=최하 ~ 5=최상)가 높은 항목을 먼저 표기한다(내림차순 정렬).
- Agent #1C가 "조치가이드 조회 실패(응답 불일치)"로 표시한 항목은 조치방법 없이
  "조치가이드 조회 실패 — 수동 확인 필요"라고만 표기하고, 임의로 다른 항목의
  조치방법을 대신 채워 넣지 않는다.

【출력 구조 — 담당자가 N명이면 N개 섹션】
담당자마다 아래 두 부분으로 구성된 섹션을 하나씩 작성한다.

=== 담당자명(담당자ID) ===  (실제 담당자명과 담당자ID 값으로 치환해 작성. 예: === 홍길동(user_001) ===)

[1] 압박 메시지
- 그 담당자의 미조치 항목 총 건수(이 중 심각도 상 이상인 건수를 괄호로 병기)와
  경과일 최댓값을 명시해, 방치되어 있음을 안내하는 정중하지만 명확한 문구를
  2~3문장으로 작성한다.
- 유예 기간 중인 항목이 있으면 "별도로 N건은 조치 유예 기간(7일 미만)이라
  이번 안내에서는 제외했습니다"라고 덧붙인다(N은 실제 건수).

[2] 조치가이드 요약
아래 표 형식으로 미조치 항목을 severity 내림차순으로 나열한다. 표의 각 행은
Agent #1C 원시 데이터의 다음 값들로 채운다: 자산의 hostNm/ipAddrStr(호스트/IP),
guidelineCd(항목코드), guidelineNm(항목명), severity(심각도), 경과일(오늘 날짜와
timeEndYmd의 차이), 조치방법 요약(measure 원문에서 【조치방법】 섹션만 발췌하고,
없으면 measure 전체 앞부분을 요약).

| 자산(호스트/IP) | 항목코드 | 항목명 | 심각도 | 경과일 | 조치방법 요약 |
|---|---|---|---|---|---|
| (값) | (값) | (값) | (값) | (값)일 | (값) |

표 아래에 "상세 조치가이드가 필요하면 항목코드를 알려주시면 원문 전체를 안내해
드립니다"라는 안내 문구를 한 줄 추가한다.

【전체 출력 마무리】
모든 담당자 섹션을 순서대로(조치 필요 건수가 많은 담당자 우선) 나열한 뒤,
맨 마지막에 "총 N명, 총 미조치 M건에 대한 안내입니다. 승인해 주시면 이 내용
그대로 보안담당자에게 전달됩니다."라는 요약 문구를 추가한다(N, M은 실제 값).
```

---

### 2-10. Human Approval

| 항목 | 값 |
|---|---|
| Target Message | Agent #2 `Response` 연결 |
| question | `"위 담당자분들의 압박메시지 및 조치가이드를 이 내용 그대로 승인하시겠습니까?"` (고정 문자열 입력 — 노드 연결 아님, 직접 텍스트 입력) |
| Model | `azure_openai:gpt-4.1-mini` |

> 09번 문서 2절 요구사항("N명분의 결과물을 하나로 통합해 1회 승인")에 따라, 담당자별 개별 승인이 아닌 전체 통합 승인 1회로 구성한다.

---

### 2-11. Language Model (승인 후 패스스루)

| 항목 | 값 |
|---|---|
| Input | Human Approval `Human Approval` 포트 연결 |
| Model | `azure_openai:gpt-4.1-mini` |

**System Prompt Template (전체 원문)**

```
당신은 승인된 내용을 그대로 사용자에게 전달하는 패스스루 역할만 수행한다.
입력된 내용을 요약하거나 재작성하거나 첨언하지 말고, 입력받은 텍스트를
그대로(승인 여부 표시만 맨 앞에 추가하여) 출력한다.

- 승인된 경우: "[승인 완료]"를 맨 앞에 붙이고 입력 내용 전체를 그대로 출력한다.
- 거절된 경우: "[거절됨] 요청하신 내용은 승인되지 않아 발송되지 않습니다."만 출력하고
  원본 내용은 다시 출력하지 않는다.
```

> ⚠️ 이 노드는 `04-ixi-enterprise-node-catalog.md` 674/679행 제약(Human Approval 출력 → Chat Output 직접 연결 불가)을 우회하기 위한 필수 경유 노드다. `07-ixi-enterprise-requirements-spec.md` REQ-002가 향후 구현되면 이 노드는 생략 가능하다.

---

### 2-12. Chat Output

- **Input**: Language Model `Response` 연결
- ⚠️ **연결 방향 주의**: Language Model의 `Response` 포트에서 드래그하면 Chat Output이 목록에 나타나지 않는다(04번 문서 151행). 반드시 **Chat Output 노드의 `Input` 포트 쪽에서 드래그를 시작**해 Language Model을 선택할 것.

---

## 3. 전체 연결 순서 요약표

> **개정 이력(2026-07-14, Agent 분할)**: 컨텍스트 예산 초과 문제로 Agent #1을 #1A/#1B/#1C 3개로 분할했다(0절 개정 이력 참고). 아래 표는 분할 후 구조 기준이다.
>
> **개정 이력(2026-07-14, 3차 — #1B-2 추가)**: Agent #1B의 페이지네이션 반복 누적 문제가 재발해, #1B를 "경량 스캔"으로 재정의하고 그 뒤에 **Agent #1B-2(담당자별 자산 정밀조회)**를 신설했다(2-7절/2-7-2절 참고). 아래 표는 #1B-2 추가 후 구조 기준이다.

| 순서 | From (출력 포트) | To (입력 포트) | 비고 |
|---|---|---|---|
| 1 | Chat Input → `User Message` | Agent #1A → `Input` | 파란 점선 |
| 2 | API Request Tool(`orgList`) → `Tool` | Agent #1A → `Tools` | 빨간, 다중 연결 |
| 3 | API Request Tool(`assetSsrcceTemplate`) → `Tool` | Agent #1A → `Tools` | 동일 포트에 추가 연결 |
| 4 | API Request Tool(`assetCategory`) → `Tool` | Agent #1A → `Tools` | 동일 포트에 추가 연결 |
| 5 | Agent #1A → `Response` | Agent #1B → `Input` | 파란 점선, 컨텍스트 분리 지점 |
| 6 | API Request Tool(`mngtListDetail`) → `Tool` | Agent #1B → `Tools` | 빨간 |
| 7 | Agent #1B → `Response` | Agent #1B-2 → `Input` | 파란 점선, 컨텍스트 분리 지점(신설) |
| 8 | API Request Tool(`mngtListDetail`) → `Tool` | Agent #1B-2 → `Tools` | 빨간, Agent #1B와 공유 또는 복제(⚠️ 확인 필요, 2-7-2절 참고) |
| 9 | Agent #1B-2 → `Response` | Agent #1C → `Input` | 파란 점선, 컨텍스트 분리 지점 |
| 10 | API Request Tool(`scanResultCodeMngtDetail`) → `Tool` | Agent #1C → `Tools` | 빨간 |
| 11 | Agent #1C → `Response` | Agent #2 → `Input` | 파란 점선, 컨텍스트 분리 지점 |
| 12 | Agent #2 → `Response` | Human Approval → `Target Message` | 파란, 필수 포트 |
| 13 | Human Approval → `Human Approval` | Language Model → `Input` | Chat Output 직결 불가 → 경유 필수 |
| 14 | Language Model → `Response` | Chat Output → `Input` | **Chat Output 쪽에서 드래그 시작** |

> `guidelineCdInfo`(4단계, 7.4절)는 아직 미검증 상태라 위 표에 포함하지 않았다. 검증 후 추가할 때는 Agent #1C의 Tools 포트에 4번째로 얹을지, Agent #1D를 신설해 #1C→#1D로 연결할지 그 시점의 컨텍스트 사용량을 보고 판단한다.

---

## 4. 완성된 구조도

> **개정 이력(2026-07-14, 3차)**: Agent #1B의 반복 누적 문제 재발로 #1B를 "경량 스캔"으로 재정의하고 Agent #1B-2(담당자별 정밀조회)를 추가했다. 아래는 갱신된 구조도다.
>
> **개정 이력(2026-07-14, 재작성 — 누락 보완)**: 이 구조도에 `guidelineCdInfo` Tool이 누락되어 있었다(5절 Tool 개수 표, 7.4절, 2-8절 최종본과 불일치). 7.4절 결정대로 Agent #1C의 Tools에 `scanResultCodeMngtDetail`과 함께 2번째로 추가했다 — 단 `guidelineCdInfo`는 0절 개정 이력 기준으로 아직 미검증 상태다.

```
[Chat Input]
     │ User Message
     ▼
[Agent #1A: 조직/템플릿/분류 확인] ←Tools← [API Req: orgList]
     │                                     [API Req: assetSsrcceTemplate]
     │                                     [API Req: assetCategory]
     │ Response
     ▼
[Agent #1B: 담당자 목록 경량 스캔] ←Tools← [API Req: mngtListDetail]
     │ Response (chrgId/chrgNm 목록만, 자산 상세 제외)
     ▼
[Agent #1B-2: 담당자별 자산 정밀조회] ←Tools← [API Req: mngtListDetail] (공유 또는 복제, ⚠️ 확인 필요)
     │ Response (담당자별 자산 상세)
     ▼
[Agent #1C: 취약점 상세 수집] ←Tools← [API Req: scanResultCodeMngtDetail]
     │                                [API Req: guidelineCdInfo] (⚠️ 미검증, 7.4절)
     │ Response
     ▼
[Agent #2: 담당자별 압박메시지+조치가이드 생성]
     │ Response
     ▼
[Human Approval]  (question: "위 N명분 ... 승인하시겠습니까?")
     │ Human Approval
     ▼
[Language Model]  (패스스루)
     │ Response
     ▼
[Chat Output]
```

---

## 5. `10`번 문서와의 차이점 요약

> **개정 이력(2026-07-14, 재작성 — 전체 일관성 점검)**: 아래 표는 최초 재설계(0절 4단계 API 체이닝) 시점 기준이었으나, 이후 Agent 분할(#1A/#1B/#1B-2/#1C)과 `assetSsrcceTemplate`/`assetCategory` 추가를 반영하지 않아 "API Request Tool 개수"가 실제(6개)와 맞지 않았다. 최종 구조 기준으로 갱신했다.

| 구분 | `10`번 문서 (기존) | 본 문서 (`11`번, 최종 구조 기준) |
|---|---|---|
| API Request Tool 개수 | 4개 (orgList, asstChrgInfo, mngtListDetail, guidelineCdInfo) | **6개** (orgList, assetSsrcceTemplate, assetCategory, mngtListDetail, scanResultCodeMngtDetail, guidelineCdInfo) — `asstChrgInfo` 제외, `assetSsrcceTemplate`/`assetCategory`/`scanResultCodeMngtDetail` 추가. 단 `guidelineCdInfo`(7.4절)는 아직 미검증 상태(0절 개정 이력 참고)이며, 6개 모두 Agent #1A/#1B/#1B-2/#1C 4개 Agent에 분산 연결된다(4절 구조도 참고) |
| Agent 구성 | Agent #1 단일 노드 | Agent #1A(조직/템플릿/분류) → #1B(담당자 경량 스캔) → #1B-2(담당자별 정밀조회) → #1C(취약점 상세+조치가이드) 4개로 분할(0절 개정 이력 참고 — 컨텍스트 예산 초과 대응) |
| 담당자 목록 획득 방법 | `asstChrgInfo`로 orgId 기준 별도 조회(불가능한 방식 — API가 자산 단위) | `mngtListDetail` 응답의 `chrgId`/`chrgNm` 필드에서 Agent #1B가 경량 스캔으로 추출, Agent #1B-2가 담당자별 `rspnMngId`로 정밀조회 |
| `guidelineCdInfo` 호출 전 단계 | 없음(파라미터 출처 불명확) | `scanResultCodeMngtDetail`에서 `aresultNo`(=resultIfKey)/`guidelineIfKey`/`itemCode`/`agentServerNm` 확보 후 호출 |
| System Prompt 상세도 | 요약 수준(4줄 내외) | 단계별 파라미터 매핑, 페이지네이션, 응답 불일치 방어 로직까지 전체 원문 포함 |
| URL | `{IVMS_BASE_URL}` 플레이스홀더만 표기 | 정확한 엔드포인트 경로 + Header/Query/Body 전체 필드 명시 |

---

## 6. 구성 후 확인 체크리스트 (플로우 A 전용)

> **개정 이력(2026-07-14, Agent 분할)**: Agent #1 분할(#1A/#1B/#1C)에 맞춰 체크리스트를 갱신했다.
>
> **개정 이력(2026-07-14, 3차 — #1B-2 추가)**: Agent #1B를 경량 스캔/#1B-2 정밀조회로 재분할한 구조에 맞춰 체크리스트를 갱신했다.

- [ ] Agent #1A/#1B/#1B-2/#1C 각각의 Tools 포트에 올바른 Tool만 연결되었는지 확인 — #1A에는 `orgList`/`assetSsrcceTemplate`/`assetCategory` 3개만, #1B와 #1B-2에는 각각 `mngtListDetail`이 연결되어 있는지(같은 Tool 노드를 공유 연결했는지, 아니면 복제 배치했는지 실제 캔버스에서 확인 — 2-7-2절 "⚠️ 확인 필요" 참고), #1C에는 `scanResultCodeMngtDetail` 1개만(다른 Agent의 Tool을 잘못 연결하지 않았는지 재확인) — `asstChrgInfo`는 어느 Agent에도 연결하지 않음
- [ ] Agent #1A → #1B → #1B-2 → #1C → #2 순서로 `Response`→`Input` 연결이 올바르게 되어 있는지 확인(역방향 연결이나 건너뛰기 없는지, #1B에서 #1C로 바로 건너뛰지 않았는지)
- [ ] Agent #1B의 실제 응답에 자산 상세 필드(asstNm/asstCode/hostNm/securityScore/timeEndYmd)가 섞여 나오지 않고 담당자 목록(chrgId/chrgNm)만 나오는지 확인 — 섞여 나오면 System Prompt가 자산 상세를 버리지 못하고 있다는 신호
- [ ] Agent #1B-2가 담당자별로 개별 호출(`rspnMngId` 파라미터 사용)하고 있는지, 담당자 미배정 그룹도 별도로 처리되는지 실제 응답으로 확인
- [ ] 각 API Request Tool이 Tool Mode ON 상태인지 확인
- [ ] `mngtListDetail`, `scanResultCodeMngtDetail`의 Method가 POST로 설정되었는지 확인(GET으로 잘못 설정하기 쉬움)
- [ ] 각 Agent 실행 시 `context limit exceeded` 오류가 재발하지 않는지 확인 — 재발 시(특히 Agent #1B의 1차 경량 스캔 단계에서) 방법 3(외부 배치 스크립트 분리)을 검토
- [ ] Human Approval → Language Model → Chat Output 경유 구조 확인(직결 시도 금지)
- [ ] Chat Output은 Chat Output 쪽에서 드래그해 Language Model과 연결했는지 확인
- [ ] `{IVMS_BASE_URL}` 플레이스홀더를 실제 도메인으로 교체했는지 확인(IVMS 운영팀 확인 후)
- [ ] 인증 헤더 4종의 **키가 등록되어 있는지**(값은 빈 값으로 두면 됨 — 2026-08-18 정상 응답 확인, 1절 참고). `{IVMS_API_TOKEN}` 토큰 발급은 현 환경에서 불필요함이 확인되어 체크 항목에서 제외

> `guidelineCdInfo` 관련 체크 항목(Query Params 5개 필드, 응답 불일치 방어 로직)은 해당 Tool이 아직 미검증 상태이므로 이 체크리스트에서 제외했다. 7.4절 검증 완료 후 추가한다.

---

## 7. 단계적 구성(Staged Build) 가이드

### 7.0 왜 단계적으로 구성하는가

ixi-enterprise에는 단일 노드 독립 실행(Test Step), Pin Data, Execution Log, Input/Output 확인 패널이 없다(`07-ixi-enterprise-requirements-spec.md` REQ-009~012). 즉 노드를 하나 추가할 때마다 **Chat Input부터 전체 플로우를 재실행**해야만 그 노드가 제대로 동작하는지 확인할 수 있다. 이 제약 때문에 4개 API Request Tool을 한 번에 다 연결하고 System Prompt도 4단계를 한꺼번에 작성한 뒤 처음 실행하면, 실패했을 때 원인이 어느 Tool/어느 프롬프트 단락에 있는지 특정하기 어렵다.

따라서 본 절에서는 2절의 최종 구성을 **6단계로 쪼개어 순서대로 쌓아 올리는 방식**을 제시한다. 각 단계는 "그 시점까지 연결된 노드만으로 실행 가능한 최소 플로우"이며, 다음 단계로 넘어가기 전에 반드시 전체 실행으로 검증한다.

| 단계 | 이번 단계에서 추가하는 것 | 임시 종착점 |
|---|---|---|
| 1단계 | Chat Input, Agent #1A(Tool: `orgList` 1개만), Chat Output | Chat Output |
| 2단계 | Agent #1A에 `assetSsrcceTemplate`/`assetCategory` 추가, 신규 Agent #1B(경량 스캔)에 `mngtListDetail` 연결, #1A→#1B 연결 추가 | Chat Output(동일, #1B에서 임시 수신) |
| 2-2단계 | 신규 Agent #1B-2(담당자별 정밀조회)에 `mngtListDetail` 연결(공유 또는 복제), #1B→#1B-2 연결 추가 | Chat Output(동일, #1B-2에서 임시 수신) |
| 3단계 | 신규 Agent #1C에 `scanResultCodeMngtDetail` 연결, #1B-2→#1C 연결 추가 | Chat Output(동일, #1C에서 임시 수신) |
| 4단계 | `guidelineCdInfo` Tool 추가(Agent #1C에 얹을지 Agent #1D를 신설할지는 검증 시점에 판단) | Chat Output(동일) |
| 5단계 | Agent #2, Human Approval, Language Model을 Chat Output 앞에 끼워 넣어 최종 구조 완성 | Chat Output(최종) |

> **개정 이력(2026-07-14, 컨텍스트 예산 초과)**: Agent #1 하나에 5개 Tool을 전부 연결해 실행하자 `context limit exceeded: estimated 120032 tokens > budget 100000` 오류가 발생해, Agent를 #1A/#1B/#1C 3개로 분할했다(0절 개정 이력 참고). 이 분할 자체도 단계적으로 검증한다 — 2단계에서 #1B를, 3단계에서 #1C를 새로 만들며 그때마다 전체 플로우를 재실행해 컨텍스트 예산 오류가 재발하지 않는지 확인한다.
>
> **개정 이력(2026-07-14, 3차 — #1B-2 단계 추가)**: pageSize 상향 후에도 Agent #1B에서 오류가 재발해, #1B를 "경량 스캔"으로 재정의하고 담당자별 정밀조회를 담당하는 **Agent #1B-2**를 별도 단계(2-2단계)로 추가했다. 기존 2단계는 #1B(경량 스캔)까지만 구성하고, #1B-2는 그 다음 별도 단계에서 추가한다(7.2절/7.2-2절 참고).

각 단계의 상세 구성은 이후 절에서 순서대로 다룬다. 본 문서에서는 우선 **1단계**만 작성한다.

---

### 7.1 [1단계] Chat Input → Agent #1A(orgList만) → Chat Output

**목표**: 사용자가 조직명을 말하면 Agent #1A가 `orgList` Tool만으로 해당 조직의 `orgId`를 찾아 응답하는지 확인한다. 담당자/미조치/가이드 로직은 아직 다루지 않는다.

**배치할 노드 (3개)**

| 노드 | 라벨 |
|---|---|
| Chat Input | 기본값 |
| Agent | `Agent #1A: 조직/템플릿/분류 확인` |
| Chat Output | 기본값 |

> ⚠️ 최종 구성(2절)에는 Agent #1A 뒤에 Agent #1B → Agent #1B-2 → Agent #1C → Agent #2 → Human Approval → Language Model → Chat Output이 이어지지만, 1단계에서는 검증 대상이 아니므로 **Agent #1A의 Response를 Chat Output에 바로 연결**한다. 이 임시 연결은 다음 단계마다 새 Agent가 추가될 때 그 앞 Agent로 옮겨가며(2단계에서 #1B로, 2-2단계에서 #1B-2로, 3단계에서 #1C로), 5단계에서 최종적으로 끊고 Agent #2로 교체한다.

**연결 (2개)**

| 순서 | From | To | 비고 |
|---|---|---|---|
| 1 | Chat Input → `User Message` | Agent #1A → `Input` | 파란 점선 |
| 2 | API Request Tool(`orgList`) → `Tool` | Agent #1A → `Tools` | 빨간 |
| 3 | Agent #1A → `Response` | Chat Output → `Input` | **Chat Output 쪽에서 드래그 시작**(04번 문서 151행 제약) |

**API Request Tool 배치 — orgList 1개만**

2-2절의 값을 그대로 사용한다(요약):

| 항목 | 값 |
|---|---|
| 노드 라벨 | `API Request Tool: orgList` |
| Tool Mode | ON |
| URL | `https://ivms.lguplus.co.kr/ivms/api/orgList` |
| Method | GET |
| Connect Timeout / Read Timeout | 3000ms / 10000ms |
| Header | `X-Global-Transaction-ID`, `X-APP-NAME`, `X-AuthorizationTime`, `X-Header-Authorization` (2-2절 표 그대로) |
| Query Params | `orgType`(string, Y), `pOrgId`(string, Y) — 2-2절 표 그대로 |
| 툴 설명 | 2-2절 원문 그대로: `조직명으로 하위 조직 목록을 조회해 orgId를 확인하는 도구. pOrgId(상위 조직 ID)를 입력받아 그 하위 조직 목록을 반환한다. 최상위 조직부터 조회하려면 pOrgId="org_000001"로 시작한다.` |

**Agent #1A System Prompt (1단계 전용 — 실전 검증 버전)**

최종 4단계 System Prompt(2-6절)를 전부 쓰지 않고, 이번 단계에서 검증할 1단계 지시만 넣는다.

> ⚠️ **개정 이력**: 최초 작성한 버전(응답 형식 강제 + "아직 ~하지 않는다" 범위 제한 문구 포함)은 실제 캔버스 실행 시 오류가 발생했다. 아래는 실제 캔버스에서 **성공이 확인된 프롬프트**를 기준으로, 원래 의도했던 "재귀 조회 상한(최대 4단계)"과 "1단계 범위로 응답 한정" 지시만 최소한으로 보강한 버전이다. 응답 형식을 문장으로 강제하던 지시는 제거했다 — Tool 호출 흐름과 충돌해 실패를 유발한 것으로 추정된다.

```
사용자가 입력한 조직명과 일치하는 조직을 찾을 때까지 orgList를 호출한다.

- 처음에는 pOrgId="org_000001"(최상위)로 시작해 orgType을 "1"(부문)부터 순차 조회한다.
- 응답의 orgList[].orgNm이 사용자가 언급한 조직명과 일치하면 그 orgList[].orgId를 확정한다.
- 일치하는 조직이 없으면 응답의 orgId를 다음 pOrgId로 사용해 하위 레벨(orgType "2"→"3"→"4")로 재귀 조회한다. 최대 4단계(부문→그룹→담당→팀)까지만 순회하고, 그래도 없으면 "해당 조직명을 찾을 수 없습니다: "라고 쓰고 바로 뒤에 사용자가 입력한 조직명을 이어서 응답한다.
- 여러 개의 유사한 조직명이 나오면 사용자에게 확인을 요청하지 말고, 가장 정확히 일치하는 1건을 선택한다(모호하면 정확 일치 우선, 없으면 부분 일치 중 첫 번째).
- 담당자 조회, 미조치 항목 조회, 조치가이드 조회는 이번 단계에서 수행하지 않는다.
```

- `Jailbreak Check`: OFF
- `Model`: `azure_openai:gpt-4.1-mini`

**Chat Output**
- `Input`: Agent #1A `Response` 연결(위 표 3행)

**1단계 검증 방법**

1. Chat Input에 `"Enterprise SW프로덕트개발팀 조직 ID 확인해줘"` 입력 후 전체 플로우 실행
2. 기대 응답: `orgId`(`org_000991`)와 조직명(`Enterprise SW프로덕트개발팀`)이 포함된 응답(문장 형식은 강제하지 않음 — 위 개정 이력 참고)
3. 응답에 `orgId`가 포함되지 않거나 "Tool에 접근할 수 없다"는 취지의 응답이 나오면, 다음을 순서대로 점검:
   - API Request Tool의 Tool Mode가 ON인지, Tools 포트에 실제 연결선이 있는지
   - Header 4종의 **키가 등록되어 있는지**(값은 빈 값이어도 정상 — 2026-08-18 확인, 1절 참고). 과거에는 `X-AuthorizationTime`/`X-Header-Authorization` 만료를 우선 의심하도록 안내했으나 그 가설은 배제됐으므로, 인증보다 아래 Query Params/Timeout 항목을 먼저 점검할 것
   - System Prompt에 응답 형식을 문장으로 강제하는 지시나 "이번 단계에서 하지 않는다"류 범위 제한 문구가 들어가 있지 않은지(Tool 호출 흐름과 충돌해 오류를 유발한 사례 있음 — 위 개정 이력 참고)
4. 검증되면 2단계(`mngtListDetail` 추가)로 넘어간다.

---

### 7.2 [2단계] Agent #1A 보강 + 신규 Agent #1B(`mngtListDetail`) 추가

**목표**: 1단계에서 확정한 `orgId`만으로는 `mngtListDetail`을 호출할 수 없으므로(아래 2차 개정 이력 참고), 우선 Agent #1A에 `assetSsrcceTemplate`/`assetCategory` 2개 Tool을 추가해 `templateNo`/`asstType`까지 확보하도록 보강한다. 이어서 **신규 Agent #1B**를 만들어 `mngtListDetail` Tool을 연결하고, Agent #1A의 `Response`를 Agent #1B의 `Input`으로 이어 붙여 `orgId`(→`mgmtOrgId`)로 직접 호출해 **미조치 자산과 담당자 정보(chrgId/chrgNm)를 동시에** 획득한다.

> **개정 이력(2026-07-14, Agent 분할)**: 이 절은 원래 Agent #1 하나에 `assetSsrcceTemplate`/`assetCategory`/`mngtListDetail` 3개 Tool을 모두 추가하는 구조로 작성되어 있었다. 그러나 최종 4~5단계까지 Agent #1 하나에 Tool 5개가 전부 쌓이면 컨텍스트 예산 초과(`context limit exceeded: estimated 120032 tokens > budget 100000`)가 발생하는 것이 확인되어(0절 개정 이력 참고), 자산 목록처럼 응답이 큰 `mngtListDetail`부터는 별도 Agent(#1B)로 분리하도록 이 절을 재작성했다. 아래 1차~3차 개정 이력(엔드포인트/파라미터 관련 이슈)은 Agent 분할과 무관하게 여전히 유효하므로 그대로 유지한다.

> **개정 이력(2026-07-10, 1차)**: 이 절은 원래 `asstChrgInfo`를 선행 Tool로 두고 그 출력(`chrgId`)을 `mngtListDetail`의 `rspnMngId`에 넘기는 2-Tool 구조로 작성되어 있었다. 그러나 실제 캔버스 테스트에서 `asstChrgInfo`를 `orgId`로 호출하자 `msgCd: E`(필수 컬럼 확인 필요) 오류가 발생했고, 08번 문서 2.4절을 재조사한 결과 `asstChrgInfo`의 실제 필수 파라미터는 `asstId`+`asstVer`(**자산 1건 단위**)이며 `orgId` 입력 파라미터 자체가 없다는 사실이 확인되었다(09번 문서 50/95행, 10번 문서 91행의 "asstChrgInfo로 orgId 기준 담당자 목록 조회"라는 서술은 실제 API 스펙과 어긋난 잘못된 가정이었다). `asstChrgInfo`는 플로우 A의 필수 체인에서 제외하고, 조직 기준 담당자 목록은 `mngtListDetail` 응답의 `chrgId`/`chrgNm` 필드(자산 레코드에 이미 포함, 08번 문서 2.2절 `assetList[].chrgId`)에서 직접 획득하는 것으로 1차 수정했다.
>
> **개정 이력(2026-07-10, 2차)**: 1차 수정 후 실제 캔버스에서 `mngtListDetail`을 `mgmtOrgId` + `filter`만으로 호출했으나 다음 두 단계의 오류가 순차로 발생했다.
> 1. **HTTP 405 Method Not Allowed**: 캔버스의 `mngtListDetail` Tool 노드 Method 드롭다운이 GET으로 설정되어 있었음(POST 전용 엔드포인트인데 GET으로 호출). → Method를 POST로 수정.
> 2. **msgCd: E, "필수 컬럼 확인 필요"**: Method를 POST로 고치고 Body에 `mgmtOrgId`+`filter`만 넣어 재호출했으나 여전히 실패. 콘솔 로그상 요청 자체는 정확히 도달했음(`mgmtOrgId=org_000991`, `filter=SECURITY_SCORE neq 100` 확인됨)에도 거부된 것으로 보아, IVMS 서버는 08번 문서 스펙 표의 "필수: N" 표기와 무관하게 **`asstType`(자산타입) 또는 `templateNo`(진단템플릿) 같은 자산 유형 특정 파라미터가 없으면 컬럼을 결정할 수 없어 거부**하는 것으로 확인됐다. 08번 문서 515~523행의 유일한 성공 예시(`userId`+`asstType`+`templateNo`+`diagYear`+`asstLCtgrId` 조합)가 이 추정을 뒷받침한다.
>
> 이 `asstType`/`templateNo` 값은 조직·자산마다 다르므로 System Prompt에 고정값으로 넣을 수 없다. 08번 문서 1.2절(`assetSsrcceTemplate`, 153~183행)과 1.3절(`assetCategory`, 189~260행)에 각각 `templateNo`와 `asstType`(→`asstCtgrList[].asstType`)을 조회하는 API가 이미 존재하므로, 이 두 API를 `mngtListDetail` 호출 전에 추가로 호출해 값을 동적으로 확정하는 구조로 2차 수정한다.
>
> **개정 이력(2026-07-14, 3차)**: 2차 수정 후에도 `mngtListDetail`이 운영 서버(`ivms.lguplus.co.kr`)에서 `msgCd: E`로 계속 실패해, 한동안 `X-Header-Authorization` 서명 만료를 원인으로 의심하고 IVMS 운영팀 문의가 필요하다는 결론까지 갔었다. 그러나 실제로는 인증 서명 문제가 아니라 캔버스 Tool 노드의 **설정 2가지**가 원인이었음이 확인됐다: (1) Query Params 칸에 값이 남아있어 POST+Body 요청에 불필요한 쿼리스트링이 붙었던 점, (2) Read Timeout이 10000ms로 짧아 응답(자산 1000건 이상 조회 시 수 초 이상 소요)이 오기 전에 타임아웃 처리된 점. Query Params를 전부 비우고 Read Timeout을 **30000ms**로 늘리자 정상 성공(`listCount` 정상 반환)이 확인됐다. 성공 응답에서도 `[WARN] mgmtOrgId 불일치/누락` 경고가 함께 나올 수 있으나 이는 API 실패가 아니라 데이터 정합성 경고이며 플로우 진행에는 영향 없다.
>
> **개정 이력(2026-08-18, 서명 만료 가설 최종 배제)**: 위 3차 개정에서 "인증 서명 문제가 아니었다"고 정정했으나 가능성 자체는 열어둔 상태였다. 이후 인증 헤더 4종을 **모두 빈 값으로 두어도 API가 정상 응답값을 반환**함이 확인되어(1절 참고), `X-Header-Authorization` 서명 만료 가설은 최종적으로 배제됐다. 이 계열 실패의 원인은 위에 적힌 Query Params 잔존과 Read Timeout 부족 2가지로 확정한다.
>
> **개정 이력(2026-07-14, 4차 — pageSize 상향 후에도 재발, #1B를 경량 스캔으로 재정의)**: `pageSize=200`+반복상한(3회, 600건) 대응 후에도 자산이 더 많은 조직에서 Agent #1B의 컨텍스트 예산 초과가 재발했다(0절 3차 개정 이력 참고). 이에 따라 **이 2단계에서 구성하는 Agent #1B는 "담당자 목록 경량 스캔" 역할로 재정의**한다 — 아래 "Agent #1B System Prompt (신규)"는 이제 자산 상세(asstNm/securityScore/timeEndYmd)를 응답에 남기지 않고 `chrgId`/`chrgNm`만 추출하는 **2-7절 최신 버전**을 그대로 사용해야 한다(아래 원문은 이전 버전이므로 실제 구성 시 **2-7절의 System Prompt로 교체**할 것). 담당자별 자산 상세 수집(기존 이 절이 담당하던 역할)은 **7.2-2절(신규, Agent #1B-2)**로 분리했다 — 2단계 완료 후 바로 7.2-2절로 진행한다.

**추가로 배치할 노드 (API Request Tool 2개 + Agent 1개, Chat Input/Chat Output/Agent #1A는 1단계에서 이미 배치됨)**

| 노드 | 라벨 |
|---|---|
| API Request Tool | `API Request Tool: assetSsrcceTemplate` |
| API Request Tool | `API Request Tool: assetCategory` |
| Agent(신규) | `Agent #1B: 미조치 자산·담당자 수집` |
| API Request Tool | `API Request Tool: mngtListDetail` |

**추가 연결 (5개)**

| 순서 | From | To | 비고 |
|---|---|---|---|
| 4 | API Request Tool(`assetSsrcceTemplate`) → `Tool` | Agent #1A → `Tools` | 빨간, 1단계 `orgList` 연결과 같은 Tools 포트에 추가 |
| 5 | API Request Tool(`assetCategory`) → `Tool` | Agent #1A → `Tools` | 빨간, 동일 포트에 추가 |
| 6 | Agent #1A → `Response` | Agent #1B → `Input` | 파란 점선, 컨텍스트 분리 지점(신규) |
| 7 | API Request Tool(`mngtListDetail`) → `Tool` | Agent #1B → `Tools` | 빨간 |
| 8 | Agent #1B → `Response` | Chat Output → `Input` | **Chat Output 쪽에서 드래그 시작** — 1단계에서 걸어둔 `Agent #1A→Chat Output` 임시 연결을 끊고 이 연결로 교체(다음 단계에서 다시 #1C로 옮겨감) |

1단계의 연결 중 `Chat Input→Agent #1A`(1행)만 그대로 유지한다.

**API Request Tool 배치 — `assetSsrcceTemplate`**

08번 문서 1.2절(153~183행) 기준. GET 방식으로 `orgList`와 동일한 파라미터 위치(Query Params)를 사용한다.

| 항목 | 값 |
|---|---|
| 노드 라벨 | `API Request Tool: assetSsrcceTemplate` |
| Tool Mode | ON |
| URL | `https://ivms.lguplus.co.kr/ivms/api/assetSsrcceTemplate` |
| Method | GET |
| Connect Timeout / Read Timeout | 3000ms / 10000ms |
| Header | 공통 인증 헤더 4종(1단계 `orgList`와 동일) |
| Query Params | `userId`(string, Y — 예: `admin`) |
| 툴 설명 | `사용 가능한 진단템플릿 목록을 조회하는 도구. 응답의 templateList[]에 atemplateNo(진단템플릿 번호)와 templateName(진단템플릿명)이 담겨 있다.` |

**API Request Tool 배치 — `assetCategory`**

08번 문서 1.3절(189~260행) 기준. GET 방식.

| 항목 | 값 |
|---|---|
| 노드 라벨 | `API Request Tool: assetCategory` |
| Tool Mode | ON |
| URL | `https://ivms.lguplus.co.kr/ivms/api/assetCategory` |
| Method | GET |
| Connect Timeout / Read Timeout | 3000ms / 10000ms |
| Header | 공통 인증 헤더 4종 |
| Query Params | `userId`(string, Y — 예: `admin`), `asstCtgrLevel`(string, Y — `L`/`M`/`S` 중 대분류 조회 시 `L`) |
| 툴 설명 | `자산분류 목록을 조회하는 도구. 응답의 asstCtgrList[]에 asstCtgrId(자산분류ID), asstCtgrNm(자산분류명), asstType(자산타입)이 담겨 있다. asstCtgrLevel="L"로 대분류부터 조회한다.` |

**API Request Tool 배치 — `mngtListDetail`**

08번 문서 2.2절(480~523행) 기준. 이 Tool은 **POST + Body**라는 점이 위 두 Tool(GET)과 다르므로 API Request Tool의 파라미터 입력 위치가 Query Params가 아니라 **Body**임에 주의한다.

| 항목 | 값 |
|---|---|
| 노드 라벨 | `API Request Tool: mngtListDetail` |
| Tool Mode | ON |
| URL | `https://ivms.lguplus.co.kr/ivms/api/mngtListDetail` |
| Method | **POST** (⚠️ GET으로 잘못 설정하면 HTTP 405 Method Not Allowed 발생 — 실제 캔버스 테스트에서 확인된 오류) |
| Connect Timeout / Read Timeout | 1000ms / **30000ms** (⚠️ 10000ms 이하로 두면 응답이 오기 전에 타임아웃되어 실패 처리됨 — 2026-07-14 실제 캔버스 테스트에서 30000ms로 늘리자 정상 응답 확인됨) |
| Query Params | **반드시 비워둘 것(전부 삭제)** — 이 Tool은 POST+Body 방식인데 Query Params 칸에 값이 남아있으면 URL에 불필요한 쿼리스트링이 붙어 서버가 요청을 정상 처리하지 못함(2026-07-14 실제 확인된 오류 원인) |
| Header | 공통 인증 헤더 4종 + **`Content-Type: application/json`**(08번 문서 127행 — POST 요청에만 필요) |
| 요청 본문 스키마(Body) | `mgmtOrgId`(string), `asstType`(string), `templateNo`(string), `filter`(object: `xorStr.logic` string, `xorStr.filters` array of `{field, operator, value}`) — 아래 JSON Schema 참고 |
| Body 예시 | ```json\n{\n  "mgmtOrgId": "{1단계에서 확정한 orgId}",\n  "asstType": "{assetCategory 응답의 asstType}",\n  "templateNo": "{assetSsrcceTemplate 응답의 atemplateNo}",\n  "filter": {\n    "xorStr": {\n      "logic": "and",\n      "filters": [{"field": "SECURITY_SCORE", "operator": "neq", "value": 100}]\n    }\n  }\n}\n``` |
| 툴 설명 | `조직ID(mgmtOrgId)·자산타입(asstType)·진단템플릿(templateNo)을 입력받아 해당 조건에 맞는 자산 중 SECURITY_SCORE가 100이 아닌(취약/미조치) 자산 목록을 조회하는 도구. asstType과 templateNo는 반드시 assetCategory/assetSsrcceTemplate 조회 결과값을 사용해야 하며, 임의로 지어내면 안 된다. 응답의 assetList[]에는 asstNm(자산명), chrgId/chrgNm(담당자ID/담당자명), securityScore(보안점수), timeEndYmd(최근 진단일), resultId(진단결과 ID)가 포함된다.` |

**"요청 본문 스키마" 입력 방법 (캔버스 UI)**

`mngtListDetail` Tool의 Body 설정이 "요청 본문 스키마" 팝업(JSON Schema 편집기)으로 되어 있는 경우, 우측 상단 **"편집"** 버튼을 눌러 아래 JSON을 그대로 입력한다(좌측 "프로퍼티 추가" 버튼으로 하나씩 등록하는 방식은 `filter`처럼 object 안에 object가 중첩된 구조를 다루기 번거로우므로 권장하지 않음).

```json
{
  "title": "mngtListDetailRequest",
  "type": "object",
  "properties": {
    "mgmtOrgId": { "type": "string", "description": "조직 ID (orgList에서 확정한 orgId)" },
    "asstType": { "type": "string", "description": "자산타입 (assetCategory 응답의 asstType)" },
    "templateNo": { "type": "string", "description": "진단템플릿 번호 (assetSsrcceTemplate 응답의 atemplateNo)" },
    "filter": {
      "type": "object",
      "properties": {
        "xorStr": {
          "type": "object",
          "properties": {
            "logic": { "type": "string" },
            "filters": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "field": { "type": "string" },
                  "operator": { "type": "string" },
                  "value": {}
                }
              }
            }
          }
        }
      }
    }
  },
  "additionalProperties": true,
  "strict": false
}
```

> **09번 문서 4절 "미조치 판단 로직"(99~103행) 반영**: `mngtListDetail`의 `SECURITY_SCORE neq 100` 필터는 취약 자산을 1차로만 선별한다. 진짜 "미조치"로 확정하려면 응답의 `timeEndYmd`(최근 진단일) 기준 **경과일 ≥ 7일**인 항목만 걸러야 하는데, 이 날짜 계산은 API 파라미터로 넘길 수 없으므로(08번 문서에 그런 필터 필드 없음) System Prompt에서 Agent가 직접 오늘 날짜와 `timeEndYmd`를 비교하도록 지시할 수 있다. 다만 아래 2단계 프롬프트는 캔버스 실제 테스트 안내와 동일하게 우선 단순화된 버전(경과일 필터 제외, SECURITY_SCORE 필터만 적용)으로 작성한다 — 경과일 필터는 이후 단계(Agent #2, 09번 문서 4절 기준)에서 최종 판단에 반영해도 무방하다.

**Agent #1A System Prompt (2단계 전용 — 1단계 위에 이어붙임)**

1단계 프롬프트(7.1절)의 4개 항목(조직 조회 로직)은 그대로 두고, 그 아래에 템플릿/자산분류 확인 지시와 출력 형식 지시를 추가한다. `mngtListDetail` 호출 지시는 Agent #1A가 아니라 신규 Agent #1B에 넣는다(아래 참고) — Agent #1A 컨텍스트에는 자산 목록처럼 큰 응답을 남기지 않기 위함이다.

```
사용자가 입력한 조직명과 일치하는 조직을 찾을 때까지 orgList를 호출한다.

- 처음에는 pOrgId="org_000001"(최상위)로 시작해 orgType을 "1"(부문)부터 순차 조회한다.
- 응답의 orgList[].orgNm이 사용자가 언급한 조직명과 일치하면 그 orgList[].orgId를 확정한다.
- 일치하는 조직이 없으면 응답의 orgId를 다음 pOrgId로 사용해 하위 레벨(orgType "2"→"3"→"4")로 재귀 조회한다. 최대 4단계(부문→그룹→담당→팀)까지만 순회하고, 그래도 없으면 "해당 조직명을 찾을 수 없습니다: "라고 쓰고 바로 뒤에 사용자가 입력한 조직명을 이어서 응답한다.
- 여러 개의 유사한 조직명이 나오면 사용자에게 확인을 요청하지 말고, 가장 정확히 일치하는 1건을 선택한다(모호하면 정확 일치 우선, 없으면 부분 일치 중 첫 번째).

조직의 orgId를 확정했으면 이어서 assetSsrcceTemplate과 assetCategory를 호출한다.

- assetSsrcceTemplate은 userId="admin"으로 호출해 templateList[]를 받는다. 첫 번째 항목의 atemplateNo를 templateNo로 사용한다.
- assetCategory는 userId="admin", asstCtgrLevel="L"로 호출해 asstCtgrList[]를 받는다. 이 목록에서 asstType 값을 확인한다(여러 개면 첫 번째 값을 사용).
- templateNo와 asstType은 반드시 이 두 API의 응답값을 사용한다. 임의로 지어내거나 생략하지 않는다.

마지막으로 확정한 값을 다음 형식으로 명확히 출력한다(각 줄의 콜론 뒤에 실제 확정된
값을 그대로 적는다). 다른 설명은 덧붙이지 않는다.

orgId: (확정된 orgId 값)
templateNo: (확정된 templateNo 값)
asstType: (확정된 asstType 값)
```

- `Jailbreak Check`: OFF
- `Model`: `azure_openai:gpt-4.1-mini` (Tool 호출 스텝이 3개로 늘었으나 응답 크기가 작아 유지)

**Agent #1B System Prompt (구버전 — ⚠️ 아래 대신 2-7절 최신본을 사용할 것)**

> ⚠️ **2026-07-14, 4차 개정**: 아래 System Prompt는 자산 상세(asstNm/securityScore/timeEndYmd)까지 이 단계에서 함께 수집하던 **구버전**이다. 이 방식이 컨텍스트 예산 초과를 재발시켰으므로, 실제 캔버스 구성 시에는 아래 원문 대신 **2-7절("Agent #1B: 담당자 목록 경량 스캔")의 System Prompt 전체 원문**을 그대로 사용한다 — `chrgId`/`chrgNm`만 추출하고 자산 상세는 버리는 버전이다. 아래 원문은 이 절이 처음 작성된 시점의 기록으로만 남겨둔다.

```
입력으로 이전 단계가 확정한 orgId, templateNo, asstType 값을 텍스트로 받는다. 이 값을
그대로 파싱해 사용하고, 임의로 다른 값을 지어내거나 재확인을 위해 orgList 등을 다시
호출하지 않는다.

받은 orgId, templateNo, asstType으로 mngtListDetail을 호출한다.

- mngtListDetail 호출 시 mgmtOrgId 파라미터에는 입력받은 orgId 값을, asstType과 templateNo에는 입력받은 값을 그대로 사용한다.
- page는 숫자 1, pageSize는 숫자 200으로 integer 타입으로 넣는다(⚠️ 반드시 200 이상 큰 값을 사용 — 작은 값을 쓰면 자산 건수가 많은 조직에서 페이지 반복 호출 횟수가 급증해 컨텍스트 예산 초과가 발생한다. 2026-07-14 실제 확인된 오류 원인).
- filter.xorStr에는 {"logic":"and","filters":[{"field":"SECURITY_SCORE","operator":"neq","value":100}]}를 고정으로 사용해 미조치(취약) 자산만 조회한다.
- 응답 assetList[] 중 chrgId, chrgNm(담당자 정보)이 서로 다른 값끼리 묶어 담당자별로 자산 목록을 구분한다.
- 응답 건수가 pageSize(200)와 같으면 다음 페이지가 있을 수 있으므로 page를 1씩 증가시켜 반복 호출한다. 단, 반복 호출 3회(총 600건)를 넘어서면 더 이상 반복하지 말고, 그때까지 수집한 자산만으로 응답을 구성하며 응답 맨 앞에 "⚠️ 자산 건수가 많아 일부만 조회했습니다(최대 600건)"라고 명시한다.
- 담당자별 자산 목록(asstNm, securityScore, timeEndYmd)을 정리해 응답에 포함한다. 조치가이드 조회는 이번 단계에서 하지 않는다.

마지막으로 담당자별로 asstNm, securityScore, timeEndYmd를 표 형식으로 정리해 출력한다.
```

- `Jailbreak Check`: OFF
- `Model`: `azure_openai:gpt-4.1` (응답 다수, 페이지네이션 반복 가능성 고려해 상향)

**Chat Output**
- **연결 변경**: 1단계에서 걸어둔 `Agent #1A→Chat Output` 임시 연결을 끊고, `Agent #1B→Chat Output`으로 교체한다(위 노드 배치 표 8행) — 이 연결은 다음 7.2-2절에서 `Agent #1B-2→Chat Output`으로 다시 교체된다.

**2단계 검증 방법**

1. Chat Input에 `"Enterprise SW프로덕트개발팀 미조치 자산 확인해줘"` 입력 후 전체 플로우 실행
2. 기대 응답: Enterprise SW프로덕트개발팀 소속 담당자별로 구분된 미조치 자산 목록(자산명/보안점수/최근진단일 포함)이 응답에 나타나는지 확인 — 문장 형식은 강제하지 않음
3. 정상 동작하지 않으면 다음을 순서대로 점검:
   - Agent #1A → Agent #1B 연결(`Response`→`Input`)이 정확히 되어 있는지, Agent #1B가 orgId/templateNo/asstType 텍스트를 제대로 파싱하는지
   - `mngtListDetail` Tool의 Method가 정확히 **POST**로 설정되어 있는지(GET으로 남아있으면 HTTP 405 발생 — 실제 확인된 오류)
   - `mngtListDetail` Tool의 **Query Params가 완전히 비어있는지**(POST+Body 방식인데 Query Params에 값이 남아있으면 URL에 불필요한 쿼리스트링이 붙어 요청이 실패함 — 2026-07-14 실제 확인된 오류 원인)
   - `mngtListDetail` Tool의 **Read Timeout이 30000ms로 설정되어 있는지**(기본값 근처인 10000ms 이하로는 응답이 오기 전에 타임아웃 실패 발생 — 2026-07-14 실제 확인된 오류 원인)
   - `assetSsrcceTemplate`/`assetCategory`가 Agent #1A Tools 포트에, `mngtListDetail`이 Agent #1B Tools 포트에 각각 연결되어 있는지(서로 다른 Agent에 잘못 연결하지 않았는지)
   - `mngtListDetail`은 POST이므로 파라미터가 Body(요청 본문 스키마)에 들어가는지(Query Params에 잘못 넣으면 서버가 인식하지 못함)
   - `mngtListDetail` Header에 `Content-Type: application/json`이 추가됐는지(GET 전용이던 1단계 Header 4종에서 하나 더 필요)
   - Body에 `mgmtOrgId`뿐 아니라 `asstType`, `templateNo`가 함께 전달되는지(이 중 하나라도 빠지면 `msgCd: E`, "필수 컬럼 확인 필요" 오류 발생 — 실제 확인된 오류)
   - `mgmtOrgId`에 1단계에서 확정한 `orgId` 값이 정확히 들어가는지(다른 값을 넘기면 빈 목록이 반환될 수 있음)
   - 담당자별 구분이 안 되고 전체 자산이 하나로 뭉쳐 나오면, System Prompt의 "chrgId, chrgNm이 서로 다른 값끼리 묶어 담당자별로 구분" 지시가 Agent에게 제대로 인식되고 있는지 확인
   - **컨텍스트 예산 오류(`context limit exceeded`)가 재발하는지** — `mngtListDetail`의 `pageSize`가 `200`으로(작은 값이 아니라) 설정되어 있는지, 반복 호출 상한(3회, 총 600건) 지시가 System Prompt에 포함되어 있는지 우선 확인한다. 이 값들이 정상인데도 재발하면 자산 건수가 상한(600건)보다도 훨씬 많은 조직인지 확인하고, 필요하면 Agent #1B를 페이지 단위로 한 번 더 분할하는 것을 검토
4. **정상 성공 시에도 나타날 수 있는 경고(에러 아님)**: 콘솔 로그에 `[WARN] 요청 mgmtOrgId나 응답 자산 중 일부의 mgmtOrgId가 다름 또는 비어 있음`이 뜰 수 있다. 이는 API 호출 자체는 성공(`listCount` 정상 반환)했으나, 응답으로 돌아온 자산 중 일부가 요청한 조직 소속이 아니거나 `mgmtOrgId`가 비어있다는 **데이터 정합성 경고**이며 플로우 진행을 막지 않는다. 서버 측 조직 필터링이 완전하지 않을 수 있다는 점만 인지하고 다음 단계로 진행한다.
5. **데이터/필터 정합성 확인 필요 사항(2026-07-14, 실제 콘솔 로그 기반 확인)**: HTTP 응답은 모두 `200`/`_server_message_.type="200"`으로 정상이었으나(`text`는 원래 선택 필드라 비어 있어도 정상 — `08-ivms_openapi_spec.md` 참고), `result` 데이터 자체에서 다음 불일치가 확인됨. 이는 캔버스 설정 문제가 아니라 IVMS 서버가 입력 필터를 참고값으로만 쓰고 엄격히 적용하지 않는 데서 비롯된 것으로 추정된다:
   - `mgmtOrgId=org_000991`로 조회했으나 반환 자산 중 `mgmtOrgId`가 빈 값이거나, 그룹 경로가 요청 조직과 불일치하는 항목이 포함됨
   - `chrgId`/`chrgNm`(담당자 정보)이 빈 값으로 반환되는 자산이 존재해 담당자별 그룹핑이 불완전할 수 있음
   - → **대응**: Agent #1 System Prompt에 "응답에서 `mgmtOrgId`가 요청값과 다르거나 비어있는 자산은 제외 또는 별도 표시", "`chrgId`/`chrgNm`이 빈 값인 자산은 '담당자 미배정'으로 분류" 규칙을 추가하는 것을 검토한다(2-6절 프롬프트 개정 시 반영).
6. **컨텍스트 예산 재발 이력(2026-07-14, 2차)**: Agent 분할(#1A/#1B/#1C) 이후 실제 재실행에서 Agent #1B 실행 중 `context limit exceeded: estimated 109508 tokens > budget 100000` 오류가 재발했다. 원인은 System Prompt의 `pageSize=10` 기본값 — 미조치 자산이 많은 조직에서 페이지 반복 호출이 과도하게 누적됐기 때문이다. → **대응**: `pageSize`를 `200`으로 상향하고 반복 호출 상한(3회, 총 600건)을 추가했다(위 System Prompt 참고). 재실행 시 이 값들이 실제로 적용됐는지, 그리고 오류가 사라졌는지 반드시 재확인한다.
7. **검증되면 3단계가 아니라 7.2-2단계(신규 Agent #1B-2: 담당자별 자산 정밀조회 추가)로 먼저 넘어간다.** Agent #1B는 이 시점부터 "담당자 목록 경량 스캔" 역할만 담당하며, 자산 상세 수집은 #1B-2가 이어받는다.

---

### 7.2-2 [2-2단계] 신규 Agent #1B-2 생성 + 담당자별 `mngtListDetail` 정밀조회

> **개정 이력(2026-07-14, 4차)**: Agent #1B를 "경량 스캔"으로 재정의하면서(위 7.2절 4차 개정 이력 참고), 담당자별 자산 상세 수집 역할을 이 신규 절로 분리했다. Agent #1B가 넘긴 담당자 목록(`chrgId`/`chrgNm` 유니크 집합)을 입력받아, 담당자별로 `rspnMngId`를 채운 `mngtListDetail`을 재호출해 자산 상세를 수집한다. 담당자 1인 단위로 호출을 좁히면 응답 건수가 조직 전체보다 훨씬 작아 페이지네이션 반복이 줄어들 것으로 기대되나, 완전한 근본 해결은 아니다(0절 3차 개정 이력 참고).

**목표**: Agent #1B가 스캔한 담당자 목록을 순회하며, 담당자별로 `mngtListDetail`을 `rspnMngId`로 좁혀 재호출해 자산 상세(`asstNm`/`asstCode`/`hostNm`/`securityScore`/`timeEndYmd`)를 수집한다. 이전(구버전) 2-7절이 담당하던 "자산 상세 수집" 역할이 여기로 옮겨왔다.

**추가로 배치할 노드 (Agent 1개 + Tool 1개 또는 기존 Tool 공유)**

| # | 노드 종류 | 이름(권장) | 비고 |
|---|-----------|-----------|------|
| 1 | Agent | `Agent #1B-2` | 신규 배치 |
| 2 | API Request Tool | `mngtListDetail` (2) | ⚠️ **확인 필요**: Agent #1B가 이미 연결한 `mngtListDetail` Tool 노드를 그대로 공유 연결(같은 Tool 노드의 출력을 Agent #1B와 #1B-2 양쪽 Tools 포트에 연결)할 수 있는지, 아니면 `04-ixi-enterprise-node-catalog.md` 기준 Tool 노드는 단일 Agent에만 연결 가능해 복제 배치가 필요한지 캔버스에서 직접 시도해 확인한다. 공유가 안 되면 동일한 설정(Method/Header/Body 스키마)으로 Tool 노드를 하나 더 복제해 배치한다. |

**연결**

- `Agent #1B` → `Response` → `Agent #1B-2` → `Input`
- `mngtListDetail`(공유 또는 복제본) → `Agent #1B-2` `Tools` 포트
- **연결 변경**: 7.2절에서 걸어둔 `Agent #1B→Chat Output` 임시 연결을 끊고, `Agent #1B-2→Chat Output`으로 교체한다.

**Agent #1B-2 System Prompt** (2-7-2절 원문과 동일 — 아래는 재사용을 위한 요약. 실제 구성 시 2-7-2절 원문을 그대로 붙여넣는다)

```
입력으로 Agent #1B의 응답(담당자 목록: chrgId/chrgNm 쌍, "담당자 미배정 존재 여부",
orgId/templateNo/asstType)을 텍스트로 받는다. 이 값을 그대로 파싱해 사용한다.

담당자 목록을 순회하며, 담당자 1명당 다음과 같이 mngtListDetail을 호출한다:
- mgmtOrgId=orgId, asstType, templateNo는 입력받은 값을 그대로 사용
- rspnMngId=해당 담당자의 chrgId
- page=1, pageSize=200(integer)로 시작해, 응답 건수가 pageSize와 같으면 page를
  1씩 증가시켜 반복 호출한다. 단, 담당자 1명당 반복 호출 3회(총 600건)를 넘으면
  중단하고 "⚠️ 이 담당자의 자산이 많아 일부만 조회했습니다"라고 표시한다.
- 응답 assetList[]의 mgmtOrgId가 요청한 orgId와 다르거나 비어있는 자산은 제외하거나
  별도 표시한다(서버가 필터를 완벽히 적용하지 않을 수 있음 — 7.2절 5번 항목 참고).

"담당자 미배정 존재 여부"가 있으면, rspnMngId 없이 mgmtOrgId+asstType+templateNo만으로
1회 추가 호출하고, 응답 중 chrgId/chrgNm이 빈 값인 자산만 걸러 "담당자 미배정" 그룹으로
별도 포함한다.

마지막으로 담당자별로(그리고 담당자 미배정 그룹도 있다면 별도로) asstNm, asstCode,
hostNm, securityScore, timeEndYmd를 표 형식으로 정리해 출력한다. orgId/templateNo/
asstType 값도 다음 단계가 재사용할 수 있도록 함께 전달한다.
```

- `Jailbreak Check`: OFF
- `Model`: `azure_openai:gpt-4.1`(담당자 단위 반복 호출이라 #1B보다는 가볍지만 페이지네이션 가능성 있음)

**2-2단계 검증 방법**

1. Chat Input에 `"Enterprise SW프로덕트개발팀 미조치 자산 확인해줘"` 입력 후 전체 플로우(#1A→#1B→#1B-2) 실행
2. 기대 응답: 담당자별로 구분된 자산 상세 목록(자산명/자산코드/호스트명/보안점수/최근진단일)이 응답에 나타나는지 확인
3. 정상 동작하지 않으면 다음을 순서대로 점검:
   - `Agent #1B → Agent #1B-2` 연결(`Response`→`Input`)이 정확한지, #1B-2가 담당자 목록 텍스트를 제대로 파싱하는지
   - `mngtListDetail` Tool이 #1B-2의 Tools 포트에도 실제로 연결되어 있는지(공유 또는 복제본)
   - Body에 `rspnMngId`가 담당자별로 다르게 채워져 호출되는지(모든 호출에 같은 값이 들어가면 System Prompt가 목록을 순회하지 못하고 있는 것)
   - **컨텍스트 예산 오류가 여기서도 재발하는지** — 재발하면 담당자 1인당 자산 건수 자체가 상한(600건)보다 많은 조직이라는 뜻이며, 방법 3(외부 배치 스크립트 분리)을 검토해야 한다(0절 3차 개정 이력 참고)
4. 검증되면 3단계(`scanResultCodeMngtDetail` 추가)로 넘어간다.

---

### 7.3 [3단계] 신규 Agent #1C 생성 + `scanResultCodeMngtDetail` Tool 추가

**목표**: 2단계에서 확보한 미조치 자산 목록(`asstCode`, `hostNm`)을 이어받아, 자산별 항목별 취약점 상세(`scanRsltCodeList[]`)를 조회한다. 이 응답에서 다음 단계(`guidelineCdInfo`)가 필요로 하는 4개 키(`guidelineIfKey`, `itemCode`, `agentServerNm`, `resultIfKey`)를 확보하는 것이 이번 단계의 핵심이다. 2단계와 마찬가지로 `scanResultCodeMngtDetail`은 페이지네이션 반복 호출로 응답이 커질 수 있으므로, Agent #1B에 얹지 않고 **신규 Agent #1C**를 만들어 별도 컨텍스트로 분리한다.

> **개정 이력(2026-07-14, Agent 분할)**: 이 절은 원래 Agent #1 하나에 `scanResultCodeMngtDetail`을 4번째 Tool로 추가하는 구조로 작성되어 있었다. 그러나 0절/7.2절 개정 이력에서 설명한 컨텍스트 예산 초과 문제로, `mngtListDetail`에 이어 `scanResultCodeMngtDetail`도 별도 Agent(#1C)로 분리하도록 재작성했다. 아래 severity 불일치 관련 개정 이력(5번 항목)은 Agent 분할과 무관하게 여전히 유효하므로 그대로 유지한다.

**추가로 배치할 노드 (Tool 1개 + Agent 1개)**

| 노드 | 라벨 |
|---|---|
| Agent(신규) | `Agent #1C: 취약점 상세 수집` |
| API Request Tool | `API Request Tool: scanResultCodeMngtDetail` |

**추가 연결 (3개)**

| 순서 | From | To | 비고 |
|---|---|---|---|
| 9 | Agent #1B-2 → `Response` | Agent #1C → `Input` | 파란 점선, 컨텍스트 분리 지점(신규) — 7.2-2단계에서 걸어둔 `Agent #1B-2→Chat Output` 임시 연결을 끊고 이 연결로 교체 |
| 10 | API Request Tool(`scanResultCodeMngtDetail`) → `Tool` | Agent #1C → `Tools` | 빨간 |
| 11 | Agent #1C → `Response` | Chat Output → `Input` | **Chat Output 쪽에서 드래그 시작** — 7.2-2단계에서 걸어둔 `Agent #1B-2→Chat Output` 연결을 끊고 이 연결로 교체(다음 단계에서 다시 Agent #2로 옮겨감) |

1~2단계 및 2-2단계의 연결 중 `Chat Input→Agent #1A`, `Agent #1A→Agent #1B`, `Agent #1B→Agent #1B-2`, `assetSsrcceTemplate/assetCategory→Agent #1A`, `mngtListDetail(경량 스캔용)→Agent #1B`, `mngtListDetail(정밀조회용, 공유 또는 복제)→Agent #1B-2`는 그대로 유지한다.

**API Request Tool 배치 — `scanResultCodeMngtDetail`**

2-4절(216~318행) 기준. `mngtListDetail`과 동일하게 **POST + Body** 방식이며, 2026-07-14에 확인된 Query Params/Read Timeout 설정을 처음부터 반영한다.

| 항목 | 값 |
|---|---|
| 노드 라벨 | `API Request Tool: scanResultCodeMngtDetail` |
| Tool Mode | ON |
| URL | `https://ivms.lguplus.co.kr/ivms/api/scanResultCodeMngtDetail` |
| Method | **POST** (⚠️ GET으로 잘못 설정하면 HTTP 405 발생 — `mngtListDetail`과 동일한 함정) |
| Connect Timeout / Read Timeout | 1000ms / **30000ms** (⚠️ `mngtListDetail`과 동일하게 응답에 시간이 걸릴 수 있으므로 처음부터 30000ms로 설정 — 2026-07-14 확인된 원인 재발 방지) |
| Query Params | **반드시 비워둘 것(전부 삭제)** — POST+Body 방식이므로 Query Params에 값이 남아있으면 요청 실패(2026-07-14 `mngtListDetail`에서 확인된 것과 동일한 함정이므로 처음부터 비워서 구성) |
| Header | 공통 인증 헤더 4종 + `Content-Type: application/json`(POST 요청이므로 필수) |
| 요청 본문 스키마(Body) | `userId`(string), `asstCode`(array of string), `hostNm`(array of string), `resultStatusCdListStr`(string, JSON 배열 직렬화), `vadaYn`(string), `severity`(string), `asstType`(string), `atemplateNo`(string), `page`(integer), `pageSize`(integer) — 아래 JSON Schema 참고 |
| 툴 설명 | `자산 코드(asstCode)·호스트명(hostNm) 목록 기준으로 취약점 항목별 상세 진단 결과를 조회하는 도구. resultStatusCdListStr에 ["FAIL"]을 지정하면 취약(미조치) 항목만 반환된다. 이 응답의 guidelineIfKey/itemCode/agentServerNm/resultIfKey 값이 있어야 다음 단계의 조치가이드(guidelineCdInfo)를 조회할 수 있다.` |

**"요청 본문 스키마" 입력 방법 (캔버스 UI)**

`mngtListDetail`과 동일하게 우측 상단 "편집" 버튼으로 아래 JSON을 그대로 입력한다.

```json
{
  "title": "scanResultCodeMngtDetailRequest",
  "type": "object",
  "properties": {
    "userId": { "type": "string", "description": "요청 사용자 ID (예: admin)" },
    "asstCode": { "type": "array", "items": { "type": "string" }, "description": "2단계 mngtListDetail 응답의 assetList[].asstCode 목록" },
    "hostNm": { "type": "array", "items": { "type": "string" }, "description": "asstCode와 병행 전달되는 호스트명 목록(2단계 응답의 assetList[].hostNm)" },
    "resultStatusCdListStr": { "type": "string", "description": "점검결과 필터, JSON 배열을 문자열로 직렬화. 미조치만 조회 시 [\"FAIL\"]" },
    "vadaYn": { "type": "string", "description": "자산타입 VADA 여부, 기본 N" },
    "severity": { "type": "string", "description": "취약도 필터 (예: 4)" },
    "asstType": { "type": "string", "description": "자산타입 (2단계 assetCategory 응답과 동일 값)" },
    "atemplateNo": { "type": "string", "description": "진단템플릿 번호 (2단계 assetSsrcceTemplate 응답과 동일 값)" },
    "page": { "type": "integer", "description": "현재 페이지, 기본 1" },
    "pageSize": { "type": "integer", "description": "페이지당 항목 수, 기본 50" }
  },
  "additionalProperties": true,
  "strict": false
}
```

**Agent #1C System Prompt (신규)**

```
입력으로 이전 단계가 정리한 담당자별 자산 표(asstNm, asstCode, hostNm, securityScore,
timeEndYmd 등)를 텍스트로 받는다. 이 값을 그대로 파싱해 사용하고, 임의로 다른 값을
지어내거나 mngtListDetail 등을 다시 호출하지 않는다.

받은 자산 목록의 asstCode와 hostNm을 각각 배열로 담아 scanResultCodeMngtDetail을 호출한다.

- asstCode와 hostNm은 반드시 함께(같은 순서로 대응하도록) 전달한다.
- resultStatusCdListStr은 반드시 문자열 "[\"FAIL\"]"로 지정해 취약(미조치) 항목만 조회한다.
- asstType은 입력받은 값을 그대로 사용하고, vadaYn은 "N"으로 고정한다.
- severity는 "4", atemplateNo는 입력받은 templateNo 값을 그대로 사용한다.
- 응답 scanRsltCodeList[]에서 asstId, asstCode, guidelineIfKey, itemCode, agentServerNm, resultIfKey, guidelineCd, guidelineNm, severity, result를 반드시 추출해 보관한다.
- 응답 중 severity 값이 요청한 "4"와 다른 항목은 결과에서 제외한다(서버가 severity 필터를 엄격히 적용하지 않는 사례가 확인되어 재검증이 필요함).
- page는 숫자 1, pageSize는 숫자 200으로 integer 타입으로 넣는다(⚠️ 반드시 200 이상 큰 값을 사용 — 작은 값을 쓰면 항목 수가 많을 때 페이지 반복 호출 횟수가 급증해 컨텍스트 예산 초과가 발생한다. 2026-07-14 Agent #1B에서 실제 확인된 오류 원인과 동일한 구조적 위험).
- 자산 수가 많아 한 번에 조회되지 않으면 asstCode/hostNm을 나누어 여러 번 호출한다(page를 늘려가며 반복). 단, 반복 호출 3회(총 600건)를 넘어서면 더 이상 반복하지 말고, 그때까지 수집한 항목만으로 응답을 구성하며 응답 맨 앞에 "⚠️ 항목 수가 많아 일부만 조회했습니다(최대 600건)"라고 명시한다.
- 조치가이드 조회는 이번 단계에서 하지 않는다.

마지막으로 담당자별로 asstId, asstCode, guidelineIfKey, itemCode, agentServerNm,
resultIfKey, guidelineCd, guidelineNm, severity, result를 표로 정리해 출력한다.
담당자 배정 정보(asstNm, hostNm 등 입력으로 받은 항목)도 함께 유지해 다음 단계가
매핑할 수 있게 한다.
```

- `Jailbreak Check`: OFF
- `Model`: `azure_openai:gpt-4.1`(자산 수만큼 반복 호출이 필요하므로 `gpt-4.1-mini`보다 상향 권장)

**Chat Output**
- **연결 변경**: 7.2-2단계에서 걸어둔 `Agent #1B-2→Chat Output` 임시 연결을 끊고, `Agent #1C `Response`를 Chat Output `Input`에 연결한다(위 추가 연결 표 11행과 동일)

**3단계 검증 방법**

1. Chat Input에 `"Enterprise SW프로덕트개발팀 미조치 취약점 상세 확인해줘"` 입력 후 전체 플로우 실행
2. 기대 응답: 담당자별 자산 목록에 더해, 각 자산의 취약 항목(`guidelineCd`/`guidelineNm`/`severity`)까지 포함된 응답이 나타나는지 확인
3. 정상 동작하지 않으면 다음을 순서대로 점검:
   - Agent #1B-2 → Agent #1C 연결(`Response`→`Input`)이 정확히 되어 있는지, Agent #1C가 담당자별 자산 표를 제대로 파싱하는지
   - `scanResultCodeMngtDetail` Tool의 Method가 정확히 **POST**로 설정되어 있는지(GET으로 남아있으면 HTTP 405 발생)
   - `scanResultCodeMngtDetail` Tool의 **Query Params가 완전히 비어있는지**(값이 남아있으면 요청 실패 — `mngtListDetail`과 동일한 함정)
   - `scanResultCodeMngtDetail` Tool의 **Read Timeout이 30000ms로 설정되어 있는지**
   - Header에 `Content-Type: application/json`이 추가됐는지
   - Body에 `asstCode`와 `hostNm`이 반드시 함께(배열로) 전달되는지(둘 중 하나만 전달하면 실패 가능)
   - `asstType`, `atemplateNo`가 2단계에서 확보한 값과 동일하게 전달되는지(값이 다르면 빈 목록이 반환될 수 있음)
   - `resultStatusCdListStr`이 문자열로 직렬화된 형태(`"[\"FAIL\"]"`)로 전달되는지(배열 그대로 넣으면 서버가 인식하지 못할 수 있음)
   - `scanResultCodeMngtDetail`이 Agent #1C Tools 포트에 연결되어 있는지(다른 Agent에 잘못 연결하지 않았는지)
4. **정상 성공 시에도 나타날 수 있는 경고(에러 아님)**: 2단계와 마찬가지로 `mgmtOrgId` 관련 WARN이 함께 나올 수 있으며 이는 데이터 정합성 경고로 플로우 진행에 영향 없다.
5. **필터 정합성 확인 필요(2026-07-14, 실제 콘솔 로그 기반 확인)**: `severity="4"`로 요청했음에도 응답 `scanRsltCodeList[]`에 `severity="5"` 항목이 포함되는 사례가 확인됨(`08-ivms_openapi_spec.md` 4.2절 참고). `severity`가 필수 입력 파라미터라는 것이 서버의 엄격한 필터링을 보장하지 않는 것으로 보인다. → **대응**: Agent #1C System Prompt에 "severity 값이 요청한 값과 다른 항목은 제외" 규칙을 반영했다(위 프롬프트 참고).
6. **컨텍스트 예산 오류(`context limit exceeded`)가 재발하는지** — 재발 시 취약점 항목 수가 매우 많은 조직인지 확인하고, 필요하면 Agent #1C를 페이지 단위로 한 번 더 분할하는 것을 검토
7. 검증되면 4단계(`guidelineCdInfo` 추가)로 넘어간다.

---

### 7.4 [4단계] Agent #1C 보강 + `guidelineCdInfo` Tool 추가

**목표**: 3단계에서 확보한 4개 키(`resultIfKey`→`aresultNo`, `guidelineIfKey`, `itemCode`, `agentServerNm`)로 각 미조치 항목의 조치방법(`measure`) 원문을 조회한다. 이 호출은 3단계에서 이미 확보한 값만 사용하고 새로운 "큰 응답"(자산 목록·취약점 목록 같은 배열)을 만들어내지 않으므로, 신규 Agent를 만들지 않고 **Agent #1C에 4번째 Tool로 그대로 얹는다**(Agent #1D로 분리하지 않음 — 3-Agent 구조 유지).

> **개정 이력(2026-07-14, Agent 분할)**: 이 절은 원래 Agent #1 하나에 `guidelineCdInfo`를 4번째 Tool로 추가하는 구조로 작성되어 있었고, "Agent #1C에 얹을지 신규 Agent #1D로 뺄지는 검증 시점에 판단한다"는 유보 문구가 있었다. 이번에 3-Agent 구조로 확정 재작성하면서 **Agent #1C에 4번째 Tool로 추가**하는 쪽으로 결정했다 — `guidelineCdInfo`는 항목당 1회 호출이고 응답 크기(진단기준/현황/조치방법 텍스트 3개)가 `mngtListDetail`/`scanResultCodeMngtDetail`의 배열 응답보다 작아, 별도 Agent로 컨텍스트를 나눌 실익이 크지 않기 때문이다. 아래 `guidelineCd` 응답 불일치 관련 개정 이력은 Agent 분할과 무관하게 여전히 유효하므로 그대로 유지한다.

**추가로 배치할 노드 (Tool 1개, 신규 Agent 없음)**

| 노드 | 라벨 |
|---|---|
| API Request Tool | `API Request Tool: guidelineCdInfo` |

**추가 연결 (1개)**

| 순서 | From | To | 비고 |
|---|---|---|---|
| 12 | API Request Tool(`guidelineCdInfo`) → `Tool` | Agent #1C → `Tools` | 빨간, 3단계까지 연결해둔 `scanResultCodeMngtDetail`과 같은 Tools 포트에 추가(Agent #1A/#1B의 Tools 포트에는 연결하지 않는다) |

1~3단계 및 2-2단계의 연결(`Chat Input→Agent #1A`, `Agent #1A→Agent #1B`, `Agent #1B→Agent #1B-2`, `Agent #1B-2→Agent #1C`, `Agent #1C→Chat Output`)은 그대로 유지한다.

**API Request Tool 배치 — `guidelineCdInfo`**

2-5절(322~369행) 기준. 이 Tool은 **GET + Query Params** 방식으로, Agent #1C에 이미 연결된 `scanResultCodeMngtDetail`(POST+Body)과 파라미터 위치가 다르다는 점에 주의한다.

| 항목 | 값 |
|---|---|
| 노드 라벨 | `API Request Tool: guidelineCdInfo` |
| Tool Mode | ON |
| URL | `https://ivms.lguplus.co.kr/ivms/api/guidelineCdInfo` |
| Method | GET |
| Connect Timeout / Read Timeout | 3000ms / 10000ms (GET 계열이므로 1절 공통 설정 기준 기본값 사용 — POST+Body 계열처럼 30000ms로 늘릴 필요 없음) |
| Query Params | `aresultNo`(integer, Y), `guidelineIfKey`(integer, Y), `guidelineCd`(string, Y), `itemCode`(string, Y), `agentServerNm`(string, Y) — 2-5절 표 그대로 |
| Header | 공통 인증 헤더 4종(GET이므로 `Content-Type` 불필요) |
| 툴 설명 | `취약점 항목의 상세 조치가이드(진단기준/현황/조치방법)를 조회하는 도구. aresultNo, guidelineIfKey, itemCode, agentServerNm 4개 값이 모두 있어야 정확한 항목이 조회된다. 이 4개 값은 같은 Agent가 방금 호출한 scanResultCodeMngtDetail 응답에서 얻는다(aresultNo는 resultIfKey 값을 사용). 주의: 응답이 요청한 guidelineCd와 무관하게 다른 항목을 반환하는 경우가 있으므로, 응답의 guidelineCd가 원래 요청한 항목과 일치하는지 반드시 재확인해야 한다.` |

> ⚠️ **2-5절 369행의 중대 이슈 재확인**: 요청 시 `guidelineCd`를 지정해도 응답이 그 코드로 필터링되지 않고 `aresultNo`+`guidelineIfKey`+`itemCode`+`agentServerNm` 조합으로 응답이 결정되는 것으로 실제 curl 테스트에서 확정됐다. 아래 System Prompt에 응답 불일치 방어 지시를 반드시 포함해야 한다.

**Agent #1C System Prompt (4단계 반영 — 3단계 프롬프트 위에 이어붙임)**

7.3절/2-8절의 `scanResultCodeMngtDetail` 호출 지시는 그대로 두고, 그 아래에 조치가이드 조회 지시와 최종 출력 형식을 추가한다(기존 "담당자별 표 정리" 출력 지시는 이 지시로 대체된다).

```
scanResultCodeMngtDetail로 확보한 각 미조치 항목(guidelineIfKey, itemCode, agentServerNm 조합)마다
이어서 guidelineCdInfo를 호출한다.

- aresultNo 파라미터에는 방금 조회한 resultIfKey 값을 사용한다.
- guidelineCd 파라미터에는 방금 조회한 guidelineCd 값을 그대로 전달한다.
- ⚠️ 매우 중요: 이 API는 요청한 guidelineCd와 무관하게 다른 항목의 데이터를 반환하는 경우가
  실제로 확인되었다. 응답을 받으면 반드시 응답 본문의 guidelineCdInfo.guidelineCd 값이 방금
  요청에 사용한 guidelineCd와 일치하는지 확인한다. 일치하지 않으면 그 응답은 신뢰할 수 없는
  것으로 간주하고, 해당 항목은 "조치가이드 조회 실패(응답 불일치)"로 표시해 다음 단계로
  넘긴다. 이 불일치 항목을 임의로 다른 값으로 대체하거나 추측해서 채우지 않는다.
- 동일한 (aresultNo, guidelineIfKey, itemCode, agentServerNm) 조합에 대해 이미 조회한 적이
  있다면 다시 호출하지 않고 캐시된 결과를 재사용한다(같은 자산 내 동일 항목 중복 방지).

모든 항목의 조치가이드 조회가 끝나면, 담당자별로 asstNm, hostNm 등 입력으로 받은 담당자·자산
정보와 함께 guidelineCd, guidelineNm, severity, criteria(조치기준), analysisInfo(현황),
measure(조치방법) 원문을 아래 구조로 정리해 출력한다. 가공하거나 요약하지 말고 수집한 원문
그대로 전달한다.

담당자: chrgNm 값(chrgId 값)
  자산: asstCode 값 (hostNm 값)
    - 항목: guidelineCd 값 guidelineNm 값 (severity: severity 값)
      최근진단일: timeEndYmd 값
      조치기준(criteria): criteria 원문 그대로
      현황(analysisInfo): analysisInfo 원문 그대로
      조치방법(measure): measure 원문 그대로

위 구조를 담당자 수만큼, 각 담당자의 미조치 항목 수만큼 반복해 모두 나열한다. 데이터를 임의로
축약하거나 누락하지 않는다. "조치가이드 조회 실패(응답 불일치)"로 표시된 항목은 criteria/
analysisInfo/measure 없이 그 표시만 남긴다.
```

- `Jailbreak Check`: OFF
- `Model`: `azure_openai:gpt-4.1`(2-8절과 동일 — Tool이 2개로 늘고 항목 수만큼 반복 호출되므로 유지)

**Chat Output**
- 연결 변경 없음(3단계와 동일하게 Agent #1C `Response`를 그대로 수신). 이 시점에서 Agent #1C의 Tools 구성(`scanResultCodeMngtDetail` + `guidelineCdInfo` 2개)과 System Prompt(4단계 전체)는 2-8절의 최종본과 동일해진다.

**4단계 검증 방법**

1. Chat Input에 `"Enterprise SW프로덕트개발팀 미조치 현황 및 조치가이드 확인해줘"` 입력 후 전체 플로우 실행
2. 기대 응답: 담당자별 자산·취약 항목마다 `criteria`(진단기준)/`analysisInfo`(현황)/`measure`(조치방법) 원문이 포함된 응답이 나타나는지 확인
3. 정상 동작하지 않으면 다음을 순서대로 점검:
   - `guidelineCdInfo`가 Agent #1C Tools 포트에 연결되어 있는지(다른 Agent에 잘못 연결하지 않았는지)
   - `guidelineCdInfo` Query Params에 5개 필드(`aresultNo`, `guidelineIfKey`, `guidelineCd`, `itemCode`, `agentServerNm`)가 모두 등록되어 있는지(POST Tool과 달리 이 Tool은 Query Params를 비우면 안 됨 — GET 방식이므로 파라미터가 여기 들어가야 함)
   - `aresultNo`에 `resultIfKey` 값이 들어가는지(필드명이 다르다는 점에서 혼동하기 쉬움 — Agent가 잘못된 필드를 매핑하지 않는지 System Prompt 재확인)
   - 응답의 `guidelineCdInfo.guidelineCd`가 요청한 값과 다르게 나오는 경우, System Prompt의 방어 로직(불일치 시 "조회 실패"로 표시)이 실제로 동작하는지(Agent가 불일치를 무시하고 잘못된 데이터를 그대로 쓰지 않는지)
   - 항목 수가 많아 응답이 느려지면 Read Timeout(GET 계열 10000ms)이 부족한지 확인 — 부족하면 `mngtListDetail`/`scanResultCodeMngtDetail`과 동일하게 상향 조정 검토
   - **컨텍스트 예산 오류(`context limit exceeded`)가 재발하는지** — Agent #1C에 Tool이 2개(`scanResultCodeMngtDetail` + `guidelineCdInfo`)로 늘고 항목당 추가 호출이 붙으므로, 재발 시 Agent #1C를 `scanResultCodeMngtDetail`(Agent #1C)과 `guidelineCdInfo`(신규 Agent #1D)로 다시 분리하는 것을 검토한다
4. 검증되면 5단계(Agent #2, Human Approval, Language Model을 끼워 넣어 최종 구조 완성)로 넘어간다.

---

### 7.5 [5단계] Agent #2 · Human Approval · Language Model 삽입 — 최종 구조 완성

**목표**: 1~4단계에서 검증한 Agent #1A→#1B→#1C(IVMS 데이터 수집)의 최종 출력(Agent #1C `Response`)을 Chat Output에 직결하던 임시 연결을 끊고, 그 사이에 Agent #2(압박메시지+조치가이드 생성) → Human Approval → Language Model(패스스루)을 끼워 넣어 2절의 최종 구조(4절 구조도)를 완성한다.

**끊어야 할 연결 (1개)**

| 대상 | 비고 |
|---|---|
| Agent #1C `Response` → Chat Output `Input` | 3단계(7.3절)부터 유지해온 임시 연결. 이 연결선을 삭제한다 |

**추가로 배치할 노드 (3개)**

| 노드 | 라벨 |
|---|---|
| Agent | `Agent #2: 담당자별 압박메시지+조치가이드 생성` |
| Human Approval | 기본값 |
| Language Model | 기본값 |

**추가 연결 (4개, 기존 연결표 3.절과 동일)**

| 순서 | From | To | 비고 |
|---|---|---|---|
| 12 | Agent #1C → `Response` | Agent #2 → `Input` | 파란 점선 — 방금 끊은 임시 연결 대신 이 연결로 대체 |
| 13 | Agent #2 → `Response` | Human Approval → `Target Message` | 파란, 필수 포트 |
| 14 | Human Approval → `Human Approval` | Language Model → `Input` | Chat Output 직결 불가 → 경유 필수(2-11절 근거) |
| 15 | Language Model → `Response` | Chat Output → `Input` | **Chat Output 쪽에서 드래그 시작**(04번 문서 151행 제약 — 2-12절과 동일 주의) |

**Agent #2 구성**

2-9절의 값을 그대로 사용한다.

| 항목 | 값 |
|---|---|
| 노드 라벨 | `Agent #2: 담당자별 압박메시지+조치가이드 생성` |
| Input | Agent #1C `Response` 연결(위 표 12행) |
| Tools | 연결 없음 |
| Jailbreak Check | OFF |
| Model | `azure_openai:gpt-4.1-mini` |
| System Prompt | 2-9절 원문 그대로(미조치 판단 및 선별 기준, 담당자별 섹션 출력 구조, 전체 마무리 문구 — "Agent #1C가 수집한" 표현 포함) |

**Human Approval 구성**

2-10절의 값을 그대로 사용한다.

| 항목 | 값 |
|---|---|
| Target Message | Agent #2 `Response` 연결(위 표 13행) |
| question | `"위 담당자분들의 압박메시지 및 조치가이드를 이 내용 그대로 승인하시겠습니까?"`(고정 문자열 직접 입력 — 노드 연결 아님) |
| Model | `azure_openai:gpt-4.1-mini` |

> 09번 문서 2절 요구사항에 따라 담당자별 개별 승인이 아닌 전체 통합 승인 1회로 구성한다(2-10절과 동일).

**Language Model 구성 (패스스루)**

2-11절의 값을 그대로 사용한다.

| 항목 | 값 |
|---|---|
| Input | Human Approval `Human Approval` 포트 연결(위 표 14행) |
| Model | `azure_openai:gpt-4.1-mini` |
| System Prompt | 2-11절 원문 그대로("승인된 경우"/"거절된 경우" 분기 패스스루 지시) |

> ⚠️ 이 노드는 `04-ixi-enterprise-node-catalog.md` 674/679행 제약(Human Approval 출력 → Chat Output 직접 연결 불가)을 우회하기 위한 필수 경유 노드다(2-11절과 동일 근거).

**Chat Output 최종 연결**

- **Input**: Language Model `Response` 연결(위 표 15행)
- ⚠️ **연결 방향 주의**: Language Model의 `Response` 포트에서 드래그하면 Chat Output이 목록에 나타나지 않는다(04번 문서 151행). 반드시 **Chat Output 노드의 `Input` 포트 쪽에서 드래그를 시작**해 Language Model을 선택할 것(2-12절과 동일 주의).

**5단계 검증 방법**

1. Chat Input에 `"Enterprise SW프로덕트개발팀 미조치 현황 압박 및 조치가이드 생성해줘"` 입력 후 전체 플로우 실행
2. 기대 응답 순서: Agent #1A→#1B→#1C가 순차로 원시 데이터 수집 → Agent #2가 담당자별 압박 메시지+조치가이드 요약 생성 → Human Approval이 승인 질문("위 N명분 ... 승인하시겠습니까?")을 띄움
3. 승인(Yes) 응답 시: Language Model이 "[승인 완료]"를 앞에 붙여 Agent #2의 출력 전체를 그대로 Chat Output에 전달하는지 확인
4. 거절(No) 응답 시: Language Model이 "[거절됨] 요청하신 내용은 승인되지 않아 발송되지 않습니다."만 출력하고 원본 내용을 다시 출력하지 않는지 확인
5. 정상 동작하지 않으면 다음을 순서대로 점검:
   - Agent #1C `Response` → Chat Output `Input` 임시 연결이 실제로 삭제되었는지(삭제하지 않으면 Agent #1C 원시 데이터와 최종 응답이 중복 출력되거나 플로우가 꼬일 수 있음)
   - Human Approval → Language Model → Chat Output 경유 구조가 정확한지(Human Approval을 Chat Output에 직결 시도하면 노드가 목록에 나타나지 않음 — 04번 문서 674/679행 제약)
   - Chat Output은 반드시 Chat Output 쪽에서 드래그해 Language Model과 연결했는지(반대 방향으로 시도하면 실패)
   - Agent #2가 "조치가이드 조회 실패(응답 불일치)" 항목을 임의로 다른 값으로 채우지 않고 그대로 "수동 확인 필요"로 표기하는지(2-9절 지시 준수 여부)
6. 검증되면 플로우 A 전체 구성이 완료된 것이며, 6절의 "구성 후 확인 체크리스트"로 최종 점검한다.

---
