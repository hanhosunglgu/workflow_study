# MCP 연동 패턴

**카테고리**: concepts  
**태그**: MCP, mcp-connection-tool, 외부연동  
**최종 수정**: 2026-05-19  
**관련 페이지**: [[mcp-connection-tool]], [[api-request]], [[flow-mcp]]

---

## MCP(Model Context Protocol) 개요

AI 모델이 외부 서비스/데이터와 표준화된 방식으로 통신하는 프로토콜.

| 방식 | API Request | MCP Connection Tool |
|------|-------------|-------------------|
| 도구 목록 | 고정 (개발자가 지정) | 동적 (MCP 서버가 제공, Agent가 선택) |
| 통신 방식 | HTTP 직접 호출 | MCP 프로토콜 |
| 적합한 경우 | 자체 REST API | 표준 MCP 서버가 존재하는 서비스 |

---

## 연결 모드

| 모드 | 설명 | 사용 상황 |
|------|------|---------|
| **Stdio** | MCP 서버 프로세스와 표준 입출력 통신 | 로컬/사내 서버 |
| **Streamable-HTTP** | HTTP 스트리밍으로 통신 | 원격 서버 |

### 테스트 권장 3선 설정 (2026-05-19 실측)

#### Context7
```
Mode: Stdio
MCP Command: npx -y @upstash/context7-mcp
Environment: 없음 (인증 불필요)
Tool List: resolve-library-id → query-docs (2개, 모두 활성화)
```

#### GitHub
```
Mode: Stdio
MCP Command: npx -y @modelcontextprotocol/server-github
Environment:
  GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
  (GitHub → Settings → Developer settings → Personal access tokens)
```

#### Atlassian (Jira + Confluence)
```
Mode: Stdio
MCP Command: npx -y @modelcontextprotocol/server-atlassian
Environment:
  JIRA_URL:       "https://lgucorp.atlassian.net"   ← 기존 n8n JIRA_BASE_URL 재활용
  JIRA_USERNAME:  "<jira 계정 이메일>"               ← 기존 n8n JIRA_USER_EMAIL 재활용
  JIRA_API_TOKEN: "<API Token>"                      ← 기존 n8n JIRA_API_TOKEN 재활용
  (토큰 발급: https://id.atlassian.com/manage-profile/security/api-tokens)
```

---

## 내장 MCP 갤러리 (12개 서버)

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

## MCP vs API Request 선택 기준

| 상황 | 권장 방식 | 이유 |
|------|---------|------|
| 표준 MCP 서버 존재 (GitHub, Jira 등) | MCP Connection Tool | 동적 도구 목록, 표준화 |
| 자체 REST API만 있는 경우 | API Request | MCP 서버 구축 불필요 |
| 레거시 시스템 (XML, SOAP) | API Request | MCP 미지원 프로토콜 |
| 다수의 API를 동적으로 선택해야 할 때 | MCP Connection Tool | Agent가 도구 자율 선택 |

---

## 보안 고려사항

```
읽기 전용 작업: Guardrail만으로 충분
  Chat Input → Guardrail → Agent(MCP) → Chat Output

쓰기/변경 작업: Human Approval 필수
  Chat Input → Guardrail → Agent(MCP 읽기) → Human Approval
                                             ↓ 승인
                                         Agent(MCP 쓰기) → Chat Output

삭제/중요 변경: Human Approval + Structured Output으로 명확한 작업 내용 표시
```

---

## 사전 확인 필요 사항

> ❓ 미확인: 사내 운영 중인 MCP 서버 목록, 접속 방식, 인증 정보 확보 필요
