# ixi-enterprise 노드 카탈로그

**작성일**: 2026-05-15  
**최종 수정**: 2026-05-18 (전체 노드 포트 검증 완료 — Chat Input / Chat Output / Template Message / Language Model / Agent / AI Router / Structured Output / JSON Output / Simple Calculator Tool / Web Search Tool / Youtube Search Tool / MCP Connection Tool / KOSIS Statistics Tool / API Request / KMS Retriever / Document Formatter / Human Approval / Human Choice / Moderation Guardrail / PLL Guardrail)  
**기준**: 개발 버전 노드 이미지 분석

---

## 노드 전체 목록

| 노드 | 카테고리 | 상태 | 설명 |
|------|----------|------|------|
| Chat Input | I/O | ✅ 확인 | 채팅 입력 컴포넌트 |
| Chat Output | I/O | ✅ 확인 | AI 출력 컴포넌트 |
| **Send Mail Output** | **I/O** | ✅ **확인(2026-08-20 추가)** | **메일 발송 컴포넌트** — `mail_title`(필수), `mail_receiver`(필수, ARRAY), `input`(필수, `['DATA','AI_MESSAGE']`). ⚠️ 본문이 평문이라 줄바꿈이 표시되지 않음(REQ-020) |
| JSON Output | I/O | ✅ 확인 | JSON 출력 컴포넌트 (Structured Output 결과 출력) |
| Template Message | I/O | ✅ 확인 | 템플릿화 된 휴먼 메시지 생성 |
| Language Model | AI/LLM | ✅ 확인 | LLM으로 입력 메시지에 대한 응답 생성 |
| Agent | AI/LLM | ✅ 확인 | 주어진 도구를 사용하여 처리하는 에이전트 |
| AI Router | AI/LLM | ✅ 확인 | LLM이 입력을 보고 적절한 엣지로 라우팅 |
| Structured Output | AI/LLM | ✅ 확인 | 메시지를 구조화된 데이터로 변환 |
| Simple Calculator Tool | Tools | ✅ 확인 | 간단한 계산기 도구 |
| Web Search Tool | Tools | ✅ 확인 | 웹 검색 도구 |
| Youtube Search Tool | Tools | ✅ 확인 | YouTube 검색 도구 |
| MCP Connection Tool | Tools | ✅ 확인 | MCP 서버 연결 도구 |
| KOSIS Statistics Tool | Tools | ✅ 확인 | KOSIS 데이터 관련 도구 |
| API Request | Tools | ✅ 확인 | HTTP API 요청 송수신 |
| KMS Retriever | RAG | ✅ 확인 | KMS 지식에서 검색 후 결과 반환 |
| Document Formatter | RAG | ✅ 확인 | Retriever 결과를 프롬프트에 활용 가능하게 포매팅 |
| Human Approval | Human-in-the-Loop | ✅ 확인 | 다음 작업 전 사용자 승인 요청 |
| Human Choice | Human-in-the-Loop | ✅ 확인 | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
| Moderation Guardrail | Guardrail | ✅ 확인 | 콘텐츠 안전 필터링 (Hate/SelfHarm/Sexual/Violence) |
| PLL Guardrail | Guardrail | ✅ 확인 | 개인정보(PII) 필터링 |

---

## 카테고리별 상세 명세

### I/O 노드

#### Chat Input
- **설명**: 채팅 입력 컴포넌트
- **입력 포트**: 없음 (플로우 시작 노드)
- **출력 포트**: `User Message` → (파란 점선)
- **User Message에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자의 승인을 받음 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | KMS Retriever | 주어진 질문을 KMS 지식에서 검색하여 결과를 가져옴 |
  | Structured Output | 메시지를 구조화된 데이터로 변환 |
- **용도**: 플로우 진입점. 사용자 텍스트 입력 수신
- **검증 일자**: 2026-05-18

#### JSON Output
- **설명**: JSON 출력 컴포넌트
- **입력 포트**: `Input *` ←(주황, 필수)
- **출력 포트**: 없음 (플로우 종료 노드)
- **Input에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | API Request | HTTP API 요청을 보내고 응답을 처리 |
  | KMS Retriever | 주어진 질문을 KMS 지식에서 검색하여 결과를 가져옴 |
  | Structured Output | 메시지를 구조화된 데이터로 변환 |
- **용도**: Structured Output 결과(JSON)를 플로우 출력으로 표시. Chat Output의 JSON 전용 버전
- ⚠️ **상호 배타적 제약**: 플로우에 JSON Output을 추가하면 Chat Output이 비활성화됨. 두 노드는 동시에 사용 불가 — 출력 방식을 하나만 선택해야 함 (2026-05-18 확인)
- **검증 일자**: 2026-05-18

#### Chat Output
- **설명**: AI 출력 컴포넌트
- **입력 포트**: `Input *` ← (필수, 빨간 별표)
- **출력 포트**: 없음 (플로우 종료 노드)
- **Input에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | PLL Guardrail | PLL Guardrail 컴포넌트 |
  | Moderation Guardrail | Moderation Guardrail 컴포넌트 |
- ⚠️ **상호 배타적 제약**: 플로우에 JSON Output을 추가하면 Chat Output이 비활성화됨. 두 노드는 동시에 사용 불가 (2026-05-18 확인)
- **용도**: 플로우 종료점. AI 응답을 사용자에게 표시
- **검증 일자**: 2026-05-18

#### Template Message
- **설명**: 템플릿화 된 휴먼 메시지를 생성합니다
- **입력 (프롬프트 등록)**:
  - `Template *` (필수) — 텍스트 에디터 팝업에서 프롬프트 직접 입력
  - 플레이스홀더: `Enter the input to the agent`
  - **프롬프트 변수** 지원: 중괄호 안에 변수명을 넣어 생성
    - 예: `{variable}`, `{Variable}`, `{variable1}`, `{Variable-123}`
    - 변수명은 영문자 또는 영문자로 시작하는 숫자/기호 조합이어야 함
- **출력 포트**: `User Message` → (파란 점선)
- **User Message에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자의 승인을 받음 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | KMS Retriever | 주어진 질문을 KMS 지식에서 검색하여 결과를 가져옴 |
  | Structured Output | 메시지를 구조화된 데이터로 변환 |
- **용도**: 정해진 형식의 메시지를 LLM에 전달할 때 사용. Chat Input과 달리 플로우 내부에서 고정된 프롬프트를 생성할 때 활용
- ⚠️ **INPUT 컴포넌트 제약**: Template Message는 플로우의 INPUT 컴포넌트로 인식되지 않음. 플로우 시작점으로 단독 사용 시 "단 하나의 INPUT 컴포넌트는 필수입니다. (현재 개수 : 0개)" 오류 발생. Chat Input과 함께 사용하거나 Chat Input으로 대체할 것 (2026-05-18 확인)
- **검증 일자**: 2026-05-18

---

### AI/LLM 노드

#### Language Model
- **설명**: LLM을 사용하여 입력 메시지에 대한 응답 생성
- **내부 파라미터**:
  - `Input *` (필수): 사용자 메시지 또는 컨텍스트
  - `System Prompt Template` (선택): LLM 역할 및 지시문 (팝업 텍스트 에디터)
  - `Model *` (필수): 사용할 LLM 선택 (드롭다운)
    - `azure_openai:gpt-4.1`
    - `azure_openai:gpt-4.1-mini`
    - `azure_openai:gpt-4.1-nano`
    - `azure_openai:gpt-4o`
- **입력 포트**: `Input *` ← (필수)
- **Input에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Chat Input | 채팅 입력 컴포넌트 |
  | Template Message | 템플릿화 된 휴먼 메시지 생성 |
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자의 승인을 받음 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | API Request | HTTP API 요청을 보내고 응답을 처리 |
  | Document Formatter | Retriever 결과를 프롬프트에 활용 가능하게 포매팅 |
  | PLL Guardrail | PII 필터링 컴포넌트 |
  | Moderation Guardrail | 콘텐츠 안전 필터링 컴포넌트 |
- **출력 포트**: `Response` → (파란 점선)
- **Response에 연결 가능한 노드** (실제 UI 검증 완료 — 2026-05-18 재검증):
  | 노드 | 설명 |
  |------|------|
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자의 승인을 받음 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | KMS Retriever | 주어진 질문을 KMS 지식에서 검색하여 결과를 가져옴 |
  | Structured Output | 메시지를 구조화된 데이터로 변환 |
  | PLL Guardrail | PII 필터링 컴포넌트 |
  | Moderation Guardrail | 콘텐츠 안전 필터링 컴포넌트 |
- ⚠️ **Chat Output 연결 방향 주의**: Language Model Response 포트에서 드래그 시 Chat Output이 목록에 없음 (UI 검증 2026-05-18). Chat Output Input 포트에서 드래그 시 Language Model 선택 가능 — Chat Output 쪽에서 연결 시작할 것. Human Approval 출력 → Chat Output 직접 연결은 양방향 모두 불가 — ~~Agent 또는~~ **Language Model 경유 필수**.

> 🔴 **정정(2026-08-20, 실측)**: 위의 "**Agent 또는** Language Model 경유"는 부정확하다. **Agent 경유는 실제로 불가능**하다.
>
> `Chat Output`/`Send Mail Output`의 `input`은 **`AI_MESSAGE` 타입만** 허용하는데, Agent의 `response`는 런타임에 `MESSAGE`로 해석되어 거부된다. 실측 오류:
> ```
> 소스 출력 타입 [MESSAGE]은(는) 대상 필드 입력 타입 [DATA, AI_MESSAGE]과(와)
> 호환되지 않습니다. 컴포넌트에 타입에 맞춰 다시 연결해주세요.
> ```
> **`AI_MESSAGE`를 생성할 수 있는 노드는 Language Model뿐**이므로, 출력 노드 앞 경유 노드는 Language Model로 한정된다.
>
> ⚠️ **주의**: export JSON에서 Agent와 Language Model의 `output_types`는 `["MESSAGE","AI_MESSAGE"]`로 **동일하게 선언**되어 있으나, 캔버스는 이 값이 아니라 노드 타입별 런타임 규칙으로 판정한다. **JSON 정적 검사로는 타입 호환성을 확인할 수 없다.**
>
> 관련: `07-ixi-enterprise-requirements-spec.md` REQ-002 / REQ-019, `ixi-enterprise/docs/ivms-flow-a-build-lessons.md` 5.7절
- **용도**: Tool 없이 단순 LLM 응답이 필요한 경우
- **검증 일자**: 2026-05-18

#### Agent
- **설명**: 요청을 주어진 도구를 사용하여 처리하는 에이전트
- **내부 파라미터**:
  - `Input *` (필수): 에이전트 입력
  - `Tools` (선택, 빨간 점): 사용할 Tool 노드 연결
  - `System Prompt Template` (선택): 에이전트 역할 정의 (팝업 텍스트 에디터 + 프롬프트 갤러리)
    - **프롬프트 갤러리 태그**: 블로그 초안, 회의록 작성, 피드백 생성, 이메일 작성, 코드 설명, 문서 생성, 요약, 이미지, 번역, RAG
    - **갤러리 샘플 프롬프트**: 멀티모달 이미지 분석, 코드 기능 설명 도우미, 회의록 요약 비서, 정확한 문맥 기반 RAG, 국가 기반 다국어 번역
  - `Jailbreak Check` (토글, 기본 OFF): 탈옥 시도 감지 ON/OFF (i 아이콘 포함)
  - `Model *` (필수): 사용할 LLM 선택 (드롭다운)
    - `azure_openai:gpt-4.1`
    - `azure_openai:gpt-4.1-mini`
    - `azure_openai:gpt-4.1-nano`
    - `azure_openai:gpt-4o`
- **입력 포트**: `Input *` ← (필수) / `Tools` ←(빨간)
- **Input에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Chat Input | 채팅 입력 컴포넌트 |
  | Template Message | 템플릿화 된 휴먼 메시지 생성 |
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자의 승인을 받음 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | API Request | HTTP API 요청을 보내고 응답을 처리 |
  | PLL Guardrail | PII 필터링 컴포넌트 |
  | Moderation Guardrail | 콘텐츠 안전 필터링 컴포넌트 |
- **Tools에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Simple Calculator Tool | 간단한 계산기 도구 |
  | Web Search Tool | 웹 검색 도구 |
  | Youtube Search Tool | YouTube 검색 도구 |
  | MCP Connection Tool | MCP 서버 연결 도구 |
  | KOSIS Statistics Tool | KOSIS 데이터 관련 도구 |
- **출력 포트**: `Response` → (파란 점선)
- **Response에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Chat Output | AI 출력 컴포넌트 |
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자의 승인을 받음 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | KMS Retriever | 주어진 질문을 KMS 지식에서 검색하여 결과를 가져옴 |
  | Structured Output | 메시지를 구조화된 데이터로 변환 |
  | PLL Guardrail | PII 필터링 컴포넌트 |
  | Moderation Guardrail | 콘텐츠 안전 필터링 컴포넌트 |
- **용도**: Tool 호출이 필요한 복잡한 작업 처리
- **검증 일자**: 2026-05-18

#### AI Router
- **설명**: LLM이 입력을 보고 적절한 엣지로 라우팅하는 컴포넌트
- **내부 파라미터**:
  - `Input *` (필수): 라우팅 판단에 사용할 입력
  - `Edit Conditions *` (필수): 분기 조건 설정 (기어 아이콘 → 팝업 모달)
    - 팝업 구성: `Condition Name` + `Condition Description` 컬럼, `+ 추가` 버튼
    - 설명: "Conditions to determine which edge to route the message to."
  - `else 조건 기본 AI 메시지 사용 *` (필수, 토글): 어느 조건도 해당 없을 때 AI 판단으로 대체
  - `Model *` (필수): 라우팅 판단에 사용할 LLM (드롭다운)
    - `azure_openai:gpt-4.1`
    - `azure_openai:gpt-4.1-mini`
    - `azure_openai:gpt-4.1-nano`
    - `azure_openai:gpt-4o`
- **입력 포트**: `Input *` ← (필수)
- **Input에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Chat Input | 채팅 입력 컴포넌트 |
  | Template Message | 템플릿화 된 휴먼 메시지 생성 |
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자의 승인을 받음 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | API Request | HTTP API 요청을 보내고 응답을 처리 |
  | PLL Guardrail | PII 필터링 컴포넌트 |
  | Moderation Guardrail | 콘텐츠 안전 필터링 컴포넌트 |
- **출력 포트**: `else` → (파란) + 조건별 분기 포트 (Edit Conditions에서 추가한 조건마다 생성)
- **else에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자의 승인을 받음 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | KMS Retriever | 주어진 질문을 KMS 지식에서 검색하여 결과를 가져옴 |
  | Structured Output | 메시지를 구조화된 데이터로 변환 |
- **용도**: 입력 내용에 따라 다른 처리 경로로 자동 분기
- **검증 일자**: 2026-05-18

#### Structured Output
- **설명**: 메시지를 구조화된 데이터로 변환
- **내부 파라미터**:
  - `Input *` (필수): 변환할 텍스트
  - `데이터 스키마 *` (필수): JSON 스키마 정의 (`{ } 스키마 추가하기` 버튼 → 팝업 모달)
    - 팝업 제목: `출력 스키마 정의`
    - 우측 패널: `JSON 스키마 미리보기` (수정 / 복사 버튼)
    - **속성 추가** (`+ 속성 추가` 버튼):
      - `속성 명`: 텍스트 입력
      - `타입` 드롭다운: Object / String / Number / Integer / Boolean / Array
      - `설명`: 텍스트 입력
      - `필수여부`: 체크박스
      - `열거형 값`: 허용 값 입력 후 엔터로 추가
    - **추가 속성** (라디오버튼, 기본값: 추가 속성 허용):
      - `추가 속성 허용` (기본 선택)
      - `추가 필드 없음`
      - `Strict 모드`
  - ⚠️ **스키마 이름 제약**: 스키마 최상위 name 값은 `^[a-zA-Z0-9_-]+$` 패턴만 허용
    - 한글, 공백, 특수문자 포함 시 `Error code: 400 - invalid_value` 발생
    - 예) `3줄요약` ❌ → `document_summary` ✅ / `회의록_분석` ❌ → `meeting_summary` ✅
  - `Model *` (필수): 변환에 사용할 LLM (드롭다운)
    - `azure_openai:gpt-4.1`
    - `azure_openai:gpt-4.1-mini`
    - `azure_openai:gpt-4.1-nano`
    - `azure_openai:gpt-4o`
- **입력 포트**: `Input *` ← (필수)
- **Input에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Chat Input | 채팅 입력 컴포넌트 |
  | Template Message | 템플릿화 된 휴먼 메시지 생성 |
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자의 승인을 받음 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | API Request | HTTP API 요청을 보내고 응답을 처리 |
  | PLL Guardrail | PII 필터링 컴포넌트 |
  | Moderation Guardrail | 콘텐츠 안전 필터링 컴포넌트 |
- **출력 포트**: `Result` →(주황)
- **Result에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | JSON Output | JSON 출력 컴포넌트 |
  | Document Formatter | Retriever 결과를 프롬프트에 활용 가능하게 포매팅 |
- ⚠️ **Document Formatter 연결 시 주의**: Structured Output Result(주황)를 Document Formatter에 연결하면 `'str' object has no attribute 'page_content'` 오류 발생. Document Formatter는 KMS Retriever의 Document 객체 배열을 기대하며, Structured Output의 JSON 문자열과 내부 타입이 다름. 포트 색상이 동일(주황)해도 데이터 타입 불일치로 런타임 오류 발생.
- **용도**: LLM 자유 텍스트 응답을 정해진 JSON 구조로 파싱. 결과 출력은 JSON Output 연결 필수. Chat Output과 JSON Output은 동일 플로우에서 동시 사용 불가(상호 배타) — 채팅 출력이 필요하면 Structured Output 없이 Language Model → Chat Output 경로로 별도 플로우 구성 권장
- **검증 일자**: 2026-05-18

---

### Tools 노드

#### Simple Calculator Tool
- **설명**: 간단한 계산기
- **내부 파라미터**:
  - `Tool List *` (필수): 기어 아이콘 → 팝업 모달
    - 컬럼: `Tool Name` / `Tool Description` / `Is Enabled`
    - 기본 제공 툴: `_calculate`
      - 간단한 계산을 수행하는 함수
      - param a: 첫 번째 숫자
      - param b: 두 번째 숫자
      - param operator: 연산자 (+, -, *, /)
      - return: 계산 결과
      - Is Enabled: 체크박스 (기본 체크)
- **입력 포트**: 없음
- **출력 포트**: `Tool` →(빨간)
- **Tool에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
- **검증 일자**: 2026-05-18

#### Web Search Tool
- **설명**: 웹 검색 도구
- **내부 파라미터**:
  - `Tool List *` (필수): 기어 아이콘 → 팝업 모달
    - 컬럼: `Tool Name` / `Tool Description` / `Is Enabled`
    - 기본 제공 툴: `_web_search`
      - 웹 검색을 수행하는 함수
      - Is Enabled: 체크박스 (기본 체크)
- **입력 포트**: 없음
- **출력 포트**: `Tool` →(빨간)
- **Tool에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
- **검증 일자**: 2026-05-18

#### Youtube Search Tool
- **설명**: Youtube 검색 도구
- **내부 파라미터**:
  - `Tool List *` (필수): 기어 아이콘 → 팝업 모달
    - 컬럼: `Tool Name` / `Tool Description` / `Is Enabled`
    - 기본 제공 툴: `_youtube_search`
      - YouTube 검색을 수행하는 함수
      - Is Enabled: 체크박스 (기본 체크)
- **입력 포트**: 없음
- **출력 포트**: `Tool` →(빨간)
- **Tool에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
- **검증 일자**: 2026-05-18

#### MCP Connection Tool
- **설명**: MCP 연결 도구
- **내부 파라미터 — Stdio 모드**:
  - `Mode *` (필수): `Stdio` / `Streamable-HTTP` 토글 선택
  - `MCP Server` (선택): MCP 서버 선택 드롭다운 (서버 목록 팝업)
    - 기본 제공 서버 목록: Atlassian, Fetch, Tavily, Bright Data, Browserbase, Context7, Exa Search, Notion, Github, Google Maps, Mem0 Memory, Supabase
    - 하단 MCP 갤러리 링크 제공
  - `MCP Command *` (필수): 실행할 MCP 명령 (텍스트 입력)
  - `Environment` (선택): 지구본 아이콘 → 팝업 (Stdio 환경변수)
    - 컬럼: `Environment Key` / `Environment Description` / `Environment Value`
    - `+ 추가` 버튼
    - 안내: "환경 변수는 Settings > My Secrets 에서 관리 가능합니다."
  - `Tool List *` (필수): 기어 아이콘 + 새로고침 버튼
- **내부 파라미터 — Streamable-HTTP 모드**:
  - `Mode *` (필수): `Stdio` / `Streamable-HTTP` 토글 선택
  - `MCP Streamable HTTP Endpoint *` (필수): URL 텍스트 입력
  - `Tool List *` (필수): 기어 아이콘 + 새로고침 버튼
  - `Header` (선택): 지구본 아이콘 → 팝업 (요청 헤더)
    - 컬럼: `Header Key` / `Header Value`
    - `+ 추가` 버튼
    - 안내: "환경 변수는 Settings > My Secrets 에서 관리 가능합니다."
  - `Timeout (ms)` (선택): 기본값 5000
  - `SSE Read Timeout (ms)` (선택): 기본값 300000
- **입력 포트**: 없음
- **출력 포트**: `Tool` →(빨간)
- **Tool에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
- **용도**: 외부 MCP 서버와 통신하여 확장 기능 제공
- **검증 일자**: 2026-05-18

#### KOSIS Statistics Tool
- **설명**: KOSIS 데이터 관련 도구
- **내부 파라미터**:
  - `Tool List *` (필수): 기어 아이콘 → 팝업 모달
    - 컬럼: `Tool Name` / `Tool Description` / `Is Enabled`
    - 기본 제공 툴 4종 (모두 기본 체크):
      | Tool Name | Tool Description |
      |-----------|----------------|
      | `search_statistics` | Find available statistics tables by topic or keyword. Always use this tool FIRST before querying data. Returns metadata with exact values needed for `sql_db_query` filters. |
      | `sql_db_schema` | Get table structure (columns, types, sample rows) for query writing. Use table identifiers from search_statistics metadata. |
      | `sql_db_query_checker` | Validate SQL query for syntax errors and metadata usage. Use before sql_db_query to catch errors early. |
      | `sql_db_query` | Execute SQL query for statistical analysis and data retrieval. Use exact values from search_statistics metadata. prd_se filter is required. Get table structure from sql_db_schema before writing queries. |
- **입력 포트**: 없음
- **출력 포트**: `Tool` →(빨간)
- **Tool에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
- **검증 일자**: 2026-05-18

#### API Request
- **설명**: HTTP API 요청을 보내고 응답을 처리합니다
- **모드 전환**: 노드 상단 `Tool Mode` 토글로 일반 모드 / Tool 모드 전환
- **내부 파라미터 — 일반 모드** (Tool Mode OFF):
  - `URL *` (필수): API 엔드포인트 URL (placeholder: `https://api.example.com/data`)
  - `Method *` (필수): GET / POST / PUT / PATCH / DELETE
  - `Connect Timeout (ms)` (선택): 연결 타임아웃 (기본값 1000ms)
  - `Read Timeout (ms)` (선택): 응답 대기 타임아웃 (기본값 1000ms)
  - `Header` (선택): 기어 아이콘 → 팝업 (`Header Key` / `Header Value`, `+ 추가`)
- **내부 파라미터 — Tool 모드** (Tool Mode ON):
  - `툴 설명 *` (필수): 툴 설명 텍스트 (에이전트가 참고)
  - `URL *` (필수): API 엔드포인트 URL
  - `Method *` (필수): GET / POST / PUT / PATCH / DELETE
  - `Connect Timeout (ms)` (선택): 기본값 1000ms
  - `Read Timeout (ms)` (선택): 기본값 3000ms (일반 모드와 다름)
  - `Header` (선택): 기어 아이콘 → 팝업 (`Header Key` / `Header Value`, `+ 추가`)
  - `Query Params` (선택): 기어 아이콘 → 팝업 (`Query Param 이름` / `Query Param 설명`, `+ 추가`) — Tool 모드 전용
- **입력 포트**: 없음
- **출력 포트 — 일반 모드**: `Data` →(파란)
- **Data에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | JSON Output | JSON 출력 컴포넌트 |
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자의 승인을 받음 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | KMS Retriever | 주어진 질문을 KMS 지식에서 검색하여 결과를 가져옴 |
  | Document Formatter | Retriever 결과를 프롬프트에 활용 가능하게 포매팅 |
  | Structured Output | 메시지를 구조화된 데이터로 변환 |
- **출력 포트 — Tool 모드**: `Tool` →(빨간)
- **Tool에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
- **용도**: 외부 REST API 호출. Tool 모드 시 Agent의 도구로 직접 등록 가능
- **검증 일자**: 2026-05-18

---

### RAG 노드

#### KMS Retriever
- **설명**: 주어진 질문을 KMS 지식에서 검색하여 결과를 가져옵니다
- **내부 파라미터**:
  - `Query *` (필수): 검색할 단어/문장 직접 입력 또는 컴포넌트 연결
    - placeholder: "검색할 단어/문장을 입력하거나 컴포넌트를 연결해주세요"
  - `Knowledge *` (필수): 검색 대상 지식베이스 선택 (드롭다운 + 새로고침 버튼)
    - 지식베이스는 ixi-enterprise 내 **지식베이스 탭**에서 별도 생성 및 관리
    - 지식 생성: `지식명 *` + `설명` 입력 → 문서(PDF 등) 업로드 → RAG 인덱싱
- **입력 포트**: `Query *` ←(파란, 필수) — 텍스트 직접 입력 또는 노드 연결 모두 가능
- **Query에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Chat Input | 채팅 입력 컴포넌트 |
  | Template Message | 템플릿화 된 휴먼 메시지 생성 |
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자의 승인을 받음 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | API Request | HTTP API 요청을 보내고 응답을 처리 |
  | Document Formatter | Retriever 결과를 프롬프트에 활용 가능하게 포매팅 |
  | PLL Guardrail | PII 필터링 컴포넌트 |
  | Moderation Guardrail | 콘텐츠 안전 필터링 컴포넌트 |
- **출력 포트**: `Documents` →(주황)
- **Documents에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | JSON Output | JSON 출력 컴포넌트 |
  | Document Formatter | Retriever 결과를 프롬프트에 활용 가능하게 포매팅 |
- **용도**: RAG 파이프라인의 검색 단계
- **검증 일자**: 2026-05-18

#### Document Formatter
- **설명**: Retriever의 결과를 프롬프트에 활용할 수 있게 적절하게 포매팅합니다
- **내부 파라미터**:
  - `Documents *` (필수): 주황 포트로 연결
- **입력 포트**: `Documents *` ←(주황, 필수)
- **Documents에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | API Request | HTTP API 요청을 보내고 응답을 처리 |
  | KMS Retriever | 주어진 질문을 KMS 지식에서 검색하여 결과를 가져옴 |
  | Structured Output | 메시지를 구조화된 데이터로 변환 |
- ⚠️ **Structured Output 연결 시 런타임 오류**: UI 상 연결은 가능하나 실행 시 `'str' object has no attribute 'page_content'` 오류 발생. Document Formatter는 KMS Retriever의 LangChain Document 객체 배열을 기대하며, Structured Output의 JSON 문자열과 내부 타입이 다름 — Structured Output → Document Formatter 연결 금지 (2026-05-18 확인)
- **출력 포트**: `Result` →(초록)
- **Result에 연결 가능한 노드** (실제 UI 검증 완료 — 일부):
  | 노드 | 설명 |
  |------|------|
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | Human Approval | 다음 작업 전 사용자의 승인을 받음 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | KMS Retriever | 주어진 질문을 KMS 지식에서 검색하여 결과를 가져옴 |
- **용도**: 검색된 문서 청크를 LLM이 읽기 좋은 형태로 변환
- **검증 일자**: 2026-05-18

---

### Human-in-the-Loop 노드

#### Human Approval
- **설명**: 다음 작업 전 사용자의 승인을 받습니다. 승인하지 않으면 전체 작업이 취소됩니다
- **내부 파라미터**:
  - `Target Message *` (필수): 승인 화면에 표시할 메시지 (노드 연결)
  - `question` (선택): 사용자에게 표시할 질문 (직접 입력 또는 노드 연결, 기본값: "진행하시겠습니까?")
  - `Model *` (필수): 판단에 사용할 LLM (드롭다운)
    - `azure_openai:gpt-4.1`
    - `azure_openai:gpt-4.1-mini`
    - `azure_openai:gpt-4.1-nano`
    - `azure_openai:gpt-4o`
- **입력 포트**: `Target Message *` ←(파란, 필수) / `question` ←(초록, 선택)
- **Target Message에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Chat Input | 채팅 입력 컴포넌트 |
  | Template Message | 템플릿화 된 휴먼 메시지 생성 |
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자의 승인을 받음 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | API Request | HTTP API 요청을 보내고 응답을 처리 |
  | PLL Guardrail | PII 필터링 컴포넌트 |
  | Moderation Guardrail | 콘텐츠 안전 필터링 컴포넌트 |
- **question에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | API Request | HTTP API 요청을 보내고 응답을 처리 |
  | Document Formatter | Retriever 결과를 프롬프트에 활용 가능하게 포매팅 |
- **출력 포트**: `Human Approval` →(파란)
- **Human Approval에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Agent | 요청을 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자의 승인을 받음 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | KMS Retriever | 주어진 질문을 KMS 지식에서 검색하여 결과를 가져옴 |
  | Structured Output | 메시지를 구조화된 데이터로 변환 |
- **용도**: 중요한 작업 실행 전 사람의 확인이 필요한 게이트. 거부 시 전체 플로우 즉시 종료
- **검증 일자**: 2026-05-18

#### Human Choice
- **설명**: 사용자가 직접 다음 노드를 선택하는 수동 라우팅 컴포넌트
- **내부 파라미터**:
  - `Input` (필수): 선택 화면에 표시할 컨텍스트 (텍스트 입력 또는 노드 연결)
  - `question`: 사용자에게 표시할 질문 텍스트 (기본값: "어떤 작업을 진행하시겠습니까?") / 노드 연결 가능: API Request, Document Formatter
  - `Edit Conditions`: 조건 분기 설정 팝업 (Condition Name + Condition Description 열로 구성)
  - `else 조건 기본 AI 메시지 사용` (토글, 필수): fallback 동작 방식 선택
    - `<>` 버튼: "코드 수정" 팝업 — Markdown 에디터로 커스텀 AI fallback 메시지 작성
  - `Model` (필수): LLM 선택 — `azure_openai:gpt-4.1`, `azure_openai:gpt-4.1-mini`, `azure_openai:gpt-4.1-nano`, `azure_openai:gpt-4o`
- **입력 포트**: `Input` (파란)
- **Input에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Chat Input | 채팅 입력 컴포넌트 |
  | Template Message | 템플릿화 된 휴먼 메시지 생성 |
  | Agent | 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자 승인 요청 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | API Request | HTTP API 요청 송수신 |
  | PLL Guardrail | 개인정보(PII) 필터링 |
  | Moderation Guardrail | 콘텐츠 안전 필터링 |
- **출력 포트**:
  - `else` (조건 분기): `else 조건 기본 AI 메시지 사용` 토글 상태에 따라 연결 가능 노드가 달라짐
- **else에 연결 가능한 노드 — 토글 OFF 상태** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Agent | 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자 승인 요청 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | KMS Retriever | KMS 지식에서 검색 후 결과 반환 |
  | Structured Output | 메시지를 구조화된 데이터로 변환 |
- **else에 연결 가능한 노드 — 토글 ON 상태** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Chat Output | AI 출력 컴포넌트 |
  | PLL Guardrail | 개인정보(PII) 필터링 |
  | Moderation Guardrail | 콘텐츠 안전 필터링 |
- **용도**: AI 자동 판단 대신 사람이 직접 분기를 선택; else는 정의된 조건에 해당하지 않는 fallback 경로
- **검증 일자**: 2026-05-18

---

### Guardrail 노드

#### Moderation Guardrail
- **설명**: 콘텐츠 안전 필터링 컴포넌트
- **내부 파라미터**:
  - `Hate` (슬라이더 1~7): 혐오 발언 민감도 (1=가장 엄격, 7=가장 관대)
  - `SelfHarm` (슬라이더 1~7): 자해 관련 민감도
  - `Sexual` (슬라이더 1~7): 성적 콘텐츠 민감도
  - `Violence` (슬라이더 1~7): 폭력 관련 민감도
- **입력 포트**: `Input *` (파란, 필수)
- **Input에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Agent | 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | PLL Guardrail | 개인정보(PII) 필터링 |
  | Moderation Guardrail | 콘텐츠 안전 필터링 |
- **출력 포트**: `Response` (파란 파선)
- **Response에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Chat Output | AI 출력 컴포넌트 |
  | Agent | 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자 승인 요청 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | KMS Retriever | KMS 지식에서 검색 후 결과 반환 |
  | Structured Output | 메시지를 구조화된 데이터로 변환 |
  | PLL Guardrail | 개인정보(PII) 필터링 |
  | Moderation Guardrail | 콘텐츠 안전 필터링 |
- **용도**: 입력 또는 출력 텍스트의 유해 콘텐츠 감지 및 차단
- **검증 일자**: 2026-05-18

#### PLL Guardrail
- **설명**: PII(개인식별정보) 필터링 컴포넌트
- **내부 파라미터**: 없음 (Input 포트 연결만으로 동작)
- ⚠️ **사전 조건**: Azure Language Service API Key 및 엔드포인트를 ixi-enterprise Settings에 등록 필요. 미등록 시 `401 Access denied` 오류 발생 (2026-05-18 확인). 등록 방법 미확인 → `04-open-questions.md` 항목 13 참조
- **입력 포트**: `Input *` (파란, 필수)
- **Input에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Agent | 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | PLL Guardrail | 개인정보(PII) 필터링 |
  | Moderation Guardrail | 콘텐츠 안전 필터링 |
- **출력 포트**: `Response` (파란 파선)
- **Response에 연결 가능한 노드** (실제 UI 검증 완료):
  | 노드 | 설명 |
  |------|------|
  | Chat Output | AI 출력 컴포넌트 |
  | Agent | 주어진 도구를 사용하여 처리하는 에이전트 |
  | Language Model | LLM으로 입력 메시지에 대한 응답 생성 |
  | AI Router | LLM이 입력을 보고 적절한 엣지로 라우팅 |
  | Human Approval | 다음 작업 전 사용자 승인 요청 |
  | Human Choice | 사용자가 직접 다음 노드를 선택하는 수동 라우팅 |
  | KMS Retriever | KMS 지식에서 검색 후 결과 반환 |
  | Structured Output | 메시지를 구조화된 데이터로 변환 |
  | PLL Guardrail | 개인정보(PII) 필터링 |
  | Moderation Guardrail | 콘텐츠 안전 필터링 |
- **용도**: 주민등록번호, 전화번호, 이메일 등 개인정보 감지 및 마스킹 처리
- **검증 일자**: 2026-05-18

---

## 노드 연결 포트 색상 규칙

| 색상 | 선 종류 | 의미 | 대표 포트 |
|------|--------|------|----------|
| 파란 실선 | 실선 | 필수 입력 포트 | Chat Output Input, KMS Retriever Query |
| 파란 점선 | 점선 | 일반 데이터 출력 | Chat Input User Message, Language Model Response, Agent Response |
| 빨간 점 | 점 | 선택 입력 포트 (미연결 가능) | Agent Tools |
| 빨간 실선 | 실선 | Tool 출력 포트 | Simple Calculator Tool, Web Search Tool 등 Tool 노드 출력 |
| 주황 | - | 문서/RAG 데이터 | KMS Retriever Documents 출력, Document Formatter Documents 입력, Structured Output Result 출력 |
| 초록 | - | 포매팅 결과 출력 | Document Formatter Result 출력 |
| 파란 파선 | 파선 | Guardrail 출력 | PLL Guardrail Response, Moderation Guardrail Response |

### 주요 포트 연결 제약 요약

| 제약 | 내용 |
|------|------|
| Chat Input → Guardrail | ❌ 직접 연결 불가. Agent 또는 Language Model 경유 필수 |
| Human Approval 출력 → Chat Output | ❌ 직접 연결 불가. Agent 또는 Language Model 경유 필수 |
| AI Router else → Chat Output | ❌ 직접 연결 불가. Language Model 또는 Agent 경유 필수 |
| Human Choice else(토글 ON) → Chat Output | ✅ 직접 연결 가능 |
| Human Choice else(토글 OFF) → Chat Output | ❌ 직접 연결 불가. Language Model 또는 Agent 경유 필수 |
| Structured Output Result → Document Formatter | ⚠️ UI 연결 가능하나 런타임 오류 (`'str' object has no attribute 'page_content'`) — 연결 금지 |
| Structured Output Result → JSON Output | ✅ 권장 연결 |
| JSON Output + Chat Output 동시 사용 | ❌ 상호 배타적 — 하나만 선택 |
| Language Model Response → Chat Output | ⚠️ Language Model 포트에서 드래그 시 목록에 없음. Chat Output 쪽에서 드래그 시 연결 가능 |
| Template Message 단독 사용 | ❌ INPUT 컴포넌트 미인식 — Chat Input 병행 또는 대체 필수 |
