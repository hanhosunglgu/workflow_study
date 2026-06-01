# 미확인 사항 및 추가 필요 정보

**작성일**: 2026-05-15  
**최종 수정**: 2026-05-18 (UI 검증으로 확인된 항목 상태 업데이트)  
**목적**: 추가 분석/개발 진행 전 확인이 필요한 항목 정리

---

## 우선순위별 미확인 사항

### 🔴 높음 (개발 착수 전 필수)

| # | 항목 | 왜 필요한가 | 확인 방법 |
|---|------|------------|----------|
| 1 | **KMS 대체 방안 확정** | Qdrant vs Supabase vs In-Memory 선택 필요 | 사내 보안 정책 확인, 인프라 담당자 협의 |
| 2 | **Azure OpenAI 엔드포인트 정보** | n8n Credential 등록에 필요 | Azure Portal → OpenAI 리소스 → 키 및 엔드포인트 |
| 3 | **Azure Embedding 모델 배포 여부** | 인제스트 파이프라인 임베딩 단계에 필요 | Azure Portal에서 `text-embedding-3-small` 또는 `ada-002` 배포 확인 |
| 4 | **노드 간 데이터 스키마** | 연동 개발 시 입출력 형식 확인 필요 | ixi-enterprise 개발팀 문서 또는 소스 확인 |

### 🟡 중간 (2단계 개발 전 필요)

| # | 항목 | 왜 필요한가 | 확인 방법 |
|---|------|------------|----------|
| 5 | **PPTX 처리 방식 확정** | 인제스트 파이프라인 설계 방향이 달라짐 | LibreOffice 설치 가능 여부, Azure Document Intelligence 사용 가능 여부 |
| 6 | **KMS Knowledge ID 형식** | KMS Retriever의 `Knowledge` 파라미터 형식 | ixi 플랫폼 관리자 확인 |
| 7 | **MCP 서버 목록** | MCP Connection Tool 활용 범위 파악 | 사내 MCP 서버 운영 현황 |
| 13 | **PLL Guardrail Azure API Key 등록 방법** | PLL Guardrail 사용 시 Azure Language Service API Key 및 엔드포인트 등록 필요 — 미등록 시 `401 Access denied` 오류 발생 (2026-05-18 확인) | ixi-enterprise Settings > Credentials 또는 My Secrets 에서 등록 방법 확인 |

### 🟢 낮음 (3단계 운영화 전 필요)

| # | 항목 | 왜 필요한가 | 확인 방법 |
|---|------|------------|----------|
| 9 | **Human Approval UI 채널** | 승인 요청이 어느 채널(Teams/이메일/웹)로 가는지 | ixi 플랫폼 UX 확인 |
| 10 | **KOSIS API 연동 방식** | 공개 API Key vs 사내 프록시 여부 | KOSIS OpenAPI 포털 또는 담당자 확인 |
| 11 | **멀티턴 대화 세션 관리 방식** | Agent에 별도 context 포트 없음 — MCP 메모리 Tool 또는 외부 세션 관리 방식 검토 필요 | ixi-enterprise 세션 관리 스펙 |

---

## ✅ 확인 완료 항목 (2026-05-18 UI 검증)

| # | 항목 | 확인 결과 |
|---|------|---------|
| 8 | **Moderation/PLL Guardrail 실패 처리** | Guardrail 통과 시 Response 포트로 출력. 실패 시 플로우 중단 (상세 분기 스펙은 미공개). Input 포트 연결 가능 노드: Agent / Language Model / PLL Guardrail / Moderation Guardrail만 허용 — Chat Input 직접 연결 불가 확인 |
| 12 | **Structured Output 스키마 이름 제약** | 스키마 이름은 `^[a-zA-Z0-9_-]+$` 패턴만 허용. 한글/공백 포함 시 `Error code: 400 - invalid_value` 발생 (2026-05-18 확인) |
| 14 | **JSON Output ↔ Chat Output 상호 배타적** | 플로우에 JSON Output을 추가하면 Chat Output이 비활성화됨. 두 노드 동시 사용 불가 — 출력 방식 하나만 선택 (2026-05-18 확인) |
| 15 | **Language Model Response → Chat Output 연결 방향** | Language Model Response 포트에서 드래그 시 Chat Output이 목록에 없음. Chat Output Input 포트에서 드래그 시 Language Model 선택 가능 — **Chat Output 쪽에서 연결 시작**해야 함 (2026-05-18 확인) |
| 16 | **Template Message INPUT 컴포넌트 여부** | Template Message는 INPUT 컴포넌트로 인식되지 않음. 단독 사용 시 "단 하나의 INPUT 컴포넌트는 필수입니다 (현재 개수 : 0개)" 오류 발생 — Chat Input으로 대체 (2026-05-18 확인) |
| 17 | **Structured Output → Document Formatter 연결** | 포트 색상이 동일(주황)해도 런타임에서 `'str' object has no attribute 'page_content'` 오류 발생. Structured Output Result는 JSON 문자열이고 Document Formatter는 Document 객체 배열을 기대 — JSON Output으로만 연결할 것 (2026-05-18 확인) |
| 18 | **Human Approval 출력 → Chat Output 직접 연결** | 양방향 모두 불가. Human Approval 출력 포트 연결 가능 노드: Agent / Language Model / AI Router / Human Approval / Human Choice / KMS Retriever / Structured Output — Chat Output 직접 연결 불가 (2026-05-18 확인) |
| 19 | **Chat Input → Guardrail 직접 연결** | 불가. Guardrail Input 포트는 Agent / Language Model / PLL Guardrail / Moderation Guardrail만 허용. Chat Input 연결 시 연결 가능 노드 목록에 Guardrail 없음 (2026-05-18 확인) |

---

## 현재 플로우에서 확인된 미완성 항목

| 항목 | 현재 상태 | 영향 |
|------|----------|------|
| Agent Tools 포트 | 미연결 (빨간 점 — 선택 포트) | 동작은 하지만 불필요한 ReAct 루프 실행 |
| 멀티턴 대화 히스토리 | 미적용 (Agent에 별도 context 포트 없음) | 대화 히스토리 누적 미지원 |
| System Prompt | 일부만 확인 (`...focused on Question~`) | 요약 품질에 직접 영향 |
| Query Rewriting | 없음 | 검색 품질 저하 가능 |
| Guardrail | 없음 (PLL Guardrail API Key 미등록) | 입력 안전 검사 미적용 |

---

## 전체 워크플로 JSON 확보 필요

현재는 스크린샷으로만 분석했기 때문에 아래 정보가 불명확합니다:

- 노드 간 정확한 연결 맵핑 (어떤 포트 → 어떤 포트)
- 각 노드의 세부 파라미터 값 전체
- Document Formatter → Agent 연결 방식 (Input vs System Prompt 내 변수)
- 플로우 전체 실행 조건 및 에러 처리

**요청**: ixi-enterprise 플로우 JSON 파일 또는 추가 스크린샷(노드 설정 패널 확대) 공유

---

## n8n 구현 전 확인 필요한 n8n 환경 정보

| 항목 | 확인 필요 내용 |
|------|--------------|
| n8n 버전 | MCP Tool 노드는 v1.88+에서만 지원 |
| LangChain 노드 활성화 여부 | `@n8n/n8n-nodes-langchain` 패키지 설치 확인 |
| Docker 네트워크 | n8n ↔ Qdrant 컨테이너 통신 가능한지 |
| Azure OpenAI Credential | n8n에 등록되어 있는지 |
| 외부 네트워크 접근 | Web Search Tool 사용 시 인터넷 접근 가능한지 |
