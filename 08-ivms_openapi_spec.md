# IVMS OpenAPI 규격서

> 인프라 취약점 통합 관리 시스템(IVMS, Infra Vulnerability Management System)의 Open API 규격 정리 문서.
> 원본 출처: `ivms/` 폴더 내 API 등록 신청서(엑셀) 캡처 이미지 (2026-07-07 캡처)
> 각 오퍼레이션 제목의 `IF-API-XXXXXX`는 `ivms/*/api_test/` 폴더의 실제 curl 테스트 캡처에 표기된 API 식별자이며, 해당 캡처의 curl 명령/응답으로 실제 검증한 내용을 예시로 반영함.

## 문서 정보

| 항목 | 내용 |
|---|---|
| 서비스명 | 보안_IVMS |
| 시스템명(시스템코드) | 인프라 취약점 통합 관리 시스템 (IVMS) |
| 개발자 | 윤지원 |
| 소속팀 | 정보보안점검팀 |
| 개발자 이메일 | jwyoon21@lguplusparthers.co.kr |
| API 요청구분 | 등록 |
| 서비스 구분 | 대내 (전체 오퍼레이션) |

## 공통 규격

### 공통 응답 코드

| 코드 | 설명 |
|---|---|
| 200 | OK (일반적인 요청 성공) |
| 400 | Bad Request (잘못된 요청) |
| 404 | Not Found (요청한 URI에 해당하는 리소스가 존재하지 않음) |
| 405 | Method Not Allowed (지원하지 않는 http 메소드를 사용함) |
| 500 | Internal Server Error (서버 내부에서 예기치 못한 오류 발생) |

> 404, 405는 API 기본 정보(표지) 상의 공통 응답 코드 표에 정의되어 있으나, 개별 오퍼레이션 상세에는 200/400/500만 표기됨.

### 공통 응답 래퍼(Wrapper)

모든 오퍼레이션의 출력 데이터는 아래 공통 구조를 따른다.

```json
{
  "result": {
    // 오퍼레이션별 실제 응답 데이터
  },
  "_server_message_": {
    "text": "결과 내용",
    "type": "200"
  }
}
```

| 필드 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|
| result | 결과 정보 | object | Y | 오퍼레이션별 실제 응답 데이터 |
| _server_message_ | 결과 정보 | object | Y | 서버 처리 결과 메시지 |
| _server_message_.text | 결과 내용 | string | N | 결과 내용 |
| _server_message_.type | 결과 코드 | string | Y | 성공 시 "200" 등 |

### BIZ Exception (비즈니스 에러) 규격

비즈니스 에러는 Provider(API 제공자)의 business logic 처리 중 발생하는 에러 case를 의미하며, 클라이언트 애플리케이션에게 전달하기 위한 에러로 HTTP 상태코드 기반 시스템 에러와는 구분되는 에러다.

- 비즈니스 에러코드는 API Provider에서 정의하며, Response Body에 비즈니스 에러정보를 담아 리턴한다.
- BIZErrorCode에는 HTTP 상태코드가 아닌 어떤 비즈니스 에러인지 구분할 수 있는 값을 정의해야 한다.

**필수 사항**
1. HTTP Status(Header) 값은 `200` 또는 `201`로 고정한다.
2. BIZError(Header) 값은 `Y`로 고정한다.
3. 리턴 메시지에는 어떤 비즈니스 에러인지 명시할 수 있도록 한다.

**성공 메시지 예시**
```json
{
  "msgCd": "00",
  "msg": "처리에 성공하였습니다."
}
```
```json
{
  "result": {
    "$(성공했을 때 응답데이터 정의)"
  },
  "serverMsg": {
    "code": "S",
    "message": "성공입니다."
  }
}
```

**비즈 에러 메시지 예시**
```json
{
  "msgCd": "23",
  "msg": "존재하지 않는 데이터입니다."
}
```
```json
{
  "error Server": "$(API 제공하는 서버)",
  "error Code": "23",
  "error Message": "존재하지 않는 데이터입니다."
}
```
> 위 `error Server/Code/Message` 형태는 서버 default 리턴 메시지(Framework에서 리턴해주는 경우) 예시임.

**비즈니스 에러 출력 데이터 정의**

| 파라미터 위치 | 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|---|
| Body | result | ifRslt | 연동결과 | object | Y | |
| | | prssRsltCd | 처리결과코드 | string | N | N: 실패 (처리결과코드 값이 "N"인 경우, 오류 메시지) |
| | | prssRsltMsg | 처리결과메시지 | string | N | |
| | _server_message_ | text | 서버 결과 내용 | string | Y | |
| | | type | 서버 결과 코드 | string | Y | 200 등 성공 |
| | msgCd | 결과코드 | string | | 결재가 유효하지 않습니다 / 결재단계가 완료된 상태입니다 |
| | msg | 결과메시지 | string | N | prssRsltMsg 값과 동일 |

---

## 1. cmmCode (시스템보안_공통코드관리)

### 1.0 API 기본 정보

| 항목 | 내용 |
|---|---|
| API 제목 | 시스템보안_시스템보안_공통코드관리 |
| API 이름(영문) | cmmCode |
| API 설명 | 인프라 취약점 통합 관리 시스템에서 관리하는 공통 데이터 조회 정보 제공 API |

### 1.1 서브 리소스 목록

| 번호 | HTTP 메소드 | 서브 리소스(한글명) | API Endpoint URI | 서비스 구분 |
|---|---|---|---|---|
| 1 | GET | 진단 템플릿 조회 | /ivms/api/assetSsrcceTemplate | 대내 |
| 2 | GET | 자산 분류 조회 | /ivms/api/assetCategory | 대내 |
| 3 | GET | 자산 그룹 조회 | /ivms/api/assetGroup | 대내 |
| 4 | GET | 코드 목록 조회 | /ivms/api/codeList | 대내 |
| 5 | GET | 조직 조회 | /ivms/api/orgList | 대내 |

### 1.2 진단 템플릿 조회 — `GET /ivms/api/assetSsrcceTemplate` (IF-API-098001)

**입력 데이터 (Query)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 | 설명 |
|---|---|---|---|---|---|---|
| Query | userId | 사용자 ID | string | Y | admin | |

```json
{ "userId": "admin" }
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 진단템플릿 결과 정보 | object | Y | |
| result.templateList | templateList | 진단템플릿 목록 | Array[object] | Y | |
| templateList[].atemplateNo | atemplateNo | 진단템플릿 번호 | string | Y | |
| templateList[].templateName | templateName | 진단템플릿명 | string | Y | |

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

**응답시간(초) 샘플**: 0.01458

---

### 1.3 자산 분류 조회 — `GET /ivms/api/assetCategory` (IF-API-098002)

**입력 데이터 (Query)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 |
|---|---|---|---|---|---|
| Query | userId | 사용자 ID | string | Y | admin |
| Query | asstCtgrLevel | 자산분류 레벨(대/중/소) | string | Y | L |

```json
{ "userId": "admin", "asstCtgrLevel": "L" }
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 자산분류 결과정보 | object | Y | |
| result.asstCtgrList | asstCtgrList | 자산분류 목록 | Array[object] | Y | |
| asstCtgrList[].affltId | affltId | 계열사 ID | string | N | org_000001 |
| asstCtgrList[].asstCtgrId | asstCtgrId | 자산분류ID | string | N | AT_0004356 |
| asstCtgrList[].pAsstCtgrId | pAsstCtgrId | 상위자산분류ID | string | N | 자산분류ID의 최상위 1인 경우 NULL |
| asstCtgrList[].asstCtgrNm | asstCtgrNm | 자산분류명 | string | Y | NETWORK |
| asstCtgrList[].asstCtgrDesc | asstCtgrDesc | 자산분류설명 | string | N | |
| asstCtgrList[].asstCtgrLevel | asstCtgrLevel | 자산분류레벨 | string | Y | 자산분류레벨 종류: L, M, S |
| asstCtgrList[].ifKey | ifKey | 인터페이스 키 | string | N | |
| asstCtgrList[].ordNo | ordNo | 순서 | integer | Y | 1 |
| asstCtgrList[].useYn | useYn | 사용여부 | string | Y | Y(기본) 사용, N: 미사용 |
| asstCtgrList[].delYn | delYn | 삭제여부 | string | N | Y(기본) 미삭제, Y: 삭제 |
| asstCtgrList[].insertDt | insertDt | 등록일 | string | Y | 2024-11-08 08:20:39 |
| asstCtgrList[].updateDt | updateDt | 수정일 | string | N | 2024-11-12 14:19:37 |
| asstCtgrList[].deleteDt | deleteDt | 삭제일 | string | N | |
| asstCtgrList[].insertUser | insertUser | 등록자 | string | Y | BATCH_SSRCCE |
| asstCtgrList[].updateUser | updateUser | 수정자 | string | N | BATCH_SSRCCE |
| asstCtgrList[].deleteUser | deleteUser | 삭제자 | string | N | |
| asstCtgrList[].asstType | asstType | 자산타입 | string | N | SSRCCE |
| asstCtgrList[].userUseYn | userUseYn | 사용자 사용여부 | string | N | Y(기본): 미사용 Y: 사용 |

```json
{
  "result": {
    "asstCtgrList": [
      {
        "affltId": "org_000001",
        "asstCtgrId": "AT_0004356",
        "pAsstCtgrId": "",
        "asstCtgrNm": "HYPERVISOR",
        "asstCtgrDesc": "",
        "asstCtgrLevel": "L",
        "ifKey": "HYPERVISOR",
        "ordNo": "",
        "useYn": "Y",
        "delYn": "N",
        "insertDt": "2024-11-08 08:20:39",
        "updateDt": "2024-11-12 14:19:37",
        "deleteDt": "",
        "insertUser": "BATCH_SSRCCE",
        "updateUser": "BATCH_SSRCCE",
        "deleteUser": "",
        "asstType": "SSRCCE",
        "userUseYn": "Y"
      }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> **실제 curl 테스트로 확인**: 응답 필드 순서 및 필드명(`useUserYn` → `userUseYn`)을 실제 캡처 기준으로 정정함. `ordNo`는 실제 응답에서 빈 문자열로 반환됨(문서 예시상 정수 `1`이었으나 이 레코드는 빈 값).

**응답시간(초) 샘플**: 0.020

---

### 1.4 자산 그룹 조회 — `GET /ivms/api/assetGroup` (IF-API-098003)

**입력 데이터 (Query)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 |
|---|---|---|---|---|---|
| Query | userId | 사용자 ID | string | Y | admin |
| Query | asstGroupLevel | 자산그룹 레벨(대/중/소) | string | Y | L |

```json
{ "userId": "admin", "asstGroupLevel": "L" }
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 자산그룹 결과정보 | object | Y | |
| result.asstGroupList | asstGroupList | 자산그룹 목록 | Array[object] | Y | |
| asstGroupList[].ifKey | ifKey | 인터페이스 키 | string | N | 29 |
| asstGroupList[].affltId | affltId | 계열사코드 | string | N | org_000001 |
| asstGroupList[].asstGroupId | asstGroupId | 자산그룹ID | string | N | GR_0001500 |
| asstGroupList[].pAsstGroupId | pAsstGroupId | 상위자산그룹ID | string | N | GR_0001470 |
| asstGroupList[].asstGroupNm | asstGroupNm | 자산그룹명 | string | Y | 기술연구소 |
| asstGroupList[].pAsstGroupNm | pAsstGroupNm | 상위자산그룹명 | string | N | |
| asstGroupList[].asstGroupDesc | asstGroupDesc | 자산그룹설명 | string | N | 서비스컨트롤팀, 자산그룹별 부서와 사용자 연락처 등 |
| asstGroupList[].ordNo | ordNo | 순서 | integer | Y | 1 |
| asstGroupList[].useYn | useYn | 사용여부 | string | Y | Y(기본): 사용 N: 미사용 |
| asstGroupList[].delYn | delYn | 삭제여부 | string | N | N(기본): 미삭제 Y: 삭제 |
| asstGroupList[].insertDt | insertDt | 등록일 | string | Y | 2024-11-08 08:20:39 |
| asstGroupList[].updateDt | updateDt | 수정일 | string | N | 2024-11-12 14:19:37 |
| asstGroupList[].deleteDt | deleteDt | 삭제일 | string | N | 2024-11-15 14:19:37 |
| asstGroupList[].insertUser | insertUser | 등록자 | string | Y | BATCH_SSRCCE |
| asstGroupList[].updateUser | updateUser | 수정자 | string | N | BATCH_SSRCCE |
| asstGroupList[].deleteUser | deleteUser | 삭제자 | string | N | |
| asstGroupList[].asstGroupLevel | asstGroupLevel | 자산그룹레벨 | string | Y | 자산그룹레벨 종류: L, M, S |
| asstGroupList[].asstLGroupNm | asstLGroupNm | 자산그룹(대) | string | N | HR_System |
| asstGroupList[].asstMGroupNm | asstMGroupNm | 자산그룹(중) | string | N | JSP456 |
| asstGroupList[].asstSGroupNm | asstSGroupNm | 자산그룹(소) | string | N | JSP789 |
| asstGroupList[].authConcatList | authConcatList | 자산그룹별 권한부여 사용자/부서명 목록 | string | N | 서비스인프라팀, S팀 |
| asstGroupList[].agentServerNm | agentServerNm | 에이전트 서버명 | string | N | CCE1 |
| asstGroupList[].groupType | groupType | 그룹타입 | integer | N | 3자산그룹유형: 3 |
| asstGroupList[].hideYn | hideYn | 숨김여부 | string | N | N(기본): 미사용 Y: 사용 |

```json
{
  "result": {
    "asstGroupList": [
      {
        "ifKey": "241",
        "affltId": "org_000001",
        "asstGroupId": "GR_0001494",
        "pAsstGroupId": "GR_0001493",
        "asstGroupNm": "3",
        "pAsstGroupNm": "2",
        "asstGroupDesc": "",
        "ordNo": "0",
        "useYn": "Y",
        "delYn": "N",
        "insertDt": "2025-03-17 16:04:01",
        "updateDt": "2025-06-30 12:12:08",
        "deleteDt": "",
        "insertUser": "BATCH_SSRCCE",
        "updateUser": "BATCH_SSRCCE",
        "deleteUser": "",
        "asstGroupLevel": "S",
        "asstLGroupNm": "QA",
        "asstMGroupNm": "2",
        "asstSGroupNm": "",
        "authConcatList": "",
        "agentServerNm": "CCE1",
        "groupType": "3",
        "hideYn": "N"
      }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> **실제 curl 테스트로 확인**: 기존 문서 예시의 `insertDt`/`updateDt` 콜론 누락은 캡처 오타였음(정정 완료). `pAsstGroupNm`(상위자산그룹명), `authConcatList`(자산그룹별 권한부여 사용자/부서명 목록) 필드는 실제 응답에 존재하나 기존 문서에는 누락되어 있어 추가함. 응답 필드 순서도 실제 캡처 기준으로 정정함.

**응답시간(초) 샘플**: 0.02262

---

### 1.5 코드 목록 조회 — `GET /ivms/api/codeList` (IF-API-098004)

**입력 데이터 (Query)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| Query | cdTypeEngNm | 코드 구분 영문명 | string | Y | 예시값: ASST_USAGE_CD (자산용도), VADA_DGNOS_RESULT_CD (점검결과), REMOTE_RUN_TYPE_CD (자산정보 원격연결 사용유무), CONN_SERVICE_TYPE_CD (자산정보 원격연결할 서비스), LOGIN_TYPE_CD (자산정보 원격연결 로그인방식) |

```json
{ "cdTypeEngNm": "ASST_USAGE_CD" }
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 코드목록 결과 정보 | object | Y | |
| result.codeList | codeList | 코드 목록 | Array[object] | Y | |
| codeList[].cd | cd | 코드 | string | Y | INTG |
| codeList[].cdNm | cdNm | 코드명 | string | Y | 통시 |

```json
{
  "result": {
    "codeList": [
      { "cd": "DR", "cdNm": "DR" },
      { "cd": "DEV", "cdNm": "DEV" },
      { "cd": "REVIEW", "cdNm": "REVIEW" },
      { "cd": "EDU", "cdNm": "EDU" },
      { "cd": "OPER", "cdNm": "OPER" },
      { "cd": "INTG", "cdNm": "통시" }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> 실제 curl 테스트(`cmmCode_공통코드관리/api_test/`) 응답에서 cd값 6종(DR, DEV, REVIEW, EDU, OPER, INTG)을 확인함.

**응답시간(초) 샘플**: 0.0093

---

### 1.6 조직 조회 — `GET /ivms/api/orgList` (IF-API-098005)

**입력 데이터 (Query)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 | 설명 |
|---|---|---|---|---|---|---|
| Query | orgType | 조직 타입 | string | Y | 1 | 부문: "1" 그룹: "2" 담당: "3" 팀: "4" |
| Query | pOrgId | 상위 부서 ID | string | Y | org_000001 | |

```json
{ "orgType": "1", "pOrgId": "org_000001" }
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 |
|---|---|---|---|---|---|
| result | result | 조직목록 결과 정보 | object | Y | |
| result.orgList | orgList | 조직 목록 | Array[object] | Y | |
| orgList[].orgId | orgId | 조직ID | string | Y | org_000008 |
| orgList[].orgNm | orgNm | 조직명 | string | Y | 서비스인프라팀 |
| orgList[].useYn | useYn | 사용여부 | string | Y | Y |
| orgList[].pOrgId | pOrgId | 상위조직ID | string | Y | org_000001 |
| orgList[].pAffltId | pAffltId | 계열사코드 | string | Y | org_000001 |

```json
{
  "result": {
    "orgList": [
      {
        "orgId": "org_000001",
        "orgNm": "직속",
        "useYn": "Y",
        "pOrgId": "",
        "pAffltId": "org_000001"
      },
      {
        "orgId": "org_001953",
        "orgNm": "CSEO",
        "useYn": "Y",
        "pOrgId": "org_000001",
        "pAffltId": "org_000001"
      },
      {
        "orgId": "org_001199",
        "orgNm": "CHO",
        "useYn": "Y",
        "pOrgId": "org_000001",
        "pAffltId": "org_000001"
      },
      {
        "orgId": "org_000008",
        "orgNm": "서비스인프라팀",
        "useYn": "Y",
        "pOrgId": "org_000001",
        "pAffltId": "org_000001"
      }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> 실제 curl 테스트(`cmmCode_공통코드관리/api_test/`) 응답에서 최상위(`pOrgId=org_000001`) 산하 조직 다수(CSEO, CHO, 서비스인프라팀 등)를 확인함.

**응답시간(초) 샘플**: 0.014

---

## 2. assetInfo (시스템보안_자산정보)

### 2.0 API 기본 정보

| 항목 | 내용 |
|---|---|
| API 제목 | 시스템보안_시스템보안_자산정보 |
| API 이름(영문) | assetInfo |
| API 설명 | 인프라 취약점 통합 관리 시스템에서 관리하는 자산 조회 정보 제공 API |

### 2.1 서브 리소스 목록

| 번호 | HTTP 메소드 | 서브 리소스(한글명) | API Endpoint URI |
|---|---|---|---|
| 1 | POST | 관리 리스트 상세현황 | /ivms/api/mngtListDetail |
| 2 | GET | 정보 조회 | /ivms/api/asstInfo |
| 3 | GET | 담당자 정보조회 | /ivms/api/asstChrgInfo |
| 4 | GET | 진단옵션 정보조회 | /ivms/api/asstSsrcOption |

### 2.2 관리 리스트 상세현황 — `POST /ivms/api/mngtListDetail` (IF-API-099401)

**입력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 | 설명 |
|---|---|---|---|---|---|---|
| Body(1) | userId | 사용자ID | string | N | admin | |
| | asstType | 자산타입 | string | N | SSRCCE | |
| | asstCode | 자산코드 | Array[string] | N | ["SSRCCE1-000747","SSRCCE1-000741"] | |
| | asstGroup | 자산그룹 | string | N | | |
| | templateNo | 진단템플릿 | string | N | 2 | |
| | diagYear | 기준연도 | string | N | 2025 | |
| | mgmtOrgId | 부서ID | string | N | | |
| | rspnMngId | 담당자ID | string | N | | |
| | asstLCtgrId | 자산분류(대) | string | N | AT_0004286 | *대시보드에서 이동시 다름값 설정 |
| | asstMCtgrId | 자산분류(중) | string | N | | |
| | asstSCtgrId | 자산분류(소) | string | N | | |
| | asstLGroupId | 자산그룹(대) | string | N | GR_0001495 | |
| | asstMGroupId | 자산그룹(중) | string | N | | |
| | asstSGroupId | 자산그룹(소) | string | N | | |
| | ipAddrStr | IP주소 | string | N | | |
| | hostNm | 호스트명 | Array[string] | N | ["Solid-DB1","Solid-DB2"] | |
| | profileNm | 프로파일명 | string | N | | |
| | agentState | 에이전트 상태 | string | N | 1 | 정상연동: "1" 수동등록: "-1" 미응답: "0" |
| | asstUsage | 자산용도 | string | N | 검수 | DA, 개발, 검수, 교육, 운영, 통신 |
| | asstChgChangeReqSeq | 담당자변경 요청 순번(구분자) | string | N | Y전송 | 전체관리자산 항목 및 상세 조건은 아래 표 참고 |
| | filter/xorStr | 필터 문자열 | Array[object] | N | (아래 참고) | 전체관리자산, 취약, 정상연동, 종합/양호/취약, 수동등록, 종합/양호/취약, 점검미수행, 미응답 등 상세조건 필터 |
| 2 | filter/xorStr.logic | 로직 | string | N | "logic":"and" | and / or 화이트리스트 처리 필요 |
| 2 | filter/xorStr.filters | 필터 내용 | Array[object] | N | [{"field":"SECURITY_SCORE","operator":"eq","value":100}] | 화이트리스트 처리 필요 |
| 3 | filters.field | 필드명 | string | N | "SECURITY_SCORE" | eq / neq 화이트리스트 처리 필요 |
| 3 | filters.operator | 연산자 | string | N | "eq" | |
| 3 | filters.value | 대상값 | string | N | "100" | 화이트리스트 처리 필요 |
| 1 | page | 현재 페이지 | integer | N | 1 | |
| 1 | pageSize | 페이지당 항목 수 | integer | N | 50 | |

```json
{
  "userId": "jwyoon21",
  "asstType": "SSRCCE",
  "templateNo": "151",
  "diagYear": "2025",
  "asstLCtgrId": "AT_0005382"
}
```

**`filter/xorStr` 상세 조건 (전체관리자산 항목 및 상세조건)**

전체관리자산, 양호:
```
logic: and
filters:
  field: "SECURITY_SCORE"
  operator: "eq"
  value: 100
```

전체관리자산, 취약:
```
logic: and
filters:
  field: "SECURITY_SCORE"
  operator: "neq"
  value: 100
```

정상연동, 종합:
```
logic: and
filters:
  field: "AGENT_STATE"
  operator: "eq"
  value: "1"
```

정상연동, 양호:
```
logic: and
filters:
  field: "AGENT_STATE"
  operator: "eq"
  value: "1"
logic: and
filters:
  field: "SECURITY_SCORE"
  operator: "eq"
  value: 100
```

정상연동, 취약:
```
logic: and
filters:
  field: "AGENT_STATE"
  operator: "eq"
  value: "1"
logic: and
filters:
  field: "SECURITY_SCORE"
  operator: "neq"
  value: 100
```

수동등록, 종합:
```
logic: and
filters:
  field: "AGENT_STATE"
  operator: "eq"
  value: "-1"
```

수동등록, 양호:
```
logic: and
filters:
  field: "AGENT_STATE"
  operator: "eq"
  value: "-1"
logic: and
filters:
  field: "SECURITY_SCORE"
  operator: "eq"
  value: 100
```

수동등록, 취약:
```
logic: and
filters:
  field: "AGENT_STATE"
  operator: "eq"
  value: "-1"
logic: and
filters:
  field: "SECURITY_SCORE"
  operator: "neq"
  value: 100
```

점검미수행, 종합:
```
logic: and
filters:
  field: "AGENT_STATE"
  operator: "neq"
  value: "0"
logic: and
filters:
  field: "SECURITY_SCORE"
  operator: "isnullorempty"
```

미응답, 종합:
```
logic: and
filters:
  field: "AGENT_STATE"
  operator: "eq"
  value: "0"
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 | 설명 |
|---|---|---|---|---|---|---|
| result | result | 자산관리리스트 결과 정보 | object | Y | | |
| result.assetList | assetList | 자산관리리스트 목록 | Array[object] | Y | | |
| assetList[].ifKey | ifKey | 인터페이스 키 | string | N | 157 | |
| assetList[].affltId | affltId | 계열사ID | string | N | org_000001 | |
| assetList[].asstId | asstId | 자산 ID | string | Y | ASST_000000000000240 | |
| assetList[].asstVer | asstVer | 자산 버전 | integer | Y | 2 | |
| assetList[].asstCode | asstCode | 자산 코드 | string | Y | SSRCCE1-000157 | |
| assetList[].asstNm | asstNm | 자산 명 | string | N | SolidStep-CVE | |
| assetList[].asstGroup | asstGroup | 자산 그룹 | string | N | | |
| assetList[].asstLCtgrId | asstLCtgrId | 자산 대분류 ID | string | N | AT_0004286 | |
| assetList[].asstMCtgrId | asstMCtgrId | 자산 중분류 ID | string | N | AT_0004287 | |
| assetList[].asstSCtgrId | asstSCtgrId | 자산 소분류 ID | string | N | AT_0004288 | |
| assetList[].asstLCtgrNm | asstLCtgrNm | 자산 대분류 명 | string | N | OS | |
| assetList[].asstMCtgrNm | asstMCtgrNm | 자산 중분류 명 | string | N | LINUX | |
| assetList[].asstSCtgrNm | asstSCtgrNm | 자산 소분류 명 | string | N | LINUX | |
| assetList[].asstLGroupIdStr | asstLGroupIdStr | 자산 대그룹 ID 문자열 | string | N | GR_0001486 | |
| assetList[].asstMGroupIdStr | asstMGroupIdStr | 자산 중그룹 ID 문자열 | string | N | GR_0001487 | |
| assetList[].asstSGroupIdStr | asstSGroupIdStr | 자산 소그룹 ID 문자열 | string | N | | |
| assetList[].asstLGroupNm | asstLGroupNm | 자산 대그룹 명 | string | N | VPN_Gateway | |
| assetList[].asstMGroupNm | asstMGroupNm | 자산 중그룹 명 | string | N | 기술연구소 | |
| assetList[].asstGroupNmPath | asstGroupNmPath | 자산 그룹 경로명 | string | N | 기술연구소 | |
| assetList[].asstGroupNmPathStr | asstGroupNmPathStr | 자산 그룹 경로 문자열 | string | N | VPN_Gateway > 기술연구소 | |
| assetList[].asstGroupIdStr | asstGroupIdStr | 자산 그룹 ID 문자열 | string | N | GR_0001487 | |
| assetList[].asstDetail | asstDetail | 자산 상세 명 | string | N | | |
| assetList[].asstUseYn | asstUseYn | 자산 사용 여부 | string | N | Y | |
| assetList[].asstUseYnNm | asstUseYnNm | 자산 사용 여부명 | string | N | 사용 | |
| assetList[].asstLocation | asstLocation | 자산 위치 | string | N | | |
| assetList[].abandonYn | abandonYn | 폐기 여부 | string | N | N | |
| assetList[].networkRealmCd | networkRealmCd | 네트워크 영역 코드 | string | N | | |
| assetList[].networkRealmNm | networkRealmNm | 네트워크 영역 명 | string | N | | |
| assetList[].asstUsage | asstUsage | 자산 용도 | string | N | | |
| assetList[].asstEtc | asstEtc | 기타 자산 정보 | string | N | | |
| assetList[].mgmtOrgId | mgmtOrgId | 관리 조직 ID | string | N | org_000009 | |
| assetList[].mgmtOrgNm | mgmtOrgNm | 관리 조직 명 | string | N | 개인정보보호팀 | |
| assetList[].asstConf | asstConf | 자산 기밀성 | string | N | 1 | |
| assetList[].asstIntg | asstIntg | 자산 무결성 | string | N | 1 | |
| assetList[].asstAvbl | asstAvbl | 자산 가용성 | string | N | 1 | |
| assetList[].asstCiaGrade | asstCiaGrade | 자산 CIA 등급 | integer | N | 3 | |
| assetList[].asstCiaGradeNm | asstCiaGradeNm | 자산 CIA 등급명 | string | N | 다 | |
| assetList[].osCd | osCd | 운영체제 코드 | string | N | Linux | |
| assetList[].osNm | osNm | 운영체제 명 | string | N | Linux | |
| assetList[].osVer | osVer | 운영체제 버전 | string | N | | |
| assetList[].hostNm | hostNm | 호스트명 | string | Y | SolidStep-CVE | |
| assetList[].protocol | protocol | 프로토콜 | string | N | AGENT | |
| assetList[].protocolNm | protocolNm | 프로토콜명 | string | N | O(AGENT) | |
| assetList[].delYn | delYn | 삭제 여부 | string | N | N | |
| assetList[].updateDt | updateDt | 수정 일자 | string | N | 2025-06-30 12:13:40 | |
| assetList[].insertDt | insertDt | 등록 일자 | string | N | 2025-06-25 15:21:22 | |
| assetList[].syncDt | syncDt | 동기화 일시 | string | N | 2025-06-30 11:14:15 | |
| assetList[].asstType | asstType | 자산 유형 | string | N | SSRCCE | |
| assetList[].agentState | agentState | 에이전트 상태 | string | N | 1 | 정상연동: "1" 수동등록: "-1" 미응답: "0" |
| assetList[].agentStateNm | agentStateNm | 에이전트 상태명 | string | N | 정상 | |
| assetList[].chrgId | chrgId | 담당자 ID | string | N | yjw | |
| assetList[].chrgNm | chrgNm | 담당자 명 | string | N | 유정원(yjw) | |
| assetList[].chrgOrgIdStr | chrgOrgIdStr | 담당자 조직 ID 문자열 | string | N | org_000009 | |
| assetList[].subChrgId | subChrgId | 부담당자 ID | string | N | | |
| assetList[].subChrgNm | subChrgNm | 부담당자 명 | string | N | | |
| assetList[].chrgNmId | chrgNmId | 담당자 명(ID 포함) | string | N | 유정원(yjw)(yjw) | |
| assetList[].subChrgNmId | subChrgNmId | 부담당자 명(ID 포함) | string | N | | |
| assetList[].ipAddrStr | ipAddrStr | IP 주소 문자열 | string | Y | 192.168.2.112 | |
| assetList[].installDirectory | installDirectory | 설치 경로 문자열 | string | N | | |
| assetList[].securityScore | securityScore | 보안 점수 | string | N | 90 | |
| assetList[].timeEndYmd | timeEndYmd | 최근 진단일 | string | N | 2025-06-30 11:14:15 | |
| assetList[].agentServerNm | agentServerNm | 에이전트 서버 명 | string | N | CCE1 | |
| assetList[].agentGroup | agentGroup | 에이전트 그룹 | string | N | 234 | |
| assetList[].serviceNm | serviceNm | 서비스 명 | string | N | | |
| assetList[].templateNo | templateNo | 템플릿 번호 | string | N | 2 | |
| assetList[].profileNm | profileNm | 프로파일명 | string | N | 진단0627-7 | |
| assetList[].regulationNm | regulationNm | 진단템플릿명 | string | N | SSR_기준항목 | |
| assetList[].delayYn | delayYn | 지연 여부 | string | N | N | |
| assetList[].assetChrgChangeReqSeq | assetChrgChangeReqSeq | 자산 담당자 변경 요청 순번 | integer | N | null | |
| assetList[].resultId | resultId | 진단결과 ID | string | N | | |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | | |
| _server_message_.text | text | 결과 내용 | string | N | | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 | 성공 등 |

> **실제 curl 테스트로 확인**: 출력 필드 전체를 실제 응답 캡처 기준으로 재정렬함. 기존 문서의 `asstDc`(기자재 정보)는 오기이며 실제 필드명은 `asstEtc`(기타 자산 정보). `resultId`(진단결과 ID) 필드는 실제 응답에 존재하나 이번 캡처 레코드에는 값이 나타나지 않음(다른 조건에서 값이 채워질 수 있음) — 다른 값 없음 필드와의 표기 일관성을 위해 JSON 예시에 `"resultId": ""`로 추가함. `asstMGroupIdStr`, `asstGroupNmPathStr`, `asstUseYnNm`, `chrgNmId`, `subChrgNmId` 필드는 기존 문서에 누락되어 있어 추가함. 기존 예시의 `chrgOrgIdStr: "국정청조직문자열"`은 실제 값이 아니라 필드 설명이 잘못 들어간 것으로 확인되어 실제 캡처값으로 교체함.

```json
{
  "result": {
    "assetList": [
      {
        "ifKey": "157",
        "affltId": "org_000001",
        "asstId": "ASST_000000000000240",
        "asstVer": 2,
        "asstCode": "SSRCCE1-000157",
        "asstNm": "SolidStep-CVE",
        "asstGroup": "",
        "asstLCtgrId": "AT_0004286",
        "asstMCtgrId": "AT_0004287",
        "asstSCtgrId": "AT_0004288",
        "asstLCtgrNm": "OS",
        "asstMCtgrNm": "LINUX",
        "asstSCtgrNm": "LINUX",
        "asstLGroupIdStr": "GR_0001486",
        "asstMGroupIdStr": "GR_0001487",
        "asstSGroupIdStr": "",
        "asstLGroupNm": "VPN_Gateway",
        "asstMGroupNm": "기술연구소",
        "asstGroupNmPath": "기술연구소",
        "asstGroupNmPathStr": "VPN_Gateway > 기술연구소",
        "asstGroupIdStr": "GR_0001487",
        "asstDetail": "",
        "asstUseYn": "Y",
        "asstUseYnNm": "사용",
        "asstLocation": "",
        "abandonYn": "N",
        "networkRealmCd": "",
        "networkRealmNm": "",
        "asstUsage": "",
        "asstEtc": "",
        "mgmtOrgId": "org_000009",
        "mgmtOrgNm": "개인정보보호팀",
        "asstConf": "1",
        "asstIntg": "1",
        "asstAvbl": "1",
        "asstCiaGrade": 3,
        "asstCiaGradeNm": "다",
        "osCd": "Linux",
        "osNm": "Linux",
        "osVer": "",
        "hostNm": "SolidStep-CVE",
        "protocol": "AGENT",
        "protocolNm": "O(AGENT)",
        "delYn": "N",
        "updateDt": "2025-06-30 12:13:40",
        "insertDt": "2025-06-25 15:21:22",
        "syncDt": "2025-06-30 11:14:15",
        "asstType": "SSRCCE",
        "agentState": "1",
        "agentStateNm": "정상",
        "chrgId": "yjw",
        "chrgNm": "유정원(yjw)",
        "chrgOrgIdStr": "org_000009",
        "subChrgId": "",
        "subChrgNm": "",
        "chrgNmId": "유정원(yjw)(yjw)",
        "subChrgNmId": "",
        "ipAddrStr": "192.168.2.112",
        "installDirectory": "",
        "securityScore": "90",
        "timeEndYmd": "2025-06-30 11:14:15",
        "agentServerNm": "CCE1",
        "agentGroup": "234",
        "serviceNm": "",
        "templateNo": "2",
        "profileNm": "진단0627-7",
        "regulationNm": "SSR_기준항목",
        "delayYn": "N",
        "assetChrgChangeReqSeq": null,
        "resultId": ""
      }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

---

### 2.3 정보 조회 — `GET /ivms/api/asstInfo` (IF-API-099402)

**입력 데이터 (Query)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 |
|---|---|---|---|---|---|
| Query | asstId | 자산ID | string | Y | ASST_000000000095080 |
| Query | asstVer | 자산VER | string | Y | 8 |
| Query | templateNo | 진단템플릿 | string | Y | 151 |

```json
{ "asstId": "ASST_000000000095080", "asstVer": 8, "templateNo": "151" }
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 |
|---|---|---|---|---|---|
| result | result | 자산 정보(기본) 결과 정보 | object | Y | |
| result.asstInfo | asstInfo | 자산 정보(기본) 목록 | object | Y | |
| asstInfo.asstId | asstId | 자산ID | string | Y | ASST_000000000000204 |
| asstInfo.asstVer | asstVer | 자산 버전 | integer | Y | 38 |
| asstInfo.asstType | asstType | 자산 유형 | string | N | SSRCCE |
| asstInfo.templateNo | templateNo | 진단 템플릿 | string | N | 2 |
| asstInfo.asstCode | asstCode | 자산 코드 | string | Y | SSRCCE1-000052 |
| asstInfo.asstNm | asstNm | 자산 명 | string | Y | SolidStep-CCE |
| asstInfo.hostNm | hostNm | 호스트 명 | string | N | |
| asstInfo.asstLCtgrNm | asstLCtgrNm | 자산 대분류 명 | string | N | WEB |
| asstInfo.asstMCtgrNm | asstMCtgrNm | 자산 중분류 명 | string | N | NGINX |
| asstInfo.asstSCtgrNm | asstSCtgrNm | 자산 소분류 명 | string | N | NGINX |
| asstInfo.mgmtOrgNm | mgmtOrgNm | 관리 조직명 | string | N | 서비스인프라팀 |
| asstInfo.assetGroupModelList | assetGroupModelList | 자산 그룹 모델 리스트 | Array[object] | N | |
| assetGroupModelList[].asstGroupNmPath | asstGroupNmPath | 자산 그룹명 경로 | string | N | HR_System > SCA |
| assetGroupModelList[].asstGroupIdPath | asstGroupIdPath | 자산 그룹ID 경로 | string | N | GR_0001489,GR_0001518 |
| asstInfo.asstGroupNmPath | asstGroupNmPath | 자산 그룹명 | string | N | SCA |
| asstInfo.agentState | agentState | 에이전트 상태 | string | Y | 1 |
| asstInfo.agentStateNm | agentStateNm | 에이전트 상태명 | string | Y | 정상 |
| asstInfo.asstDetail | asstDetail | 자산 상세 | string | N | Nginx 1.22.1 |
| asstInfo.asstLocation | asstLocation | 자산 위치 | string | N | |
| asstInfo.asstUsage | asstUsage | 자산 용도 | string | N | 운영 |
| asstInfo.asstUseYn | asstUseYn | 자산 사용 여부 | string | N | Y |
| asstInfo.asstUseYnNm | asstUseYnNm | 자산 사용 여부 명 | string | N | 사용 |
| asstInfo.abandonYn | abandonYn | 폐기 여부 | string | N | N |
| asstInfo.ipAddr | ipAddr | IP 주소 | Array[string] | N | ["192.168.2.78"] |
| asstInfo.osCd | osCd | 운영체제 코드 | string | N | Linux |
| asstInfo.osNm | osNm | 운영체제 명 | string | N | Linux |
| asstInfo.serviceNm | serviceNm | 서비스 명 | string | N | SolidStep-204-서비스 |
| asstInfo.agentServerNm | agentServerNm | 에이전트 서버 명 | string | Y | CCE1 |
| asstInfo.syncDt | syncDt | 동기화 일시 | string | Y | 2025-06-11 00:00:22 |
| asstInfo.timeEndYmd | timeEndYmd | 최근 진단 일시 | string | N | 2025-06-30 11:13:02 |
| asstInfo.securityScore | securityScore | 보안 점수 | string | N | 100 |
| asstInfo.asstEtc | asstEtc | 비고 | string | N | 비고 |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | |
| _server_message_.text | text | 결과 내용 | string | N | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 성공 등 |

> **실제 curl 테스트로 확인**: `asstInfo.asstGroupNmPath`(자산 그룹명, "SCA")는 `assetGroupModelList[].asstGroupNmPath`(자산 그룹명 경로, "HR_System > SCA")와 별개 필드로 확인됨(값이 다름). 기존 문서의 필드명 `asstIc`는 오기이며 실제 필드명은 `asstEtc`. `timeEndYmd`, `securityScore`, `asstEtc`, `asstInfo.asstGroupNmPath` 값이 기존 예시 JSON에 누락되어 있어 추가함. 최상위 객체명도 실제 응답값에 맞춰 `asstinfo` → `asstInfo`(대문자 I)로 통일함.

```json
{
  "result": {
    "asstInfo": {
      "asstId": "ASST_000000000000204",
      "asstVer": 38,
      "asstType": "SSRCCE",
      "templateNo": "2",
      "asstCode": "SSRCCE1-000052",
      "asstNm": "SolidStep-CCE",
      "hostNm": "SolidStep-CCE",
      "asstLCtgrNm": "WEB",
      "asstMCtgrNm": "NGINX",
      "asstSCtgrNm": "NGINX",
      "mgmtOrgNm": "서비스인프라팀",
      "assetGroupModelList": [
        { "asstGroupNmPath": "HR_System > SCA", "asstGroupIdPath": "GR_0001489,GR_0001518" }
      ],
      "asstGroupNmPath": "SCA",
      "agentState": "1",
      "agentStateNm": "정상",
      "asstDetail": "Nginx 1.22.1",
      "asstLocation": "",
      "asstUsage": "운영",
      "asstUseYn": "Y",
      "asstUseYnNm": "사용",
      "abandonYn": "N",
      "ipAddr": ["192.168.2.78"],
      "osCd": "Linux",
      "osNm": "Linux",
      "serviceNm": "SolidStep-204-서비스",
      "agentServerNm": "CCE1",
      "syncDt": "2025-06-11 00:00:22",
      "timeEndYmd": "2025-06-30 11:13:02",
      "securityScore": "100",
      "asstEtc": "비고"
    }
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

**응답시간(초) 샘플**: 0.036

---

### 2.4 담당자 정보조회 — `GET /ivms/api/asstChrgInfo` (IF-API-099403)

**입력 데이터 (Query)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 |
|---|---|---|---|---|---|
| Query | asstId | 자산ID | string | Y | ASST_000000000094531 |
| Query | asstVer | 자산VER | string | Y | 14 |

```json
{ "asstId": "ASST_000000000094531", "asstVer": 14 }
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 자산 정보(담당자) 결과 정보 | object | Y | |
| result.asstChrgList | asstChrgList | 자산 정보(담당자) 목록 | Array[object] | Y | |
| asstChrgList[].chrgId | chrgId | 담당자 ID | string | Y | |
| asstChrgList[].chrgNm | chrgNm | 담당자 명 | string | Y? | |
| asstChrgList[].chrgTypeCd | chrgTypeCd | 담당 유형 코드 | string | Y | CHGR |
| asstChrgList[].chrgTypeCdNm | chrgTypeCdNm | 담당 유형 명 | string | Y | 담당자 정/부 코드. 정(CHGR) 부(SCHGR) |
| asstChrgList[].orgId | orgId | 조직 ID | string | Y | |
| asstChrgList[].orgNm | orgNm | 조직 명 | string | Y | |
| asstChrgList[].orgIdPath | orgIdPath | 조직 ID 경로 | string | Y | org_000001 / org_001746 / org_001048 (상위 조직 ~ 해당 조직의 경로 표시, 계층 단계는 조직마다 다름) |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | |
| _server_message_.text | text | 결과 내용 | string | N | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 성공 등 |

```json
{
  "result": {
    "asstChrgList": [
      {
        "chrgTypeCd": "CHGR",
        "chrgTypeCdNm": "정",
        "chrgId": "macksh",
        "chrgNm": "김상현",
        "orgId": "org_000008",
        "orgNm": "서비스인프라팀",
        "orgIdPath": "org_000001 / org_000008"
      },
      {
        "chrgTypeCd": "SCHGR",
        "chrgTypeCdNm": "부",
        "chrgId": "yjw",
        "chrgNm": "유정원",
        "orgId": "org_000008",
        "orgNm": "서비스인프라팀",
        "orgIdPath": "org_000001 / org_000008"
      }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> **실제 curl 테스트로 확인**: `asstChrgList`는 정담당자(`chrgTypeCd: CHGR`)와 부담당자(`chrgTypeCd: SCHGR`)가 배열로 함께 반환됨을 확인. `orgIdPath`는 조직 계층 깊이에 따라 2단계(`org_000001 / org_000008`)부터 3단계 이상까지 가변적임.

**응답시간(초) 샘플**: 0.01

---

### 2.5 진단옵션 정보조회 — `GET /ivms/api/asstSsrcOption` (IF-API-099404)

**입력 데이터 (Query)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 |
|---|---|---|---|---|---|
| Query | ifKey | 자산 인터페이스키 | string | Y | 88 |
| Query | asstNo | 연동자산번호(SSRCCE) | string | Y | 65778 |
| Query | agentServerNm | 에이전트 서버명 | string | Y | CCE1 |

```json
{ "ifKey": "88", "asstNo": "65778", "agentServerNm": "CCE1" }
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 자산 정보(진단옵션) 결과 정보 | object | Y | |
| result.asstSsrcOption | asstSsrcOption | 자산 정보(진단옵션) 목록 | Array[object] | Y | |
| asstSsrcOption[].aoptNo | aoptNo | 고유 번호 | string | N | |
| asstSsrcOption[].description | description | 입력값 | string | N | 수집 예외 - bash 쉘 버전 관련 정보 |
| asstSsrcOption[].descriptionEn | descriptionEn | 입력값(영문) | string | N | Exceptions to collection - information related to bash shell version |
| asstSsrcOption[].optionName | optionName | 옵션 | string | N | |
| asstSsrcOption[].isEnable | isEnable | 사용 여부 | string | N | 0: 미사용 1: 사용, htmlDisplay는 대상아님 |
| asstSsrcOption[].isRequire | isRequire | 필수 여부 | string | N | |
| asstSsrcOption[].isPc | isPc | PC 여부 | string | N | |
| asstSsrcOption[].optionType | optionType | 옵션 타입 | string | N | 1/99: value가 입력값에 할당, 2: value가 입력값에 할당(password 형태), 그외: description이 입력값에 할당 |
| asstSsrcOption[].optionParams | optionParams | 옵션 파라미터 | string | N | |
| asstSsrcOption[].aoptLinkNo | aoptLinkNo | 연결 옵션 번호 | string | N | 해당 옵션의 html상 ID로 쓰임 |
| asstSsrcOption[].autoHelp | autoHelp | 도움말 | string | N | |
| asstSsrcOption[].isEnableOpt | isEnableOpt | 옵션 사용여부 | string | N | 0: 미사용 1: 사용, htmlDisplay는 대상아님 |
| asstSsrcOption[].value | value | 입력값 | string | N | optionType이 1,2,99인 경우 입력값으로 쓰임 |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | |
| _server_message_.text | text | 결과 내용 | string | N | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 성공 등 |

```json
{
  "result": {
    "asstSsrcOption": [
      {
        "aoptNo": "10000",
        "description": "수집 예외 - bash 쉘 버전 관련 정보",
        "descriptionEn": "Exceptions to collection - information related to bash shell version",
        "optionName": "options/skipBaseVersionInfo",
        "isEnable": "1",
        "isRequire": "0",
        "isPc": "0",
        "optionType": "0",
        "optionParams": {},
        "aoptLinkNo": "",
        "autoHelp": "",
        "isEnableOpt": "",
        "value": ""
      }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

**응답시간(초) 샘플**: 0.11

---

## 3. dashboardInfo (시스템보안_대시보드정보)

### 3.0 API 기본 정보

| 항목 | 내용 |
|---|---|
| API 제목 | 시스템보안_시스템보안_대시보드정보 |
| API 이름(영문) | dashboardInfo |
| API 설명 | 인프라 취약점 통합 관리 시스템에서 관리하는 대시보드 데이터 조회 정보 제공 API |

### 3.1 서브 리소스 목록

| 번호 | HTTP 메소드 | 서브 리소스(한글명) | API Endpoint URI |
|---|---|---|---|
| 1 | GET | 자산상태별 인프라 취약점 현황 | /ivms/api/vulStatByAsst |
| 2 | GET | 최근 6개월 취약점 현황 | /ivms/api/vulCntRcnt |
| 3 | GET | 취약점 항목 순위 | /ivms/api/vulCodeRank |
| 4 | GET | 올해 등록된 자산별 취약점 현황 | /ivms/api/rcntAsstRslt |
| 5 | GET | 올해 미점검 자산 현황 | /ivms/api/diagStatAsst |
| 6 | GET | 자산 상태별 현황 | /ivms/api/asstStateByAgState |
| 7 | GET | 자산 취약점 현황 | /ivms/api/asstVulState |
| 8 | GET | 항목별 취약자산 현황 | /ivms/api/asstVulStateByGdln |

> 공통 입력 파라미터: `userId`(사용자ID, admin), `templateNo`(진단템플릿), `diagYear`(기준연도), `orgId`(부서ID), `rspnMngId`(담당자ID), `asstLCtgrId`/`asstMCtgrId`/`asstSCtgrId`(자산분류 대/중/소, *대시보드 조회시 디폴트 값 설정)가 대부분 오퍼레이션에 공통으로 사용된다.

### 3.2 자산상태별 인프라 취약점 현황 — `GET /ivms/api/vulStatByAsst` (IF-API-097901)

**입력 데이터 (Query)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 |
|---|---|---|---|---|---|
| Query | userId | 사용자ID | string | Y | admin |
| Query | templateNo | 진단템플릿 | string | Y | 2 |
| Query | diagYear | 기준년도 | string | Y | 2025 |
| Query | orgId | 부서ID | string | N | |
| Query | rspnMngId | 담당자ID | string | N | yjw |
| Query | asstLCtgrId | 자산분류(대) | string | N | AT_0004286 |
| Query | asstMCtgrId | 자산분류(중) | string | N | |
| Query | asstSCtgrId | 자산분류(소) | string | N | |

```json
{
  "userId": "jwyoon21",
  "templateNo": "151",
  "diagYear": "2025",
  "asstLCtgrId": "AT_0005393",
  "orgId": "org_001048"
}
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 자산상태별취약점현황 결과 | object | Y | |
| result.asstStatusList | asstStatusList | 자산상태별취약점현황 목록 | Array[object] | Y | |
| asstStatusList[].category | category | 자산상태 | string | Y | 전체 관리 자산 |
| asstStatusList[].totalCnt | totalCnt | 합계 | integer | Y | 76 |
| asstStatusList[].passCnt | passCnt | 양호 개수 | integer | Y | 1 |
| asstStatusList[].vulCnt | vulCnt | 취약 개수 | integer | Y | 20 |
| asstStatusList[].gapCnt | gapCnt | 주차 (일주일) | integer | Y | 3 |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | |
| _server_message_.text | text | 결과 내용 | string | N | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 성공 등 |

```json
{
  "result": {
    "asstStatusList": [
      { "category": "전체 관리 자산", "totalCnt": 76, "passCnt": 1, "vulCnt": 20, "gapCnt": 3 },
      { "category": "정상 연동", "totalCnt": 4, "passCnt": 0, "vulCnt": 4, "gapCnt": 2 },
      { "category": "수동 등록", "totalCnt": 45, "passCnt": 0, "vulCnt": 7, "gapCnt": 0 },
      { "category": "점검 미수행", "totalCnt": 38, "passCnt": 0, "vulCnt": 0, "gapCnt": 38 },
      { "category": "미응답", "totalCnt": 27, "passCnt": 0, "vulCnt": 0, "gapCnt": 1 }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> 실제 curl 테스트(`dashboardInfo_대시보드정보/api_test/`) 응답에서 category 5종(전체 관리 자산, 정상 연동, 수동 등록, 점검 미수행, 미응답) 전체를 확인함.

**응답시간(초) 샘플**: 0.124

---

### 3.3 최근 6개월 취약점 현황 — `GET /ivms/api/vulCntRcnt` (IF-API-097902)

**입력 데이터 (Query)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 |
|---|---|---|---|---|---|
| Query | userId | 사용자ID | string | Y | admin |
| Query | templateNo | 진단템플릿 | string | Y | 2 |
| Query | diagYear | 기준년도 | string | Y | 2025 |
| Query | orgId | 부서ID | string | N | |
| Query | rspnMngId | 담당자ID | string | N | yjw |
| Query | asstLCtgrId | 자산분류(대) | string | N | AT_0004286 |
| Query | asstMCtgrId | 자산분류(중) | string | N | |
| Query | asstSCtgrId | 자산분류(소) | string | N | |
| Query | severity | 취약도 | string | Y | 1(최하), 2(하), 3(중), 4(상), 5(최상) |

```json
{
  "userId": "jwyoon21", "templateNo": "151", "diagYear": "2025",
  "severity": "1", "asstLCtgrId": "AT_0005393", "orgId": "org_001048"
}
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 6개월취약점현황 결과 정보 | object | Y | |
| result.vulCntList | vulCntList | 6개월취약점현황 목록 | Array[object] | Y | |
| vulCntList[].category | category | 월(month) | string | Y | |
| vulCntList[].totalCnt | totalCnt | 합계 | integer | Y | |
| vulCntList[].templateNo | templateNo | 진단템플릿 | string | Y | |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | |
| _server_message_.text | text | 결과 내용 | string | N | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 성공 등 |

```json
{
  "result": {
    "vulCntList": [
      { "category": "02", "totalCnt": 6, "templateNo": "2" },
      { "category": "03", "totalCnt": 77, "templateNo": "2" },
      { "category": "04", "totalCnt": 77, "templateNo": "2" },
      { "category": "05", "totalCnt": 77, "templateNo": "2" },
      { "category": "06", "totalCnt": 83, "templateNo": "2" },
      { "category": "07", "totalCnt": 83, "templateNo": "2" }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> **실제 curl 테스트로 확인**: `vulCntList`는 최근 6개월치(월별 6건)가 배열로 반환됨을 확인, 예시를 6건 전체로 교체함.

**응답시간(초) 샘플**: 0.427

---

### 3.4 취약점 항목 순위 — `GET /ivms/api/vulCodeRank` (IF-API-097903)

**입력 데이터 (Query)**: `vulCntRcnt`와 동일 (userId, templateNo, diagYear, orgId, rspnMngId, asstLCtgrId, asstMCtgrId, asstSCtgrId, severity)

```json
{
  "userId": "jwyoon21", "templateNo": "151", "diagYear": "2025",
  "severity": "4", "asstLCtgrId": "AT_0005393", "orgId": "org_001048"
}
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 취약점항목순위 결과 정보 | object | Y | |
| result.vulCntRankList | vulCntRankList | 취약점항목순위 목록 | Array[object] | Y | |
| vulCntRankList[].severity | severity | 취약도 | string | Y | 1(최하), 2(하), 3(중), 4(상), 5(최상) |
| vulCntRankList[].guidelineCd | guidelineCd | 항목코드 | string | Y | U-316 |
| vulCntRankList[].guidelineNm | guidelineNm | 항목명 | string | Y | 접속 IP 및 포트 제한 (U-316) |
| vulCntRankList[].totalCnt | totalCnt | 점검자산수 | integer | Y | |
| vulCntRankList[].vulCnt | vulCnt | 취약 자산수 | integer | Y | |
| vulCntRankList[].templateNo | templateNo | 진단템플릿 | string | Y | |
| vulCntRankList[].actionRate | actionRate | 조치율 | string | Y | 단위: %(비율) |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | |
| _server_message_.text | text | 결과 내용 | string | N | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 성공 등 |

```json
{
  "result": {
    "vulCntRankList": [
      {
        "severity": "4",
        "guidelineCd": "U-322",
        "guidelineNm": "OpenSSL 버전 취약성 및 최신 패치 사용유무 점검 (U-322)",
        "totalCnt": 5,
        "vulCnt": 5,
        "templateNo": "2",
        "actionRate": "0.0"
      },
      {
        "severity": "4",
        "guidelineCd": "U-301",
        "guidelineNm": "root 계정 원격 접속 제한 (U-301)",
        "totalCnt": 5,
        "vulCnt": 5,
        "templateNo": "2",
        "actionRate": "0.0"
      },
      {
        "severity": "4",
        "guidelineCd": "U-316",
        "guidelineNm": "접속 IP 및 포트 제한 (U-316)",
        "totalCnt": 5,
        "vulCnt": 5,
        "templateNo": "2",
        "actionRate": "0.0"
      },
      {
        "severity": "4",
        "guidelineCd": "U-403",
        "guidelineNm": "/etc/hosts 파일 소유자 및 권한 설정 (U-403)",
        "totalCnt": 5,
        "vulCnt": 4,
        "templateNo": "2",
        "actionRate": "20.0"
      },
      {
        "severity": "4",
        "guidelineCd": "U-103",
        "guidelineNm": "불필요한 계정 제거 (U-103)",
        "totalCnt": 5,
        "vulCnt": 4,
        "templateNo": "2",
        "actionRate": "20.0"
      }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> **실제 curl 테스트로 확인**: `vulCntRankList`는 취약도(severity)별 취약 항목 순위 5건이 배열로 반환됨을 확인, 예시를 5건 전체로 교체함.

**응답시간(초) 샘플**: 0.230

---

### 3.5 올해 등록된 자산별 취약점 현황 — `GET /ivms/api/rcntAsstRslt` (IF-API-097904)

**입력 데이터 (Query)**: userId, templateNo, diagYear, orgId, rspnMngId, asstLCtgrId, asstMCtgrId, asstSCtgrId

```json
{ "userId": "jwyoon21", "templateNo": "151", "asstLCtgrId": "AT_0005393", "orgId": "org_001048" }
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 올해자산별취약점 결과 정보 | object | Y | |
| result.recentAsstList | recentAsstList | 올해자산별취약점 목록 | Array[object] | Y | |
| recentAsstList[].hostNm | hostNm | 호스트명 | string | Y | SolidStep-CVE |
| recentAsstList[].ipAddrStr | ipAddrStr | IP주소 | string | Y | 192.168.2.112 |
| recentAsstList[].point | point | 보안점수 | integer | Y | 최근 진단이력이 있지만 진단상태가 중단이거나 실패인 경우에는 취약점 상세 정보 표시되지 않으며 보안점수가 0으로 나옴 |
| recentAsstList[].asstId | asstId | 자산ID | string | Y | |
| recentAsstList[].asstVer | asstVer | 자산버전 | integer | Y | |
| recentAsstList[].asstType | asstType | 자산타입 | string | Y | SSRCCE |
| recentAsstList[].asstLCtgrNm | asstLCtgrNm | 자산분류(대) | string | Y | |
| recentAsstList[].asstCode | asstCode | 자산코드 | string | Y | SSRCCE1-000001 |
| recentAsstList[].templateNo | templateNo | 진단템플릿 | string | Y | |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | |
| _server_message_.text | text | 결과 내용 | string | N | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 성공 등 |

```json
{
  "result": {
    "recentAsstList": [
      {
        "hostNm": "SolidStep-CVE",
        "ipAddrStr": "192.168.2.77",
        "point": 90,
        "asstId": "ASST_000000000000214",
        "asstVer": 1,
        "asstType": "SSRCCE",
        "asstLCtgrNm": "OS",
        "asstCode": "SSRCCE1-000001",
        "templateNo": "2"
      },
      {
        "hostNm": "SolidStep-CVE",
        "ipAddrStr": "192.168.2.112",
        "point": 90,
        "asstId": "ASST_000000000000240",
        "asstVer": 2,
        "asstType": "SSRCCE",
        "asstLCtgrNm": "OS",
        "asstCode": "SSRCCE1-000157",
        "templateNo": "2"
      },
      {
        "hostNm": "localhost.localdomain",
        "ipAddrStr": "192.168.2.114,192.168.122.1",
        "point": 0,
        "asstId": "ASST_000000000000341",
        "asstVer": 1,
        "asstType": "SSRCCE",
        "asstLCtgrNm": "OS",
        "asstCode": "SSRCCE1-028323",
        "templateNo": "2"
      }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> **실제 curl 테스트로 확인**: `ipAddrStr`는 자산에 IP가 여러 개인 경우 콤마로 구분되어 복수 값이 올 수 있음(예: "192.168.2.114,192.168.122.1"). `point`는 최근 진단이력이 없거나 진단이 중단/실패한 경우 0으로 반환됨.

---

### 3.6 올해 미점검 자산 현황 — `GET /ivms/api/diagStatAsst` (IF-API-097905)

**입력 데이터 (Query)**: userId, templateNo, diagYear, orgId, rspnMngId, asstLCtgrId, asstMCtgrId, asstSCtgrId + `page`(현재 페이지), `pageSize`(페이지당 항목 수)

```json
{ "userId": "jwyoon21", "templateNo": "151", "asstLCtgrId": "AT_0005393", "orgId": "org_001048" }
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 올해미점검자산 결과 정보 | object | Y | |
| result.diagStateList | diagStateList | 올해미점검자산 목록 | Array[object] | Y | |
| diagStateList[].hostNm | hostNm | 호스트명 | string | Y | SolidStep-CVE |
| diagStateList[].ipAddrStr | ipAddrStr | IP주소 | string | Y | 192.168.2.112 |
| diagStateList[].syncDt | syncDt | 등록일 | string | Y | 연동자산등록일(SSRCCE) |
| diagStateList[].asstId | asstId | 자산ID | string | Y | |
| diagStateList[].asstVer | asstVer | 자산버전 | integer | Y | |
| diagStateList[].asstLCtgrNm | asstLCtgrNm | 자산분류(대) | string | Y | |
| diagStateList[].templateNo | templateNo | 진단템플릿 | string | Y | |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | |
| _server_message_.text | text | 결과 내용 | string | N | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 성공 등 |

```json
{
  "result": {
    "diagStateList": [
      {
        "hostNm": "SolidStep-CCE",
        "ipAddrStr": "192.168.224.3",
        "syncDt": "2025-06-20",
        "asstId": "ASST_000000000000415",
        "asstVer": 1,
        "asstLCtgrNm": "OS",
        "templateNo": "2"
      },
      {
        "hostNm": "RHCOS_Openshift",
        "ipAddrStr": "https://api.test250415.ssrinc.co.kr:6443",
        "syncDt": "2025-06-24",
        "asstId": "ASST_000000000000395",
        "asstVer": 1,
        "asstLCtgrNm": "OS",
        "templateNo": "2"
      },
      {
        "hostNm": "1216자산",
        "ipAddrStr": "12.12.12.12",
        "syncDt": "2024-12-16",
        "asstId": "ASST_000000000000194",
        "asstVer": 1,
        "asstLCtgrNm": "OS",
        "templateNo": "2"
      }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> **실제 curl 테스트로 확인**: `diagStateList`는 실제로 총 44건이 배열로 반환됨(문서에는 대표 3건만 수록). `ipAddrStr`는 IP 대신 접속 URL 형태(예: "https://api.test250415.ssrinc.co.kr:6443")로 오는 경우도 있고, `hostNm`에 한글이 포함되는 경우도 있음.

**응답시간(초) 샘플**: 0.245

---

### 3.7 자산 상태별 현황 — `GET /ivms/api/asstStateByAgState` (IF-API-097906)

**입력 데이터 (Query)**: userId, orgId, templateNo, diagYear, severity, rspnMngId, asstLCtgrId, asstMCtgrId, asstSCtgrId

```json
{
  "userId": "jwyoon21", "templateNo": "151", "diagYear": "2025",
  "severity": "1", "asstLCtgrId": "AT_0005393", "orgId": "org_001048"
}
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 자산상태별현황 결과 정보 | object | Y | |
| result.asstStatusList | asstStatusList | 자산상태별현황 목록 | Array[object] | Y | |
| asstStatusList[].category | category | 자산 상태 분류 | string | Y | 전체연동자산 |
| asstStatusList[].totalCnt | totalCnt | 합계 | integer | Y | 76 |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | |
| _server_message_.text | text | 결과 내용 | string | N | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 성공 등 |

```json
{
  "result": {
    "asstStatusList": [
      { "category": "전체연동자산", "totalCnt": 76 },
      { "category": "정상연동", "totalCnt": 4 },
      { "category": "수동등록", "totalCnt": 45 },
      { "category": "점검완료", "totalCnt": 6 }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> 실제 curl 테스트(`dashboardInfo_대시보드정보/api_test/`) 응답에서 category 4종(전체연동자산, 정상연동, 수동등록, 점검완료) 전체를 확인함.

**응답시간(초) 샘플**: 0.05

---

### 3.8 자산 취약점 현황 — `GET /ivms/api/asstVulState` (IF-API-097907)

**입력 데이터 (Query)**: `asstStateByAgState`와 동일 (userId, orgId, templateNo, diagYear, severity, rspnMngId, asstLCtgrId, asstMCtgrId, asstSCtgrId)

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 자산취약점현황 결과 정보 | object | Y | |
| result.asstStatusList | asstStatusList | 자산취약점현황 목록 | Array[object] | Y | |
| asstStatusList[].category | category | 자산 상태 분류 | string | Y | 평균점수 |
| asstStatusList[].totalCnt | totalCnt | 합계 | integer | Y | 62 |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | |
| _server_message_.text | text | 결과 내용 | string | N | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 성공 등 |

```json
{
  "result": {
    "asstStatusList": [
      { "category": "평균점수", "totalCnt": 62 },
      { "category": "조치완료(100점)자산", "totalCnt": 0 },
      { "category": "조치중(100점미만)자산", "totalCnt": 6 },
      { "category": "총 취약점 개수", "totalCnt": 83 }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> **실제 curl 테스트로 확인**: category 4종의 정확한 명칭은 "평균점수", "조치완료(100점)자산", "조치중(100점미만)자산"(공백 없음), "총 취약점 개수"임 — 기존 문서의 "평균 점수", "조치 완료(100점)자산", "조치 중(100점미만)자산", "총 취약 개수"(공백 포함, "취약"만 표기)는 오기로 확인되어 수정함.

**응답시간(초) 샘플**: 0.06

---

### 3.9 항목별 취약자산 현황 — `GET /ivms/api/asstVulStateByGdln` (IF-API-097908)

**입력 데이터 (Query)**: userId, orgId, templateNo, diagYear, severity, rspnMngId, asstLCtgrId, asstMCtgrId, asstSCtgrId + `excludeYn`(조치율100%제외 여부, 기본 "N", 조치율 100% 제외 시 "Y"), `page`(현재 조회할 페이지), `pageSize`(페이지당 항목 수)

```json
{
  "userId": "jwyoon21", "templateNo": "151", "diagYear": "2025",
  "severity": "1", "asstLCtgrId": "AT_0005393", "orgId": "org_001048", "excludeYn": "Y"
}
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 항목별 취약자산 현황 결과 정보 | object | Y | |
| result.asstStatusList | asstStatusList | 항목별 취약자산 현황 목록 | Array[object] | Y | |
| asstStatusList[].guidelineNm | guidelineNm | 항목명 | string | Y | 사용자 UMASK 설정 (U-303) |
| asstStatusList[].severity | severity | 취약도 | string | Y | "4" |
| asstStatusList[].totalCnt | totalCnt | 점검자산수 | integer | Y | 5 |
| asstStatusList[].vulCnt | vulCnt | 취약자산수 | integer | Y | 1 |
| asstStatusList[].actionRate | actionRate | 조치율 | string | Y | 단위: %(비율) |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | |
| _server_message_.text | text | 결과 내용 | string | N | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 성공 등 |

**실제 curl 테스트 확정 예시** (`dashboardInfo_대시보드정보/api_test/`) — `asstStatusList` 46건 전체:

```json
{
  "result": {
    "asstStatusList": [
      { "guidelineNm": "/dev에 존재하지 않는 device 파일 제거 (U-309)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "/etc/(x)inetd.conf 파일 소유자 및 권한 설정 (U-404)", "severity": "4", "totalCnt": 5, "vulCnt": 2, "actionRate": "60.00" },
      { "guidelineNm": "/etc/hosts 파일 소유자 및 권한 설정 (U-403)", "severity": "4", "totalCnt": 5, "vulCnt": 4, "actionRate": "20.00" },
      { "guidelineNm": "/etc/shadow 파일 소유자 및 권한 설정 (U-402)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "$HOME/.rhosts, hosts.equiv 사용 금지 (U-408)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "AT 파일 소유자 및 권한 설정 (U-315)", "severity": "3", "totalCnt": 5, "vulCnt": 2, "actionRate": "60.00" },
      { "guidelineNm": "automountd 서비스 비활성화 (U-213)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "cron 파일 소유자 및 권한설정 (U-317)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "DoS 공격에 취약한 서비스 비활성화 (U-202)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "FTP 계정 shell 제한 (U-314)", "severity": "3", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "FTP 서비스 확인 (U-214)", "severity": "2", "totalCnt": 5, "vulCnt": 2, "actionRate": "60.00" },
      { "guidelineNm": "FTPusers 파일 설정 (U-216)", "severity": "3", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "FTPusers 파일 소유자 및 권한 설정 (U-215)", "severity": "2", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "hosts.lpd 파일 소유자 및 권한 설정 (U-310)", "severity": "2", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "NFS 서비스 비활성화 (U-206)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "NTP 시간 동기화 설정 (U-601)", "severity": "2", "totalCnt": 5, "vulCnt": 4, "actionRate": "20.00" },
      { "guidelineNm": "OpenSSL 버전 취약성 및 최신 패치 사용유무 점검 (U-322)", "severity": "4", "totalCnt": 5, "vulCnt": 5, "actionRate": "0.00" },
      { "guidelineNm": "R 계열 서비스 비활성화 (U-205)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "root 계정 원격 접속 제한 (U-301)", "severity": "4", "totalCnt": 5, "vulCnt": 5, "actionRate": "0.00" },
      { "guidelineNm": "RPC 서비스 확인 (U-217)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "Sendmail 버전 취약성 및 최신 패치 사용유무 점검 (U-318)", "severity": "4", "totalCnt": 5, "vulCnt": 2, "actionRate": "60.00" },
      { "guidelineNm": "Session Timeout 설정 (U-306)", "severity": "2", "totalCnt": 5, "vulCnt": 2, "actionRate": "60.00" },
      { "guidelineNm": "SMTP를 통한 사용자 정보 제공 명령어 제거 (U-208)", "severity": "3", "totalCnt": 5, "vulCnt": 2, "actionRate": "60.00" },
      { "guidelineNm": "SNMP COMMUNITY STRING 복잡성 설정 (U-210)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "SNMP 서비스 확인 (U-209)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "SU 명령어 사용 제한 (U-304)", "severity": "4", "totalCnt": 5, "vulCnt": 2, "actionRate": "60.00" },
      { "guidelineNm": "SUID, SGID 설정 파일 점검 (U-406)", "severity": "4", "totalCnt": 5, "vulCnt": 2, "actionRate": "60.00" },
      { "guidelineNm": "TFTP, TALK 서비스 비활성화 (U-203)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "World Writable 파일 점검 (U-308)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "경고 메시지 설정 (U-201)", "severity": "2", "totalCnt": 5, "vulCnt": 2, "actionRate": "60.00" },
      { "guidelineNm": "계정이 존재하지 않는 GID 금지 (U-112)", "severity": "2", "totalCnt": 5, "vulCnt": 3, "actionRate": "40.00" },
      { "guidelineNm": "관리자 그룹에 최소한의 계정 포함 (U-111)", "severity": "2", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "로그인 실패 횟수 제한 (U-107)", "severity": "3", "totalCnt": 5, "vulCnt": 2, "actionRate": "60.00" },
      { "guidelineNm": "불필요한 계정 제거 (U-103)", "severity": "4", "totalCnt": 5, "vulCnt": 4, "actionRate": "20.00" },
      { "guidelineNm": "불필요한 서비스 포트 제거 (U-602)", "severity": "3", "totalCnt": 5, "vulCnt": 2, "actionRate": "60.00" },
      { "guidelineNm": "사용자 UMASK 설정 (U-303)", "severity": "3", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "사용자, 시스템 시작파일 및 환경파일 소유자 및 권한 설정 (U-407)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "일반 사용자의 Sendmail 실행 방지 (U-319)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "접속 IP 및 포트 제한 (U-316)", "severity": "4", "totalCnt": 5, "vulCnt": 5, "actionRate": "0.00" },
      { "guidelineNm": "최근 패스워드 기억 설정 (U-114)", "severity": "3", "totalCnt": 5, "vulCnt": 2, "actionRate": "60.00" },
      { "guidelineNm": "최신 보안 패치 및 벤더 권고사항 적용 (U-501)", "severity": "4", "totalCnt": 5, "vulCnt": 2, "actionRate": "60.00" },
      { "guidelineNm": "파일 및 디렉터리 소유자 설정 (U-307)", "severity": "4", "totalCnt": 5, "vulCnt": 2, "actionRate": "60.00" },
      { "guidelineNm": "패스워드 복잡성 설정 (U-108)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "패스워드 알고리즘 SHA512 변경 여부 (U-701)", "severity": "4", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "패스워드 최소 사용기간 설정 (U-110)", "severity": "3", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" },
      { "guidelineNm": "홈 디렉터리 소유자 및 권한 설정 (U-409)", "severity": "3", "totalCnt": 5, "vulCnt": 1, "actionRate": "80.00" }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

**응답시간(초) 샘플**: 0.165

---

## 4. vulnerabilityInfo (시스템보안_취약점정보)

### 4.0 API 기본 정보

| 항목 | 내용 |
|---|---|
| API 제목 | 시스템보안_시스템보안_취약점정보 |
| API 이름(영문) | vulnerabilityInfo |
| API 설명 | 인프라 취약점 통합 관리 시스템에서 관리하는 취약점 조회 정보 제공 API |

### 4.1 서브 리소스 목록

| 번호 | HTTP 메소드 | 서브 리소스(한글명) | API Endpoint URI |
|---|---|---|---|
| 1 | POST | 취약점 항목별 상세조회 | /ivms/api/scanResultCodeMngtDetail |
| 2 | GET | 진단결과 이력조회 | /ivms/api/dgnsRslt |
| 3 | GET | 진단결과 상세 조회 | /ivms/api/guidelineScRslt |
| 4 | GET | 규정항목 상세 조회 | /ivms/api/guidelineCdInfo |
| 5 | POST | 규정항목 목록 조회 | /ivms/api/guidelineCdList |

> 5번 `guidelineCdList`는 서브 리소스 목록표에는 별도 행으로 기재되어 있지 않으나, 상세 스펙 캡처가 존재하여 본 문서에 포함함.

### 4.2 취약점 항목별 상세조회 — `POST /ivms/api/scanResultCodeMngtDetail` (IF-API-099501)

> **불일치 확인**: 서브 리소스 목록표의 endpoint는 `/scanResultCodeMngtDetail`이나, 실제 curl 테스트(`vulnerabilityInfo_취약점정보/api_test/`)의 요청 URL은 `/ivms/api/mngtListDetail`로 캡처되어 있어 표기가 서로 다름. 실제 서버에서 사용하는 endpoint 확정이 필요함.

**입력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 | 설명 |
|---|---|---|---|---|---|---|
| Body | userId | 사용자ID | string | Y | jwyoon21 | 데이터가 많아 오래 걸릴 수 있으니 좌측 데이터 샘플로 조회 바랍니다 |
| | resultStatusCdListStr | 점검결과리스트 | string | N | FAIL | |
| | guidelineCdList | 항목코드리스트 | string | N | | |
| | vadaYn | 자산타입 VADA 여부 | string | N | N | 기본: "N", assetType이 "VADA": "Y" |
| | ipAddrStr | IP주소 | string | N | | |
| | hostNm | 호스트명 | Array[string] | N | | 데이터가 많아 오래 걸릴 수 있으니 좌측 데이터 샘플로 조회 바랍니다 |
| | asstLCtgrId | 자산분류(대) | string | N | AT_0005393 | *대시보드에서 이동시 디폴트 값 설정. 데이터가 많아 오래 걸릴 수 있으니 좌측 데이터 샘플로 조회 바랍니다 |
| | asstMCtgrId | 자산분류(중) | string | N | | |
| | asstSCtgrId | 자산분류(소) | string | N | | |
| | asstLGroupId | 자산그룹(대) | string | N | GR_0001495 | |
| | asstMGroupId | 자산그룹(중) | string | N | | |
| | asstSGroupId | 자산그룹(소) | string | N | | |
| | mgmtOrgId | 부서ID | string | N | | |
| | rspnMngId | 담당자ID | string | N | | |
| | asstType | 자산타입 | string | Y | SSRCCE | |
| | severity | 취약도 | string | Y | 4 | 1(최하), 2(하), 3(중), 4(상), 5(최상). 데이터가 많아 오래 걸릴 수 있으니 좌측 데이터 샘플로 조회 바랍니다 |
| | profileNm | 프로파일명 | string | N | | |
| | atemplateNo | 진단템플릿 | string | N | | *대시보드에서 이동시 디폴트 값 설정 |
| | asstCode | 자산코드 | Array[string] | N | SSRCCE1-000001 | |
| | chartDashboardYn | 차트 대시보드 여부 | string | N | Y | 최근자산취약점현황에서 이동시 필수 세팅. 대시보드 > 그래프에서 이동시 "Y"로 필수 세팅 |
| | guidelineCd | 항목코드 | string | N | U-322 | 대시보드 > 그래프에서 이동시 필수 세팅 |
| | page | 현재 페이지 | integer | N | 1 | |
| | pageSize | 페이지당 항목 수 | integer | N | 50 | |

```json
{
  "userId": "admin",
  "asstCode": ["SSRCCE3-000747", "SSRCCE3-000492", "SSRCCE1-000529"],
  "hostNm": ["absdb1", "lbsh1", "verfdba1"],
  "resultStatusCdListStr": "[\"FAIL\"]",
  "vadaYn": "N",
  "asstType": "SSRCCE",
  "severity": "4",
  "atemplateNo": "151"
}
```

> **실제 curl 테스트로 확인**: `resultStatusCdListStr`은 JSON 배열을 문자열로 직렬화한 값(`"[\"FAIL\"]"`)으로 전달됨. 필드명은 `assetCode`가 아닌 `asstCode`로 확인됨.

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 취약점진단항목 결과 정보 | object | Y | |
| result.scanRsltCodeList | scanRsltCodeList | 취약점진단항목 목록 | Array[object] | Y | |
| scanRsltCodeList[].asstId | asstId | 자산 ID | string | Y | |
| scanRsltCodeList[].asstCode | asstCode | 자산 코드 | string | N | |
| scanRsltCodeList[].mgmtOrgId | mgmtOrgId | 관리 조직 ID | string | N | |
| scanRsltCodeList[].asstNm | asstNm | 자산 명 | string | Y | AIX7 |
| scanRsltCodeList[].hostNm | hostNm | 호스트명 | string | Y | AIX7 |
| scanRsltCodeList[].asstType | asstType | 자산 유형 | string | N | |
| scanRsltCodeList[].asstLCtgrId | asstLCtgrId | 자산 대분류 ID | string | N | |
| scanRsltCodeList[].asstMCtgrId | asstMCtgrId | 자산 중분류 ID | string | N | |
| scanRsltCodeList[].asstSCtgrId | asstSCtgrId | 자산 소분류 ID | string | N | |
| scanRsltCodeList[].ipAddrStr | ipAddrStr | IP 주소 문자열 | string | N | |
| scanRsltCodeList[].asstLCtgrNm | asstLCtgrNm | 자산 대분류 명 | string | N | AIX |
| scanRsltCodeList[].asstMCtgrNm | asstMCtgrNm | 자산 중분류 명 | string | N | AIX |
| scanRsltCodeList[].asstSCtgrNm | asstSCtgrNm | 자산 소분류 명 | string | N | 값이 없으면 필드 자체가 응답에서 생략될 수 있음 |
| scanRsltCodeList[].scanIfKey | scanIfKey | 스캔 인터페이스 키 | string | Y | |
| scanRsltCodeList[].resultIfKey | resultIfKey | 결과 인터페이스 키 | string | Y | |
| scanRsltCodeList[].ifKey | ifKey | 인터페이스 키 | string | Y | |
| scanRsltCodeList[].assetIfKey | assetIfKey | 자산 인터페이스 키 | integer | Y | |
| scanRsltCodeList[].profileIfKey | profileIfKey | 프로파일 인터페이스 키 | integer | Y | |
| scanRsltCodeList[].guidelineIfKey | guidelineIfKey | 가이드라인 인터페이스 키 | integer | Y | |
| scanRsltCodeList[].asrcId | asrcId | ASRC ID | string | N | |
| scanRsltCodeList[].asrcVer | asrcVer | ASRC 버전 | integer | N | |
| scanRsltCodeList[].agentServerNm | agentServerNm | 에이전트 서버 명 | string | N | |
| scanRsltCodeList[].profileNm | profileNm | 프로파일 명 | string | N | SSR_기준항목 |
| scanRsltCodeList[].regulationNm | regulationNm | 진단템플릿명 | string | N | |
| scanRsltCodeList[].guidelineCd | guidelineCd | 항목 코드 | string | Y | U-114 |
| scanRsltCodeList[].createdTime | createdTime | 생성 일시 | string | Y | 2025-04-02 15:36:29 |
| scanRsltCodeList[].atemplateNo | atemplateNo | 템플릿 번호 | string | Y | |
| scanRsltCodeList[].itemCode | itemCode | 시스템 코드 | string | Y | U6112 |
| scanRsltCodeList[].guidelineNm | guidelineNm | 항목 명 | string | Y | 최근 패스워드 기억 설정 |
| scanRsltCodeList[].subjectType | subjectType | 자산 분류 | string | N | OS |
| scanRsltCodeList[].subjectSubType | subjectSubType | 시스템 유형 | string | N | AIX,HP-UX,Linux,Solaris |
| scanRsltCodeList[].severity | severity | 취약도 | string | N | |
| scanRsltCodeList[].result | result | 결과 | string | N | FAIL |
| scanRsltCodeList[].resultNm | resultNm | 결과명 | string | N | 취약. NA: N/A FAIL: 취약 PASS: 양호 EXCEPT: 예외 REVIEW: 리뷰 |
| scanRsltCodeList[].stateCd | stateCd | 등록상태 코드 | string | N | U |
| scanRsltCodeList[].stateCdNm | stateCdNm | 등록상태 코드 명 | string | N | |
| scanRsltCodeList[].dgnosResult | dgnosResult | 진단 결과 | string | N | |
| scanRsltCodeList[].dgnosResultNm | dgnosResultNm | 진단 결과 명 | string | N | |
| scanRsltCodeList[].expectDt | expectDt | 예상 일시 | string | N | |
| scanRsltCodeList[].changeReason | changeReason | 변경 사유 | string | N | 불필요계정/서비스아님 |
| scanRsltCodeList[].changeReasonNm | changeReasonNm | 변경 사유 명 | string | N | UANS: 불필요계정/서비스아님 SIANC: 서비스 영향도 확인불가 |
| scanRsltCodeList[].detail | detail | 상세 설명 | string | N | |
| scanRsltCodeList[].vadaYn | vadaYn | VADA 여부 | string | N | Y |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | |
| _server_message_.text | text | 결과 내용 | string | N | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 성공 등 |

```json
{
  "result": {
    "scanRsltCodeList": [
      {
        "asstId": "ASST_000000000000297",
        "asstCode": "SSRCCE1-028277",
        "mgmtOrgId": "",
        "asstNm": "AIX7",
        "hostNm": "AIX7",
        "asstType": "SSRCCE",
        "asstLCtgrId": "AT_0004286",
        "asstMCtgrId": "AT_0004291",
        "asstSCtgrId": "AT_0004292",
        "ipAddrStr": "192.168.2.155",
        "asstLCtgrNm": "OS",
        "asstMCtgrNm": "AIX",
        "scanIfKey": "10000000001761644",
        "resultIfKey": "1761644",
        "ifKey": "64462414",
        "assetIfKey": 28277,
        "profileIfKey": 644,
        "guidelineIfKey": 27741,
        "asrcId": "",
        "asrcVer": 0,
        "agentServerNm": "CCE1",
        "profileNm": "test0327",
        "regulationNm": "SSR_기준항목",
        "guidelineCd": "U-103",
        "createdTime": "2025-04-02 15:36:29",
        "atemplateNo": "151",
        "itemCode": "U5110",
        "guidelineNm": "불필요한 계정 제거",
        "subjectType": "OS",
        "subjectSubType": "AIX,HP-UX,Linux,Solaris",
        "severity": "4",
        "result": "FAIL",
        "resultNm": "취약",
        "stateCd": "",
        "dgnosResult": "",
        "dgnosResultNm": "",
        "expectDt": "",
        "changeReason": "",
        "changeReasonNm": "",
        "detail": "",
        "vadaYn": "Y"
      }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> **실제 curl 테스트로 확인**: `asstMCtgrNm` 다음에 오던 `asstSCtgrNm`은 값이 없을 경우 응답에서 필드 자체가 생략될 수 있음(위 예시에는 미포함). `profileIfKey`/`guidelineIfKey` 값은 문서상 서로 뒤바뀌어 있었던 것을 실제 캡처 기준(profileIfKey: 644, guidelineIfKey: 27741)으로 수정함. `atemplateNo`는 요청 파라미터 값을 따라 실제로는 "151"로 반환됨. `stateCd`, `dgnosResult`, `dgnosResultNm`, `expectDt`, `changeReason`, `changeReasonNm`, `detail`은 값이 없는 경우 빈 문자열("")로 반환됨을 확인.

---

### 4.3 진단결과 이력조회 — `GET /ivms/api/dgnsRslt` (IF-API-099502)

**입력 데이터 (Query)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 | 설명 |
|---|---|---|---|---|---|---|
| Query | ip | ip | string | Y | 165.244.21.243 | |
| Query | assetIfKey | 자산 인터페이스키 | integer | Y | | |
| Query | agentServerNm | 에이전트 서버명 | string | Y | | |
| Query | atemplateNo | 진단템플릿 | string | N | | 필수값은 아니지만 파라미터 누락시, 전체 템플릿 기준으로 리스트가 조회됩니다 |

```json
{
  "ip": "165.244.21.243",
  "asstId": "ASST_000000000094531",
  "assetIfKey": 88,
  "agentServerNm": "CCE1",
  "atemplateNo": "151"
}
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 진단결과 이력조회 결과 정보 | object | Y | |
| result.ip | ip | IP 주소 | string | Y | |
| result.diagResultList | diagResultList | 진단결과 이력조회 목록 | Array[object] | Y | |
| diagResultList[].regulationIfKey | regulationIfKey | 규정 인터페이스키 | string | N | |
| diagResultList[].resultIfKey | resultIfKey | 진단결과 인터페이스키 | integer | N | |
| diagResultList[].profileIfKey | profileIfKey | 프로파일 인터페이스키 | integer | N | |
| diagResultList[].scanIfKey | scanIfKey | 진단 인터페이스키 | string | N | |
| diagResultList[].point | point | 보안점수 | integer | N | |
| diagResultList[].progressRate | progressRate | 진단 진행률 | string | N | 3/3 |
| diagResultList[].timeStart | timeStart | 진단시작시간 | string | N | 2025-04-02 15:36:29 |
| diagResultList[].timeEnd | timeEnd | 진단종료시간 | string | N | |
| diagResultList[].state | state | 진단 상태 | string | N | COMPLETED |
| diagResultList[].profileNm | profileNm | 프로젝트명 | string | N | test0327 |
| diagResultList[].cntFail | cntFail | 진단결과 '실패' 개수 | integer | N | 35 |
| diagResultList[].cntReview | cntReview | 진단결과 '리뷰' 개수 | integer | N | 0 |
| diagResultList[].asstType | asstType | 자산타입 | string | N | SSRCCE |
| diagResultList[].agentServerNm | agentServerNm | 에이전트 서버명 | string | N | CCE1 |
| diagResultList[].regulationNm | regulationNm | 규정(진단템플릿) 명 | string | N | SSR_기준항목 |
| diagResultList[].atemplateNo | atemplateNo | 진단템플릿 | string | N | |
| diagResultList[].reportFilePath | reportFilePath | SSRCCE 보고서 경로 | string | N | 2/Individual/OS/1761_aix_AIX7_192.168.2.155.xlsm |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | |
| _server_message_.text | text | 결과 내용 | string | N | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 성공 등 |

```json
{
  "result": {
    "ip": "192.168.2.155",
    "diagResultList": [
      {
        "regulationIfKey": "2",
        "resultIfKey": 1761644,
        "profileIfKey": 644,
        "scanIfKey": "10000000001761644",
        "point": 50,
        "progressRate": "3/3",
        "timeStart": "2025-04-02 15:36:29",
        "timeEnd": "2025-04-02 15:36:29",
        "state": "COMPLETED",
        "profileNm": "test0327",
        "cntFail": 35,
        "cntReview": 0,
        "asstType": "SSRCCE",
        "agentServerNm": "CCE1",
        "regulationNm": "SSR_기준항목",
        "atemplateNo": "2",
        "reportFilePath": "2/Individual/OS/1761_aix_AIX7_192.168.2.155.xlsm"
      },
      {
        "regulationIfKey": "2",
        "resultIfKey": 1754644,
        "profileIfKey": 644,
        "scanIfKey": "10000000001754644",
        "point": 50,
        "progressRate": "3/3",
        "timeStart": "2025-04-01 13:47:05",
        "timeEnd": "2025-04-02 15:36:28",
        "state": "COMPLETED",
        "profileNm": "test0327",
        "cntFail": 35,
        "cntReview": 0,
        "asstType": "SSRCCE",
        "agentServerNm": "CCE1",
        "regulationNm": "SSR_기준항목",
        "atemplateNo": "2",
        "reportFilePath": "2/Individual/OS/1754_aix_AIX7_192.168.2.155.xlsm"
      },
      {
        "regulationIfKey": "2",
        "resultIfKey": 1718640,
        "profileIfKey": 640,
        "scanIfKey": "10000000001718640",
        "point": 50,
        "progressRate": "3/3",
        "timeStart": "2025-03-27 14:47:28",
        "timeEnd": "2025-03-27 14:47:28",
        "state": "COMPLETED",
        "profileNm": "test0326-1",
        "cntFail": 35,
        "cntReview": 0,
        "asstType": "SSRCCE",
        "agentServerNm": "CCE1",
        "regulationNm": "SSR_기준항목",
        "atemplateNo": "2",
        "reportFilePath": "2/Individual/OS/1718_aix_AIX7_192.168.2.155.xlsm"
      }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> **실제 curl 테스트로 확인**: `diagResultList`는 실제로 총 12건이 배열로 반환됨(문서에는 대표 3건만 수록). 필드표에는 있었으나 예시에서 누락되었던 `scanIfKey`를 추가함. `reportFilePath`의 디렉터리명은 `individual`이 아닌 `Individual`(대문자 I)로 확인됨.

**응답시간(초) 샘플**: 0.08

---

### 4.4 진단결과 상세 조회 — `GET /ivms/api/guidelineScRslt` (IF-API-099503)

**입력 데이터 (Query)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 |
|---|---|---|---|---|---|
| Query | resultId | 진단결과 ID | string | Y | RESULT_01005430 |
| Query | agentServerNm | 에이전트 서버명 | string | Y | CCE1 |
| Query | page | 현재 조회할 페이지 | integer | N | 1 |
| Query | pageSize | 페이지당 항목 수 | integer | N | 50 |

```json
{ "resultId": "RESULT_01005430", "agentServerNm": "CCE1" }
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 진단결과 상세조회 결과 정보 | object | Y | |
| result.guidelineScRsltList | guidelineScRsltList | 진단결과 상세조회 목록 | Array[object] | Y | |
| guidelineScRsltList[].resultIfKey | resultIfKey | 진단결과 인터페이스키 | integer | Y | |
| guidelineScRsltList[].guidelineIfKey | guidelineIfKey | 항목 인터페이스키 | integer | Y | |
| guidelineScRsltList[].itemCode | itemCode | 시스템코드 | string | Y | U5203_08 |
| guidelineScRsltList[].agentServerNm | agentServerNm | 에이전트서버명 | string | Y | CCE1 |
| guidelineScRsltList[].regulationNm | regulationNm | 규정(진단템플릿)명 | string | Y | |
| guidelineScRsltList[].category | category | 분류 | string | Y | 계정관리. (자산 진단 항목 분류명(조인관리, 패치관리, 사용자인증, 접근권한관리, 시스템보안설정 등)) |
| guidelineScRsltList[].guidelineCd | guidelineCd | 항목코드 | string | Y | U-101 |
| guidelineScRsltList[].guidelineNm | guidelineNm | 항목명 | string | Y | 관리자 계정의 UID 중복 제거 |
| guidelineScRsltList[].severity | severity | 취약도 | string | Y | "3" |
| guidelineScRsltList[].result | result | 결과 | string | Y | PASS |
| guidelineScRsltList[].resultNm | resultNm | 결과명 | string | Y | 양호. 양호, 리뷰, 취약, 예외, N/A |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | |
| _server_message_.text | text | 결과 내용 | string | N | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 성공 등 |

```json
{
  "result": {
    "guidelineScRsltList": [
      {
        "resultIfKey": 2404975,
        "guidelineIfKey": 27739,
        "itemCode": "U1102",
        "agentServerNm": "CCE1",
        "regulationNm": "SSR_기준항목",
        "category": "계정관리",
        "guidelineCd": "U-101",
        "guidelineNm": "관리자 계정의 UID 중복 제거",
        "severity": "3",
        "result": "PASS",
        "resultNm": "양호"
      }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> 실제 curl 테스트(`vulnerabilityInfo_취약점정보/api_test/`) 응답에서 확인된 항목은 `guidelineCd: U-101`(관리자 계정의 UID 중복 제거, severity 3) 예시 1건뿐임. 이전 버전 문서에 있던 LG-001/LG-PW-001~004/SRV-001·003·004·013·018·020·022 항목들은 실제 캡처에서 확인되지 않아(스펙 정의표 재확인 결과 근거 없음) 모두 삭제함.

**응답시간(초) 샘플**: 0.175

---

### 4.5 규정항목 상세 조회 — `GET /ivms/api/guidelineCdInfo` (IF-API-099504)

**입력 데이터 (Query)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 샘플 |
|---|---|---|---|---|---|
| Query | aresultNo | 진단결과 번호 | integer | Y | 269953 |
| Query | guidelineIfKey | 항목 인터페이스키 | integer | Y | 81438 |
| Query | guidelineCd | 항목코드 | string | Y | DBM-001 |
| Query | itemCode | 시스템코드 | string | Y | MAR6103_001 |
| Query | agentServerNm | 에이전트 서버명 | string | Y | CCE3 |

```json
{
  "aresultNo": 269953, "guidelineIfKey": 81438,
  "guidelineCd": "DBM-001", "itemCode": "MAR6103_001", "agentServerNm": "CCE3"
}
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | 타입 | 필수 | 설명 |
|---|---|---|---|---|---|
| result | result | 규정항목 상세조회 결과 정보 | object | Y | |
| result.guidelineCdInfo | guidelineCdInfo | 규정항목 상세조회 | object | Y | |
| guidelineCdInfo.guidelineCd | guidelineCd | 항목코드 | string | Y | U-103 |
| guidelineCdInfo.category | category | 분류 | string | Y | 계정관리. **자산 진단 항목 분류명 (보안관리, 패치관리, 사용자인증, 접근권한관리, 시스템보안설정 등)** |
| guidelineCdInfo.subjectType | subjectType | 자산분류 | string | Y | Web |
| guidelineCdInfo.subjectSubType | subjectSubType | 점검대상 | string | Y | Apache |
| guidelineCdInfo.severity | severity | 취약도 | string | Y | 3 |
| guidelineCdInfo.guidelineNm | guidelineNm | 항목명 | string | Y | 불필요한 계정 제거 |
| guidelineCdInfo.criteria | criteria | 진단기준 | string | Y | 소스 및 설정 파일 쓰기권한 제거 |
| guidelineCdInfo.analysisInfo | analysisInfo | 현황 | string | Y | |
| guidelineCdInfo.measure | measure | 조치방법 | string | Y | (아래 참고) |
| guidelineCdInfo.measureDetailOrigin | measureDetailOrigin | 세부설정 | object | Y | |
| _server_message_ | _server_message_ | 결과 정보 | object | Y | |
| _server_message_.text | text | 결과 내용 | string | N | |
| _server_message_.type | type | 결과 코드 | string | Y | 200 성공 등 |

**실제 curl 테스트 확정 예시** (`vulnerabilityInfo_취약점정보/api_test/`):

> **참고**: 요청 파라미터는 `guidelineCd=DBM-001`(aresultNo=269953, guidelineIfKey=81438, itemCode=MAR6103_001, agentServerNm=CCE3)이나, 실제 응답 본문에 담긴 데이터는 `guidelineCd: U-103`(계정관리/OS/AIX,HP-UX,Linux,Solaris/불필요한 계정 제거) 건임. 동일한 요청 조건으로 재확인한 결과 응답이 재현되어, 이는 캡처 오류가 아니라 이 오퍼레이션의 실제 동작(요청 파라미터의 `guidelineCd`와 무관하게 `aresultNo`/`guidelineIfKey`/`itemCode`/`agentServerNm` 조합 기준으로 해당 진단결과의 항목 상세를 반환하는 것으로 추정)으로 확정함.

```json
{
  "result": {
    "guidelineCdInfo": {
      "guidelineCd": "U-103",
      "category": "계정관리",
      "subjectType": "OS",
      "severity": "4",
      "subjectSubType": "AIX,HP-UX,Linux,Solaris",
      "guidelineNm": "불필요한 계정 제거",
      "criteria": "【진단기준】\n----------------------------------------------------------------------------------------------\n◆ 양호 : 계정 정보를 확인하여 불필요한 계정이 없는 경우 \n◆ 취약 : 인가되지 않은 계정, 퇴직자 계정, 테스트 계정 등 불필요한 계정이 존재하는 경우\n\n【상세설명】\n----------------------------------------------------------------------------------------------\n- 시스템 계정 중 불필요한 계정(퇴직, 전직, 휴직 등의 이유로 사용하지 않는 계정 및 장기적으로 사용하지 않는 계정 등) 이 존재하는지 점검\n- 불필요한 계정이 존재하는지 점검하여 관리되지 않은 계정에 의한 침입에 잘 대비하는지 확인하기 위함\n- OS나 Package 설지 시 Default로 생성되는 계정 및 불필요한 계정들은 비인가자의 공격(무작위 대입 공격, 사전 대입 공격) 에 의해 패스워드가 유출될 위험이 존재함\n\n◆ 참고\n    - Default 계정: OS나 Package 설치 시 기본적으로 생성되는 계정(예 Ip, uucp, nuucp 등)\n    - 불필요한 default 계정 삭제 시 업무 영향도 파악 후 삭제 권고",
      "analysisInfo": "[취약점현황]\n.......................................................................\n문제점1. /etc/passwd 의 설정 현황 >> 불필요한 계정 존재\n     lp     uucp     \n.......................................................................\n\n[시스템현황]\n/etc/passwd 의 설정 현황 >>\nroot:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\nbin:x:2:2:bin:/bin:/usr/sbin/nologin\nsys:x:3:3:sys:/dev:/usr/sbin/nologin\nsync:x:4:65534:sync:/bin:/bin/sync\ngames:x:5:60:games:/usr/games:/usr/sbin/nologin\nman:x:6:12:man:/var/cache/man:/usr/sbin/nologin\nmail:x:8:8:mail:/var/mail:/usr/sbin/nologin\nnews:x:9:9:news:/var/spool/news:/usr/sbin/nologin\nproxy:x:13:13:proxy:/bin:/usr/sbin/nologin\nwww-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\nbackup:x:34:34:backup:/var/backups:/usr/sbin/nologin\nlist:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin\nirc:x:39:39:ircd:/run/ircd:/usr/sbin/nologin\ngnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/usr/sbin/nologin\nnobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin\n_apt:x:100:65534::/nonexistent:/usr/sbin/nologin\nsystemd-timesync:x:101:101:systemd Time Synchronization,,,:/run/systemd:/usr/sbin/nologin\nsystemd-network:x:102:103:systemd Network Management,,,:/run/systemd:/usr/sbin/nologin\nsystemd-resolve:x:103:104:systemd Resolver,,,:/run/systemd:/usr/sbin/nologin\nmessagebus:x:104:110::/nonexistent:/usr/sbin/nologin\nsshd:x:105:65534::/run/sshd:/usr/sbin/nologin\nssrinc:x:1000:1000:ssrinc,,,:/home/ssrinc:/bin/bash\nsystemd-coredump:x:999:999:systemd Core Dumper:/:/usr/sbin/nologin\npostgres:x:106:113:PostgreSQL administrator,,,:/var/lib/postgresql:/bin/bash\nredis:x:107:114::/var/lib/redis:/usr/sbin/nologin\ntcpdump:x:108:115::/nonexistent:/usr/sbin/nologin\nlp:x:7:7::/var/spool/lpd:/usr/sbin/nologin\nuucp:x:10:10::/var/spool/uucp:/usr/sbin/nologin\nntp:x:109:116::/nonexistent:/usr/sbin/nologin\n_rpc:x:110:65534::/run/rpcbind:/usr/sbin/nologin\nstatd:x:111:65534::/var/lib/nfs:/usr/sbin/nologin\n\n===============================================================================================\n[세부설정현황]\n* SolidStep UI > 항목 탭 > SSR_기준항목 > U-103 > 수정\n#----------------------------------------------------------------------------------------------\n설정 : check_unnecessary_account=1\n설명 : [전체 적용 옵션] 불필요한 계정 진단 여부 설정\n#----------------------------------------------------------------------------------------------\n설정 : aix_check_unnecessary_account\n설명 : \nOS별 불필요한 계정 목록 입력\nglob 방식 옵션 (대소문자 구분 안함)\n*      : 매칭되는 모든 문자를 찾음                  ex) ABCtest, 123Test\n*test : 문자열 뒤에 test 존재시\n?      : 매칭되는 임의의 문자 1개를 찾음\ntest? : test 뒤의 문자 하나가 있는 경우           ex) test1, testr, test_\n설정값 : lp, uucp, nuucp\n#----------------------------------------------------------------------------------------------\n설정 : hpux_check_unnecessary_account\n설명 : \nOS별 불필요한 계정 목록 입력\nglob 방식 옵션 (대소문자 구분 안함)\n*      : 매칭되는 모든 문자를 찾음                  ex) ABCtest, 123Test\n*test : 문자열 뒤에 test 존재시\n?      : 매칭되는 임의의 문자 1개를 찾음\ntest? : test 뒤의 문자 하나가 있는 경우           ex) test1, testr, test_\n설정값 : lp, uucp, nuucp\n#----------------------------------------------------------------------------------------------\n설정 : linux_check_unnecessary_account\n설명 : \nOS별 불필요한 계정 목록 입력\nglob 방식 옵션 (대소문자 구분 안함)\n*      : 매칭되는 모든 문자를 찾음                  ex) ABCtest, 123Test\n*test : 문자열 뒤에 test 존재시\n?      : 매칭되는 임의의 문자 1개를 찾음\ntest? : test 뒤의 문자 하나가 있는 경우           ex) test1, testr, test_\n설정값 : lp, uucp, nuucp\n#----------------------------------------------------------------------------------------------\n설정 : solaris_check_unnecessary_account\n설명 : \nOS별 불필요한 계정 목록 입력\nglob 방식 옵션 (대소문자 구분 안함)\n*      : 매칭되는 모든 문자를 찾음                  ex) ABCtest, 123Test\n*test : 문자열 뒤에 test 존재시\n?      : 매칭되는 임의의 문자 1개를 찾음\ntest? : test 뒤의 문자 하나가 있는 경우           ex) test1, testr, test_\n설정값 : lp, uucp, nuucp\n#----------------------------------------------------------------------------------------------\n설정 : exclude_check_os\n설명 : \n[전체 적용 옵션] 진단 제외 Unix OS 한 줄에 하나씩 입력 ( OS 별 옵션은 <OTHERS>옵션보다 우선순위가 높음)\n입력 OS 목록 : [aix, linux, hpux, solaris <OTHERS>]\n제외 OS 처리 : [ 0-양호, 1-N/A, 2-취약, 3-수동, 4-대체, 5-예외, 9-일반진단 ]\nex) aix^1, <OTHERS>^3 (aix에서는 N/A, 나머지 OS는 수동처리, 미입력 일반진단)\n설정값 : 미설정\n#----------------------------------------------------------------------------------------------\n설정 : check_service\n설명 : [전체 적용 옵션] 서비스 실행여부 진단 여부 설정\n설정값 : [Uncheck]\n#----------------------------------------------------------------------------------------------\n설정 : check_conffile_contents\n설명 : [전체 적용 옵션] 설정파일 내용 진단 여부 설정\n설정값 : [Uncheck]\n===============================================================================================\n",
      "measure": "▶ 현재 등록된 계정 현황 확인 후 불필요한 계정 삭제\n\n【점검방법】\n----------------------------------------------------------------------------------------------\n[SunOS, LINUX, AIX, HP-UX]\n- 사용하지 않는 불필요한 계정의 존재 여부를 확인한다\n    # cat /etc/passwd     \n        root:x:0:0:root:/root:/bin/bash\n        daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n        bin:x:2:2:bin:/bin:/usr/sbin/nologin\n        sys:x:3:3:sys:/dev:/usr/sbin/nologin\n        sync:x:4:65534:sync:/bin:/bin/sync\n        games:x:5:60:games:/usr/games:/usr/sbin/nologin\n        man:x:6:12:man:/var/cache/man:/usr/sbin/nologin\n        lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin\n        mail:x:8:8:mail:/var/mail:/usr/sbin/nologin\n        uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin\n\n◆ 참고\n    - 리눅스 주요 계정\n        lp : Line Printer\n        UUCP : Unix-to-Unix Copy\n\n【조치방법】\n----------------------------------------------------------------------------------------------\n[Solaris, LINUX, HP-UX]\n- 서버에 등록된 불필요한 사용자 계정을 제거한다\n    # userdel [사용자명]\n\n◆ 참고\n    /etc/passwd 파일에서 계정 앞에 #을 삽입하여도 주석처리가 되지 않으므로 조치 시에는 반드시 계정을 삭제하여야 한다\n\n[AIX]\n- 서버에 등록된 불필요한 사용자 계정을 제거한다\n    # rmuser [사용자명]",
      "measureDetailOrigin": "#---------------------------------------------------------------------------------------------- \n# [전체 적용 옵션] 불필요한 계정 진단 여부 설정\ncheck_unnecessary_account=1\n#---------------------------------------------------------------------------------------------- \n# OS별 불필요한 계정 목록 입력\n# glob 방식 옵션 (대소문자 구분 안함)\n# *      : 매칭되는 모든 문자를 찾음                  ex) ABCtest, 123Test\n# *test : 문자열 뒤에 test 존재시\n# ?      : 매칭되는 임의의 문자 1개를 찾음\n# test? : test 뒤의 문자 하나가 있는 경우           ex) test1, testr, test_\naix_check_unnecessary_account=<<EOT \nlp\nuucp\nnuucp\nEOT \n#---------------------------------------------------------------------------------------------- \nhpux_check_unnecessary_account=<<EOT \nlp\nuucp\nnuucp\nEOT \n#---------------------------------------------------------------------------------------------- \nlinux_check_unnecessary_account=<<EOT \nlp\nuucp\nnuucp\nEOT \n#---------------------------------------------------------------------------------------------- \nsolaris_check_unnecessary_account=<<EOT \nlp\nuucp\nnuucp\nEOT\n#----------------------------------------------------------------------------------------------\n# [전체 적용 옵션] 진단 제외 Unix OS 한 줄에 하나씩 입력 ( OS 별 옵션은 <OTHERS>옵션보다 우선순위가 높음)\n# 입력 OS 목록 : [aix, linux, hpux, solaris <OTHERS>]\n# 제외 OS 처리 : [ 0-양호, 1-N/A, 2-취약, 3-수동, 4-대체, 5-예외, 9-일반진단 ]\n# ex) aix^1, <OTHERS>^3 (aix에서는 N/A, 나머지 OS는 수동처리, 미입력 일반진단)\nexclude_check_os=<<EOT\nEOT\n#----------------------------------------------------------------------------------------------\n# [전체 적용 옵션] 서비스 실행여부 진단 여부 설정\ncheck_service=[Uncheck]\n#----------------------------------------------------------------------------------------------\n# [전체 적용 옵션] 설정파일 내용 진단 여부 설정\ncheck_conffile_contents=[Uncheck]\n############################################################\n# 항목에 대한 특별한 처리 옵션\n############################################################\n# 해당 항목 진단 여부 (0: 수동, 1:진단)\nenable=1\n#----------------------------------------------------------------------------------------------\n# not_applicable_type 값은 아래와 같이 적용되며 결과는 '예외'로 처리, 현황은 not_applicable_message 문구 출력됨\n# 0 : 예외 처리 미사용\n# 1 : 전체 서버를 예외 처리함\n# 2 : 전체 서버 중 not_applicable_target 에 지정된 서버를 예외 처리함\n# 3 : 전체 서버 중 not_applicable_target 에 지정되지 않은 서버를 예외 처리함\nnot_applicable_type=0\n#----------------------------------------------------------------------------------------------\n# 예외 처리 시 현황에 출력할 문구, not_applicable_type 값이 0 이면 무시됨\nnot_applicable_message=\n#----------------------------------------------------------------------------------------------\n# 예외 처리 적용 대상 자산번호를 한줄에 하나씩\nnot_applicable_target=<<EOT\nEOT\n#----------------------------------------------------------------------------------------------\n# alternate_type 값은 아래와 같이 적용되며 결과는 '대체'로 처리, 현황은 alternate_message 문구 출력됨\n# 0 : 대체 처리 미사용\n# 1 : 전체 서버를 대체 처리함\n# 2 : 전체 서버 중 alternate_target 에 지정된 서버를 대체 처리함\n# 3 : 전체 서버 중 alternate_target 에 지정되지 않은 서버를 대체 처리함\nalternate_type=0\n#----------------------------------------------------------------------------------------------\n# 대체 처리 시 현황에 출력할 문구, alternate_type 값이 0 이면 무시됨\nalternate_message=<<EOT\nEOT\n#----------------------------------------------------------------------------------------------\n# 대체 처리 적용 대상 자산번호를 한줄에 하나씩\nalternate_target=<<EOT\nEOT"
    }
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> `criteria`/`analysisInfo`/`measure`/`measureDetailOrigin` 전체 원문은 사용자가 제공한 캡처 텍스트로 확정 반영함(요청/응답 예시 JSON 전체 그대로). 요청 파라미터(DBM-001)와 응답 데이터(U-103)가 다른 캡처 불일치는 위에 명시함.

**응답시간(초) 샘플**: 0.01

---

### 4.6 규정항목 목록 조회 — `POST /ivms/api/guidelineCdList`

**입력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | Hierarchy | 타입 | 필수 | 샘플 |
|---|---|---|---|---|---|---|
| Body | resultId | 진단결과 ID | 1 | Array[string] | Y | RESULT_00003789 |
| | guidelineCd | 항목코드 | | string | N | APA-202 |

```json
{ "resultId": "RESULT_00003789", "guidelineCd": "APA-202" }
```

**출력 데이터 (Body)**

| 데이터셋명 | 영문명 | 한글명 | Hierarchy | 타입 | 필수 | 샘플 |
|---|---|---|---|---|---|---|
| result | result | | 1 | object | Y | |
| result.guidelineList | guidelineList | 규정 항목 리스트 | 2 | object | Y | |
| guidelineList.guidelineCd | guidelineCd | 항목코드 | 3 | string | Y | APA-202 |
| guidelineList.category | category | 분류 | 3 | string | Y | 계정관리. 자산 진단 항목 분류명 (보안관리, 패치관리, 사용자인증, 접근권한관리, 시스템보안설정 등) |
| guidelineList.subjectType | subjectType | 자산분류 | 3 | string | Y | DB |
| guidelineList.severity | severity | 취약도 | 3 | string | Y | 4 |
| guidelineList.subjectSubType | subjectSubType | 점검대상 | 3 | string | Y | PostgreSQL |
| guidelineList.guidelineNm | guidelineNm | 항목명 | 3 | string | Y | 불필요한 계정 제거 |
| guidelineList.criteria | criteria | 진단기준 | 3 | string | Y | |
| guidelineList.analysisInfo | analysisInfo | 현황 | 3 | string | Y | |
| guidelineList.measure | measure | 조치방법 | 3 | string | Y | |
| guidelineList.measureDetailOrigin | measureDetailOrigin | 세부설정 | 3 | string | Y | |
| _server_message_ | _server_message_ | 결과 정보 | 1 | object | Y | |
| _server_message_.text | text | 결과 내용 | 2 | string | N | |
| _server_message_.type | type | 결과 코드 | 2 | string | Y | 200 성공 등 |

```json
{
  "result": {
    "guidelineList": [
      {
        "guidelineCd": "POS-101",
        "category": "계정관리",
        "subjectType": "DB",
        "severity": "4",
        "subjectSubType": "PostgreSQL",
        "guidelineNm": "불필요한 계정 제거",
        "criteria": "【진단기준】\n----------------------------------------------------------------------------------------------\n◆ 양호 : 계정 정보를 확인하여 불필요한 계정이 없는 경우 \n◆ 취약 : 인가되지 않은 계정, 퇴직자 계정, 테스트 계정 등 불필요한 계정이 존재하는 경우\n\n【상세설명】\n----------------------------------------------------------------------------------------------\n- DBMS에 존재하는 계정 중 DB 관리나 운용에 사용하지 않는 불필요한 계정이 존재하는지 점검\n- 불필요한 계정 존재 유무를 점검하여 불필요한 계정 정보(패스워드)의 유출시 발생할 수 있는 비인가자의 DB 접근에 대비되어 있는지 확인하기 위함\n- DB 관리나 운용에 사용하지 않는 불필요한 계정이 존재할 경우 비인가자가 불필요한 계정을 이용하여 DB에 접근하여 데이터를 열람, 삭제, 수정할 위험이 존재함",
        "analysisInfo": "",
        "measure": "▶ 기본 계정 외 계정의 용도를 파악 후 불필요한 계정은 삭제한다\n\n【점검방법】 \n----------------------------------------------------------------------------------------------\n[PostgreSQL]\n- 기본 계정을 제외하고 로그인 가능한 계정 중 사용하지 않은 불필요한 계정을 파악한다\n    SELECT rolname, rolsuper FROM PG_ROLES WHERE rolcanlogin = 'TRUE' AND rolname NOT IN ('postgres','enterprisedb');\n\n【조치방법】\n----------------------------------------------------------------------------------------------\n[PostgreSQL]\n- 불필요한 계정을 삭제한다\n    DROP USER [계정명];",
        "measureDetailOrigin": "#----------------------------------------------------------------------------------------------\n# 불필요한 계정목록(해당 계정이 존재하는경우 취약)\nunnecessary_user=<<EOT\nEOT\n#----------------------------------------------------------------------------------------------\n# 사용자 계정 개수 제한\naccount_limit=3\nenable=1"
      },
      {
        "guidelineCd": "POS-102",
        "category": "계정관리",
        "subjectType": "DB",
        "severity": "4",
        "subjectSubType": "PostgreSQL",
        "guidelineNm": "기본 계정의 패스워드 변경",
        "criteria": "【진단기준】\n----------------------------------------------------------------------------------------------\n◆ 양호 : 기본 계정의 패스워드를 변경하여 사용하는 경우\n◆ 취약 : 기본 계정의 패스워드를 변경하여 사용하지 않는 경우\n\n【상세설명】\n----------------------------------------------------------------------------------------------\n- PostgreSQL의 기본 계정의 패스워드는 postgres 로 아이디와 동일하여 패스워드를 변경하지 않고 사용하는 경우 악의적인 공격자가 데이터베이스에 쉽게 접근할 수 있다.",
        "analysisInfo": "",
        "measure": "▶ 기본 계정 및 패스워드 변경 확인\n\n【점검방법】 \n----------------------------------------------------------------------------------------------\n[PostgreSQL]\n- 기본 패스워드로 접속이 가능한지 확인\n    # psql -U postgres -h 127.0.0.1 -W\n\n【조치방법】\n----------------------------------------------------------------------------------------------\n[PostgreSQL]\n- postgres 계정 패스워드 변경\n    SQL> ALTER USER postgres WITH ENCRYPTED PASSWORD [변경할 패스워드];",
        "measureDetailOrigin": "############################################################\n# 항목에 대한 특별한 처리 옵션\n############################################################\nenable=1"
      },
      {
        "guidelineCd": "POS-201",
        "category": "권한관리",
        "subjectType": "DB",
        "severity": "4",
        "subjectSubType": "PostgreSQL",
        "guidelineNm": "DBA 권한 제한",
        "criteria": "【진단기준】\n---------------------------------------------------------------------------------------------- \n◆ 양호 : 불필요하게 DBA 권한을 가진 계정이 없는 경우\n◆ 취약 : 불필요하게 DBA 권한을 가진 계정이 존재하는 경우\n\n【상세설명】\n---------------------------------------------------------------------------------------------- \n- DBA 권한이 부여된 사용자는 해당 DB에 대해 모든 권한을 부여 받게 되고 부적절하게 부여된 경우 DB에 심각한 문제를 초래할 수 있다.",
        "analysisInfo": "",
        "measure": "▶ 불필요하게 DBA 권한을 가진 계정이 존재하는 경우 권한을 제거한다.\n\n【점검방법】 \n----------------------------------------------------------------------------------------------\n[PostgreSQL]\n- DBA 권한을 가진 계정의 목록을 확인한다\n    postgres=# SELECT * FROM pg_user WHERE usesuper = TRUE;\n\n【조치방법】\n----------------------------------------------------------------------------------------------\n[PostgreSQL]\n- 불필요하게 DBA 권한을 가진 계정이 존재하는 경우 권한을 제거한다\n    postgres=# ALTER USER [계정명] WITH NOSUPERUSER;",
        "measureDetailOrigin": "#----------------------------------------------------------------------------------------------\n# 진단 예외 계정 목록(해당 계정은 진단에서 예외)\n# solidadmin 계정은 솔루션 운영시 필수 계정이므로 예외처리\nexclude_user=<<EOT\nsolidadmin\nEOT\nenable=1"
      }
    ]
  },
  "_server_message_": { "text": "", "type": "200" }
}
```

> **실제 curl 테스트로 확인**: 응답 `guidelineList`는 실제로 총 6건(POS-101, POS-102, POS-103, POS-201, POS-202, POS-203)이 배열로 반환됨(문서에는 대표 3건만 수록). 필드 순서는 `severity`가 `subjectSubType`보다 먼저 옴. 요청 파라미터의 `guidelineCd`(`APA-202`, Apache 관련)와 실제 응답의 `guidelineCd`(`POS-101` 등, PostgreSQL 관련)가 무관하여, 4.5(`guidelineCdInfo`, IF-API-099504)에서 확인된 것과 동일하게 요청 파라미터의 `guidelineCd`와 무관하게 `resultId` 기준으로 해당 진단결과에 포함된 항목 상세 목록 전체를 반환하는 것으로 확인됨. `criteria`/`measure`/`measureDetailOrigin`은 실제 캡처 원문(구분선 포함)으로 교체함.

---

## 참고 사항 / 미확인 항목

### 이번 세션에서 실제 curl 테스트 캡처로 확정/보강한 항목

- 전체 21개 오퍼레이션 제목에 `IF-API-XXXXXX` 식별자 추가 완료 (cmmCode: 098001~098005, assetInfo: 099401~099404, dashboardInfo: 097901~097908, vulnerabilityInfo: 099501~099504).
- `cmmCode.codeList`(IF-API-098004): 실제 응답의 `cd` 값 6종(DR, DEV, REVIEW, EDU, OPER, INTG) 확인 및 예시 갱신.
- `cmmCode.orgList`(IF-API-098005): `pOrgId=org_000001` 산하 조직 다수(CSEO, CHO, 서비스인프라팀 등) 확인 및 예시 갱신.
- `assetInfo.asstChrgInfo`(IF-API-099403): `orgIdPath`가 3단계 계층(`org_000001 / org_001746 / org_001048`)임을 확인 및 예시/설명 갱신.
- `dashboardInfo.vulStatByAsst`(IF-API-097901): `asstStatusList` 5개 카테고리(전체 관리 자산/정상 연동/수동 등록/점검 미수행/미응답) 실제 수치로 예시 확장.
- `dashboardInfo.vulCodeRank`(IF-API-097903): SRV-133, SRV-125 항목 추가 확인 및 예시 확장.
- `dashboardInfo.asstStateByAgState`(IF-API-097906): `asstStatusList` 4개 카테고리(전체연동자산/정상연동/수동등록/점검완료) 확인 및 예시 확장.
- `dashboardInfo.asstVulState`(IF-API-097907): `asstStatusList` 4개 카테고리(평균 점수/조치 완료/조치 중/총 취약 개수) 확인 및 예시 확장.
- `vulnerabilityInfo.guidelineScRslt`(IF-API-099503): 실제 캡처의 응답 예시는 `guidelineCd: U-101`(관리자 계정의 UID 중복 제거, severity 3) 1건만 확인됨. 이전 버전에 있던 LG-001/LG-PW-001~004/SRV-001·003·004·013·018·020·022 항목은 재확인 결과 실제 캡처 근거가 없어 모두 삭제함.
- `vulnerabilityInfo.guidelineCdInfo`(IF-API-099504): 요청 파라미터는 `guidelineCd=DBM-001`(aresultNo=269953, guidelineIfKey=81438, itemCode=MAR6103_001, agentServerNm=CCE3)이나 응답 본문 실제 데이터는 `guidelineCd: U-103`(계정관리/OS/AIX,HP-UX,Linux,Solaris/불필요한 계정 제거) 건으로, `criteria`/`analysisInfo`(`/etc/passwd` 전체 목록 포함)/`measure`/`measureDetailOrigin`(`exclude_check_os`/`check_service`/`check_conffile_contents`/`enable`/`not_applicable_*`/`alternate_*` 옵션 포함) 전체 원문을 사용자 제공 캡처로 확정 반영함.
- `dashboardInfo.asstVulStateByGdln`(IF-API-097908): 실제 curl 테스트 응답의 `asstStatusList` 46건 전체(U-101~U-701 계열 항목별 severity/totalCnt/vulCnt/actionRate)를 사용자 제공 JSON으로 확정 반영함.
- `vulnerabilityInfo.guidelineCdList`(4.6, ID 미부여): 실제 응답 `guidelineList`는 총 6건(POS-101~POS-203)이며 문서에는 대표 3건만 수록. 요청 파라미터 `guidelineCd`(APA-202)와 실제 응답 데이터(POS 계열)가 무관함을 확인, 4.5와 동일하게 `resultId` 기준으로 해당 진단결과의 항목 상세 목록 전체를 반환하는 동작으로 확정. 필드 순서(`severity`가 `subjectSubType`보다 선행)와 텍스트 필드 원문을 실제 캡처로 갱신함.

### 사용자 확인이 필요한 미해결 항목 (추측으로 채우지 않고 명시적으로 남김)

1. **`vulnerabilityInfo.scanResultCodeMngtDetail`(IF-API-099501) endpoint 확정**: `/scanResultCodeMngtDetail`로 확정(사용자 확인 완료). 서브 리소스 목록표와 다르게 캡처된 `/ivms/api/mngtListDetail` 표기는 오기로 판단, 반영하지 않음.
2. **`vulnerabilityInfo.guidelineCdList`(4.6, ID 미부여)**: 해당 오퍼레이션 전용 `api_test` 캡처는 없음(사용자 확인 완료). 스펙 정의표 원본 내용만 유지하고 IF-API-ID는 부여하지 않음.
3. `assetInfo.mngtListDetail`의 `filter/xorStr` 하위 필드 설명(전체관리자산/정상연동/수동등록/점검미수행/미응답 각각의 종합·양호·취약 필터 조합)은 사용자 제공 텍스트로 정확히 반영함.
4. `assetInfo.asstChrgInfo` 응답 필드 중 `chrgNm`의 필수 여부 표기가 캡처상 불명확하여 "Y?"로 표기함.
5. `assetInfo.mngtListDetail` 응답 필드 중 `resultId`는 캡처에서 하이라이트(주황색) 표시만 되어 있고 별도 설명 텍스트가 없어 원본 그대로 반영함.
