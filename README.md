# ixi-Enterprise workflow 의 이해를 위한 N8N 프로젝트 개발기

ixi-enterprise 플로우 카탈로그를 학습하고, n8n Self-hosted 환경에서 실제 Multi-Agent 자동화 시스템을 직접 구현하며 n8n 워크플로우를 체득한 기록입니다.

---

## 프로젝트 구성

```
workflow_study/
├── ixi-enterprise/         # ixi-enterprise 플로우 카탈로그 분석 문서
│   └── docs/               # 노드 카탈로그, 플로우 분석, 보안 에이전트 요구사항 등
├── n8n/                    # WBS Check Agent 구현물
│   ├── workflow/           # n8n 워크플로우 JSON 파일 (13개 Agent)
│   └── docs/               # 개발 가이드, Phase별 구현 기록, wiki
├── n8n_project-summary.md  # 전체 프로젝트 요약 (아키텍처, 노드 상세, 이슈 목록)
├── n8n_guide.md            # n8n 핵심 개념 및 사용 가이드
└── n8n_vs_ai_agent.md      # n8n과 AI Agent 프레임워크 비교 분석
```

---

## WBS Check Agent 개요

팀 리더/PM이 개발팀의 주간 진척률을 수작업 없이 자동으로 모니터링하고 보고받는 n8n 기반 Multi-Agent 자동화 시스템.

- **Jira** 스프린트 티켓·Story Point 수집
- **GitHub** Commit/PR 활동 분석
- **설계 문서(.md)** 대비 실제 코드 적합성 검증
- **Microsoft Teams** 채널에 주간 리포트 자동 발송 및 Bot 명령 응답

### Agent 구성 (13개)

| Agent | 역할 |
|-------|------|
| WBS-TRG-001 | Teams Bot 명령 수신·파싱·라우팅 |
| WBS-ORK | 전체 오케스트레이터 (26노드) |
| WBS-JRA | Jira Sprint 티켓·SP 수집 (13노드) |
| WBS-GRC | GitHub Repo 분류 + Commit/PR 집계 (20노드) |
| WBS-DDA | 설계 문서 파싱·Gap 탐지 (9노드) |
| WBS-BAK | Backend 코드 분석·Call Flow 추출 (12노드) |
| WBS-FRT | Frontend API 호출 패턴 분석 (12노드) |
| WBS-CFG | IaC/Config 분석·Gap 추출 (12노드) |
| WBS-MOB | Mobile 화면 흐름·API 시퀀스 분석 (12노드) |
| WBS-RPT | Teams Adaptive Card 리포트 발송 (7노드) |
| WBS-INT | 통합 테스트 (57노드) |
| WBS-TRG-002 | Cron 스케줄러 (3노드) |
| WBS-ERR | 전역 에러 핸들러 (4노드) |

### 진척률 계산 공식

```
total_progress = Jira 티켓 완료율 × 40%
               + Story Point 소진율 × 40%
               + GitHub 커밋 활성일률 × 20%
```

---

## ixi-enterprise 플로우 카탈로그 분석

ixi-enterprise에서 제공하는 n8n 플로우 패턴을 분석한 문서 모음입니다.

| 문서 | 내용 |
|------|------|
| 01-node-catalog.md | n8n 노드 종류 및 용도 정리 |
| 02-current-flow-analysis.md | 현재 플로우 구조 분석 |
| 03-n8n-implementation.md | n8n 구현 방법론 |
| 05~11-flow-*.md | RAG, Agent Tool, Routing, Human Loop, Guardrail, MCP 플로우 패턴 |
| 12-security-agent-requirements.md | 보안 솔루션 5종 연동 에이전트 요구사항 |

---

## 기술 스택

| 항목 | 내용 |
|------|------|
| Workflow Engine | n8n Self-hosted (Docker) |
| LLM | OpenAI gpt-4.1-mini |
| 이슈 관리 | Jira Cloud API v3 |
| 소스 관리 | GitHub REST API v3 |
| 알림 | Microsoft Teams (Adaptive Card) |
| 터널 | cloudflared |

---

## 개발 기간

2026-05-08 ~ 2026-05-20 (Phase 0~5 + Post 버그 수정 완료)
