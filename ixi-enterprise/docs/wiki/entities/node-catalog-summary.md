# 노드 카탈로그 요약

**카테고리**: entities  
**태그**: 노드, 포트, UI검증  
**최종 수정**: 2026-05-18  
**관련 페이지**: [[port-color-rules]], [[agent]], [[kms-retriever]], [[api-request]], [[human-choice]]

---

## 검증 현황

2026-05-18 UI 스크린샷으로 전체 20개 노드의 입출력 포트 및 연결 가능 노드 목록 검증 완료.  
원본 상세 스펙: `docs/01-node-catalog.md`

---

## 노드별 핵심 특징 요약

### I/O 노드

| 노드 | 입력 | 출력 | 특징 |
|------|------|------|------|
| [[chat-input]] | 없음 (시작점) | User Message (파란) | 플로우 진입점 |
| [[chat-output]] | Message (파란) | 없음 (종료점) | 플로우 종료점 |
| [[json-output]] | Input (파란) | 없음 (종료점) | Structured Output 결과 출력용 |
| [[template-message]] | 없음 | User Message (파란) | 고정 템플릿으로 메시지 생성 |

### AI/LLM 노드

| 노드 | 입력 | 출력 | 특징 |
|------|------|------|------|
| [[language-model]] | Input * (파란) | Response (파란 점선) | System Prompt + 4개 모델 선택 |
| [[agent]] | Input * (파란), Tools (빨간 점, 선택) | Response (파란 점선) | ReAct 루프, Jailbreak Check 토글 |
| [[ai-router]] | Input * (파란) | 조건별 분기 + else | LLM이 자동 라우팅, Edit Conditions 팝업 |
| [[structured-output]] | Input * (파란) | Result (주황) | JSON 스키마 정의 → 구조화 추출. 스키마 이름은 `^[a-zA-Z0-9_-]+$` 패턴만 허용 (한글 불가) |

### Tools 노드 — 공통 특징

- **Tool List 포트** (초록 점선): Agent의 Tools 포트에 연결
- **Tool 포트** (빨간): 다른 Tool 노드와 체이닝 가능

| 노드 | 특징 |
|------|------|
| [[simple-calculator-tool]] | 수식 계산 |
| [[web-search-tool]] | 실시간 웹 검색 |
| [[youtube-search-tool]] | YouTube 영상 검색 |
| [[mcp-connection-tool]] | Stdio / Streamable-HTTP 두 가지 모드, MCP 갤러리 12개 서버 |
| [[kosis-statistics-tool]] | 국가통계포털 데이터 조회 |
| [[api-request]] | 일반 모드(Data 출력) / Tool 모드(Tool 출력) 토글로 전환 |

### RAG 노드

| 노드 | 입력 | 출력 | 특징 |
|------|------|------|------|
| [[kms-retriever]] | Query * (파란) + Knowledge * (드롭다운) | Documents (주황) | KMS 지식베이스 벡터 검색 |
| [[document-formatter]] | Documents * (주황) | Result (초록) | RAG 청크 → 프롬프트 문자열 변환 |

### Human-in-the-Loop 노드

| 노드 | 입력 | 출력 | 특징 |
|------|------|------|------|
| [[human-approval]] | Target Message + question | Approved / Rejected | 승인/거부 2분기 |
| [[human-choice]] | Input + question | 조건별 분기 + else | else 토글 ON/OFF로 출력 노드 목록 달라짐 |

### Guardrail 노드

| 노드 | 입력 가능 노드 | 출력 | 특징 |
|------|-------------|------|------|
| [[moderation-guardrail]] | Agent, Language Model, PLL Guardrail, Moderation Guardrail | Response (파란) | Hate/SelfHarm/Sexual/Violence 슬라이더 |
| [[pll-guardrail]] | Agent, Language Model, PLL Guardrail, Moderation Guardrail | Response (파란) | 파라미터 없음, 연결만으로 동작 |

> ⚠️ Guardrail 노드는 Chat Input, Template Message 등 I/O 노드와 직접 연결 불가.  
> Chat Input → (Agent 또는 Language Model) → Guardrail 순서로 연결해야 함.  
> 단, Guardrail Response는 KMS Retriever에 연결 가능.

---

## 주요 발견 사항 (UI 검증)

1. **JSON Output**: 기존 목록에 없던 20번째 노드로 발견
2. **API Request Tool 모드**: 토글 하나로 완전히 다른 노드로 동작
3. **Human Choice else 토글**: ON 상태에서는 Chat Output, PLL Guardrail, Moderation Guardrail만 연결 가능
4. **Agent Tools 포트**: 빨간 점(선택 포트) — 미연결 상태로도 동작
5. **MCP Connection Tool**: 갤러리에 12개 서버 내장 (Atlassian, GitHub, Notion 등)
6. **Structured Output 스키마 이름 제약**: `^[a-zA-Z0-9_-]+$` 패턴 위반 시 `Error 400 invalid_value` 발생 — 한글/공백 불가
7. **Structured Output → Document Formatter 타입 불일치**: 포트 색상이 동일(주황)해도 런타임에서 `'str' object has no attribute 'page_content'` 오류 발생. Structured Output Result는 JSON 문자열이고 Document Formatter는 Document 객체 배열을 기대함 — JSON Output으로만 연결할 것
8. **Template Message는 INPUT 컴포넌트 아님**: 플로우 시작점으로 단독 사용 시 "단 하나의 INPUT 컴포넌트는 필수입니다 (현재 개수 : 0개)" 오류 발생. 반드시 Chat Input과 함께 사용하거나 Chat Input으로 대체할 것 (2026-05-18 확인)
9. **JSON Output ↔ Chat Output 상호 배타적**: 플로우에 JSON Output을 추가하면 Chat Output이 비활성화됨. 두 노드 동시 사용 불가 — 출력 방식 하나만 선택 (2026-05-18 확인)
10. **Language Model Response → Chat Output 연결 방향 주의**: Language Model Response 포트에서 연결 드래그 시 Chat Output이 목록에 없음 (UI 검증 2026-05-18). 단, Chat Output Input 포트에서 연결 드래그 시 Language Model이 선택 가능 — Chat Output 쪽에서 연결 시작하면 연결 가능. 연결 방향에 따라 선택 가능 목록이 다름에 유의. Human Approval → Chat Output 직접 연결은 양방향 모두 불가 — Agent 또는 Language Model 경유 필수.
