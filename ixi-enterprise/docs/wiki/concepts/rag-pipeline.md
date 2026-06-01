# RAG 파이프라인 패턴

**카테고리**: concepts  
**태그**: RAG, KMS, 검색, 지식베이스  
**최종 수정**: 2026-05-18  
**관련 페이지**: [[kms-retriever]], [[document-formatter]], [[language-model]], [[agent-vs-language-model]], [[flow-rag]]

---

## 기본 구성

```
[Chat Input]
     ↓ User Message (파란)
[KMS Retriever]
  Query *: 사용자 입력 연결
  Knowledge *: 지식베이스 선택 (드롭다운)
     ↓ Documents (주황)
[Document Formatter]
     ↓ Result (초록)
[Language Model]
  System Prompt: "아래 문서를 바탕으로 답변하세요."
     ↓ Response (파란 점선)
[Chat Output]
```

---

## KMS 지식베이스

- ixi-enterprise 내 **지식베이스 탭**에서 별도 생성·관리
- PDF 등 파일 업로드 → RAG 인덱싱
- Knowledge 파라미터: 드롭다운으로 선택 (새로고침 버튼 포함)

---

## Document Formatter의 역할

- KMS Retriever의 Documents (주황 포트)를 받아 텍스트 문자열로 변환
- 출력 Result (초록 포트)는 Language Model, Human Approval, Human Choice 등에 연결 가능
- 주황 포트 → 초록 포트로 색상이 바뀜 (파란 포트와 연결 가능해짐)

> ⚠️ KMS Retriever의 Documents는 주황 포트라 Language Model에 직접 연결 불가.  
> 반드시 Document Formatter를 경유해야 한다.

---

## Query Rewriting 패턴 (개선안)

대화체 입력의 검색 품질 향상을 위해 KMS Retriever 앞에 Language Model 삽입:

```
[Chat Input]
     ↓
[Language Model]  ← "사용자 질문을 검색에 최적화된 단어로 재작성하세요"
     ↓
[KMS Retriever]
     ↓
[Document Formatter]
     ↓
[Language Model]  ← 최종 답변 생성
     ↓
[Chat Output]
```

---

## 멀티 KMS 비교 패턴

두 지식베이스를 병렬 검색하여 비교 분석:

```
[Chat Input]
     ├──────────────────────┐
[KMS Retriever A]    [KMS Retriever B]
     ↓                     ↓
[Document Formatter A] [Document Formatter B]
     └──────────┬───────────┘
          [Language Model]  ← "두 문서를 비교하세요"
                ↓
          [Chat Output]
```

---

## n8n 대응

| ixi 노드 | n8n 대응 |
|---------|---------|
| KMS Retriever | Qdrant Vector Store (retrieve mode) |
| Document Formatter | Code 노드 (JS로 직접 구현) |
| KMS 지식베이스 | Qdrant Collection + Azure OpenAI Embeddings |

→ [[n8n-mapping]] 참조
