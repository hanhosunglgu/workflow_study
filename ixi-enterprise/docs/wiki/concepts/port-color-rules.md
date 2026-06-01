# 포트 색상 규칙

**카테고리**: concepts  
**태그**: 포트, 연결, UI규칙  
**최종 수정**: 2026-05-18  
**관련 페이지**: [[node-catalog-summary]], [[rag-pipeline]], [[agent]]

---

## 색상별 의미

| 색상 | 의미 | 예시 |
|------|------|------|
| **파란** | 일반 데이터 연결 | Chat Input → Language Model |
| **빨간** | 필수 또는 Tool 전용 연결 | Agent Tools 포트, Document Formatter Documents 포트 |
| **주황** | 문서/RAG 데이터 연결 | KMS Retriever Documents → Document Formatter |
| **초록** | 결과 출력 | Document Formatter Result, Structured Output Result, Tool List |

---

## 포트 형태별 의미

| 형태 | 의미 |
|------|------|
| 실선 포트 | 일반 연결 |
| 점선 포트 | 선택적 연결 또는 출력 |
| 점(●) 포트 | Tool 전용 연결 포트 |

---

## 중요 연결 규칙

### RAG 체인 — 주황 포트로만 연결

```
KMS Retriever [Documents 주황] → Document Formatter [Documents * 주황]
Document Formatter [Result 초록] → Language Model / Agent / Human Approval ...
```

### Tool 체인 — 초록(Tool List)과 빨간(Tool) 구분

```
Tool 노드 [Tool List 초록] → Agent [Tools 빨간]
Tool 노드 [Tool 빨간] → 다른 Tool 노드 [Tool 빨간]  ← 체이닝
```

### Guardrail 연결 제약

```
❌ Chat Input → Guardrail (직접 연결 불가)
✅ Chat Input → Language Model / Agent → Guardrail
✅ Guardrail Response → KMS Retriever (연결 가능)
```

---

## 연결 불가 조합 (검증된 사실)

- Chat Input / Template Message → Moderation Guardrail (직접 연결 불가)
- Chat Input / Template Message → PLL Guardrail (직접 연결 불가)
- KMS Retriever Documents → Language Model (주황↔파란 불일치, Document Formatter 경유 필요)
