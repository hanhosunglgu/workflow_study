#!/usr/bin/env python3
"""
W0-1 (계층 0 — 조직 조회 플로우) 워크플로우 JSON 생성기
작성일: 2026-08-21

목적:
  stage1-orgid-test.json을 기반으로, 12-flow-a-restructure-plan.md 6.2절이 규정한
  계층 0 워크플로우를 생성한다. 런타임 체인에서 분리되어 "조직 변경 시에만" 실행되며,
  산출된 orgId/templateNo/asstType은 상수로 관리해 W1/W2에 하드코딩한다.

stage1 대비 변경점:
  1. Read Timeout 3000 → 30000 (12번 문서 8.4절: POST 계열 30000ms 필수,
     GET도 응답 지연 대비 상향)
  2. System Prompt에서 조직명을 파라미터화하고, 재귀 상한을 명시적으로 제한
  3. 4차 실패 재발 방지 문구 추가 — 이 플로우는 체인의 일부가 아니라 단독 실행임을 명시

⚠️ 운영기/개발기 데이터 차이 (2026-08-21 실측):
  프롬프트 [작업 3]의 조직 트리 힌트(pOrgId=org_002205, orgType=3 → Lab 5개 등)는
  개발기 실측값이다. 운영기 트리 구조가 다르면 Agent가 2회차에서 못 찾고 4회 상한까지
  소진할 수 있다. 운영기 첫 실행 시 orgList 호출 횟수를 반드시 확인하고, 트리가 다르면
  ORG_TREE_HINT를 실제 구조로 교체할 것.

사용법:
  python3 build-w01.py            # 운영기 URL로 생성
  python3 build-w01.py --verify   # 생성하지 않고 구조 검증만 수행
"""

import json
import sys
import copy
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "stage1-orgid-test.json"
OUT = HERE / "w01-org-lookup.json"

DEV_BASE = "http://165.244.21.49:8080"
PROD_BASE = "https://ivms.lguplus.co.kr"

# 12번 문서 8.4절 — POST 계열 Read Timeout 30000ms. GET도 개발기 지연 대비 상향.
READ_TIMEOUT = 30000
CONNECT_TIMEOUT = 5000

# ─────────────────────────────────────────────────────────────
# System Prompt — 4차 실패 교훈 반영
#
# 중괄호 {} 금지(12번 문서 8.4절): {orgId} 형태는 템플릿 변수로 해석되어 실행 거부됨.
# 따라서 모든 값 참조는 서술형으로 표현한다.
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """너는 IVMS 자산 점검에 필요한 정적 참조값 3개를 확정하는 에이전트다.

이 플로우는 다른 플로우와 연결되지 않는 단독 실행 플로우다. 여기서 얻은 값은 사람이
받아적어 상수로 관리하며, 조직 구조가 바뀌지 않는 한 다시 실행하지 않는다.
따라서 이번 실행 안에서 3개 값을 모두 확정하는 것이 유일한 목표다.

⚠️ 사용자 입력이 "조직 ID만 알려줘"처럼 일부만 요청하는 것처럼 보여도 3개 작업을 전부
수행한다. 3개 값이 모두 채워지기 전에는 작업이 끝난 것이 아니다.

[작업 1] assetSsrcceTemplate 호출 — templateNo 확보
- userId는 admin으로 호출해 templateList 배열을 받는다.
- 첫 번째 항목의 atemplateNo를 templateNo로 확정한다.
- 조직 조회와 무관하므로 가장 먼저 수행한다. 호출은 1회로 끝낸다.

[작업 2] assetCategory 호출 — asstType 확보
- userId는 admin, asstCtgrLevel은 L로 호출해 asstCtgrList 배열을 받는다.
- asstType은 선택 필드라 항목에 따라 비어 있을 수 있다. 배열의 첫 번째 항목을 무조건
  쓰지 말고, 앞에서부터 훑어 asstType 값이 비어 있지 않은 첫 번째 항목의 값을 사용한다.
- 모든 항목에서 비어 있으면 asstType 자리에 "응답에 값 없음"이라고 쓰고, 확인한 배열의
  항목 수와 첫 항목의 asstCtgrNm을 함께 적는다.
- 조직 조회와 무관하므로 조직 조회 전에 수행한다. 호출은 1회로 끝낸다.

[작업 3] orgList 호출 — orgId 확보
- 사용자가 말한 조직명을 찾는다. 조직명을 말하지 않았으면 Enterprise SW프로덕트개발팀을
  대상으로 한다.

- 조직 트리는 2단계로 되어 있다. 아래 순서를 그대로 따른다(2026-08-21 실측 확인).

  1회차: pOrgId는 org_002205, orgType은 3으로 호출한다.
         Lab 단위 조직 5개가 반환된다.
         이 목록에서 대상 조직명을 찾으면 그 orgId를 확정하고 즉시 종료한다.

  2회차: 1회차에 없으면, 1회차 목록에서 대상 조직이 속할 가능성이 가장 높은 Lab을 하나
         고른다. 조직명이 비슷하거나 사업 영역이 겹치는 것을 고른다.
         그 Lab의 orgId를 pOrgId로 삼고 orgType은 4로 호출한다. 팀 단위 조직이 반환된다.
         여기서 대상 조직명을 찾으면 그 orgId를 확정하고 즉시 종료한다.

  3~4회차: 2회차에 없으면, 1회차 목록의 다른 Lab을 orgType 4로 조회한다.
           최대 4회차까지만 시도한다.

  참고: Enterprise SW프로덕트개발팀은 Enterprise서비스개발Lab(org_001738) 아래 있다.
  이 경우 2회차에서 찾게 된다.

- 🔴 orgList 호출은 전체를 통틀어 최대 4회를 넘기지 않는다. 4회 안에 찾지 못하면 즉시
  중단하고 orgId 자리에 "찾을 수 없음"이라고 쓴 뒤, 그때까지 조회한 조직명 목록을 함께
  적는다. 호출을 더 늘려 탐색을 이어가지 않는다.
- orgType 1과 2는 자기 자신만 반환하므로 호출하지 않는다. 3과 4만 쓴다.
- 여러 개의 유사한 조직명이 나오면 사용자에게 되묻지 말고 가장 정확히 일치하는 1건을
  선택한다. 정확 일치를 우선하고, 없으면 부분 일치 중 첫 번째를 쓴다.
- 작업 1과 2에서 확보한 templateNo와 asstType 값을 잊지 않는다.

[작업 4] 최종 출력
3개 작업이 끝난 뒤 아래 형식으로만 출력한다. 다른 설명은 덧붙이지 않는다.

orgId: 실제 값
orgNm: 실제 조직명
templateNo: 실제 값
asstType: 실제 값

templateNo와 asstType은 반드시 API 응답값을 사용한다. 임의로 지어내지 않는다.
값을 얻지 못한 항목은 빈칸으로 두지 말고 "응답에 값 없음" 또는 "찾을 수 없음"이라고
명시한다.

[중요] 위 3개 API 외에 다른 도구를 호출하지 않는다. 자산 목록 조회나 취약점 조회는
이 플로우의 범위가 아니다."""

TOOL_DESCRIPTIONS = {
    "orgList": (
        "조직 목록을 조회하는 도구. pOrgId(상위 조직 ID)와 orgType(1=부문, 2=그룹, "
        "3=담당, 4=팀)을 입력받아 그 하위 조직 목록을 반환한다. 응답의 orgList 배열에 "
        "orgId와 orgNm이 담겨 있다. 배열 첫 항목은 pOrgId가 빈 값인 자기 자신이므로 "
        "하위 조직이 아니다. "
        "실측 트리 구조(2026-08-21): pOrgId가 org_002205이고 orgType이 3이면 Lab 단위 "
        "5개가 반환되고, 그중 하나를 pOrgId로 삼아 orgType 4로 호출하면 팀 단위가 "
        "반환된다. orgType 1과 2는 자기 자신만 반환하므로 쓰지 않는다."
    ),
    "assetSsrcceTemplate": (
        "사용 가능한 진단템플릿 목록을 조회하는 도구. userId만 입력받는다. 응답의 "
        "templateList 배열에 atemplateNo(진단템플릿 번호)와 templateName(진단템플릿명)이 "
        "담겨 있다."
    ),
    "assetCategory": (
        "자산분류 목록을 조회하는 도구. userId와 asstCtgrLevel을 입력받는다. 응답의 "
        "asstCtgrList 배열에 asstCtgrId(자산분류ID), asstCtgrNm(자산분류명), "
        "asstType(자산타입)이 담겨 있다. asstType은 비어 있는 항목이 있을 수 있다."
    ),
}


def set_field(node: dict, field_name: str, value) -> bool:
    """노드의 특정 필드값을 설정. 성공 시 True."""
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

    # ── 워크플로우 메타 ──
    wf["name"] = "graph_w01_org_lookup"
    wf["display_name"] = "W0-1 조직 조회 (계층 0)"
    wf["description"] = (
        "계층 0 — orgId/templateNo/asstType 확정 전용 단독 플로우. "
        "조직 변경 시에만 실행하고 결과는 상수로 관리한다. "
        "런타임 체인(W1/W2)과 연결하지 않는다. 근거: 12-flow-a-restructure-plan.md 6.2절"
    )
    wf["role"] = "IVMS 계층 0 정적 참조값 확정"

    changes = []

    for n in wf["nodes"]:
        m = n["metadata"]
        name = m.get("name")

        if name == "Agent":
            set_field(n, "system_prompt_template", SYSTEM_PROMPT)
            changes.append("Agent: System Prompt 교체 (호출 상한 4회 명시, 단독 실행 명시)")

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
            changes.append(
                f"{ep}: timeout → connect {CONNECT_TIMEOUT} / read {READ_TIMEOUT}"
            )

            if ep in TOOL_DESCRIPTIONS:
                set_field(n, "tool_description", TOOL_DESCRIPTIONS[ep])
                changes.append(f"{ep}: tool_description 갱신")

    return wf, changes


def verify(wf: dict, target_base: str, other_base: str) -> list:
    """생성 결과 구조 검증. 문제 목록을 반환(빈 리스트면 정상)."""
    problems = []

    nodes = {n["id"]: n for n in wf["nodes"]}
    by_name = {}
    for n in wf["nodes"]:
        by_name.setdefault(n["metadata"]["name"], []).append(n)

    # 1) 필수 노드 구성
    expect = {"Agent": 1, "ChatInput": 1, "ChatOutput": 1, "APIRequest": 3}
    for k, cnt in expect.items():
        got = len(by_name.get(k, []))
        if got != cnt:
            problems.append(f"노드 구성 불일치: {k} 기대 {cnt}개, 실제 {got}개")

    # 2) 엣지 정합성 — 참조 무결성
    for e in wf["edges"]:
        if e["source"] not in nodes:
            problems.append(f"엣지 source 미존재: {e['source'][:8]}")
        if e["target"] not in nodes:
            problems.append(f"엣지 target 미존재: {e['target'][:8]}")

    # 3) Tool 3개가 모두 Agent에 연결됐는지
    agent = by_name.get("Agent", [None])[0]
    if agent:
        aid = agent["id"]
        tool_edges = [
            e for e in wf["edges"]
            if e["target"] == aid and e.get("target_field_name") == "tools"
        ]
        if len(tool_edges) != 3:
            problems.append(f"Agent tools 연결 {len(tool_edges)}개 (기대 3개)")

        # 4) System Prompt 중괄호 검사 (12번 문서 8.4절)
        sp = get_field(agent, "system_prompt_template") or ""
        import re
        # {단일식별자} 형태만 금지. JSON 형태({"key":...})는 무방
        bad = re.findall(r"\{[A-Za-z_][A-Za-z0-9_]*\}", sp)
        if bad:
            problems.append(f"System Prompt에 템플릿 변수로 해석될 중괄호: {set(bad)}")

    # 5) API Request 설정
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
        # 인증 헤더 4종 키 보존 확인 (12번 문서 8.4절 — 값은 비어도 키는 삭제 금지)
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
    print(f" W0-1 조직 조회 플로우 생성 — {env_label}")
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
    print("── 다음 단계 ──")
    print("  1) 캔버스에서 이 JSON을 import")
    print("  2) Chat Input에 조직명 입력 후 실행")
    print("     예) Enterprise SW프로덕트개발팀 참조값 확인해줘")
    print("  3) 출력된 orgId/templateNo/asstType을 받아적어")
    print("     W1/W2의 System Prompt에 상수로 반영")
    print("  4) 이 플로우는 조직 구조가 바뀔 때만 재실행")
    print()
    print("── 🔴 운영기 첫 실행 시 반드시 확인 ──")
    print("  · orgList 호출 횟수 (Thinking 로그) — 상한 4회가 지켜지는지")
    print("  · 조직 트리가 개발기와 같은지 (pOrgId=org_002205 / orgType=3)")
    print("    다르면 프롬프트 [작업 3]의 실측 힌트를 운영기 구조로 교체할 것")
    print("  · templateNo·asstType이 개발기값(151 / SSRCCE)과 같은지")


if __name__ == "__main__":
    main()
