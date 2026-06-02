# 보안 통합 Agent 시스템 요구사항 명세서

**문서 번호**: REQ-SEC-001  
**작성일**: 2026-05-15  
**최종 수정**: 2026-05-18 (ixi-enterprise Guardrail 연결 제약 반영)  
**버전**: 1.1  
**상태**: 초안 (인터뷰 기반)

---

## 1. 프로젝트 개요

### 1.1 배경

ixi-enterprise 플로우 카탈로그의 **2-2 사내 시스템 연동 Agent** 패턴을 기반으로, 사내 보안 솔루션 5종과 연동하는 **통합 보안 AI 에이전트**를 n8n으로 구현한다.

실제 보안 솔루션은 사내 인프라에 종속되어 있으므로, 개발 및 검증 단계에서는 **Python FastAPI 기반 Mock 서버**로 각 솔루션 API를 시뮬레이션한다.

### 1.2 목표

| 목표 | 설명 |
|------|------|
| 통합 보안 조회 | 채팅 한 줄로 5개 보안 솔루션 현황 통합 조회 |
| 상태 변경 | 취약점 조치 완료 처리, 탐지 알림 확인 등 제한적 쓰기 |
| Human Approval 적용 | 상태 변경 작업은 반드시 사람 승인 후 실행 |
| Mock 서버 연동 | FastAPI 기반 Mock으로 실제 API 응답 구조 시뮬레이션 |

### 1.3 연동 대상 보안 솔루션

| 솔루션 | 개발사 | 카테고리 | 인증 방식 |
|--------|--------|---------|---------|
| **SolidStep** | 에스에스알(SSR) | CCE 취약점 진단 자동화 | API Key |
| **MetiEye** | 에스에스알(SSR) | 실시간 웹쉘 탐지/차단 | API Key |
| **Prisma CSPM** | Palo Alto Networks | 클라우드 보안 태세 관리 | JWT (Access Key 발급) |
| **CCE** | KISA 기준 | 주요정보통신기반시설 취약점 진단 | API Key |
| **Server-i** | 소만사 | 서버 DLP / 개인정보 보호 | API Key |

---

## 2. 시스템 아키텍처

### 2.1 전체 구성도

```
[사용자]
   │ 자연어 채팅
   ▼
[n8n Chat Trigger]
   │
   ▼
[n8n AI Agent]
  Model: azure_openai:gpt-4.1-mini
  System Prompt: 통합 보안 어시스턴트
   │
   ├──(Tool)── [HTTP Request] → SolidStep Mock Server  :8001
   │           CCE 취약점 진단 결과 조회/상태 변경
   │
   ├──(Tool)── [HTTP Request] → MetiEye Mock Server    :8002
   │           웹쉘 탐지 이벤트 조회/알림 확인 처리
   │
   ├──(Tool)── [HTTP Request] → Prisma CSPM Mock Server:8003
   │           클라우드 보안 알림/정책 위반 조회
   │
   ├──(Tool)── [HTTP Request] → CCE Mock Server        :8004
   │           KISA 기준 취약점 항목 진단 결과 조회
   │
   └──(Tool)── [HTTP Request] → Server-i Mock Server   :8005
               서버 개인정보 탐지/취약점 현황 조회
   │
   ▼
[Human Approval] ← 상태변경 작업 시에만 활성화
   │ 승인
   ▼
[HTTP Request] → 해당 Mock Server (실제 변경 실행)
   │
   ▼
[Chat Output]
```

### 2.2 배포 환경

```
로컬 개발 환경:
  n8n          : http://localhost:5678  (기존 Docker 실행)
  SolidStep    : http://localhost:8001  (uvicorn 실행)
  MetiEye      : http://localhost:8002  (uvicorn 실행)
  Prisma CSPM  : http://localhost:8003  (uvicorn 실행)
  CCE          : http://localhost:8004  (uvicorn 실행)
  Server-i     : http://localhost:8005  (uvicorn 실행)

실행 명령어 (각 Mock 서버):
  uvicorn solidstep_mock:app --port 8001 --reload
  uvicorn metieye_mock:app   --port 8002 --reload
  uvicorn prisma_mock:app    --port 8003 --reload
  uvicorn cce_mock:app       --port 8004 --reload
  uvicorn serveri_mock:app   --port 8005 --reload
```

---

## 3. 기능 요구사항

### 3.1 FR-001: SolidStep CCE 취약점 진단 연동

#### 3.1.1 개요
SolidStep은 IT 인프라(서버, 네트워크 장비, DB)의 보안 취약점을 자동 진단하는 솔루션이다. 1,000개 이상의 진단 항목을 기반으로 취약점 수준을 상/중/하로 분류한다.

#### 3.1.2 조회 API (GET)

**취약점 목록 조회**
```
GET /api/v1/vulnerabilities
Headers: X-API-Key: {api_key}
Query Params:
  - severity: HIGH | MEDIUM | LOW  (선택)
  - status: OPEN | IN_PROGRESS | RESOLVED  (선택)
  - target_type: SERVER | NETWORK | DB | PC  (선택)
  - limit: int (기본값 20)
  - page: int (기본값 1)

Response 200:
{
  "total": 147,
  "page": 1,
  "limit": 20,
  "items": [
    {
      "vuln_id": "SS-2026-0001",
      "title": "SSH 루트 로그인 허용",
      "severity": "HIGH",
      "category": "계정 관리",
      "target": "web-server-01",
      "target_type": "SERVER",
      "status": "OPEN",
      "detected_at": "2026-05-10T09:00:00Z",
      "cce_id": "CCE-54-1",
      "description": "SSH 설정에서 PermitRootLogin이 yes로 설정됨",
      "recommendation": "PermitRootLogin no로 변경 권장"
    }
  ]
}
```

**요약 통계 조회**
```
GET /api/v1/vulnerabilities/summary
Headers: X-API-Key: {api_key}

Response 200:
{
  "total": 147,
  "by_severity": { "HIGH": 12, "MEDIUM": 58, "LOW": 77 },
  "by_status": { "OPEN": 89, "IN_PROGRESS": 23, "RESOLVED": 35 },
  "by_target_type": { "SERVER": 62, "NETWORK": 31, "DB": 29, "PC": 25 },
  "last_scan_at": "2026-05-15T06:00:00Z",
  "compliance_score": 72.4
}
```

**개별 취약점 상세 조회**
```
GET /api/v1/vulnerabilities/{vuln_id}
Headers: X-API-Key: {api_key}

Response 200:
{
  "vuln_id": "SS-2026-0001",
  "title": "SSH 루트 로그인 허용",
  "severity": "HIGH",
  "category": "계정 관리",
  "target": "web-server-01",
  "target_ip": "192.168.1.10",
  "target_type": "SERVER",
  "os": "CentOS 7.9",
  "status": "OPEN",
  "detected_at": "2026-05-10T09:00:00Z",
  "cce_id": "CCE-54-1",
  "check_item": "U-01",
  "check_detail": "/etc/ssh/sshd_config 파일의 PermitRootLogin 설정 확인",
  "description": "SSH 설정에서 PermitRootLogin이 yes로 설정됨",
  "recommendation": "PermitRootLogin no 로 변경 후 sshd 서비스 재시작",
  "cvss_score": 7.2,
  "reference": "KISA CCE 가이드 U-01"
}
```

#### 3.1.3 상태 변경 API (PATCH) — Human Approval 필수

**취약점 상태 변경**
```
PATCH /api/v1/vulnerabilities/{vuln_id}/status
Headers: X-API-Key: {api_key}
Body:
{
  "status": "IN_PROGRESS" | "RESOLVED",
  "comment": "조치 내용 설명",
  "updated_by": "hong.gildong"
}

Response 200:
{
  "vuln_id": "SS-2026-0001",
  "previous_status": "OPEN",
  "current_status": "IN_PROGRESS",
  "updated_by": "hong.gildong",
  "updated_at": "2026-05-15T14:30:00Z",
  "comment": "SSH 설정 수정 작업 착수"
}
```

---

### 3.2 FR-002: MetiEye 웹쉘 탐지 연동

#### 3.2.1 개요
MetiEye는 웹 서버에서 신·변종 웹쉘, 악성코드 URL, DB쉘 등을 실시간 탐지하고 격리 조치하는 솔루션이다. S.R.O.A 알고리즘으로 실시간 탐지 속도를 18배 향상시킨 특허 기술을 보유한다.

#### 3.2.2 조회 API (GET)

**탐지 이벤트 목록 조회**
```
GET /api/v1/detections
Headers: X-API-Key: {api_key}
Query Params:
  - type: WEBSHELL | MALWARE | DBSHELL | DEFACEMENT  (선택)
  - status: DETECTED | QUARANTINED | CONFIRMED_SAFE  (선택)
  - server: 서버명 (선택)
  - from: ISO8601 날짜 (선택)
  - to: ISO8601 날짜 (선택)
  - limit, page

Response 200:
{
  "total": 34,
  "items": [
    {
      "event_id": "ME-2026-0088",
      "type": "WEBSHELL",
      "filename": "upload_1715.php",
      "filepath": "/var/www/html/uploads/upload_1715.php",
      "server": "web-server-02",
      "server_ip": "192.168.1.11",
      "detected_at": "2026-05-15T13:42:00Z",
      "status": "QUARANTINED",
      "risk_score": 95,
      "detection_method": "PATTERN_MATCH",
      "pattern_id": "WS-PHP-001",
      "file_hash": "a3f5c2e1d4b6...",
      "file_size": 2048
    }
  ]
}
```

**탐지 통계 조회**
```
GET /api/v1/detections/summary
Headers: X-API-Key: {api_key}

Response 200:
{
  "total_today": 7,
  "total_week": 34,
  "by_type": { "WEBSHELL": 18, "MALWARE": 9, "DBSHELL": 4, "DEFACEMENT": 3 },
  "by_status": { "DETECTED": 5, "QUARANTINED": 27, "CONFIRMED_SAFE": 2 },
  "high_risk_count": 12,
  "monitored_servers": 15,
  "last_scan_at": "2026-05-15T14:00:00Z"
}
```

#### 3.2.3 상태 변경 API (PATCH) — Human Approval 필수

**탐지 이벤트 처리 상태 변경**
```
PATCH /api/v1/detections/{event_id}/action
Headers: X-API-Key: {api_key}
Body:
{
  "action": "CONFIRM_THREAT" | "CONFIRM_SAFE" | "DELETE_FILE",
  "comment": "처리 내용",
  "handled_by": "security.team"
}

Response 200:
{
  "event_id": "ME-2026-0088",
  "previous_status": "QUARANTINED",
  "current_status": "CONFIRMED_THREAT",
  "action_taken": "CONFIRM_THREAT",
  "handled_by": "security.team",
  "handled_at": "2026-05-15T14:35:00Z"
}
```

---

### 3.3 FR-003: Prisma CSPM 클라우드 보안 연동

#### 3.3.1 개요
Palo Alto Networks Prisma Cloud CSPM은 AWS, Azure, GCP 등 멀티 클라우드 환경의 보안 태세를 관리한다. 공개 REST API를 제공하며, Access Key로 JWT를 발급받아 인증한다.

#### 3.3.2 인증 API

**JWT 토큰 발급** (10분 유효)
```
POST /login
Body:
{
  "username": "{access_key_id}",
  "password": "{secret_key}"
}

Response 200:
{
  "token": "eyJhbGciOiJSUzI1NiJ9...",
  "message": "login successful",
  "customerNames": [{ "customerName": "company-name", "prismaId": "..." }]
}
```

#### 3.3.3 조회 API (GET)

**보안 알림(Alert) 목록 조회**
```
GET /alert/v2/list
Headers: x-redlock-auth: {jwt_token}
Body (POST로도 가능):
{
  "timeRange": { "type": "relative", "value": { "unit": "day", "amount": 7 }},
  "filters": [
    { "name": "alert.status", "operator": "=", "value": "open" },
    { "name": "policy.severity", "operator": "=", "value": "high" }
  ],
  "limit": 50
}

Response 200:
{
  "totalRows": 128,
  "items": [
    {
      "id": "P-2026-0042",
      "status": "open",
      "severity": "high",
      "policy": {
        "name": "AWS S3 버킷 공개 접근 허용",
        "policyType": "config",
        "complianceMetadata": [{ "standardName": "CIS AWS", "requirementId": "2.1.5" }]
      },
      "resource": {
        "name": "company-data-bucket",
        "resourceType": "AWS S3 Bucket",
        "cloudType": "aws",
        "region": "ap-northeast-2",
        "accountId": "123456789012"
      },
      "firstSeen": "2026-05-10T00:00:00Z",
      "lastSeen": "2026-05-15T12:00:00Z"
    }
  ]
}
```

**컴플라이언스 현황 조회**
```
GET /compliance/posture/v2
Headers: x-redlock-auth: {jwt_token}
Query: limit=10

Response 200:
{
  "items": [
    {
      "name": "CIS AWS v1.4.0",
      "description": "CIS Amazon Web Services Foundations Benchmark",
      "passedPolicies": 143,
      "failedPolicies": 22,
      "passPercent": 86.7
    }
  ]
}
```

#### 3.3.4 상태 변경 API (POST) — Human Approval 필수

**알림 해제 (Dismiss)**
```
POST /alert/v2/dismiss
Headers: x-redlock-auth: {jwt_token}
Body:
{
  "ids": ["P-2026-0042"],
  "dismissalNote": "임시 비즈니스 예외 승인됨",
  "dismissalTimeRange": { "type": "relative", "value": { "unit": "day", "amount": 30 }}
}

Response 200:
{ "successful": ["P-2026-0042"], "failed": [] }
```

---

### 3.4 FR-004: CCE 취약점 기준 관리 연동

#### 3.4.1 개요
KISA의 주요정보통신기반시설 기술적 취약점 분석·평가 기준(CCE)을 기반으로 진단 항목을 관리하고 진단 결과를 조회한다. SolidStep이 CCE 항목을 자동 진단하는 솔루션이라면, 이 Mock은 CCE 항목 자체를 관리하는 독립 시스템으로 구성한다.

#### 3.4.2 조회 API (GET)

**CCE 항목 목록 조회**
```
GET /api/v1/cce/items
Headers: X-API-Key: {api_key}
Query Params:
  - platform: UNIX | WINDOWS | NETWORK | DB | WEB | CLOUD  (선택)
  - category: 계정관리 | 서비스관리 | 패치관리 | 로그관리 | 기능관리  (선택)
  - severity: 상 | 중 | 하  (선택)

Response 200:
{
  "total": 262,
  "items": [
    {
      "item_id": "U-01",
      "platform": "UNIX",
      "category": "계정관리",
      "severity": "상",
      "title": "root 계정 원격 접속 제한",
      "check_description": "시스템 정책에 root 계정으로 원격접속 제한 여부 점검",
      "diagnostic_criteria": {
        "vulnerable": "/etc/securetty 파일 내 pts/0~x 설정 존재 시",
        "safe": "/etc/securetty 파일에 pts 설정이 없거나 파일 미존재 시"
      },
      "reference": "KISA CCE 가이드 2026"
    }
  ]
}
```

**진단 결과 조회**
```
GET /api/v1/cce/results
Headers: X-API-Key: {api_key}
Query Params:
  - target: 점검 대상 서버명
  - severity: 상 | 중 | 하
  - result: VULNERABLE | SAFE | NA

Response 200:
{
  "target": "db-server-01",
  "scan_date": "2026-05-14",
  "total_items": 72,
  "vulnerable": 8,
  "safe": 60,
  "na": 4,
  "items": [
    {
      "item_id": "U-01",
      "title": "root 계정 원격 접속 제한",
      "severity": "상",
      "result": "VULNERABLE",
      "evidence": "PermitRootLogin yes 설정 확인됨",
      "recommendation": "PermitRootLogin no로 변경 필요"
    }
  ]
}
```

---

### 3.5 FR-005: Server-i 서버 DLP 연동

#### 3.5.1 개요
소만사의 Server-i는 서버 내 개인정보 탐지(DLP), 서버 취약점 상시 점검, 악성코드/랜섬웨어 차단 기능을 제공한다. 제1금융기관 최다 도입 솔루션이다.

#### 3.5.2 조회 API (GET)

**개인정보 탐지 현황 조회**
```
GET /api/v1/pii-detections
Headers: X-API-Key: {api_key}
Query Params:
  - server: 서버명 (선택)
  - pii_type: RESIDENT_ID | PHONE | CREDIT_CARD | ACCOUNT | EMAIL  (선택)
  - status: DETECTED | MASKED | DELETED  (선택)
  - limit, page

Response 200:
{
  "total": 523,
  "items": [
    {
      "detection_id": "SI-2026-1021",
      "server": "file-server-01",
      "file_path": "/data/hr/employee_list_2026.xlsx",
      "pii_type": "RESIDENT_ID",
      "pii_count": 342,
      "file_size": 1048576,
      "status": "DETECTED",
      "detected_at": "2026-05-15T02:00:00Z",
      "risk_level": "HIGH"
    }
  ]
}
```

**서버 보안 현황 요약**
```
GET /api/v1/servers/security-status
Headers: X-API-Key: {api_key}

Response 200:
{
  "monitored_servers": 42,
  "items": [
    {
      "server": "file-server-01",
      "server_ip": "192.168.1.20",
      "os": "RHEL 8.6",
      "pii_detection_count": 523,
      "vulnerability_count": 12,
      "malware_count": 0,
      "last_scan_at": "2026-05-15T02:00:00Z",
      "risk_level": "HIGH",
      "agent_status": "ACTIVE"
    }
  ]
}
```

**악성코드/랜섬웨어 탐지 현황**
```
GET /api/v1/malware-detections
Headers: X-API-Key: {api_key}
Query Params:
  - threat_type: MALWARE | RANSOMWARE | VIRUS (선택)
  - status: DETECTED | BLOCKED | QUARANTINED (선택)

Response 200:
{
  "total": 3,
  "items": [
    {
      "detection_id": "SI-MAL-2026-001",
      "server": "app-server-03",
      "threat_type": "RANSOMWARE",
      "filename": "update.exe",
      "filepath": "/tmp/update.exe",
      "status": "BLOCKED",
      "detected_at": "2026-05-14T23:15:00Z",
      "threat_name": "Ransom.WannaCry",
      "action_taken": "AUTO_BLOCKED"
    }
  ]
}
```

#### 3.5.3 상태 변경 API (PATCH) — Human Approval 필수

**개인정보 파일 처리 요청**
```
PATCH /api/v1/pii-detections/{detection_id}/action
Headers: X-API-Key: {api_key}
Body:
{
  "action": "MASK" | "DELETE" | "ENCRYPT",
  "reason": "개인정보보호법 준수 조치",
  "requested_by": "privacy.officer"
}

Response 200:
{
  "detection_id": "SI-2026-1021",
  "action": "MASK",
  "status": "PROCESSING",
  "requested_by": "privacy.officer",
  "requested_at": "2026-05-15T14:40:00Z",
  "estimated_completion": "2026-05-15T15:00:00Z"
}
```

---

## 4. n8n Agent 요구사항

### 4.1 AG-001: 시스템 프롬프트

```
당신은 사내 보안 통합 AI 어시스턴트입니다.

[역할]
SolidStep, MetiEye, Prisma CSPM, CCE, Server-i 5가지 보안 솔루션의 현황을 
통합적으로 조회하고 분석하여 보안 담당자를 지원합니다.

[사용 가능한 도구]
- solidstep_api: SolidStep CCE 취약점 진단 결과 조회/상태 변경
- metieye_api: MetiEye 웹쉘/악성파일 탐지 이벤트 조회/처리
- prisma_api: Prisma CSPM 클라우드 보안 알림/컴플라이언스 조회
- cce_api: KISA CCE 취약점 항목 기준 및 진단 결과 조회
- serveri_api: Server-i 서버 DLP/개인정보 탐지 현황 조회

[응답 규칙]
1. 조회 요청: 즉시 도구를 호출하여 데이터를 조회하고 한국어로 요약
2. 상태 변경 요청: 변경 내용을 명확히 설명한 후 Human Approval 게이트 통과 후 실행
3. 복수 솔루션 조회: 가능한 경우 병렬로 호출하여 통합 요약 제공
4. 불확실한 사항은 "확인이 필요합니다"로 안내
5. 민감한 보안 정보 처리 시 주의 문구 포함

[제한 사항]
- 취약점 삭제, 보안 정책 비활성화는 절대 실행 불가
- 파일 삭제 작업은 반드시 Human Approval 필요
- 개인정보가 포함된 경우 마스킹하여 응답
```

### 4.2 AG-002: 대화 시나리오 및 Tool 매핑

| 사용자 요청 | 호출 Tool | 설명 |
|-----------|---------|------|
| "전체 보안 현황 요약해줘" | 5개 API 병렬 호출 (summary) | 통합 대시보드 출력 |
| "긴급 HIGH 취약점 목록 보여줘" | solidstep_api (severity=HIGH) | 즉각 조치 필요 항목 |
| "오늘 웹쉘 탐지 있었어?" | metieye_api (from=today) | 당일 탐지 이벤트 |
| "클라우드 알림 중 미해결 HIGH 알려줘" | prisma_api (status=open, severity=high) | Prisma 위험 알림 |
| "SS-2026-0001 취약점 조치 시작으로 변경해줘" | solidstep_api PATCH → **Human Approval** | 상태 변경 |
| "file-server-01 개인정보 탐지 현황" | serveri_api (server=file-server-01) | 서버별 현황 |
| "UNIX 계정관리 CCE 항목 알려줘" | cce_api (platform=UNIX, category=계정관리) | CCE 항목 조회 |
| "ME-2026-0088 웹쉘 위협 확인 처리해줘" | metieye_api PATCH → **Human Approval** | 탐지 처리 |

### 4.3 AG-003: Human Approval 적용 기준

```
Human Approval 필수 작업:
  ✅ 취약점 상태 변경 (OPEN → IN_PROGRESS, IN_PROGRESS → RESOLVED)
  ✅ 웹쉘 탐지 이벤트 처리 (CONFIRM_THREAT, DELETE_FILE)
  ✅ Prisma CSPM 알림 해제 (Dismiss)
  ✅ 개인정보 파일 처리 (MASK, DELETE, ENCRYPT)

Human Approval 불필요 (조회만):
  ❌ 취약점 목록/통계 조회
  ❌ 탐지 이벤트 목록 조회
  ❌ 컴플라이언스 현황 조회
  ❌ CCE 항목 기준 조회

Human Approval 메시지 포맷:
  📋 변경 내용 확인
  ─────────────────────────
  시스템: [솔루션명]
  대상: [ID / 서버명 / 파일명]
  작업: [변경 내용]
  사유: [AI가 분석한 요청 사유]
  ─────────────────────────
  ⚠️ 승인 시 즉시 실행됩니다.
```

---

## 5. Mock 서버 요구사항

### 5.1 MS-001: 공통 요구사항

| 항목 | 요구사항 |
|------|---------|
| 프레임워크 | Python FastAPI |
| 데이터 저장소 | In-memory (dict/list) — 재시작 시 초기화 |
| 시드 데이터 | 현실적인 보안 데이터 20~50건 사전 로딩 |
| 응답 시간 | 200ms 이내 (시뮬레이션을 위해 50~150ms 랜덤 지연) |
| 에러 시뮬레이션 | 404, 401, 403, 500 에러 응답 포함 |
| CORS | n8n 로컬(localhost:5678)에서 접근 허용 |
| 로그 | 모든 API 호출을 콘솔 로그로 출력 |

### 5.2 MS-002: 인증 요구사항

| 솔루션 | 인증 방식 | Mock 구현 |
|--------|---------|---------|
| SolidStep | API Key (X-API-Key 헤더) | 유효 키: `ss-test-key-001` |
| MetiEye | API Key (X-API-Key 헤더) | 유효 키: `me-test-key-001` |
| Prisma CSPM | JWT (POST /login → Bearer Token) | Access Key: `prisma-access-id` / `prisma-secret` |
| CCE | API Key (X-API-Key 헤더) | 유효 키: `cce-test-key-001` |
| Server-i | API Key (X-API-Key 헤더) | 유효 키: `si-test-key-001` |

### 5.3 MS-003: 시드 데이터 요구사항

#### SolidStep 시드 데이터 (최소 30건)

| 구분 | 수량 | 내용 |
|------|------|------|
| HIGH + OPEN | 5건 | SSH 설정, 패스워드 정책, 불필요 계정 등 |
| HIGH + IN_PROGRESS | 3건 | 조치 진행 중 항목 |
| HIGH + RESOLVED | 4건 | 완료 항목 |
| MEDIUM + OPEN | 10건 | 서비스 설정, 로그 관리 등 |
| LOW + OPEN | 8건 | 권고 사항 수준 항목 |

#### MetiEye 시드 데이터 (최소 20건)

| 구분 | 수량 | 내용 |
|------|------|------|
| WEBSHELL + QUARANTINED | 8건 | PHP/JSP 웹쉘 탐지 |
| MALWARE + BLOCKED | 5건 | 악성코드 차단 이벤트 |
| DBSHELL + DETECTED | 3건 | DB 쉘 미처리 건 |
| DEFACEMENT + QUARANTINED | 2건 | 웹 변조 탐지 |
| WEBSHELL + CONFIRMED_SAFE | 2건 | 오탐 확인 완료 |

#### Prisma CSPM 시드 데이터 (최소 25건)

| 구분 | 수량 | 내용 |
|------|------|------|
| HIGH + open (AWS) | 8건 | S3 공개 접근, IAM 권한 과다 등 |
| HIGH + open (Azure) | 4건 | 스토리지 암호화 미적용 등 |
| MEDIUM + open | 10건 | 보안 그룹 설정 등 |
| dismissed | 3건 | 예외 승인 완료 건 |

#### CCE 시드 데이터

- UNIX 항목: 72건 (KISA 가이드 기준)
- WINDOWS 항목: 68건
- 진단 결과 (db-server-01 기준): 취약 8건, 양호 60건, 해당없음 4건

#### Server-i 시드 데이터 (최소 30건)

| 구분 | 수량 | 내용 |
|------|------|------|
| PII + DETECTED | 12건 | 주민번호, 카드번호 등 미처리 |
| PII + MASKED | 10건 | 마스킹 완료 건 |
| MALWARE + BLOCKED | 3건 | 랜섬웨어 자동 차단 |
| 서버 보안 현황 | 5개 서버 | 각 서버별 위험 수준 |

### 5.4 MS-004: 디렉터리 구조

```
ixi-enterprise/mock-servers/
├── README.md                  # 실행 방법 및 API 목록
├── requirements.txt           # FastAPI, uvicorn, faker 등
├── common/
│   ├── __init__.py
│   ├── auth.py                # API Key / JWT 인증 공통 처리
│   └── models.py              # 공통 Pydantic 모델
├── solidstep/
│   ├── __init__.py
│   ├── main.py                # FastAPI 앱 (port 8001)
│   ├── routes.py              # API 라우터
│   └── seed_data.py           # 시드 데이터
├── metieye/
│   ├── main.py                # (port 8002)
│   ├── routes.py
│   └── seed_data.py
├── prisma_cspm/
│   ├── main.py                # (port 8003)
│   ├── routes.py
│   └── seed_data.py
├── cce/
│   ├── main.py                # (port 8004)
│   ├── routes.py
│   └── seed_data.py
└── server_i/
    ├── main.py                # (port 8005)
    ├── routes.py
    └── seed_data.py
```

---

## 6. 비기능 요구사항

### 6.1 NFR-001: 보안

| 요구사항 | 설명 |
|---------|------|
| API Key 노출 방지 | n8n Credentials 기능 사용 (환경변수 저장) |
| JWT 갱신 | Prisma CSPM JWT 10분 만료 → n8n에서 자동 갱신 로직 구현 |
| 민감 정보 마스킹 | 서버 IP, 파일 경로 등은 로그에서 마스킹 처리 |
| HTTPS | Mock 서버는 로컬이므로 HTTP 허용, 실제 환경 전환 시 HTTPS 필수 |

### 6.2 NFR-002: 확장성

| 요구사항 | 설명 |
|---------|------|
| 솔루션 추가 용이성 | 새 Mock 서버 추가 시 기존 코드 수정 최소화 |
| 실제 서버 전환 | n8n의 Base URL Credential만 변경하면 Mock → 실제 서버 전환 가능 |

### 6.3 NFR-003: 테스트

| 요구사항 | 설명 |
|---------|------|
| Swagger UI | 각 Mock 서버에 `/docs` 경로로 Swagger UI 제공 |
| Health Check | `GET /health` 엔드포인트로 서버 상태 확인 |
| 에러 시뮬레이션 | `?simulate_error=500` 파라미터로 에러 응답 강제 발생 가능 |

---

## 7. 구현 로드맵

### 7.1 Phase 1 — Mock 서버 기반 POC (1~2일)

```
Day 1:
  1. Mock 서버 디렉터리 구조 생성
  2. SolidStep Mock 서버 구현 (조회 API + 시드 데이터)
  3. MetiEye Mock 서버 구현 (조회 API + 시드 데이터)
  4. n8n에서 두 솔루션 연동 Agent 동작 확인

Day 2:
  5. Prisma CSPM Mock (JWT 인증 + 조회 API)
  6. CCE / Server-i Mock 서버 구현
  7. 5개 솔루션 통합 n8n Agent 완성
  8. 기본 대화 시나리오 동작 검증
```

### 7.2 Phase 2 — 상태 변경 + Human Approval (1~2일)

```
  1. 각 Mock 서버 PATCH API 구현
  2. n8n Human Approval 노드 연결
  3. 상태 변경 시나리오 e2e 테스트
  4. 승인 메시지 포맷 최적화
```

### 7.3 Phase 3 — 안정화 및 고도화 (선택)

```
  1. Guardrail 추가 (PLL + Moderation)
  2. 보안 리포트 자동 생성 플로우 연결 (4-2 멀티스텝 승인)
  3. Prisma CSPM JWT 자동 갱신 처리
  4. 실제 보안 솔루션으로 Base URL 전환 테스트
```

> ⚠️ **ixi-enterprise에서 Guardrail 추가 시 연결 순서 주의** (Phase 3 해당)  
> PLL Guardrail / Moderation Guardrail의 Input 포트는 Agent / Language Model / PLL Guardrail / Moderation Guardrail만 허용.  
> Chat Input → Guardrail 직접 연결 불가 — `Chat Input → Agent → PLL Guardrail` 순서로 배치.  
> PLL Guardrail 사용 시 Azure Language Service API Key 등록 필수 (`04-open-questions.md` 항목 13 참조).  
> API Key 미등록 시 `401 Access denied` 오류 발생.

---

## 8. 미결 사항 (Backlog)

| # | 항목 | 우선순위 | 담당 |
|---|------|---------|------|
| 1 | n8n Tool 정의 방식 — HTTP Request vs Code Node 선택 | 🔴 높음 | 개발 시 결정 |
| 2 | Prisma CSPM JWT 갱신 주기 처리 방법 (10분 만료) | 🔴 높음 | Phase 2 |
| 3 | 5개 솔루션 병렬 호출 시 n8n Agent 응답 지연 허용 범위 | 🟡 중간 | Phase 1 검증 |
| 4 | Mock 서버 상태 초기화 API (`POST /reset`) 필요 여부 | 🟡 중간 | Phase 1 |
| 5 | 실제 솔루션 전환 시 인증 정보 관리 방안 (Vault 등) | 🟢 낮음 | Phase 3 이후 |

---

## 참고 자료

- [SolidStep 공식](http://www.ssrinc.co.kr/solidstep.html) — 에스에스알 SolidStep CCE 취약점 진단
- [MetiEye 공식](https://www.ssrinc.co.kr/solution/metieye) — 에스에스알 MetiEye 웹쉘 탐지
- [Prisma Cloud API 문서](https://pan.dev/prisma-cloud/api/cspm/) — Palo Alto Networks 공식 API
- [Server-i 소만사](https://www.somansa.com/solution/possesion-control/server-i/) — 소만사 Server-i DLP
- [KISA CCE 가이드](https://krcert.or.kr/kr/bbs/view.do?searchCnd=1&bbsId=B0000127&searchWrd=%EC%B7%A8%EC%95%BD%EC%A0%90&menuNo=205021&pageIndex=1&categoryCode=&nttId=35988) — 주요정보통신기반시설 기술적 취약점 분석·평가
