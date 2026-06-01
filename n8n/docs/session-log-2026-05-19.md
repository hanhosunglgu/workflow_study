# 세션 로그 — 2026-05-19

## 목표
n8n 워크플로우 LLM 모델을 Ollama(qwen2.5-coder:7b) → OpenAI gpt-4.1-mini 로 전환

---

## 완료된 작업

### 1. 환경 설정
- `.env` 파일 위치: `/Users/hosunghan/workplace/self-hosted-ai-starter-kit/.env`
- `OPENAI_API_KEY` 추가 완료
- n8n 재시작 완료
- n8n Credentials에 OpenAI API Key 등록 완료

### 2. OpenAI 전환 대상 파일 확인
Ollama 사용 파일 (8개):
- WBS-BAK.json ✅ 이미 OpenAI URL + gpt-4.1-mini 설정됨
- WBS-FRT.json ✅ 이미 OpenAI URL + gpt-4.1-mini 설정됨
- WBS-CFG.json ✅ 이미 OpenAI URL + gpt-4.1-mini 설정됨
- WBS-MOB.json ✅ 이미 OpenAI URL + gpt-4.1-mini 설정됨
- WBS-DDA.json ✅ 이미 OpenAI URL + gpt-4.1-mini 설정됨
- WBS-ORK.json ⚠️ model 필드 누락 → 수정 완료
- WBS-INT.json (통합테스트용, 별도 처리)
- TEST-Ollama-LLM.json (테스트용, 제외)

### 3. WBS-ORK.json 수정 내용
- `Build Gap Analysis Prompt` 노드 jsCode에 추가:
  - `model: 'gpt-4.1-mini'`
  - `messages: [{ role: 'user', content: prompt }]`
  - `stream: false`
- `Ollama Gap Analysis` 노드명 → `OpenAI Gap Analysis` 변경
- connections 참조도 함께 업데이트

### 4. WBS-DDA.json 수정 내용
- `Ollama Extract Structure` 노드명 → `OpenAI Extract Structure` 변경
- `respondToWebhook` typeVersion: 1 → 1.1 변경
- `Loop Over Files` SplitInBatches 포트 순서 교체:
  - 수정 전: port0=Build Ollama Request(done), port1=GET File Content(loop 중) ❌
  - 수정 후: port0=GET File Content(loop 중), port1=Build Ollama Request(done) ✅

### 5. WBS-BAK/FRT/CFG/MOB.json 수정 내용
- `respondToWebhook` typeVersion: 1 → 1.1 변경
- `responseMode`: lastNode로 잘못 변경했다가 다시 responseNode로 복구
- `Loop Over Repos` SplitInBatches 포트 순서 교체:
  - 수정 전: port0=Aggregate Results(done), port1=GET Commits(loop 중) ❌
  - 수정 후: port0=GET Commits(loop 중), port1=Aggregate Results(done) ✅

---

## 현재 미해결 이슈

### WBS-DDA 테스트 실패
- 증상: `{"code":0,"message":"No Respond to Webhook node found in the workflow"}`
- 원인 추정: n8n UI에서 Import 후에도 DB에 반영이 안 되는 문제
- 시도한 것:
  1. respondToWebhook typeVersion 1→1.1 수정
  2. responseMode lastNode로 변경 후 복구
  3. SplitInBatches 포트 순서 수정
  4. 여러 차례 Import 시도
- 미확인 사항:
  - UI에서 Webhook 노드의 `Respond Mode` 설정값
  - UI에서 `Respond to Webhook` 노드 실제 존재 여부
  - n8n DB와 파일 간 sync 상태

---

## 다음 세션 작업 순서

1. WBS-DDA UI에서 직접 확인:
   - Webhook 노드 클릭 → `Respond Mode` = "Using 'Respond to Webhook' Node" 인지 확인
   - `Respond to Webhook` 노드 존재 여부 확인
2. WBS-DDA 테스트 통과 후 → WBS-BAK → WBS-FRT → WBS-CFG → WBS-MOB → WBS-ORK 순서로 테스트

---

## 파일 경로
- Workflow 파일: `/Users/hosunghan/workplace/mvp/3rdWBSAgent/n8n/workflow/`
- n8n: http://localhost:5678
- Docker container: n8n (n8nio/n8n:latest, Up 4 days)
- 환경변수 파일: `/Users/hosunghan/workplace/self-hosted-ai-starter-kit/.env`

---

## 세션 2 (오후) — WBS-DDA/RPT 완전 해결 및 E2E 재검증

**일시**: 2026-05-19 오후  
**상태**: ✅ 완료

### 작업 내역

#### WBS-DDA curl 오류 디버깅 → 재구현
1. Filter MD Files: GitHub API 404 → GET Design Doc List credential ID 비어있음 확인 → credential 제거 (public repo)
2. SplitInBatches typeVersion 3 → 루프 즉시 done 포트 탈출 → typeVersion 2로 수정
3. Build Ollama Request `$('Decode Base64').all()` → 미실행 오류 → Store File Content 노드 추가
4. download_url 방식으로 GitHub raw 텍스트 직접 fetch (base64 decode 불필요)
5. n8n 내장 OpenAI 노드 사용 (Community Edition Variables 미지원)
6. **최종 테스트 PASS**: endpoints=5, tables=2, sequences=2 ✅

#### WBS-RPT 수정
1. Confluence 노드 4개 제거
2. TEAMS_WEBHOOK_URL 하드코딩
3. retry 제거, executionOrder 제거
4. **Teams 채널 메시지 수신 확인** ✅

#### E2E 전체 테스트
- 전체 워크플로우 active 확인 후 WBS-ORK 트리거
- total_progress=0%, design_score=56%, teams_sent=true
- **Teams 채널 메시지 수신 확인** ✅

### 핵심 발견사항

1. **SplitInBatches 반드시 typeVersion 2** — v3는 executionOrder v1과 충돌
2. **Loop done 포트에서 루프 내 노드 참조 불가** — Store 노드로 누적 필수
3. **n8n 2.14.2 Community Edition Variables 없음** — Enterprise 전용, $vars 미동작
4. **OpenAI 호출은 내장 노드 + Credential** — HTTP Request 직접 호출 시 키 주입 불가

### 현재 상태
- 모든 워크플로우 active 및 정상 동작
- E2E 파이프라인 전 구간 검증 완료

---

## 세션 3 (오후 후반) — Teams Bot 진척률 명령 실동작 검증

**일시**: 2026-05-19 오후  
**상태**: ✅ 완료

### 작업 내역

#### WBS-TRG-001 활성화 및 Teams Bot 명령 테스트

1. WBS-TRG-001 Active 토글 ON
2. curl로 `진척률` 명령 테스트 → `IF 진척률` 분기 정상 통과 확인
   - `Invalid URL: v3/conversations//activities` 오류는 curl 테스트 한계 (convId 미제공) — 실제 Teams에서는 정상
3. Teams 채널에서 Bot에게 `진척률` 메시지 직접 전송
4. WBS-TRG-001 → WBS-ORK 트리거 → 전체 파이프라인 실행
5. Teams 채널 리포트 메시지 수신 확인 ✅

### 실행 결과

```
Teams Bot ("진척률")
  → WBS-TRG-001 ✅ SUCCESS
  → WBS-ORK ✅ SUCCESS
    → WBS-JRA / WBS-GRC / WBS-DDA / WBS-BAK / WBS-FRT / WBS-CFG / WBS-MOB
  → WBS-RPT → Teams 채널 리포트 전송 ✅
```

### 최종 활성화 워크플로우 목록

| 워크플로우 | 역할 | 상태 |
|-----------|------|------|
| WBS-TRG-001 | Teams Bot 명령 라우팅 | ✅ Active |
| WBS-ORK | Orchestration | ✅ Active |
| WBS-JRA | Jira Agent | ✅ Active |
| WBS-GRC | GitHub Classifier | ✅ Active |
| WBS-DDA | Design Doc Agent | ✅ Active |
| WBS-BAK | Backend Agent | ✅ Active |
| WBS-FRT | Frontend Agent | ✅ Active |
| WBS-CFG | Config Agent | ✅ Active |
| WBS-MOB | Mobile Agent | ✅ Active |
| WBS-RPT | Report Agent | ✅ Active |
