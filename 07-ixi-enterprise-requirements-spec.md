# ixi-enterprise 추가 개발 요구사항 명세서

**작성일**: 2026-06-02  
**작성 목적**: ixi-enterprise로 구성된 워크플로우를 n8n으로 대체 구현하는 과정에서 확인된 제약사항과 구조적 한계를 바탕으로, ixi-enterprise 개발팀에 추가 개발을 요청하기 위한 요구사항을 정의한다.  
**참조 문서**: `03-n8n-implementation.md` — ixi 제약 & n8n 대체 종합 비교, 구조적 한계 분석  
**개정**: 2026-08-20 — IVMS 플로우 A 구현 중 실증된 제약 2건(REQ-019/020) 추가. 근거: `ixi-enterprise/stage5-test-guide.md`, `ixi-enterprise/docs/ivms-flow-a-build-lessons.md` 5.7절  
**목표**: n8n 수준의 플로우 개발 생산성 및 운영 안정성 확보

---

## 요구사항 전체 목록

| ID | 분류 | 요구사항 요약 | 우선순위 |
|----|------|------------|---------|
| REQ-001 | 포트 연결 | Guardrail 노드 Input에 Chat Input 직접 연결 허용 | 🔴 High |
| REQ-002 | 포트 연결 | Human Approval 출력 → Chat Output 직접 연결 허용 | 🔴 High |
| REQ-003 | 포트 연결 | AI Router / Human Choice else 포트 → Chat Output 직접 연결 허용 | 🟡 Medium |
| REQ-004 | 포트 연결 | Tool 노드에 일반 모드 / Tool 모드 토글 추가 | 🟡 Medium |
| REQ-005 | 포트 연결 | JSON Output ↔ Chat Output 상호 배타 제약 해제 | 🟡 Medium |
| REQ-006 | 포트 연결 | Structured Output → Document Formatter 연결 시 UI 타입 불일치 경고/차단 | 🟡 Medium |
| REQ-007 | 트리거 | Schedule Trigger(Cron) 및 Webhook Trigger 노드 추가 | 🔴 High |
| REQ-008 | 플로우 구조 | Sub-flow(플로우 호출) 노드 추가 | 🔴 High |
| REQ-009 | 디버깅 | 노드 실행 후 Input/Output 데이터 확인 패널 추가 | 🔴 High |
| REQ-010 | 디버깅 | 플로우 실행 로그(Execution Log) 화면 추가 | 🔴 High |
| REQ-011 | 디버깅 | 단일 노드 독립 실행(Test Step) 기능 추가 | 🔴 High |
| REQ-012 | 디버깅 | 노드 출력 고정(Pin Data) 기능 추가 | 🟡 Medium |
| REQ-013 | 예외처리 | 노드별 재시도(Retry) 설정 기능 추가 | 🔴 High |
| REQ-014 | 예외처리 | 노드별 타임아웃(Timeout) 설정 기능 추가 | 🔴 High |
| REQ-015 | 예외처리 | 노드 실패 시 폴백 경로 설정(On Error 분기) 기능 추가 | 🔴 High |
| REQ-016 | 예외처리 | 전역 Error Workflow(에러 발생 시 알림) 연결 기능 추가 | 🟡 Medium |
| REQ-017 | 예외처리 | Human Approval 승인 대기 타임아웃 설정 기능 추가 | 🟡 Medium |
| REQ-018 | 문서화 | 노드 간 Input/Output 데이터 스키마 공식 문서 제공 | 🟡 Medium |
| REQ-019 | 데이터 전달 | Language Model 노드의 입력 개행(줄바꿈) 보존 (또는 Passthrough 노드 제공) | 🔴 High |
| REQ-020 | 데이터 전달 | Send Mail Output 본문의 서식(줄바꿈) 지원 | 🔴 High |

---

## 분류 1 — 포트 연결 제약 개선

### REQ-001. Guardrail 노드 Input에 Chat Input 직접 연결 허용

**현재 문제**

Guardrail 노드(PLL Guardrail, Moderation Guardrail)의 Input 포트는 Agent 또는 Language Model만 연결 가능하다.  
사용자 입력을 Guardrail로 직접 보내는 가장 직관적인 패턴이 불가능하여, 아무 처리도 하지 않는 Language Model 노드를 중간에 삽입해야 한다.

**현재 강제되는 우회 패턴**
```
Chat Input → Language Model (실질 처리 없는 패스스루) → PLL Guardrail
```
불필요한 LLM 호출이 발생해 토큰 비용과 응답 지연이 증가한다.

**요구사항**

- Guardrail 노드의 Input 허용 노드 목록에 `Chat Input` 추가
- 연결 가능 노드: Agent / Language Model / Chat Input / PLL Guardrail / Moderation Guardrail

**기대 효과**

```
Chat Input → PLL Guardrail (직접 연결)
```
패스스루 Language Model 제거 → LLM 호출 1회 감소 → 토큰 절약 + 응답 속도 향상

---

### REQ-002. Human Approval 출력 → Chat Output 직접 연결 허용

**현재 문제**

Human Approval의 출력 포트는 Chat Output에 직접 연결할 수 없다.  
승인/거절 결과를 사용자에게 표시하는 단순한 경우에도 반드시 Agent 또는 Language Model을 경유해야 한다.

**현재 강제되는 우회 패턴**
```
Human Approval → Language Model ("승인되었습니다.") → Chat Output
```
고정 문자열 응답에도 LLM 호출이 강제된다.

**요구사항**

- Human Approval 출력 포트의 허용 연결 노드 목록에 `Chat Output` 추가
- **추가 권장**: Human Approval 노드 자체에 "승인 시 응답 메시지 / 거절 시 응답 메시지" 텍스트 입력 필드 추가

**기대 효과**

승인 결과 전달에 LLM 호출 불필요 → 운영 비용 절감 + 플로우 구조 단순화

---

### REQ-003. AI Router / Human Choice else 포트 → Chat Output 직접 연결 허용

**현재 문제**

AI Router의 `else` 포트와 Human Choice의 `else` 포트(토글 OFF 상태)는 Chat Output에 직접 연결 불가하다.  
분류되지 않은 입력에 "처리할 수 없습니다"라는 단순 안내를 보낼 때도 LLM을 반드시 경유해야 한다.

**현재 강제되는 우회 패턴**
```
AI Router (else) → Language Model ("처리할 수 없는 요청입니다.") → Chat Output
```

**요구사항**

- AI Router `else` 포트의 허용 연결 노드 목록에 `Chat Output` 추가
- Human Choice `else` 포트(토글 OFF)의 허용 연결 노드 목록에 `Chat Output` 추가
- **추가 권장**: else 포트에 "고정 응답 메시지" 텍스트 설정 필드 추가 (LLM 없이 고정 메시지 반환)

**기대 효과**

라우팅 불일치 케이스를 LLM 없이 처리 → 불필요한 토큰 소모 제거

---

### REQ-004. Tool 노드에 일반 모드 / Tool 모드 토글 추가

**현재 문제**

Web Search Tool, Youtube Search Tool, KOSIS Statistics Tool, Simple Calculator Tool의 출력 포트는 Agent의 Tools 포트에만 연결 가능하다.  
Tool 결과를 Language Model에 직접 연결하는 패턴(Tool 호출 후 LLM 요약)이 불가능하여, 단순 검색 후 요약 용도에도 Agent의 ReAct 루프 오버헤드가 강제된다.

**요구사항**

- Web Search Tool / Youtube Search Tool / KOSIS Statistics Tool / Simple Calculator Tool 노드에 **Tool Mode 토글** 추가
  - **Tool Mode ON**: 기존 동작 유지 (Agent Tools 포트에 연결)
  - **Tool Mode OFF**: 일반 데이터 출력 포트로 전환 (Language Model / AI Router 등에 직접 연결 가능)
- API Request 노드가 이미 이 토글을 지원하는 방식을 동일하게 적용

**기대 효과**

```
[Web Search Tool (일반 모드)] → [Language Model: 검색 결과 요약]
```
Agent ReAct 루프 없이 단순 검색 + LLM 요약 패턴 구현 → 응답 속도 향상

---

### REQ-005. JSON Output ↔ Chat Output 상호 배타 제약 해제

**현재 문제**

동일 플로우에 JSON Output과 Chat Output을 함께 배치하면 Chat Output이 비활성화된다.  
Structured Output으로 JSON을 추출하면서 동시에 사용자에게 자연어 응답을 보내는 패턴이 불가능하다.

**요구사항**

- JSON Output과 Chat Output의 동시 사용 허용
- 두 노드가 동일 플로우 내에서 독립적으로 동작하도록 실행 엔진 수정
- **추가 권장**: Structured Output 노드에 "채팅 응답 포함" 옵션 추가 — JSON 추출과 자연어 요약을 단일 노드에서 처리

**기대 효과**

JSON 추출 결과와 자연어 응답을 하나의 플로우에서 동시 처리 → 별도 플로우 2개로 분리하는 비효율 제거

---

### REQ-006. Structured Output → Document Formatter 연결 시 UI 타입 불일치 경고/차단

**현재 문제**

Structured Output의 Result 포트(주황)와 Document Formatter의 Documents 포트(주황)는 색상이 동일해 UI 상으로 연결이 허용된다.  
그러나 실행 시 `'str' object has no attribute 'page_content'` 런타임 오류가 발생한다.  
Document Formatter는 KMS Retriever의 LangChain Document 객체 배열을 기대하지만, Structured Output은 JSON 문자열을 출력하기 때문이다.

**요구사항**

- 포트 연결 시점에 데이터 타입 호환성 검사 수행
- Structured Output Result → Document Formatter 연결 시도 시:
  - **방안 A**: 연결 차단 + "데이터 타입이 호환되지 않습니다" 경고 표시
  - **방안 B**: 연결 허용 + "런타임 오류가 발생할 수 있습니다" 경고 아이콘 표시
- 포트 색상이 동일하더라도 내부 데이터 타입이 다른 경우 구분 가능하도록 UI 개선

**기대 효과**

UI 연결은 되지만 실행 시 실패하는 "함정" 패턴 제거 → 개발자 혼란 방지 및 디버깅 시간 절감

---

## 분류 2 — 트리거 확장

### REQ-007. Schedule Trigger(Cron) 및 Webhook Trigger 노드 추가

**현재 문제**

현재 ixi-enterprise의 모든 플로우는 Chat Input(사용자 인터랙션)을 필수 시작 노드로 요구한다.  
Template Message 노드는 INPUT 컴포넌트로 인식되지 않아 단독 플로우 시작이 불가능하다.  
이로 인해 정기 보고서 생성, 주기적 데이터 요약, 배치 문서 처리 등 스케줄 기반 자동화를 구현할 수 없다.

**요구사항**

**Schedule Trigger 노드**
- Cron 표현식으로 실행 주기 설정 (예: `0 9 * * 1` = 매주 월요일 오전 9시)
- 단독 플로우 시작 노드로 인식 (INPUT 컴포넌트 조건 충족)
- 실행 이력 및 다음 실행 예정 시각 표시

**Webhook Trigger 노드**
- 지정된 URL로 HTTP POST 수신 시 플로우 시작
- 외부 시스템(Jira, GitHub, Teams 등)에서 이벤트 발생 시 플로우 자동 실행
- 응답 모드 설정: 즉시 응답 / 플로우 완료 후 응답

**기대 효과**

```
[Schedule Trigger: 매주 금 17:00]
     → [KMS Retriever: 주간 문서 검색]
     → [Language Model: 주간 요약 생성]
     → [API Request: 이메일/Teams 발송]
```
사용자 인터랙션 없이 업무 자동화 플로우 구성 가능

---

## 분류 3 — 플로우 구조 확장

### REQ-008. Sub-flow(플로우 호출) 노드 추가

**현재 문제**

ixi는 모든 노드를 하나의 플로우 캔버스 안에서만 구성할 수 있다.  
공통 로직(PII 필터, KMS 검색, 승인 게이트 등)을 재사용 가능한 단위로 분리하는 수단이 없어,  
여러 플로우에서 동일한 노드 패턴을 중복 구성해야 한다.

**요구사항**

**Sub-flow 노드**
- 다른 플로우를 노드처럼 삽입해 실행하는 노드 추가
- 호출 시 입력 데이터를 Sub-flow에 전달하고, Sub-flow 결과를 반환값으로 수신
- Sub-flow는 독립 플로우로 저장 및 관리 가능 (단독 실행/테스트 가능)
- 동기(결과 대기) / 비동기(fire-and-forget) 실행 모드 지원

**Sub-agent 중첩 구조**
- Agent 노드 내부에서 다른 Agent를 Sub-agent로 호출하는 구조 지원
- 오케스트레이터 Agent가 전문화된 Sub-agent에게 역할을 위임하는 패턴 구현 가능

**기대 효과**

```
[통합 플로우]
     │
     ├─ Sub-flow 호출 → [PII 필터 공통 플로우]    ← 여러 플로우에서 재사용
     ├─ Sub-flow 호출 → [KMS 검색 공통 플로우]    ← 단독 테스트 가능
     └─ Sub-flow 호출 → [리포트 발송 공통 플로우]  ← 변경 시 한 곳만 수정
```

- 공통 패턴 모듈화 → 중복 구성 제거
- 역할 단위 분리 → 팀 병렬 개발 가능
- Sub-flow 단독 실행으로 구간별 독립 디버깅 가능

---

## 분류 4 — 디버깅 기능 추가

### REQ-009. 노드 실행 후 Input/Output 데이터 확인 패널 추가

**현재 문제**

플로우 실행 후 각 노드에서 어떤 데이터가 들어오고 나갔는지 확인할 수 없다.  
오류 발생 시 어느 노드가 문제인지, 중간 데이터 형태가 어떤지 파악하는 수단이 전혀 없어  
디버깅이 "전체 플로우 재실행 → 최종 결과 비교"라는 원시적인 방법에 의존한다.

**요구사항**

- 플로우 실행 후 각 노드를 클릭하면 **INPUT / OUTPUT 패널** 표시
- **INPUT 패널**: 해당 노드가 수신한 데이터를 JSON 형태로 표시
- **OUTPUT 패널**: 해당 노드가 출력한 데이터를 JSON 형태로 표시
- 데이터 크기가 클 경우 접기/펼치기 기능 제공
- 노드별 실행 시간(ms) 표시

**표시 대상 노드 (전체 노드 적용 권장)**

| 노드 | Input 표시 내용 | Output 표시 내용 |
|------|--------------|---------------|
| KMS Retriever | 검색 쿼리 | 검색된 문서 목록, 유사도 점수 |
| Document Formatter | Documents 배열 | 포매팅된 텍스트 문자열 |
| Language Model | 입력 메시지, 시스템 프롬프트 | 생성된 텍스트, 사용 토큰 수 |
| Agent | 입력 메시지 | 최종 응답, Tool 호출 이력 |
| AI Router | 입력 텍스트 | 선택된 분기 조건, 판단 근거 |
| PLL Guardrail | 원본 텍스트 | 마스킹된 텍스트, 감지된 PII 항목 |
| Human Approval | 표시된 메시지, 질문 | 승인/거절 결과, 의견 |
| API Request | 요청 URL, 헤더, 바디 | 응답 statusCode, 바디 |

---

### REQ-010. 플로우 실행 로그(Execution Log) 화면 추가

**현재 문제**

플로우 실행 이력이 기록되지 않아 과거 실행에서 어떤 결과가 나왔는지, 어떤 오류가 발생했는지 사후 조회가 불가능하다.  
운영 서비스에서 사용자가 "아까 답변이 이상했어요"라고 할 때 원인을 추적할 방법이 없다.

**요구사항**

- 플로우별 실행 이력 목록 화면 제공
  - 실행 시각, 소요 시간, 성공/실패 여부 표시
- 실행 항목 클릭 시 상세 화면으로 이동
  - 노드 단위 실행 순서, 각 노드의 Input/Output 데이터, 오류 메시지 표시
- 실패한 실행은 오류 발생 노드 하이라이트 표시
- 보관 기간 설정 가능 (예: 최근 100건 / 최근 7일)

**기대 효과**

운영 중 발생한 이상 응답을 실행 로그로 소급 분석 가능 → 운영 이슈 대응 시간 단축

---

### REQ-011. 단일 노드 독립 실행(Test Step) 기능 추가

**현재 문제**

특정 노드의 프롬프트나 파라미터를 수정하고 싶을 때 항상 플로우 전체를 처음부터 실행해야 한다.  
예를 들어 Language Model의 System Prompt를 조정할 때마다 Chat Input → KMS → Document Formatter → Language Model 순서를 전부 실행해야 하므로 이터레이션 속도가 매우 느리다.

**요구사항**

- 노드 우클릭 또는 노드 패널에 **"이 노드만 실행"(Test Step)** 버튼 추가
- 이전 노드의 마지막 실행 Output 데이터를 현재 노드의 Input으로 자동 사용
- 실행 결과를 노드 Output 패널에 즉시 표시
- Pin Data(REQ-012)와 연동하여 고정 데이터로 반복 실행 지원

**기대 효과**

프롬프트 튜닝, 파라미터 조정 시 해당 노드만 반복 실행 → 전체 플로우 실행 대비 이터레이션 속도 대폭 향상

---

### REQ-012. 노드 출력 고정(Pin Data) 기능 추가

**현재 문제**

하위 노드 로직을 반복 테스트할 때 매번 상위 노드(KMS 검색, LLM 호출 등)도 함께 실행된다.  
LLM 호출이 포함된 상위 노드가 반복 실행되면 불필요한 토큰 비용이 발생한다.

**요구사항**

- 노드 Output 패널에 **"출력 고정"(Pin Data)** 버튼 추가
- 고정된 노드는 플로우 실행 시 실제 실행을 건너뛰고 저장된 Output 데이터를 그대로 전달
- 고정 상태 시각적 표시 (노드에 핀 아이콘 표시)
- 고정 해제 버튼으로 원래 실행 모드로 복귀

**기대 효과**

```
[Chat Input] → [KMS Retriever: 📌고정] → [Document Formatter: 📌고정] → [Language Model: 수정 중]
                                                                                ↑
                                                                          이 노드만 반복 실행
```
상위 노드 LLM/KMS 호출 없이 하위 노드만 반복 테스트 → 토큰 절약 + 테스트 속도 향상

---

## 분류 5 — 예외처리 기능 추가

### REQ-013. 노드별 재시도(Retry) 설정 기능 추가

**현재 문제**

API 호출 노드(PLL Guardrail, KMS Retriever, Language Model, API Request 등)가 일시적 네트워크 오류나 서버 과부하로 실패하면 플로우 전체가 즉시 중단된다.  
재시도 없이 중단되므로 일시적 오류에도 사용자는 아무 응답을 받지 못한다.

**요구사항**

- API 호출이 발생하는 노드에 **Retry 설정 패널** 추가
  - 재시도 횟수 설정 (예: 1~5회)
  - 재시도 간격 설정 (예: 1000ms~10000ms)
  - 재시도 조건 설정: 전체 실패 / HTTP 5xx만 / 타임아웃만
- 재시도 중 상태를 로그에 기록

**적용 권장 노드**: PLL Guardrail, Moderation Guardrail, Language Model, Agent, KMS Retriever, API Request

---

### REQ-014. 노드별 타임아웃(Timeout) 설정 기능 추가

**현재 문제**

LLM 호출이나 외부 API 호출이 응답 없이 무한 대기 상태에 빠질 경우 플로우 전체가 멈춘다.  
현재 API Request 노드에는 Connect Timeout / Read Timeout 설정이 있으나, Language Model / Agent / KMS Retriever / Guardrail 노드에는 타임아웃 설정이 없다.

**요구사항**

- Language Model / Agent / KMS Retriever / PLL Guardrail / Moderation Guardrail 노드에 **Timeout(ms) 설정 필드** 추가
- 타임아웃 초과 시 동작 선택:
  - **플로우 중단** (현재 동작 유지)
  - **폴백 경로로 진행** (REQ-015와 연동)
- 권장 기본값: Language Model 60,000ms / KMS Retriever 10,000ms / Guardrail 10,000ms

---

### REQ-015. 노드 실패 시 폴백 경로 설정(On Error 분기) 기능 추가

**현재 문제**

노드 실행이 실패하면 플로우 전체가 즉시 중단되고 사용자에게 아무 응답이 전달되지 않는다.  
실패 시 대체 경로(폴백 메시지 반환, 대체 API 호출 등)를 지정하는 수단이 없다.

**요구사항**

- 각 노드에 **On Error 설정** 추가
  - **Stop Flow** (현재 동작): 플로우 즉시 중단
  - **Continue with Error**: 오류 정보를 Output에 담아 다음 노드로 진행
  - **Go to Error Path**: 별도 지정한 오류 처리 경로(노드)로 분기

- **On Error Path 연결**: 노드에 오류 출력 포트(빨간 파선) 추가 → 오류 발생 시 연결된 노드로 분기
  ```
  [Language Model] ──(정상)──→ [Chat Output]
         │
         └──(오류)──→ [Language Model: "일시적 오류가 발생했습니다. 잠시 후 다시 시도해주세요."]
                                │
                                └──→ [Chat Output]
  ```

**적용 권장 노드**: Language Model, Agent, KMS Retriever, PLL Guardrail, Moderation Guardrail, API Request

---

### REQ-016. 전역 Error Workflow(에러 발생 시 알림) 연결 기능 추가

**현재 문제**

어느 노드에서든 처리 불가 오류가 발생해도 운영자에게 알림이 전달되지 않는다.  
사용자가 직접 문의하기 전까지 오류 발생 사실을 알 수 없어 운영 대응이 늦어진다.

**요구사항**

- 플로우 설정에 **Error Workflow 연결** 옵션 추가
- 플로우 내 처리되지 않은 오류 발생 시 지정된 Error Workflow 자동 실행
- Error Workflow에 전달되는 정보:
  - 플로우명, 오류 발생 노드명, 오류 메시지, 발생 시각, 실행 로그 URL
- Error Workflow 내에서 Teams / 이메일 / Slack 알림 발송 가능

---

### REQ-017. Human Approval 승인 대기 타임아웃 설정 기능 추가

**현재 문제**

Human Approval 노드는 승인자가 응답할 때까지 무한 대기한다.  
승인자가 장기간 미응답 시 플로우가 영구 중단 상태에 빠지며 처리 결과를 사용자에게 전달할 방법이 없다.

**요구사항**

- Human Approval 노드에 **대기 타임아웃 설정 필드** 추가
  - 대기 시간 설정 (예: 1시간 / 24시간 / 7일)
  - 타임아웃 초과 시 동작 선택:
    - **자동 거절**: 거절 경로로 분기
    - **자동 승인**: 승인 경로로 분기
    - **알림 후 대기 연장**: 승인자에게 재알림 발송
- 타임아웃 임박 시 승인자에게 리마인드 알림 발송 옵션 추가

---

## 분류 6 — 문서화

### REQ-018. 노드 간 Input/Output 데이터 스키마 공식 문서 제공

**현재 문제**

각 노드의 Input/Output 포트가 전달하는 데이터의 필드명과 타입이 공식 문서화되어 있지 않다.  
개발자는 노드를 실제 실행해보기 전까지 어떤 데이터 구조가 오가는지 알 수 없어,  
파라미터 표현식 작성이나 하위 노드 로직 개발 시 시행착오를 반복해야 한다.

**현재 확인이 어려운 데이터 스키마 예시**

| 노드 | 포트 | 알 수 없는 정보 |
|------|------|--------------|
| KMS Retriever | Documents (주황) | 문서 객체의 필드명 (`pageContent`? `content`?), 유사도 점수 필드명 |
| Document Formatter | Result (초록) | 출력 문자열 형식, 문서 구분자 패턴 |
| Agent | Response (파란) | 최종 응답 필드명, Tool 호출 이력 포함 여부 |
| PLL Guardrail | Response (파란) | 마스킹 처리 결과 필드명, 원본/마스킹 텍스트 구조 |
| Human Approval | Human Approval (파란) | 승인/거절 결과 필드명, 의견 텍스트 필드명 |

**요구사항**

- 전체 노드의 Input/Output 포트별 데이터 스키마 공식 문서 제공
  - 포트명, 데이터 타입, 필드명, 필드 설명, 예시 값 포함
- ixi-enterprise 개발자 문서(또는 노드 패널 내 "?" 아이콘 클릭) 형태로 접근 가능
- 데이터 스키마 변경 시 버전 이력 관리

---

## 분류 7 — 데이터 전달 무결성 (2026-08-20 추가)

> 아래 2건은 IVMS 연동 플로우 A 5단계 구현 중 **실증으로 확인된 제약**이다. 검증 과정은 `ixi-enterprise/stage5-test-guide.md` 참조.

### REQ-019. Language Model 노드의 입력 개행(줄바꿈) 보존

**현재 문제**

Language Model 노드를 경유하면 **입력 텍스트의 줄바꿈이 모두 소실되어 한 줄로 병합**된다. 내용은 보존되지만 서식이 완전히 무너진다.

**실증 근거 (2026-08-20)**

동일한 Agent 출력을 두 경로로 분기해 비교한 결과:

| 경로 | 개행 |
|---|---|
| `Agent → Chat Output` | ✅ 정상 (담당자 헤더/문단/번호목록 10건 모두 유지) |
| `Agent → Language Model → Send Mail Output` | ❌ 전부 한 줄로 병합 |

변수는 Language Model 노드 하나뿐이었다.

**프롬프트로 해결되지 않음** — 아래 시도가 모두 실패했다.

| 시도 | 결과 |
|---|---|
| `prompt`에 "줄바꿈을 그대로 유지하라" 명시 | 개행 소실 |
| `prompt`에 여러 줄 출력 예시 삽입 | **입력을 인식하지 못함**("승인할 입력 본문이 없습니다") |
| `prompt` 비움 | "작업 지시가 없다"며 되물음 |
| `prompt`에 HTML `<br>` 태그 사용 지시 | 태그가 **문자 그대로** 출력됨(본문이 평문임을 확인) |
| `temperature: 0` | 효과 없음 |

**제약이 회피 불가능한 이유**

`Chat Output`과 `Send Mail Output`의 `input`은 **`AI_MESSAGE` 타입만** 허용한다. 그런데 `Human Approval`의 출력은 `MESSAGE`이고, `Agent`의 출력도 런타임에 `MESSAGE`로 해석되어 거부된다(실측 오류: `소스 출력 타입 [MESSAGE]은(는) 대상 필드 입력 타입 [DATA, AI_MESSAGE]과(와) 호환되지 않습니다`).

즉 **`AI_MESSAGE`를 생성할 수 있는 노드는 Language Model뿐**이므로, 출력 노드 앞에는 반드시 Language Model이 와야 하고, 그 결과 서식이 항상 무너진다.

**요구사항**

- Language Model 노드가 입력을 전달할 때 **개행·들여쓰기·빈 줄을 원본 그대로 보존**할 것
- 또는 **가공 없이 입력을 그대로 통과시키는 "Passthrough" 노드**를 신규 제공할 것 (LLM 호출 없이 타입만 `AI_MESSAGE`로 변환)

**기대 효과**

표·목록·문단이 포함된 구조화된 텍스트를 사용자에게 원형 그대로 전달 가능. REQ-002와 함께 해결되면 LLM 호출 자체가 불필요해져 비용도 절감된다.

---

### REQ-020. Send Mail Output 본문의 서식(줄바꿈) 지원

**현재 문제**

`Send Mail Output`으로 발송된 메일 본문에서 **줄바꿈이 표시되지 않아 전체가 한 문단으로 뭉쳐진다.** 수십 건의 목록을 담은 안내 메일이 사실상 판독 불가능한 형태로 발송된다.

**실증 근거 (2026-08-20)**

| 시도 | 결과 |
|---|---|
| 일반 개행(`\n`) 사용 | 표시되지 않음 |
| 마크다운 표(`|`, `---|---`) | 렌더링되지 않고 기호가 그대로 노출 |
| HTML 태그(`<br>`, `<hr>`, `<b>`) | **태그 문자열이 그대로 노출** — 본문이 평문임이 확인됨 |

**REQ-019와의 관계**

근본 원인은 REQ-019(Language Model 개행 소실)다. Send Mail Output 앞에는 타입 제약상 Language Model이 필수이므로, 개행이 이미 소실된 상태의 텍스트가 전달된다. **REQ-019가 해결되면 이 항목도 함께 해소될 가능성이 높다.**

다만 Send Mail Output 자체가 평문만 지원하는 것으로 보이므로, 별도 확인이 필요하다.

**요구사항**

- 메일 본문의 줄바꿈이 수신 메일에 그대로 반영될 것
- **추가 권장**: HTML 본문 지원 여부를 노드 옵션(`평문 / HTML`)으로 명시적으로 제공할 것

**기대 효과**

목록·표가 포함된 실무용 안내 메일 발송 가능. 현재는 이 제약으로 **메일 발송 기능 자체를 플로우에서 제외**해야 했다.

---

## 우선순위 요약

### 🔴 High — 운영 서비스 수준 구현을 위한 필수 요구사항

| ID | 요구사항 |
|----|---------|
| REQ-001 | Guardrail Input에 Chat Input 직접 연결 허용 |
| REQ-002 | Human Approval → Chat Output 직접 연결 허용 |
| REQ-007 | Schedule Trigger / Webhook Trigger 노드 추가 |
| REQ-008 | Sub-flow(플로우 호출) 노드 추가 |
| REQ-009 | 노드 실행 후 Input/Output 데이터 확인 패널 추가 |
| REQ-010 | 플로우 실행 로그(Execution Log) 추가 |
| REQ-011 | 단일 노드 독립 실행(Test Step) 기능 추가 |
| REQ-013 | 노드별 재시도(Retry) 설정 기능 추가 |
| REQ-014 | 노드별 타임아웃(Timeout) 설정 기능 추가 |
| REQ-015 | 노드 실패 시 폴백 경로(On Error 분기) 기능 추가 |
| REQ-019 | **Language Model 노드의 입력 개행 보존** (또는 Passthrough 노드 신규 제공) |
| REQ-020 | **Send Mail Output 본문의 서식(줄바꿈) 지원** |

### 🟡 Medium — 개발 생산성 및 운영 품질 향상

| ID | 요구사항 |
|----|---------|
| REQ-003 | AI Router / Human Choice else → Chat Output 직접 연결 허용 |
| REQ-004 | Tool 노드에 일반 모드 / Tool 모드 토글 추가 |
| REQ-005 | JSON Output ↔ Chat Output 상호 배타 제약 해제 |
| REQ-006 | Structured Output → Document Formatter 타입 불일치 경고/차단 |
| REQ-012 | 노드 출력 고정(Pin Data) 기능 추가 |
| REQ-016 | 전역 Error Workflow 연결 기능 추가 |
| REQ-017 | Human Approval 승인 대기 타임아웃 설정 추가 |
| REQ-018 | 노드 간 데이터 스키마 공식 문서 제공 |
