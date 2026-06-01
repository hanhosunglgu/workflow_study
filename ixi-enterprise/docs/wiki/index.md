# Wiki 인덱스

**최종 수정**: 2026-05-19  
**총 페이지 수**: 15  
LLM이 query 시 이 파일을 먼저 읽어 관련 페이지를 파악한다.

---

## Overview

| 파일 | 요약 |
|------|------|
| [overview.md](./overview.md) | wiki 전체 합성 요약, 노드 목록, 설계 원칙, 로드맵 진입점 |

---

## Entities (개체 페이지)

| 파일 | 요약 |
|------|------|
| [entities/node-catalog-summary.md](./entities/node-catalog-summary.md) | 20개 노드 전체 핵심 특징 요약 — UI 검증 완료 (2026-05-18) |

> 📝 미생성 entity 페이지 (필요 시 개별 생성):  
> [[chat-input]], [[chat-output]], [[json-output]], [[template-message]],  
> [[language-model]], [[agent]], [[ai-router]], [[structured-output]],  
> [[simple-calculator-tool]], [[web-search-tool]], [[youtube-search-tool]],  
> [[mcp-connection-tool]], [[kosis-statistics-tool]], [[api-request]],  
> [[kms-retriever]], [[document-formatter]],  
> [[human-approval]], [[human-choice]],  
> [[moderation-guardrail]], [[pll-guardrail]]

---

## Concepts (개념 페이지)

| 파일 | 요약 |
|------|------|
| [concepts/port-color-rules.md](./concepts/port-color-rules.md) | 포트 색상별 의미, 연결 제약 규칙, 불가 조합 |
| [concepts/agent-vs-language-model.md](./concepts/agent-vs-language-model.md) | Agent vs Language Model 선택 기준 |
| [concepts/rag-pipeline.md](./concepts/rag-pipeline.md) | RAG 파이프라인 패턴, Query Rewriting, 멀티 KMS |
| [concepts/guardrail-design.md](./concepts/guardrail-design.md) | Guardrail 설계 원칙, 이중 적용 패턴, 민감도 가이드 |
| [concepts/human-approval-pattern.md](./concepts/human-approval-pattern.md) | Human Approval / Human Choice 패턴, else 토글 동작 |
| [concepts/routing-pattern.md](./concepts/routing-pattern.md) | AI Router vs Human Choice, 조건 작성 가이드, 계층 조합 |
| [concepts/mcp-pattern.md](./concepts/mcp-pattern.md) | MCP 연동 패턴, Stdio/HTTP 모드, 갤러리 12개 서버 |
| [concepts/n8n-mapping.md](./concepts/n8n-mapping.md) | ixi ↔ n8n 전체 노드 매핑, Qdrant RAG 구현 방안 |

---

## Flows (플로우 페이지)

| 파일 | 요약 |
|------|------|
| [flows/current-flow.md](./flows/current-flow.md) | 현재 동작 중인 PPT RAG 플로우 — 5가지 문제점 및 개선안 |
| [flows/flow-security-agent.md](./flows/flow-security-agent.md) | 보안 통합 Agent (5개 솔루션, Mock 서버, Human Approval) |

> 📝 미생성 flow 페이지 (필요 시 생성):  
> [[flow-rag]], [[flow-agent-tool]], [[flow-routing]], [[flow-human-loop]], [[flow-guardrail]], [[flow-mcp]]

---

## Sources (소스 요약 페이지)

| 파일 | 요약 |
|------|------|
| [sources/ixi-enterprise-docs-2026-05-18.md](./sources/ixi-enterprise-docs-2026-05-18.md) | 기존 docs 폴더 전체 요약 — 12개 문서, 핵심 발견 13가지, 포트 제약 UI 검증 완료 |

---

## 미생성 페이지 목록 (`[[링크]]` 참조 존재)

다음 페이지가 참조되었으나 아직 생성되지 않음. 우선순위가 높은 것부터 생성 권장:

| 페이지명 | 참조 위치 | 우선순위 |
|---------|---------|---------|
| [[flow-rag]] | overview.md, rag-pipeline.md | 🔴 높음 |
| [[flow-routing]] | overview.md, routing-pattern.md | 🔴 높음 |
| [[agent]] | 여러 곳 | 🟡 중간 |
| [[kms-retriever]] | 여러 곳 | 🟡 중간 |
| [[api-request]] | 여러 곳 | 🟡 중간 |
| [[flow-agent-tool]] | overview.md | 🟡 중간 |
| [[flow-human-loop]] | overview.md | 🟡 중간 |
| [[flow-guardrail]] | overview.md | 🟡 중간 |
| [[flow-mcp]] | overview.md | 🟢 낮음 |
| 나머지 개별 노드 페이지 | node-catalog-summary.md | 🟢 낮음 |
