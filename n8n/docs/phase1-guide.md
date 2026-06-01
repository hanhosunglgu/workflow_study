# WBS Agent Phase 1 — 개발 가이드

**작성일**: 2026-05-13  
**대상 독자**: n8n을 처음 접하는 개발자 / 기획자  
**목적**: Phase 1에서 구현한 6개 워크플로의 구조와 각 노드의 역할을 상세히 설명

---

## 목차

1. [n8n 기본 개념](#1-n8n-기본-개념)
2. [전체 아키텍처 개요](#2-전체-아키텍처-개요)
3. [공통 노드 패턴](#3-공통-노드-패턴)
4. [WBS-GRC — Repo 분류기](#4-wbs-grc--repo-분류기)
5. [WBS-DDA — 설계 문서 분석기](#5-wbs-dda--설계-문서-분석기)
6. [WBS-BAK — Backend 코드 분석기](#6-wbs-bak--backend-코드-분석기)
7. [WBS-FRT — Frontend 코드 분석기](#7-wbs-frt--frontend-코드-분석기)
8. [WBS-CFG — IaC/Config 분석기](#8-wbs-cfg--iacconfig-분석기)
9. [WBS-MOB — Mobile 코드 분석기](#9-wbs-mob--mobile-코드-분석기)
10. [WBS-INT — 통합 테스트 워크플로](#10-wbs-int--통합-테스트-워크플로)
11. [주요 기술 이슈 및 해결 방법](#11-주요-기술-이슈-및-해결-방법)

---

## 1. n8n 기본 개념

### n8n이란?

n8n은 **노드(Node)를 시각적으로 연결하여 자동화 흐름(Workflow)을 만드는 도구**입니다.  
코드를 직접 짜지 않아도 되지만, 복잡한 로직은 JavaScript 코드 노드로 처리할 수 있습니다.

```
[노드 A] → [노드 B] → [노드 C]
  데이터가 왼쪽에서 오른쪽으로 흐름
```

### 핵심 용어

| 용어 | 설명 |
|------|------|
| **Workflow** | 노드들을 연결한 자동화 흐름 전체. 하나의 `.json` 파일로 저장/임포트 가능 |
| **Node** | Workflow를 구성하는 단위 작업 블록 (API 호출, 코드 실행, 조건 분기 등) |
| **Item** | 노드 간에 전달되는 데이터 단위. JSON 객체 1개 = Item 1개 |
| **Webhook** | 외부에서 HTTP POST 요청을 보내면 Workflow가 실행되는 진입점 |
| **Credential** | API Key, Token 등 인증 정보를 n8n이 안전하게 보관하는 저장소 |
| **Variable (`$vars`)** | n8n Settings → Variables에 등록한 전역 설정값 |
| **Expression** | 노드 파라미터 안에서 `{{ }}` 또는 `=` 로 시작하는 동적 값 |

### 노드 간 데이터 흐름

```
노드 A가 출력한 JSON → 노드 B의 입력으로 자동 전달
노드 B 안에서: $input.first().json  ← 이전 노드의 첫 번째 결과
              $input.all()          ← 이전 노드의 모든 결과 배열
              $('노드이름').first().json ← 특정 노드의 결과를 직접 참조
```

---

## 2. 전체 아키텍처 개요

### Phase 1 구성

Phase 1은 **설계 적합성 검증**을 목적으로 하는 6개의 Specialist Agent로 구성됩니다.  
각 Agent는 독립적인 n8n Workflow이며, `WBS-INT`가 이를 순차 호출합니다.

```
외부 호출 (curl / Teams Bot)
        │
        ▼
  [WBS-INT] 통합 워크플로
        │
        ├─▶ [WBS-GRC] GitHub Repo 분류
        │         └─ backend / frontend / config / mobile 판별
        │
        ├─▶ [WBS-DDA] 설계 문서 분석
        │         └─ API 명세 / ERD / 시퀀스 추출
        │
        ├─▶ [WBS-BAK] Backend 코드 분석
        │         └─ 실제 API 엔드포인트 / Call Flow 추출
        │
        ├─▶ [WBS-FRT] Frontend 코드 분석
        │         └─ API 호출 패턴 / 화면 흐름 추출
        │
        ├─▶ [WBS-CFG] IaC/Config 분석
        │         └─ 인프라 컴포넌트 / 보안 Gap 추출
        │
        └─▶ [WBS-MOB] Mobile 코드 분석
                  └─ 화면 전환 흐름 / API 호출 추출
```

### 시스템 구성 요소

| 구성 요소 | 역할 |
|-----------|------|
| **n8n** (Docker) | Workflow 실행 엔진. `http://localhost:5678` |
| **Ollama** (Docker) | 로컬 LLM 서버. 모델: `qwen2.5-coder:7b`. `http://ollama:11434` |
| **GitHub API** | 커밋/파일 정보 조회. Personal Access Token 인증 |
| **WBS_Check** (GitHub Repo) | 테스트용 더미 Repo. 각 에이전트 유형별 파일 포함 |

### 입력/출력 규격

**공통 입력 (WBS-INT 기준)**:
```json
{
  "owner": "hanhosunglgu",
  "repos": ["WBS_Check"],
  "dda_repo": "hanhosunglgu/WBS_Check",
  "dda_path": "docs/design",
  "since": "2026-05-06T00:00:00Z",
  "until": "2026-05-13T23:59:59Z"
}
```

**공통 출력 필드**:
```json
{
  "agent_id": "WBS-XXX",
  "repo": "WBS_Check",
  "repo_type": "backend | frontend | config | mobile | design_doc",
  "commit_count": 8,
  "active_days": 1,
  "error": null
}
```

---

## 3. 공통 노드 패턴

Phase 1의 6개 Workflow는 공통적으로 다음 노드 타입을 사용합니다.

### 3.1 Webhook 노드

**역할**: 외부 HTTP POST 요청을 받아 Workflow를 실행하는 진입점

```
POST http://localhost:5678/webhook/wbs-grc
Content-Type: application/json
{ "owner": "...", "repos": [...] }
```

- `responseMode: responseNode` 설정 → 마지막 "Respond to Webhook" 노드가 응답을 반환
- 활성화(Active) 상태여야 Production URL이 동작

### 3.2 Code 노드 (JavaScript)

**역할**: JavaScript 코드로 데이터를 변환, 필터링, 가공

```javascript
// 이전 노드 데이터 접근
const input = $input.first().json;     // 단일 item
const items = $input.all();            // 전체 item 배열

// 특정 노드 데이터 직접 참조
const meta = $('Build Ollama Request').first().json._meta;

// 다음 노드로 데이터 전달 (반드시 배열 형태로 반환)
return [{ json: { key: value } }];

// 여러 item 반환 (루프 대상)
return repos.map(repo => ({ json: { repo } }));
```

- n8n Code 노드는 `require()`, `fetch()`, `$env` 사용 불가
- `$vars.KEY`로 n8n Variables 접근 가능
- `Buffer`는 사용 가능 (Base64 디코딩 등)

### 3.3 HTTP Request 노드

**역할**: 외부 API (GitHub, Ollama) 호출

```
주요 설정:
- URL: 동적 표현식 사용 가능 (={{ $json.owner }})
- Authentication: GitHub PAT → "GitHub PAT" Credential 선택
- neverError: true → HTTP 오류 응답도 에러로 처리하지 않고 계속 진행
- timeout: 600000 → Ollama 호출 시 10분 대기 (CPU 추론 시간 고려)
```

### 3.4 SplitInBatches 노드 (루프)

**역할**: 여러 개의 Item을 하나씩 순차 처리 (for 루프와 동일한 역할)

```
핵심 포트 규칙:
  index 0 (Done 포트)  → 루프가 끝났을 때 연결되는 노드
  index 1 (Loop 포트)  → 루프 본체 (각 item 처리) 연결되는 노드

잘못 연결하면 루프가 즉시 종료되거나 무한 루프 발생!
```

```
[SplitInBatches]
    ├─ index 0 (Done) ──▶ [집계 노드]   ← 모든 처리 완료 후
    └─ index 1 (Loop) ──▶ [처리 노드]   ← 각 item 처리
              └──────────────────────────▶ [SplitInBatches]  ← 다시 루프로 돌아옴
```

### 3.5 Respond to Webhook 노드

**역할**: Workflow 실행 결과를 HTTP 응답으로 반환

```
설정:
- respondWith: json
- responseBody: ={{ JSON.stringify($json) }}
- responseCode: 200
```

### 3.6 _meta 패턴 (메타데이터 전달)

Ollama HTTP Request 노드는 응답을 받으면 이전 `$json`을 덮어씁니다.  
그래서 앞 노드의 정보(repo, commit_count 등)를 `_meta` 필드에 담아 Ollama 노드를 거친 후에도 참조할 수 있게 합니다.

```javascript
// Build Ollama Request 노드 (Ollama 호출 직전)
return [{ json: {
  model: 'qwen2.5-coder:7b',
  prompt: prompt,
  stream: false,
  _meta: {                          // ← 메타데이터를 함께 담아서 전달
    repo: prevData.repo,
    commit_count: prevData.commit_count,
    active_days: prevData.active_days,
    commit_messages: prevData.commit_messages
  }
}}];

// Parse & Build Output 노드 (Ollama 응답 처리 후)
const meta = $('Build Ollama Request').first().json._meta;  // ← 직접 참조
```

---

## 4. WBS-GRC — Repo 분류기

**파일**: `workflow/WBS-GRC.json`  
**Webhook**: `POST /webhook/wbs-grc`  
**목적**: GitHub Repo 목록을 루트 파일 패턴으로 분석하여 유형 분류

### 4.1 전체 흐름

```
Webhook
  → Init Params           파라미터 파싱
  → GET User Repos        GitHub API: 전체 Repo 목록 조회
  → Filter & Split Repos  분석 대상 Repo만 필터링, 1개씩 분리
  → Loop Over Repos       [루프 시작]
      ├─ (Done) → Build Output     분류 결과 최종 정리
      └─ (Loop) → GET Root Contents  GitHub API: 루트 파일 목록 조회
                → Attach Repo Info   파일 목록 + Repo 정보 결합
                → Classify Repos     파일 패턴으로 유형 분류
                → Loop Over Repos    [다음 Repo로]
  → Respond to Webhook
```

### 4.2 노드별 상세 설명

#### Init Params
입력 파라미터를 파싱합니다.

```javascript
const owner = body.owner || $vars.GITHUB_OWNER || '';
let repos = body.repos || $vars.GITHUB_REPOS || '[]';
// repos를 배열로 통일 처리 (문자열 JSON이거나 배열이거나)
```

- `owner`: GitHub 계정명 (예: `hanhosunglgu`)
- `repos`: 분석할 Repo 이름 목록 (예: `["WBS_Check"]`)

#### GET User Repos
```
GET https://api.github.com/users/{owner}/repos?per_page=100&type=all
인증: GitHub PAT Credential
```
계정의 전체 Repo 목록을 가져옵니다. `per_page=100`으로 최대 100개까지 조회.

#### Filter & Split Repos
```javascript
// repos 입력값에 있는 이름과 일치하는 것만 필터링
const filtered = filterList.length > 0
  ? repoList.filter(r => filterList.includes(r.name))
  : repoList;

// 1 Repo = 1 Item으로 분리 (SplitInBatches가 1개씩 처리)
return filtered.map(r => ({ json: { owner: r.owner.login, repo: r.name, full_name: r.full_name } }));
```

#### Loop Over Repos (SplitInBatches)
- `batchSize: 1` → Repo 1개씩 처리
- Done 포트 → `Build Output` (모든 Repo 처리 완료 시)
- Loop 포트 → `GET Root Contents` (각 Repo 처리)

#### GET Root Contents
```
GET https://api.github.com/repos/{full_name}/contents/
```
Repo 루트 경로의 파일/디렉토리 목록을 가져옵니다.

#### Attach Repo Info
GitHub API 응답에서 파일 이름 목록을 추출하고, URL 파싱으로 owner/repo 정보를 확보합니다.
```javascript
// URL 파싱으로 owner/repo 추출
const m = f.url.match(/repos\/([^/]+\/[^/]+)\/contents/);
// 결과: { repo, file_names: ['package.json', 'vite.config.js', ...] }
```

#### Classify Repos
파일 패턴으로 유형을 판별합니다. **5단계 우선순위** 적용:

| 우선순위 | 유형 | 판별 파일 패턴 |
|---------|------|--------------|
| 1 | `mobile` | `Podfile`, `pubspec.yaml`, `Package.swift`, `build.gradle`(단독) |
| 2 | `config` | `terraform/`, `k8s/`, `helm/`, `Dockerfile`(단독), `docker-compose.yml` |
| 3 | `backend` | `server.js`, `app.py`, `main.go`, `pom.xml`, `routes/`, `controllers/` |
| 4 | `frontend` | `package.json`+`vite.config.*`, `angular.json`, `nuxt.config.*`, `.tsx`/`.vue` |
| 5 | `unknown` | 위 패턴 해당 없음 |

#### Build Output
분류 결과를 표준 스키마로 정리합니다.
```json
{
  "agent_id": "WBS-GRC",
  "backend": [],
  "frontend": ["WBS_Check"],
  "config": [],
  "mobile": [],
  "unknown": [],
  "_classified_detail": [
    { "repo": "WBS_Check", "type": "frontend", "reason": "Vite" }
  ],
  "error": null
}
```

---

## 5. WBS-DDA — 설계 문서 분석기

**파일**: `workflow/WBS-DDA.json`  
**Webhook**: `POST /webhook/wbs-dda`  
**목적**: GitHub에 저장된 설계 문서(.md)를 읽어 API 명세 / DB 테이블 / 시퀀스 구조를 AI로 추출

> ⚠️ **주의**: 다른 에이전트와 달리 입력 파라미터가 다릅니다.
> - `repos[]` 배열 대신 `{ repo, path }` 사용
> - `repo`: `owner/reponame` 또는 `reponame` (단일 설계 문서 Repo)
> - `path`: 설계 문서가 있는 디렉토리 경로 (예: `docs/design`)

### 5.1 전체 흐름

```
Webhook
  → Init Params             파라미터 파싱 (owner/repo/path 분리)
  → GET Design Doc List     GitHub API: 지정 경로의 파일 목록 조회
  → Filter MD Files         .md 파일만 필터링
  → Loop Over Files         [루프 시작]
      ├─ (Done) → Build Ollama Request  전체 문서 합산 → LLM 프롬프트 구성
      │             → Ollama Extract Structure  AI 분석
      │             → Parse & Build Output     결과 파싱
      │             → Respond to Webhook
      └─ (Loop) → GET File Content  GitHub API: 파일 내용 조회 (Base64)
                → Decode Base64    Base64 → 텍스트 디코딩
                → Loop Over Files  [다음 파일로]
```

### 5.2 노드별 상세 설명

#### Init Params
```javascript
const docRepo = body.repo || $vars.DESIGN_DOC_REPO || '';
const docPath = body.path || $vars.DESIGN_DOC_PATH || '';

// "owner/repo" 형식 분리
const repoName = docRepo.includes('/') ? docRepo.split('/').pop() : docRepo;
const repoOwner = docRepo.includes('/') ? docRepo.split('/')[0] : owner;
```

#### GET Design Doc List
```
GET https://api.github.com/repos/{owner}/{repo}/contents/{path}
```
지정 경로의 파일 목록을 가져옵니다. 결과는 파일/디렉토리 정보 배열.

#### Filter MD Files
```javascript
// .md 확장자, 타입이 'file'인 것만 선택
const mdFiles = files.filter(f => f.name.endsWith('.md') && f.type === 'file');
// 결과: [{ name: 'api-spec.md', url: 'https://api.github.com/...' }]
```
.md 파일이 없으면 에러를 발생시켜 워크플로를 중단합니다.

#### Loop Over Files (SplitInBatches)
파일 목록을 1개씩 처리합니다.

#### GET File Content
```
GET {url}  ← Filter MD Files에서 얻은 GitHub API URL
```
GitHub API는 파일 내용을 **Base64로 인코딩**하여 반환합니다.

#### Decode Base64
```javascript
const encoded = (item.content || '').replace(/\n/g, '');  // 줄바꿈 제거
const decoded = Buffer.from(encoded, 'base64').toString('utf-8');  // 디코딩
// 결과: 마크다운 원문 텍스트
```

#### Build Ollama Request
루프가 끝난 후 (Done 포트) 모든 파일 내용을 합산하여 프롬프트를 구성합니다.
```javascript
const items = $input.all();  // 모든 디코딩된 파일
const combined = items.map(i => `## ${i.json.name}\n\n${i.json.content}`).join('\n\n---\n\n');

const prompt = `Extract API endpoints, DB tables, and sequence steps from the docs below.
Return ONLY JSON:
{"endpoints":[{"method":"","path":"","description":""}],
 "tables":[{"name":"","columns":[]}],
 "sequences":[{"name":"","steps":[]}]}

Docs:
${combined.substring(0, 2000)}`;  // 2000자 제한 (LLM 컨텍스트 초과 방지)
```

#### Ollama Extract Structure
```
POST http://ollama:11434/api/generate
Body: { model: "qwen2.5-coder:7b", prompt: "...", stream: false }
timeout: 600000ms (10분)
neverError: true
```
로컬 LLM에 분석 요청. `stream: false`로 전체 응답을 한 번에 받습니다.

#### Parse & Build Output
LLM 응답에서 JSON을 추출합니다. LLM이 markdown 코드블록으로 감싸는 경우도 처리:
```javascript
const m = raw.match(/```json\s*([\s\S]*?)```/)  // ```json ... ``` 패턴
         || raw.match(/(\{[\s\S]*\})/);          // 순수 JSON 객체 패턴
```

**출력**:
```json
{
  "agent_id": "WBS-DDA",
  "repo_type": "design_doc",
  "endpoints": [
    { "method": "POST", "path": "/api/auth/login", "description": "사용자 로그인" }
  ],
  "tables": [
    { "name": "users", "columns": ["id", "email", "password", "created_at"] }
  ],
  "sequences": [
    { "name": "로그인 흐름", "steps": ["클라이언트 요청", "인증 확인", "토큰 발급"] }
  ],
  "error": null
}
```

---

## 6. WBS-BAK — Backend 코드 분석기

**파일**: `workflow/WBS-BAK.json`  
**Webhook**: `POST /webhook/wbs-bak`  
**목적**: Backend Repo의 최신 커밋에서 변경된 라우터/컨트롤러 파일을 AI로 분석하여 API 엔드포인트와 Call Flow 추출

### 6.1 전체 흐름

```
Webhook
  → Init Params            파라미터 파싱, repos 배열 → 1개씩 Item 분리
  → Loop Over Repos        [루프 시작]
      ├─ (Done) → Aggregate Results  여러 Repo 결과 취합
      │             → Respond to Webhook
      └─ (Loop) → GET Commits         GitHub API: 기간 내 커밋 목록
                → Extract Commit Info  커밋 SHA, 메타 정보 추출
                → GET Commit Files     최신 커밋의 변경 파일 목록
                → Build Ollama Request Backend 파일 필터링 + 프롬프트 구성
                → Ollama Extract Call Flow  AI 분석
                → Parse & Build Output    결과 파싱
                → Loop Over Repos      [다음 Repo로]
```

### 6.2 노드별 상세 설명

#### Init Params
```javascript
const since = body.since || new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(); // 기본: 7일 전
const until = body.until || new Date().toISOString();
// repos 배열을 1 repo = 1 item으로 변환
return repos.map(repo => ({ json: { owner, repo, since, until } }));
```

#### GET Commits
```
GET https://api.github.com/repos/{owner}/{repo}/commits?since={since}&until={until}&per_page=50
```
지정 기간 내 커밋 목록을 가져옵니다. 최대 50개.

#### Extract Commit Info
```javascript
// 커밋 URL에서 owner/repo 추출 (Init Params를 참조하지 않고 직접 파싱)
const m = commits[0].url.match(/repos\/([^/]+)\/([^/]+)\/commits/);
owner = m[1]; repo = m[2];

// 최신 5개 커밋 SHA 추출
const shas = commits.slice(0, 5).map(c => c.sha);

// 활성 개발일 계산 (커밋 날짜의 unique 날짜 수)
const activeDays = new Set(commits.map(c => c.commit.author.date.substring(0, 10)));

// _meta에 담아 Ollama 이후에도 참조 가능하게
return [{ json: { owner, repo, shas, commit_count, active_days, commit_messages, _meta: {...} } }];
```

#### GET Commit Files
```
GET https://api.github.com/repos/{owner}/{repo}/commits/{shas[0]}
```
가장 최신 커밋(`shas[0]`)에서 변경된 파일 전체 목록과 각 파일의 `patch`(diff)를 가져옵니다.

#### Build Ollama Request
변경 파일 중 Backend 관련 파일만 필터링합니다:

```javascript
const routerPatterns = [
  'routes/', 'controllers/', 'router.', 'controller.',
  'handler.', 'api/', 'endpoints/', 'route.'
];
// 패턴에 해당하는 파일만 선택, 없으면 .js/.ts/.py/.java 파일로 fallback
```

프롬프트:
```
Analyze backend code changes and extract API endpoints and call flow.
Return ONLY JSON:
{"endpoints":[{"method":"","path":"","description":""}],
 "call_flow":[{"from":"","to":"","handler":"","calls":[]}]}

Code changes:
[필터링된 파일의 patch 내용, 최대 2000자]
```

#### Parse & Build Output
```javascript
const meta = $('Build Ollama Request').first().json._meta;  // _meta 패턴으로 메타 복원
```

**출력**:
```json
{
  "agent_id": "WBS-BAK",
  "repo": "WBS_Check",
  "repo_type": "backend",
  "extracted_endpoints": [
    { "method": "POST", "path": "/api/auth/login", "description": "로그인" }
  ],
  "call_flow": [],
  "commit_count": 8,
  "active_days": 1,
  "commit_messages": ["Add routes for WBS-BAK test", ...],
  "error": null
}
```

#### Aggregate Results
여러 Repo를 분석한 경우 결과를 하나로 합칩니다.
```javascript
if (items.length === 1) return [items[0]];  // 단일 Repo면 그대로 반환
return [{ json: { agent_id: 'WBS-BAK', results: items.map(i => i.json) } }];
```

---

## 7. WBS-FRT — Frontend 코드 분석기

**파일**: `workflow/WBS-FRT.json`  
**Webhook**: `POST /webhook/wbs-frt`  
**목적**: Frontend Repo의 최신 커밋에서 컴포넌트/서비스 파일을 AI로 분석하여 API 호출 패턴과 화면 흐름 추출

### 7.1 전체 흐름

WBS-BAK와 동일한 구조이며, 파일 필터 패턴과 프롬프트만 다릅니다.

```
Webhook → Init Params → Loop Over Repos
  └─(Loop)→ GET Commits → Extract Commit Info → GET Commit Files
           → Build Ollama Request (Frontend 필터)
           → Ollama Extract API Calls
           → Parse & Build Output → Loop Over Repos
  └─(Done)→ Aggregate Results → Respond to Webhook
```

### 7.2 Frontend 파일 필터 패턴

```javascript
const frontendPatterns = [
  '.tsx', '.jsx',          // React 컴포넌트
  '.vue', '.svelte',       // Vue / Svelte 컴포넌트
  'service.ts', 'service.js',  // API 서비스 레이어
  '/api/', '/hooks/',      // API 호출 디렉토리 / React Hooks
  '/store/', '/pages/',    // 상태관리 / 페이지 컴포넌트
  '/views/', '/components/'  // 화면 / 공통 컴포넌트
];
// 없으면 .tsx/.jsx/.ts/.js/.vue/.svelte 파일로 fallback
```

### 7.3 Ollama 프롬프트

```
Analyze frontend code changes and extract API calls and screen flow.
Return ONLY JSON:
{"api_calls":[{"method":"","url":"","component":""}],
 "screen_flow":[{"from":"","to":"","trigger":""}],
 "call_flow":[{"from":"","to":"","handler":"","calls":[]}]}
```

### 7.4 출력

```json
{
  "agent_id": "WBS-FRT",
  "repo": "WBS_Check",
  "repo_type": "frontend",
  "api_calls": [
    { "method": "POST", "url": "/api/auth/login", "component": "authService.js" }
  ],
  "screen_flow": [],
  "call_flow": [],
  "commit_count": 8,
  "active_days": 1,
  "error": null
}
```

---

## 8. WBS-CFG — IaC/Config 분석기

**파일**: `workflow/WBS-CFG.json`  
**Webhook**: `POST /webhook/wbs-cfg`  
**목적**: Terraform, Kubernetes, Docker 등 인프라 설정 파일을 AI로 분석하여 구성 요소 추출 및 보안/설계 Gap 식별

### 8.1 전체 흐름

WBS-BAK와 동일한 구조.

### 8.2 Config 파일 필터 패턴

```javascript
const configPatterns = [
  '.tf', '.hcl',                     // Terraform
  '.yaml', '.yml',                   // Kubernetes, Helm, CI/CD
  'dockerfile', 'docker-compose',    // Docker
  'helm/', 'k8s/', 'kubernetes/',    // Helm Chart, K8s 매니페스트
  'helmfile', 'infra/', 'deploy/'    // Helmfile, 인프라 디렉토리
];
// 없으면 .yaml/.yml/.json/.toml/.ini/.conf 파일로 fallback
```

### 8.3 Ollama 프롬프트

```
Analyze IaC and config file changes. Extract infrastructure components and design gaps.
Return ONLY JSON:
{"components":[{"type":"","name":"","config":""}],
 "call_flow":[],
 "design_gaps":[{"item":"","discrepancy_type":"","severity":"","design":"","actual":""}]}
```

**design_gaps severity 기준**:
- `high`: 보안 취약점 (하드코딩 비밀번호, 평문 시크릿 등)
- `medium`: 설계 불일치, 불필요한 설정
- `low`: 권장 사항 미준수

### 8.4 출력

```json
{
  "agent_id": "WBS-CFG",
  "repo": "WBS_Check",
  "repo_type": "config",
  "components": [
    { "type": "service", "name": "app", "config": "image: node:18-alpine, port: 3000" },
    { "type": "service", "name": "postgres", "config": "image: postgres:15-alpine" },
    { "type": "volume", "name": "postgres_data", "config": "" }
  ],
  "design_gaps": [
    {
      "item": "postgres password",
      "discrepancy_type": "insecure",
      "severity": "high",
      "design": "비밀번호는 시크릿 매니저에 저장되어야 함",
      "actual": "POSTGRES_PASSWORD=secret 하드코딩"
    }
  ],
  "commit_count": 8,
  "active_days": 1,
  "error": null
}
```

---

## 9. WBS-MOB — Mobile 코드 분석기

**파일**: `workflow/WBS-MOB.json`  
**Webhook**: `POST /webhook/wbs-mob`  
**목적**: iOS(Swift), Android(Kotlin), Flutter(Dart) 코드에서 화면 전환 흐름과 API 호출 시퀀스 추출

### 9.1 전체 흐름

WBS-BAK와 동일한 구조.

### 9.2 Mobile 파일 필터 패턴

```javascript
const mobilePatterns = [
  '.swift',                              // iOS Swift
  '.kt',                                 // Android Kotlin
  '.dart',                               // Flutter Dart
  'viewcontroller', 'screen.',           // iOS ViewController, 화면 파일
  'activity.', 'fragment.',             // Android Activity, Fragment
  'viewmodel.',                          // MVVM ViewModel
  '/screens/', '/views/', '/widgets/',   // Flutter 화면/위젯
  '/services/', '/repositories/'         // 서비스/레포지토리 레이어
];
// 없으면 .swift/.kt/.dart/.java 파일로 fallback
```

### 9.3 Ollama 프롬프트

```
Analyze mobile code changes (iOS/Android/Flutter) and extract screen flow and API calls.
Return ONLY JSON:
{"screen_flow":[{"from":"","to":"","trigger":""}],
 "api_calls":[{"method":"","url":"","screen":""}],
 "call_flow":[{"from":"","to":"","handler":"","calls":[]}],
 "design_gaps":[{"item":"","discrepancy_type":"","severity":"","design":"","actual":""}]}
```

### 9.4 출력

```json
{
  "agent_id": "WBS-MOB",
  "repo": "WBS_Check",
  "repo_type": "mobile",
  "screen_flow": [
    { "from": "", "to": "LoginScreen", "trigger": "앱 시작 또는 세션 만료" }
  ],
  "api_calls": [
    { "method": "POST", "url": "https://api.example.com/api/auth/login", "screen": "LoginScreen" }
  ],
  "design_gaps": [
    {
      "item": "API endpoint",
      "discrepancy_type": "Potential security risk",
      "severity": "High",
      "design": "HTTPS 암호화 통신 필요",
      "actual": "평문 HTTP 사용"
    }
  ],
  "commit_count": 8,
  "active_days": 1,
  "error": null
}
```

---

## 10. WBS-INT — 통합 테스트 워크플로

**파일**: `workflow/WBS-INT.json`  
**Webhook**: `POST /webhook/wbs-int`  
**목적**: 6개 Specialist Agent를 순차 실행하고 통합 리포트 생성  
**노드 수**: 57개 처리 노드 + 8개 Sticky Note = 65개 총 노드

### 10.1 전체 흐름

```
Webhook
  → Init Params
  → [GRC 체인] 8개 노드
  → [DDA 체인] 9개 노드
  → [BAK 체인] 9개 노드
  → [FRT 체인] 9개 노드
  → [CFG 체인] 9개 노드
  → [MOB 체인] 9개 노드
  → Build Report
  → Respond to Webhook
```

각 에이전트 체인은 해당 에이전트의 전체 노드를 그대로 인라인으로 포함합니다.  
별도의 Webhook 호출 없이 단일 워크플로 내에서 실행됩니다.

### 10.2 Init Params (통합 버전)

```javascript
// 모든 에이전트 파라미터를 한 번에 처리
const owner = body.owner || $vars.GITHUB_OWNER || '';
const repos = body.repos || [];
const since = body.since || new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
const until = body.until || new Date().toISOString();

// DDA 전용 파라미터
const ddaRepo = body.dda_repo || $vars.DESIGN_DOC_REPO || '';
const ddaPath = body.dda_path || $vars.DESIGN_DOC_PATH || 'docs/design';
```

### 10.3 노드 이름 충돌 해결

6개 에이전트를 하나의 워크플로에 합칠 때 노드 이름이 중복됩니다.  
각 노드 이름에 에이전트 접두사를 붙여 구분합니다:

| 원본 노드 이름 | 통합 워크플로 노드 이름 |
|---------------|------------------------|
| `Extract Commit Info` | `BAK Extract Commit Info` |
| `Build Ollama Request` | `BAK Build Ollama Request` |
| `Loop Over Repos` | `BAK Loop Over Repos` |
| `$('Extract Commit Info')` (코드 내 참조) | `$('BAK Extract Commit Info')` |

### 10.4 Build Report 노드

6개 에이전트 결과를 종합하여 최종 리포트를 생성합니다.
```javascript
// 각 에이전트 결과 직접 참조
const grc = $('GRC Build Output').first().json;
const dda = $('DDA Parse & Build Output').first().json;
const bak = $('BAK Aggregate Results').first().json;
// ...

// PASS 판정: error 없고 agent_id 있으면 PASS
const ok = !r.error && bool(r.agent_id);
```

**최종 출력**:
```json
{
  "test_id": "WBS-INT-PHASE1",
  "tested_at": "2026-05-13T06:33:32.984Z",
  "total": 6,
  "passed": 6,
  "failed": 0,
  "result": "ALL_PASS",
  "agents": [
    {
      "agent_id": "WBS-GRC",
      "status": "PASS",
      "details": { "classified": [{ "repo": "WBS_Check", "type": "frontend", "reason": "Vite" }] }
    },
    {
      "agent_id": "WBS-DDA",
      "status": "PASS",
      "details": { "endpoint_count": 5, "table_count": 2, "sequence_count": 2 }
    }
  ],
  "raw": { "grc": {...}, "dda": {...}, "bak": {...}, "frt": {...}, "cfg": {...}, "mob": {...} }
}
```

### 10.5 실행 방법

```bash
curl -X POST http://localhost:5678/webhook/wbs-int \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "hanhosunglgu",
    "repos": ["WBS_Check"],
    "dda_repo": "hanhosunglgu/WBS_Check",
    "dda_path": "docs/design"
  }' \
  --max-time 1800
```

> 💡 **소요 시간**: Ollama CPU 기준 약 7~8분. 실행 전 Ollama 웜업 권장:
> ```bash
> curl -X POST http://localhost:11434/api/generate \
>   -H "Content-Type: application/json" \
>   -d '{"model":"qwen2.5-coder:7b","prompt":"hi","stream":false}'
> ```

---

## 11. 주요 기술 이슈 및 해결 방법

### 11.1 SplitInBatches 포트 순서

**문제**: SplitInBatches의 Done(완료)와 Loop(반복) 포트를 반대로 연결하면 루프가 동작하지 않음

**해결**: connections JSON에서 반드시 확인
```json
"Loop Over Repos": {
  "main": [
    [{ "node": "집계 노드", ... }],    ← index 0 = Done (루프 완료 후)
    [{ "node": "처리 노드", ... }]     ← index 1 = Loop (각 item 처리)
  ]
}
```

### 11.2 Ollama 응답 JSON 파싱 오류

**문제**: `specifyBody: "json"` + n8n 표현식이 포함된 jsonBody → "Invalid JSON" 에러

**해결**: 별도 Code 노드에서 완성된 JSON 객체를 만든 후 `JSON.stringify`로 직렬화
```javascript
// Code 노드 (Build Ollama Request)
return [{ json: { model: '...', prompt: '...', stream: false } }];

// HTTP Request 노드 jsonBody
={{ JSON.stringify({ model: $json.model, prompt: $json.prompt, stream: $json.stream }) }}
```

### 11.3 Webhook Timeout 초과

**문제**: 6개 에이전트 순차 실행 시 기본 300초 초과

**해결**: `.env`에서 timeout 연장
```
N8N_WEBHOOK_TIMEOUT=900
```

### 11.4 Ollama 응답 빈 값

**문제**: Ollama 첫 호출 시 모델 로드에 ~109초 소요 → timeout 발생

**해결**: 워크플로 실행 전 항상 웜업 요청 전송
```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5-coder:7b","prompt":"hi","stream":false}'
```

### 11.5 Webhook flat JSON 파싱

**문제**: n8n Webhook은 요청 바디를 `{ body: {...} }` 또는 `{...}` 두 가지 형태로 전달

**해결**: Init Params에서 항상 양쪽을 대응
```javascript
const input = $input.first().json;
const body = input.body || input;  // 중첩 여부 무관하게 처리
```

### 11.6 통합 워크플로 노드 참조 오류

**문제**: 6개 에이전트를 하나로 합칠 때 `$('Extract Commit Info')` 같은 코드 내 노드 참조가 중복 이름과 충돌

**해결**: 코드 내 모든 `$('노드이름')` 참조에 에이전트 접두사 추가
```javascript
// 변경 전
const meta = $('Build Ollama Request').first().json._meta;

// 변경 후 (BAK 에이전트의 경우)
const meta = $('BAK Build Ollama Request').first().json._meta;
```

---

## 부록: n8n Variables 등록 목록

n8n Settings → Variables에 등록되어야 하는 값들:

| 변수명 | 예시값 | 사용 에이전트 |
|--------|--------|--------------|
| `GITHUB_OWNER` | `hanhosunglgu` | GRC, BAK, FRT, CFG, MOB |
| `GITHUB_REPOS` | `["WBS_Check"]` | GRC |
| `DESIGN_DOC_REPO` | `hanhosunglgu/WBS_Check` | DDA |
| `DESIGN_DOC_PATH` | `docs/design` | DDA |
| `JIRA_BASE_URL` | `https://xxx.atlassian.net` | Phase 2 |
| `JIRA_PROJECT_KEYS` | `["WBS"]` | Phase 2 |
| `JIRA_BOARD_ID` | `8207` | Phase 2 |

## 부록: 파일 구조

```
3rdWBSAgent/
├── workflow/
│   ├── WBS-GRC.json    # Repo 분류기
│   ├── WBS-DDA.json    # 설계 문서 분석기
│   ├── WBS-BAK.json    # Backend 분석기
│   ├── WBS-FRT.json    # Frontend 분석기
│   ├── WBS-CFG.json    # IaC/Config 분석기
│   ├── WBS-MOB.json    # Mobile 분석기
│   └── WBS-INT.json    # 통합 테스트 워크플로 (65 노드)
└── doc/
    ├── task-plan.md    # 전체 Task 계획서
    └── phase1-guide.md # 이 문서
```
