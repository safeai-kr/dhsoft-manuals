# SMART EDC 매뉴얼 원본 PDF를 구조 데이터(JSON)로 읽어 낸다. 원본 PDF가 HTML→크롬 PDF라서 글자 색·굵기·위치로 구조를 되살린다.
# 사용: python3 parse.py 원본.pdf 분권폴더   → 분권폴더/data/model.json, 분권폴더/img/orig/*.png
# 글자는 원본 그대로 둔다. 줄이 바뀐 자리는 U+2063으로 표시하고 띄어쓰기 여부는 data/joins.json 판정(build.py)으로 정한다.
import sys, json, os, re
import pymupdf as f
from PIL import Image, ImageChops

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(f'{OUT}/img/orig', exist_ok=True); os.makedirs(f'{OUT}/data', exist_ok=True)
d = f.open(SRC)
FL = f.TEXTFLAGS_DICT & ~f.TEXT_MEDIABOX_CLIP

def hexc(c): return '#%06x' % c
def near(a, b, t): return abs(a - b) <= t

BADGE = {(0.863, 0.149, 0.149): 'set', (0.114, 0.306, 0.847): 'res', (0.392, 0.455, 0.545): 'ref'}
RED, BLUE, DBLUE, GRAY, BLACK = '#b91c1c', '#1d4ed8', '#1e3a8a', '#64748b', '#1a1a1a'

def spans_of(p):
    out = []
    for bl in p.get_text('dict', flags=FL)['blocks']:
        for l in bl.get('lines', []):
            for s in l['spans']:
                if not s['text']: continue
                fn = s['font']
                out.append(dict(t=s['text'], x0=s['bbox'][0], y0=s['bbox'][1], x1=s['bbox'][2], y1=s['bbox'][3],
                                oy=s['origin'][1], size=round(s['size'], 1), color=hexc(s['color']), font=fn,
                                bold='Bold' in fn))
    return out

def badges_of(p):
    """색 원(배지)과 3pt 점(글머리)을 찾는다"""
    bs, dots = [], []
    for dr in p.get_drawings():
        r = dr['rect']; fill = dr.get('fill')
        if fill is None: continue
        key = tuple(round(c, 3) for c in fill)
        if 9 <= r.width <= 15 and 9 <= r.height <= 15 and key in BADGE:
            cx, cy = (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2
            if any(near(b['cx'], cx, 2) and near(b['cy'], cy, 2) for b in bs): continue
            bs.append(dict(kind=BADGE[key], cx=cx, cy=cy, r=[r.x0, r.y0, r.x1, r.y1], n=None))
        elif 2 <= r.width <= 4 and 2 <= r.height <= 4:
            dots.append(dict(cx=(r.x0 + r.x1) / 2, cy=(r.y0 + r.y1) / 2, color='#%02x%02x%02x' % tuple(int(c * 255 + .5) for c in fill)))
    return bs, dots

def attach_digits(spans, bs):
    rest = []
    for s in spans:
        if s['color'] == '#ffffff' and s['size'] <= 7 and s['t'].strip().isdigit():
            cx, cy = (s['x0'] + s['x1']) / 2, (s['y0'] + s['y1']) / 2
            hit = [b for b in bs if b['r'][0] - 1 <= cx <= b['r'][2] + 1 and b['r'][1] - 2 <= cy <= b['r'][3] + 2]
            if hit: hit[0]['n'] = int(s['t']); continue
        rest.append(s)
    return rest

def group_lines(spans, tol=3.2):
    """기준선(origin y)이 가까운 글자 조각을 한 줄로 묶는다"""
    lines = []
    for s in sorted(spans, key=lambda s: (s['oy'], s['x0'])):
        for L in lines:
            if near(L['oy'], s['oy'], tol): L['sp'].append(s); break
        else: lines.append(dict(oy=s['oy'], sp=[s]))
    for L in lines:
        L['sp'].sort(key=lambda s: s['x0']); L['x0'] = L['sp'][0]['x0']
        L['y0'] = min(s['y0'] for s in L['sp']); L['y1'] = max(s['y1'] for s in L['sp'])
    return sorted(lines, key=lambda L: L['oy'])

def is_code(s):
    f_ = s['font']
    return s['size'] in (8.0,) and ('Consolas' in f_ or 'GulimChe' in f_ or 'pe3' in f_ or '(' in f_)

def runs_of(tokens):
    """글자 조각과 배지를 인라인 런 목록으로. 같은 모양끼리 붙인다"""
    out = []
    for k in tokens:
        if 'kind' in k:
            out.append(dict(badge=k['kind'], n=k['n'])); continue
        t = k['t']
        if t in ('⚠', '⛔', 'ⓘ', '💡'):
            out.append(dict(icon=t)); continue
        c = k['color']
        tone = 'danger' if c == RED else 'warn' if c == BLUE else 'res' if c == DBLUE else 'mute' if c == GRAY else None
        r = dict(t=t, b=k['bold'], code=is_code(k), tone=tone)
        if out and 't' in out[-1] and all(out[-1].get(x) == r[x] for x in ('b', 'code', 'tone')):
            out[-1]['t'] += t
        else: out.append(r)
    for r in out:
        if 't' in r and r['code']: r['t'] = r['t'].strip()
    # 코드 조각 사이 빈칸 정리: 'fieldKey' 앞뒤 ' ' 런이 따로 있던 것을 합친다
    return [r for r in out if not ('t' in r and r['t'] == '' )]

def line_tokens(L, bs):
    toks = list(L['sp'])
    for b in bs:
        if L['y0'] - 3 <= b['cy'] <= L['y1'] + 3 and b['cx'] > L['x0'] + 4:
            toks.append(dict(kind=b['kind'], n=b['n'], x0=b['r'][0]))
    return sorted(toks, key=lambda k: k['x0'])

def parse_figure_area(p, spans, bs, y0, y1, pi):
    """가. 메인화면: 이미지(잘린 영역), 배지 상대 위치, 캡션"""
    figs = []
    infos = [i for i in p.get_image_info(xrefs=True) if i['xref']]
    frames = []
    for dr in p.get_drawings():
        r = dr['rect']; c = dr.get('color')
        if c and tuple(round(x, 2) for x in c) == (0.8, 0.84, 0.88) and r.width > 60 and r.height > 15 and y0 - 4 <= r.y0 <= y1:
            frames.append([r.x0, r.y0, r.x1, r.y1])
    frames.sort(key=lambda r: (r[1], r[0]))
    pairs = []
    for fr in frames:
        def ov(i):
            b = i['bbox']; return max(0, min(b[2], fr[2]) - max(b[0], fr[0])) * max(0, min(b[3], fr[3]) - max(b[1], fr[1]))
        area = (fr[2] - fr[0]) * (fr[3] - fr[1])
        cands = [i for i in infos if ov(i) > area * 0.5]
        if len(cands) > 1:
            # 큰 이미지 여러 장이 같은 자리에 겹쳐 놓여(잘라 보임) 겹침 넓이로는 못 고른다. 실제로 보이는 모습(쪽 렌더링)과 가장 비슷한 이미지를 고른다
            clip = f.Rect(*fr); ren = p.get_pixmap(clip=clip, dpi=72)
            ren = Image.frombytes('RGB', (ren.width, ren.height), ren.samples)
            best = None
            for i in cands:
                pix = f.Pixmap(d, i['xref'])
                if pix.n - pix.alpha > 3: pix = f.Pixmap(f.csRGB, pix)
                im = Image.frombytes('RGB' if pix.n == 3 else 'RGBA', (pix.width, pix.height), pix.samples).convert('RGB')
                b = i['bbox']; sx = pix.width / (b[2] - b[0]); sy = pix.height / (b[3] - b[1])
                box = [(fr[0] - b[0]) * sx, (fr[1] - b[1]) * sy, (fr[2] - b[0]) * sx, (fr[3] - b[1]) * sy]
                crop = im.crop(tuple(int(round(v)) for v in box)).resize(ren.size)
                diff = ImageChops.difference(crop, ren).convert('L')
                score = sum(diff.histogram()[k] * k for k in range(256)) / (ren.width * ren.height)
                if best is None or score < best[0]: best = (score, i)
            info = best[1]
        else:
            info = max(infos, key=ov)
        b = info['bbox']
        cb = [max(b[0], fr[0]), max(b[1], fr[1]), min(b[2], fr[2]), min(b[3], fr[3])]
        pairs.append((cb, info, fr))
    for i, (cb, info, fr0) in enumerate(pairs):
        x = info['xref']; fb = info['bbox']
        pix = f.Pixmap(d, x)
        if pix.n - pix.alpha > 3: pix = f.Pixmap(f.csRGB, pix)
        name = f'p{pi:02d}_{i+1}.png'; pix.save(f'{OUT}/img/orig/{name}')
        cw, ch = cb[2] - cb[0], cb[3] - cb[1]
        fig = dict(img=name, iw=pix.width, ih=pix.height, w=cw, h=ch,
                   # 이미지 전체를 잘린 영역 기준 백분율로
                   ix=(fb[0] - cb[0]) / cw * 100, iy=(fb[1] - cb[1]) / ch * 100,
                   iwp=(fb[2] - fb[0]) / cw * 100, ihp=(fb[3] - fb[1]) / ch * 100, badges=[], cap=[])
        fig['frame'] = fr0; fig['cb'] = cb
        figs.append(fig)
    # 캡션: 그림 테두리 아래에 있는 줄. 줄 안의 배지는 캡션 글자 속 배지로 둔다
    caplines = [L for L in group_lines([s for s in spans if y0 <= s['y0'] <= y1 + 4])
                if any(L['y0'] >= g['frame'][3] - 2 for g in figs)]
    def inside(L, g):
        fr = g['frame']; return fr[1] < (L['y0'] + L['y1']) / 2 < fr[3] - 2 and fr[0] < (L['sp'][0]['x0'] + L['sp'][-1]['x1']) / 2 < fr[2]
    caplines = [dict(L, sp=[x for x in L['sp'] if not any(g['frame'][0] < (x['x0'] + x['x1']) / 2 < g['frame'][2] and g['frame'][1] < (x['y0'] + x['y1']) / 2 < g['frame'][3] - 2 for g in figs)]) for L in caplines]
    caplines = [L for L in caplines if L['sp']]
    for L in caplines:
        for b in bs:
            if L['y0'] - 3 <= b['cy'] <= L['y1'] + 3: b['incap'] = True
    for g in figs:
        fr = g['frame']; cb = g['cb']
        for b in bs:
            if b.get('incap'): continue
            if fr[0] - 8 <= b['cx'] <= fr[2] + 8 and fr[1] - 8 <= b['cy'] <= fr[3] + 8:
                b['used'] = True
                g['badges'].append(dict(kind=b['kind'], n=b['n'], x=(b['cx'] - cb[0]) / g['w'] * 100, y=(b['cy'] - cb[1]) / g['h'] * 100))
    for L in caplines:
        for g in figs:
            sp = [s for s in L['sp'] if g['frame'][0] - 30 <= (s['x0'] + s['x1']) / 2 <= g['frame'][2] + 30]
            if not sp: continue
            # 같은 가로 범위에 그림이 위아래로 여러 개면, 캡션 바로 위에 있는 그림에만 붙인다
            above = [h for h in figs if h['frame'][3] - 2 <= L['y0'] and h['frame'][0] - 30 <= (sp[0]['x0'] + sp[-1]['x1']) / 2 <= h['frame'][2] + 30]
            if above and max(above, key=lambda h: h['frame'][3]) is not g: continue
            sub = dict(L, sp=sp, x0=sp[0]['x0'] - 1)
            bsub = [b for b in bs if b.get('incap') and g['frame'][0] - 30 <= b['cx'] <= g['frame'][2] + 30 and L['y0'] - 3 <= b['cy'] <= L['y1'] + 3]
            for b in bsub: b['used'] = True
            toks = line_tokens(sub, bsub)
            if g['cap']: g['cap'].append(dict(t=' ', b=False, code=False, tone='mute'))
            g['cap'] += runs_of(toks)
    for g in figs:
        fr = g.pop('frame'); g.pop('cb'); g['fx0'], g['fy0'], g['fy1'] = fr[0], fr[1], fr[3]   # 쪽 안 위치(나란히/위아래 배치 판단용)
    return figs

def parse_list(lines, bs, dots, mode):
    """개요·유의사항: 글머리 점 기준 / 화면 설명: 배지 기준"""
    items = []
    for L in lines:
        lead = None
        L = dict(L, sp=[s for s in L['sp'] if s['t'].strip() != '└'] or L['sp'], sub=any(s['t'].strip() == '└' for s in L['sp']))
        L['x0'] = L['sp'][0]['x0']
        if mode == 'bul':
            dot = next((dt for dt in dots if near(dt['cy'], (L['y0'] + L['y1']) / 2, 5) and dt['cx'] < L['x0']), None)
            if dot: lead = dict(level=0, color=dot['color'])
        else:
            b = next((b for b in bs if not b.get('used') and L['y0'] - 4 <= b['cy'] <= L['y1'] + 4 and b['cx'] < L['x0']), None)
            if b:
                b['used'] = True
                sub = L['sub'] or b['cx'] > 50
                lead = dict(level=1 if sub else 0, badge=b['kind'], n=b['n'])
        sp = [s for s in L['sp'] if s['t'].strip() != '└']
        toks = line_tokens(dict(L, sp=sp), [b for b in bs if not b.get('used')])
        if lead or not items:
            items.append(dict(lead or dict(level=0), toks=toks))
        else:
            # 줄바꿈 자리 표시. 띄어쓰기 여부는 joins.json 판정으로 정한다
            if toks and 't' in toks[0]: toks[0] = dict(toks[0], t='\u2063' + toks[0]['t'])
            items[-1]['toks'] += toks
    for it in items: it['runs'] = runs_of(it.pop('toks'))
    return items

def table_geometry(p, y0, y1):
    """표 머리 채움(#eff6ff) 사각형 → 열 경계, 얇은 가로줄 → 행 경계"""
    heads, rules = [], []
    for dr in p.get_drawings():
        r = dr['rect']; fl = dr.get('fill')
        if fl is None or not (y0 - 4 <= r.y0 <= y1 + 10): continue
        c = '#%02x%02x%02x' % tuple(int(x * 255 + .5) for x in fl)
        if c == '#eff6ff' and r.height > 8: heads.append(r)
        elif r.height < 1.5 and r.width > 30: rules.append(r)
    if not heads: return None
    cols = sorted((r.x0, r.x1) for r in heads)
    top = min(r.y0 for r in heads)
    ys = sorted({round(r.y0, 1) for r in rules if r.y0 >= top - 1 and cols[0][0] - 2 <= r.x0 <= cols[-1][1] + 2})
    # 같은 줄의 조각을 하나로
    rows = []
    for y in ys:
        if not rows or y - rows[-1] > 2: rows.append(y)
    return dict(cols=cols, rows=rows)

def parse_table(spans, geo):
    cols, rows = geo['cols'], geo['rows']
    grid = [[[] for _ in cols] for _ in range(len(rows) - 1)]
    for s in spans:
        cy = (s['y0'] + s['y1']) / 2; cx = s['x0'] + 1
        ri = next((i for i in range(len(rows) - 1) if rows[i] <= cy <= rows[i + 1]), None)
        ci = next((j for j, (a, b) in enumerate(cols) if a - 2 <= cx <= b + 2), None)
        if ri is None or ci is None: continue
        grid[ri][ci].append(s)
    def cell(sp):
        if not sp: return []
        lines = group_lines(sp, tol=4)
        toks = []
        for k, L in enumerate(lines):
            t = list(L['sp'])
            if k and t and 't' in t[0]: t[0] = dict(t[0], t='\u2063' + t[0]['t'])
            toks += t
        return runs_of(toks)
    table = [[cell(c) for c in row] for row in grid]
    head = [''.join(r.get('t', '') for r in c).strip() for c in table[0]]
    return dict(head=head, rows=table[1:], widths=[round((b - a) / (cols[-1][1] - cols[0][0]) * 100, 1) for a, b in cols])

# ---- 목차(2쪽): 장(11pt 굵게) · 절(9.5pt, 왼쪽) · 원본 쪽번호(오른쪽 회색)
toc = []
for bl in d[1].get_text('dict', flags=f.TEXT_INHIBIT_SPACES)['blocks']:
    for l in bl.get('lines', []):
        s0 = l['spans'][0]; t = ''.join(s['text'] for s in l['spans']).strip()
        if abs(s0['size'] - 11) < .3 and re.match(r'^\d+\. ', t):
            n, title = t.split('. ', 1); toc.append(dict(ch=n, title=title, items=[]))
        elif abs(s0['size'] - 9.5) < .3 and re.match(r'^\d+\.\d+ ', t) and s0['bbox'][0] < 100:
            no, title = t.split(' ', 1); toc[-1]['items'].append(dict(no=no, title=title))

pages = []
title_doc = d.metadata.get('title', '')
for pi, p in enumerate(d, 1):
    sp = spans_of(p)
    if pi == 1:
        pages.append(dict(kind='cover', lines=[s['t'] for s in sorted(sp, key=lambda s: s['oy'])])); continue
    if pi == 2:
        pages.append(dict(kind='toc')); continue
    bs, dots = badges_of(p)
    sp = attach_digits(sp, bs)
    title = next(s['t'] for s in sp if s['size'] == 12.0)
    body = [s for s in sp if 30 < s['oy'] < 830 and not (s['color'] == '#ffffff' and s['size'] > 7) and s['size'] != 12.0 and not (s['color'] in ('#ffffff', '#7dd3fc') and s['oy'] < 40)]
    heads = [s for s in body if s['size'] == 9.5 and s['bold'] and re.match(r'^[가-힣]\. ', s['t'])]
    pg = dict(kind='body', no=pi, title=title, sections=[])
    pl = next((L for L in group_lines(body) if ''.join(x['t'] for x in L['sp']).startswith('1. 경로')), None)
    path = pl['sp'] if pl else []
    body = [s for s in body if s not in path]
    if path:
        pg['path'] = [dict(t=s['t'], cur=s['color'] == BLUE) for s in path]
    hs = sorted(heads, key=lambda s: s['oy'])
    all_lines = group_lines(body)
    for i, h in enumerate(hs):
        y0, y1 = h['oy'] + 2, (hs[i + 1]['oy'] - 12 if i + 1 < len(hs) else 830)
        hl = next(L for L in all_lines if h in L['sp'])
        name = ''.join(x['t'] for x in hl['sp'])[3:].strip()
        region = [s for s in body if y0 < s['oy'] <= y1 + 10 and s not in hl['sp'] and not s['t'].startswith('2. 화면 설명')]
        geo = table_geometry(p, y0, y1) if name != '메인화면' else None
        if geo:
            pg['sections'].append(dict(kind='table', name=name, **parse_table(region, geo))); continue
        if name == '메인화면':
            legend_y = min((s['oy'] for s in region), default=0)
            figs = parse_figure_area(p, region, bs, y0 + 12, y1 + 10, pi)
            for b in bs:
                if near(b['cy'], legend_y - 2, 6): b['used'] = True
            pg['sections'].append(dict(kind='figs', name=name, figs=figs)); continue
        lines = group_lines(region)
        if lines and '빨간 글씨' in ''.join(s['t'] for s in lines[0]['sp']): lines = lines[1:]
        mode = 'badge' if name == '화면 설명' else 'bul'
        pg['sections'].append(dict(kind='list', mode=mode, name=name, items=parse_list(lines, bs, dots, mode)))
    unused = [b for b in bs if not b.get('used') and b['n'] is not None]
    if unused: pg['unused_badges'] = [dict(kind=b['kind'], n=b['n'], cx=round(b['cx'], 1), cy=round(b['cy'], 1)) for b in unused]
    pages.append(pg)

json.dump(dict(title=title_doc, src=os.path.basename(SRC), toc=toc, pages=pages), open(f'{OUT}/data/model.json', 'w'), ensure_ascii=False, indent=1)
print('pages', len(pages), 'toc', sum(len(c['items']) for c in toc))
