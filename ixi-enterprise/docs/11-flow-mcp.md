# 플로우 카테고리 6: MCP 확장

**작성일**: 2026-05-15  
**최종 수정**: 2026-05-19 (MCP 갤러리 전체 서버 목록 보강, 테스트 권장 3선 추가)  
**포함 플로우**: 6-1 MCP 연결 통합 Agent

---

## 6-1. MCP 연결 통합 Agent

### 개요

| 항목 | 내용 |
|------|------|
| 난이도 | ⭐⭐⭐ 복잡 |
| 핵심 노드 | Chat Input → Agent (Context7 + GitHub + Atlassian MCP Connection) → Chat Output |
| 구현 예상 시간 | 3~5일 (사내 MCP 서버 운영 전제) |
| 현재 상태 | 🔲 미구현 |
| 전제 조건 | 사내 MCP 서버 목록 및 접속 정보 확보 필요 |

---

### MCP(Model Context Protocol) 개요

```
MCP는 AI 모델이 외부 서비스/데이터와 표준화된 방식으로 통신하는 프로토콜.

일반 API Request와의 차이:
  API Request: 특정 엔드포인트를 직접 호출 (정적)
  MCP Tool:    MCP 서버가 제공하는 도구 목록을 동적으로 조회 후 Agent가 선택 (동적)

MCP 연결 모드:
  - Stdio:           MCP 서버 프로세스와 표준 입출력으로 통신 (로컬/사내 서버)
  - Streamable-HTTP: HTTP 스트리밍으로 통신 (원격 서버)
```

---

### 플로우 구성도

```
[MCP Connection Tool — Context7]     ─┐
[MCP Connection Tool — GitHub MCP]   ─┤ Tool 포트(빨간) → Agent Tools에 연결
[MCP Connection Tool — Atlassian]    ─┘

[Chat Input]
     │ User Message (파란)
     ▼
[Agent]
  ⚠️ Guardrail 필요 시: Agent → PLL/Moderation Guardrail 순서로 배치
     (Chat Input → Guardrail 직접 연결 불가 — Agent 또는 Language Model 경유 필수)
  System Prompt:
    "당신은 사내 시스템 통합 AI 어시스턴트입니다.
     Context7로 공식 문서를 조회하고, GitHub으로 코드 저장소를 관리하며,
     Atlassian(Jira/Confluence)으로 프로젝트 및 문서를 처리하세요.
     사용자의 요청을 분석하여 적절한 도구를 선택하고 실행하세요."
  Jailbreak Check: ON
  Model: azure_openai:gpt-4.1-mini
     │ Response (파란 점선)
     ▼
[Chat Output]
```

> ⚠️ **Guardrail 사용 시 연결 순서 주의**  
> Chat Input → (PLL/Moderation Guardrail) 직접 연결 불가.  
> Guardrail을 사용하려면 `Chat Input → Agent → PLL Guardrail → ...` 순서로 배치.  
> PLL Guardrail은 Azure Language Service API Key 등록 필수 — 미등록 시 `401 Access denied` 오류.

---

### 사내 MCP 서버 활용 시나리오

#### Context7 MCP 연동

| 요청 | Agent 동작 |
|------|-----------|
| "React useEffect 공식 사용법 알려줘" | Context7 → React 공식 문서 조회 → 요약 |
| "Next.js 14 App Router 마이그레이션 가이드 찾아줘" | Context7 → Next.js 문서 조회 |
| "Tailwind CSS flex 레이아웃 예제 보여줘" | Context7 → Tailwind 문서 조회 → 코드 예제 반환 |
| "Express.js 미들웨어 작성 패턴 설명해줘" | Context7 → Express 공식 패턴 조회 → 설명 |

#### GitHub MCP 연동

| 요청 | Agent 동작 |
|------|-----------|
| "WBS_Check 저장소의 최근 PR 목록 보여줘" | GitHub MCP → PR 목록 조회 |
| "이번 주 커밋한 사람들 알려줘" | GitHub MCP → 커밋 이력 조회 |
| "main 브랜치의 README 내용 요약해줘" | GitHub MCP → 파일 내용 조회 → Language Model 요약 |
| "열린 이슈 중 버그 레이블 달린 것들 목록화해줘" | GitHub MCP → 이슈 필터 조회 |

#### Atlassian MCP 연동 (Jira / Confluence)

| 요청 | Agent 동작 |
|------|-----------|
| "현재 스프린트 진행 현황 알려줘" | Atlassian MCP → Jira 스프린트 조회 |
| "내 담당 미완료 티켓 목록 보여줘" | Atlassian MCP → Jira 이슈 쿼리 |
| "WBS-123 티켓 상태 업데이트해줘" | Atlassian MCP → Jira 티켓 상태 변경 + Human Approval 권장 |
| "API 명세서 최신 버전 찾아줘" | Atlassian MCP → Confluence 페이지 검색 |
| "온보딩 가이드 내용 요약해줘" | Atlassian MCP → Confluence 페이지 조회 → 요약 |
| "이 내용을 위키 페이지에 추가해줘" | Atlassian MCP → Confluence 페이지 업데이트 + Human Approval 권장 |

---

### MCP 보안 고려사항

```
MCP는 강력한 시스템 접근 권한을 가질 수 있으므로 반드시 보안 레이어 적용:

1. 읽기 전용 작업: Jailbreak Check ON으로 충분
   [Chat Input] → [Agent(Jailbreak Check: ON, MCP Tools)] → [Chat Output]

2. 쓰기/변경 작업: Human Approval 필수
   [Chat Input]
        ↓
   [Agent(MCP 읽기 — 변경 내용 확인)]
        ↓
   [Human Approval]
        ├─ 승인 → [Agent(MCP 쓰기 실행)] → [Chat Output]
        └─ 거부 → 플로우 즉시 종료

3. 삭제/중요 변경: Human Approval 필수 + 작업 내용 명확히 표시
   Human Approval Target Message에 변경 대상/내용 상세 전달 권장
```

> ⚠️ **Human Approval → Chat Output 직접 연결 불가**  
> Human Approval 출력은 Agent / Language Model / AI Router 등을 경유해야 Chat Output 연결 가능.

### MCP Connection Tool 설정 가이드

#### Context7

```
연결 모드: Streamable-HTTP
MCP Server URL: https://mcp.context7.com/mcp
Environment: (없음 — 인증 불필요)

사전 준비: 없음 (공개 서버, 즉시 사용 가능)
```

#### GitHub

```
연결 모드: Stdio
MCP Command: npx -y @modelcontextprotocol/server-github
Environment:
  GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"

사전 준비:
  1. GitHub → Settings → Developer settings → Personal access tokens → Generate new token
  2. 필요 권한: repo (읽기/쓰기), read:org (조직 정보 조회 시)
  3. 쓰기 작업(PR 생성, 이슈 변경 등) 사용 시 Human Approval 적용 권장
```

#### Atlassian (Jira + Confluence)

```
연결 모드: Stdio
MCP Command: npx -y @modelcontextprotocol/server-atlassian
Environment:
  ATLASSIAN_URL:      "https://yoursite.atlassian.net"
  ATLASSIAN_USERNAME: "user@company.com"
  ATLASSIAN_API_TOKEN: "xxxxxxxxxxxxxxxxxxxx"

사전 준비:
  1. https://id.atlassian.com/manage-profile/security/api-tokens 에서 API Token 발급
  2. ATLASSIAN_URL은 Cloud Site URL (도메인 형식: yoursite.atlassian.net)
  3. 티켓 상태 변경 / Confluence 페이지 수정 시 Human Approval 적용 필수
```

### MCP 갤러리 내장 서버 (12개)

ixi-enterprise MCP Connection Tool 갤러리에 기본 제공되는 서버 목록:

| 서버 | 용도 |
|------|------|
| Atlassian | Jira / Confluence 연동 |
| Fetch | 웹 페이지 콘텐츠 수집 및 변환 |
| Tavily | 실시간 웹 검색 및 데이터 추출 |
| Bright Data | 웹 크롤링 및 차단 우회 검색 |
| Browserbase | 브라우저 자동화 (스크린샷, 웹 조작) |
| Context7 | 라이브러리/프레임워크 공식 문서 조회 |
| Exa Search | AI 기반 웹 검색 |
| Notion | 노션 워크스페이스 연동 |
| GitHub | 코드 저장소 연동 |
| Google Maps | 위치 정보 및 지도 기능 |
| Mem0 Memory | 사용자별 대화 맥락 기억 |
| Supabase | Supabase DB / Storage 연동 |

---

### 테스트 권장 MCP 3선

실제 구현 전 기능 검증용으로 우선 테스트를 권장하는 3개:

| 서버 | 토큰 발급 | 설정 복잡도 | 테스트 시나리오 |
|------|---------|-----------|----------------|
| **Context7** | 불필요 | ⭐ 낮음 | "React useEffect 공식 문서 요약해줘" |
| **GitHub** | Personal Access Token | ⭐⭐ 보통 | "main 브랜치 최근 커밋 목록 보여줘" |
| **Atlassian** | API Token + Cloud URL | ⭐⭐⭐ 높음 | "현재 스프린트 Jira 티켓 목록 알려줘" |

> ⚠️ **Atlassian 사전 준비**: Atlassian Cloud 계정, API Token (`id.atlassian.com`에서 발급), Cloud Site URL (`https://yoursite.atlassian.net`) 필요.

---

### MCP vs API Request 선택 기준

| 상황 | 권장 방식 | 이유 |
|------|---------|------|
| 표준 MCP 서버 존재 (GitHub, Jira 등) | MCP Connection Tool | 동적 도구 목록, 표준화된 통신 |
| 자체 REST API만 있는 경우 | API Request (Tool 모드 ON) | MCP 서버 구축 불필요 |
| 레거시 시스템 (XML, SOAP 등) | API Request (Tool 모드 ON) | MCP 미지원 프로토콜 |
| 다수의 API를 동적으로 선택해야 할 때 | MCP Connection Tool | Agent가 도구를 자율 선택 |

---

## MCP 확장 로드맵

```
1단계: Context7 MCP 연동 (토큰 불필요, 즉시 테스트 가능)
  → 공식 문서 기반 코드 생성, 라이브러리 API 조회 자동화

2단계: GitHub MCP 연동
  → 코드 리뷰 보조, PR 요약, 이슈 트래킹

3단계: Atlassian MCP 연동 (Jira + Confluence 통합)
  → 스프린트 관리, 티켓 자동 업데이트, 위키 검색 통합

4단계: 사내 커스텀 MCP 서버 개발
  → 사내 전용 데이터/시스템을 MCP 프로토콜로 노출
  → Agent가 사내 모든 시스템을 통합 조작 가능
```

> ⚠️ **사전 확인 필요**: 사내 운영 중인 MCP 서버 목록, 접속 방식, 인증 정보 (`04-open-questions.md` 항목 7 참조)
