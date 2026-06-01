# ixi-enterprise 분석 문서

**작성일**: 2026-05-15  
**대상**: ixi-enterprise 사내향 AI 플로우 빌더 노드 분석 및 n8n 구현 방안

---

## 문서 목록

| 파일 | 내용 |
|------|------|
| [01-node-catalog.md](./01-node-catalog.md) | 전체 노드 카탈로그 — 20개 노드 파라미터/포트/용도 상세 (UI 검증 완료) |
| [02-current-flow-analysis.md](./02-current-flow-analysis.md) | 현재 동작 플로우 분석 — PPT RAG 요약 플로우 구조 및 문제점 |
| [03-n8n-implementation.md](./03-n8n-implementation.md) | n8n 구현 방안 — KMS 없이 Qdrant로 RAG 파이프라인 구축 |
| [04-open-questions.md](./04-open-questions.md) | 미확인 사항 — 추가 개발 전 확인 필요 항목 |
| [05-flow-overview.md](./05-flow-overview.md) | 자동화 플로우 아이디어 전체 목록 (13개 플로우) |
| [06-flow-rag.md](./06-flow-rag.md) | 플로우 카테고리 1: RAG / 지식 검색 기반 (1-1~1-3) |
| [07-flow-agent-tool.md](./07-flow-agent-tool.md) | 플로우 카테고리 2: Agent + Tool 조합 (2-1~2-3) |
| [08-flow-routing.md](./08-flow-routing.md) | 플로우 카테고리 3: 라우팅 / 분기 (3-1~3-2) |
| [09-flow-human-loop.md](./09-flow-human-loop.md) | 플로우 카테고리 4: Human-in-the-Loop (4-1~4-2) |
| [10-flow-guardrail.md](./10-flow-guardrail.md) | 플로우 카테고리 5: Guardrail 안전 레이어 (5-1~5-2) |
| [11-flow-mcp.md](./11-flow-mcp.md) | 플로우 카테고리 6: MCP 확장 (6-1) |
| [12-security-agent-requirements.md](./12-security-agent-requirements.md) | 보안 통합 Agent 시스템 요구사항 명세 (Mock 서버 포함) |

---

## 핵심 요약

### ixi-enterprise 노드 카테고리

```
I/O          : Chat Input, Chat Output, JSON Output, Template Message
AI/LLM       : Language Model, Agent, AI Router, Structured Output
Tools        : Calculator, Web Search, Youtube, MCP Connection, KOSIS, API Request
RAG          : KMS Retriever, Document Formatter
Human Loop   : Human Approval, Human Choice
Guardrail    : Moderation Guardrail, PLL Guardrail
```
총 20개 노드 (2026-05-18 UI 검증 완료)

### 현재 동작 플로우

```
Chat Input → KMS Retriever → Document Formatter → Agent → Chat Output
             (PPT 업로드)     (청크 포매팅)        (azure/gpt-4.1-mini)
```

### n8n 구현 방향

```
KMS → Qdrant (Docker) + Azure OpenAI Embeddings
Agent → n8n LangChain Agent 또는 LLM Chain 노드
전체 2개 워크플로: 인제스트(문서 저장) + 채팅(RAG 검색)
```

### 구현 로드맵

| 단계 | 기간 | 목표 |
|------|------|------|
| 1단계 POC | 1~2일 | txt 파일 + In-Memory Vector Store로 RAG 채팅 동작 확인 |
| 2단계 안정화 | 3~5일 | Qdrant 영구 저장 + PPTX 자동 인제스트 |
| 3단계 운영화 | 1주 | Guardrail, Human Approval, 멀티턴 대화 추가 |
