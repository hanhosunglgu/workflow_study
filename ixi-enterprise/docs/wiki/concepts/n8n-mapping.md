# ixi-enterprise ↔ n8n 노드 매핑

**카테고리**: concepts  
**태그**: n8n, 매핑, 구현  
**최종 수정**: 2026-05-18  
**관련 페이지**: [[rag-pipeline]], [[flow-rag]], [[node-catalog-summary]]

---

## 전체 매핑표

| ixi 노드 | n8n 대응 노드 | 패키지 |
|---------|--------------|--------|
| Chat Input | `chatTrigger` | `@n8n/n8n-nodes-langchain` |
| Chat Output | Chat Trigger 자동응답 | built-in |
| JSON Output | Set 노드 또는 Respond to Webhook | built-in |
| Template Message | `Set` 노드 또는 프롬프트 직접 작성 | built-in |
| Language Model | `chainLlm` | `@n8n/n8n-nodes-langchain` |
| Agent | `agent` | `@n8n/n8n-nodes-langchain` |
| AI Router | `agent` + Switch 노드 조합 | 커스텀 구성 |
| Structured Output | `chainLlm` + JSON 파서 Code 노드 | 커스텀 구성 |
| Simple Calculator Tool | `toolCalculator` | `@n8n/n8n-nodes-langchain` |
| Web Search Tool | `toolSerpApi` / `toolWikipedia` | `@n8n/n8n-nodes-langchain` |
| Youtube Search Tool | HTTP Request → YouTube Data API | `n8n-nodes-base` |
| MCP Connection Tool | `mcpClientTool` (n8n v1.88+) | `@n8n/n8n-nodes-langchain` |
| KOSIS Statistics Tool | HTTP Request → KOSIS OpenAPI | `n8n-nodes-base` |
| API Request | `httpRequest` | `n8n-nodes-base` |
| KMS Retriever | `vectorStoreQdrant` (retrieve mode) | `@n8n/n8n-nodes-langchain` |
| Document Formatter | `Code` 노드 (JS) | built-in |
| Human Approval | `Wait` 노드 + `Form Trigger` | built-in |
| Human Choice | `Wait` 노드 + `Form Trigger` | built-in |
| Moderation Guardrail | HTTP Request → Azure Content Safety API | `n8n-nodes-base` |
| PLL Guardrail | HTTP Request → Azure PII Detection API | `n8n-nodes-base` |

---

## n8n RAG 아키텍처

ixi의 KMS = n8n의 Qdrant + Azure OpenAI Embeddings

```
워크플로 1 (인제스트):
PPTX → 텍스트 추출 → 청킹 → Azure Embeddings → Qdrant 저장

워크플로 2 (채팅 RAG):
Chat Trigger → Qdrant Retriever → Code(Document Formatter) → LLM Chain → 응답
```

---

## n8n 구현 로드맵

| 단계 | 기간 | 목표 |
|------|------|------|
| 1단계 POC | 1~2일 | txt + In-Memory Vector Store로 RAG 채팅 동작 확인 |
| 2단계 안정화 | 3~5일 | Qdrant 영구 저장 + PPTX 자동 인제스트 |
| 3단계 운영화 | 1주 | Guardrail, Human Approval, 멀티턴 대화 추가 |

---

## 사전 확인 필요 사항

> ❓ 미확인: n8n 버전 (MCP Tool은 v1.88+ 필요), Azure OpenAI Credential 등록 여부,  
> `text-embedding-3-small` 모델 배포 여부
