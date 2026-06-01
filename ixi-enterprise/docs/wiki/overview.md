# ixi-enterprise Wiki — 전체 개요

**카테고리**: overview  
**태그**: ixi-enterprise, 전체요약, 진입점  
**최종 수정**: 2026-05-19  
**관련 페이지**: [[index]], [[node-catalog-summary]], [[rag-pipeline]], [[routing-pattern]]

---

## ixi-enterprise란

사내 AI 플로우 빌더. 노드를 연결해 AI 워크플로를 시각적으로 구성한다.  
백엔드는 LangChain 기반, 모델은 Azure OpenAI(`azure_openai:gpt-4.1-mini` 등)를 사용.

---

## 노드 전체 구조 (20개, 2026-05-18 UI 검증 완료)

| 카테고리 | 노드 |
|---------|------|
| I/O | [[chat-input]], [[chat-output]], [[json-output]], [[template-message]] |
| AI/LLM | [[language-model]], [[agent]], [[ai-router]], [[structured-output]] |
| Tools | [[simple-calculator-tool]], [[web-search-tool]], [[youtube-search-tool]], [[mcp-connection-tool]], [[kosis-statistics-tool]], [[api-request]] |
| RAG | [[kms-retriever]], [[document-formatter]] |
| Human-in-the-Loop | [[human-approval]], [[human-choice]] |
| Guardrail | [[moderation-guardrail]], [[pll-guardrail]] |

---

## 포트 색상 규칙 요약

| 색상 | 선 종류 | 의미 | 예시 |
|------|--------|------|------|
| 파란 실선 | 실선 | 일반 데이터 연결 | Chat Input → Language Model |
| 파란 점선 | 점선 | 선택적 출력 | Language Model Response (출력) |
| 파란 파선 | 파선 | Guardrail 출력 | PLL/Moderation Response 포트 |
| 빨간 | 실선 | 필수 또는 Tool 전용 | Agent Tools, Document Formatter Documents |
| 주황 | 실선 | 문서/RAG 데이터 | KMS Retriever Documents → Document Formatter |
| 초록 | 실선 | 결과 출력 | Document Formatter Result, Tool List |

### 주요 연결 제약 (UI 검증)

| 제약 | 내용 |
|------|------|
| Chat Input → Guardrail | 직접 연결 불가 — Language Model(패스스루) 또는 Agent 경유 필수 |
| Human Approval → Chat Output | 직접 연결 불가 (양방향 모두) — Agent/Language Model 경유 필수 |
| JSON Output ↔ Chat Output | 상호 배타적 — 동시 사용 불가 |
| Structured Output → Document Formatter | 포트 색상 동일(주황)하나 런타임 오류 발생 — JSON Output으로만 연결 |
| Language Model → Chat Output 연결 방향 | Chat Output Input 포트에서 드래그 시작 필요 (LM Response에서 드래그 시 목록에 없음) |
| AI Router else(OFF) → Chat Output | 직접 연결 불가 — Language Model 경유 필수 |

→ 상세: [[port-color-rules]]

---

## 핵심 설계 원칙 요약

- **단순 LLM 응답** → [[language-model]] (Tool 불필요 시 [[agent]] 대신 사용)
- **도구 호출 필요** → [[agent]] + Tool 연결
- **자동 분기** → [[ai-router]] (LLM이 판단)
- **수동 분기** → [[human-choice]] (사람이 선택)
- **승인 게이트** → [[human-approval]] (데이터 변경·발송 직전)
- **RAG** → [[kms-retriever]] → [[document-formatter]] → LLM
- **안전 레이어** → [[pll-guardrail]] → [[moderation-guardrail]] (입력 단계에 배치)
- **MCP 확장** → [[mcp-connection-tool]] (GitHub, Jira, Confluence 등)

→ 상세 원칙: [[guardrail-design]], [[agent-vs-language-model]], [[human-approval-pattern]]

---

## 현재 동작 중인 플로우

```
Chat Input → KMS Retriever → Document Formatter → Agent → Chat Output
             (PPT 업로드)     (청크 포매팅)        (azure_openai:gpt-4.1-mini)
```

문제점: Tools 미연결, 멀티턴 히스토리 없음, Guardrail 없음  
→ 상세: [[current-flow]]

---

## 구현 로드맵 요약

| 단계 | 플로우 | 문서 |
|------|--------|------|
| 즉시 구현 가능 | 1-1 문서 Q&A, 5-2 개인정보 비식별화 | [[flow-rag]], [[flow-guardrail]] |
| 1~2일 | 2-2 사내 시스템 연동, 3-1 AI 라우터, 4-1 승인 플로우 | [[flow-agent-tool]], [[flow-routing]], [[flow-human-loop]] |
| 3~5일 | 2-3 하이브리드, 4-2 멀티스텝 승인, 6-1 MCP Agent | [[flow-mcp]] |
| 별도 설계 | 보안 통합 Agent (5개 솔루션 연동) | [[flow-security-agent]] |

---

## n8n 대응 요약

ixi-enterprise를 n8n으로 구현 시 핵심 매핑:

| ixi 노드 | n8n 대응 |
|---------|---------|
| KMS Retriever | Qdrant Vector Store (retrieve mode) |
| Document Formatter | Code 노드 (JS) |
| Agent | `@n8n/n8n-nodes-langchain` agent |
| Human Approval | Wait 노드 + Form Trigger |
| Moderation Guardrail | HTTP Request → Azure Content Safety API |

→ 전체 매핑: [[n8n-mapping]]
