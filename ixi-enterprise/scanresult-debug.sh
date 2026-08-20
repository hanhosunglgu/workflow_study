#!/bin/bash
# scanResultCodeMngtDetail msgCd:E 원인 규명용 진단 스크립트
# 작성일: 2026-08-18
# 목적: 3단계에서 "필수 컬럼 확인 필요" 오류를 유발하는 파라미터를 이분 탐색으로 특정
#
# 사용법:
#   1) 아래 BASE_URL을 개발기 주소로 수정
#   2) ASSTCODE1/2, HOSTNM1/2를 2-2단계에서 얻은 실제 값으로 교체
#   3) bash scanresult-debug.sh
#
# 참조: 08-ivms_openapi_spec.md 4.2절 (검증된 성공 curl)

set -u

# ─────────────────────────────────────────────────────────────
# 설정 — 실행 전 반드시 수정
# ─────────────────────────────────────────────────────────────
BASE_URL="http://165.244.21.49:8080"       # 개발기 (2026-08-18 확인). 운영기: https://ivms.lguplus.co.kr
EP="${BASE_URL}/ivms/api/scanResultCodeMngtDetail"

# 2-2단계 결과에서 가져온 실제 자산코드/호스트명으로 교체할 것
ASSTCODE1="SSRCCE3-000747"
ASSTCODE2="SSRCCE3-000492"
HOSTNM1="lbsh1"
HOSTNM2="absdb1"

USER_ID="admin"
ASST_TYPE="SSRCCE"
TEMPLATE_NO="151"

# 인증 헤더는 빈 값으로도 동작함이 확인됨(2026-08-18, 11번 문서 1절)
HDRS=(
  -H "Content-Type: application/json"
  -H "X-Global-Transaction-ID: "
  -H "X-APP-NAME: "
  -H "X-AuthorizationTime: "
  -H "X-Header-Authorization: "
)

# ─────────────────────────────────────────────────────────────
# 공통 호출 함수: 결과를 성공/실패로만 요약 출력
# ─────────────────────────────────────────────────────────────
call() {
  local label="$1"; local body="$2"
  local resp
  resp=$(curl -s -k -m 30 -X POST "${HDRS[@]}" -d "$body" "$EP" 2>&1)

  local verdict
  if echo "$resp" | grep -q '"msgCd":"E"'; then
    verdict="❌ FAIL"
  elif echo "$resp" | grep -q 'scanRsltCodeList'; then
    local cnt
    cnt=$(echo "$resp" | grep -o '"guidelineCd"' | wc -l | tr -d ' ')
    verdict="✅ OK (항목 ${cnt}건)"
  else
    verdict="⚠️  UNKNOWN"
  fi

  printf '%-46s %s\n' "$label" "$verdict"
  # 파일명에 쓸 수 없는 문자(/ ( ) 공백 등) 제거
  local safe
  safe=$(echo "$label" | tr -c 'a-zA-Z0-9_=-' '_')
  echo "$resp" > "/tmp/scanresult_${safe}.json"

  # 실패 시 서버 메시지만 한 줄로
  if [ "${verdict:0:1}" = "❌" ] || [ "${verdict:0:1}" = "⚠" ]; then
    echo "     └ $(echo "$resp" | head -c 200)"
  fi
}

echo "=============================================================="
echo " scanResultCodeMngtDetail 진단"
echo " EP: $EP"
echo " 전체 응답은 /tmp/scanresult_*.json 에 저장됨"
echo "=============================================================="
echo

# ─────────────────────────────────────────────────────────────
# [T1] 08번 문서의 검증된 성공 조합 그대로 — 기준선
#      이것이 실패하면 서버/환경 문제이지 파라미터 문제가 아님
# ─────────────────────────────────────────────────────────────
echo "── [T1] 문서상 검증된 성공 조합 (기준선) ──"
call "T1 baseline (pageSize=50, asstCode 2건)" "$(cat <<EOF
{
  "userId": "$USER_ID",
  "asstCode": ["$ASSTCODE1", "$ASSTCODE2"],
  "hostNm": ["$HOSTNM1", "$HOSTNM2"],
  "resultStatusCdListStr": "[\"FAIL\"]",
  "vadaYn": "N",
  "severity": "4",
  "asstType": "$ASST_TYPE",
  "atemplateNo": "$TEMPLATE_NO",
  "page": 1,
  "pageSize": 50
}
EOF
)"
echo

# ─────────────────────────────────────────────────────────────
# [T2] pageSize 가설 검증 — 현재 가장 유력한 후보
#      T1 성공 + T2 실패 → pageSize가 원인 확정
# ─────────────────────────────────────────────────────────────
echo "── [T2] pageSize 변화 (T1에서 pageSize만 변경) ──"
for ps in 100 200; do
  call "T2 pageSize=$ps" "$(cat <<EOF
{
  "userId": "$USER_ID",
  "asstCode": ["$ASSTCODE1", "$ASSTCODE2"],
  "hostNm": ["$HOSTNM1", "$HOSTNM2"],
  "resultStatusCdListStr": "[\"FAIL\"]",
  "vadaYn": "N",
  "severity": "4",
  "asstType": "$ASST_TYPE",
  "atemplateNo": "$TEMPLATE_NO",
  "page": 1,
  "pageSize": $ps
}
EOF
)"
done
echo

# ─────────────────────────────────────────────────────────────
# [T3] 파라미터 1개씩 제거 — 어떤 것이 실제 필수인지 확인
#      스펙표는 userId/asstType/severity 3개만 필수(Y)로 기재하나
#      mngtListDetail 선례상 서버 실제 요구가 다를 수 있음
# ─────────────────────────────────────────────────────────────
echo "── [T3] 파라미터 개별 제거 (실패 = 그 값이 실제 필수) ──"

call "T3 without atemplateNo" "$(cat <<EOF
{"userId":"$USER_ID","asstCode":["$ASSTCODE1","$ASSTCODE2"],"hostNm":["$HOSTNM1","$HOSTNM2"],
 "resultStatusCdListStr":"[\"FAIL\"]","vadaYn":"N","severity":"4","asstType":"$ASST_TYPE","page":1,"pageSize":50}
EOF
)"

call "T3 without vadaYn" "$(cat <<EOF
{"userId":"$USER_ID","asstCode":["$ASSTCODE1","$ASSTCODE2"],"hostNm":["$HOSTNM1","$HOSTNM2"],
 "resultStatusCdListStr":"[\"FAIL\"]","severity":"4","asstType":"$ASST_TYPE","atemplateNo":"$TEMPLATE_NO","page":1,"pageSize":50}
EOF
)"

call "T3 without hostNm" "$(cat <<EOF
{"userId":"$USER_ID","asstCode":["$ASSTCODE1","$ASSTCODE2"],
 "resultStatusCdListStr":"[\"FAIL\"]","vadaYn":"N","severity":"4","asstType":"$ASST_TYPE","atemplateNo":"$TEMPLATE_NO","page":1,"pageSize":50}
EOF
)"

call "T3 without resultStatusCdListStr" "$(cat <<EOF
{"userId":"$USER_ID","asstCode":["$ASSTCODE1","$ASSTCODE2"],"hostNm":["$HOSTNM1","$HOSTNM2"],
 "vadaYn":"N","severity":"4","asstType":"$ASST_TYPE","atemplateNo":"$TEMPLATE_NO","page":1,"pageSize":50}
EOF
)"

call "T3 without page/pageSize" "$(cat <<EOF
{"userId":"$USER_ID","asstCode":["$ASSTCODE1","$ASSTCODE2"],"hostNm":["$HOSTNM1","$HOSTNM2"],
 "resultStatusCdListStr":"[\"FAIL\"]","vadaYn":"N","severity":"4","asstType":"$ASST_TYPE","atemplateNo":"$TEMPLATE_NO"}
EOF
)"
echo

# ─────────────────────────────────────────────────────────────
# [T4] asstLCtgrId 추가 — 2순위 후보
#      T1이 실패했을 때 이 값이 필요한지 확인
#      AT_0005393 / AT_0005382 는 08번 문서의 샘플값(조직마다 다를 수 있음)
# ─────────────────────────────────────────────────────────────
echo "── [T4] asstLCtgrId 추가 (T1 실패 시 확인) ──"
for ctgr in AT_0005393 AT_0005382; do
  call "T4 asstLCtgrId=$ctgr" "$(cat <<EOF
{"userId":"$USER_ID","asstCode":["$ASSTCODE1","$ASSTCODE2"],"hostNm":["$HOSTNM1","$HOSTNM2"],
 "resultStatusCdListStr":"[\"FAIL\"]","vadaYn":"N","severity":"4","asstType":"$ASST_TYPE",
 "atemplateNo":"$TEMPLATE_NO","asstLCtgrId":"$ctgr","page":1,"pageSize":50}
EOF
)"
done
echo

# ─────────────────────────────────────────────────────────────
# [T5] 최소 조합 — 스펙표상 필수(Y) 3개만
# ─────────────────────────────────────────────────────────────
echo "── [T5] 스펙표상 필수 3개만 ──"
call "T5 minimal (userId/asstType/severity)" \
  "{\"userId\":\"$USER_ID\",\"asstType\":\"$ASST_TYPE\",\"severity\":\"4\"}"
echo

echo "=============================================================="
echo " 해석 가이드"
echo "──────────────────────────────────────────────────────────────"
echo " T1 ✅ & T2 ❌  → pageSize가 원인. 캔버스에서 50 사용(이미 반영됨)"
echo " T1 ✅ & T2 ✅  → pageSize 무관. asstCode 건수(10건) 또는"
echo "                  실제 자산코드 값 문제일 가능성 → 값 교체 후 재실행"
echo " T1 ❌ & T4 ✅  → asstLCtgrId가 실제 필수. #1A에 assetCategory 재연결 필요"
echo " T1 ❌ & T4 ❌  → 자산코드/호스트명 값이 유효하지 않거나 서버 정책 변경"
echo "                  → T5 결과와 08번 문서 4.2절 재대조 필요"
echo " T3에서 실패한 항목 = 스펙표 표기와 무관하게 서버가 실제로 요구하는 필수값"
echo "=============================================================="
