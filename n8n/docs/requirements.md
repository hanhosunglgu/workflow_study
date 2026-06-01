# 개발 진척률 모니터링 Agent 요구사항 명세서

**프로젝트명**: 3rd WBS Agent  
**작성일**: 2026-05-08  
**버전**: v1.0  

---

## 1. 프로젝트 개요

### 1.1 목적

팀 리더/PM이 개발팀의 주간 진척률을 자동으로 모니터링하고 보고받을 수 있는 n8n 기반 자동화 Agent 시스템을 구축한다.

### 1.2 핵심 가치

- **자동화**: 수작업 없이 주간 진척률 자동 수집 및 보고
- **통합**: Jira, GitHub, Microsoft Teams를 하나의 워크플로우로 연결
- **가시성**: PM/팀 리더가 코드 수준까지 진척 상황을 파악 가능
- **가이드 준수 검증**: 프로젝트 가이드라인(MD 파일) 대비 실제 개발 품질 검증

### 1.3 사용 대상

| 역할 | 사용 방식 |
|------|-----------|
| 팀 리더 / PM | Teams Bot 명령 호출, 자동 주간 리포트 수신 |

---

## 2. 시스템 아키텍처

### 2.1 구성 요소

#### 2.1.1 전체 시스템 구성도

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │                        외부 트리거 레이어                                  │
 │                                                                          │
 │   [Teams Bot Webhook]          [n8n Cron Scheduler]                     │
 │    (수동 명령 수신)              (매주 금요일 17:00)                        │
 └────────────────────────┬─────────────────────────────────────────────────┘
                          │
                          ▼
 ┌──────────────────────────────────────────────────────────────────────────┐
 │                     n8n Workflow Engine (Self-hosted)                    │
 │                                                                          │
 │  ┌─────────────────────────────────────────────────────────────────────┐ │
 │  │              Orchestration Agent (WBS-ORK)                          │ │
 │  │                                                                     │ │
 │  │  1. GitHub Repo 목록 스캔 → Repo 유형 분류                           │ │
 │  │     (Backend / Frontend / Config / Mobile)                          │ │
 │  │  2. Specialist Agent 병렬 호출                                       │ │
 │  │  3. 각 Agent 결과 수집 → 전체 Call Flow 재구성                       │ │
 │  │  4. 설계 문서 시퀀스 vs 실제 구현 흐름 통합 비교                      │ │
 │  │  5. 진척률 계산 → 최종 리포트 생성                                    │ │
 │  └────────┬──────────┬────────────┬──────────────┬─────────────────────┘ │
 │           │(병렬)    │(병렬)      │(병렬)        │(병렬)                  │
 │           ▼          ▼            ▼              ▼                        │
 │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
 │  │ Jira Agent   │ │GitHub Repo   │ │ Design Doc   │ │ Report Agent     │ │
 │  │ (WBS-JRA)    │ │ Classifier   │ │ Agent        │ │ (WBS-RPT)        │ │
 │  │              │ │ (WBS-GRC)    │ │ (WBS-DDA)    │ │                  │ │
 │  │ Sprint 티켓  │ │              │ │              │ │ Teams 메시지     │ │
 │  │ 수집 및      │ │ Repo 유형    │ │ 설계 문서    │ │ Teams 채널       │ │
 │  │ 진척률 집계  │ │ 분류 →       │ │ 파싱 및      │ │ 메시지 전송       │ │
 │  │              │ │ Specialist   │ │ 시퀀스 추출  │ │                  │ │
 │  │              │ │ Agent 라우팅 │ │              │ │                  │ │
 │  └──────────────┘ └──────┬───────┘ └──────────────┘ └──────────────────┘ │
 │                          │                                                │
 │           ┌──────────────┼──────────────┬──────────────┐                 │
 │           ▼              ▼              ▼              ▼                  │
 │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
 │  │ Backend      │ │ Frontend     │ │ Config/IaC   │ │ Mobile Agent     │ │
 │  │ Agent        │ │ Agent        │ │ Agent        │ │ (WBS-MOB)        │ │
 │  │ (WBS-BAK)    │ │ (WBS-FRT)    │ │ (WBS-CFG)    │ │                  │ │
 │  │              │ │              │ │              │ │ iOS/Android/     │ │
 │  │ API 엔드포인 │ │ 컴포넌트 트리│ │ 인프라 설계  │ │ Flutter          │ │
 │  │ 트 추출      │ │ 분석         │ │ vs 실제      │ │ 화면 흐름 분석   │ │
 │  │ Call Flow    │ │ 이벤트 흐름  │ │ 구성 비교    │ │                  │ │
 │  │ 시퀀스 생성  │ │ 시퀀스 생성  │ │              │ │                  │ │
 │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘ │
 └──────────────────────────────────────────────────────────────────────────┘
          │                                      │
          ▼                                      ▼
 ┌─────────────────────┐              ┌─────────────────────┐
 │   외부 데이터 소스   │              │   출력 채널          │
 │                     │              │                     │
 │  • Jira Cloud API   │              │  • Teams 채널 메시지 │
 │  • GitHub REST API  │              │                     │
 │  • 설계 문서 (.md)  │              │                     │
 │  • Ollama LLM (로컬) │              │                     │
 └─────────────────────┘              └─────────────────────┘
```

#### 2.1.2 Agent 역할 정의

| Agent ID | 이름 | 역할 | 사용 도구 |
|----------|------|------|-----------|
| WBS-ORK | Orchestration Agent | 전체 워크플로우 조율, Repo 유형 분류, 결과 통합, Call Flow 재구성 | n8n Workflow, Ollama API |
| WBS-JRA | Jira Agent | Sprint 티켓 수집, 상태 집계, Story Point 소진률 계산 | Jira Cloud API |
| WBS-GRC | GitHub Repo Classifier | Repo 목록 스캔, 언어/구조 분석으로 유형 분류, Commit 수집 | GitHub REST API |
| WBS-DDA | Design Doc Agent | 설계 문서 (.md) 파싱, API 명세/ERD/시퀀스 구조 추출 | GitHub REST API (설계 문서 파일 읽기) |
| WBS-BAK | Backend Agent | API 엔드포인트/라우터 추출, DB 모델 분석, 서비스 간 Call Flow 시퀀스 생성 | GitHub REST API, Ollama API |
| WBS-FRT | Frontend Agent | 컴포넌트 트리 분석, API 호출 패턴 추출, 화면-API 연결 시퀀스 생성 | GitHub REST API, Ollama API |
| WBS-CFG | Config/IaC Agent | 인프라 설계 문서 vs 실제 Terraform/k8s 구성 비교 | GitHub REST API, Ollama API |
| WBS-MOB | Mobile Agent | iOS/Android/Flutter 화면 흐름 및 API 호출 시퀀스 분석 | GitHub REST API, Ollama API |
| WBS-RPT | Report Agent | Teams 채널 메시지 전송 | Teams Workflows Webhook |

#### 2.1.3 Orchestration Agent 상세 동작

```
[Step 1] Repo 유형 분류
  ├─ GitHub API로 Repo 목록 조회
  ├─ 각 Repo의 주요 언어, 디렉토리 구조, 파일 패턴 분석
  │    • package.json + React → Frontend
  │    • pom.xml / requirements.txt / node(express) → Backend
  │    • *.tf / k8s manifests / Dockerfile → Config/IaC
  │    • Podfile / build.gradle / pubspec.yaml → Mobile
  └─ 분류 결과 → 해당 Specialist Agent 호출 목록 결정

[Step 2] 병렬 Agent 호출
  ├─ WBS-JRA : Jira 데이터 수집 (독립 실행)
  ├─ WBS-DDA : 설계 문서 파싱 (독립 실행)
  └─ Specialist Agents (분류된 유형에 따라 선택적 병렬 실행)
       WBS-BAK / WBS-FRT / WBS-CFG / WBS-MOB

[Step 3] Call Flow 재구성
  ├─ WBS-DDA 결과: 설계 문서의 시퀀스 다이어그램 (설계 흐름)
  ├─ Specialist Agent 결과: 실제 코드에서 추출한 호출 흐름
  ├─ Orchestration Agent가 두 흐름을 레이어별로 정렬
  │    Frontend → Backend API → Service → DB 순으로 연결
  └─ 통합 시퀀스: [설계 흐름] vs [실제 구현 흐름] 비교 맵 생성

[Step 4] Gap 분석 및 최종 통합
  ├─ 설계 vs 구현 불일치 항목 통합 (High/Medium/Low)
  ├─ 진척률 계산 (Jira 상태 + Story Point + Commit 빈도)
  └─ WBS-RPT 호출 → 리포트 생성 및 전송
```

### 2.2 데이터 흐름

```
Trigger (Teams Bot 명령 / 매주 금요일 17:00)
  │
  ▼
[WBS-ORK] Repo 유형 분류
  │
  ├─── [WBS-JRA] Jira Sprint 티켓 수집 ──────────────────────┐
  ├─── [WBS-DDA] 설계 문서 파싱 (API 명세/ERD/시퀀스 추출) ──┤
  ├─── [WBS-BAK] Backend 코드 Call Flow 추출 ────────────────┤ 결과
  ├─── [WBS-FRT] Frontend 컴포넌트/API 호출 흐름 추출 ───────┤ 수집
  ├─── [WBS-CFG] Config/IaC 설계 vs 실제 비교 ──────────────┤
  └─── [WBS-MOB] Mobile 화면 흐름 및 API 시퀀스 추출 ────────┘
                                                             │
  ◄────────────────────────────────────────────────────────┘
  │
  ▼
[WBS-ORK] 결과 통합
  ├─ 설계 시퀀스 vs 실제 구현 흐름 통합 비교
  ├─ 서비스 간 전체 Call Flow 재구성
  ├─ 불일치(Gap) 항목 통합 및 심각도 분류
  └─ 진척률 계산
  │
  ▼
[WBS-RPT]
  └─ Teams 채널: 주간 진척률 + 설계 적합성 리포트 전송
```

---

## 3. 기능 요구사항

### 3.1 Trigger 시스템

#### 3.1.1 자동 트리거

| 항목 | 내용 |
|------|------|
| 실행 주기 | 매주 금요일 17:00 |
| 대상 | n8n Cron 스케줄러 |
| 동작 | 전체 주간 진척률 리포트 자동 생성 및 전송 |

#### 3.1.2 수동 트리거 (Teams Bot 명령어)

| 명령어 | 설명 |
|--------|------|
| `@WBSAgent 진척률` | 현재 시점 진척률 리포트 즉시 생성 |
| `@WBSAgent 진척률 [repo명]` | 특정 repo 진척률 조회 |
| `@WBSAgent 티켓 [JIRA-ID]` | 특정 Jira 티켓 상태 조회 |
| `@WBSAgent 코드검증 [repo명]` | 특정 repo 가이드 준수 검증 실행 |
| `@WBSAgent 도움말` | 명령어 목록 출력 |

- Teams Webhook을 통해 Bot 메시지 수신
- n8n에서 Webhook 노드로 Teams Bot 이벤트 처리

---

### 3.2 Jira 연동

#### 3.2.1 티켓 구조

```
Epic
 └─ Story
      └─ Task (Sub-task)
```

#### 3.2.2 이번 주 할일 조회 조건

- 현재 활성 Sprint에 할당된 Story / Task 조회
- 상태 필터: `To Do`, `In Progress`, `Done`
- 조회 범위: 연동된 모든 Jira Project

#### 3.2.3 수집 데이터

| 필드 | 설명 |
|------|------|
| 티켓 ID | `PROJ-123` 형식 |
| 티켓 유형 | Epic / Story / Task |
| 제목 | 티켓 Summary |
| 상태 | To Do / In Progress / In Review / Done |
| Story Point | 추정 포인트 (없으면 0 처리) |
| 담당자 | Assignee |
| 연결된 Epic | Parent Epic |
| 업데이트 일시 | 마지막 상태 변경 시각 |

---

### 3.3 GitHub 연동

#### 3.3.1 분석 범위

- 지정된 다수의 Repository 대상
- 이번 주(월요일 00:00 ~ 금요일 23:59) 기간 내 활동

#### 3.3.2 수집 데이터

| 항목 | 내용 |
|------|------|
| Commit 목록 | 이번 주 commit SHA, 메시지, 작성자, 일시 |
| PR 목록 | 이번 주 생성/merge된 PR 목록 |
| 변경 파일 | commit별 변경된 파일 목록 |

#### 3.3.3 Jira 티켓 매핑

- Commit 메시지에서 Jira 티켓 ID 패턴 추출: `[PROJ-\d+]` 또는 `PROJ-\d+`
- 추출된 티켓 ID로 해당 Jira 티켓과 연결
- 매핑 결과를 기반으로 "commit이 연결된 Jira 티켓" vs "commit 없는 Jira 티켓" 분류

---

### 3.4 설계 적합성 검증 (Design Conformance)

설계 문서(최초 설계 기준)와 실제 구현된 소스코드를 비교하여, 설계대로 개발되었는지 또는 개발 과정에서 설계가 변경되었는지를 추적하고 분석한다.

#### 3.4.1 설계 문서 입력

PM/리더가 직접 제공하는 `.md` 형식의 설계 문서를 입력으로 사용한다.

| 설계 문서 유형 | 포함 내용 |
|---------------|-----------|
| API 명세서 (Swagger/OpenAPI) | 엔드포인트 경로, HTTP 메서드, 요청/응답 파라미터, 상태 코드 |
| ERD / DB 스키마 설계 | 테이블명, 컬럼명/타입, 관계(FK), 인덱스 |
| 시스템 아키텍처 문서 | 컴포넌트 구성, 서비스 간 의존관계, 레이어 구조 |

- 파일 위치: 지정 GitHub repo 내 특정 경로 (n8n 환경변수로 설정)
- 문서가 여러 파일로 나뉜 경우 모두 로드하여 통합 분석

#### 3.4.2 정적 비교 검증

설계 문서와 실제 코드를 구조적으로 비교하여 자동 감지:

| 검증 대상 | 설계 문서 기준 | 실제 코드 비교 방법 |
|-----------|--------------|-------------------|
| API 엔드포인트 | 설계된 경로/메서드 목록 | GitHub에서 라우터 파일 파싱, 실제 경로 추출 |
| API 파라미터 | 설계된 요청/응답 필드명·타입 | 컨트롤러/스키마 코드에서 필드 추출 후 비교 |
| DB 테이블/컬럼 | ERD에 정의된 테이블·컬럼·타입 | 마이그레이션 파일 또는 ORM 모델 코드에서 추출 |
| 컴포넌트 구조 | 아키텍처 문서의 모듈/레이어 정의 | 디렉토리 구조 및 import 관계 분석 |

감지 결과 분류:

- **설계에 있으나 구현 없음**: 미구현 항목
- **구현에 있으나 설계 없음**: 설계 외 추가 구현 항목
- **설계와 스펙 불일치**: 구현은 됐으나 명세(파라미터명, 타입 등)가 다른 항목

#### 3.4.3 LLM 의도 분석

정적 비교에서 감지된 불일치 항목에 대해 LLM(Ollama)이 의도를 분석한다.

- **입력**: 설계 문서 원문 + 해당 불일치 코드 + 관련 Commit 메시지
- **분석 관점**:
  - 불일치가 의도적 개선인가, 실수/누락인가, 설계 반영 지연인가
  - 변경이 기능적으로 동등한가(명칭만 다름), 아니면 동작이 달라졌는가
- **출력 형식** (JSON):

```json
{
  "item": "POST /api/user/register",
  "design": "요청 필드: username, password, email",
  "actual": "요청 필드: user_name, password, email_address",
  "discrepancy_type": "spec_changed",
  "intent_analysis": "필드명이 snake_case로 변경됨. 의도적 컨벤션 통일로 보이나 설계 문서 미반영 상태",
  "severity": "medium"
}
```

#### 3.4.4 불일치 심각도 분류

| 심각도 | 기준 | 예시 |
|--------|------|------|
| 🔴 High | 동작이 달라지는 변경 (엔드포인트 삭제, 필수 파라미터 제거, 테이블 누락) | 설계된 API가 구현되지 않음 |
| 🟡 Medium | 스펙은 바뀌었으나 기능적으로 유사 (필드명 변경, 타입 변경) | 응답 필드명이 설계와 다름 |
| 🟢 Low | 설계 외 추가 구현 (새 엔드포인트, 추가 컬럼) | 설계에 없는 편의 API 추가 |

---

### 3.5 진척률 계산

#### 3.5.1 계산 지표

| 지표 | 가중치 | 계산 방식 |
|------|--------|-----------|
| Jira 티켓 상태 | 40% | Done 티켓 수 / 전체 이번 주 티켓 수 × 100 |
| Story Point 소진률 | 40% | 완료된 Story Point 합 / 전체 Sprint Story Point 합 × 100 |
| GitHub Commit 빈도 | 20% | 이번 주 활성 commit 일수 / 5일 × 100 |

#### 3.5.2 진척률 등급

| 등급 | 범위 | 색상 표시 |
|------|------|-----------|
| 정상 | 80% 이상 | 🟢 Green |
| 주의 | 50~79% | 🟡 Yellow |
| 위험 | 49% 이하 | 🔴 Red |

---

### 3.6 리포트 출력

#### 3.6.1 Teams 채널 메시지 형식

```
📊 [WBS Agent] 주간 개발 진척률 리포트
📅 기간: 2026-05-04 (월) ~ 2026-05-08 (금)

━━━━━━━━━━━━━━━━━━━━━
🎯 전체 진척률: 73% 🟡 주의
━━━━━━━━━━━━━━━━━━━━━

📋 Jira 티켓 현황
  • 전체: 12개 | ✅ 완료: 6개 | 🔄 진행중: 4개 | ⏳ 미착수: 2개
  • Story Point: 24 / 40 소진 (60%)

💻 GitHub 활동
  • Commit: 23회 (repo-A: 15, repo-B: 8)
  • PR: 3개 merge
  • 활성 개발일: 4/5일

📌 미완료 티켓 (이번 주 목표 미달)
  • [PROJ-45] 로그인 API 구현 - In Progress (담당: 홍길동)
  • [PROJ-48] 단위 테스트 작성 - To Do (담당: 미배정)

🔍 설계 적합성: 87% (불일치 5건)
  🔴 High: API /user/register 파라미터 스펙 변경 (1건)
  🟡 Medium: DB 컬럼명 불일치 (2건)
  🟢 Low: 설계 외 추가 구현 (2건)

```

---

## 4. 비기능 요구사항

### 4.1 성능

| 항목 | 목표값 |
|------|--------|
| 리포트 생성 시간 | 2분 이내 (자동 트리거 기준) |
| Teams Bot 응답 시간 | 30초 이내 (수동 명령 기준) |
| API 호출 실패 재시도 | 최대 3회, 30초 간격 |

### 4.2 가용성

- n8n Self-hosted 서버 기준 운영
- API 오류 시 에러 내용을 Teams 채널로 알림
- 부분 실패 시 (예: GitHub API 실패) 가능한 데이터만으로 리포트 생성

### 4.3 보안

| 항목 | 처리 방법 |
|------|-----------|
| API 키 관리 | n8n Credential 기능으로 암호화 저장 |
| Jira API Token | n8n Jira Credential 사용 |
| GitHub PAT | n8n GitHub Credential 사용 |
| Ollama LLM | 로컬 Docker 컨테이너 (http://ollama:11434) |
| Teams Webhook URL | n8n 환경변수로 관리 |

### 4.4 확장성

- Repo 목록은 n8n 워크플로우 환경변수로 관리 (추가/삭제 용이)
- Jira Project 목록도 환경변수로 관리
- MD 가이드 파일 교체 시 워크플로우 수정 없이 파일만 교체

---

## 5. 기술 스택

| 컴포넌트 | 기술 |
|----------|------|
| Workflow Engine | n8n (Self-hosted) |
| Trigger | Microsoft Teams Webhook, n8n Cron |
| 이슈 관리 | Jira Cloud API v3 |
| 소스 관리 | GitHub REST API v3 |
| LLM | Ollama (qwen2.5-coder:7b, 로컬 Docker) |

| 설계 문서 | `.md` 파일 (GitHub repo 내 지정 경로 저장) |
| Multi-Agent 프레임워크 | n8n Sub-workflow + Execute Workflow 노드 |

---

## 6. n8n Multi-Agent Workflow 구성

### 6.1 Workflow(Agent) 목록

| Workflow ID | Agent 이름 | 유형 | 설명 |
|-------------|-----------|------|------|
| `WBS-TRG-001` | Teams Trigger | Trigger | Teams Bot Webhook 수신 및 명령 파싱 |
| `WBS-TRG-002` | Scheduler Trigger | Trigger | 매주 금요일 17:00 Cron 실행 |
| `WBS-ORK` | Orchestration Agent | Orchestrator | Repo 분류, 병렬 Agent 호출, 결과 통합, Call Flow 재구성 |
| `WBS-JRA` | Jira Agent | Specialist | Sprint 티켓 수집, 상태 집계, Story Point 계산 |
| `WBS-GRC` | GitHub Repo Classifier | Specialist | Repo 스캔 및 Backend/Frontend/Config/Mobile 유형 분류 |
| `WBS-DDA` | Design Doc Agent | Specialist | 설계 문서 파싱, API 명세/ERD/시퀀스 추출 |
| `WBS-BAK` | Backend Agent | Specialist | API 라우터/컨트롤러 분석, 서비스 Call Flow 시퀀스 생성 |
| `WBS-FRT` | Frontend Agent | Specialist | 컴포넌트 트리 및 API 호출 패턴 분석, 화면 흐름 시퀀스 생성 |
| `WBS-CFG` | Config/IaC Agent | Specialist | Terraform/k8s 실제 구성 vs 설계 비교 |
| `WBS-MOB` | Mobile Agent | Specialist | iOS/Android/Flutter 화면 흐름 및 API 시퀀스 분석 |
| `WBS-RPT` | Report Agent | Output | Teams 채널 메시지 전송 |

### 6.2 n8n Workflow 실행 구조

```
[WBS-TRG-001] Teams Webhook
[WBS-TRG-002] Cron Scheduler
       │
       ▼
[WBS-ORK] Orchestration Agent
  │
  ├─ Execute Workflow → [WBS-GRC] GitHub Repo Classifier
  │    └─ 결과: { backend: [...], frontend: [...], config: [...], mobile: [...] }
  │
  ├─ 병렬 Execute Workflow (Split in Batches 노드)
  │    ├─ [WBS-JRA]  Jira Agent
  │    ├─ [WBS-DDA]  Design Doc Agent
  │    ├─ [WBS-BAK]  Backend Agent       ← WBS-GRC 결과에 해당 Repo만 전달
  │    ├─ [WBS-FRT]  Frontend Agent      ← WBS-GRC 결과에 해당 Repo만 전달
  │    ├─ [WBS-CFG]  Config/IaC Agent    ← WBS-GRC 결과에 해당 Repo만 전달
  │    └─ [WBS-MOB]  Mobile Agent        ← WBS-GRC 결과에 해당 Repo만 전달
  │
  ├─ Merge 노드: 전체 Agent 결과 대기 및 취합
  │
  ├─ Code 노드: Call Flow 재구성
  │    ├─ 설계 시퀀스 (WBS-DDA) vs 실제 흐름 (WBS-BAK/FRT/CFG/MOB) 비교
  │    └─ 레이어별 통합 흐름: Mobile/Frontend → Backend → Config/DB
  │
  ├─ HTTP Request 노드 (Ollama API): Gap 의도 분석
  │    └─ 불일치 항목별 High/Medium/Low 심각도 판정
  │
  └─ Execute Workflow → [WBS-RPT] Report Agent
```

### 6.3 Orchestration Agent 내부 노드 구성

```
Webhook / Cron
  → [Set 노드] 실행 파라미터 초기화 (주간 날짜 범위, Repo 목록)
  → [Execute: WBS-GRC] Repo 유형 분류
  → [IF 노드] 각 유형별 분기 (Backend 있으면 WBS-BAK 포함 등)
  → [Split in Batches] 병렬 Agent 실행
  → [Merge 노드] 전체 결과 수집 대기
  → [Code 노드] Call Flow 재구성 및 Gap 계산
  → [HTTP Request] Ollama API 의도 분석
  → [Code 노드] 진척률 계산 (Jira + SP + Commit)
  → [Execute: WBS-RPT] 리포트 생성 및 전송
```

### 6.4 Specialist Agent 간 데이터 인터페이스

각 Specialist Agent는 아래 표준 Output 스키마로 결과를 반환하여 Orchestration Agent가 통합한다.

```json
{
  "agent_id": "WBS-BAK",
  "repo": "api-server",
  "repo_type": "backend",
  "call_flow": [
    {
      "from": "Frontend",
      "to": "POST /api/auth/login",
      "handler": "AuthController.login()",
      "calls": ["AuthService.validate()", "UserRepository.findByEmail()"]
    }
  ],
  "design_gaps": [
    {
      "item": "POST /api/user/register",
      "discrepancy_type": "spec_changed",
      "severity": "high",
      "design": "필드: username, password, email",
      "actual": "필드: user_name, password, email_address"
    }
  ],
  "commit_count": 15,
  "active_days": 4
}
```

---

## 7. 인터페이스 명세

### 7.1 Jira API 사용 엔드포인트

| 기능 | 엔드포인트 |
|------|-----------|
| 활성 Sprint 조회 | `GET /rest/agile/1.0/board/{boardId}/sprint?state=active` |
| Sprint 이슈 조회 | `GET /rest/agile/1.0/sprint/{sprintId}/issue` |
| 이슈 상세 조회 | `GET /rest/api/3/issue/{issueId}` |

### 7.2 GitHub API 사용 엔드포인트

| 기능 | 엔드포인트 |
|------|-----------|
| Commit 목록 | `GET /repos/{owner}/{repo}/commits?since={date}&until={date}` |
| PR 목록 | `GET /repos/{owner}/{repo}/pulls?state=all&sort=updated` |
| 파일 내용 | `GET /repos/{owner}/{repo}/contents/{path}` |

### 7.3 Ollama LLM

| 항목 | 설정 |
|------|------|
| 모델 | `qwen2.5-coder:7b` |
| 호출 Agent | WBS-ORK (통합 Gap 분석), WBS-BAK, WBS-FRT, WBS-CFG, WBS-MOB (각 코드 흐름 추출) |
| 용도 1 (Specialist) | 소스코드 분석 → Call Flow 시퀀스 추출, 설계 문서와 비교 |
| 용도 2 (Orchestrator) | 불일치 항목의 의도 분석 (개선/실수/누락 판단), 심각도 분류 |
| 입력 | 설계 문서 원문 + 해당 소스코드 + 관련 Commit 메시지 |
| 출력 | Call Flow JSON, Gap 목록, 심각도, 의도 분석 결과 (JSON) |

---

## 8. MD 가이드 파일 형식

PM/리더가 작성할 가이드 파일의 권장 구조:

```markdown
# 프로젝트 개발 가이드

## 디렉토리 구조
(필수 구조 명세)

## 네이밍 규칙
(파일명, 함수명, 변수명 규칙)

## 필수 파일
(프로젝트에 반드시 존재해야 하는 파일 목록)

## 금지 사항
(절대 사용하면 안 되는 패턴, 라이브러리, 코드 스타일)

## 코드 스타일
(린트 규칙, 포맷팅 기준)
```

---

## 9. 개발 단계 계획

### Phase 1: 기반 구축
- [ ] n8n Self-hosted 환경 설정 및 Credential 등록 (Jira/GitHub/Ollama)
- [ ] WBS-TRG-001: Teams Bot Webhook 수신 및 명령 파싱 구현
- [ ] WBS-TRG-002: Cron 스케줄러 (금요일 17:00) 설정
- [ ] WBS-JRA: Jira Agent — Sprint 티켓 수집 및 상태/SP 집계
- [ ] WBS-GRC: GitHub Repo Classifier — Repo 언어/구조 스캔 및 유형 분류

### Phase 2: Specialist Agent 구현
- [ ] WBS-DDA: Design Doc Agent — 설계 문서 파싱 (API 명세/ERD/시퀀스 추출)
- [ ] WBS-BAK: Backend Agent — 라우터/컨트롤러 분석, Call Flow 시퀀스 생성
- [ ] WBS-FRT: Frontend Agent — 컴포넌트/API 호출 패턴 분석, 화면 흐름 시퀀스 생성
- [ ] WBS-CFG: Config/IaC Agent — Terraform/k8s 설계 vs 실제 비교
- [ ] WBS-MOB: Mobile Agent — iOS/Android/Flutter 화면 흐름 분석
- [ ] 표준 Output 스키마 정의 및 각 Agent 출력 검증

### Phase 3: Orchestration 및 통합
- [ ] WBS-ORK: Orchestration Agent — 병렬 실행 조율 및 결과 취합
- [ ] Call Flow 재구성 로직 — 설계 시퀀스 vs 실제 구현 흐름 통합 비교
- [ ] Ollama LLM 연동 — Gap 의도 분석 (개선/실수/누락 판단) 및 심각도 분류
- [ ] WBS-RPT: Report Agent — Teams 메시지 전송

### Phase 4: 안정화
- [ ] 각 Agent API 호출 실패 재시도 로직 (최대 3회)
- [ ] 부분 실패 처리 — 특정 Agent 실패 시 가용 데이터로 리포트 생성
- [ ] 전체 E2E 시나리오 테스트 및 검증

---

## 10. 용어 정의

| 용어 | 정의 |
|------|------|
| Sprint | Jira의 시간 단위 이터레이션 (보통 1~2주) |
| Story Point | 개발 작업량의 상대적 추정치 |
| PAT | Personal Access Token (GitHub 인증 토큰) |
| Webhook | 이벤트 발생 시 HTTP 요청을 전송하는 콜백 URL |
| WBS | Work Breakdown Structure (업무 분류 체계) |
| 설계 문서 | 개발 착수 전 작성된 API 명세서, ERD, 아키텍처 문서의 총칭 (`.md` 형식으로 제공) |
| 설계 적합성 | 설계 문서 대비 실제 구현의 일치 정도를 나타내는 지표 |
| 불일치 (Discrepancy) | 설계와 구현 간 차이 (미구현, 설계 외 추가, 스펙 변경) |
| 의도 분석 | LLM이 불일치의 원인을 의도적 개선/실수/누락으로 판단하는 과정 |
