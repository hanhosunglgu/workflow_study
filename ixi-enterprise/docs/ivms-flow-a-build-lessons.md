# IVMS 플로우 A 구축 실전 기록 — 시행착오와 확정 사항

**작성일**: 2026-08-18
**대상**: ixi-enterprise 캔버스에서 IVMS 연동 플로우(플로우 A)를 단계적으로 구축하며 확인된 사실
**진척**: 1~4단계 ✅ 전체 검증 완료 / 5단계 ✅ (단 메일 발송은 플랫폼 제약으로 제외)
**관련 문서**: `08-ivms_openapi_spec.md`(API 스펙), `11-flow-a-node-detail-config.md`(노드 상세), `ixi-enterprise/stage*-test-guide.md`(단계별 실행 이력)

> 이 문서는 다음 프로젝트에서 같은 시행착오를 반복하지 않기 위한 **참조용 요약**이다. 상세 실행 이력은 `ixi-enterprise/stage*-test-guide.md`에 있다.

---

## 1. 서버 접속 정보

| 환경 | 주소 | 비고 |
|---|---|---|
| **개발기** | `http://165.244.21.49:8080` | **HTTP, 포트 8080**. API 진단·파라미터 검증에 사용 |
| 운영기 | `https://ivms.lguplus.co.kr` | HTTPS |

엔드포인트 경로는 두 환경 동일: `{BASE_URL}/ivms/api/{operation}`

### 인증 헤더 — 빈 값으로 동작함 (2026-08-18 확인)

`08-ivms_openapi_spec.md` 스펙표는 아래 4종을 **필수(Y)** 로 기재하나, **모두 빈 값으로 두어도 API가 정상 응답값을 반환**한다. 운영기·개발기 모두에서 확인됐다.

```
X-Global-Transaction-ID:   (빈 값)
X-APP-NAME:                (빈 값)
X-AuthorizationTime:       (빈 값)
X-Header-Authorization:    (빈 값)
Content-Type: application/json   ← POST에는 필요
```

- **헤더 키 자체는 삭제하지 말고 빈 값으로 유지**할 것
- 한때 `msgCd: E` 실패 원인으로 "서명 만료"를 의심했으나 **완전히 배제**됐다
- 단, 서버가 검증을 안 하는 것인지 네트워크 레벨에서 이미 인가된 것인지는 구분되지 않았다. **배포 환경이 바뀌면 재확인 필요**

---

## 2. 🔴 가장 중요 — IVMS 스펙표의 필수 Y/N을 신뢰하지 말 것

두 개 API에서 연달아 **스펙표 표기와 실제 서버 동작이 어긋났다.** 이는 개별 버그가 아니라 IVMS API 전반의 특성으로 봐야 한다.

### 2.1 `mngtListDetail`

스펙표상 `asstType`/`templateNo`는 선택(N)이나, **없으면 `msgCd: E`("필수 컬럼 확인 필요")로 거부**된다.

실제 동작하는 조합:
```json
{"userId":"admin","mgmtOrgId":"org_000991","asstType":"SSRCCE",
 "templateNo":"151","diagYear":"2026","page":1,"pageSize":200,
 "filter":{"xorStr":{"logic":"and","filters":[
   {"field":"SECURITY_SCORE","operator":"neq","value":"100"}]}}}
```

- `asstLCtgrId`는 **불필요**(문서에 "출처 미해결"로 남아 있었으나 없어도 동작)
- `rspnMngId`로 담당자 단위 조회 가능

### 2.2 `scanResultCodeMngtDetail` — 개발기 curl로 확정 (2026-08-18)

파라미터를 1개씩 제거하며 검증한 결과:

| 파라미터 | 스펙표 | 실제 |
|---|---|---|
| `resultStatusCdListStr` | N | **필수** — 생략 시 `msgCd: E` |
| `vadaYn` | N | **필수** — 생략 시 `msgCd: E` |
| `atemplateNo` | N | 선택 맞음 |
| `page` / `pageSize` | N | 선택 맞음. **값 크기 제한 없음**(50/100/200 모두 정상) |
| `asstLCtgrId` | N | 선택 맞음(불필요) |

### 2.3 🔴 `asstCode`와 `hostNm`을 함께 보내면 결과가 0건

같은 검증에서 **`hostNm`을 제거하자 8건이 조회**됐고, 함께 보낸 모든 케이스는 0건이었다. 두 값이 **AND 조건**으로 걸려 정확히 대응하지 않으면 교집합이 빈다.

**→ `asstCode`만 전달할 것.** `asstCode`만으로 자산이 특정된다.

실제 동작하는 조합:
```json
{"userId":"admin","asstCode":["SSRCCE3-000747","SSRCCE3-000492"],
 "resultStatusCdListStr":"[\"FAIL\"]","vadaYn":"N",
 "severity":"4","asstType":"SSRCCE","atemplateNo":"151",
 "page":1,"pageSize":50}
```

> `resultStatusCdListStr`은 JSON 배열을 **문자열로 직렬화**한 값(`"[\"FAIL\"]"`)이다.

### 2.4 `guidelineCdInfo` — 예외적으로 스펙표가 정확 (2026-08-18 검증)

세 번째 API에서는 **스펙표와 실제 동작이 일치**했다. 필수(Y) 5개가 실제로도 전부 필수이며, 하나라도 빠지면 `msgCd: E`로 거부된다.

```
GET /ivms/api/guidelineCdInfo
  ?aresultNo=269953&guidelineIfKey=81438
  &guidelineCd=DBM-001&itemCode=MAR6103_001&agentServerNm=CCE3
```

즉 "스펙표는 항상 틀리다"가 아니라 **"신뢰할 수 없으므로 매번 검증해야 한다"** 가 정확한 교훈이다.

### 2.5 🔴 제3의 실패 모드 — "빈 응답"

`guidelineCdInfo`는 5개 키가 하나의 세트로 맞지 않으면 **`msgCd: E`가 아니라 HTTP 200 + 모든 필드가 빈 문자열**을 반환한다.

```json
{"result":{"guidelineCdInfo":{"guidelineCd":"","measure":"", ...}},
 "_server_message_":{"text":"","type":"200"}}
```

에러가 아니므로 **Agent가 성공으로 오인하기 쉽다.** 조치가이드가 통째로 비어 있는데 정상 처리된 것처럼 보인다.

→ 프롬프트에 **"`measure`가 빈 문자열이면 조회 실패로 간주"** 하는 방어 로직을 반드시 넣을 것.

> 참고: `09-ivms-ixi-integration-requirements-spec.md` 5.3절의 "`guidelineCdInfo`가 요청 파라미터와 무관한 응답을 반환한다"는 이슈는 **개발기 검증에서 재현되지 않았다.** `guidelineCd`를 바꾸면 응답도 따라 바뀐다(짝이 맞지 않으면 빈 응답). 서로 다른 두 호출의 캡처가 섞인 착오로 보인다.

### 2.6 응답 필터 신뢰성 문제

서버가 입력 필터를 참고값으로만 쓰는 정황이 여러 곳에서 확인됐다. **클라이언트가 응답을 재검증해야 한다.**

- `severity="4"` 요청에도 응답에 `severity="5"` 항목이 섞임
- `mgmtOrgId`로 필터링해도 다른 조직 자산이나 `mgmtOrgId`가 빈 자산이 반환됨
- `chrgId`/`chrgNm`(담당자)이 빈 자산이 실재함 → "담당자 미배정"으로 별도 처리 필요

---

## 3. 🔴 진단 방법 — 캔버스에서 추측하지 말고 curl로 좁힐 것

**ixi-enterprise 캔버스는 실제 요청 Body를 확인할 방법이 없다**(`07-ixi-enterprise-requirements-spec.md` REQ-009~012: Execution Log·Input/Output 패널 부재). 따라서 API 오류가 나도 어떤 파라미터가 문제인지 캔버스 안에서는 알 수 없다.

이번에 `scanResultCodeMngtDetail` 오류를 캔버스에서 추측으로 접근하다 **두 개의 가설(`pageSize`, `asstLCtgrId`)이 모두 빗나갔고**, 개발기 curl 진단은 **한 번에 5개 가설을 판별**했다.

**→ API 파라미터 문제는 반드시 개발기 curl로 먼저 좁힐 것.**

진단 스크립트: `ixi-enterprise/scanresult-debug.sh` (파라미터 1개씩 제거하며 필수값을 색출하는 패턴 — 다른 API에도 그대로 응용 가능)

```bash
# 핵심 패턴: 기준선 → 1개씩 제거 → 실패한 것이 실제 필수값
call "without vadaYn"  '{...vadaYn 뺀 body...}'
call "without hostNm"  '{...hostNm 뺀 body...}'
```

---

## 4. 컨텍스트 예산 — 최대 난관

### 4.1 예산은 모델에 따라 다르다

| 모델 | 관측된 예산 |
|---|---|
| (구 모델) | 100,000 토큰 |
| `gpt-5.5` | **945,000 토큰** |

모델 상향만으로 예산이 9.45배 늘었다. **다단계 Tool 호출이 필요한 Agent에는 `gpt-5.5`를 쓸 것.**

### 4.2 구조적 한계 — Agent 분할로 해결되지 않는다

`04-ixi-enterprise-node-catalog.md` 기준 ixi-enterprise에는 **Function/Code/Merge/Loop 노드가 없다.** 따라서 API 응답을 Agent 컨텍스트 밖에서 가공·축약할 방법이 없고, **한 Agent 안에서 페이지 반복 호출 응답이 계속 누적**된다.

Agent를 #1A/#1B/#1B-2/#1C로 쪼개도 이 문제는 사라지지 않는다. 분할은 "서로 다른 Tool의 응답을 분리"할 뿐이다.

### 4.3 🔴 파이프라인이 길어지면 앞단 비용이 뒤로 전파된다

가장 값비싼 교훈이다. 축소 대상을 계속 뒷단에서 찾았으나, **실제 병목은 이미 검증을 마쳐 손대지 않던 맨 앞 Agent #1A**였다.

`orgList` 재귀 조회는 1·2단계(파이프라인이 짧을 때)는 통과했지만, #1A → #1B → #1B-2로 길어지자 조직 배열 응답 6회분이 뒤로 계속 전달되며 예산을 소진했다. 이때 #1B-2는 **시작조차 못 했다**.

**→ 컨텍스트 문제 진단 시 Thinking 로그로 "어느 Agent에서 터졌는지"를 먼저 확인할 것.** 뒷단을 아무리 축소해도 앞단이 원인이면 소용없다.

### 4.4 실측 절감 효과

| 조치 | 효과 |
|---|---|
| Body 스키마에 `pageSize` 추가 | **가장 큰 효과.** 스키마에 없으면 프롬프트가 지시해도 요청에 실리지 않아 서버 기본값(추정 10)으로 동작 → 페이지 반복 폭증 |
| #1A 하드코딩(Tool 3개 제거) | Tool 호출 6회 → 2회 |
| 페이지 반복 1회 고정 | 담당자 목록 600건 → 200건 |
| 출력 필드 축소(5개 → 2개) | 레코드당 비용 대폭 감소 |

> **Body 스키마 누락은 조용히 실패한다.** 프롬프트에 "pageSize=200"이라고 써도 스키마에 그 필드가 없으면 전달되지 않는다. 과거 "pageSize를 10→200으로 올렸는데도 재발"한 이력은 값이 애초에 반영되지 않았기 때문일 가능성이 높다.

---

## 5. 프롬프트 작성 규칙 (실패로 확인된 것들)

### 5.1 🔴 중괄호를 쓰지 말 것

Agent의 프롬프트 필드는 **`System Prompt Template`** — 텍스트가 아니라 템플릿이다. `{orgId}` 같은 **단일 식별자 형태의 중괄호를 입력 변수 선언으로 해석**한다.

```
❌ mgmtOrgId={orgId}, asstType={asstType}
   → 실행 전 검증 오류: "'Agent' 노드의 'orgId' 항목이 비어 있습니다"

✅ mgmtOrgId 에는 입력에서 파싱한 orgId 값
```

- 값 참조는 **서술형**으로 표현
- 단, **JSON 구조는 무방**하다: `filter={"xorStr":{...}}`는 정상 동작
- ⚠️ `11-flow-a-node-detail-config.md`의 System Prompt 원문들이 `{값}` 표기를 광범위하게 사용 중 — 그대로 옮기면 오류

### 5.2 사용자 입력 문구가 Tool 호출 범위를 좌우한다

| 입력 | 결과 |
|---|---|
| "조직 ID 확인해줘" | `orgList`만 호출, 후속 API 미호출 |
| "자산 확인해줘" | Tool 3개 모두 호출 |

**System Prompt가 3개 작업을 지시해도, 사용자 메시지가 범위를 좁게 표현하면 그쪽이 우선한다.**

→ 프롬프트에 **"사용자 입력이 일부 작업만 요청하는 것처럼 보여도 전부 수행한다"** 를 명시할 것.

### 5.3 `orgId`에 의존하지 않는 API는 먼저 호출

`assetSsrcceTemplate`/`assetCategory`는 `userId`만 필요하다. 조직 탐색 뒤에 배치하면 **재귀 조회에 휩쓸려 호출되지 않는다.**

→ 의존성 없는 Tool을 **앞에** 배치하고, 조건부 문장("~를 확정했으면 이어서") 대신 **독립 단계**로 분리할 것.

### 5.4 선택 필드는 "첫 번째 항목" 규칙으로 뽑으면 빈 값이 나온다

`assetCategory` 응답의 `asstType`은 선택 필드(N)라 첫 항목이 비어 있을 수 있다.

```
❌ 여러 개면 첫 번째 값을 사용한다
✅ 값이 비어 있지 않은 첫 번째 항목을 사용한다
```

### 5.5 값을 못 얻으면 빈칸 대신 진단 정보를 출력하게 할 것

빈칸이면 "호출 실패"인지 "응답에 값 없음"인지 구분이 안 돼 진단에 한 바퀴를 더 돈다.

→ `"응답에 값 없음"` + 배열 항목 수 등 원인 파악용 정보를 함께 출력하도록 지시.

### 5.6 실패 시 무한 재시도 방지

파라미터를 임의로 바꿔가며 반복 호출하면 컨텍스트만 소진된다.

→ **"1회만 재시도하고, 그래도 실패하면 응답 원문을 그대로 보여주며 중단"** 을 명시.

---

## 5.7 🔴 노드 간 데이터 전달 제약 (5단계에서 실증)

### 5.7.1 타입 시스템이 Language Model 경유를 강제한다

출력 노드(`Chat Output`, `Send Mail Output`)는 **`AI_MESSAGE` 타입만** 받는다. 그런데 이를 생성할 수 있는 노드는 **Language Model뿐**이다.

| 노드 | 실제 출력 타입 |
|---|---|
| `Human Approval` | `MESSAGE` → 출력 노드에 직결 불가 |
| `Agent` | `MESSAGE`로 해석 → **직결 불가** |
| `Language Model` | **`AI_MESSAGE`** → 유일하게 허용 |

실측 오류 메시지:
```
소스 출력 타입 [MESSAGE]은(는) 대상 필드 입력 타입 [DATA, AI_MESSAGE]과(와)
호환되지 않습니다. 컴포넌트에 타입에 맞춰 다시 연결해주세요.
```

> 📌 `04-ixi-enterprise-node-catalog.md` 151행의 "Human Approval → Chat Output 직결 불가, **Agent 또는 Language Model** 경유 필수"에서 **Agent 경유는 실제로 불가능**하다. 문서 정정 필요.

### 5.7.2 ⚠️ JSON의 `output_types` 선언을 신뢰하지 말 것

Agent와 Language Model은 export JSON에서 `output_types`가 **동일하게** 선언되어 있다.

```json
"outputs": [{"name":"response","output_types":["MESSAGE","AI_MESSAGE"]}]
```

그러나 캔버스는 이 값이 아니라 **노드 타입별 런타임 규칙**으로 판정한다. 이 때문에 JSON 기준 사전 검증이 "타입 불일치 0건"으로 통과했음에도 실제 실행에서 거부된 사례가 있다.

**→ 타입 호환성은 JSON 정적 검사로 확인할 수 없다. 실제 실행으로만 검증된다.**

### 5.7.3 Language Model은 입력의 개행을 보존하지 못한다

LM을 경유하면 **줄바꿈이 모두 소실되어 한 줄로 병합**된다. 내용은 보존되지만 서식이 무너진다.

동일 출력을 두 경로로 분기한 비교:

| 경로 | 개행 |
|---|---|
| `Agent → Chat Output` | ✅ 정상 |
| `Agent → Language Model → Send Mail Output` | ❌ 한 줄 병합 |

**프롬프트로 해결되지 않는다** — 5회 시도 전부 실패:

| 시도 | 결과 |
|---|---|
| "줄바꿈을 유지하라" 명시 | 소실 |
| 여러 줄 출력 예시 삽입 | **입력을 인식 못 함**("입력 본문이 없습니다") |
| `prompt` 비움 | "지시가 없다"며 되물음 |
| HTML `<br>` 태그 | 태그가 문자 그대로 노출(본문은 평문) |
| `temperature: 0` | 효과 없음 |

> **LM 노드의 `prompt`와 `input`은 합쳐져 전달되는 것으로 보인다.** `prompt`에 긴 예시를 넣으면 모델이 그것을 입력으로 착각해 실제 `input`을 무시한다. 이 노드는 입력을 안정적으로 가공하는 용도가 아니다.

**영향**: 표·목록·문단이 포함된 텍스트를 사용자에게 원형으로 전달할 수 없다. **메일 발송 기능을 플로우에서 제외**해야 했다.

→ `07-ixi-enterprise-requirements-spec.md` **REQ-019 / REQ-020** 신규 등록(2026-08-20).

### 5.7.4 진단 방법 — 출력을 분기해 구간을 좁힐 것

개행 소실의 원인 구간은 **Chat Output 분기를 추가**해 특정했다.

```
Agent #2 ─┬→ Chat Output          ← 진단용 (개행 정상 확인)
          └→ LM → Send Mail       ← 문제 구간
```

캔버스는 중간 데이터를 볼 수 없으므로(REQ-009~012), **의심 지점 앞뒤에 Chat Output을 붙여 분기 비교**하는 것이 사실상 유일한 격리 수단이다. API 문제에 curl 진단이 유효했던 것과 같은 원리다(3절).

---

## 6. 노드 설정 확정값

### 6.1 API Request Tool 공통

| 항목 | 값 |
|---|---|
| Tool Mode | **ON** (Agent Tools 포트 연결에 필수) |
| Connect Timeout | 1000~3000ms |
| Read Timeout (GET) | 10000ms |
| **Read Timeout (POST)** | **30000ms** — 10000ms에서는 응답 전 타임아웃 발생 |
| **Query Params (POST)** | **반드시 비울 것** — 값이 남으면 URL에 쿼리스트링이 붙어 실패 |

### 6.2 연결 제약

- Chat Output 연결은 **Chat Output 쪽에서 드래그 시작**해야 함
- Human Approval → Chat Output 직결 불가, Language Model 경유 필수
- Agent → Agent 연결(`Response` → `Input`)은 지원됨

---

## 7. 검증된 API 체이닝

`09`/`10`번 문서의 원래 설계(`orgList → asstChrgInfo → mngtListDetail → guidelineCdInfo`)는 **잘못된 가정**이었다. `asstChrgInfo`는 자산 단위 API(`asstId`+`asstVer` 필수)라 조직 기준 담당자 조회에 쓸 수 없다.

**실제 동작하는 체인:**

```
1. orgList                    (GET)  조직명 → orgId
   assetSsrcceTemplate        (GET)  → templateNo
   assetCategory              (GET)  → asstType
2. mngtListDetail             (POST) orgId 기준 자산 목록 + 담당자(chrgId/chrgNm)
3. mngtListDetail + rspnMngId (POST) 담당자별 자산 상세 → asstCode
4. scanResultCodeMngtDetail   (POST) asstCode 기준 취약점 항목
                                     → guidelineIfKey/itemCode/agentServerNm/resultIfKey
5. guidelineCdInfo            (GET)  위 4개 키로 조치가이드(measure)   ← 미검증
```

### 검증에 사용한 확정값 (Enterprise SW프로덕트개발팀)

| 항목 | 값 |
|---|---|
| `orgId` | `org_000991` |
| `templateNo` | `151` |
| `asstType` | `SSRCCE` |
| `orgList` 재귀 시작점 | `pOrgId="org_002205"` (Enterprise 서비스개발Lab) |

> ⚠️ `08-ivms_openapi_spec.md`는 `org_000991`의 상위를 `org_000001`로 기록하고 있으나, **실측 결과 `org_002205`에서 시작해야 탐색된다.** 문서의 조직 계층 기록이 현재 구조와 불일치 — 정정 필요.

---

## 8. 남은 과제

### 8.1 4단계 `guidelineCdInfo` — ✅ API 검증 완료 (2026-08-18)

개발기 curl 검증으로 **API 자체는 정상 동작이 확인**됐다(`ixi-enterprise/guideline-debug.sh`). 프로젝트 시작 이래 처음으로 조치가이드 원문(`measure`)을 확보했다.

```
guidelineCd  : DBM-001
guidelineNm  : 취약하게 설정된 비밀번호 존재
criteria     : 487자   (진단기준)
analysisInfo : 645자   (취약점현황)
measure      : 569자   (조치방법 — 【점검방법】/【조치방법】 + 실제 명령어 포함)
```

- 필수 5개 표기 정확(2.4절)
- "파라미터 무관 응답" 이슈 재현되지 않음
- ⚠️ 빈 응답 실패 모드 주의(2.5절)

**남은 것**: 캔버스에서의 동작 검증(3단계 출력 → #1C가 4개 키를 정확히 넘기는지).

### 8.2 규모 문제 — 현재 구성은 운영 불가

3·4단계 기능 검증을 위해 데이터를 강제 축소한 상태다.

| 항목 | 현재(검증용) | 실제 필요 |
|---|---|---|
| Agent #1A | **하드코딩** | `orgList` 재귀 복원 |
| 담당자 | **1명만** | 전체 |
| 페이지 | **1회 고정** | 전량 |
| 자산 | 담당자당 **30건** | 전량(확인된 것만 80건) |
| 취약점 조회 | **5건** | 전량 |

`11-flow-a-node-detail-config.md`가 제시한 **"방법 3 — 외부 배치 스크립트로 페이지네이션을 캔버스 밖에서 처리"** 가 유일한 근본 해결책으로 보인다. 캔버스에 Function/Loop 노드가 없는 한 이 제약은 유지된다.

### 8.3 5단계 — 구현 완료, 단 메일 발송 제외

원본 워크플로우에 없던 Human Approval·Language Model·**Send Mail Output** 노드를 캔버스 export로 스키마를 확보해 조립했다(5단계 가이드 2절).

**결과**: 안내문 생성·승인·출력까지 동작하나, **메일 발송은 플랫폼 제약으로 제외**했다 — Language Model이 개행을 보존하지 못해 목록이 한 줄로 뭉개진다(5.7절, REQ-019/020).

최종 구성 2종:

| 파일 | 승인 | 개행 |
|---|---|---|
| `stage5-final-chatout.json` | ✅ | ⚠️ LM 경유로 소실 가능 |
| `stage5-final-noapproval.json` | ❌ | ✅ 보장 |

> **Send Mail Output 노드는 실재한다.** `09-ivms-ixi-integration-requirements-spec.md` 5.2절("외부 발송 노드 부재")과 `04-ixi-enterprise-node-catalog.md`(20개 노드 목록)는 이 노드를 반영하지 못한 상태다 — 문서 갱신 필요.

---

## 9. 파일 위치

| 파일 | 내용 |
|---|---|
| `ixi-enterprise/stage1-orgid-test.json` | 1단계 (6노드) |
| `ixi-enterprise/stage2-mngtlist-test.json` | 2단계 (8노드) |
| `ixi-enterprise/stage2_2-precise-test.json` | 2-2단계 (7노드, #1A 하드코딩) |
| `ixi-enterprise/stage3-scanresult-test.json` | 3단계 (9노드) |
| `ixi-enterprise/scanresult-debug.sh` | 개발기 curl 진단 스크립트 |
| `ixi-enterprise/stage1-test-guide.md` | 1단계 실행 이력·교훈 |
| `ixi-enterprise/stage2-test-guide.md` | 2단계 실행 이력 |
| `ixi-enterprise/stage2_2-3-test-guide.md` | 2-2·3단계 실행 이력·진단 결과 |
