# 플로우 A — 5단계 기능 테스트 가이드 (최종)

**작성일**: 2026-08-19
**대상 파일**: `stage5-mail-test.json`
**선행 단계**: 1 / 2 / 2-2 / 3 / 4단계 ✅ 모두 완료
**참조**: `09-ivms-ixi-integration-requirements-spec.md` 2절, `11-flow-a-node-detail-config.md` 2-9~2-11절

---

## 🔴 실행 전 필독 — 이 단계는 실제로 메일을 발송한다

4단계까지는 결과가 화면에만 표시됐다. **5단계는 승인 시 실제 메일이 나간다.**

현재 수신자는 **테스트용으로 본인 주소 1건에 고정**되어 있다.

```
mail_receiver: ['hhosung@lguplus.co.kr']
mail_title   : [IVMS] 미조치 취약점 조치 안내 (테스트)
```

⚠️ **수신자를 실제 담당자 주소로 바꾸기 전에 반드시 확인할 것:**

1. 현재 데이터는 **담당자 1명 × 자산 30건 중 취약점 3건**만 조회한 축소 표본이다(#1A 하드코딩 포함)
2. IVMS 응답에 **다른 조직 자산이 섞이거나 담당자 정보가 빈 사례**가 확인되어 있다(08번 문서 2.2절)
3. 이 상태로 실제 담당자에게 발송하면 **부정확한 내용으로 실존 인물에게 조치를 요구**하게 된다

→ 수신자 변경은 규모 확대와 데이터 정합성 검증이 끝난 뒤에 할 것.

---

## 1. 구조 (13노드 / 12엣지)

```
Chat Input → #1A(하드코딩) → #1B → #1B-2 → #1C ─┐
                                                  │
   ┌──────────────────────────────────────────────┘
   └→ Agent #2 → Human Approval → Language Model → Send Mail Output
                                   (경유 필수)        (최종 출력)
```

**Chat Output 노드는 제거**했다. 최종 출력이 메일 발송으로 대체되므로 그래프의 sink가 `Send Mail Output` 하나가 된다.

| 노드 | 설정 |
|---|---|
| Agent #2 | `gpt-5.5`, 담당자별 안내 메시지 + 조치가이드 표 생성 |
| Human Approval | `gpt-5.5`, question 고정 문자열 |
| Language Model | `gpt-5.5`, 패스스루 프롬프트 |
| Send Mail Output | 제목/수신자 고정 |

---

## 2. 노드 스키마 확보 경위

원본 워크플로우(`ivms test_prd.json`)에는 Human Approval·Language Model·Send Mail Output 노드가 **존재하지 않았다.** 이들 노드의 내부 스키마(`metadata.name`, `outputs`, 필드별 `type`/`input_types`)를 추측으로 작성하면 임포트가 거부되거나 오작동할 위험이 있어, **캔버스에서 빈 노드를 배치해 export한 파일**(`Agent Test (2).json`)에서 실제 스키마를 가져와 조립했다.

```
Human Approval : name=HumanInTheLoopHumanApproval, category=CONTROL
                 출력 포트 = human_approval (MESSAGE)
                 필드 = input(필수) / question / model / temperature / max_tokens
Language Model : name=LanguageModel, category=MODEL
                 출력 포트 = response (MESSAGE, AI_MESSAGE)
                 필드 = input(필수) / prompt / model / ...
Send Mail Output: name=SendMailOutput, category=OUTPUT
                 필드 = input(필수) / mail_title(필수) / mail_receiver(필수, ARRAY)
```

> 📌 **이 방식은 앞으로도 유효하다.** 카탈로그에 없는 노드를 써야 할 때는 캔버스에서 빈 노드를 배치·export해 스키마를 확보한 뒤 조립하는 것이 가장 안전하다.

---

## 3. 🔴 이번에 발견된 사실 2가지

### 3.1 Send Mail Output 노드가 실재한다 — 문서 전제 뒤집힘

`09-ivms-ixi-integration-requirements-spec.md` 5.2절은 **"외부 발송 노드 부재도 블로커가 아님"** 을 전제로 작성됐고, `04-ixi-enterprise-node-catalog.md`의 20개 노드 목록에도 이 노드는 없다.

그러나 실제 캔버스에는 **`Send Mail Output`(category=OUTPUT)이 존재**한다. 문서 작성 이후 추가된 것으로 보인다.

**영향**: 이 플로우는 이제 "화면에 표시하는 것"이 아니라 **실제로 메일을 발송하는 자동화**가 된다. Human Approval의 실효성도 달라진다 — 4단계까지는 형식적 검증에 가까웠으나, 이제는 오발송을 막는 실질적 안전장치다.

→ 09번 문서 5.2절과 04번 노드 카탈로그 갱신 필요.

### 3.2 Human Approval → Language Model 연결 확인

export의 실제 연결에서 `human_approval` 출력이 Language Model로 이어지는 것이 확인됐다(export에서는 Human Choice를 경유했으나, 타입상 직결도 가능 — `human_approval`은 MESSAGE, LM `input`은 `['MESSAGE','STRING']` 허용).

`REQ-002`의 "Human Approval → Chat Output 직결 불가" 제약은 이번 구성에서 Chat Output을 쓰지 않으므로 해당사항 없다.

> **Human Choice는 요구사항에 없어 제외**했다(09번 문서 2절은 "통합 1회 승인"만 요구). 승인/거절 분기가 필요하면 추후 추가 검토.

---

## 4. Agent #2 프롬프트 설계

11번 문서 2-9절 원문을 기반으로 하되, 현재 데이터 상태에 맞춰 조정했다.

| 항목 | 원문 | 이번 구성 |
|---|---|---|
| 경과일 7일 기준 선별 | timeEndYmd로 필터링 | **timeEndYmd가 입력에 없으면 "-" 표기, 선별 안 함** |
| 표현 수위 | "압박 메시지" | **"안내 메시지"** — 과도한 위협·인신공격 표현 금지 명시 |
| 조회 실패 항목 | 수동 확인 필요 표기 | 동일 유지 |
| 표본 한계 | (없음) | **"미조회 N건" 명시 지시 추가** |

**timeEndYmd/securityScore가 현재 입력에 없다.** 컨텍스트 절약을 위해 #1B-2에서 `asstCode`/`hostNm`만 남기도록 축소했기 때문이다(2-2단계 A+B 축소). 따라서 경과일 기반 선별은 이번 단계에서 동작하지 않으며, 프롬프트가 이를 "-"로 처리하도록 되어 있다.

> 5단계를 실전 구성으로 되돌릴 때는 #1B-2에서 `securityScore`/`timeEndYmd`/`asstNm`을 되살려야 한다. 그만큼 컨텍스트가 늘어나므로 재측정이 필요하다.

**표현 수위를 낮춘 이유**: 실제 메일이 나가는 구조가 됐고, 데이터가 축소 표본이며 정합성 이슈도 확인된 상태다. "압박"보다 "안내"가 적절하다고 판단했다. 운영 시 수위는 요구사항 담당자와 협의할 사항이다.

---

## 5. 테스트 절차

입력은 1~4단계와 동일하게 유지한다.

```
Enterprise SW프로덕트개발팀 자산 점검 준비해줘.
조직ID, 진단템플릿, 자산분류 세 가지 다 확인해야 해.
```

### 실행 흐름

1. #1A~#1C가 4단계와 동일하게 데이터 수집
2. Agent #2가 담당자별 안내 메시지 + 조치가이드 표 생성
3. **Human Approval 화면에서 대기** — 내용 검토 후 승인/거절
4. 승인 시 Language Model이 `[승인 완료]` 붙여 패스스루
5. **Send Mail Output이 `hhosung@lguplus.co.kr`로 발송**

### 성공 기준

- ✅ `context limit exceeded` 미발생
- ✅ Human Approval 화면에 담당자별 섹션이 정상 표시
- ✅ 승인 시 메일 수신 확인
- ✅ 메일 본문에 `[승인 완료]` + 담당자 섹션 + 조치가이드 표 포함
- ✅ **거절 시 메일이 발송되지 않을 것** — 반드시 함께 확인

> 거절 케이스 검증이 중요하다. 거절했는데 메일이 나간다면 승인 단계가 무의미하다.

### 실패 시 대응

| 증상 | 대응 |
|---|---|
| Human Approval 화면이 안 뜸 | `input` 포트에 Agent #2 `response`가 연결됐는지 확인 |
| 거절해도 메일 발송됨 | 🔴 Language Model 패스스루 프롬프트가 거절 분기를 처리 못 함. Human Choice 노드 추가 검토 필요 |
| 메일 미수신 | `mail_receiver` 형식(ARRAY) 확인. 사내 메일 서버 정책·스팸함 확인 |
| `context limit exceeded` | Agent #2가 입력 전체를 그대로 재출력했을 가능성. 4단계까지 통과했다면 Agent #2 구간이 원인 |
| 안내 메시지에 없는 자산이 등장 | 프롬프트의 "지어내지 않는다" 지시 무시. 입력 데이터 재확인 |

---

## 5.5 실행 이력

### 1차 (2026-08-19) — ❌ 메일은 발송됐으나 내용이 잘못됨

메일 본문에 조치가이드가 아니라 **Language Model 노드의 내부 시스템 프롬프트 전문**이 담겨 왔다.

```
[승인 완료]Current Time Information: - Korean Time: 2026-08-19 ...
## Capability Honesty — Do Not Over-Promise ...
User Information: My Role: 당신은 승인된 내용을 그대로 전달하는 패스스루 역할만 수행한다.
- 승인된 경우: "[승인 완료]"를 맨 앞에 붙이고 ...
```

- 플랫폼이 주입한 시스템 텍스트 + **작성한 패스스루 프롬프트 원문**이 그대로 노출
- `[승인 완료]` 접두사만 정상이고, **담당자 안내 메시지·조치가이드 표는 전혀 포함되지 않음**

**원인 — Language Model 노드의 필드 성격을 잘못 이해했다.**

| 노드 | 지시를 넣는 필드 | 데이터 입력 | 동작 |
|---|---|---|---|
| Agent | `system_prompt_template` | `input` | 지시에 따라 `input`을 처리 |
| **Language Model** | `prompt` | `input` | **`prompt` 내용 자체를 처리 대상으로 삼는 것으로 보임** |

즉 Agent와 달리 Language Model의 `prompt`는 "시스템 지시"가 아니라 **LLM에 그대로 던져지는 본문**에 가깝다. 그래서 패스스루 지시문이 처리 대상이 되어 그대로 출력됐고, `input`으로 들어온 승인 내용은 무시됐다.

**대응 (반영 완료)**

**A안 — `prompt` 필드를 비움** (`stage5-mail-test.json`)
이 노드는 REQ-002 제약을 우회하는 **경유용**이라 가공이 불필요하다. 11번 문서 2-11절도 "패스스루"로만 규정한다. `prompt`를 비우면 `input`이 그대로 전달될 것으로 기대된다.

> `prompt` 안에서 `input`을 참조하는 방법(예: `{input}`)은 시도하지 않았다 — **중괄호는 템플릿 변수로 해석되어 실행이 차단**된 전례가 있다(2-2단계, 가이드 1.2-1절).

**B안 — Language Model 제거, 직결** (`stage5b-direct-test.json`)
A안이 실패할 경우를 대비해 함께 준비했다.

```
Human Approval --human_approval--> Send Mail Output.input
```

REQ-002의 제약은 *Chat Output* 직결 불가이며, 여기서는 Send Mail Output을 쓰므로 해당하지 않을 수 있다. 다만 타입 정합성이 미확인이다 — `human_approval` 출력은 `MESSAGE`, `SendMailOutput.input`은 `['DATA','AI_MESSAGE']`를 허용하므로 **거부될 가능성이 있다.** 실패하면 그 자체가 REQ-002 제약의 범위를 확인해주는 결과가 된다.

**실행 순서**: A안 먼저 → 실패 시 B안.

### 2차 (A안: `prompt` 비움) — ❌ 실패

```
요청하신 작업 지시가 포함되어 있지 않습니다.
자산 점검 안내문을 발송하려면 "승인"이라고 말씀해 주세요.
```

시스템 프롬프트 유출은 사라졌으나(=`prompt` 비운 효과), **LLM이 "수행할 지시가 없다"며 되물었다.**

다만 "자산 점검 안내문을 발송하려면"이라는 문구는 **`input`의 내용을 인지하고 있다는 증거**다. 데이터는 도달했으나 처리 지시가 없었을 뿐이다.

**→ Language Model 노드의 `prompt` 필드 성격이 확정됐다:**

| `prompt` 상태 | 결과 |
|---|---|
| 지시문 작성 | 지시문 자체가 처리 대상이 되어 그대로 출력 |
| 비움 | 지시가 없어 LLM이 되물음 |

즉 이 노드는 `input`을 자동 처리하지 않는다. `prompt`에서 `input`을 **명시적으로 참조**해야 하나(중괄호 변수 추정), 중괄호는 실행 차단 전례가 있어 시도하지 않았다.

### 3차 (B안: Human Approval → Send Mail 직결) — ❌ 타입 불일치로 차단

```
소스 출력 타입 [MESSAGE]은(는) 대상 필드 입력 타입 [DATA, AI_MESSAGE]과(와)
호환되지 않습니다. 컴포넌트에 타입에 맞춰 다시 연결해주세요.
```

가이드에 예상해둔 그대로 **`human_approval`(MESSAGE) → `SendMailOutput.input`(DATA/AI_MESSAGE)** 이 거부됐다.

**→ 확정된 사실**: `Send Mail Output`은 `AI_MESSAGE`를 요구하므로 **LLM 계열 노드 경유가 필수**다. REQ-002의 "Human Approval 직결 불가" 제약이 Chat Output뿐 아니라 **Send Mail Output에도 적용**된다.

### C안 — 경유 노드를 Agent로 교체 (`stage5c-relay-test.json`)

Language Model의 `prompt` 동작이 불투명한 반면, **Agent는 `system_prompt_template`(지시) + `input`(데이터) 구조가 이 프로젝트에서 이미 5회 검증**됐다(#1A~#1C, #2). `04-ixi-enterprise-node-catalog.md` 151행도 경유 노드로 **"Agent 또는 Language Model"** 을 명시하므로 Language Model을 고집할 이유가 없다.

**타입 정합성 사전 검증 완료** — B안이 걸린 그 지점을 포함해 전 엣지(12개)를 프로그램으로 검사했다.

| 연결 | 출력 타입 | 입력 허용 | 판정 |
|---|---|---|---|
| Human Approval → Agent(중계) | `MESSAGE` | `['MESSAGE']` | ✅ |
| Agent(중계) → Send Mail Output | `MESSAGE`, **`AI_MESSAGE`** | `['DATA','AI_MESSAGE']` | ✅ |

중계 Agent 설정:
- `temperature: 0` — 원문을 그대로 옮기는 역할이므로 창작 여지를 제거
- 프롬프트에 **"이 지시문 자체를 출력하지 않는다"** 를 명시(1차 실패 재발 방지)
- 승인/거절 분기 지시 포함

> ⚠️ **거절 케이스 미검증**: 1차 실행에서 승인 경로만 확인했다. `prompt`를 비우면 "거절 시 원본을 출력하지 않는다"는 지시도 함께 사라지므로, **거절 시 무엇이 발송되는지(혹은 발송되지 않는지) 반드시 확인**해야 한다. 거절인데 메일이 나가면 승인 단계가 무의미하다.

---

### 4차~7차 — 개행 소실 추적, 원인 확정

| 차수 | 구성 | 결과 |
|---|---|---|
| 4차 (D안) | LM `prompt` 명령형 재작성 | ✅ **메일 발송 성공**, 내용 정상. 단 **전체가 한 줄로 병합** |
| 5차 (E안) | 마크다운 표 제거, 평문 블록 레이아웃 | 구조는 지시대로 생성됐으나 여전히 한 줄 |
| 6차 (F안) | HTML `<br>`/`<hr>`/`<b>` 태그 사용 | **태그가 문자 그대로 노출** → 본문이 평문임이 확정. HTML 가설 기각 |
| 7차 (G안) | **Agent #2 → Chat Output 진단 분기 추가** | 🔑 **Chat Output은 개행 완벽 정상** — Agent #2는 `\n`을 정상 출력 중임이 확인됨 |

**7차가 결정적이었다.** 같은 Agent 출력을 두 경로로 분기해 비교하니 원인 구간이 좁혀졌다.

```
Agent #2 ─┬→ Chat Output                    ✅ 개행 정상
          └→ LM → Send Mail Output          ❌ 한 줄 병합
```

### 8차~9차 — Language Model 확정

| 차수 | 구성 | 결과 |
|---|---|---|
| 8차 (H안) | LM `prompt`에 여러 줄 출력 예시 삽입 | ❌ **"승인할 입력 본문이 없습니다"** — LM이 입력 자체를 인식 못 함 |
| 9차 (I안) | **Human Approval 제거**, Agent #2 → LM → Send Mail | ❌ 여전히 한 줄 병합 |

9차로 **Human Approval은 무관**함이 확인됐고, **Language Model이 개행 소실의 원인**으로 확정됐다.

8차 결과는 LM 노드의 성격을 드러낸다 — `prompt`에 긴 예시를 넣자 **모델이 그 예시를 입력으로 착각**하고 실제 `input`을 인식하지 못했다. `prompt`와 `input`이 하나로 합쳐져 전달되는 것으로 보이며, 이 노드는 입력을 안정적으로 가공하는 용도로 설계되지 않았다.

---

## 5.6 🔴 최종 결론 — 메일 발송 제외, Chat Output으로 전환

### 확정된 플랫폼 제약

**① Language Model 노드는 입력의 개행을 보존하지 못한다** → `REQ-019` 등록

프롬프트로 해결 불가함이 5회 시도로 확인됐다(명시 지시 / 예시 삽입 / 비움 / HTML 태그 / `temperature: 0`).

**② 이 제약은 회피할 수 없다** — 타입 시스템이 LM 경유를 강제한다

| 노드 | `input` 허용 타입 |
|---|---|
| `Chat Output` | `['AI_MESSAGE']` |
| `Send Mail Output` | `['DATA', 'AI_MESSAGE']` |

| 노드 | 실제 출력 타입 |
|---|---|
| `Human Approval` | `MESSAGE` → 거부됨 |
| `Agent` | `MESSAGE`로 해석 → **거부됨**(3차 실측) |
| `Language Model` | **`AI_MESSAGE`** → 유일하게 허용 |

즉 **출력 노드 앞에는 반드시 Language Model이 와야 하고, 거치면 서식이 무너진다.**

> ⚠️ **JSON의 `output_types` 선언을 신뢰하지 말 것.** Agent와 Language Model은 JSON상 `output_types`가 `["MESSAGE","AI_MESSAGE"]`로 **동일하게 선언**되어 있으나, 캔버스는 노드 타입별로 런타임에 실제 타입을 결정한다. 이 때문에 C안 조립 시 JSON 기준 사전 검증이 "타입 불일치 0건"으로 통과했음에도 실제로는 거부됐다. **타입 호환성은 JSON이 아니라 실제 실행으로만 확인할 수 있다.**

**③ Send Mail Output은 평문만 지원** → `REQ-020` 등록

### 최종 구성

메일 발송을 **플로우에서 제외**하고 Chat Output으로 전환했다. 두 가지 버전을 제공한다.

| 파일 | 구조 | 승인 | 개행 |
|---|---|---|---|
| `stage5-final-chatout.json` | Agent#2 → Human Approval → LM → Chat Output | ✅ | ⚠️ 소실 가능(LM 경유) |
| `stage5-final-noapproval.json` | Agent#2 → Chat Output | ❌ | ✅ **보장**(7차 실증) |

**승인과 개행 보존을 동시에 얻을 수 없다.** Chat Output도 `AI_MESSAGE`만 받으므로, 승인 단계를 유지하려면 LM 경유가 필수이고 그 순간 서식이 위험해진다. 이것이 `REQ-002`가 요구하는 개선의 실질적 이유다.

> 실제 발송이 없어진 시점에서 승인 단계의 실효성은 낮아졌다. 가독성이 우선이면 `noapproval` 버전을 사용해도 무방하다.

> 📌 **중간 시도 파일은 정리됨(2026-08-20)**: 원인 규명 과정에서 만든 9개 파일(`stage5-mail-test`, `stage5b~5i`)은 삭제했다. 각 시도의 구성·결과·판정 근거는 위 5.5절 실행 이력에 전부 기록되어 있으므로 재현이 필요하면 그 내용을 참고할 것. 저장소에는 최종 2개만 남긴다.

---

## 6. 남은 작업 (5단계 성공 이후)

| 항목 | 내용 |
|---|---|
| **수신자 실주소 전환** | 데이터 정합성 검증 완료 후에만. 현재는 테스트 주소 고정 |
| ~~**#1A 하드코딩 되돌리기**~~ | 🔴 **철회 (2026-08-21)** — 4차 실패에서 `orgList` 재귀만으로 1,017,179 토큰을 소진했다. 되돌릴 것이 아니라 **별도 워크플로우(W0-1)로 분리**하고 결과를 상수로 관리하는 것이 정식 설계다(`12-flow-a-restructure-plan.md` 6.2절) |
| **필드 복원** | #1B-2에서 `securityScore`/`timeEndYmd`/`asstNm` 되살리기 → 경과일 기반 선별 활성화 |
| **규모 확대** | 담당자 1명 → 전체, 취약점 3건 → 전량. ~~11번 문서 "방법 3"(외부 배치 스크립트) 검토~~ → **기각.** 캔버스 컴포넌트 한정 제약에 따라 **처리 범위를 `mgmtOrgId` 하위 조직 단위로 축소**하는 방식으로 해결한다(`12-flow-a-restructure-plan.md` 7.2절) |
| ⚠️ **담당자 축 검증 제약** | 개발기는 `chrgId` 채움률 **0%**(1,394건 전 샘플)로 담당자 기반 검증이 불가능하다. 운영기 접근 가능한 망에서 수행할 것(12번 문서 4-1.4절) |
| **문서 갱신** | 09번 문서 5.2절(발송 노드 부재 전제), 04번 노드 카탈로그(Send Mail Output 누락) |
| **승인 타임아웃** | REQ-017 — 승인자 장기 미응답 시 무한 대기. 운영 전 확인 필요 |
