# 프로젝트 개요

**프로젝트명**: 3rd WBS Agent  
**버전**: v1.2  
**시작일**: 2026-05-08  
**Phase 1 완료**: 2026-05-13  
**엔진**: n8n Self-hosted  

---

## 목적

팀 리더/PM이 개발팀의 주간 진척률을 **자동으로 모니터링하고 보고받는** n8n 기반 Multi-Agent 자동화 시스템.

수작업 없이 Jira, GitHub, 설계 문서를 통합 분석하여 매주 금요일 17:00에 자동 리포트를 생성하거나, Teams Bot 명령으로 즉시 조회한다.

---

## 핵심 차별점

일반 진척률 집계 도구와 달리, **설계 문서 대비 실제 코드의 적합성**을 검증하는 것이 핵심 차별점이다.

| 기능 | 설명 |
|------|------|
| 설계 적합성 검증 | `.md` 설계 문서(API 명세/ERD/시퀀스)와 실제 소스코드를 비교하여 Gap 자동 추출 |
| LLM 의도 분석 | Gap이 의도적 개선인지, 실수/누락인지 Ollama LLM이 판단 |
| Call Flow 재구성 | Frontend → Backend → DB 전체 호출 흐름을 설계 vs 구현 기준으로 비교 |
| 통합 진척률 | Jira 티켓 상태 + Story Point + GitHub Commit 빈도를 가중 합산 |

---

## 사용 대상

| 역할 | 사용 방식 |
|------|-----------|
| 팀 리더 / PM | Teams Bot 명령, 자동 주간 리포트 수신 |

---

## Teams Bot 명령어

| 명령어 | 동작 |
|--------|------|
| `@WBSAgent 진척률` | 현재 시점 진척률 리포트 즉시 생성 |
| `@WBSAgent 진척률 [repo명]` | 특정 repo 진척률 조회 |
| `@WBSAgent 티켓 [JIRA-ID]` | 특정 Jira 티켓 상태 조회 |
| `@WBSAgent 코드검증 [repo명]` | 특정 repo 설계 적합성 검증 실행 |
| `@WBSAgent 도움말` | 명령어 목록 출력 |

---

## 기술 스택

| 컴포넌트 | 기술 |
|----------|------|
| Workflow Engine | n8n (Self-hosted) |
| Trigger | Microsoft Teams Webhook, n8n Cron |
| 이슈 관리 | Jira Cloud API v3 |
| 소스 관리 | GitHub REST API v3 |
| LLM | Ollama (`qwen2.5-coder:7b`, 로컬 Docker) |
| 설계 문서 입력 | `.md` 파일 (GitHub repo 지정 경로) |
| Multi-Agent 프레임워크 | n8n Sub-workflow + Execute Workflow 노드 |

---

## 진척률 계산 방식

| 지표 | 가중치 | 계산식 |
|------|--------|--------|
| Jira 티켓 상태 | 40% | Done 티켓 수 / 전체 티켓 수 × 100 |
| Story Point 소진률 | 40% | 완료 SP / 전체 Sprint SP × 100 |
| GitHub Commit 빈도 | 20% | 활성 commit 일수 / 5일 × 100 |

| 등급 | 범위 |
|------|------|
| 🟢 Green (정상) | 80% 이상 |
| 🟡 Yellow (주의) | 50~79% |
| 🔴 Red (위험) | 49% 이하 |

---

## 설계 적합성 심각도 분류

| 심각도 | 기준 |
|--------|------|
| 🔴 High | 동작이 달라지는 변경 (엔드포인트 삭제, 필수 파라미터 제거) |
| 🟡 Medium | 스펙은 바뀌었으나 기능적으로 유사 (필드명 변경, 타입 변경) |
| 🟢 Low | 설계 외 추가 구현 (새 엔드포인트, 추가 컬럼) |
