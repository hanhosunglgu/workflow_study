# 현재 동작 플로우 분석

**카테고리**: flows  
**태그**: 현재플로우, RAG, 개선필요  
**최종 수정**: 2026-05-18  
**관련 페이지**: [[rag-pipeline]], [[agent-vs-language-model]], [[guardrail-design]], [[flow-rag]]

---

## 플로우 구성

```
Chat Input → KMS Retriever → Document Formatter → Agent → Chat Output
             (PPT 업로드)     (청크 포매팅)        (azure_openai:gpt-4.1-mini)
```

### 노드별 설정

| 노드 | 설정값 |
|------|--------|
| KMS Retriever | Knowledge: "국내서비 마냥" (PPT 업로드 지식베이스) |
| Agent | Model: `azure_openai:gpt-4.1-mini`, Tools: 미연결, Jailbreak Check: OFF |

---

## 문제점 및 개선안

| # | 문제 | 원인 | 개선안 |
|---|------|------|--------|
| 1 | Agent에 Tools 미연결 | 빨간 점(선택 포트) 미연결 — 불필요한 ReAct 루프 실행 | Language Model 노드로 교체 |
| 2 | Query Rewriting 없음 | 사용자 원문이 그대로 KMS 검색 쿼리로 사용 | KMS Retriever 앞에 Language Model 추가 |
| 3 | 멀티턴 대화 히스토리 없음 | Agent에 별도 context 포트 없음 | MCP 메모리 Tool 또는 외부 세션 관리 검토 |
| 4 | Guardrail 없음 | 사용자 입력이 바로 KMS 검색 및 LLM으로 전달 | PLL Guardrail → Moderation Guardrail 추가 |
| 5 | 시스템 프롬프트 미완성 | `"Role: You are an AI assistant focused on Question~"` (미완성) | 요약 전용 프롬프트 작성 |

---

## 단기 개선 플로우

```
[Chat Input]
     ↓
[Language Model]         ← ⚠️ 패스스루: Chat Input은 PLL Guardrail에 직접 연결 불가
  System Prompt: 없음 (입력 그대로 전달)
     ↓
[PLL Guardrail]          ← 개인정보 필터 추가
     ↓
[Language Model]         ← Query Rewriting
  "사용자 질문을 검색에 최적화된 단어로 재작성하세요"
     ↓
[KMS Retriever]
     ↓
[Document Formatter]
     ↓
[Language Model]         ← Agent 교체 (Tool 불필요)
  "다음 문서를 한국어로 요약하세요. 핵심 내용 3가지를 bullet point로 정리하세요."
     ↓
[Chat Output]
```

> ⚠️ **Guardrail 연결 필수 패턴**: Guardrail Input은 Agent / Language Model / PLL Guardrail / Moderation Guardrail만 허용.  
> Chat Input은 직접 연결 불가 — Language Model(패스스루) 또는 Agent를 앞에 배치해야 함.  
> ⚠️ **PLL Guardrail 사전 조건**: Azure Language Service API Key 등록 필수. 미등록 시 `401 Access denied` 발생.  
> → [[port-color-rules]], [[guardrail-design]] 참조
