#!/bin/sh
# 번역본 캡처 글자 교체부터 검사까지 한 번에. 사용: sh template/localize_all.sh [분권 ...]   (언어는 LANGS 환경변수, 기본 en de ja)
# 순서: img_localize(글자 교체) → build(HTML) → widen_buttons·extend_cut_buttons(좁은 버튼) → place_markers(번호 원 옮기기) → check_img_hangul(한글 0) → check_img_patch(얼룩 0) → check(쪽 검사)
# OCR 실행 파일: IMG_OCR_BIN (없으면 swift 스크립트를 직접 돌린다)
cd "$(dirname "$0")/.." || exit 1
VOLS="${*:-로그인 내계정 플랫폼관리 워크스페이스 프로젝트 참여기관 기관관리 사용자관리 SAE통보_권한관리 방문정의 배정 피험자 데이터입력 Query AE지정 Lock AuditTrail 데이터내보내기}"
SHEETS="${WIDEN_SHEETS:-/tmp/widen_sheets}"; mkdir -p "$SHEETS"
for v in $VOLS; do
  for l in ${LANGS:-en de ja}; do
    python3 template/img_localize.py "$v" "$l" | grep -v '^s[0-9]' || { echo "LOCALIZE FAIL $v $l"; continue; }
    python3 -W ignore template/build.py "$v" "$l" >/dev/null || { echo "BUILD FAIL $v $l"; continue; }
    python3 tools/widen_buttons.py manuals --only "$v/$l" --sheet "$SHEETS" | tail -1 | sed "s/^/widen $v $l /"
    python3 tools/extend_cut_buttons.py manuals --only "$v/$l" | tail -1 | sed "s/^/extend $v $l /"
    python3 tools/place_markers.py manuals --only "$v/$l" | tail -1 | sed "s/^/markers $v $l /"
    python3 template/check_img_hangul.py "$v" "$l" | head -1
    python3 template/check_img_patch.py "$v" "$l" | head -1
    python3 template/check.py "$v" "$l" | tail -1 | python3 -c "import sys,json; c=json.loads(sys.stdin.read()); print(c['manual'], c['lang'], c['pages'], 'PASS' if c['pass'] else 'FAIL '+str({k:v for k,v in c['checks'].items() if not v['pass']}))"
  done
done
