"""HTML 안에 박힌 쪽 나눔 스크립트(template/paginate.js)를 지금 템플릿 것으로 바꾼다 (2026-11-04).
build.py로 다시 만들지 않는 권(CRF 필드 매뉴얼 16권)도 표·제목 규칙을 같이 받게 하려는 것이다.
사용: python3 tools/update_paginate.py manuals [분권 ...]   (분권을 안 주면 manuals 아래 모든 html)
"""
import os, re, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
js = open(f'{ROOT}/template/paginate.js').read().strip()
css = open(f'{ROOT}/template/style.css').read()
# build.py의 원형 숫자 코드(FONT ~ circle)를 그대로 떼어 와 쓴다. 언어별 글꼴(ja = Pretendard JP)
_src = open(f'{ROOT}/template/build.py').read()
_blk = _src[_src.index('FONT = '):_src.index('# ---------- 글(런 목록)')]
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
def circle_mod(lang):
    ns = dict(HERE=f'{ROOT}/template', lang=lang, TTFont=TTFont, BoundsPen=BoundsPen); exec(_blk, ns); return ns
_mods = {}
SVG = re.compile(r'<svg class="cn" width="(\d+)" height="\d+" viewBox="[^"]*" aria-hidden="false">(.*?)</svg>', re.S)
def redraw(m):
    dia, body = int(m.group(1)), m.group(2); build_mod = CUR
    n = re.search(r'>([^<]*)</text>', body).group(1)
    tfill = re.search(r'<text[^>]*fill="([^"]+)"', body).group(1)
    kind = 'res' if tfill.upper() == build_mod['BLUE'].upper() else ('set' if build_mod['BLUE'] in body else 'ref')
    if dia == 14: where = 'legend'
    elif dia == 23: where = 'item'
    elif dia == 22: where = 'mk' if 'r="11" fill="#fff"' in body.replace('r="11.0"', 'r="11"') else 'res'
    else: return m.group(0)
    return build_mod['circle'](kind, n, where)
root = sys.argv[1]; vols = sys.argv[2:] or sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
n = 0; skip = 0
for v in vols:
    for hp in sorted(glob.glob(os.path.join(root, v, '*', '*.html'))):
        h = open(hp).read()
        lang = os.path.basename(os.path.dirname(hp))
        if lang not in _mods: _mods[lang] = circle_mod(lang)
        CUR = _mods[lang]
        i = h.find('<script>(async function () {')
        if i < 0: skip += 1; continue
        i += len('<script>'); j = h.find('})();', i) + len('})();')
        changed = h[i:j].strip() != js
        h = h[:i] + js + h[j:]
        # 인라인 CSS(첫 <style> 블록 = template/style.css)도 바꾼다 (2026-11-09 글자 크기 짝수화)
        a = h.find('<style>'); b = h.find('</style>', a)
        if a >= 0 and '@page{size:210mm 297mm' in h[a:b] and h[a + 7:b] != css:
            h = h[:a + 7] + css + h[b:]; changed = True
        # 번호 원 SVG도 지금 build.py 크기로 다시 그린다 (2026-11-09 숫자 12px·범례 10px)
        h2 = SVG.sub(redraw, h)
        if h2 != h: h = h2; changed = True
        if not changed: continue
        open(hp, 'w').write(h); n += 1; print('updated', hp)
print('updated', n, 'no script', skip)
