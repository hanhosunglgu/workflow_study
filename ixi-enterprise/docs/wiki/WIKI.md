# ixi-enterprise LLM Wiki — Schema

**작성일**: 2026-05-18  
**목적**: LLM이 이 wiki를 어떻게 유지·확장해야 하는지 정의하는 설정 파일

---

## 이 wiki의 역할

ixi-enterprise 플로우 빌더에 대한 지식을 **점진적으로 누적하는 persistent artifact**.  
소스를 추가할 때마다 LLM이 wiki를 업데이트한다. 질문에 대한 좋은 답변도 wiki 페이지로 저장된다.  
사람은 소싱과 방향 결정을 담당하고, LLM은 작성·교차 참조·일관성 유지를 담당한다.

---

## 디렉터리 구조

```
wiki/
├── WIKI.md          ← 이 파일 (schema / 운영 규칙)
├── index.md         ← 전체 페이지 카탈로그 (LLM이 매 ingest마다 갱신)
├── log.md           ← append-only 작업 이력
├── overview.md      ← wiki 전체 합성 요약 (최상위 진입점)
│
├── entities/        ← 노드, 솔루션, 시스템 등 고유 개체 페이지
├── concepts/        ← 패턴, 원칙, 설계 철학 등 개념 페이지
├── flows/           ← 구체적인 플로우 구성도 및 분석 페이지
└── sources/         ← 원본 소스 요약 페이지 (불변 원본의 LLM 요약)
```

---

## 페이지 포맷 규칙

### 모든 페이지 공통 헤더

```markdown
# [페이지 제목]

**카테고리**: entities | concepts | flows | sources  
**태그**: [관련 태그, 쉼표 구분]  
**최종 수정**: YYYY-MM-DD  
**관련 페이지**: [[페이지명]], [[페이지명]]
```

### 교차 참조

- 다른 wiki 페이지를 언급할 때는 `[[페이지명]]` 형식 사용
- 새 개념/개체가 등장하면 해당 페이지가 없어도 `[[페이지명]]` 링크 작성 (추후 생성 표시)

### 모순/미확인 표기

- 소스 간 충돌: `> ⚠️ 모순: [내용] — [출처A] vs [출처B]`
- 미검증 정보: `> ❓ 미확인: [내용]`
- 구버전 정보: `> 🕐 구버전: [내용] (이후 [출처]에서 변경됨)`

---

## Operations

### Ingest (새 소스 추가)

1. `sources/` 에 소스 요약 페이지 작성
2. 소스에서 등장하는 entities → `entities/` 페이지 생성 또는 업데이트
3. 소스에서 등장하는 concepts → `concepts/` 페이지 생성 또는 업데이트
4. 관련 flows가 있으면 `flows/` 업데이트
5. `index.md` 갱신
6. `log.md`에 항목 추가: `## [YYYY-MM-DD] ingest | [소스명]`
7. `overview.md` 필요시 업데이트

### Query (질문 답변)

1. `index.md` 읽어 관련 페이지 파악
2. 관련 페이지 읽고 답변 합성
3. 유의미한 답변은 `concepts/` 또는 `flows/` 페이지로 저장
4. `log.md`에 항목 추가: `## [YYYY-MM-DD] query | [질문 요약]`

### Lint (wiki 건강 점검)

주기적으로 수행:
- 교차 참조 없는 orphan 페이지 탐지
- 링크만 있고 페이지가 없는 `[[미생성]]` 탐지
- 소스 간 모순 재확인
- 새로 조사할 질문 제안
- `log.md`에 항목 추가: `## [YYYY-MM-DD] lint | 점검 결과 요약`

---

## 이 wiki의 도메인 범위

- **ixi-enterprise**: 사내 AI 플로우 빌더 — 노드, 포트, 연결 규칙
- **구현 플로우**: RAG, Agent+Tool, 라우팅, Human-in-the-Loop, Guardrail, MCP
- **n8n 대응**: ixi 노드 ↔ n8n 노드 매핑
- **보안 Agent**: 5개 보안 솔루션 Mock 서버 연동 설계
- **설계 원칙**: 포트 색상 규칙, 노드 선택 기준, Guardrail 배치 원칙 등

---

## 모델 표기 규칙

이 wiki 전체에서 모델은 `azure_openai:gpt-4.1-mini` 형식을 표준으로 사용.  
(`azure_openai/gpt-4.1-mini` 형식은 구버전 표기 — 사용 금지)
