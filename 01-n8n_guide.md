# n8n 완전 가이드

---

## 1. n8n이란?

n8n은 오픈소스 기반의 노코드/로우코드 워크플로우 자동화 플랫폼이다. 400개 이상의 노드를 활용해 300개 이상의 앱·서비스를 연동하고, 복잡한 자동화 파이프라인을 시각적으로 구성할 수 있다.

### 핵심 특징

- 드래그 앤 드롭 방식의 시각적 워크플로우 설계
- JavaScript / Python 코드 노드로 고급 로직 구현 가능
- Fair-Code 오픈소스 라이선스 (내부 사용 무제한)
- 셀프호스팅 지원으로 데이터 완전 통제 가능

### 배포 방식 3가지 분류

n8n은 크게 세 가지 방식으로 사용할 수 있다.

#### A. 오픈소스 직접 설치 (Self-Hosted)

n8n 오픈소스를 내 서버에 직접 설치하고 운영하는 방식.

```bash
# Docker (권장)
docker run -it --rm -p 5678:5678 -v n8n_data:/home/node/.n8n docker.n8n.io/n8nio/n8n

# npm
npm install -g n8n && n8n start
```

- 비용: 서버비만 (Hetzner $5/월, DigitalOcean $6/월 수준)
- 실행 횟수 제한 없음, 완전한 데이터 통제
- 업데이트·보안 패치를 직접 관리해야 함

#### B. PaaS 플랫폼 원클릭 배포

플랫폼이 n8n 오픈소스를 패키징해서 버튼 클릭만으로 배포해주는 방식. 인프라는 해당 플랫폼이 소유한다.

| 플랫폼 | 배포 방식 | 비용 | 특징 |
|--------|---------|------|------|
| **Railway** | 원클릭 템플릿 | $5~15/월 | PostgreSQL 자동 포함, 가장 간편 |
| **Render** | Docker 배포 | $7~40/월 | 무료 티어 있으나 15분 비활성 시 종료 |
| **DigitalOcean** | 1-Click App | $6/월~ | 기본 설치만 제공, 이후 직접 관리 |
| **Koyeb** | 원클릭 템플릿 | $10/월~ | 글로벌 배포 |
| **Fly.io** | CLI 배포 | $10/월~ | 글로벌, 세밀한 제어 |
| **Elestio** | 완전 관리형 | $11/월~ | 백업·업데이트 모두 대신 관리 |
| **Heroku** | Deploy 버튼 | $16/월~ | 가성비 낮아 비추천 |

> **Coolify / CapRover**: 내 VPS에 셀프호스팅 PaaS를 올리고, 그 위에서 n8n을 원클릭 배포하는 방식. A와 B의 중간 형태.

#### C. n8n 공식 클라우드 (SaaS)

n8n.io가 직접 운영하는 서비스. 설치 없이 가입만 하면 바로 사용한다.

| 플랜 | 비용 | 실행 횟수 |
|------|------|---------|
| Starter | $24/월 | 2,000회 |
| Pro | $60/월 | 10,000회 |
| Enterprise | 견적 | 무제한 |

#### 방식별 비교

| 항목 | A. 직접 설치 | B. PaaS 원클릭 | C. 공식 클라우드 |
|------|------------|--------------|---------------|
| 설정 난이도 | 어려움 | 쉬움 | 매우 쉬움 |
| 비용 | $5~15/월 | $6~40/월 | $24/월~ |
| 실행 횟수 제한 | 없음 | 없음 | 플랜별 제한 |
| 데이터 주권 | 내 서버 | 플랫폼 서버 | n8n 서버 |
| 업데이트 관리 | 직접 | 직접 또는 플랫폼 | n8n 팀 자동 |
| 공식 기술 지원 | 없음 | 없음 | 유료 플랜 제공 |
| 적합 대상 | 개발자·보안 중시 | 빠른 시작 선호 | 비개발자·기업 |

---

## 2. Auth 인증 연동 앱 리스트

### 지원 인증 방식

#### API Key
가장 단순한 방식. HTTP 헤더로 전달되며 n8n 자격증명 관리자에 암호화 저장.

- OpenAI, Anthropic, Mailchimp, HubSpot, Stripe, SerpAPI 등

#### OAuth 2.0
사용자 계정으로 직접 인증. Authorization Code, PKCE 방식 지원.

- **Google**: Gmail, Google Sheets, Google Calendar, Google Drive, YouTube
- **Microsoft**: Outlook, OneDrive, Teams
- **기타**: Facebook, GitHub, Slack, Notion, Shopify, Salesforce, Discord, Trello, Asana

#### JWT (JSON Web Token)
상태 비저장 인증. 분산 시스템 및 SSO에 최적.

- 지원 알고리즘: HS256, RS256/384/512, ES256/384/512
- 사용 사례: API 보안, SSO 구현, Auth0 연동

#### 기타

| 방식 | 용도 |
|------|------|
| Basic Auth | 레거시 시스템 |
| Bearer Token | API 토큰 기반 |
| Digest Auth | 특정 내부 시스템 |
| SAML | 엔터프라이즈 SSO |

### 중앙화된 자격증명 관리
한 번 설정한 자격증명을 모든 워크플로우에서 재사용 가능. 정기 로테이션 권장 (6~12개월).

---

## 3. AI Agent 연동 LLM 모델

### 지원 제공자 및 모델

| 제공자 | 모델 | 특징 |
|--------|------|------|
| **OpenAI** | GPT-4o, GPT-4 Turbo, GPT-3.5-turbo | 복잡한 추론, 도구 호출 성능 우수 |
| **Anthropic** | Claude 4 Opus/Sonnet/Haiku, Claude 3.x | 200K 컨텍스트, 구조화 출력 우수 |
| **Google** | Gemini Pro, Gemini Ultra | 비용 효율, 단순 작업에 적합 |
| **Ollama** | Llama 3, Mistral, Neural Chat 등 | 완전 로컬, 프라이버시 중심 |
| **Hugging Face** | 다양한 오픈소스 모델 | 커스텀 파인튜닝 가능 |
| **Cohere** | Command R+ 등 | 텍스트 생성 및 분류 |

### AI Agent 아키텍처

```
LLM (Brain)     메모리 (Memory)      벡터 DB            도구 (Tools)
──────────────  ─────────────────   ────────────────   ──────────────────
OpenAI        │ Buffer Memory     │ Pinecone         │ HTTP Request Tool
Claude        │ Window Memory     │ Supabase         │ Calculator Tool
Gemini        │ Redis Memory      │ In-Memory        │ Code Tool
Ollama        │                   │ Qdrant           │ Workflow Tool
```

### 연동 데이터베이스

#### SQL (관계형 DB)

| DB | 연동 방식 | 특징 |
|----|---------|------|
| **PostgreSQL** | 공식 노드 | n8n 권장 기본 DB, 프로덕션 표준 |
| **MySQL** | 공식 노드 | 범용 RDBMS |
| **MariaDB** | 공식 노드 | MySQL 호환 오픈소스 |
| **Microsoft SQL Server** | 공식 노드 | 엔터프라이즈 환경 |
| **SQLite** | 공식 노드 | 로컬/개발용 (프로덕션 비권장) |
| **CockroachDB** | 공식 노드 | 분산 SQL, 고가용성 |

#### NoSQL (비관계형 DB)

| DB | 연동 방식 | 특징 |
|----|---------|------|
| **MongoDB** | 공식 노드 | 문서형 DB, 유연한 스키마 |
| **Redis** | 공식 노드 | 인메모리 캐시·메모리 저장소 |
| **Elasticsearch** | 공식 노드 | 검색·로그 분석 |
| **CouchDB** | 공식 노드 | 문서형 DB, 오프라인 동기화 |
| **QuestDB** | 공식 노드 | 시계열 데이터 특화 |

#### SaaS형 데이터베이스 / BaaS

| 서비스 | 연동 방식 | 특징 |
|--------|---------|------|
| **Supabase** | 공식 노드 + 벡터 DB | PostgreSQL 기반 BaaS, RAG에 적합 |
| **Airtable** | 공식 노드 | 스프레드시트형 DB, 비개발자 친화 |
| **Notion Database** | 공식 노드 | 문서·DB 통합, 팀 협업 |
| **Firebase / Firestore** | HTTP Request | Google BaaS, 실시간 동기화 |
| **PlanetScale** | HTTP Request | MySQL 호환 서버리스 DB |
| **Neon** | PostgreSQL 노드 | 서버리스 PostgreSQL |
| **Pinecone** | 공식 노드 | 벡터 DB, AI 검색·RAG 특화 |
| **Qdrant** | 공식 노드 | 오픈소스 벡터 DB |
| **Weaviate** | 공식 노드 | 벡터 DB + GraphQL |
| **Google Sheets** | 공식 노드 | 스프레드시트를 DB처럼 활용 |

---

## 4. 사용 가능한 Tool 노드 리스트 (AI Agent용)

### 공식 내장 Tool 노드 (Built-in)

| Tool 노드 | 상태 | 기능 |
|----------|------|------|
| **Calculator** | ✅ 활성 | 수학 계산 수행 |
| **Code Tool** | ✅ 활성 | JavaScript / Python 커스텀 코드 실행 |
| **HTTP Request Tool** | ✅ 활성 | REST API 호출 (GET/POST/PUT/DELETE) |
| **Wikipedia** | ✅ 활성 | Wikipedia 검색 및 데이터 조회 |
| **SerpAPI** (공식 커뮤니티 노드) | ✅ 활성 | Google/Bing/Baidu 등 20+ 검색 API, `n8n-nodes-serpapi` 설치 필요 |
| **Workflow Tool** | ✅ 활성 | 다른 n8n 워크플로우를 도구로 실행 |
| **AI Agent Tool** | ✅ 활성 | Agent가 다른 Agent를 도구로 호출 (멀티 에이전트) |
| **Vector Store Tool** | ✅ 활성 | 벡터 DB 검색 (RAG 구현), v1.74.0 신규 |
| **MCP Client Tool** | ✅ 활성 (2025.04 신규) | 외부 MCP 서버 도구 호출 |

> **Think Tool**: 별도 노드로 존재하지 않음. ReAct Agent 내부에 추론 과정이 내장되어 있음.

### Memory 노드

| 노드 | 기능 |
|------|------|
| **Window Buffer Memory** | 최근 N개 메시지만 유지 |
| **Postgres Chat Memory** | PostgreSQL 기반 영구 저장 |
| **Redis Chat Memory** | Redis 기반 캐시 메모리 |
| **Zep Memory** | 장기 메모리 관리 |
| **Chat Memory Manager** | 메모리 로드·삽입·삭제 고급 제어 (신규) |

### 주요 커뮤니티 Tool 노드

| Tool 노드 | 기능 |
|----------|------|
| **Brave Search** | Brave 검색 엔진 API (SerpAPI 무료 대안) |
| **Tavily** | 웹 검색·크롤링·리서치 리포트 생성 |
| **Apify** | 대규모 웹 스크래핑 (1,500+ 사전 빌드 Actor) |
| **Firecrawl** | AI 최적화 웹 크롤링 및 구조화 데이터 추출 |
| **Puppeteer** | JavaScript 렌더링 브라우저 자동화 |

---

## 5. 노드 종류 정보

### 트리거 노드 (Trigger)

워크플로우의 시작점. 특정 이벤트 발생 시 실행을 시작한다.

#### 🔴 Schedule / Cron
- **기능**: `0 9 * * *` 형식의 cron 표현식으로 정해진 시간·주기에 자동 실행
- **사용 사례**:
  - 매일 오전 9시 일일 매출 보고서 생성
  - 매주 월요일 주간 회의 자료 자동 수집
  - 매시간 외부 API 데이터 동기화
- **주의**: 실행 간격이 짧을수록 서버 부하 증가

#### 🔴 Webhook
- **기능**: 외부 서비스가 HTTP POST/GET 요청을 보내면 즉시 워크플로우 실행 (밀리초 단위 응답)
- **사용 사례**:
  - Shopify 주문 완료 이벤트 수신 → 자동 발송 처리
  - GitHub PR 생성 → Slack 알림 발송
  - 폼 제출 → DB 저장 + 확인 이메일 발송
- **특징**: 응답 반환이 필요한 경우 `Respond to Webhook` 노드와 함께 사용

#### Email Trigger (IMAP)
- **기능**: 지정한 메일함을 주기적으로 폴링하여 새 이메일 감지 시 워크플로우 실행
- **사용 사례**:
  - 고객 문의 이메일 자동 분류 → 담당자 배정
  - 특정 발신자 이메일 → Notion DB에 자동 저장
  - 첨부파일 자동 추출 → Google Drive 저장

#### App Event Trigger
- **기능**: Slack, GitHub, Notion 등 앱에서 발생하는 특정 이벤트를 실시간 감지
- **사용 사례**:
  - Slack 특정 채널 메시지 → AI 요약 후 노션 저장
  - GitHub Issue 오픈 → Jira 티켓 자동 생성
  - Notion DB 항목 추가 → 담당자에게 이메일 발송

#### MCP Server Trigger
- **기능**: Claude, Cursor 같은 외부 AI 에이전트가 n8n 워크플로우를 MCP 도구로 호출할 때 수신
- **사용 사례**:
  - Claude가 "DB 조회" 도구를 호출 → n8n이 쿼리 실행 후 결과 반환
  - Cursor에서 "배포 실행" 명령 → n8n이 CI/CD 파이프라인 트리거

#### Manual Trigger
- **기능**: n8n UI에서 수동으로 실행 버튼을 눌러 워크플로우 시작
- **사용 사례**: 개발·테스트 단계에서 워크플로우 동작 확인

#### n8n Form Trigger
- **기능**: n8n이 자체 생성한 웹 폼 URL을 공유하고, 제출 시 워크플로우 실행
- **사용 사례**:
  - 외부 개발 없이 간단한 데이터 수집 폼 운영
  - 내부 직원 요청 접수 → 자동 처리 파이프라인 연결

---

### 코어 노드 (Core)

데이터 처리, 흐름 제어, API 호출 등 핵심 로직을 담당한다.

#### 🔴 Edit Fields (Set)
- **기능**: 데이터 항목에 필드를 추가·수정·삭제하거나 값을 고정·변환
- **사용 사례**:
  - API 응답에서 필요한 필드만 추려서 다음 노드로 전달
  - 날짜 포맷 변환 (`2024-01-01` → `2024년 1월 1일`)
  - 고정값 주입 (`status: "pending"` 추가)

#### 🔴 Code
- **기능**: JavaScript 또는 Python 코드를 직접 작성하여 실행. n8n 노드로 처리하기 어려운 복잡한 로직 구현
- **사용 사례**:
  - 정규표현식으로 텍스트 파싱
  - 복잡한 데이터 변환·계산 로직
  - 외부 npm 패키지 활용 (셀프호스팅 한정)

#### 🔴 HTTP Request
- **기능**: GET/POST/PUT/PATCH/DELETE 등 REST API를 직접 호출. n8n 공식 노드가 없는 서비스도 연동 가능
- **사용 사례**:
  - 공식 노드가 없는 국내 서비스 API 연동 (카카오, 네이버 등)
  - 사내 REST API 호출
  - 웹훅으로 외부 서비스에 데이터 전송

#### GraphQL
- **기능**: GraphQL 엔드포인트에 쿼리·뮤테이션 실행
- **사용 사례**:
  - Shopify GraphQL API로 상품·주문 데이터 조회
  - GitHub GraphQL API로 PR·이슈 복합 조회

#### Execute Workflow
- **기능**: 다른 n8n 워크플로우를 서브루틴처럼 호출하고 결과를 받아옴
- **사용 사례**:
  - 공통 로직(이메일 발송, Slack 알림)을 별도 워크플로우로 분리해 재사용
  - 복잡한 워크플로우를 기능 단위로 모듈화

#### Wait
- **기능**: 지정한 시간 또는 Webhook 응답이 올 때까지 워크플로우 실행을 일시 중단
- **사용 사례**:
  - 승인 요청 이메일 발송 후 담당자 응답 대기 (수시간~수일)
  - API Rate Limit 회피를 위한 인터벌 조정
  - 배치 작업 간 간격 설정

#### Respond to Webhook
- **기능**: Webhook으로 수신한 요청에 대해 HTTP 응답을 직접 반환
- **사용 사례**:
  - 외부 서비스의 Webhook 검증 요청에 즉시 `200 OK` 응답
  - 처리 결과를 요청자에게 실시간 반환하는 API 서버 구현

#### Read/Write Files
- **기능**: 서버 파일 시스템에서 파일을 읽거나 쓰기
- **사용 사례**:
  - CSV 파일 읽기 → 데이터 처리 → DB 저장
  - 처리 결과를 JSON 파일로 저장
  - 첨부파일 임시 저장 후 외부 스토리지 업로드

#### Crypto
- **기능**: SHA256, MD5 등 해시 생성, 데이터 암호화·복호화
- **사용 사례**:
  - Webhook 서명 검증 (HMAC-SHA256)
  - 민감 데이터 해시 처리 후 저장
  - API 요청 서명 생성

#### Date & Time
- **기능**: 날짜·시간 파싱, 포맷 변환, 덧셈·뺄셈, 타임존 변환
- **사용 사례**:
  - API 응답의 Unix timestamp → 사람이 읽을 수 있는 날짜 변환
  - 현재 시각 기준 D+7 마감일 계산
  - KST ↔ UTC 타임존 변환

---

### 분기 / 흐름 제어 노드

#### 🔴 If
- **기능**: 하나의 조건식을 평가해 `true` / `false` 두 경로로 분기
- **사용 사례**:
  - 주문 금액 > 10만원이면 → VIP 처리 경로 / 아니면 → 일반 처리 경로
  - 이메일 발신자가 특정 도메인이면 → 스팸 처리

#### 🔴 Switch
- **기능**: 하나의 값을 여러 케이스와 비교해 다중 경로로 분기 (if-else if 체인)
- **사용 사례**:
  - 티켓 유형(결제/배송/환불/기타)에 따라 각 담당팀으로 라우팅
  - 언어 코드(`ko`/`en`/`ja`)에 따라 다국어 응답 분기

#### Merge
- **기능**: 여러 경로로 분기된 데이터를 하나로 합침. 모드에 따라 동작이 다름
- **모드**:
  - `Append`: 모든 입력 데이터를 순서대로 합침
  - `Merge By Index`: 같은 인덱스 위치의 항목끼리 병합
  - `Merge By Key`: 지정한 키가 같은 항목끼리 병합
- **사용 사례**:
  - 병렬로 조회한 두 API 결과를 하나의 데이터셋으로 합산
  - 분기 처리 후 최종 결과를 단일 경로로 수렴

#### 🔴 Loop Over Items
- **기능**: 배열의 각 항목을 순서대로 하나씩 처리. 내부 노드들이 항목마다 반복 실행됨
- **사용 사례**:
  - 고객 목록 100명에게 각각 개인화된 이메일 발송
  - 상품 목록을 순회하며 각 상품 상세 페이지 크롤링

#### Split Out
- **기능**: 배열 필드를 개별 아이템으로 분리해 각각 독립적으로 처리
- **사용 사례**:
  - API가 반환한 `orders: [...]` 배열을 개별 주문 아이템으로 분리
  - 이후 노드에서 각 주문을 병렬 처리

#### Aggregate
- **기능**: 개별 아이템들을 하나의 배열로 합산. Split Out의 역방향
- **사용 사례**:
  - 각각 처리된 결과를 모아 하나의 리스트로 만들어 DB에 일괄 저장
  - 반복 처리 결과를 배열로 수집 후 요약 리포트 생성

#### 🔴 Filter
- **기능**: 조건을 만족하는 아이템만 통과시키고 나머지는 제거
- **사용 사례**:
  - 상태가 `active`인 사용자만 필터링
  - 금액이 0보다 큰 주문만 통과

#### Limit
- **기능**: 최대 N개의 아이템만 다음 노드로 전달
- **사용 사례**:
  - API 응답에서 상위 10개 결과만 처리
  - 배치 크기 제한으로 Rate Limit 관리

#### Remove Duplicates
- **기능**: 지정한 필드 기준으로 중복 항목을 제거
- **사용 사례**:
  - 여러 소스에서 수집한 이메일 목록에서 중복 주소 제거
  - 크롤링 결과에서 동일 URL 중복 제거

#### Sort
- **기능**: 지정한 필드를 기준으로 아이템 정렬 (오름차순/내림차순)
- **사용 사례**:
  - 주문 목록을 금액 기준 내림차순 정렬
  - 날짜 기준 최신순으로 정렬 후 상위 N개만 처리

---

### 연결 노드 (Connector) — 주요 앱

| 카테고리 | 노드 | 주요 용도 |
|---------|------|---------|
| **생산성** | Google Sheets | 데이터 읽기·쓰기, 간이 DB로 활용 |
| | Notion | DB 항목 생성·조회, 문서 자동 작성 |
| | Airtable | 구조화 데이터 관리, 프로젝트 트래킹 |
| | Microsoft Excel | 기업 내 엑셀 파일 자동화 |
| **커뮤니케이션** | Slack | 알림 발송, 채널 메시지, 봇 응답 |
| | Gmail / Outlook | 이메일 발송·수신·분류 |
| | Telegram | 봇 메시지 발송, 개인 알림 |
| | Discord | 서버 알림, 커뮤니티 자동화 |
| **CRM** | HubSpot | 리드 생성·업데이트, 딜 관리 |
| | Salesforce | 영업 데이터 동기화, 기회 관리 |
| | Pipedrive | 파이프라인 자동 업데이트 |
| **프로젝트 관리** | Jira | 이슈 생성·업데이트, 스프린트 관리 |
| | Linear | 이슈 트래킹, 개발팀 워크플로우 |
| | Asana / Trello | 태스크 자동 생성·완료 처리 |
| **이커머스** | Shopify | 주문·상품·고객 데이터 처리 |
| | Stripe | 결제 이벤트 수신, 청구서 자동화 |
| | WooCommerce | 워드프레스 쇼핑몰 주문 처리 |
| **개발** | GitHub | PR·이슈 자동화, 릴리스 관리 |
| | GitLab | CI/CD 트리거, MR 알림 |
| **스토리지** | Google Drive | 파일 업로드·다운로드·공유 |
| | AWS S3 | 대용량 파일 저장·조회 |
| | Dropbox | 파일 동기화 자동화 |
| **AI** | OpenAI | 텍스트 생성, 분류, 임베딩 |
| | Anthropic | 긴 문서 분석, 구조화 출력 |
| | Google Gemini | 비용 효율적 텍스트 처리 |
| | Ollama | 완전 로컬 LLM 실행 |

---

## 6. 데이터 처리 노드

### 크롤링 워크플로우 구조

```
Trigger (Schedule / Webhook)
    ↓
HTTP Request          ← HTML 페이지 다운로드
    ↓
HTML Extract          ← CSS 선택자로 데이터 추출
    ↓
Code Node             ← 커스텀 파싱 / 정제 로직
    ↓
Filter / If           ← 필요한 데이터만 선택
    ↓
Google Sheets / DB    ← 결과 저장
```

### 크롤링 관련 노드

| 노드 | 기능 |
|------|------|
| **HTTP Request** | 정적 HTML 페이지 다운로드 |
| **HTML Extract** | CSS 선택자 기반 데이터 추출 |
| **XML** | XML / RSS 파싱 |
| **Puppeteer** (커뮤니티) | JS 렌더링 필요한 동적 사이트 처리 |
| **Playwright** (커뮤니티) | 복잡한 브라우저 자동화 |

> **주의**: 기본 HTTP Request 노드는 정적 HTML만 가져온다. JavaScript로 렌더링되는 콘텐츠는 Puppeteer / Playwright 노드가 필요하다.

### 데이터 변환 / 분석 노드

#### 🔴 Edit Fields (Set)
- **기능**: 데이터 항목의 필드를 추가·수정·삭제하거나 값을 고정·변환. 거의 모든 워크플로우에서 사용되는 가장 기본적인 노드
- **사용 방법**:
  - `Add Field`: 새 필드 추가 (`status: "pending"`)
  - `Set Field`: 기존 필드 값 덮어쓰기
  - `Remove Field`: 불필요한 필드 제거
  - Expression 사용: `{{ $json.price * 1.1 }}` 형식으로 동적 값 계산
- **사용 사례**:
  - API 응답에서 필요한 필드만 추려 다음 노드로 전달
  - 필드명 변경 (`user_name` → `name`)
  - 계산값 추가 (`totalPrice = price * quantity`)

#### 🔴 Code
- **기능**: JavaScript 또는 Python 코드를 직접 작성해 실행. 노드만으로 처리하기 어려운 복잡한 변환 로직을 구현
- **사용 방법**:
  ```javascript
  // 입력 아이템 전체 처리
  return items.map(item => ({
    json: {
      ...item.json,
      fullName: `${item.json.firstName} ${item.json.lastName}`,
      isVip: item.json.totalSpent > 1000000
    }
  }));
  ```
- **사용 사례**:
  - 정규표현식으로 텍스트에서 특정 패턴 추출
  - 중첩 JSON 구조를 플랫하게 변환
  - 여러 필드를 조합한 복합 값 생성
  - 외부 npm 라이브러리 활용 (셀프호스팅 한정)

#### Item List Operations
- **기능**: 배열 데이터에 대한 필터·정렬·매핑·그룹화 등을 코드 없이 GUI로 처리
- **사용 방법**:
  - `Filter`: 조건에 맞는 항목만 남기기
  - `Sort`: 필드 기준 정렬
  - `Limit`: 상위 N개만 추출
  - `Summarize`: 그룹별 집계
- **사용 사례**:
  - 주문 목록에서 `status === "completed"`인 항목만 추출
  - 매출 기준 내림차순 정렬 후 상위 10개 추출

#### 🔴 Split Out
- **기능**: 하나의 아이템 안에 있는 배열 필드를 개별 아이템으로 분리. 이후 노드에서 각 항목을 독립적으로 처리할 수 있게 함
- **사용 방법**: 분리할 배열 필드명 지정 → 각 원소가 별도 아이템으로 출력
- **사용 사례**:
  - API가 반환한 `{ orders: [{...}, {...}] }` → 개별 주문 아이템으로 분리
  - 분리 후 각 항목을 Loop 또는 병렬로 처리
  - 커뮤니티 노드 설치 없이 배열 전개가 필요할 때

#### Aggregate
- **기능**: 여러 개의 개별 아이템을 하나의 배열로 합산. Split Out의 역방향
- **사용 방법**: 합산할 필드 지정 → 하나의 아이템에 배열로 묶임
- **사용 사례**:
  - Loop에서 처리된 개별 결과를 모아 DB에 일괄 저장
  - 분산 처리 결과를 하나의 리포트 배열로 수집

#### 🔴 Summarize
- **기능**: 그룹 기준 필드를 지정하고 집계 함수(Sum, Count, Average, Min, Max)를 적용. SQL의 `GROUP BY`와 동일한 동작
- **사용 방법**: `Group By` 필드 + 집계할 필드 + 집계 함수 선택
- **사용 사례**:
  - 부서별 총 매출 합산 (`GROUP BY department, SUM(sales)`)
  - 카테고리별 상품 개수 집계 (`GROUP BY category, COUNT(*)`)
  - 일별 평균 주문 금액 계산

#### Math
- **기능**: 덧셈·뺄셈·곱셈·나눗셈·반올림·절댓값 등 수치 연산을 노드로 처리
- **사용 방법**: 연산 대상 필드와 연산자 선택
- **사용 사례**:
  - 세금 포함 가격 계산 (`price * 1.1`)
  - 할인율 적용 (`price * (1 - discountRate)`)
  - 소수점 반올림 처리

#### 🔴 Date & Time
- **기능**: 날짜·시간 파싱, 포맷 변환, 타임존 변환, 날짜 연산(더하기·빼기)
- **사용 방법**: 변환할 필드 선택 → 출력 포맷 지정 (`YYYY-MM-DD`, `MM/DD/YYYY` 등)
- **사용 사례**:
  - Unix timestamp → 한국어 날짜 포맷 변환
  - UTC → KST 타임존 변환
  - 현재 날짜 기준 D+7 마감일 자동 계산
  - 날짜 기준 필터링을 위한 비교값 생성

#### Text Classifier (AI)
- **기능**: LLM을 사용해 텍스트를 사전 정의한 카테고리 중 하나로 분류. 별도 프롬프트 없이 카테고리 목록만 지정하면 동작
- **사용 방법**: 분류 카테고리 목록 입력 → 입력 텍스트가 자동으로 카테고리에 매핑
- **사용 사례**:
  - 고객 문의 이메일을 `결제문의 / 배송문의 / 환불요청 / 기타`로 자동 분류
  - 뉴스 기사를 `정치 / 경제 / 스포츠 / 기술`로 분류
  - 리뷰 감정을 `긍정 / 부정 / 중립`으로 분류

#### Sentiment Analysis (AI)
- **기능**: LLM을 사용해 텍스트의 감정(긍정/부정/중립)과 감정 점수를 분석
- **사용 방법**: 분석할 텍스트 필드 지정 → 감정 레이블과 점수 출력
- **사용 사례**:
  - 상품 리뷰 감정 점수 일괄 분석 → Google Sheets 저장
  - SNS 멘션 모니터링 → 부정 반응 감지 시 알림 발송
  - 고객 피드백 대시보드 구축

### 시각화 / 출력

n8n 자체에는 차트 렌더링 노드가 없다. 분석 결과를 외부 도구로 내보내는 방식을 사용한다.

| 출력 대상 | 방법 |
|---------|------|
| Google Sheets | 데이터 저장 후 Sheets에서 차트 생성 |
| Grafana | HTTP Request로 데이터 전송 |
| Metabase / Superset | DB에 저장 후 BI 도구 연결 |
| Slack / Email | 텍스트 기반 리포트 발송 |

---

## 7. MCP (Model Context Protocol) 지원

### n8n의 MCP 역할

n8n은 **MCP 서버**와 **MCP 클라이언트** 역할을 모두 수행할 수 있다.

### MCP Server Trigger 노드 (AI 에이전트 → n8n)

n8n 워크플로우가 **MCP 서버** 역할을 한다. Claude, Cursor, Windsurf 같은 AI 에이전트(MCP 클라이언트)가 n8n 워크플로우를 MCP 도구로 호출하는 구조다.

```
AI 에이전트 (MCP 클라이언트)        n8n (MCP 서버)
──────────────────────────    →    ──────────────────────
Claude / Cursor / Windsurf         MCP Server Trigger 노드
                                   → 워크플로우 실행
                                   → 결과 반환
```

- **n8n = 도구를 제공하는 서버** (MCP Server)
- **AI 에이전트 = 도구를 호출하는 클라이언트** (MCP Client)
- 인증: Bearer Token, 커스텀 헤더, OAuth2 지원
- 전송 방식: SSE (Server-Sent Events)

### MCP Client Tool 노드 (n8n AI Agent → 외부 MCP 서버)

n8n의 AI Agent 노드가 **MCP 클라이언트** 역할을 하여 외부 MCP 서버의 도구를 호출한다.

```
n8n (MCP 클라이언트)               외부 MCP 서버
──────────────────────────    →    ──────────────────────
n8n AI Agent 노드                  GitHub MCP
+ MCP Client Tool 노드             Slack MCP
                                   파일시스템 MCP 등
```

- **n8n AI Agent = 도구를 호출하는 클라이언트** (MCP Client)
- **외부 MCP 서버 = 도구를 제공하는 서버** (MCP Server)
- 연결: SSE 엔드포인트
- 인증: Bearer Token, OAuth2

### 커뮤니티 MCP 서버: n8n-MCP

#### n8n-MCP란?

Claude Code 같은 AI 에이전트가 **자연어 명령만으로 n8n 워크플로우를 생성·수정·실행**할 수 있게 해주는 브릿지 MCP 서버다. GitHub의 czlonkowski이 개발한 커뮤니티 프로젝트.

**n8n-MCP가 없을 때** — REST API JSON을 직접 작성해야 함:
```json
// 사람이 직접 작성해야 하는 복잡한 워크플로우 JSON
{
  "nodes": [{ "type": "n8n-nodes-base.scheduleTrigger", ... }],
  "connections": { ... }
}
```

**n8n-MCP가 있을 때** — 자연어로 명령만 하면 됨:
```
"매일 오전 9시에 Google Sheets에서 데이터를 읽어서 Slack으로 보내는 워크플로우 만들어줘"
→ Claude가 워크플로우 자동 생성 + n8n에 등록 + 활성화까지 처리
```

#### 동작 구조

```
사용자 (자연어 명령)
    ↓
Claude Code (MCP 클라이언트)
    ↓ MCP 프로토콜
n8n-MCP 서버 (번역기 역할)
    ↓ n8n REST API 호출
n8n 인스턴스
    ↓
워크플로우 생성 · 수정 · 실행 · 조회
```

#### n8n-MCP가 제공하는 기능

| 기능 | 설명 |
|------|------|
| 워크플로우 생성 | 자연어 설명으로 워크플로우 자동 생성 |
| 워크플로우 조회 | 기존 워크플로우 목록 검색 및 내용 확인 |
| 워크플로우 수정 | 특정 노드 추가·변경·삭제 |
| 워크플로우 실행 | 즉시 실행 및 실행 결과 확인 |
| 노드 검색 | 1,851개 노드 중 목적에 맞는 노드 탐색 |
| 템플릿 활용 | 2,352개 워크플로우 템플릿 검색 및 적용 |

#### 규모

| 항목 | 수치 |
|------|------|
| 지원 노드 수 | 1,851개 (코어 822 + 커뮤니티 1,029) |
| AI 기능 도구 | 265개 |
| 워크플로우 템플릿 | 2,352개 |
| 노드 속성 커버리지 | 99% |
| 문서 커버리지 | 87% |

#### Claude Code에서 n8n-MCP 설정

```json
{
  "mcpServers": {
    "n8n": {
      "command": "npx",
      "args": ["n8n-mcp"],
      "env": {
        "N8N_API_URL": "https://your-n8n-instance.com",
        "N8N_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

설정 후 Claude Code에서 바로 사용 가능:
```
# 워크플로우 생성
"Shopify 주문이 들어오면 Gmail로 확인 이메일을 보내는 워크플로우 만들어줘"

# 기존 워크플로우 조회
"현재 활성화된 워크플로우 목록 보여줘"

# 워크플로우 수정
"기존 보고서 워크플로우에 Slack 알림 노드도 추가해줘"
```

---

## 8. Claude Code에서 n8n 워크플로우 만드는 방법

### 방법 1: n8n REST API 직접 호출

#### API 키 생성
1. n8n 인스턴스 로그인
2. **Settings → API → Create API Key**
3. 생성된 키를 환경변수로 관리

#### 주요 엔드포인트

| 메서드 | 엔드포인트 | 기능 |
|--------|-----------|------|
| GET | `/api/v1/workflows` | 워크플로우 목록 조회 |
| GET | `/api/v1/workflows/{id}` | 특정 워크플로우 조회 |
| POST | `/api/v1/workflows` | 워크플로우 생성 |
| PUT | `/api/v1/workflows/{id}` | 워크플로우 수정 |
| DELETE | `/api/v1/workflows/{id}` | 워크플로우 삭제 |
| POST | `/api/v1/workflows/{id}/activate` | 워크플로우 활성화 |
| GET | `/api/v1/executions` | 실행 이력 조회 |

#### Python 예제

```python
import requests
import os

N8N_BASE_URL = "https://your-n8n-instance.com/api/v1"
headers = {
    "X-N8N-API-KEY": os.environ["N8N_API_KEY"],
    "Content-Type": "application/json"
}

# 워크플로우 생성
workflow = {
    "name": "Daily Report",
    "nodes": [
        {
            "id": "1",
            "name": "Schedule Trigger",
            "type": "n8n-nodes-base.scheduleTrigger",
            "position": [250, 300],
            "parameters": {
                "rule": {"interval": [{"field": "cronExpression", "expression": "0 9 * * *"}]}
            }
        },
        {
            "id": "2",
            "name": "HTTP Request",
            "type": "n8n-nodes-base.httpRequest",
            "position": [450, 300],
            "parameters": {
                "method": "GET",
                "url": "https://api.example.com/data"
            }
        }
    ],
    "connections": {
        "Schedule Trigger": {
            "main": [[{"node": "HTTP Request", "type": "main", "index": 0}]]
        }
    },
    "active": False
}

response = requests.post(f"{N8N_BASE_URL}/workflows", headers=headers, json=workflow)
workflow_id = response.json()["id"]

# 활성화
requests.post(f"{N8N_BASE_URL}/workflows/{workflow_id}/activate", headers=headers)
print(f"워크플로우 생성 및 활성화 완료: {workflow_id}")
```

#### JavaScript 예제

```javascript
const N8N_BASE_URL = "https://your-n8n-instance.com/api/v1";
const headers = {
  "X-N8N-API-KEY": process.env.N8N_API_KEY,
  "Content-Type": "application/json"
};

const workflow = {
  name: "Slack Alert",
  nodes: [
    {
      id: "1",
      name: "Webhook",
      type: "n8n-nodes-base.webhook",
      position: [250, 300],
      parameters: { path: "alert", httpMethod: "POST" }
    },
    {
      id: "2",
      name: "Slack",
      type: "n8n-nodes-base.slack",
      position: [450, 300],
      parameters: {
        resource: "message",
        operation: "post",
        channel: "#alerts",
        text: "={{ $json.message }}"
      }
    }
  ],
  connections: {
    "Webhook": {
      main: [[{ node: "Slack", type: "main", index: 0 }]]
    }
  },
  active: false
};

const res = await fetch(`${N8N_BASE_URL}/workflows`, {
  method: "POST",
  headers,
  body: JSON.stringify(workflow)
});
const { id } = await res.json();
console.log("생성된 워크플로우 ID:", id);
```

### 방법 2: n8n-MCP를 통해 Claude Code에서 자연어로 생성

n8n-MCP를 Claude Code에 연결하면 자연어 명령으로 워크플로우를 생성할 수 있다.

```
# Claude Code에서 입력 예시

"매일 오전 9시에 실행되고, Google Sheets에서 고객 데이터를 읽어서
 OpenAI로 요약한 뒤 Slack #daily-report 채널에 전송하는
 n8n 워크플로우를 만들어줘."
```

Claude Code가 자동으로:
1. 워크플로우 JSON 구조 생성
2. n8n REST API로 워크플로우 등록
3. 활성화 및 테스트 실행

### 보안 모범 사례

- API 키는 반드시 환경변수로 관리 (`N8N_API_KEY`)
- 코드 저장소에 API 키 절대 커밋 금지
- 프로덕션 배포 전 복제 워크플로우로 테스트
- 활성 워크플로우는 직접 수정하지 말고 비활성화 후 수정

---

## 참고 자료

- [n8n 공식 문서](https://docs.n8n.io/)
- [n8n REST API 레퍼런스](https://docs.n8n.io/api/api-reference/)
- [n8n MCP Client Tool 노드](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolmcp/)
- [n8n-MCP GitHub (czlonkowski)](https://github.com/czlonkowski/n8n-mcp)
- [n8n 커뮤니티 포럼](https://community.n8n.io/)
- [n8n 워크플로우 템플릿](https://n8n.io/workflows/)
