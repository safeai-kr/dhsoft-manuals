"""HTML 안에 박힌 쪽 나눔 스크립트(template/paginate.js)를 지금 템플릿 것으로 바꾼다 (2026-11-04).
build.py로 다시 만들지 않는 권(CRF 필드 매뉴얼 16권)도 표·제목 규칙을 같이 받게 하려는 것이다.
사용: python3 tools/update_paginate.py manuals [분권 ...]   (분권을 안 주면 manuals 아래 모든 html)
"""
import os, re, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
js = open(f'{ROOT}/template/paginate.js').read().strip()
root = sys.argv[1]; vols = sys.argv[2:] or sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
n = 0; skip = 0
for v in vols:
    for hp in sorted(glob.glob(os.path.join(root, v, '*', '*.html'))):
        h = open(hp).read()
        i = h.find('<script>(async function () {')
        if i < 0: skip += 1; continue
        i += len('<script>'); j = h.find('})();', i) + len('})();')
        if h[i:j].strip() == js: continue
        open(hp, 'w').write(h[:i] + js + h[j:]); n += 1; print('updated', hp)
print('updated', n, 'no script', skip)
