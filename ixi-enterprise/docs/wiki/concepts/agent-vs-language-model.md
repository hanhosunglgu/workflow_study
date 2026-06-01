# Agent vs Language Model 선택 기준

**카테고리**: concepts  
**태그**: agent, language-model, 설계원칙, 노드선택  
**최종 수정**: 2026-05-18  
**관련 페이지**: [[agent]], [[language-model]], [[rag-pipeline]], [[flow-rag]]

---

## 핵심 차이

| 항목 | Language Model | Agent |
|------|---------------|-------|
| 동작 방식 | 입력 → LLM → 응답 (1회) | ReAct 루프 (Think → Act → Observe 반복) |
| Tool 연결 | 불가 | 가능 (Tools 포트) |
| 오버헤드 | 낮음 | 높음 (루프 실행) |
| 용도 | 단순 LLM 응답, 요약, 번역 | 도구 호출이 필요한 복합 작업 |
| Jailbreak Check | 없음 | 토글로 ON/OFF |
| 프롬프트 갤러리 | 없음 | 있음 (10개 태그, 5개 샘플) |

---

## 언제 Language Model을 써야 하나

- RAG 결과를 받아서 요약·번역·포매팅할 때
- Tool이 전혀 필요 없는 단순 LLM 응답
- Query Rewriting (KMS 검색 전 쿼리 최적화)
- Structured Output 대신 자유 텍스트 응답이 필요할 때

```
✅ Chat Input → KMS Retriever → Document Formatter → Language Model → Chat Output
❌ Chat Input → KMS Retriever → Document Formatter → Agent (Tool 없음) → Chat Output
   (Agent는 Tool 없이도 동작하지만 불필요한 ReAct 루프 오버헤드 발생)
```

---

## 언제 Agent를 써야 하나

- Web Search, KOSIS, API Request 등 Tool 호출이 필요할 때
- 어떤 Tool을 몇 번 쓸지 LLM이 동적으로 판단해야 할 때
- 복합 리서치 (여러 소스를 순서 없이 조합)
- 사내 시스템 API를 자연어로 조작할 때

---

## 현재 플로우의 문제

현재 동작 플로우에서 Agent에 Tools가 미연결 상태. 단순 RAG 요약 용도이므로 Language Model로 교체가 적합.  
→ [[current-flow]] 참조
