#!/usr/bin/env python3
"""분권 구조 데이터(data/model.json)와 번역(data/<lang>.json)으로 A4 쪽 HTML을 만든다.
사용: python3 build.py <분권> <lang> [--export]
  --export  번역 단위만 뽑는다 → data/units_ko.json (번역 뒤 data/<lang>.json 으로 돌려받는다)
결과: manuals/<분권>/<lang>/SMART-EDC_사용자매뉴얼_<분권>_<lang>.html · img/ · fonts/ · img/quality-manifest.json
디자인 규칙: prompt/SMART-EDC_매뉴얼_디자인_고정프롬프트.md (CSS·쪽 나눔 JS는 template/style.css, template/paginate.js 하나를 전 분권·전 언어가 같이 쓴다)
"""
import json, re, os, sys, html as H, shutil
from PIL import Image, ImageFilter
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
vol, lang = sys.argv[1], sys.argv[2]
EXPORT = '--export' in sys.argv
V = f'{ROOT}/manuals/{vol}'; D = f'{V}/data'; OUT = f'{V}/{lang}'
m = json.load(open(f'{D}/model.json'))
joins = json.load(open(f'{D}/joins.json')) if os.path.exists(f'{D}/joins.json') else {}
FIXED = json.load(open(f'{HERE}/fixed.json'))[lang]
FX = lambda k: FIXED[k]
TR = {} if lang == 'ko' or EXPORT else json.load(open(f'{D}/{lang}.json'))
units = []          # 번역 단위 (key, kind, ko)
esc = lambda t: H.escape(t, quote=False)
plain = lambda h: re.sub(r'<[^>]+>', '', h)
KEEP_REF_WORD = False   # True면 「(1.4 참조)」의 '참조'를 글자로 남긴다 (hy0909 확인 전 기본값: 괄호와 함께 뺀다)

def U(key, kind, ko_html):
    """번역 단위를 기록하고, 해당 언어의 글을 돌려준다"""
    units.append(dict(key=key, kind=kind, ko=ko_html))
    if lang == 'ko' or EXPORT: return ko_html
    if key not in TR: raise SystemExit(f'번역 없음: {key} ← {ko_html[:60]}')
    return TR[key]

# ---------- 원형 숫자 (고정프롬프트 7절: 원과 숫자를 한 SVG에, 좌표는 글꼴 글리프 잉크 경계로)
FONT = f'{HERE}/assets/fonts_ja/PretendardJP-Bold.ttf' if lang == 'ja' else f'{HERE}/assets/fonts/Pretendard-700.ttf'
_tt = TTFont(FONT); _upm = _tt['head'].unitsPerEm; _gs = _tt.getGlyphSet(); _cmap = _tt.getBestCmap(); _hmtx = _tt['hmtx']
def _ink(s):
    x = 0; xs = []; ys = []
    for ch in s:
        g = _cmap[ord(ch)]; bp = BoundsPen(_gs); _gs[g].draw(bp); b = bp.bounds; adv = _hmtx[g][0]
        if b: xs += [x + b[0], x + b[2]]; ys += [b[1], b[3]]
        x += adv
    return (min(xs) + max(xs)) / 2 / _upm, x / 2 / _upm, (min(ys) + max(ys)) / 2 / _upm
def _xy(dia, fs, s):
    ic, ac, yc = _ink(s)
    return dia / 2 - (ic - ac) * fs, dia / 2 + yc * fs
BLUE, GRAY = '#3C55EB', '#64748B'
def circle(kind, n, where):
    """kind: set/res/ref · where: legend(14) / mk(22, 그림 위) / item(23) / res(22, 결과 설명)"""
    dia, fs = {'legend': (14, 10), 'mk': (22, 12), 'item': (23, 12), 'res': (22, 12)}[where]
    c = dia / 2; x, y = _xy(dia, fs, str(n))
    if where == 'mk':
        shapes = f'<circle cx="{c}" cy="{c}" r="{c}" fill="#fff"/>'
        if kind == 'res': shapes += f'<circle cx="{c}" cy="{c}" r="8.25" fill="#fff" stroke="{BLUE}" stroke-width="1.5"/>'
        else: shapes += f'<circle cx="{c}" cy="{c}" r="9" fill="{BLUE if kind == "set" else GRAY}"/>'
    elif where == 'legend':
        if kind == 'res': shapes = f'<circle cx="{c}" cy="{c}" r="6.4" fill="#fff" stroke="{BLUE}" stroke-width="1.2"/>'
        else: shapes = f'<circle cx="{c}" cy="{c}" r="{c}" fill="{BLUE if kind == "set" else GRAY}"/>'
    elif where == 'res':
        shapes = f'<circle cx="{c}" cy="{c}" r="10.5" fill="#fff" stroke="{BLUE}" stroke-width="1"/>'
    else:
        shapes = f'<circle cx="{c}" cy="{c}" r="{c}" fill="{BLUE if kind == "set" else GRAY}"/>'
    fill = BLUE if kind == 'res' else '#fff'
    return (f'<svg class="cn" width="{dia}" height="{dia}" viewBox="0 0 {dia} {dia}" aria-hidden="false">{shapes}'
            f'<text x="{x:.3f}" y="{y:.3f}" font-size="{fs:g}" text-anchor="middle" fill="{fill}" text-rendering="geometricPrecision" transform="rotate(0.2 {c} {c})">{n}</text></svg>')

# ---------- 글(런 목록) → HTML 조각. 글자는 원본 그대로, 줄바꿈 자리는 joins.json 판정대로 띄우거나 붙인다
REF = re.compile(r'\s*\((\d+\.\d+(?:\s*·\s*\d+\.\d+)*|\d+장)(\s*참조)?\)')
def R(runs, key):
    chars = []   # (글자, 모양) 모양: n 보통 · b 굵게 · c 코드
    k = 0
    for r in runs:
        if 'icon' in r: chars.append((r['icon'], 'n')); continue
        if 'badge' in r:
            chars.append((('\0badge', r['badge'], r['n']), 'x')); continue
        st = 'c' if r.get('code') else 'b' if r.get('b') else 'n'
        for ch in r['t']:
            if ch == '⁣':
                dec = joins.get(f'{key}b{k}', 'space'); k += 1
                if dec == 'space': chars.append((' ', st))
                continue
            chars.append((ch, st))
    while chars and chars[0][0] == ' ': chars.pop(0)
    while chars and chars[-1][0] == ' ': chars.pop()
    TAG = {'c': '<code>{}</code>', 'b': '<b>{}</b>', 'n': '{}'}
    out, i = '', 0
    while i < len(chars):
        if chars[i][1] == 'x':
            _, kind, n = chars[i][0]; out += f'<span class="lcir l-{kind} inl">{circle(kind, n, "legend")}</span>'; i += 1; continue
        st, j = chars[i][1], i
        while j < len(chars) and chars[j][1] == st: j += 1
        seg = esc(''.join(c for c, _ in chars[i:j]))
        if st != 'c':
            seg = REF.sub(lambda mm: ' <span class="ref">' + mm.group(1).replace(' ', '') .replace('·', ' · ') + (mm.group(2) or '' if KEEP_REF_WORD else '') + '</span>', seg)
        out += TAG[st].format(seg); i = j
    return out.replace('  ', ' ')

def runs_key(no, si, ii): return f'p{no}s{si}i{ii}'

# ---------- 화면 이미지: 원본 캡처를 잘라 2배 확대(Lanczos + 약한 선명화)해 300dpi 기준을 맞춘다
os.makedirs(f'{OUT}/img', exist_ok=True); os.makedirs(f'{OUT}/fonts', exist_ok=True)
# 번역본 캡처(img/<lang>/, template/img_localize.py 결과)가 있으면 그 파일을 쓰고 덩어리 기록을 품질 기록에 합친다
LOCI = f'{V}/img/{lang}'
LOC_REP = json.load(open(f'{LOCI}/replacements.json'))['files'] if lang != 'ko' and os.path.exists(f'{LOCI}/replacements.json') else None
manifest = dict(document=f'SMART-EDC_사용자매뉴얼_{vol}_{lang}.html', source=m['src'], lang=lang,
                localized_text=(lang == 'ko' or LOC_REP is not None),
                note='' if lang == 'ko' else ('한국어 캡처의 글자 자리만 번역어로 바꿈(template/img_localize.py). 덩어리별 기록은 files[*].segments' if LOC_REP is not None else '한국어 캡처를 그대로 씀 — 이미지 안 글자 현지화는 아직 하지 않았다 [확인 필요]'),
                method='PIL Lanczos ×2 + UnsharpMask(r=1.0, 35%, t=3)' + ('; 글자 교체는 확대본에서' if LOC_REP is not None else ''), files={})
K = 650 / 532.5   # 원본 본문 폭(532.5pt) → 본문 영역 폭(650px)
def place_figs(figs, secno):
    """같은 줄(세로로 겹침)에 있는 그림은 나란히, 아니면 위아래로. 돌려주는 값: [[(fig, width_px, aspect, name)...] ...]"""
    rows = []
    for g in figs:
        for row in rows:
            if any(not (g['fy1'] <= h['fy0'] or g['fy0'] >= h['fy1']) for h in row): row.append(g); break
        else: rows.append([g])
    out = []
    for row in rows:
        row.sort(key=lambda g: g['fx0'])
        ws = [min(560, 400 * g['w'] / g['h'], g['w'] * K) for g in row]
        avail = 650 - 16 * (len(row) - 1)
        if sum(ws) > avail: ws = [w * avail / sum(ws) for w in ws]
        out.append([(g, w) for g, w in zip(row, ws)])
    return out

def process_image(g, name, width_px):
    src = f'{V}/img/orig/{g["img"]}'
    im = Image.open(src).convert('RGB')
    iw, ih = im.size
    x0 = max(0, round(-g['ix'] / g['iwp'] * iw)); x1 = min(iw, round((100 - g['ix']) / g['iwp'] * iw))
    y0 = max(0, round(-g['iy'] / g['ihp'] * ih)); y1 = min(ih, round((100 - g['iy']) / g['ihp'] * ih))
    crop = im.crop((x0, y0, x1, y1))
    scale = 2
    big = crop.resize((crop.width * scale, crop.height * scale), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.0, percent=35, threshold=3))
    loc = None
    if LOC_REP is not None and name in LOC_REP and os.path.exists(f'{LOCI}/{name}'):
        lim = Image.open(f'{LOCI}/{name}').convert('RGB')
        if lim.size != big.size: sys.exit(f'번역 캡처 크기가 한국어판과 다름: {name} {lim.size} != {big.size}')
        big = lim; loc = LOC_REP[name]
    big.save(f'{OUT}/img/{name}', optimize=True)
    disp_h = width_px * g['h'] / g['w']
    mm = [width_px / 96 * 25.4, disp_h / 96 * 25.4]
    req = [int(-(-mm[0] // 25.4 * 300)), int(-(-mm[1] // 25.4 * 300))]
    manifest['files'][name] = dict(name=name, source_xref_image=g['img'], source_px=[iw, ih], crop_box_px=[x0, y0, x1, y1], crop_px=[crop.width, crop.height],
                                  output_px=[big.width, big.height], scale=scale, scale_from_orig=float(scale), method='PIL Lanczos + UnsharpMask(r=1.0, 35%, t=3)',
                                  localized=loc is not None, replaced=(loc or {}).get('replaced', 0), segments=(loc or {}).get('segments', []), flags=(loc or {}).get('flags', []),
                                  placed_css_px=[round(width_px, 1), round(disp_h, 1)], placed_mm=[round(v, 2) for v in mm], required_px_300dpi=req,
                                  effective_dpi=round(big.width / (mm[0] / 25.4), 1), meets_300dpi_pixels=big.width >= req[0] and big.height >= req[1])

# ---------- 쪽(절) 단위 마크업
CHEV = '<svg class="chev" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg>'
def tab(label): return f'<div class="blk tab kwn"><h3><span>{label}</span></h3></div>'
TONE = {'#b91c1c': 'must', '#1d4ed8': 'misc', '#1a1a1a': 'note'}
def cards(items, key_prefix):
    groups = {'must': [], 'misc': [], 'note': []}
    for ii, it in enumerate(items):
        groups[TONE.get(it.get('color'), 'note')].append(U(f'{key_prefix}i{ii}', 'notice', R(it['runs'], f'{key_prefix}i{ii}')))
    o = ''
    for cls, lis in groups.items():
        if not lis: continue
        if cls == 'must': h = f'<h4><span class="ttl">{FX("필수 확인")} </span><span class="sub">{FX("데이터 손상 · 폼 완료 불가")}</span></h4>'
        elif cls == 'misc': h = f'<h4><span class="ttl">{FX("오해하기 쉬운 동작")}</span></h4>'
        else: h = f'<h4><span class="ttl">{FX("참고")}</span></h4>'
        o += f'<div class="blk card {cls}">{h}<ul>' + ''.join(f'<li><span class="bul">• </span>{x}</li>' for x in lis) + '</ul></div>'
    return o
def plain_list(items, key_prefix):
    lis = [U(f'{key_prefix}i{ii}', 'list', R(it['runs'], f'{key_prefix}i{ii}')) for ii, it in enumerate(items)]
    return '<div class="blk plain"><ul>' + ''.join(f'<li><span class="bul">• </span>{x}</li>' for x in lis) + '</ul></div>'
def table_html(s, key_prefix):
    ths = ''.join(f'<th style="width:{w}%">{U(f"{key_prefix}h{c}", "th", esc(h))}</th>' for c, (h, w) in enumerate(zip(s['head'], s['widths'])))
    rows = ''
    for ri, row in enumerate(s['rows']):
        rows += '<tr>' + ''.join(f'<td class="c{ci}">{U(f"{key_prefix}r{ri}c{ci}", "td", R(c, f"{key_prefix}r{ri}c{ci}")) if c else ""}</td>' for ci, c in enumerate(row)) + '</tr>'
    return f'<div class="blk tblwrap"><table><thead><tr>{ths}</tr></thead><tbody>{rows}</tbody></table></div>'

chapters = {c['ch']: c for c in m['toc']}
def split_title(t):
    return t.split(' > ', 1)[-1].strip()

# ---------- 표지 글줄: SMART / EDC / 시스템 설명 / 제목 / 보조 설명 / 매뉴얼 구분 / 날짜(넣지 않는다)
cover = [l for l in m['pages'][0]['lines'] if l.strip() not in ('SMART', 'EDC')]
assert len(cover) == 5 and re.match(r'\d{4}-\d\d-\d\d', cover[4]), cover
COVER_SYS, COVER_TITLE, COVER_SUB, COVER_KIND = [c.strip() for c in cover[:4]]
assert COVER_KIND == '사용자 매뉴얼 · 화면별 분권', COVER_KIND

secs_html = ''
seen_ch = set(); seen_sid = {}
for pg in m['pages']:
    if pg['kind'] != 'body': continue
    no = pg['title'].split(' ', 1)[0]; ch = no.split('.')[0]
    sec_title = U(f'p{pg["no"]}.title', 'h2', esc(split_title(pg['title'])))   # 쪽 머리 제목(같은 절 번호가 두 쪽이면 ①·② 제목이 다르다)
    ch_title = U(f'ch{ch}.title', 'h1', esc(chapters[ch]['title']))
    chtitle_attr = f'{ch}. {plain(ch_title)}'
    if ch not in seen_ch:
        seen_ch.add(ch); c = chapters[ch]
        lis = ''.join(f'<li><span class="dn">{i["no"]}</span><span class="dt">{U(f"sec{i['no']}.title", "h2", esc(split_title(i["title"])))}</span></li>' for i in c['items'])
        secs_html += (f'<section class="divider" data-ch="{ch}" data-chtitle="{esc(chtitle_attr)}">\n<div class="dlabel">{FX("화면별 분권")} — {U("cover.title", "cover", esc(COVER_TITLE))}</div>\n'
                      f'<div class="dhead"><div class="dnum">{ch}</div><h1 class="dtitle" id="ch{ch}">{ch_title}</h1></div>\n<ul class="dlist">{lis}</ul></section>')
    sid = 's' + no.replace('.', '-')
    seen_sid[sid] = seen_sid.get(sid, 0) + 1
    if seen_sid[sid] > 1: sid += 'abcdefg'[seen_sid[sid] - 1]   # 같은 절 번호가 여러 쪽이면 두 번째부터 id 뒤에 글자를 붙인다(목차는 첫 쪽으로)
    body = ''
    # 경로: 「1. 경로 : A > B > C」 → 라벨 + 항목 (마지막 항목도 같은 색·굵기, 고정프롬프트 6절)
    if pg.get('path'):
        raw = ''.join(x['t'] for x in pg['path'])
        crumbs = [c.strip() for c in raw.split(':', 1)[1].split('>')]
        pis = [U(f'p{pg["no"]}.path.{i}', 'path', esc(c)) for i, c in enumerate(crumbs)]
        body += f'<div class="blk path kwn"><span class="lbl">{FX("경로")} </span>' + CHEV.join(f'<span class="pi">{x}</span>' for x in pis) + '</div>\n'
    figs = next((s['figs'] for s in pg['sections'] if s['kind'] == 'figs'), [])
    for si, s in enumerate(pg['sections']):
        if s['kind'] == 'figs': continue
        kp = f'p{pg["no"]}s{si}'
        if s['kind'] == 'table':
            body += tab(U(f'{kp}.name', 'h3', esc(s['name']))) + '\n' + table_html(s, kp) + '\n'; continue
        if s['name'] == '개요':
            body += tab(FX('개요')) + '\n' + ''.join(f'<div class="blk ov"><p>{U(f"{kp}i{ii}", "overview", R(it["runs"], f"{kp}i{ii}"))}</p></div>\n' for ii, it in enumerate(s['items'])); continue
        if s['name'] == '화면 설명':
            body += tab(FX('화면 설명')) + '\n'
            body += (f'<div class="blk legend kwn"><div class="lg"><span class="lcir l-set">{circle("set", 1, "legend")}</span><b>{FX("설정")} </b><span>{FX("직접 조작하는 위치")}</span></div>'
                     f'<div class="lg"><span class="lcir l-res">{circle("res", 1, "legend")}</span><b>{FX("결과")} </b><span>{FX("바로 위 설정으로 바뀌는 위치")}</span></div>'
                     f'<div class="lg note"><span class="lcir l-ref">{circle("ref", 1, "legend")}</span><b>{FX("참고")}</b></div></div>\n')
            n_img = 0
            for ri, row in enumerate(place_figs(figs, no)):
                shots = ''
                for g, wpx in row:
                    n_img += 1; name = f'{sid.replace("-", "_")}_{n_img}.png'
                    process_image(g, name, wpx)
                    aspect = g['w'] / g['h']
                    mks = ''.join(f'<span class="mk mk-{b["kind"]}" style="margin-left:calc({b["x"]:.3f}% - 11px);margin-top:calc({b["y"] / aspect:.3f}% - 11px)">{circle(b["kind"], b["n"], "mk")}</span>'
                                  for b in g['badges'] if b['n'] is not None)
                    cap = U(f'p{pg["no"]}.cap.{n_img}', 'caption', R(g['cap'], f'p{pg["no"]}cap{n_img}')) if g['cap'] else ''
                    shots += (f'<div class="shot" style="width:{wpx:.1f}px"><div class="imgbox" style="aspect-ratio:{aspect:.5f}"><img src="img/{name}" alt="">{mks}</div>'
                              + (f'<figcaption>{cap}</figcaption>' if cap else '') + '</div>')
                body += f'<div class="blk fig{" kwn" if ri == 0 else ""}{" two" if len(row) > 1 else ""}">{shots}</div>\n'
            # 번호 설명: 설정·참고는 바깥 항목, 결과(└)는 바로 앞 항목 안에 붙인다
            cur = None
            for ii, it in enumerate(s['items']):
                t = U(f'{kp}i{ii}', 'desc', R(it['runs'], f'{kp}i{ii}'))
                kind = it.get('badge', 'set'); n = it.get('n', '')
                if it.get('level') == 1 and kind == 'res' and cur is not None:
                    cur['res'].append(f'<div class="res"><span class="cir c-res">{circle("res", n, "res")}</span><p class="t">{t}</p></div>')
                    continue
                if cur: body += cur['html'].format(ress=f'<div class="ress">{"".join(cur["res"])}</div>' if cur['res'] else '') + '\n'
                cur = dict(res=[], html=f'<div class="blk item k-{kind}"><span class="cir c-{kind}">{circle(kind, n, "res" if kind == "res" else "item")}</span><div class="body"><p class="t">{t.replace("{", "{{").replace("}", "}}")}</p>{{ress}}</div></div>')
            if cur: body += cur['html'].format(ress=f'<div class="ress">{"".join(cur["res"])}</div>' if cur['res'] else '') + '\n'
            continue
        # 유의사항 · 그 밖의 글머리 목록: 색이 있는 항목은 카드로, 검은 점만 있는 목록은 일반 목록으로
        if s['name'] == '이 화면으로 가는 다른 길': label = FX('접근 경로')   # 원본 목록 제목을 고정 표기로 바꾼다 (hy0909 결정, 2026-10-30)
        elif s['name'] == '유의사항': label = FX('유의사항')
        else: label = U(f'{kp}.name', 'h3', esc(s['name']))
        colored = s['name'] == '유의사항' or any(it.get('color') in ('#b91c1c', '#1d4ed8') for it in s['items'])
        body += tab(label) + '\n' + (cards(s['items'], kp) if colored else plain_list(s['items'], kp)) + '\n'
    hdr = f'<template class="hdr-tpl"><h2 class="ht"><span class="hn">{no}</span><span class="hx">{sec_title}</span></h2></template>'
    secs_html += f'<section class="sec" id="{sid}" data-num="{no}" data-chtitle="{esc(chtitle_attr)}">\n{hdr}\n<div class="flow">{body}</div></section>\n'

# ---------- 표지 · 목차 · 문서 조립
doc_title = U('doc.title', 'title', esc(f'SMART-EDC 사용자 매뉴얼 — {COVER_TITLE}')) if lang == 'ko' or EXPORT else f'{FX("SMART-EDC 사용자 매뉴얼")} — {plain(TR["cover.title"])}'
cover_html = (f'<section class="cover">\n  <div class="cv-wave"></div><div class="cv-grad"></div>\n'
              f'  <div class="cv-top"><img class="cv-brand" src="img/smart-edc-logo.png" alt="SMART EDC"><span class="cv-sys">{FX("임상시험 전자자료수집 시스템")}</span></div>\n'
              f'  <div class="cv-main noclass"><h1 class="cv-title">{U("cover.title", "cover", esc(COVER_TITLE))}</h1><p class="cv-sub">{U("cover.sub", "cover", esc(COVER_SUB))}</p></div>\n'
              f'  <div class="cv-bottom"><span class="cv-kind">{FX("사용자 매뉴얼 · 화면별 분권")}</span><img class="cv-logo" src="img/logo.png" alt="DH Digital Healthcare Software"></div>\n</section>')
toc_html = ''.join(
    f'<div class="tch blk"><div class="tchh"><span class="tcn">{c["ch"]}</span><span class="tct">{U(f"ch{c['ch']}.title", "h1", esc(c["title"]))}</span></div><ul>'
    + ''.join(f'<li><a href="#s{i["no"].replace(".", "-")}"><span class="tn">{i["no"]}</span><span class="tt">{U(f"sec{i['no']}.title", "h2", esc(split_title(i["title"])))}</span><span class="tp" data-for="s{i["no"].replace(".", "-")}"></span></a></li>' for i in c['items'])
    + '</ul></div>' for c in m['toc'])

if EXPORT:
    seen = {}
    for u in units: seen.setdefault(u['key'], u)
    json.dump(list(seen.values()), open(f'{D}/units_ko.json', 'w'), ensure_ascii=False, indent=1)
    print('units', len(seen)); sys.exit()

css = open(f'{HERE}/style.css').read(); js = open(f'{HERE}/paginate.js').read()
html_doc = ('<!doctype html>\n'
            f'<html lang="{lang}"><head><meta charset="utf-8"><title>{plain(doc_title)}</title>\n\n'
            f'<style>{css}</style></head>\n<body class="lang-{lang}">\n<div id="src" hidden>\n{cover_html}\n'
            f'<section class="toc" data-title="{FX("목차")}"><div class="flow">{toc_html}</div></section>\n'
            f'{secs_html}</div>\n<div id="book"></div>\n<script>{js}</script>\n</body></html>\n')
open(f'{OUT}/SMART-EDC_사용자매뉴얼_{vol}_{lang}.html', 'w').write(html_doc)
fonts = f'{HERE}/assets/fonts_ja' if lang == 'ja' else f'{HERE}/assets/fonts'
for fn in os.listdir(fonts): shutil.copy(f'{fonts}/{fn}', f'{OUT}/fonts/{fn}')
for fn in ('wave.jpg', 'logo.png', 'smart-edc-logo.png', 'smart-edc-logo-gray.png', 'smart-edc-logo-footer.png'): shutil.copy(f'{HERE}/assets/img/{fn}', f'{OUT}/img/{fn}')
json.dump(manifest, open(f'{OUT}/img/quality-manifest.json', 'w'), ensure_ascii=False, indent=1)
print('html', f'{OUT}/SMART-EDC_사용자매뉴얼_{vol}_{lang}.html', 'images', len(manifest['files']), 'units', len({u['key'] for u in units}))
