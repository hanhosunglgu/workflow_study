#!/usr/bin/env python3
"""
W0-M (운영기 규모 측정) 워크플로우 JSON 생성기
작성일: 2026-08-21

목적:
  운영기 조직별 실자산 규모를 측정한다. orgscale-debug.sh와 같은 측정을
  캔버스에서 수행하는 버전이다.

왜 캔버스로 하는가:
  운영기는 방화벽으로 터미널에서 도달 불가하나, 캔버스 서버는 도달한다
  (W0-1 운영기 실행 성공으로 확인, 2026-08-21). 따라서 curl 대신 캔버스를
  측정 도구로 쓴다. 방화벽을 우회하는 것이 아니라 이미 열린 경로를 쓰는 것이다.

🔴 측정의 핵심 — 가짜 조직 ID 대조:
  개발기에서 org_000991이 9,794건을 반환했으나 실자산은 약 112건이었다.
  나머지 9,682건은 mgmtOrgId가 미기입된 자산이 조건과 무관하게 딸려온 것이다
  (12번 문서 4-2.1절). 존재하지 않는 조직 ID로도 같은 건수가 나온다.

  따라서 반드시 가짜 ID를 함께 호출해 기준선을 잡아야 한다.
      실자산 ≈ (조직 조회 건수) − (가짜 ID 건수)

  대조군 없이 "조직마다 건수가 다르다"만 보면 필터가 동작한다고 오판한다.
  이것이 4-1.2절 판정이 4-2절에서 뒤집힌 원인이다.

구성:
  Chat Input → Agent(Tool: mngtListDetail) → Chat Output   (4노드)
  Tool 1개, Agent 1개. 호출 상한 4회로 제한해 컨텍스트 초과를 막는다.

⚠️ 응답 크기 주의:
  pageSize=200이면 1페이지가 약 121,085 tok(예산의 13%)다. 본 측정은
  listCount만 필요하므로 pageSize=1로 고정해 응답을 최소화한다.

사용법:
  python3 build-w0m.py            # 운영기 URL로 생성
  python3 build-w0m.py --verify   # 생성하지 않고 구조 검증만 수행
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "stage2-mngtlist-test.json"   # body 필드를 가진 APIRequest 원본
OUT = HERE / "w0m-scale-measure.json"

DEV_BASE = "http://165.244.21.49:8080"
PROD_BASE = "https://ivms.lguplus.co.kr"

READ_TIMEOUT = 30000      # POST 계열 필수 (12번 문서 8.4절)
CONNECT_TIMEOUT = 5000

TARGET_EP = "mngtListDetail"

# ─────────────────────────────────────────────────────────────
# System Prompt
#
# 중괄호 {} 금지(12번 문서 8.4절): {orgId} 형태는 템플릿 변수로 해석되어 실행 거부됨.
# JSON 예시는 무방하나, 혼동을 피해 본 프롬프트에서는 쓰지 않는다.
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """너는 IVMS 조직별 자산 규모를 재는 측정 전담 에이전트다.

측정 목적은 조직 하나를 캔버스 워크플로우로 처리할 수 있는지 판단할 숫자를 얻는
것이다. 자산 내용은 필요 없고 건수만 필요하다.

[가장 중요한 규칙 — 가짜 조직 ID 대조]
IVMS는 조직 ID가 미기입된 자산을 조회 조건과 무관하게 함께 반환한다. 그래서
조직을 지정해 조회해도 그 건수 대부분이 해당 조직과 무관할 수 있다.
이를 걸러내려면 존재하지 않는 조직 ID로도 한 번 호출해 기준선을 잡아야 한다.

실자산은 다음과 같이 계산한다.
  실자산 = 조직 조회 건수 - 가짜 조직 ID 건수

이 대조를 생략하면 측정 결과가 무의미하다. 반드시 수행한다.

[호출 규칙]
- mngtListDetail을 호출한다. Method는 POST다.
- 모든 호출에서 pageSize는 반드시 1로 한다. 응답의 listCount만 쓰기 때문이며,
  값을 키우면 자산 원문이 통째로 들어와 예산을 넘긴다.
- 공통 파라미터는 아래 값을 그대로 쓴다.
    userId 는 admin
    asstType 은 SSRCCE
    templateNo 는 151
    diagYear 는 2026
    page 는 1
    pageSize 는 1
- filter 파라미터는 사용하지 않는다. 서버가 무시함이 확인됐다.
- 🔴 호출은 전체를 통틀어 최대 4회를 넘기지 않는다. 4회를 채우면 즉시 중단하고
  그때까지 얻은 결과만 보고한다. 더 재려 하지 않는다.

[측정 순서]
1회차: mgmtOrgId 에 존재하지 않는 값 org_ZZZZZZZ 를 넣어 호출한다.
       이 건수가 기준선이다. 이 값을 반드시 먼저 확보한다.

2회차: 사용자가 지정한 조직 ID로 호출한다.
       조직을 지정하지 않았으면 org_000991 로 한다.

3~4회차: 사용자가 조직을 여러 개 지정한 경우에만 추가 호출한다.
        지정하지 않았으면 2회차에서 끝낸다.

[출력 형식]
아래 형식으로만 출력한다. 다른 설명은 덧붙이지 않는다.

기준선(가짜 ID org_ZZZZZZZ): 건수
---
조직ID: 실제 값
반환건수: 실제 값
실자산: 반환건수 빼기 기준선
페이지수: 실자산을 200으로 나눠 올림한 값
판정: 아래 기준에 따라 한 줄

판정 기준
- 실자산이 600건 이하이면 "계층1 1회 실행으로 완주 가능"
- 실자산이 601에서 1400건이면 "계층1 2에서 3회 실행 필요"
- 실자산이 1401건 이상이면 "조직 단위로도 초과. 추가 분해 필요"
- 기준선이 100건 미만이면 "운영기에는 조직 미기입 자산이 거의 없음"을 함께 적는다

숫자는 응답의 listCount 값을 그대로 쓴다. 추정하거나 지어내지 않는다.
호출이 실패하면 실패한 파라미터를 그대로 적는다.

[중요] 이 플로우는 자산 목록이나 취약점을 조회하지 않는다. 건수만 센다.
안내문 생성도 하지 않는다."""

TOOL_DESCRIPTION = (
    "조직별 자산 건수를 조회하는 도구. Method는 POST이며 Body로 조건을 전달한다. "
    "응답의 result.listCount가 조건에 해당하는 자산 총 건수다. "
    "본 측정에서는 listCount만 사용하므로 pageSize를 1로 고정해 응답을 최소화한다. "
    "주의: 조직 ID가 미기입된 자산은 mgmtOrgId 조건과 무관하게 함께 반환되므로, "
    "존재하지 않는 조직 ID로 호출한 결과를 기준선으로 삼아 차감해야 실자산이 나온다."
)

# Body 스키마 — 측정에 필요한 필드만. filter/asstLCtgrId는 제외.
BODY_SCHEMA = {
    "title": "mngtListDetail",
    "type": "object",
    "properties": {
        "userId": {
            "type": "string",
            "description": '요청 사용자 ID. "admin"을 사용한다.',
        },
        "mgmtOrgId": {
            "type": "string",
            "description": (
                "조직 ID. 측정 대상 조직의 ID를 넣는다. 기준선 측정 시에는 "
                "존재하지 않는 값 org_ZZZZZZZ 를 넣는다."
            ),
        },
        "asstType": {
            "type": "string",
            "description": '자산타입. "SSRCCE"를 사용한다.',
        },
        "templateNo": {
            "type": "string",
            "description": '진단템플릿 번호. "151"을 사용한다.',
        },
        "diagYear": {
            "type": "string",
            "description": '기준연도. "2026"을 사용한다.',
        },
        "page": {
            "type": "integer",
            "description": "현재 페이지. 항상 1을 사용한다.",
        },
        "pageSize": {
            "type": "integer",
            "description": (
                "페이지당 항목 수. 반드시 1을 사용한다. listCount만 필요하므로 "
                "값을 키우면 자산 원문이 통째로 들어와 컨텍스트 예산을 넘긴다."
            ),
        },
    },
    "required": ["userId", "mgmtOrgId", "asstType", "templateNo"],
    "additionalProperties": True,
    "strict": False,
}


def set_field(node: dict, field_name: str, value) -> bool:
    for f in node["metadata"].get("fields", []):
        if f.get("name") == field_name:
            f["value"] = value
            return True
    return False


def get_field(node: dict, field_name: str):
    for f in node["metadata"].get("fields", []):
        if f.get("name") == field_name:
            return f.get("value")
    return None


def build():
    if not SRC.exists():
        sys.exit(f"[ERROR] 원본을 찾을 수 없음: {SRC}")

    src = json.loads(SRC.read_text(encoding="utf-8"))
    changes = []

    # ── 남길 노드 선별: Agent 1 + ChatInput + ChatOutput + mngtListDetail Tool ──
    by_name = {}
    for n in src["nodes"]:
        by_name.setdefault(n["metadata"]["name"], []).append(n)

    chat_in = by_name["ChatInput"][0]
    chat_out = by_name["ChatOutput"][0]

    api_node = None
    for n in by_name.get("APIRequest", []):
        if TARGET_EP in (get_field(n, "url") or ""):
            api_node = n
            break
    if api_node is None:
        sys.exit(f"[ERROR] {TARGET_EP} APIRequest 노드를 찾을 수 없음")

    # Agent는 Tool 포트에 대상 API가 연결된 것을 고른다
    agent = None
    for a in by_name.get("Agent", []):
        linked = [
            e for e in src["edges"]
            if e["source"] == api_node["id"] and e["target"] == a["id"]
        ]
        if linked:
            agent = a
            break
    if agent is None:
        agent = by_name["Agent"][0]

    keep = {agent["id"], chat_in["id"], chat_out["id"], api_node["id"]}
    nodes = [n for n in src["nodes"] if n["id"] in keep]
    changes.append(f"노드 {len(src['nodes'])}개 → {len(nodes)}개로 축소")

    # ── 엣지 재구성: ChatInput→Agent, API→Agent(tools), Agent→ChatOutput ──
    edges = [
        {
            "source": chat_in["id"],
            "source_output_name": "message",
            "target": agent["id"],
            "target_field_name": "input",
        },
        {
            "source": api_node["id"],
            "source_output_name": "tool",
            "target": agent["id"],
            "target_field_name": "tools",
        },
        {
            "source": agent["id"],
            "source_output_name": "response",
            "target": chat_out["id"],
            "target_field_name": "input",
        },
    ]
    # 원본 엣지에서 실제 output_name을 가져와 정확도 보정
    for e in src["edges"]:
        for ne in edges:
            if e["source"] == ne["source"] and e["target"] == ne["target"]:
                ne["source_output_name"] = e.get(
                    "source_output_name", ne["source_output_name"]
                )
                ne["target_field_name"] = e.get(
                    "target_field_name", ne["target_field_name"]
                )
    changes.append(f"엣지 {len(src['edges'])}개 → {len(edges)}개로 재구성")

    # ── 노드 설정 ──
    set_field(agent, "system_prompt_template", SYSTEM_PROMPT)
    changes.append("Agent: System Prompt 교체 (가짜 ID 대조, 호출 상한 4회)")

    url = get_field(api_node, "url") or ""
    new_url = url.replace(DEV_BASE, PROD_BASE)
    if new_url != url:
        set_field(api_node, "url", new_url)
    changes.append(f"{TARGET_EP}: URL → 운영기")

    set_field(api_node, "tool_description", TOOL_DESCRIPTION)
    set_field(api_node, "read_timeout", READ_TIMEOUT)
    set_field(api_node, "connect_timeout", CONNECT_TIMEOUT)
    set_field(api_node, "body", json.dumps(BODY_SCHEMA, ensure_ascii=False, indent=2))
    set_field(api_node, "query_params", [])
    changes.append(f"{TARGET_EP}: body 스키마 교체 (pageSize=1 고정, filter 제거)")
    changes.append(f"{TARGET_EP}: query_params 비움 (POST 계열 필수, 8.4절)")

    wf = dict(src)
    wf["nodes"] = nodes
    wf["edges"] = edges
    wf["name"] = "graph_w0m_scale_measure"
    wf["display_name"] = "ivms W0-M - 운영기 규모 측정"
    wf["role"] = "사내보안 ivms 연결 테스트"
    wf["description"] = (
        "운영기 조직별 실자산 규모 측정: mngtListDetail을 pageSize=1로 호출해 "
        "listCount만 수집한다. 가짜 조직 ID를 기준선으로 대조해 조직 미기입 자산을 "
        "차감한다. 터미널에서 운영기 접근이 막혀 캔버스를 측정 도구로 사용"
    )
    wf["validation_status"] = "VALID"
    wf["validation_errors"] = []

    return wf, changes


def verify(wf: dict) -> list:
    problems = []
    nodes = {n["id"]: n for n in wf["nodes"]}
    by_name = {}
    for n in wf["nodes"]:
        by_name.setdefault(n["metadata"]["name"], []).append(n)

    expect = {"Agent": 1, "ChatInput": 1, "ChatOutput": 1, "APIRequest": 1}
    for k, cnt in expect.items():
        got = len(by_name.get(k, []))
        if got != cnt:
            problems.append(f"노드 구성 불일치: {k} 기대 {cnt}개, 실제 {got}개")

    for e in wf["edges"]:
        if e["source"] not in nodes:
            problems.append(f"엣지 source 미존재: {e['source'][:8]}")
        if e["target"] not in nodes:
            problems.append(f"엣지 target 미존재: {e['target'][:8]}")

    agent = by_name.get("Agent", [None])[0]
    if agent:
        aid = agent["id"]
        for field, cnt in (("tools", 1), ("input", 1)):
            got = len([
                e for e in wf["edges"]
                if e["target"] == aid and e.get("target_field_name") == field
            ])
            if got != cnt:
                problems.append(f"Agent {field} 연결 {got}개 (기대 {cnt}개)")

        out_edges = [e for e in wf["edges"] if e["source"] == aid]
        if len(out_edges) != 1:
            problems.append(f"Agent 출력 엣지 {len(out_edges)}개 (기대 1개)")

        sp = get_field(agent, "system_prompt_template") or ""
        bad = re.findall(r"\{[A-Za-z_][A-Za-z0-9_]*\}", sp)
        if bad:
            problems.append(f"System Prompt에 템플릿 변수 중괄호: {set(bad)}")
        if "org_ZZZZZZZ" not in sp:
            problems.append("System Prompt에 가짜 ID 대조 지시가 없음")

    for n in by_name.get("APIRequest", []):
        url = get_field(n, "url") or ""
        ep = url.rstrip("/").split("/")[-1]
        if DEV_BASE in url:
            problems.append(f"{ep}: 개발기 URL이 남아있음")
        if not url.startswith(PROD_BASE):
            problems.append(f"{ep}: 운영기 URL이 아님 — {url}")
        if get_field(n, "method") != "POST":
            problems.append(f"{ep}: Method가 POST가 아님")
        if n["metadata"].get("tool_mode") is not True:
            problems.append(f"{ep}: tool_mode가 ON이 아님")
        rt = get_field(n, "read_timeout")
        if not isinstance(rt, int) or rt < 30000:
            problems.append(f"{ep}: read_timeout {rt} (POST는 30000 이상 필수)")
        if get_field(n, "query_params"):
            problems.append(f"{ep}: POST인데 query_params가 비어있지 않음")

        body_raw = get_field(n, "body") or ""
        try:
            body = json.loads(body_raw)
        except Exception:
            problems.append(f"{ep}: body가 유효한 JSON이 아님")
            body = {}
        props = body.get("properties", {})
        if "pageSize" not in props:
            problems.append(f"{ep}: body에 pageSize 정의 없음")
        elif "1" not in (props["pageSize"].get("description") or ""):
            problems.append(f"{ep}: pageSize 설명에 1 고정 지시가 없음")
        if "filter" in props:
            problems.append(f"{ep}: body에 filter가 남아있음 (서버가 무시, 제거 대상)")

        hdr = get_field(n, "header") or []
        keys = {h.get("key") for h in hdr if isinstance(h, dict)}
        need = {
            "X-Global-Transaction-ID", "X-APP-NAME",
            "X-AuthorizationTime", "X-Header-Authorization",
        }
        missing = need - keys
        if missing:
            problems.append(f"{ep}: 인증 헤더 키 누락 {missing}")

    return problems


def main():
    wf, changes = build()

    print("=" * 62)
    print(" W0-M 운영기 규모 측정 플로우 생성")
    print("=" * 62)
    print(f" 원본: {SRC.name}")
    print(f" 대상: {PROD_BASE}")
    print(f" 출력: {OUT.name}")
    print()
    print("── 변경 내역 ──")
    for c in changes:
        print(f"  · {c}")
    print()

    print("── 구조 검증 ──")
    problems = verify(wf)
    if problems:
        for p in problems:
            print(f"  ❌ {p}")
        print()
        sys.exit("[FAIL] 검증 실패 — 파일을 쓰지 않고 종료합니다.")
    print("  ✅ 노드 구성 (Agent 1 / ChatInput 1 / ChatOutput 1 / APIRequest 1)")
    print("  ✅ 엣지 참조 무결성 및 연결 (input 1 / tools 1 / output 1)")
    print("  ✅ System Prompt — 중괄호 없음, 가짜 ID 대조 지시 포함")
    print("  ✅ 운영기 URL / POST / tool_mode ON / read_timeout 30000")
    print("  ✅ body — pageSize 1 고정, filter 제거 / query_params 비움")
    print("  ✅ 인증 헤더 4종")
    print()

    if "--verify" in sys.argv:
        print("[--verify] 검증만 수행하고 종료합니다.")
        return

    OUT.write_text(
        json.dumps(wf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"✅ 생성 완료: {OUT}")
    print()
    print("── 캔버스 등록 정보 ──")
    print(f"  이름 : {wf['display_name']}")
    print(f"  역할 : {wf['role']}")
    print(f"  설명 : {wf['description']}")
    print()
    print("── Chat Input 입력 ──")
    print("  org_000991 규모 측정해줘                    ← 대상 조직 1개")
    print("  org_000991 org_001738 규모 측정해줘          ← 2개 (호출 3회)")
    print("  규모 측정해줘                               ← org_000991 기본값")
    print()
    print("── 개발기 대조값 (같은 측정의 개발기 결과) ──")
    print("  기준선(가짜 ID)  : 9,682건")
    print("  org_000991 반환  : 9,794건 → 실자산 112건")
    print("  운영기 기준선이 100건 미만이면 조직 미기입 자산이 거의 없다는 뜻")


if __name__ == "__main__":
    main()
