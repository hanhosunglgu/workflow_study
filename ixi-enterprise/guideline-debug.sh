#!/bin/bash
# guidelineCdInfo(4단계) 진단 스크립트 — 개발기
# 작성일: 2026-08-18
# 목적: 프로젝트 시작 이래 한 번도 검증되지 않은 4단계 API를 캔버스에 올리기 전 curl로 선검증
#
# 사용법:
#   1) 3단계 결과에서 얻은 4개 키를 아래 변수에 입력
#   2) bash guideline-debug.sh
#
# 참조: 08-ivms_openapi_spec.md 4.5절
#       ixi-enterprise/docs/ivms-flow-a-build-lessons.md 3절(진단 방법)

set -u

# ─────────────────────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────────────────────
BASE_URL="http://165.244.21.49:8080"       # 개발기. 운영기: https://ivms.lguplus.co.kr
EP="${BASE_URL}/ivms/api/guidelineCdInfo"

# ⚠️ 3단계(scanResultCodeMngtDetail) 응답에서 가져온 실제 값으로 교체할 것
#    아래 기본값은 08번 문서 4.5절의 캡처 샘플이며, 개발기에 없는 데이터일 수 있음
#
#    3단계 응답 필드 → 이 스크립트 변수 매핑:
#      resultIfKey     → ARESULT_NO      (진단결과 번호)
#      guidelineIfKey  → GUIDELINE_IFKEY (항목 인터페이스키)
#      guidelineCd     → GUIDELINE_CD    (항목코드)
#      itemCode        → ITEM_CODE       (시스템코드)
#      agentServerNm   → AGENT_SERVER    (에이전트 서버명)
ARESULT_NO="269953"
GUIDELINE_IFKEY="81438"
GUIDELINE_CD="DBM-001"
ITEM_CODE="MAR6103_001"
AGENT_SERVER="CCE3"

# 인증 헤더는 빈 값으로도 동작함이 확인됨(2026-08-18)
HDRS=(
  -H "X-Global-Transaction-ID: "
  -H "X-APP-NAME: "
  -H "X-AuthorizationTime: "
  -H "X-Header-Authorization: "
)

# ─────────────────────────────────────────────────────────────
# 공통 호출 함수 (GET + Query String)
# ─────────────────────────────────────────────────────────────
call() {
  local label="$1"; shift
  local qs="$1"
  local resp safe

  resp=$(curl -s -k -m 30 -G "${HDRS[@]}" "$EP" $qs 2>&1)

  safe=$(echo "$label" | tr -c 'a-zA-Z0-9_=-' '_')
  echo "$resp" > "/tmp/guideline_${safe}.json"

  local verdict
  if echo "$resp" | grep -q '"msgCd":"E"'; then
    verdict="❌ FAIL (msgCd:E)"
  elif echo "$resp" | grep -q '"measure"'; then
    # 응답에 실제로 돌아온 항목코드 추출 (요청값과 일치하는지 확인용)
    local got
    got=$(echo "$resp" | grep -o '"guidelineCd"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
    verdict="✅ OK (응답 guidelineCd=${got:-?})"
  elif echo "$resp" | grep -q 'guidelineCdInfo'; then
    verdict="⚠️  응답은 왔으나 measure 없음"
  else
    verdict="⚠️  UNKNOWN"
  fi

  printf '%-44s %s\n' "$label" "$verdict"
  if [ "${verdict:0:1}" != "✅" ]; then
    echo "     └ $(echo "$resp" | head -c 200)"
  fi
}

# 전체 파라미터 조합
FULL="--data-urlencode aresultNo=$ARESULT_NO \
--data-urlencode guidelineIfKey=$GUIDELINE_IFKEY \
--data-urlencode guidelineCd=$GUIDELINE_CD \
--data-urlencode itemCode=$ITEM_CODE \
--data-urlencode agentServerNm=$AGENT_SERVER"

echo "=============================================================="
echo " guidelineCdInfo 진단 (4단계 선검증)"
echo " EP: $EP"
echo " 전체 응답: /tmp/guideline_*.json"
echo "=============================================================="
echo " 요청 항목코드: $GUIDELINE_CD  (응답이 이 값과 다르면 8절 참고)"
echo

# ─────────────────────────────────────────────────────────────
# [G1] 전체 5개 파라미터 — 기준선
# ─────────────────────────────────────────────────────────────
echo "── [G1] 스펙표상 필수 5개 전체 (기준선) ──"
call "G1 all 5 params" "$FULL"
echo

# ─────────────────────────────────────────────────────────────
# [G2] 파라미터 1개씩 제거 — 실제 필수값 색출
#      스펙표는 5개 모두 필수(Y)로 기재하나, mngtListDetail·
#      scanResultCodeMngtDetail 선례상 실제와 다를 수 있음
# ─────────────────────────────────────────────────────────────
echo "── [G2] 파라미터 개별 제거 (실패 = 실제 필수) ──"

call "G2 without aresultNo" \
"--data-urlencode guidelineIfKey=$GUIDELINE_IFKEY --data-urlencode guidelineCd=$GUIDELINE_CD \
--data-urlencode itemCode=$ITEM_CODE --data-urlencode agentServerNm=$AGENT_SERVER"

call "G2 without guidelineIfKey" \
"--data-urlencode aresultNo=$ARESULT_NO --data-urlencode guidelineCd=$GUIDELINE_CD \
--data-urlencode itemCode=$ITEM_CODE --data-urlencode agentServerNm=$AGENT_SERVER"

call "G2 without guidelineCd" \
"--data-urlencode aresultNo=$ARESULT_NO --data-urlencode guidelineIfKey=$GUIDELINE_IFKEY \
--data-urlencode itemCode=$ITEM_CODE --data-urlencode agentServerNm=$AGENT_SERVER"

call "G2 without itemCode" \
"--data-urlencode aresultNo=$ARESULT_NO --data-urlencode guidelineIfKey=$GUIDELINE_IFKEY \
--data-urlencode guidelineCd=$GUIDELINE_CD --data-urlencode agentServerNm=$AGENT_SERVER"

call "G2 without agentServerNm" \
"--data-urlencode aresultNo=$ARESULT_NO --data-urlencode guidelineIfKey=$GUIDELINE_IFKEY \
--data-urlencode guidelineCd=$GUIDELINE_CD --data-urlencode itemCode=$ITEM_CODE"
echo

# ─────────────────────────────────────────────────────────────
# [G3] 응답 일치성 검증 — 09번 문서 5.3절의 알려진 이슈
#      "요청 파라미터와 무관한 응답을 반환"하는 사례가 보고됨
#      guidelineCd만 바꿔 호출했을 때 응답이 따라 바뀌는지 확인
# ─────────────────────────────────────────────────────────────
echo "── [G3] 응답이 요청 guidelineCd를 따르는지 (알려진 이슈 검증) ──"
for cd in "$GUIDELINE_CD" "U-103" "U-106"; do
  call "G3 guidelineCd=$cd" \
"--data-urlencode aresultNo=$ARESULT_NO --data-urlencode guidelineIfKey=$GUIDELINE_IFKEY \
--data-urlencode guidelineCd=$cd --data-urlencode itemCode=$ITEM_CODE \
--data-urlencode agentServerNm=$AGENT_SERVER"
done
echo

# ─────────────────────────────────────────────────────────────
# [G4] 실제 조치가이드(measure) 본문 확인
# ─────────────────────────────────────────────────────────────
echo "── [G4] measure 필드 본문 미리보기 ──"
if [ -f /tmp/guideline_G1_all_5_params.json ]; then
  python3 - <<'PY' 2>/dev/null || echo "  (python3 파싱 실패 — /tmp/guideline_G1_all_5_params.json 직접 확인)"
import json
d=json.load(open('/tmp/guideline_G1_all_5_params.json'))
g=d.get('result',{}).get('guidelineCdInfo',{})
if not g:
    print("  guidelineCdInfo 없음 — 응답 구조 확인 필요"); raise SystemExit
print(f"  guidelineCd : {g.get('guidelineCd')}")
print(f"  guidelineNm : {g.get('guidelineNm')}")
for k in ('criteria','analysisInfo','measure'):
    v=(g.get(k) or '').replace('\n',' ')
    print(f"  {k:12}: {v[:110]}{'...' if len(v)>110 else ''}  (len={len(g.get(k) or '')})")
PY
fi
echo

echo "=============================================================="
echo " 해석 가이드"
echo "──────────────────────────────────────────────────────────────"
echo " G1 ✅ → 4단계 호출 가능. 캔버스 진행 OK"
echo " G1 ❌ → 3단계에서 얻은 키 값이 실제로 유효한지 먼저 확인"
echo "         (스크립트 상단 5개 변수를 3단계 응답값으로 교체했는지)"
echo " G2에서 ✅ 인 항목 = 스펙표는 필수(Y)이나 실제로는 선택"
echo "         → 08번 문서 4.5절에 기록할 것"
echo " G3에서 guidelineCd를 바꿔도 응답이 동일 → 09번 문서 5.3절"
echo "         '파라미터 무관 응답' 이슈 재현. Agent가 항목별 조치가이드를"
echo "         구분할 수 없다는 뜻이므로 5단계 설계에 영향 → 운영팀 문의 필요"
echo " G3에서 응답이 요청을 따라 바뀜 → 이슈 해소됨. 정상 사용 가능"
echo "=============================================================="
