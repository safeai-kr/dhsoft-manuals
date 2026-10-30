#!/bin/sh
# 화면별 분권 18권 × 언어를 한꺼번에 만들고 검사한다. 사용: sh template/make_all.sh [ko|en|de|ja ...]
cd "$(dirname "$0")/.." || exit 1
LANGS="${*:-ko en de ja}"
for v in 로그인 내계정 플랫폼관리 워크스페이스 프로젝트 참여기관 기관관리 사용자관리 SAE통보_권한관리 방문정의 배정 피험자 데이터입력 Query AE지정 Lock AuditTrail 데이터내보내기; do
  for l in $LANGS; do
    if [ "$l" = ko ] || [ -f "manuals/$v/data/$l.json" ]; then
      python3 -W ignore template/build.py "$v" "$l" >/dev/null || { echo "BUILD FAIL $v $l"; continue; }
      python3 template/check.py "$v" "$l" | tail -1 | python3 -c "import sys,json; c=json.loads(sys.stdin.read()); print(c['manual'], c['lang'], c['pages'], 'PASS' if c['pass'] else 'FAIL '+str({k:v for k,v in c['checks'].items() if not v['pass']}))"
    fi
  done
done
python3 template/index_update.py
