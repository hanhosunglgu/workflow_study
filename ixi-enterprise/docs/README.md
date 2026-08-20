# ixi-enterprise 분석 문서

**작성일**: 2026-05-15  
**최종 수정**: 2026-06-02  
**대상**: ixi-enterprise 사내향 AI 플로우 빌더 노드 분석, 워크플로우 구현 분석, n8n 대비 보완점 검토 및 개발 요구사항 도출

> ⚠️ 노드 카탈로그·플로우 분석·보완점 검토·요구사항 명세 4개 문서는 프로젝트 루트(`workflow_study/`)로 이동되었습니다.

---

## 문서 목록

### 프로젝트 루트 이동 문서

| 파일 | 내용 |
|------|------|
| [04-ixi-enterprise-node-catalog.md](../../04-ixi-enterprise-node-catalog.md) | 전체 노드 카탈로그 — 21개 노드 파라미터/포트/용도 상세 (UI 검증 완료, 2026-08-20 Send Mail Output 추가) |
| [05-ixi-enterprise-flow_analysis.md](../../05-ixi-enterprise-flow_analysis.md) | ixi-enterprise로 구현한 8개 워크플로우 구성 및 노드 설정 분석 |
| [06-ixi-enterprise-improvement-review.md](../../06-ixi-enterprise-improvement-review.md) | ixi 워크플로우 n8n 대체 구현 — 노드 매핑, 디버깅·예외처리 한계 비교 |
| [07-ixi-enterprise-requirements-spec.md](../../07-ixi-enterprise-requirements-spec.md) | ixi-enterprise 개발팀 추가 개발 요구사항 명세서 (20개 REQ) |

### 플로우 카탈로그 (이 폴더)

| 파일 | 내용 |
|------|------|
| [flow-overview.md](./flow-overview.md) | 자동화 플로우 아이디어 전체 목록 (13개 플로우) |
| [flow-rag.md](./flow-rag.md) | 플로우 카테고리 1: RAG / 지식 검색 기반 (1-1~1-3) |
| [flow-agent-tool.md](./flow-agent-tool.md) | 플로우 카테고리 2: Agent + Tool 조합 (2-1~2-3) |
| [flow-routing.md](./flow-routing.md) | 플로우 카테고리 3: 라우팅 / 분기 (3-1~3-2) |
| [flow-human-loop.md](./flow-human-loop.md) | 플로우 카테고리 4: Human-in-the-Loop (4-1~4-2) |
| [flow-guardrail.md](./flow-guardrail.md) | 플로우 카테고리 5: Guardrail 안전 레이어 (5-1~5-2) |
| [flow-mcp.md](./flow-mcp.md) | 플로우 카테고리 6: MCP 확장 (6-1) |
| [security-agent-requirements.md](./security-agent-requirements.md) | 보안 통합 Agent 시스템 요구사항 명세 (Mock 서버 포함) |

### 실전 구축 기록 (2026-08-18 추가)

| 파일 | 내용 |
|------|------|
| **[ivms-flow-a-build-lessons.md](./ivms-flow-a-build-lessons.md)** | **IVMS 플로우 A 구축 실전 기록** — 개발기 서버 주소, IVMS 스펙표 오류, 컨텍스트 예산 대응, 프롬프트 작성 규칙, 검증된 API 체이닝. **다음 프로젝트 착수 전 필독** |

> 🔴 위 문서의 핵심 3가지: (1) **IVMS 스펙표의 필수 Y/N을 신뢰하지 말 것** — 두 API에서 연달아 불일치 확인, (2) **API 파라미터 문제는 캔버스가 아니라 개발기 curl로 진단할 것** — 캔버스는 요청 Body를 볼 수 없음, (3) **System Prompt에 `{변수}` 중괄호를 쓰지 말 것** — 템플릿 변수로 해석되어 실행이 차단됨

---

## 핵심 요약

### ixi-enterprise 노드 카테고리

```
I/O          : Chat Input, Chat Output, JSON Output, Template Message, Send Mail Output
AI/LLM       : Language Model, Agent, AI Router, Structured Output
Tools        : Calculator, Web Search, Youtube, MCP Connection, KOSIS, API Request
RAG          : KMS Retriever, Document Formatter
Human Loop   : Human Approval, Human Choice
Guardrail    : Moderation Guardrail, PLL Guardrail
```
총 21개 노드 (2026-05-18 UI 검증 20개 + 2026-08-20 Send Mail Output 확인)

### 구현된 워크플로우 8개 (2026-06-02 기준)

| # | 플로우 ID | 플로우명 |
|---|----------|---------|
| 1 | 1-1 | 문서 Q&A 챗봇 (KMS + Language Model) |
| 2 | 1-2 | 문서 요약 (KMS + Agent) |
| 3 | 2-1 | 리서치 Agent (Web/Youtube/KOSIS + PLL Guardrail) |
| 4 | 2-2 | 사내 시스템 연동 Agent (ISMS/EMS API Request Tool) |
| 5 | 3-1 | AI Router 라우팅 |
| 6 | 3-2 | Human Choice 라우팅 |
| 7 | 4-2 | Human Approval 승인 플로우 |
| 8 | 6-1 | MCP 통합 Agent (Context7/GitHub/Atlassian) |

### ixi-enterprise 보완점 (n8n 대비)

| 분류 | 핵심 보완 필요 사항 |
|------|-----------------|
| 포트 연결 | Chat Input → Guardrail 직접 연결 허용 등 6개 제약 해소 필요 |
| 트리거 | Schedule Trigger / Webhook Trigger 노드 추가 필요 |
| 플로우 구조 | Sub-flow(플로우 호출) 노드 추가 필요 |
| 디버깅 | 노드별 Input/Output 확인 패널, 실행 로그, Test Step 추가 필요 |
| 예외처리 | 노드별 Retry, Timeout, On Error 분기 기능 추가 필요 |
