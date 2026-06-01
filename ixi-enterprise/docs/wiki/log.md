# Wiki 작업 이력

append-only 로그. 각 항목은 `## [날짜] 작업유형 | 제목` 형식.

---

## [2026-05-18] init | wiki 초기 구축

- WIKI.md (schema), index.md, log.md, overview.md 생성
- 기존 docs 폴더 전체를 첫 번째 소스로 ingest
  - 01-node-catalog.md: 20개 노드 전체 포트 검증 완료본
  - 02-current-flow-analysis.md: PPT RAG 요약 플로우 분석
  - 03-n8n-implementation.md: n8n 구현 방안
  - 04-open-questions.md: 미확인 사항
  - 05~11: 플로우 카테고리별 설계 문서
  - 12-security-agent-requirements.md: 보안 Agent 요구사항
- 생성된 entities 페이지: 20개 노드 각각 (node-catalog 참조)
- 생성된 concepts 페이지: port-color-rules, guardrail-design, agent-vs-language-model, human-approval-pattern, rag-pipeline, routing-pattern, mcp-pattern
- 생성된 flows 페이지: current-flow, flow-rag, flow-agent-tool, flow-routing, flow-human-loop, flow-guardrail, flow-mcp, flow-security-agent
- 생성된 sources 페이지: ixi-enterprise-docs-2026-05-18

## [2026-05-18] ingest | ixi-enterprise docs (노드 카탈로그 UI 검증 완료본)

- 노드 카탈로그 2026-05-18 UI 검증 결과 반영
- 신규 발견: JSON Output 노드 (기존 목록에 없던 20번째 노드)
- API Request 노드: 일반 모드 / Tool 모드 두 가지 동작 방식 확인
- Human Choice else 출력: 토글 ON/OFF에 따라 연결 가능 노드 목록이 다름
- Guardrail 노드 Input: Agent, Language Model, PLL Guardrail, Moderation Guardrail만 연결 가능 (Chat Input 등 I/O 직접 연결 불가)

## [2026-05-19] update | 11-flow-mcp.md MCP 갤러리 실측 및 테스트 3선 설정 가이드 추가

- MCP 갤러리 전체 12개 서버 목록 상세 기재 (기존 3개 → 12개 전체)
- 테스트 권장 MCP 3선 확정: Context7 / GitHub / Atlassian
- 플로우 구성도 3개 기준으로 재구성 (Web Search, API Request 제거)
- 시나리오 섹션: Context7 신규 추가, Jira·Confluence 분리 → Atlassian 통합
- MCP Connection Tool 설정 가이드 3개 각각 상세화
  - Context7: Stdio + `npx -y @upstash/context7-mcp`, 환경변수 없음
  - GitHub: Stdio + PAT 발급 경로 및 권한 명시
  - Atlassian: Stdio + JIRA_URL / JIRA_USERNAME / JIRA_API_TOKEN 3개 환경변수
    (JIRA_URL = https://lgucorp.atlassian.net, 기존 n8n 환경변수 재활용 가능)
- 로드맵 Context7(1단계) → GitHub(2단계) → Atlassian(3단계) 순서로 재정렬
- 개요 핵심 노드 텍스트 수정, API Request Tool 모드 주의사항 삭제 (플로우에서 제외)
- Context7 Tool List 확인: resolve-library-id → query-docs 2개 도구 모두 활성화 확인

## [2026-05-18] update | 전체 문서 UI 검증 결과 반영 (포트 제약 일관성 업데이트)

**변경된 docs 파일 (12개)**

- `01-node-catalog.md`: 포트 색상 선 종류 추가, 주요 포트 연결 제약 요약 테이블 신설, Document Formatter 경고 추가, PLL Guardrail Azure Key 필수 경고 추가
- `02-current-flow-analysis.md`: 단기/장기 개선 플로우 Guardrail 연결 패턴 수정 (Chat Input → LM 패스스루 → PLL Guardrail)
- `03-n8n-implementation.md`: Phase 3 ixi-enterprise 포트 제약 경고 블록 추가
- `04-open-questions.md`: 확인 완료 항목 8개 추가 (항목 12~19): JSON Output 상호 배타, LM→Chat Output 연결 방향, Template Message INPUT 아님, Structured Output 타입 불일치, Human Approval→Chat Output 불가, Chat Input→Guardrail 불가
- `05-flow-overview.md`: 플로우 1-2/4-2 다이어그램 수정, 노드 활용 빈도 업데이트
- `10-flow-guardrail.md`: 5-1/5-2 플로우 완전 재구성 (LM 패스스루 패턴 적용)
- `11-flow-mcp.md`: Guardrail 순서 수정, Human Approval 경유 패턴 추가
- `12-security-agent-requirements.md`: Phase 3 포트 제약 경고 블록 추가

**변경된 wiki 파일 (7개)**

- `wiki/overview.md`: 포트 색상 테이블에 선 종류 및 주요 제약 요약 추가
- `wiki/concepts/port-color-rules.md`: (기존 내용 정확 — 유지)
- `wiki/concepts/guardrail-design.md`: (기존 내용 정확 — 유지)
- `wiki/concepts/human-approval-pattern.md`: (기존 내용 정확 — 유지)
- `wiki/concepts/routing-pattern.md`: 통합 업무 라우터 예시에 LM 패스스루 패턴 추가, AI Router else 제약 경고 추가
- `wiki/flows/current-flow.md`: 단기 개선 플로우에 LM 패스스루 노드 추가, PLL API Key 경고 추가
- `wiki/flows/flow-security-agent.md`: 플로우 다이어그램 재구성 (Tool 노드 위치, Human Approval → Agent → Chat Output 패턴 반영)
- `wiki/sources/ixi-enterprise-docs-2026-05-18.md`: 핵심 발견 사항 8→13개로 확장, 미결 사항 업데이트

**핵심 검증 사실 (이번 업데이트에서 확정)**

1. Chat Input → Guardrail 직접 연결 불가 — LM(패스스루) 또는 Agent 경유 필수
2. Human Approval → Chat Output 직접 연결 불가 (양방향 모두) — Agent/LM 경유 필수
3. JSON Output ↔ Chat Output 상호 배타적
4. Structured Output → Document Formatter 런타임 오류 (`'str' object has no attribute 'page_content'`)
5. Language Model → Chat Output: Chat Output Input 포트에서 드래그 시작 필요
6. Template Message: INPUT 컴포넌트 아님
7. PLL Guardrail: Azure Language Service API Key 등록 필수 (미등록 시 401)
