# 소스 요약: ixi-enterprise docs (2026-05-18)

**카테고리**: sources  
**태그**: ixi-enterprise, 노드카탈로그, UI검증  
**최종 수정**: 2026-05-18  
**관련 페이지**: [[node-catalog-summary]], [[overview]], [[current-flow]]

---

## 소스 정보

| 항목 | 내용 |
|------|------|
| 소스 유형 | 내부 분석 문서 (마크다운) |
| 위치 | `ixi-enterprise/docs/` |
| 작성 기간 | 2026-05-15 ~ 2026-05-18 |
| 주요 작업 | UI 스크린샷 기반 20개 노드 포트 검증 |

---

## 포함 문서 목록

| 파일 | 핵심 내용 |
|------|---------|
| 01-node-catalog.md | 전체 20개 노드 파라미터/포트/연결 가능 노드 (UI 검증 완료) |
| 02-current-flow-analysis.md | 현재 PPT RAG 요약 플로우 구조, 5가지 문제점, 개선안 |
| 03-n8n-implementation.md | Qdrant 기반 n8n RAG 구현 방안, docker-compose, JSON 스니펫 |
| 04-open-questions.md | 미확인 사항 12개 (KMS 대체, Azure 엔드포인트, PPTX 처리 등) |
| 05-flow-overview.md | 13개 플로우 아이디어 목록, 사내 임팩트 Top 3 |
| 06-flow-rag.md | RAG 플로우 3종 상세 설계 |
| 07-flow-agent-tool.md | Agent+Tool 플로우 3종 상세 설계 |
| 08-flow-routing.md | 라우팅 플로우 2종 상세 설계 |
| 09-flow-human-loop.md | Human-in-the-Loop 플로우 2종 상세 설계 |
| 10-flow-guardrail.md | Guardrail 플로우 2종 상세 설계 |
| 11-flow-mcp.md | MCP 연결 통합 Agent 플로우 설계 |
| 12-security-agent-requirements.md | 보안 통합 Agent 요구사항, Mock 서버 스펙 |

---

## 핵심 발견 사항

1. **JSON Output 노드 발견**: 기존 목록에 없던 20번째 노드
2. **API Request Tool 모드**: 토글로 완전히 다른 동작 (Data 출력 vs Tool 출력)
3. **Guardrail Input 제약**: Chat Input 직접 연결 불가 — Agent/Language Model 경유 필요
4. **Human Choice else 토글**: ON/OFF에 따라 연결 가능 노드 목록이 상이
5. **Agent Tools 포트**: 빨간 점(선택 포트) — 필수 아님
6. **Agent context 포트**: 존재하지 않음 (과거 문서의 오기)
7. **모델 표기**: `azure_openai:gpt-4.1-mini` (`:` 구분자)
8. **Human Approval → Chat Output 직접 연결 불가**: 양방향 모두 불가 — Agent/Language Model 경유 필수
9. **JSON Output ↔ Chat Output 상호 배타적**: JSON Output 추가 시 Chat Output 비활성화
10. **Language Model → Chat Output 연결 방향**: LM Response 포트에서 드래그 시 Chat Output 목록에 없음 — Chat Output Input 포트에서 드래그 시작 필요
11. **Template Message**: INPUT 컴포넌트 아님 — 단독 사용 시 "단 하나의 INPUT 컴포넌트는 필수입니다" 오류
12. **Structured Output → Document Formatter 타입 불일치**: 동일 주황 포트이나 런타임에서 `'str' object has no attribute 'page_content'` 오류
13. **PLL Guardrail Azure API Key 필수**: 미등록 시 `401 Access denied` 발생

---

## 미결 사항 (이 소스에서 미해결)

- Guardrail 실패 시 플로우 분기 동작 방식 (통과 시 Response 포트 출력 / 실패 시 중단 확인, 상세 스펙 미공개)
- MCP 서버 목록 및 사내 접속 정보
- n8n 버전, Azure 엔드포인트, Embedding 모델 배포 여부
- Human Approval UI 채널 (Teams/이메일/웹)
- PLL Guardrail Azure Language Service API Key 등록 방법 (ixi-enterprise Settings에서 확인 필요)
