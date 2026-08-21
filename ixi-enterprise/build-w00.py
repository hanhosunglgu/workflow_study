#!/usr/bin/env python3
"""
W0-0 (참조값 후보 조회) 워크플로우 JSON 생성기
작성일: 2026-08-21

목적:
  W0-1이 확정하는 3개 참조값(orgId/templateNo/asstType)의 **선택지 전체**를 사람이 눈으로
  확인하기 위한 조회 전용 플로우. W0-1은 값을 1개로 좁히지만, 그 선택이 옳은지 판단하려면
  후보 목록을 봐야 한다.

W0-1과 분리한 이유:
  W0-1에 목록 출력을 얹으면 26개 템플릿 전문이 컨텍스트에 들어오고 출력으로도 나온다.
  W0-1의 존재 이유가 체인을 짧게 유지하는 것이므로 목적이 다른 조회는 분리한다.
  이 플로우는 사람이 값을 정할 때 1회 실행하고, 이후에는 쓰지 않는다.

배경 (2026-08-21 실측):
  templateNo=151은 "배열 첫 번째 항목"으로 선택된 값이었다. 개발기 기준 후보가 26개이며
  _bak, _복제본_1, _원본, w16테스트 같은 항목이 섞여 있다. API 반환 순서가 바뀌면 엉뚱한
  템플릿이 선택되고 알아채기 어렵다. 반면 asstType은 8개 항목이 전부 SSRCCE라 선택의
  여지가 없고, orgId는 조직명 정확 일치로 확정되므로 순서 의존이 없다.

사용법:
  python3 build-w00.py            # 운영기 URL로 생성
  python3 build-w00.py --verify   # 생성하지 않고 구조 검증만 수행
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "stage1-orgid-test.json"
OUT = HERE / "w00-reference-list.json"

DEV_BASE = "http://165.244.21.49:8080"
PROD_BASE = "https://ivms.lguplus.co.kr"

READ_TIMEOUT = 30000
CONNECT_TIMEOUT = 5000

# ─────────────────────────────────────────────────────────────
# System Prompt
#
# 중괄호 {} 금지(12번 문서 8.4절): {orgId} 형태는 템플릿 변수로 해석되어 실행 거부됨.
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """너는 IVMS 참조값의 선택지를 사람에게 보여주는 조회 전담 에이전트다.

이 플로우의 목적은 값을 하나로 고르는 것이 아니라, **고를 수 있는 후보를 빠짐없이
나열하는 것**이다. 사람이 그 목록을 보고 직접 값을 정한다.
따라서 임의로 후보를 추리거나 대표값 하나만 고르지 않는다. 받은 것을 전부 보여준다.

사용자 입력에 따라 아래 3가지 중 해당하는 것만 수행한다.
어느 것을 원하는지 불분명하면 3가지를 모두 수행한다.

[조회 1] 진단템플릿 목록 — 사용자가 템플릿, templateNo, 진단항목을 언급한 경우
- assetSsrcceTemplate을 호출한다. userId는 admin이다.
- 응답 templateList 배열의 **모든 항목**을 번호를 붙여 나열한다.
  각 줄에 atemplateNo와 templateName을 함께 적는다.
- 개수를 맨 위에 적는다.
- 정렬하거나 재배치하지 말고 응답에 담긴 순서 그대로 출력한다.
  순서 자체가 확인 대상이기 때문이다.
- 목록 끝에 다음 안내를 덧붙인다:
  "이름에 (구), _bak, _복제본, _원본, 테스트가 붙은 항목은 운영 대상이 아닐 수 있으니
   확인이 필요합니다."

[조회 2] 자산분류 목록 — 사용자가 자산분류, asstType, 카테고리를 언급한 경우
- assetCategory를 호출한다. userId는 admin, asstCtgrLevel은 L이다.
- 응답 asstCtgrList 배열의 **모든 항목**을 번호를 붙여 나열한다.
  각 줄에 asstCtgrId와 asstCtgrNm과 asstType을 함께 적는다.
- asstType이 빈 항목은 빈 값이라고 그대로 표기한다. 건너뛰지 않는다.
- 나열 후, 등장한 asstType의 **고유 종류**를 따로 적는다.
  종류가 1개뿐이면 "asstType은 전 항목 동일하므로 선택의 여지가 없음"이라고 명시한다.

[조회 3] 조직 목록 — 사용자가 조직, 팀, Lab, orgId를 언급한 경우
- orgList를 호출한다. 사용자가 특정 상위 조직을 지정하지 않았으면
  pOrgId는 org_002205, orgType은 3으로 호출한다.
- 응답 orgList 배열에서 **pOrgId가 비어 있지 않은 항목만** 나열한다.
  배열 첫 항목은 조회 대상 자신이라 하위 조직이 아니기 때문이다.
- 각 줄에 orgId와 orgNm을 적는다.
- 사용자가 특정 조직의 하위를 보고 싶다고 하면, 그 조직의 orgId를 pOrgId로 삼고
  orgType은 4로 호출한다. 팀 단위가 반환된다.
- 🔴 orgList 호출은 전체를 통틀어 최대 3회를 넘기지 않는다. 더 깊이 파고들지 않는다.

[출력 형식]
조회한 항목마다 아래처럼 제목을 달고 나열한다. 표 대신 번호 목록을 쓴다.

=== 진단템플릿 (총 N건) ===
1. atemplateNo=151  LG유플러스_기준항목(신규)
2. atemplateNo=180  주요정보통신기반시설_기준항목(26개정)
...

값을 지어내지 않는다. 응답에 없는 항목을 추가하지 않고, 있는 항목을 빠뜨리지 않는다.
응답이 비어 있으면 "응답에 항목이 없음"이라고 적고 호출한 파라미터를 함께 밝힌다.

[중요] 이 플로우는 값을 확정하지 않는다. 어떤 값을 써야 한다고 권하지도 않는다.
목록만 제시하고, 선택은 사람에게 맡긴다. 자산 목록이나 취약점 조회는 이 플로우의
범위가 아니므로 수행하지 않는다."""

TOOL_DESCRIPTIONS = {
    "assetSsrcceTemplate": (
        "진단템플릿 목록 전체를 조회하는 도구. userId만 입력받는다. 응답의 templateList "
        "배열에 atemplateNo(진단템플릿 번호)와 templateName(진단템플릿명)이 담겨 있다. "
        "후보를 사람에게 보여주기 위한 조회이므로 전체를 그대로 받는다."
    ),
    "assetCategory": (
        "자산분류 목록 전체를 조회하는 도구. userId와 asstCtgrLevel을 입력받는다. "
        "응답의 asstCtgrList 배열에 asstCtgrId(자산분류ID), asstCtgrNm(자산분류명), "
        "asstType(자산타입)이 담겨 있다. asstType은 비어 있는 항목이 있을 수 있다."
    ),
    "orgList": (
        "조직 목록을 조회하는 도구. pOrgId(상위 조직 ID)와 orgType(1=부문, 2=그룹, "
        "3=담당, 4=팀)을 입력받아 그 하위 조직 목록을 반환한다. 응답의 orgList 배열에 "
        "orgId와 orgNm이 담겨 있다. 배열 첫 항목은 pOrgId가 빈 값인 조회 대상 자신이므로 "
        "하위 조직이 아니다. pOrgId가 org_002205이고 orgType이 3이면 Lab 단위가, "
        "Lab의 orgId로 orgType 4를 호출하면 팀 단위가 반환된다."
    ),
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


def build(target_base: str, other_base: str):
    if not SRC.exists():
        sys.exit(f"[ERROR] 원본을 찾을 수 없음: {SRC}")

    wf = json.loads(SRC.read_text(encoding="utf-8"))

    wf["name"] = "graph_w00_reference_list"
    wf["display_name"] = "ivms W0-0 - 참조값 후보 조회"
    wf["role"] = "사내보안 ivms 연결 테스트"
    wf["description"] = (
        "계층 0 사전조회: assetSsrcceTemplate/assetCategory/orgList의 "
        "후보 목록 전체를 나열한다. 값을 확정하지 않으며, 사람이 W0-1에 쓸 값을 "
        "고르기 위한 참고용. 값 확정은 W0-1이 수행"
    )

    changes = []

    for n in wf["nodes"]:
        m = n["metadata"]
        name = m.get("name")

        if name == "Agent":
            set_field(n, "system_prompt_template", SYSTEM_PROMPT)
            changes.append("Agent: System Prompt 교체 (조회 전용, 전체 나열)")

        elif name == "APIRequest":
            url = get_field(n, "url") or ""
            ep = url.rstrip("/").split("/")[-1]

            new_url = url.replace(other_base, target_base)
            if new_url != url:
                set_field(n, "url", new_url)
                label = "운영기" if target_base == PROD_BASE else "개발기"
                changes.append(f"{ep}: URL → {label}")

            set_field(n, "read_timeout", READ_TIMEOUT)
            set_field(n, "connect_timeout", CONNECT_TIMEOUT)

            if ep in TOOL_DESCRIPTIONS:
                set_field(n, "tool_description", TOOL_DESCRIPTIONS[ep])
                changes.append(f"{ep}: tool_description 갱신")

    return wf, changes


def verify(wf: dict, target_base: str, other_base: str) -> list:
    problems = []
    nodes = {n["id"]: n for n in wf["nodes"]}
    by_name = {}
    for n in wf["nodes"]:
        by_name.setdefault(n["metadata"]["name"], []).append(n)

    expect = {"Agent": 1, "ChatInput": 1, "ChatOutput": 1, "APIRequest": 3}
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
        tool_edges = [
            e for e in wf["edges"]
            if e["target"] == aid and e.get("target_field_name") == "tools"
        ]
        if len(tool_edges) != 3:
            problems.append(f"Agent tools 연결 {len(tool_edges)}개 (기대 3개)")

        import re
        sp = get_field(agent, "system_prompt_template") or ""
        bad = re.findall(r"\{[A-Za-z_][A-Za-z0-9_]*\}", sp)
        if bad:
            problems.append(f"System Prompt에 템플릿 변수로 해석될 중괄호: {set(bad)}")

    for n in by_name.get("APIRequest", []):
        url = get_field(n, "url") or ""
        ep = url.rstrip("/").split("/")[-1]
        if other_base in url:
            problems.append(f"{ep}: 대상 아닌 환경 URL이 남아있음 ({other_base})")
        if not url.startswith(target_base):
            problems.append(f"{ep}: URL이 대상 환경이 아님 — {url}")
        if not get_field(n, "tool_description"):
            problems.append(f"{ep}: tool_description 비어있음")
        if n["metadata"].get("tool_mode") is not True:
            problems.append(f"{ep}: tool_mode가 ON이 아님")
        rt = get_field(n, "read_timeout")
        if not isinstance(rt, int) or rt < 30000:
            problems.append(f"{ep}: read_timeout {rt} (30000 이상 권장)")
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
    target_base = PROD_BASE
    other_base = DEV_BASE
    env_label = "운영기"
    out = OUT

    wf, changes = build(target_base, other_base)

    print("=" * 62)
    print(f" W0-0 참조값 후보 조회 플로우 생성 — {env_label}")
    print("=" * 62)
    print(f" 원본: {SRC.name}")
    print(f" 대상: {target_base}")
    print(f" 출력: {out.name}")
    print()
    print("── 변경 내역 ──")
    for c in changes:
        print(f"  · {c}")
    print()

    print("── 구조 검증 ──")
    problems = verify(wf, target_base, other_base)
    if problems:
        for p in problems:
            print(f"  ❌ {p}")
        print()
        sys.exit("[FAIL] 검증 실패 — 파일을 쓰지 않고 종료합니다.")
    print("  ✅ 노드 구성 (Agent 1 / ChatInput 1 / ChatOutput 1 / APIRequest 3)")
    print("  ✅ 엣지 참조 무결성")
    print("  ✅ Tool 3개 → Agent tools 연결")
    print("  ✅ System Prompt 중괄호 없음")
    print(f"  ✅ {env_label} URL / tool_mode ON / read_timeout 30000 / 인증 헤더 4종")
    print()

    if "--verify" in sys.argv:
        print("[--verify] 검증만 수행하고 종료합니다.")
        return

    out.write_text(
        json.dumps(wf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"✅ 생성 완료: {out}")
    print()
    print("── 캔버스 등록 정보 ──")
    print(f"  이름 : {wf['display_name']}")
    print(f"  역할 : {wf['role']}")
    print(f"  설명 : {wf['description']}")
    print()
    print("── Chat Input 입력 예시 ──")
    print("  · 진단템플릿 목록 전부 보여줘")
    print("  · 자산분류 목록 보여줘")
    print("  · Enterprise서비스개발Lab 하위 팀 목록 보여줘")
    print("  · 참조값 후보 전부 보여줘          ← 3가지 모두 조회")


if __name__ == "__main__":
    main()
