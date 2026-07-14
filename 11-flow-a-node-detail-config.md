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

---

## 1. 인증/헤더 관련 사전 확인 사항 (플레이스홀더)

08번 문서에는 API Key, Bearer Token 등 구체적인 인증 헤더 스펙이 명시되어 있지 않다. 아래 값은 **IVMS 운영팀 확인 후 실제 값으로 교체해야 하는 플레이스홀더**다.

| Header Key | Header Value (플레이스홀더) | 비고 |
|---|---|---|
| `Authorization` | `Bearer {IVMS_API_TOKEN}` | IVMS 운영팀에 인증 방식(API Key/Bearer/Basic 등) 확인 필요 |
| `Content-Type` | `application/json` | POST(`mngtListDetail`, `scanResultCodeMngtDetail`) 요청에만 필요 |

> ⚠️ **IVMS 운영팀 확인 필요**: 실제 배포 전 반드시 (1) 인증 헤더 방식, (2) `{IVMS_BASE_URL}` 실제 도메인, (3) IP 화이트리스트 등록 필요 여부를 확인할 것.

모든 API Request Tool 노드 공통 설정:
- **Tool Mode**: ON (Agent의 Tools 포트에 연결하려면 필수)
- **Connect Timeout**: 1000~3000ms
- **Read Timeout**: GET 계열(`orgList`, `assetSsrcceTemplate`, `assetCategory` 등)은 10000ms. **POST+Body 계열(`mngtListDetail`, `scanResultCodeMngtDetail`)은 30000ms로 설정**(2026-07-14 실제 캔버스 테스트 결과: 10000ms 이하에서는 응답이 오기 전에 타임아웃되어 실패 처리됨 — 이전에 인증 서명 만료로 추정했던 실패의 실제 원인 중 하나였음)
- **Query Params**: POST+Body 계열 Tool은 Query Params를 반드시 비워둘 것(값이 남아있으면 URL에 불필요한 쿼리스트링이 붙어 요청이 실패함 — 2026-07-14 실제 확인)

---

## 2. 노드별 상세 구성

### 2-1. Chat Input

- **파라미터**: 없음(플로우 시작 노드)
- **연결**: `User Message` → Agent #1 `Input`
- **예상 사용자 입력 예시**: `"서비스인프라팀 미조치 현황 압박 및 조치가이드 생성해줘"`

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
| `X-Global-Transaction-ID` | `test` | Y | 전역 트랜잭션 ID. curl 캡처는 `test` 고정값을 사용했으나, 실제로는 호출마다 고유한 트랜잭션 ID를 발급해야 하는 필드로 추정됨. **캔버스에 그대로 `test`로 고정 입력할지, 매 호출마다 동적으로 생성할지는 IVMS 운영팀 확인 필요.** ixi-enterprise API Request 노드의 Header Value는 정적 텍스트만 지원하므로, 동적 생성이 필수라면 별도 사전 처리(Function 노드 등)가 필요하나 04번 문서 노드 카탈로그상 그런 노드가 없어 **우선 고정값 `test`로 등록** |
| `X-APP-NAME` | `IVMS` | Y | 호출 애플리케이션명 고정값. 모든 IVMS API 공통(다른 3개 API Request Tool에도 동일하게 등록해야 함) |
| `X-AuthorizationTime` | `20250804T145618+0900` | Y | 인증 서명 생성 시각(`YYYYMMDDTHHmmss+0900`, KST). ⚠️ curl 캡처의 값은 **2025-08-04 캡처 당시 시각의 스냅샷**이며, `X-Header-Authorization` 서명과 시각이 페어로 검증되는 방식이라면 이 고정값은 **캡처 시점에만 유효하고 실제 운영에서는 매 호출 시각으로 갱신해야 할 가능성이 높음**. 정적 고정값으로 두면 서버가 시각 유효기간 초과로 거부할 위험이 있으므로 운영팀에 "이 값이 고정 가능한지, 매 호출마다 현재 시각으로 재계산해야 하는지" 확인 필요 |
| `X-Header-Authorization` | `kzS7dQYRUHWC7sZb1W1Q+4OzPQEwjJ1fGVMehFOEOMjXbk22ntCbdOICw7JP15d5H4fDC4fI73hOiL0SuOgGdW==` | Y | 인증 서명 값. `X-AuthorizationTime`과 동일한 이유로, 이 값이 시각에 종속된 서명이라면 캡처 당시에만 유효한 값일 수 있다. 서명 생성 알고리즘(입력 문자열 구성, 해시 방식)이 캡처만으로는 특정되지 않으므로 **운영팀에 서명 생성 규칙을 확인해 매 호출 시 재계산하는 방식으로 전환해야 할 수 있음** |

> ⚠️ **본 노드의 Header 설정과 관련한 핵심 리스크**: `X-AuthorizationTime`/`X-Header-Authorization` 두 값이 시각 기반 서명이라면, 위 표의 고정값을 그대로 캔버스에 입력해서는 실 운영 시 인증이 실패(만료)할 가능성이 있다. ixi-enterprise의 API Request 노드는 Header Value에 정적 문자열만 입력 가능하므로(04번 문서 기준 동적 표현식 지원 여부 불명), **IVMS 운영팀에 (1) 이 두 헤더가 고정값으로 장기간 재사용 가능한지, (2) 아니라면 어떤 방식으로 캔버스에서 매 호출마다 갱신할 수 있는지**를 반드시 확인한 뒤 배포해야 한다. 이 부분은 1절의 `Authorization: Bearer {IVMS_API_TOKEN}` 플레이스홀더보다 더 구체적이지만 여전히 **실 운영 재사용 가능 여부가 미확정**인 상태다.
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
      { "orgId": "org_000008", "orgNm": "서비스인프라팀", "useYn": "Y", "pOrgId": "org_000001", "pAffltId": "org_000001" }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

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
  "mgmtOrgId": "org_000008",
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

### 2-6. Agent #1: IVMS 데이터 수집

| 항목 | 값 |
|---|---|
| 노드 라벨 | `Agent #1: IVMS 데이터 수집` |
| Input | Chat Input `User Message` 연결 |
| Tools | API Request Tool #1(orgList), #1-1(assetSsrcceTemplate), #1-2(assetCategory), #2(mngtListDetail), #3(scanResultCodeMngtDetail) — 5개 연결. #4(guidelineCdInfo)는 4단계(7.4절)에서 추가 예정, 아직 미연결 |
| Jailbreak Check | OFF (내부 API 연동 전용) |
| Model | `azure_openai:gpt-4.1` (Tool 호출 스텝이 여러 단계 + 자산/항목 수만큼 반복 호출되므로 `gpt-4.1-mini`보다 상향 권장) |

**System Prompt Template (전체 원문, 2026-07-14 기준 실제 캔버스 반영 — 1~3단계까지 검증 완료, 4단계는 미포함)**

```
사용자가 입력한 조직명과 일치하는 조직을 찾을 때까지 orgList를 호출한다.
- 처음에는 pOrgId="org_000001"(최상위)로 시작해 orgType을 "1"(부문)부터 순차 조회한다.
- 응답의 orgList[].orgNm이 사용자가 언급한 조직명과 일치하면 그 orgList[].orgId를 확정한다.
- 일치하는 조직이 없으면 응답의 orgId를 다음 pOrgId로 사용해 하위 레벨(orgType "2"→"3"→"4")로
  재귀 조회한다. 최대 4단계(부문→그룹→담당→팀)까지만 순회하고, 그래도 없으면
  "해당 조직명을 찾을 수 없습니다: {입력한 조직명}"이라고 응답한다.
- 여러 개의 유사한 조직명이 나오면 사용자에게 확인을 요청하지 말고, 가장 정확히 일치하는
  1건을 선택한다(모호하면 정확 일치 우선, 없으면 부분 일치 중 첫 번째).

조직의 orgId를 확정했으면 이어서 assetSsrcceTemplate과 assetCategory를 호출한다.
- assetSsrcceTemplate은 userId="hhosung"으로 호출해 templateList[]를 받는다. 첫 번째
  항목의 atemplateNo를 templateNo로 사용한다.
- assetCategory는 userId="hhosung", asstCtgrLevel="L"로 호출해 asstCtgrList[]를 받는다.
  이 목록에서 asstType 값을 확인한다(여러 개면 첫 번째 값을 사용).
- templateNo와 asstType은 반드시 이 두 API의 응답값을 사용한다. 임의로 지어내거나
  생략하지 않는다.
- assetCategory로 자산 분류 정보를 확인한다. 응답의 selectedCategory.asstType,
  selectedCategory.asstCtgrId 값을 각각 mngtListDetail 호출 시 asstType, asstLCtgrId
  파라미터로 그대로 사용한다. 임의로 값을 만들거나 생략하지 않는다.

templateNo와 asstType을 확보했으면 이어서 mngtListDetail을 호출한다.
- mngtListDetail 호출 시 userId, asstType, templateNo, asstLCtgrId, diagYear, page,
  pageSize, mgmtOrgId, filter 9개 파라미터만 사용한다. page는 숫자 1, pageSize는 숫자 10으로
  integer 타입으로 넣는다. mgmtOrgId는 조직 ID 확인 단계에서 얻은 값을 그대로 사용한다.
- 응답 assetList[] 중 chrgId, chrgNm(담당자 정보)이 서로 다른 값끼리 묶어 담당자별로
  자산 목록을 구분한다. 담당자별 자산 목록(asstNm, securityScore, timeEndYmd)을 정리해
  응답에 포함한다.
- 응답 건수가 pageSize(10)와 같으면 다음 페이지가 있을 수 있으므로, page를 1씩 증가시켜
  전체 자산을 모두 수집할 때까지 반복 호출한다.

mngtListDetail 응답에서 담당자별 자산 목록(asstCode, hostNm 포함)을 확보했으면 이어서
scanResultCodeMngtDetail을 호출한다.
- assetList[]에서 asstCode와 hostNm을 각각 배열로 추출해 scanResultCodeMngtDetail의
  asstCode, hostNm 파라미터에 그대로 전달한다. 두 배열은 반드시 같은 순서로 대응하도록
  함께 전달한다(asstCode만 또는 hostNm만 전달하지 않는다).
- resultStatusCdListStr은 반드시 문자열 "[\"FAIL\"]"로 지정해 취약(미조치) 항목만 조회한다.
- asstType은 앞서 확보한 값을 그대로 사용하고, vadaYn은 "N"으로 고정한다.
- severity는 "4", atemplateNo는 앞서 확보한 templateNo 값을 그대로 사용한다.
- userId는 "hhosung", page는 숫자 1, pageSize는 숫자 10으로 integer 타입으로 넣는다.
- 응답 scanRsltCodeList[]에서 asstId, asstCode, guidelineIfKey, itemCode, agentServerNm,
  resultIfKey, guidelineCd, guidelineNm, severity, result를 반드시 추출해 보관한다.
- 자산 수가 많아 한 번에 조회되지 않으면 asstCode/hostNm을 나누어 여러 번 호출한다
  (page를 늘려가며 반복).
- 조치가이드 조회는 이번 단계에서 하지 않는다.
```

> 4단계(`guidelineCdInfo` 조회 및 출력 형식 지시문)는 아직 캔버스에서 검증되지 않은 예정 항목이다. 7.4절에서 4단계 Tool을 추가·검증한 뒤, 위 System Prompt 끝에 7.4절의 4단계 지시문과 출력 형식 블록을 이어붙여 최종본을 완성한다(7.4절·7.5절 참고).

---

### 2-7. Agent #2: 담당자별 압박메시지+조치가이드 생성

| 항목 | 값 |
|---|---|
| 노드 라벨 | `Agent #2: 담당자별 압박메시지+조치가이드 생성` |
| Input | Agent #1 `Response` 연결 |
| Tools | 연결 없음 |
| Jailbreak Check | OFF |
| Model | `azure_openai:gpt-4.1-mini` |

**System Prompt Template (전체 원문)**

```
당신은 IVMS 미조치 취약점 데이터를 바탕으로, 담당자별 압박 메시지와 조치가이드
요약을 작성하는 에이전트다. 입력으로 Agent #1이 수집한 담당자별 원시 데이터를 받는다.

【미조치 판단 및 선별 기준】
- 최근진단일(timeEndYmd) 기준 오늘 날짜와 비교해 경과일이 7일 이상인 항목만
  "압박 대상 미조치 항목"으로 선별한다. 경과일이 7일 미만인 항목은
  "조치 유예 기간"으로 간주해 이번 메시지에서 제외한다(단, 완전히 숨기지 않고
  "유예 기간 중" 항목 수만 별도로 한 줄 언급한다).
- severity(취약도: 1=최하 ~ 5=최상)가 높은 항목을 먼저 표기한다(내림차순 정렬).
- Agent #1이 "조치가이드 조회 실패(응답 불일치)"로 표시한 항목은 조치방법 없이
  "조치가이드 조회 실패 — 수동 확인 필요"라고만 표기하고, 임의로 다른 항목의
  조치방법을 대신 채워 넣지 않는다.

【출력 구조 — 담당자가 N명이면 N개 섹션】
담당자마다 아래 두 부분으로 구성된 섹션을 하나씩 작성한다.

=== {담당자명}({담당자ID}) ===

[1] 압박 메시지
- 미조치 항목 총 {건수}건(이 중 심각도 상 이상 {건수}건)이 {경과일 최댓값}일째
  방치되어 있음을 안내하는 정중하지만 명확한 문구를 2~3문장으로 작성한다.
- 유예 기간 중인 항목이 있으면 "별도로 {건수}건은 조치 유예 기간(7일 미만)이라
  이번 안내에서는 제외했습니다"라고 덧붙인다.

[2] 조치가이드 요약
아래 표 형식으로 미조치 항목을 severity 내림차순으로 나열한다.

| 자산(호스트/IP) | 항목코드 | 항목명 | 심각도 | 경과일 | 조치방법 요약 |
|---|---|---|---|---|---|
| {hostNm}/{ipAddrStr} | {guidelineCd} | {guidelineNm} | {severity} | {경과일}일 | {measure 원문에서 【조치방법】 섹션만 발췌, 없으면 measure 전체 앞부분 요약} |

표 아래에 "상세 조치가이드가 필요하면 항목코드를 알려주시면 원문 전체를 안내해
드립니다"라는 안내 문구를 한 줄 추가한다.

【전체 출력 마무리】
모든 담당자 섹션을 순서대로(조치 필요 건수가 많은 담당자 우선) 나열한 뒤,
맨 마지막에 "총 {담당자 수}명, 총 미조치 {건수}건에 대한 안내입니다. 승인해
주시면 이 내용 그대로 보안담당자에게 전달됩니다."라는 요약 문구를 추가한다.
```

---

### 2-8. Human Approval

| 항목 | 값 |
|---|---|
| Target Message | Agent #2 `Response` 연결 |
| question | `"위 {담당자 수}명분 압박메시지 및 조치가이드를 이 내용 그대로 승인하시겠습니까?"` (고정 문자열 입력 — 노드 연결 아님, 직접 텍스트 입력) |
| Model | `azure_openai:gpt-4.1-mini` |

> 09번 문서 2절 요구사항("N명분의 결과물을 하나로 통합해 1회 승인")에 따라, 담당자별 개별 승인이 아닌 전체 통합 승인 1회로 구성한다.

---

### 2-9. Language Model (승인 후 패스스루)

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

### 2-10. Chat Output

- **Input**: Language Model `Response` 연결
- ⚠️ **연결 방향 주의**: Language Model의 `Response` 포트에서 드래그하면 Chat Output이 목록에 나타나지 않는다(04번 문서 151행). 반드시 **Chat Output 노드의 `Input` 포트 쪽에서 드래그를 시작**해 Language Model을 선택할 것.

---

## 3. 전체 연결 순서 요약표

| 순서 | From (출력 포트) | To (입력 포트) | 비고 |
|---|---|---|---|
| 1 | Chat Input → `User Message` | Agent #1 → `Input` | 파란 점선 |
| 2 | API Request Tool(`orgList`) → `Tool` | Agent #1 → `Tools` | 빨간, 다중 연결 |
| 3 | API Request Tool(`mngtListDetail`) → `Tool` | Agent #1 → `Tools` | 동일 포트에 추가 연결 |
| 4 | API Request Tool(`scanResultCodeMngtDetail`) → `Tool` | Agent #1 → `Tools` | 동일 포트에 추가 연결 |
| 5 | API Request Tool(`guidelineCdInfo`) → `Tool` | Agent #1 → `Tools` | 동일 포트에 추가 연결 |
| 6 | Agent #1 → `Response` | Agent #2 → `Input` | 파란 점선 |
| 7 | Agent #2 → `Response` | Human Approval → `Target Message` | 파란, 필수 포트 |
| 8 | Human Approval → `Human Approval` | Language Model → `Input` | Chat Output 직결 불가 → 경유 필수 |
| 9 | Language Model → `Response` | Chat Output → `Input` | **Chat Output 쪽에서 드래그 시작** |

---

## 4. 완성된 구조도

```
[Chat Input]
     │ User Message
     ▼
[Agent #1: IVMS 데이터 수집] ←Tools← [API Req: orgList]
     │                                [API Req: mngtListDetail]
     │                                [API Req: scanResultCodeMngtDetail]
     │                                [API Req: guidelineCdInfo]
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

| 구분 | `10`번 문서 (기존) | 본 문서 (`11`번, 수정) |
|---|---|---|
| API Request Tool 개수 | 4개 (orgList, asstChrgInfo, mngtListDetail, guidelineCdInfo) | 4개 (orgList, mngtListDetail, **scanResultCodeMngtDetail**, guidelineCdInfo) — `asstChrgInfo` 제외, `scanResultCodeMngtDetail` 추가 |
| 담당자 목록 획득 방법 | `asstChrgInfo`로 orgId 기준 별도 조회(불가능한 방식 — API가 자산 단위) | `mngtListDetail` 응답의 `chrgId`/`chrgNm` 필드에서 직접 추출 |
| `guidelineCdInfo` 호출 전 단계 | 없음(파라미터 출처 불명확) | `scanResultCodeMngtDetail`에서 `aresultNo`(=resultIfKey)/`guidelineIfKey`/`itemCode`/`agentServerNm` 확보 후 호출 |
| System Prompt 상세도 | 요약 수준(4줄 내외) | 단계별 파라미터 매핑, 페이지네이션, 응답 불일치 방어 로직까지 전체 원문 포함 |
| URL | `{IVMS_BASE_URL}` 플레이스홀더만 표기 | 정확한 엔드포인트 경로 + Header/Query/Body 전체 필드 명시 |

---

## 6. 구성 후 확인 체크리스트 (플로우 A 전용)

- [ ] Agent #1의 Tools 포트에 4개 API Request Tool(orgList, mngtListDetail, scanResultCodeMngtDetail, guidelineCdInfo)이 모두 연결되었는지 확인 — `asstChrgInfo`는 연결하지 않음
- [ ] 각 API Request Tool이 Tool Mode ON 상태인지 확인
- [ ] `mngtListDetail`, `scanResultCodeMngtDetail`의 Method가 POST로 설정되었는지 확인(GET으로 잘못 설정하기 쉬움)
- [ ] `guidelineCdInfo` Query Params에 5개 필드(`aresultNo`, `guidelineIfKey`, `guidelineCd`, `itemCode`, `agentServerNm`)가 모두 등록되었는지 확인
- [ ] Agent #1 System Prompt에 "guidelineCdInfo 응답 불일치 시 방어 로직" 포함 여부 확인
- [ ] Human Approval → Language Model → Chat Output 경유 구조 확인(직결 시도 금지)
- [ ] Chat Output은 Chat Output 쪽에서 드래그해 Language Model과 연결했는지 확인
- [ ] `{IVMS_BASE_URL}`, `{IVMS_API_TOKEN}` 플레이스홀더를 실제 값으로 교체했는지 확인(IVMS 운영팀 확인 후)

---

## 7. 단계적 구성(Staged Build) 가이드

### 7.0 왜 단계적으로 구성하는가

ixi-enterprise에는 단일 노드 독립 실행(Test Step), Pin Data, Execution Log, Input/Output 확인 패널이 없다(`07-ixi-enterprise-requirements-spec.md` REQ-009~012). 즉 노드를 하나 추가할 때마다 **Chat Input부터 전체 플로우를 재실행**해야만 그 노드가 제대로 동작하는지 확인할 수 있다. 이 제약 때문에 4개 API Request Tool을 한 번에 다 연결하고 System Prompt도 4단계를 한꺼번에 작성한 뒤 처음 실행하면, 실패했을 때 원인이 어느 Tool/어느 프롬프트 단락에 있는지 특정하기 어렵다.

따라서 본 절에서는 2절의 최종 구성을 **5단계로 쪼개어 순서대로 쌓아 올리는 방식**을 제시한다. 각 단계는 "그 시점까지 연결된 노드만으로 실행 가능한 최소 플로우"이며, 다음 단계로 넘어가기 전에 반드시 전체 실행으로 검증한다.

| 단계 | 이번 단계에서 추가하는 것 | 임시 종착점 |
|---|---|---|
| 1단계 | Chat Input, Agent #1(Tool: `orgList` 1개만), Chat Output | Chat Output |
| 2단계 | `mngtListDetail` Tool 추가, System Prompt 2단계 지시 추가 | Chat Output(동일) |
| 3단계 | `scanResultCodeMngtDetail` Tool 추가, System Prompt 3단계 지시 추가 | Chat Output(동일) |
| 4단계 | `guidelineCdInfo` Tool 추가, System Prompt 4단계 지시 추가 | Chat Output(동일) |
| 5단계 | Agent #2, Human Approval, Language Model을 Chat Output 앞에 끼워 넣어 최종 구조 완성 | Chat Output(최종) |

각 단계의 상세 구성은 이후 절에서 순서대로 다룬다. 본 문서에서는 우선 **1단계**만 작성한다.

---

### 7.1 [1단계] Chat Input → Agent #1(orgList만) → Chat Output

**목표**: 사용자가 조직명을 말하면 Agent #1이 `orgList` Tool만으로 해당 조직의 `orgId`를 찾아 응답하는지 확인한다. 담당자/미조치/가이드 로직은 아직 다루지 않는다.

**배치할 노드 (3개)**

| 노드 | 라벨 |
|---|---|
| Chat Input | 기본값 |
| Agent | `Agent #1: IVMS 데이터 수집` |
| Chat Output | 기본값 |

> ⚠️ 최종 구성(2절)에는 Agent #1 뒤에 Agent #2 → Human Approval → Language Model → Chat Output이 이어지지만, 1단계에서는 검증 대상이 아니므로 **Agent #1의 Response를 Chat Output에 바로 연결**한다. 이 임시 연결은 4단계까지 유지하다가 5단계에서 끊고 Agent #2로 교체한다.

**연결 (2개)**

| 순서 | From | To | 비고 |
|---|---|---|---|
| 1 | Chat Input → `User Message` | Agent #1 → `Input` | 파란 점선 |
| 2 | API Request Tool(`orgList`) → `Tool` | Agent #1 → `Tools` | 빨간 |
| 3 | Agent #1 → `Response` | Chat Output → `Input` | **Chat Output 쪽에서 드래그 시작**(04번 문서 151행 제약) |

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

**Agent #1 System Prompt (1단계 전용 — 실전 검증 버전)**

최종 4단계 System Prompt(2-6절)를 전부 쓰지 않고, 이번 단계에서 검증할 1단계 지시만 넣는다.

> ⚠️ **개정 이력**: 최초 작성한 버전(응답 형식 강제 + "아직 ~하지 않는다" 범위 제한 문구 포함)은 실제 캔버스 실행 시 오류가 발생했다. 아래는 실제 캔버스에서 **성공이 확인된 프롬프트**를 기준으로, 원래 의도했던 "재귀 조회 상한(최대 4단계)"과 "1단계 범위로 응답 한정" 지시만 최소한으로 보강한 버전이다. 응답 형식을 문장으로 강제하던 지시는 제거했다 — Tool 호출 흐름과 충돌해 실패를 유발한 것으로 추정된다.

```
사용자가 입력한 조직명과 일치하는 조직을 찾을 때까지 orgList를 호출한다.

- 처음에는 pOrgId="org_000001"(최상위)로 시작해 orgType을 "1"(부문)부터 순차 조회한다.
- 응답의 orgList[].orgNm이 사용자가 언급한 조직명과 일치하면 그 orgList[].orgId를 확정한다.
- 일치하는 조직이 없으면 응답의 orgId를 다음 pOrgId로 사용해 하위 레벨(orgType "2"→"3"→"4")로 재귀 조회한다. 최대 4단계(부문→그룹→담당→팀)까지만 순회하고, 그래도 없으면 "해당 조직명을 찾을 수 없습니다: {입력한 조직명}"이라고 응답한다.
- 여러 개의 유사한 조직명이 나오면 사용자에게 확인을 요청하지 말고, 가장 정확히 일치하는 1건을 선택한다(모호하면 정확 일치 우선, 없으면 부분 일치 중 첫 번째).
- 담당자 조회, 미조치 항목 조회, 조치가이드 조회는 이번 단계에서 수행하지 않는다.
```

- `Jailbreak Check`: OFF
- `Model`: `azure_openai:gpt-4.1-mini`

**Chat Output**
- `Input`: Agent #1 `Response` 연결(위 표 3행)

**1단계 검증 방법**

1. Chat Input에 `"서비스인프라팀 조직 ID 확인해줘"` 입력 후 전체 플로우 실행
2. 기대 응답: `orgId`(`org_000008`)와 조직명(`서비스인프라팀`)이 포함된 응답(문장 형식은 강제하지 않음 — 위 개정 이력 참고)
3. 응답에 `orgId`가 포함되지 않거나 "Tool에 접근할 수 없다"는 취지의 응답이 나오면, 다음을 순서대로 점검:
   - API Request Tool의 Tool Mode가 ON인지, Tools 포트에 실제 연결선이 있는지
   - Header 4종이 2-2절과 정확히 일치하는지 (특히 `X-AuthorizationTime`/`X-Header-Authorization`은 캡처 시점 값이라 만료됐을 수 있음 — 2-2절 96행 경고 참고)
   - System Prompt에 응답 형식을 문장으로 강제하는 지시나 "이번 단계에서 하지 않는다"류 범위 제한 문구가 들어가 있지 않은지(Tool 호출 흐름과 충돌해 오류를 유발한 사례 있음 — 위 개정 이력 참고)
4. 검증되면 2단계(`mngtListDetail` 추가)로 넘어간다.

---

### 7.2 [2단계] `mngtListDetail` Tool 추가

**목표**: 1단계에서 확정한 `orgId`를 이어받아, 이번 단계에서는 `mngtListDetail`을 `orgId`(→`mgmtOrgId`)로 직접 호출해 **미조치 자산과 담당자 정보(chrgId/chrgNm)를 동시에** 획득한다.

> **개정 이력(2026-07-10, 1차)**: 이 절은 원래 `asstChrgInfo`를 선행 Tool로 두고 그 출력(`chrgId`)을 `mngtListDetail`의 `rspnMngId`에 넘기는 2-Tool 구조로 작성되어 있었다. 그러나 실제 캔버스 테스트에서 `asstChrgInfo`를 `orgId`로 호출하자 `msgCd: E`(필수 컬럼 확인 필요) 오류가 발생했고, 08번 문서 2.4절을 재조사한 결과 `asstChrgInfo`의 실제 필수 파라미터는 `asstId`+`asstVer`(**자산 1건 단위**)이며 `orgId` 입력 파라미터 자체가 없다는 사실이 확인되었다(09번 문서 50/95행, 10번 문서 91행의 "asstChrgInfo로 orgId 기준 담당자 목록 조회"라는 서술은 실제 API 스펙과 어긋난 잘못된 가정이었다). `asstChrgInfo`는 플로우 A의 필수 체인에서 제외하고, 조직 기준 담당자 목록은 `mngtListDetail` 응답의 `chrgId`/`chrgNm` 필드(자산 레코드에 이미 포함, 08번 문서 2.2절 `assetList[].chrgId`)에서 직접 획득하는 것으로 1차 수정했다.
>
> **개정 이력(2026-07-10, 2차)**: 1차 수정 후 실제 캔버스에서 `mngtListDetail`을 `mgmtOrgId` + `filter`만으로 호출했으나 다음 두 단계의 오류가 순차로 발생했다.
> 1. **HTTP 405 Method Not Allowed**: 캔버스의 `mngtListDetail` Tool 노드 Method 드롭다운이 GET으로 설정되어 있었음(POST 전용 엔드포인트인데 GET으로 호출). → Method를 POST로 수정.
> 2. **msgCd: E, "필수 컬럼 확인 필요"**: Method를 POST로 고치고 Body에 `mgmtOrgId`+`filter`만 넣어 재호출했으나 여전히 실패. 콘솔 로그상 요청 자체는 정확히 도달했음(`mgmtOrgId=org_000991`, `filter=SECURITY_SCORE neq 100` 확인됨)에도 거부된 것으로 보아, IVMS 서버는 08번 문서 스펙 표의 "필수: N" 표기와 무관하게 **`asstType`(자산타입) 또는 `templateNo`(진단템플릿) 같은 자산 유형 특정 파라미터가 없으면 컬럼을 결정할 수 없어 거부**하는 것으로 확인됐다. 08번 문서 515~523행의 유일한 성공 예시(`userId`+`asstType`+`templateNo`+`diagYear`+`asstLCtgrId` 조합)가 이 추정을 뒷받침한다.
>
> 이 `asstType`/`templateNo` 값은 조직·자산마다 다르므로 System Prompt에 고정값으로 넣을 수 없다. 08번 문서 1.2절(`assetSsrcceTemplate`, 153~183행)과 1.3절(`assetCategory`, 189~260행)에 각각 `templateNo`와 `asstType`(→`asstCtgrList[].asstType`)을 조회하는 API가 이미 존재하므로, 이 두 API를 `mngtListDetail` 호출 전에 추가로 호출해 값을 동적으로 확정하는 구조로 2차 수정한다.
>
> **개정 이력(2026-07-14, 3차)**: 2차 수정 후에도 `mngtListDetail`이 운영 서버(`ivms.lguplus.co.kr`)에서 `msgCd: E`로 계속 실패해, 한동안 `X-Header-Authorization` 서명 만료를 원인으로 의심하고 IVMS 운영팀 문의가 필요하다는 결론까지 갔었다. 그러나 실제로는 인증 서명 문제가 아니라 캔버스 Tool 노드의 **설정 2가지**가 원인이었음이 확인됐다: (1) Query Params 칸에 값이 남아있어 POST+Body 요청에 불필요한 쿼리스트링이 붙었던 점, (2) Read Timeout이 10000ms로 짧아 응답(자산 1000건 이상 조회 시 수 초 이상 소요)이 오기 전에 타임아웃 처리된 점. Query Params를 전부 비우고 Read Timeout을 **30000ms**로 늘리자 정상 성공(`listCount` 정상 반환)이 확인됐다. 성공 응답에서도 `[WARN] mgmtOrgId 불일치/누락` 경고가 함께 나올 수 있으나 이는 API 실패가 아니라 데이터 정합성 경고이며 플로우 진행에는 영향 없다.

**추가로 배치할 노드 (Tool 3개, Agent/Chat Input/Chat Output은 1단계에서 이미 배치됨)**

| 노드 | 라벨 |
|---|---|
| API Request Tool | `API Request Tool: assetSsrcceTemplate` |
| API Request Tool | `API Request Tool: assetCategory` |
| API Request Tool | `API Request Tool: mngtListDetail` |

**추가 연결 (3개)**

| 순서 | From | To | 비고 |
|---|---|---|---|
| 4 | API Request Tool(`assetSsrcceTemplate`) → `Tool` | Agent #1 → `Tools` | 빨간, 1단계 `orgList` 연결과 같은 Tools 포트에 추가 |
| 5 | API Request Tool(`assetCategory`) → `Tool` | Agent #1 → `Tools` | 빨간, 동일 포트에 추가 |
| 6 | API Request Tool(`mngtListDetail`) → `Tool` | Agent #1 → `Tools` | 빨간, 동일 포트에 추가 |

1단계의 연결(Chat Input→Agent #1, Agent #1→Chat Output)은 그대로 유지한다.

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

**Agent #1 System Prompt (2단계 전용 — 1단계 위에 이어붙임)**

1단계 프롬프트(7.1절)의 4개 항목(조직 조회 로직)은 그대로 두고, 그 아래에 템플릿/자산분류 확인 + 미조치 자산 + 담당자 조회 지시를 추가한다.

```
사용자가 입력한 조직명과 일치하는 조직을 찾을 때까지 orgList를 호출한다.

- 처음에는 pOrgId="org_000001"(최상위)로 시작해 orgType을 "1"(부문)부터 순차 조회한다.
- 응답의 orgList[].orgNm이 사용자가 언급한 조직명과 일치하면 그 orgList[].orgId를 확정한다.
- 일치하는 조직이 없으면 응답의 orgId를 다음 pOrgId로 사용해 하위 레벨(orgType "2"→"3"→"4")로 재귀 조회한다. 최대 4단계(부문→그룹→담당→팀)까지만 순회하고, 그래도 없으면 "해당 조직명을 찾을 수 없습니다: {입력한 조직명}"이라고 응답한다.
- 여러 개의 유사한 조직명이 나오면 사용자에게 확인을 요청하지 말고, 가장 정확히 일치하는 1건을 선택한다(모호하면 정확 일치 우선, 없으면 부분 일치 중 첫 번째).

조직의 orgId를 확정했으면 이어서 assetSsrcceTemplate과 assetCategory를 호출한다.

- assetSsrcceTemplate은 userId="admin"으로 호출해 templateList[]를 받는다. 첫 번째 항목의 atemplateNo를 templateNo로 사용한다.
- assetCategory는 userId="admin", asstCtgrLevel="L"로 호출해 asstCtgrList[]를 받는다. 이 목록에서 asstType 값을 확인한다(여러 개면 첫 번째 값을 사용).
- templateNo와 asstType은 반드시 이 두 API의 응답값을 사용한다. 임의로 지어내거나 생략하지 않는다.

templateNo와 asstType을 확보했으면 이어서 mngtListDetail을 호출한다.

- mngtListDetail 호출 시 mgmtOrgId 파라미터에는 앞서 확정한 orgId 값을, asstType과 templateNo에는 방금 확보한 값을 그대로 사용한다.
- filter.xorStr에는 {"logic":"and","filters":[{"field":"SECURITY_SCORE","operator":"neq","value":100}]}를 고정으로 사용해 미조치(취약) 자산만 조회한다.
- 응답 assetList[] 중 chrgId, chrgNm(담당자 정보)이 서로 다른 값끼리 묶어 담당자별로 자산 목록을 구분한다.
- 담당자별 자산 목록(asstNm, securityScore, timeEndYmd)을 정리해 응답에 포함한다. 조치가이드 조회는 이번 단계에서 하지 않는다.
```

- `Jailbreak Check`: OFF
- `Model`: `azure_openai:gpt-4.1-mini` (Tool 호출 스텝이 5단계로 늘었으므로 응답이 불안정하면 `azure_openai:gpt-4.1` 상향 검토)

**Chat Output**
- 연결 변경 없음(1단계와 동일하게 Agent #1 `Response`를 그대로 수신)

**2단계 검증 방법**

1. Chat Input에 `"서비스인프라팀 미조치 자산 확인해줘"` 입력 후 전체 플로우 실행
2. 기대 응답: 서비스인프라팀 소속 담당자별로 구분된 미조치 자산 목록(자산명/보안점수/최근진단일 포함)이 응답에 나타나는지 확인 — 문장 형식은 강제하지 않음
3. 정상 동작하지 않으면 다음을 순서대로 점검:
   - `mngtListDetail` Tool의 Method가 정확히 **POST**로 설정되어 있는지(GET으로 남아있으면 HTTP 405 발생 — 실제 확인된 오류)
   - `mngtListDetail` Tool의 **Query Params가 완전히 비어있는지**(POST+Body 방식인데 Query Params에 값이 남아있으면 URL에 불필요한 쿼리스트링이 붙어 요청이 실패함 — 2026-07-14 실제 확인된 오류 원인)
   - `mngtListDetail` Tool의 **Read Timeout이 30000ms로 설정되어 있는지**(기본값 근처인 10000ms 이하로는 응답이 오기 전에 타임아웃 실패 발생 — 2026-07-14 실제 확인된 오류 원인)
   - `assetSsrcceTemplate`/`assetCategory`/`mngtListDetail` 3개 Tool 모두 Tool Mode ON이고 Agent #1 Tools 포트에 연결선이 있는지
   - `mngtListDetail`은 POST이므로 파라미터가 Body(요청 본문 스키마)에 들어가는지(Query Params에 잘못 넣으면 서버가 인식하지 못함)
   - `mngtListDetail` Header에 `Content-Type: application/json`이 추가됐는지(GET 전용이던 1단계 Header 4종에서 하나 더 필요)
   - Body에 `mgmtOrgId`뿐 아니라 `asstType`, `templateNo`가 함께 전달되는지(이 중 하나라도 빠지면 `msgCd: E`, "필수 컬럼 확인 필요" 오류 발생 — 실제 확인된 오류)
   - `mgmtOrgId`에 1단계에서 확정한 `orgId` 값이 정확히 들어가는지(다른 값을 넘기면 빈 목록이 반환될 수 있음)
   - 담당자별 구분이 안 되고 전체 자산이 하나로 뭉쳐 나오면, System Prompt의 "chrgId, chrgNm이 서로 다른 값끼리 묶어 담당자별로 구분" 지시가 Agent에게 제대로 인식되고 있는지 확인
4. **정상 성공 시에도 나타날 수 있는 경고(에러 아님)**: 콘솔 로그에 `[WARN] 요청 mgmtOrgId나 응답 자산 중 일부의 mgmtOrgId가 다름 또는 비어 있음`이 뜰 수 있다. 이는 API 호출 자체는 성공(`listCount` 정상 반환)했으나, 응답으로 돌아온 자산 중 일부가 요청한 조직 소속이 아니거나 `mgmtOrgId`가 비어있다는 **데이터 정합성 경고**이며 플로우 진행을 막지 않는다. 서버 측 조직 필터링이 완전하지 않을 수 있다는 점만 인지하고 다음 단계로 진행한다.
5. 검증되면 3단계(`scanResultCodeMngtDetail` 추가)로 넘어간다.

---

### 7.3 [3단계] `scanResultCodeMngtDetail` Tool 추가

**목표**: 2단계에서 확보한 미조치 자산 목록(`asstCode`, `hostNm`)을 이어받아, 자산별 항목별 취약점 상세(`scanRsltCodeList[]`)를 조회한다. 이 응답에서 다음 단계(`guidelineCdInfo`)가 필요로 하는 4개 키(`guidelineIfKey`, `itemCode`, `agentServerNm`, `resultIfKey`)를 확보하는 것이 이번 단계의 핵심이다.

**추가로 배치할 노드 (Tool 1개)**

| 노드 | 라벨 |
|---|---|
| API Request Tool | `API Request Tool: scanResultCodeMngtDetail` |

**추가 연결 (1개)**

| 순서 | From | To | 비고 |
|---|---|---|---|
| 7 | API Request Tool(`scanResultCodeMngtDetail`) → `Tool` | Agent #1 → `Tools` | 빨간, 2단계까지의 연결(`orgList`/`assetSsrcceTemplate`/`assetCategory`/`mngtListDetail`)과 같은 Tools 포트에 추가 |

1~2단계의 연결(Chat Input→Agent #1, Agent #1→Chat Output)은 그대로 유지한다.

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

**Agent #1 System Prompt (3단계 전용 — 1~2단계 위에 이어붙임)**

1~2단계 프롬프트(7.1~7.2절)는 그대로 두고, 그 아래에 항목별 상세 조회 지시를 추가한다.

```
2단계에서 확보한 미조치 자산 목록의 asstCode와 hostNm을 각각 배열로 담아 scanResultCodeMngtDetail을 호출한다.

- asstCode와 hostNm은 반드시 함께(같은 순서로 대응하도록) 전달한다.
- resultStatusCdListStr은 반드시 문자열 "[\"FAIL\"]"로 지정해 취약(미조치) 항목만 조회한다.
- asstType은 2단계에서 확보한 값을 그대로 사용하고, vadaYn은 "N"으로 고정한다.
- severity는 "4", atemplateNo는 2단계에서 확보한 templateNo 값을 그대로 사용한다.
- 응답 scanRsltCodeList[]에서 asstId, asstCode, guidelineIfKey, itemCode, agentServerNm, resultIfKey, guidelineCd, guidelineNm, severity, result를 반드시 추출해 보관한다.
- 자산 수가 많아 한 번에 조회되지 않으면 asstCode/hostNm을 나누어 여러 번 호출한다(page/pageSize 활용).
- 조치가이드 조회는 이번 단계에서 하지 않는다.
```

- `Jailbreak Check`: OFF
- `Model`: `azure_openai:gpt-4.1`(Tool 호출 스텝이 6단계로 늘어나고 자산 수만큼 반복 호출이 필요하므로 `gpt-4.1-mini`보다 상향 권장 — 08번/2-6절 기준과 동일)

**Chat Output**
- 연결 변경 없음(1~2단계와 동일하게 Agent #1 `Response`를 그대로 수신)

**3단계 검증 방법**

1. Chat Input에 `"서비스인프라팀 미조치 취약점 상세 확인해줘"` 입력 후 전체 플로우 실행
2. 기대 응답: 담당자별 자산 목록에 더해, 각 자산의 취약 항목(`guidelineCd`/`guidelineNm`/`severity`)까지 포함된 응답이 나타나는지 확인
3. 정상 동작하지 않으면 다음을 순서대로 점검:
   - `scanResultCodeMngtDetail` Tool의 Method가 정확히 **POST**로 설정되어 있는지(GET으로 남아있으면 HTTP 405 발생)
   - `scanResultCodeMngtDetail` Tool의 **Query Params가 완전히 비어있는지**(값이 남아있으면 요청 실패 — `mngtListDetail`과 동일한 함정)
   - `scanResultCodeMngtDetail` Tool의 **Read Timeout이 30000ms로 설정되어 있는지**
   - Header에 `Content-Type: application/json`이 추가됐는지
   - Body에 `asstCode`와 `hostNm`이 반드시 함께(배열로) 전달되는지(둘 중 하나만 전달하면 실패 가능)
   - `asstType`, `atemplateNo`가 2단계에서 확보한 값과 동일하게 전달되는지(값이 다르면 빈 목록이 반환될 수 있음)
   - `resultStatusCdListStr`이 문자열로 직렬화된 형태(`"[\"FAIL\"]"`)로 전달되는지(배열 그대로 넣으면 서버가 인식하지 못할 수 있음)
4. **정상 성공 시에도 나타날 수 있는 경고(에러 아님)**: 2단계와 마찬가지로 `mgmtOrgId` 관련 WARN이 함께 나올 수 있으며 이는 데이터 정합성 경고로 플로우 진행에 영향 없다.
5. 검증되면 4단계(`guidelineCdInfo` 추가)로 넘어간다.

---

### 7.4 [4단계] `guidelineCdInfo` Tool 추가

**목표**: 3단계에서 확보한 4개 키(`resultIfKey`→`aresultNo`, `guidelineIfKey`, `itemCode`, `agentServerNm`)로 각 미조치 항목의 조치방법(`measure`) 원문을 조회한다. 이 단계까지 완료하면 Agent #1의 4단계 API 체이닝(2절 기준)이 전부 갖춰진다.

**추가로 배치할 노드 (Tool 1개)**

| 노드 | 라벨 |
|---|---|
| API Request Tool | `API Request Tool: guidelineCdInfo` |

**추가 연결 (1개)**

| 순서 | From | To | 비고 |
|---|---|---|---|
| 8 | API Request Tool(`guidelineCdInfo`) → `Tool` | Agent #1 → `Tools` | 빨간, 1~3단계까지의 연결과 같은 Tools 포트에 추가 |

1~3단계의 연결(Chat Input→Agent #1, Agent #1→Chat Output)은 그대로 유지한다.

**API Request Tool 배치 — `guidelineCdInfo`**

2-5절(322~369행) 기준. 이 Tool은 **GET + Query Params** 방식으로, 앞의 두 POST Tool(`mngtListDetail`/`scanResultCodeMngtDetail`)과 파라미터 위치가 다르다는 점에 주의한다.

| 항목 | 값 |
|---|---|
| 노드 라벨 | `API Request Tool: guidelineCdInfo` |
| Tool Mode | ON |
| URL | `https://ivms.lguplus.co.kr/ivms/api/guidelineCdInfo` |
| Method | GET |
| Connect Timeout / Read Timeout | 3000ms / 10000ms (GET 계열이므로 1절 공통 설정 기준 기본값 사용 — POST+Body 계열처럼 30000ms로 늘릴 필요 없음) |
| Query Params | `aresultNo`(integer, Y), `guidelineIfKey`(integer, Y), `guidelineCd`(string, Y), `itemCode`(string, Y), `agentServerNm`(string, Y) — 2-5절 표 그대로 |
| Header | 공통 인증 헤더 4종(GET이므로 `Content-Type` 불필요) |
| 툴 설명 | `취약점 항목의 상세 조치가이드(진단기준/현황/조치방법)를 조회하는 도구. aresultNo, guidelineIfKey, itemCode, agentServerNm 4개 값이 모두 있어야 정확한 항목이 조회된다. 이 4개 값은 scanResultCodeMngtDetail 응답에서 얻는다(aresultNo는 resultIfKey 값을 사용). 주의: 응답이 요청한 guidelineCd와 무관하게 다른 항목을 반환하는 경우가 있으므로, 응답의 guidelineCd가 원래 요청한 항목과 일치하는지 반드시 재확인해야 한다.` |

> ⚠️ **2-5절 369행의 중대 이슈 재확인**: 요청 시 `guidelineCd`를 지정해도 응답이 그 코드로 필터링되지 않고 `aresultNo`+`guidelineIfKey`+`itemCode`+`agentServerNm` 조합으로 응답이 결정되는 것으로 실제 curl 테스트에서 확정됐다. 아래 System Prompt에 응답 불일치 방어 지시를 반드시 포함해야 한다.

**Agent #1 System Prompt (4단계 전용 — 1~3단계 위에 이어붙임, 2절 최종본과 동일)**

1~3단계 프롬프트(7.1~7.3절)는 그대로 두고, 그 아래에 조치가이드 조회 지시를 추가한다.

```
3단계에서 확보한 각 미조치 항목(guidelineIfKey, itemCode, agentServerNm 조합)마다 guidelineCdInfo를 호출한다.

- aresultNo 파라미터에는 3단계 응답의 resultIfKey 값을 사용한다.
- guidelineCd 파라미터에는 3단계 응답의 guidelineCd 값을 그대로 전달한다.
- ⚠️ 매우 중요: 이 API는 요청한 guidelineCd와 무관하게 다른 항목의 데이터를 반환하는 경우가 실제로 확인되었다. 응답을 받으면 반드시 응답 본문의 guidelineCdInfo.guidelineCd 값이 방금 요청에 사용한 guidelineCd(=3단계에서 확보한 값)와 일치하는지 확인한다. 일치하지 않으면 그 응답은 신뢰할 수 없는 것으로 간주하고, 해당 항목은 "조치가이드 조회 실패(응답 불일치)"로 표시해 다음 단계로 넘긴다. 이 불일치 항목을 임의로 다른 값으로 대체하거나 추측해서 채우지 않는다.
- 동일한 (aresultNo, guidelineIfKey, itemCode, agentServerNm) 조합에 대해 이미 조회한 적이 있다면 다시 호출하지 않고 캐시된 결과를 재사용한다(같은 자산 내 동일 항목 중복 방지).

모든 단계 완료 후, 담당자별로 아래 구조의 원시 데이터를 정리해 응답에 포함한다. 가공하거나 요약하지 말고 수집한 원문 그대로 전달한다.

담당자: {chrgNm}({chrgId})
  자산: {asstCode} ({hostNm}, {ipAddrStr})
    - 항목: {guidelineCd} {guidelineNm} (severity: {severity})
      최근진단일: {timeEndYmd}
      조치기준(criteria): {criteria 원문}
      현황(analysisInfo): {analysisInfo 원문}
      조치방법(measure): {measure 원문}

위 구조를 담당자 수만큼, 각 담당자의 미조치 항목 수만큼 반복해 모두 나열한다. 데이터를 임의로 축약하거나 누락하지 않는다.
```

- `Jailbreak Check`: OFF
- `Model`: `azure_openai:gpt-4.1`(2-6절과 동일 — Tool 호출 스텝이 4종 API + 자산/항목 수만큼 반복되므로 유지)

**Chat Output**
- 연결 변경 없음(1~3단계와 동일하게 Agent #1 `Response`를 그대로 수신). 이 시점에서 Agent #1의 Tools 구성(4개)과 System Prompt(4단계 전체)는 2-6절의 최종본과 동일해진다.

**4단계 검증 방법**

1. Chat Input에 `"서비스인프라팀 미조치 현황 및 조치가이드 확인해줘"` 입력 후 전체 플로우 실행
2. 기대 응답: 담당자별 자산·취약 항목마다 `criteria`(진단기준)/`analysisInfo`(현황)/`measure`(조치방법) 원문이 포함된 응답이 나타나는지 확인
3. 정상 동작하지 않으면 다음을 순서대로 점검:
   - `guidelineCdInfo` Query Params에 5개 필드(`aresultNo`, `guidelineIfKey`, `guidelineCd`, `itemCode`, `agentServerNm`)가 모두 등록되어 있는지(POST Tool과 달리 이 Tool은 Query Params를 비우면 안 됨 — GET 방식이므로 파라미터가 여기 들어가야 함)
   - `aresultNo`에 `resultIfKey` 값이 들어가는지(필드명이 다르다는 점에서 혼동하기 쉬움 — Agent가 잘못된 필드를 매핑하지 않는지 System Prompt 재확인)
   - 응답의 `guidelineCdInfo.guidelineCd`가 요청한 값과 다르게 나오는 경우, System Prompt의 방어 로직(불일치 시 "조회 실패"로 표시)이 실제로 동작하는지(Agent가 불일치를 무시하고 잘못된 데이터를 그대로 쓰지 않는지)
   - 항목 수가 많아 응답이 느려지면 Read Timeout(GET 계열 10000ms)이 부족한지 확인 — 부족하면 `mngtListDetail`과 동일하게 상향 조정 검토
4. 검증되면 5단계(Agent #2, Human Approval, Language Model을 끼워 넣어 최종 구조 완성)로 넘어간다.

---

### 7.5 [5단계] Agent #2 · Human Approval · Language Model 삽입 — 최종 구조 완성

**목표**: 1~4단계에서 검증한 Agent #1(IVMS 데이터 수집)의 출력을 Chat Output에 직결하던 임시 연결을 끊고, 그 사이에 Agent #2(압박메시지+조치가이드 생성) → Human Approval → Language Model(패스스루)을 끼워 넣어 2절의 최종 구조(4절 구조도)를 완성한다.

**끊어야 할 연결 (1개)**

| 대상 | 비고 |
|---|---|
| Agent #1 `Response` → Chat Output `Input` | 1단계(7.1절)부터 4단계까지 유지해온 임시 연결. 이 연결선을 삭제한다 |

**추가로 배치할 노드 (3개)**

| 노드 | 라벨 |
|---|---|
| Agent | `Agent #2: 담당자별 압박메시지+조치가이드 생성` |
| Human Approval | 기본값 |
| Language Model | 기본값 |

**추가 연결 (4개, 기존 연결표 3.절 6~9번과 동일)**

| 순서 | From | To | 비고 |
|---|---|---|---|
| 6 | Agent #1 → `Response` | Agent #2 → `Input` | 파란 점선 — 방금 끊은 임시 연결 대신 이 연결로 대체 |
| 7 | Agent #2 → `Response` | Human Approval → `Target Message` | 파란, 필수 포트 |
| 8 | Human Approval → `Human Approval` | Language Model → `Input` | Chat Output 직결 불가 → 경유 필수(2-9절 543행 근거) |
| 9 | Language Model → `Response` | Chat Output → `Input` | **Chat Output 쪽에서 드래그 시작**(04번 문서 151행 제약 — 2-10절과 동일 주의) |

**Agent #2 구성**

2-7절(457~508행)의 값을 그대로 사용한다.

| 항목 | 값 |
|---|---|
| 노드 라벨 | `Agent #2: 담당자별 압박메시지+조치가이드 생성` |
| Input | Agent #1 `Response` 연결(위 표 6행) |
| Tools | 연결 없음 |
| Jailbreak Check | OFF |
| Model | `azure_openai:gpt-4.1-mini` |
| System Prompt | 2-7절 원문 그대로(미조치 판단 및 선별 기준, 담당자별 섹션 출력 구조, 전체 마무리 문구 — 469~508행 전문 참고) |

**Human Approval 구성**

2-8절(512~520행)의 값을 그대로 사용한다.

| 항목 | 값 |
|---|---|
| Target Message | Agent #2 `Response` 연결(위 표 7행) |
| question | `"위 {담당자 수}명분 압박메시지 및 조치가이드를 이 내용 그대로 승인하시겠습니까?"`(고정 문자열 직접 입력 — 노드 연결 아님) |
| Model | `azure_openai:gpt-4.1-mini` |

> 09번 문서 2절 요구사항에 따라 담당자별 개별 승인이 아닌 전체 통합 승인 1회로 구성한다(2-8절 520행과 동일).

**Language Model 구성 (패스스루)**

2-9절(524~543행)의 값을 그대로 사용한다.

| 항목 | 값 |
|---|---|
| Input | Human Approval `Human Approval` 포트 연결(위 표 8행) |
| Model | `azure_openai:gpt-4.1-mini` |
| System Prompt | 2-9절 원문 그대로("승인된 경우"/"거절된 경우" 분기 패스스루 지시 — 533~541행 전문 참고) |

> ⚠️ 이 노드는 `04-ixi-enterprise-node-catalog.md` 674/679행 제약(Human Approval 출력 → Chat Output 직접 연결 불가)을 우회하기 위한 필수 경유 노드다(2-9절 543행과 동일 근거).

**Chat Output 최종 연결**

- **Input**: Language Model `Response` 연결(위 표 9행)
- ⚠️ **연결 방향 주의**: Language Model의 `Response` 포트에서 드래그하면 Chat Output이 목록에 나타나지 않는다(04번 문서 151행). 반드시 **Chat Output 노드의 `Input` 포트 쪽에서 드래그를 시작**해 Language Model을 선택할 것(2-10절과 동일 주의).

**5단계 검증 방법**

1. Chat Input에 `"서비스인프라팀 미조치 현황 압박 및 조치가이드 생성해줘"` 입력 후 전체 플로우 실행
2. 기대 응답 순서: Agent #1이 원시 데이터 수집 → Agent #2가 담당자별 압박 메시지+조치가이드 요약 생성 → Human Approval이 승인 질문("위 N명분 ... 승인하시겠습니까?")을 띄움
3. 승인(Yes) 응답 시: Language Model이 "[승인 완료]"를 앞에 붙여 Agent #2의 출력 전체를 그대로 Chat Output에 전달하는지 확인
4. 거절(No) 응답 시: Language Model이 "[거절됨] 요청하신 내용은 승인되지 않아 발송되지 않습니다."만 출력하고 원본 내용을 다시 출력하지 않는지 확인
5. 정상 동작하지 않으면 다음을 순서대로 점검:
   - Agent #1 `Response` → Chat Output `Input` 임시 연결이 실제로 삭제되었는지(삭제하지 않으면 Agent #1 원시 데이터와 최종 응답이 중복 출력되거나 플로우가 꼬일 수 있음)
   - Human Approval → Language Model → Chat Output 경유 구조가 정확한지(Human Approval을 Chat Output에 직결 시도하면 노드가 목록에 나타나지 않음 — 04번 문서 674/679행 제약)
   - Chat Output은 반드시 Chat Output 쪽에서 드래그해 Language Model과 연결했는지(반대 방향으로 시도하면 실패)
   - Agent #2가 "조치가이드 조회 실패(응답 불일치)" 항목을 임의로 다른 값으로 채우지 않고 그대로 "수동 확인 필요"로 표기하는지(2-7절 479~481행 지시 준수 여부)
6. 검증되면 플로우 A 전체 구성이 완료된 것이며, 6절의 "구성 후 확인 체크리스트"로 최종 점검한다.

---
