#!/bin/bash
# 조직 단위 자산 규모 측정 + mgmtOrgId 필터 유효성 검증
# 작성일: 2026-08-21
# 목적: 캔버스 한정 제약 하에서 "처리 범위를 조직 단위로 줄이면 예산 안에 들어오는가"를 판정
#
# 배경:
#   12-flow-a-restructure-plan.md 7.2절 — 캔버스에 projection 지점이 없고 서버 필터도
#   무효이므로, 남은 레버는 처리 범위 축소(mgmtOrgId 축)뿐이다. 그 유효성을 재는 스크립트.
#
# 사용법:
#   bash orgscale-debug.sh
#
# 참조: 08-ivms_openapi_spec.md 1.6절(orgList) / 2.2절(mngtListDetail)

set -u

BASE_URL="http://165.244.21.49:8080"       # 개발기. 운영기: https://ivms.lguplus.co.kr
ORG_EP="${BASE_URL}/ivms/api/orgList"
LIST_EP="${BASE_URL}/ivms/api/mngtListDetail"

TARGET_ORG="org_000991"      # Enterprise SW프로덕트개발팀
PARENT_ORG="org_002205"      # 상위 조직
USER_ID="admin"
ASST_TYPE="SSRCCE"
TEMPLATE_NO="151"
DIAG_YEAR="2026"

# 인증 헤더는 빈 값으로도 동작함이 확인됨(2026-08-18, 11번 문서 1절)
HDRS=(-H "Content-Type: application/json")

# 예산 환산 상수 (12번 문서 4-1.5절)
BUDGET=945000
TOK_PER_PAGE=121085          # pageSize=200 기준 1페이지 실측 평균

# ─────────────────────────────────────────────────────────────
# 공통 함수
# ─────────────────────────────────────────────────────────────

# listCount만 추출 (pageSize=1로 최소 응답)
count_of() {
  local oid="$1"
  local body
  if [ -z "$oid" ]; then
    body="{\"userId\":\"$USER_ID\",\"asstType\":\"$ASST_TYPE\",\"templateNo\":\"$TEMPLATE_NO\",\"diagYear\":\"$DIAG_YEAR\",\"page\":1,\"pageSize\":1}"
  else
    body="{\"userId\":\"$USER_ID\",\"asstType\":\"$ASST_TYPE\",\"templateNo\":\"$TEMPLATE_NO\",\"diagYear\":\"$DIAG_YEAR\",\"mgmtOrgId\":\"$oid\",\"page\":1,\"pageSize\":1}"
  fi
  curl -s -m 60 -X POST "${HDRS[@]}" -d "$body" "$LIST_EP" \
    | python3 -c "import json,sys; print(json.load(sys.stdin).get('result',{}).get('listCount','ERR'))" 2>/dev/null
}

# 한 페이지(200건) 받아 조직 분포를 분석
probe_page() {
  local oid="$1" page="$2" tag="$3"
  local body
  if [ -z "$oid" ]; then
    body="{\"userId\":\"$USER_ID\",\"asstType\":\"$ASST_TYPE\",\"templateNo\":\"$TEMPLATE_NO\",\"diagYear\":\"$DIAG_YEAR\",\"page\":$page,\"pageSize\":200}"
  else
    body="{\"userId\":\"$USER_ID\",\"asstType\":\"$ASST_TYPE\",\"templateNo\":\"$TEMPLATE_NO\",\"diagYear\":\"$DIAG_YEAR\",\"mgmtOrgId\":\"$oid\",\"page\":$page,\"pageSize\":200}"
  fi
  curl -s -m 60 -X POST "${HDRS[@]}" -d "$body" "$LIST_EP" > "/tmp/orgscale_${tag}.json"
  MATCH_ORG="$oid" python3 -c "
import json, os, collections
d = json.load(open('/tmp/orgscale_${tag}.json'))
al = d.get('result',{}).get('assetList',[])
if not al:
    print('     (빈 응답)'); raise SystemExit
want = os.environ.get('MATCH_ORG','')
empty = sum(1 for a in al if not (a.get('mgmtOrgId') or '').strip())
match = sum(1 for a in al if (a.get('mgmtOrgId') or '').strip() == want) if want else 0
other = len(al) - empty - match
print(f'     표본 {len(al)}건 → 요청조직 일치 {match}건 / 조직ID 빈값 {empty}건 / 타조직 {other}건')
"
}

echo "=============================================================="
echo " 조직 규모 측정 + mgmtOrgId 필터 검증"
echo " BASE: $BASE_URL"
echo " 응답 원본은 /tmp/orgscale_*.json 에 저장됨"
echo "=============================================================="
echo

# ─────────────────────────────────────────────────────────────
# [S1] 조직 트리 — 대상 조직에 하위가 있는가
#      orgType: 1=부문 2=그룹 3=담당 4=팀
# ─────────────────────────────────────────────────────────────
echo "── [S1] 조직 트리 탐색 ──"
for pid in "$TARGET_ORG" "$PARENT_ORG"; do
  echo "  pOrgId=$pid"
  for t in 1 2 3 4; do
    n=$(curl -s -m 25 "${ORG_EP}?orgType=${t}&pOrgId=${pid}" \
      | python3 -c "
import json,sys
ol = json.load(sys.stdin).get('result',{}).get('orgList',[])
# 자기 자신('직속', pOrgId 빈값)은 하위 조직이 아니므로 제외
print(len([o for o in ol if (o.get('pOrgId') or '').strip()]))
" 2>/dev/null)
    printf '     orgType=%s → 하위 조직 %s개\n' "$t" "$n"
  done
done
echo
echo "  ▸ 하위 조직 목록 (pOrgId=$PARENT_ORG, orgType=3):"
curl -s -m 25 "${ORG_EP}?orgType=3&pOrgId=${PARENT_ORG}" | python3 -c "
import json,sys
for o in json.load(sys.stdin).get('result',{}).get('orgList',[]):
    if (o.get('pOrgId') or '').strip():
        print(f\"     {o['orgId']:<14} {o['orgNm']}\")
" 2>/dev/null
echo

# ─────────────────────────────────────────────────────────────
# [S2] 🔴 필터 유효성 — 존재하지 않는 조직 ID와 대조
#      이 대조 없이는 "건수가 다르다 = 필터가 동작한다"고 오판하게 된다
# ─────────────────────────────────────────────────────────────
echo "── [S2] mgmtOrgId 필터 유효성 (가짜 ID 대조) ──"
C_NONE=$(count_of "")
C_TARGET=$(count_of "$TARGET_ORG")
C_BOGUS=$(count_of "org_ZZZZZZZ")
printf '  %-22s %8s건\n' "미지정" "$C_NONE"
printf '  %-22s %8s건\n' "$TARGET_ORG (실재)" "$C_TARGET"
printf '  %-22s %8s건  ← 기준선\n' "org_ZZZZZZZ (가짜)" "$C_BOGUS"
echo
echo "  ▸ 응답 200건 표본의 조직 분포:"
echo "    [미지정]";        probe_page ""            1 "nofilter"
echo "    [$TARGET_ORG]";   probe_page "$TARGET_ORG" 1 "target"
echo "    [가짜 ID]";       probe_page "org_ZZZZZZZ" 1 "bogus"
echo
echo "  ▸ 판정: 가짜 ID 응답의 전량이 '조직ID 빈값'이면, 그 건수는 필터 무효가 아니라"
echo "          조직 미기입 자산이 조건과 무관하게 딸려오는 것이다."
echo "          → 실자산 ≈ (조직 조회 건수) − (가짜 ID 건수)"
echo

# ─────────────────────────────────────────────────────────────
# [S3] 조직별 규모 + garbage 보정
# ─────────────────────────────────────────────────────────────
echo "── [S3] 조직별 자산 규모 (garbage 보정) ──"
printf '  %-14s %-26s %10s %10s %8s\n' "조직ID" "조직명" "반환건수" "실자산(추정)" "페이지"
echo "  ────────────────────────────────────────────────────────────────────────"
measure_org() {
  local oid="$1" onm="$2"
  local c; c=$(count_of "$oid")
  if [ "$c" = "ERR" ]; then printf '  %-14s %-26s %10s\n' "$oid" "$onm" "ERR"; return; fi
  local real=$(( c - C_BOGUS )); [ "$real" -lt 0 ] && real=0
  local pages=$(( (real + 199) / 200 )); [ "$pages" -lt 1 ] && pages=1
  printf '  %-14s %-26s %10s %10s %8s\n' "$oid" "$onm" "$c" "$real" "$pages"
}
measure_org "$PARENT_ORG" "SW개발센터(상위)"
measure_org "$TARGET_ORG" "EnterpriseSW프로덕트개발팀"
curl -s -m 25 "${ORG_EP}?orgType=3&pOrgId=${PARENT_ORG}" | python3 -c "
import json,sys
for o in json.load(sys.stdin).get('result',{}).get('orgList',[]):
    if (o.get('pOrgId') or '').strip(): print(o['orgId'], o['orgNm'])
" 2>/dev/null | while read -r oid onm; do
  measure_org "$oid" "$onm"
done
echo

# ─────────────────────────────────────────────────────────────
# [S4] garbage 구간 경계 — 조직ID 미기입 자산이 어디부터인지
# ─────────────────────────────────────────────────────────────
echo "── [S4] 조직ID 미기입 자산 구간 (무필터 전량 기준) ──"
TOTAL_PAGES=$(( (C_NONE + 199) / 200 ))
echo "  전체 ${C_NONE}건 = ${TOTAL_PAGES}페이지. 이분 탐색으로 빈값 시작 지점 탐색"
lo=1; hi=$TOTAL_PAGES
while [ $((hi-lo)) -gt 1 ]; do
  mid=$(( (lo+hi)/2 ))
  e=$(curl -s -m 60 -X POST "${HDRS[@]}" \
    -d "{\"userId\":\"$USER_ID\",\"asstType\":\"$ASST_TYPE\",\"templateNo\":\"$TEMPLATE_NO\",\"diagYear\":\"$DIAG_YEAR\",\"page\":$mid,\"pageSize\":200}" \
    "$LIST_EP" \
    | python3 -c "import json,sys; al=json.load(sys.stdin).get('result',{}).get('assetList',[]); print(sum(1 for a in al if not (a.get('mgmtOrgId') or '').strip()))" 2>/dev/null)
  printf '     page %4d → 빈값 %3s건\n' "$mid" "$e"
  if [ "${e:-0}" -ge 100 ]; then hi=$mid; else lo=$mid; fi
done
echo "  → 빈값 구간 시작: 약 page $hi (약 $((hi*200))번째 자산부터)"
echo "  → 조직ID 채워진 자산: 약 $((lo*200))건 / ${C_NONE}건"
echo

# ─────────────────────────────────────────────────────────────
# [S5] 예산 환산 — 캔버스 단독 성립 여부
# ─────────────────────────────────────────────────────────────
echo "── [S5] 예산 환산 (예산 $BUDGET tok, 1페이지 ≈ $TOK_PER_PAGE tok) ──"
REAL_TARGET=$(( C_TARGET - C_BOGUS )); [ "$REAL_TARGET" -lt 0 ] && REAL_TARGET=0
python3 - "$C_TARGET" "$REAL_TARGET" "$BUDGET" "$TOK_PER_PAGE" <<'PY'
import sys, math
raw, real, budget, tpp = map(int, sys.argv[1:5])
def rep(lbl, n):
    pages = max(1, math.ceil(n/200))
    tok = pages * tpp
    print(f'  {lbl:<28} {n:>7}건  {pages:>3}페이지  {tok:>9,} tok  예산의 {tok/budget*100:6.1f}%')
rep('개발기 반환값(garbage 포함)', raw)
rep('실자산 추정(garbage 제외)', real)
print()
# Agent당 상한: 규칙 ①(제곱 누적) 적용 시 3페이지, 누적 없이 7페이지
for lbl, cap in (('규칙 ①(제곱 누적) 적용', 3), ('누적 없음(선형)', 7)):
    limit = cap * 200
    runs = max(1, math.ceil(real/limit)) if real else 1
    ok = '✅ 캔버스 단독 성립' if runs <= 3 else '❌ 실행 횟수 과다'
    print(f'  {lbl:<28} Agent당 {cap}페이지({limit}건) → 계층1 {runs}회 실행  {ok}')
PY
echo

echo "=============================================================="
echo " 해석 가이드"
echo "──────────────────────────────────────────────────────────────"
echo " S2에서 가짜 ID 응답이 전량 '빈값'  → 필터는 정상. 건수는 garbage 혼입"
echo " S2에서 가짜 ID 응답에 실제 조직 혼재 → 필터 결함. IVMS팀 확인 필요"
echo " S5 실자산이 1,400건(7페이지) 이하   → 조직 단위 캔버스 워크플로우 성립"
echo " S5 실자산이 수천 건                  → 캔버스 단독 불가. 플랫폼 개선 선결"
echo
echo " ⚠️ 개발기 한정 주의"
echo "    - chrgId 채움률 0% → 담당자 축 검증 불가 (12번 문서 4-1.4절)"
echo "    - 조직ID 미기입 자산이 조회마다 딸려오므로 개발기 규모 검증은 S3 보정값 기준"
echo "    - 운영기 실규모는 별도 측정 필요"
echo "=============================================================="
