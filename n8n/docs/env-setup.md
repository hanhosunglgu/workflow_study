# n8n 환경변수 설정 가이드

**작성일**: 2026-05-11  

n8n Self-hosted 서버의 `.env` 파일(또는 `docker-compose.yml` environment 섹션)에 아래 변수들을 추가한다.  
변수를 추가한 뒤 n8n 서버를 재시작해야 Workflow에서 `$env.VAR_NAME`으로 참조할 수 있다.

---

## 1. Teams Bot 자격증명 (Task 0.2.1 — 보안 이관 완료)

```env
# Microsoft Teams Bot Framework
TEAMS_TENANT_ID=dbebe70a-4a50-48cc-b5a1-e047510c68a9
TEAMS_CLIENT_ID=5708513a-9c38-4991-b5f4-bf66c6996889
TEAMS_CLIENT_SECRET=<your-client-secret>
```

> ⚠️ `.env` 파일은 반드시 `.gitignore`에 포함시켜 버전 관리에서 제외할 것.

---

## 2. GitHub (Task 0.2.2)

```env
# GitHub PAT — 권한: repo (read), read:org
GITHUB_PAT=<발급한_PAT_입력>
GITHUB_OWNER=<organization_또는_username>
# 분석 대상 Repo 목록 (JSON 배열 형식)
GITHUB_REPOS=["repo-a","repo-b","repo-c"]
```

---

## 3. Jira (Task 0.2.3)

```env
# Jira Cloud API Token
JIRA_BASE_URL=https://<your-domain>.atlassian.net
JIRA_USER_EMAIL=<jira_계정_이메일>
JIRA_API_TOKEN=<발급한_API_토큰_입력>
JIRA_PROJECT_KEYS=["PROJ","WBS"]
```

---

## 4. Ollama LLM (Task 0.2.4)

```env
# Ollama (로컬 Docker 컨테이너)
OLLAMA_HOST=ollama:11434
OLLAMA_MODEL=qwen2.5-coder:7b
```

---

## 5. Teams Workflows Webhook URL (Task 4.1 — Phase 4 신규)

```env
# Teams Workflows Webhook URL
# 설정 방법: Teams 채널 → 워크플로 앱 → "채널에 웹후크 알림 보내기" 템플릿 → URL 복사
TEAMS_WEBHOOK_URL=https://prod-xx.westus.logic.azure.com/<your_webhook_url>
```

> 참고: TEAMS_CLIENT_ID / TEAMS_CLIENT_SECRET (Teams Bot Framework 답장용) 과 별개.  
> TEAMS_WEBHOOK_URL은 단방향 push 전용 (WBS-RPT → Teams 채널 메시지 전송).  
> Teams Workflows Webhook은 `{ "text": "..." }` 형식만 지원.

---

## 6. 설계 문서 경로 (Task 0.3.2)

```env
# 설계 문서가 저장된 GitHub Repo 및 경로
DESIGN_DOC_REPO=hanhosunglgu/WBS_Check
DESIGN_DOC_PATH=WBS_Check/docs/design
```

---

## 적용 방법

### Docker Compose 사용 시

```yaml
# docker-compose.yml
services:
  n8n:
    environment:
      - TEAMS_TENANT_ID=${TEAMS_TENANT_ID}
      - TEAMS_CLIENT_ID=${TEAMS_CLIENT_ID}
      - TEAMS_CLIENT_SECRET=${TEAMS_CLIENT_SECRET}
      - GITHUB_PAT=${GITHUB_PAT}
      # ... 이하 동일
```

### n8n 직접 실행 시

```bash
# .env 파일 로드 후 n8n 실행
export $(cat .env | xargs) && n8n start
```

### 재시작 후 확인

n8n Workflow 에디터에서 Code 노드 또는 Expression 창에 아래 입력 후 정상 출력되면 등록 완료:

```
{{ $env.TEAMS_TENANT_ID }}
```
