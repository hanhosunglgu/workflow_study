# 3rd WBS Agent — Wiki

**마지막 업데이트**: 2026-05-20  
**작성 방식**: Karpathy LLM Wiki 패턴 — LLM이 원본 소스를 컴파일하여 작성, 사람이 읽는 용도

---

## 목차

| 문서 | 설명 |
|------|------|
| [project-overview.md](./project-overview.md) | 프로젝트 목적, 배경, 핵심 가치 |
| [architecture.md](./architecture.md) | 시스템 아키텍처, Agent 구성, 데이터 흐름 |
| [agents.md](./agents.md) | 각 Agent 역할 및 입출력 스키마 |
| [environment.md](./environment.md) | 환경변수, 자격증명, n8n 설정 |
| [progress.md](./progress.md) | 구현 진척 현황 (Phase별 완료 상태) |
| [phase2.md](./phase2.md) | Phase 2 개발 내역, 이슈 해결, 테스트 결과 |
| [phase3.md](./phase3.md) | Phase 3 개발 내역, 이슈 해결, 테스트 결과 |
| [dev-log.md](./dev-log.md) | 개발 이력 및 주요 결정 사항 |

---

## 빠른 현황

```
Phase 0 (환경 준비)      ████████████████████  완료 (11/11)
Phase 1 (Specialist)    ████████████████████  완료 (37/37) ✅ 2026-05-13
Phase 2 (진척률 수집)    ████████████████████  완료 (10/10) ✅ 2026-05-14
Phase 3 (Orchestration) ████████████████████  완료 (16/16) ✅ 2026-05-14
Phase 4 (리포트 출력)    ████████████████████  완료 (Teams) ✅ 2026-05-14
Phase 5 (Trigger+안정화) ████████████████████  완료        ✅ 2026-05-15
Post-Phase (버그 수정)   ████████████████████  완료        ✅ 2026-05-20
```

---

## Phase 4 완료 요약 (2026-05-14)

WBS-RPT Report Agent 구현 완료, Teams 메시지 전송 **PASS**.

| 항목 | 결과 |
|------|------|
| WBS-RPT 노드 수 | 11노드 (Teams 경로) |
| Teams 전송 | ✅ `teams_sent: true, teams_status: 200` |
| 메시지 형식 | Adaptive Card v1.0 (`TextBlock + FactSet`) — Teams Workflows Webhook 호환 |
| 전송 포맷 | `{ attachments: [{ contentType: 'application/vnd.microsoft.card.adaptive', content: card }] }` |
| WBS-ORK 연동 | `Call WBS-RPT` 노드(ork-0026) 추가, Calc Progress Score 이후 병렬 호출 |
| Teams 채널 수신 | ✅ 개발팀 > WBS 모니터링 채널 메시지 수신 확인 |

---

## Phase 3 완료 요약 (2026-05-14)

WBS-ORK Orchestration Agent 구현 완료, 테스트 **PASS**.

| 항목 | 결과 |
|------|------|
| WBS-ORK 노드 수 | 25노드 (Webhook/Schedule/Manual 3종 트리거 포함) |
| 병렬 Agent 호출 | 6개 동시 실행 (JRA/DDA/BAK/FRT/CFG/MOB) |
| 부분 실패 처리 | failed_agents 목록화, 기본값 대체 후 계속 진행 |
| 진척률 계산 | Jira 40% + SP 40% + Commit 20% |
| 설계 적합성 | HIGH Gap 기준 차감 점수 산출 |
| 테스트 결과 | total_progress: 4% RED, design_score: 70% YELLOW, failed_agents: [WBS-DDA] |

---

## Phase 2 완료 요약 (2026-05-14)

WBS-JRA 신규 구현 + WBS-GRC Commit 집계 확장, 테스트 **3/3 PASS**.

| 항목 | 결과 |
|------|------|
| WBS-JRA | Sprint 조회, 한글 상태 집계(진행 중:2, 해야 할 일:2) 정상 |
| WBS-GRC | Commit 집계(8회), 활성 개발일(1일), PR 집계 정상 |
| 연동 테스트 | commit_messages → jira_commit_map 매핑 정확 |

**다음 단계**: 실운영 모니터링

---

## Post-Phase 버그 수정 완료 (2026-05-20)

실운영 중 발견된 버그 수정 및 안정화.

| 항목 | 결과 |
|------|------|
| WBS-FRT/CFG/MOB 재작성 | Webhook 응답 없음(No Respond to Webhook) 오류 해결 ✅ |
| WBS-DDA 재구현 | splitInBatches 완전 제거, GitHub PAT 인증 추가, OpenAI 전환 ✅ |
| design_score 10 버그 수정 | `/webhook/` 경로를 endpoint 비교 대상에서 제외 ✅ |
| n8n REST API 캐시 갱신 | n8n API 키 생성 + PUT API로 워크플로 업데이트 ✅ |
| docs/design 설계 문서 생성 | api-design.md, db-schema.md, sequence-design.md GitHub 업로드 ✅ |

**최종 검증 결과** (2026-05-20):

| 항목 | 값 |
|------|-----|
| total_progress | 20% (RED) |
| design_score | 100% (GREEN) |
| teams_sent | true |
| failed_agents | [] |

---

## Phase 1 완료 요약 (2026-05-13)

6개 Specialist Agent 전원 구현 및 통합 테스트 **6/6 ALL_PASS**.

| Agent | 결과 |
|-------|------|
| WBS-GRC | WBS_Check → frontend (Vite) 분류 확인 |
| WBS-DDA | endpoints=5, tables=2, sequences=2 추출 |
| WBS-BAK | routes/index.js에서 5개 엔드포인트 추출 |
| WBS-FRT | src/api/authService.js에서 5개 API 호출 추출 |
| WBS-CFG | docker-compose.yml 2 services + design_gaps 3건 |
| WBS-MOB | screen_flow=1, api_calls=1, design_gaps=2 |
| WBS-INT | 6개 통합 워크플로 57노드, 실행시간 약 7~8분 |
