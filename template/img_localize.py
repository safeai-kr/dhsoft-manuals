"""번역본 화면 캡처 만들기: 한국어 글자 자리를 바탕색으로 덮고 번역어를 같은 자리에 다시 그린다 (고정 프롬프트 11절 2순위).

사용: python3 template/img_localize.py <분권> <en|de|ja> [--only s1_1_1.png] [--dump]
입력: manuals/<분권>/ko/img/s*.png (한국어판 2배 확대본, 이 해상도에서 바로 글자를 바꾼다)
      manuals/<분권>/img/loc/segments.json, verified.json
      manuals/<분권>/i18n/image_<lang>.json  ({한국어: 번역어})
출력: manuals/<분권>/img/<lang>/s*.png
      manuals/<분권>/img/<lang>/replacements.json  (덩어리별 원문·번역어·위치·크기·굵기·정렬·축소율·플래그; build.py가 품질 기록에 넣는다)
--dump 는 번역 없이 덩어리(원문 묶음) 목록만 manuals/<분권>/img/loc/strings_ko.json 에 적는다.
"""
import json, sys, os, base64, asyncio, re, argparse
import numpy as np
from PIL import Image
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ap = argparse.ArgumentParser()
ap.add_argument('vol'); ap.add_argument('lang', nargs='?', default='')
ap.add_argument('--only', default=''); ap.add_argument('--dump', action='store_true')
a = ap.parse_args()
V = f'{ROOT}/manuals/{a.vol}'; KO = f'{V}/ko/img'; LOC = f'{V}/img/loc'
segs = {s['id']: s for s in json.load(open(f'{LOC}/segments.json'))}
ver = {v['id']: v for v in json.load(open(f'{LOC}/verified.json'))}
missing_ver = [k for k in segs if k not in ver]
if missing_ver: sys.exit(f'verified.json에 없는 id {len(missing_ver)}개: {missing_ver[:5]}')
lang = a.lang
OUT = f'{V}/img/{lang}' if lang else ''
if lang and not a.dump:
    os.makedirs(OUT, exist_ok=True)
    tr = json.load(open(f'{V}/i18n/image_{lang}.json'))
else:
    tr = None

_imcache = {}
def im_of(f):
    if f not in _imcache:
        _imcache.clear(); _imcache[f] = np.asarray(Image.open(f'{KO}/{f}').convert('RGB')).astype(int)
    return _imcache[f]

def ink_rows(s, x0, x1):
    im = im_of(s['file']); h = s['line_h']
    ya = max(0, int(s['y0'] - 0.08 * h)); yb = min(im.shape[0], int(s['y1'] + 0.08 * h))
    ink = np.abs(im[ya:yb, x0:x1] - np.array(s['bg'])).max(2) > 40
    # 글자 바로 아래·위의 입력칸 테두리 같은 가로줄(글자 오른쪽 바깥까지 이어진 잉크)은 글자 줄에서 뺀다
    xr0, xr1 = x1 + 2, min(im.shape[1], x1 + 2 + int(h))
    beyond = (np.abs(im[ya:yb, xr0:xr1] - np.array(s['bg'])).max(2) > 40).mean(1) if xr1 > xr0 else np.zeros(yb - ya)
    rule = (beyond > 0.8) & (ink.mean(1) > 0.8)
    rows = np.where(ink.any(1) & ~rule)[0]
    if not len(rows): return s['y0'], s['y1']
    return int(ya + rows.min()), int(ya + rows.max() + 1)

# ---------- 작업 묶음: 한 덩어리, 또는 join_next 로 이어진 문단
jobs = {}; done = set(); dump = []
order = list(segs)
heads = set(order) - {ver[k].get('join_next') for k in order if ver[k].get('join_next')}
for sid in order:
    v = ver[sid]
    if v.get('skip') or sid in done or sid not in heads: continue
    chain = [sid]
    while ver[chain[-1]].get('join_next') and ver[chain[-1]]['join_next'] in ver and ver[chain[-1]]['join_next'] not in chain:
        chain.append(ver[chain[-1]]['join_next'])
    done.update(chain)
    lines = []
    for cid in chain:
        s, cv = segs[cid], ver[cid]
        if cv.get('skip'): continue
        words = s['words']
        x0, x1 = words[0][0], words[-1][1]
        # 아이콘이 앞에 붙은 덩어리: 첫 낱말이 좁으면(글자 높이 1.5배 미만) 그 다음부터
        if cv.get('icon_lead') and len(words) > 1 and (words[0][1] - words[0][0]) < 1.5 * s['line_h']:
            x0 = words[1][0]
        y0r, y1r = ink_rows(s, x0, x1)
        lines.append({'id': cid, 'x0': int(x0), 'x1': int(x1), 'y0': y0r, 'y1': y1r, 'ko': cv['ko'].strip(), 'bg': s['bg'], 'fg': s['fg'], 'h': s['line_h']})
    if not lines: continue
    ko = ' '.join(l['ko'] for l in lines if l['ko'])
    if not ko: continue
    rec = {'id': sid, 'ko': ko, 'role': v.get('role', ''), 'lines': len(lines), 'truncated': bool(v.get('truncated'))}
    dump.append(rec)
    if tr is None: continue
    t = tr.get(f"{ko}@{v.get('role', '')}", tr.get(ko))   # 같은 한국어가 역할에 따라 다르게 번역되면 '원문@역할' 키를 먼저 본다
    if t is None:
        print('MISSING', sid, ko); continue
    jobs.setdefault(segs[sid]['file'], []).append({'id': sid, 'lines': lines, 'ko': ko, 'tr': t, 'align': v.get('align', 'left') or 'left',
                                                  'bold': bool(v.get('bold')), 'truncated': bool(v.get('truncated')), 'role': v.get('role', '')})
if tr is None:
    json.dump(dump, open(f'{LOC}/strings_ko.json', 'w'), ensure_ascii=False, indent=0)
    print(json.dumps({'vol': a.vol, 'jobs': len(dump), 'unique': len({d['ko'] for d in dump})}, ensure_ascii=False)); sys.exit()

# ---------- 자리 재기: 좌우 빈 공간, 덮을 색, 줄 묶음
for f, lst in jobs.items():
    im = im_of(f); H, W = im.shape[:2]
    for j in lst:
        for l in j['lines']:
            bg = np.array(l['bg']); ya, yb = max(0, l['y0']), min(H, l['y1'])
            def free(x): return np.abs(im[ya:yb, x] - bg).max() <= 30
            r = l['x1']
            while r < W - 1 and free(r): r += 1
            q = l['x0'] - 1
            while q > 0 and free(q): q -= 1
            l['free_r'] = int(r); l['free_l'] = int(q + 1)
            ring = np.concatenate([im[max(0, l['y0'] - 4), l['x0']:l['x1']], im[min(H - 1, l['y1'] + 3), l['x0']:l['x1']]])
            l['fill'] = [int(v) for v in np.median(ring, 0)] if len(ring) else l['bg']
    allboxes = [(j['id'], l) for j in lst for l in j['lines']]
    for j in lst:
        rows = []
        for l in sorted(j['lines'], key=lambda l: (l['y0'], l['x0'])):
            cy = (l['y0'] + l['y1']) / 2
            if rows and abs(cy - rows[-1]['cy']) < 0.5 * l['h']:
                r = rows[-1]; r['x0'] = min(r['x0'], l['x0']); r['x1'] = max(r['x1'], l['x1'])
                r['y0'] = min(r['y0'], l['y0']); r['y1'] = max(r['y1'], l['y1']); r['free_r'] = max(r['free_r'], l['free_r']); r['free_l'] = min(r['free_l'], l['free_l'])
            else:
                rows.append({'cy': cy, 'x0': l['x0'], 'x1': l['x1'], 'y0': l['y0'], 'y1': l['y1'], 'h': l['h'], 'fg': l['fg'], 'ko': l['ko'],
                             'free_r': l['free_r'], 'free_l': l['free_l']})
        for r in rows:
            m = 0.35 * r['h']
            nb_r = any(oid != j['id'] and abs(ol['x0'] - r['free_r']) < 0.6 * r['h'] and ol['y0'] < r['y1'] and ol['y1'] > r['y0'] for oid, ol in allboxes)
            nb_l = any(oid != j['id'] and abs(ol['x1'] - r['free_l']) < 0.6 * r['h'] and ol['y0'] < r['y1'] and ol['y1'] > r['y0'] for oid, ol in allboxes)
            edge_r = min(r['free_r'], int(W - 0.6 * r['h']))   # 이미지 오른쪽 끝에서 글자 높이 0.6배 안쪽까지만
            r['lim_r'] = int(r['x1'] + (r['free_r'] - r['x1']) * 0.5) if nb_r else int(max(r['x1'], edge_r - m))
            r['lim_l'] = int(r['x0'] - (r['x0'] - r['free_l']) * 0.5) if nb_l else int(min(r['x0'], r['free_l'] + m))
        r = rows[-1]; ya, yb = int(r['y1'] + 0.25 * r['h']), int(r['y1'] + 1.6 * r['h'])
        j['below_free'] = bool(yb < H and r['lim_r'] > r['x0'] and np.abs(im[ya:yb, r['x0']:r['lim_r']] - np.array(j['lines'][0]['bg'])).max() <= 12)
        if len(rows) > 1:
            pw = max(r['x1'] for r in rows)
            for r in rows: r['lim_r'] = min(r['lim_r'], pw + int(0.02 * (pw - rows[0]['x0'])))
        j['rows'] = rows

FONTS = f'file://{HERE}/assets/fonts'; FONTS_JA = f'file://{HERE}/assets/fonts_ja'
FAM = 'PretendardJP, PretendardS, sans-serif' if lang == 'ja' else 'PretendardS, sans-serif'
PAGE = f"""<!doctype html><html><head><meta charset=utf-8><style>
@font-face{{font-family:PretendardS;src:url({FONTS}/Pretendard-400.ttf);font-weight:400}}
@font-face{{font-family:PretendardS;src:url({FONTS}/Pretendard-500.ttf);font-weight:500}}
@font-face{{font-family:PretendardS;src:url({FONTS}/Pretendard-700.ttf);font-weight:700}}
@font-face{{font-family:PretendardJP;src:url({FONTS_JA}/PretendardJP-Regular.ttf);font-weight:400}}
@font-face{{font-family:PretendardJP;src:url({FONTS_JA}/PretendardJP-Medium.ttf);font-weight:500}}
@font-face{{font-family:PretendardJP;src:url({FONTS_JA}/PretendardJP-Bold.ttf);font-weight:700}}
</style></head><body><canvas id=c></canvas></body></html>"""
JS = r"""async ({src, jobs, fam}) => {
  for (const w of [400,500,700]) { await document.fonts.load(`${w} 40px PretendardS`, '가A'); await document.fonts.load(`${w} 40px PretendardJP`, 'あ亜'); }
  const img = new Image(); img.src = src; await img.decode();
  const c = document.getElementById('c'); c.width = img.naturalWidth; c.height = img.naturalHeight;
  const g = c.getContext('2d'); g.drawImage(img, 0, 0);
  const log = [];
  const rgb = a => `rgb(${a[0]},${a[1]},${a[2]})`;
  for (const j of jobs) for (const l of j.lines) {
    const pad = Math.max(2, Math.round(l.h * 0.1)), vpad = Math.max(1, Math.round(l.h * 0.05));
    g.fillStyle = rgb(l.fill);
    g.fillRect(l.x0 - pad, l.y0 - vpad, (l.x1 - l.x0) + 2 * pad, (l.y1 - l.y0) + 2 * vpad);
  }
  for (const j of jobs) {
    const R = j.rows, R0 = R[0];
    g.textBaseline = 'alphabetic';
    // 굵기: 원래 한글을 400·500·700으로 같은 높이에 그려 잉크 밀도가 가장 가까운 것
    const inkDensity = (w) => { g.font = `${w} 100px PretendardS`; const m = g.measureText(R0.ko); return (m.actualBoundingBoxAscent + m.actualBoundingBoxDescent) > 0 ? m.width : 1; };
    let weight = j.bold ? 700 : 500;
    if (!j.bold && j.role !== 'title' && j.role !== 'header') weight = 400;
    g.font = `${weight} 100px PretendardS`;
    const km = g.measureText(R0.ko);
    const kInk = km.actualBoundingBoxAscent + km.actualBoundingBoxDescent;
    const kMid = (km.actualBoundingBoxDescent - km.actualBoundingBoxAscent) / 2;
    const pxH = (R0.y1 - R0.y0) / kInk * 100;
    const pxW = (j.lines[0].x1 - j.lines[0].x0) / (km.actualBoundingBoxRight + km.actualBoundingBoxLeft) * 100;
    const px = Math.min(pxH * 1.05, pxW * 1.05, Math.max(pxH, pxW) * 0.95);
    const base0 = (R0.y0 + R0.y1) / 2 - kMid * px / 100;
    const lineH = R.length > 1 ? (R[R.length-1].cy - R[0].cy) / (R.length - 1) : px * 1.45;
    const fixedBox = ['button','tab','badge','header','status'].includes(j.role);
    const floor = fixedBox ? 0.65 : 0.55;
    const setFont = p => { g.font = `${weight} ${p}px ${fam}`; };
    const wrap = (p, widths) => {
      setFont(p);
      const words = j.tr.split(/(?<=\s)|(?=[぀-ヿ一-鿿])|(?<=[぀-ヿ一-鿿、。])/);
      const out = []; let cur = '';
      for (const w of words) { const t = cur + w; const lim = widths[Math.min(out.length, widths.length - 1)]; if (cur && g.measureText(t.trimEnd()).width > lim) { out.push(cur.trimEnd()); cur = w.trimStart(); } else cur = t; }
      if (cur) out.push(cur.trimEnd());
      return out;
    };
    const rowAvail = r => {
      if (j.truncated) return r.x1 - r.x0;
      if (j.align === 'center') { const cx = (r.x0 + r.x1) / 2; return Math.max(r.x1 - r.x0, 2 * Math.min(cx - r.lim_l, r.lim_r - cx)); }
      if (j.align === 'right') return Math.max(r.x1 - r.x0, r.x1 - r.lim_l);
      return Math.max(r.x1 - r.x0, r.lim_r - R0.x0);
    };
    let widths = R.map(rowAvail), maxLines = R.length;
    const fits = (ls, ws) => ls.length <= maxLines && ls.every((t, i) => g.measureText(t).width <= ws[Math.min(i, ws.length - 1)] + 0.5);
    let p = px, lines = wrap(p, widths);
    while (!fits(lines, widths) && p > px * 0.85) { p -= px * 0.02; lines = wrap(p, widths); }
    if (!fits(lines, widths) && R.length === 1 && j.below_free && !fixedBox && !j.truncated && maxLines === 1) { maxLines = 2; p = px; lines = wrap(p, widths); while (!fits(lines, widths) && p > px * 0.85) { p -= px * 0.02; lines = wrap(p, widths); } }
    if (!fits(lines, widths) && j.align === 'center' && R.length === 1) {
      const alt = [Math.max(R0.x1 - R0.x0, R0.lim_r - R0.x0)]; let q = px, l2 = wrap(q, alt);
      while (!fits(l2, alt) && q > px * 0.85) { q -= px * 0.02; l2 = wrap(q, alt); }
      if (fits(l2, alt) && q > p) { j.align = 'left'; widths = alt; p = q; lines = l2; }
    }
    while (!fits(lines, widths) && p > px * floor) { p -= px * 0.02; lines = wrap(p, widths); }
    while (!fits(lines, widths) && p > px * 0.45) { p -= px * 0.02; lines = wrap(p, widths); }
    let over = fits(lines, widths) ? 0 : 1;
    if (j.truncated) { lines = [j.tr]; over = 0; }
    else if (maxLines === 1 && lines.length > 1) lines = [j.tr];
    else if (lines.length > maxLines) lines = [...lines.slice(0, maxLines - 1), lines.slice(maxLines - 1).join(' ')];
    setFont(p);
    g.fillStyle = `rgb(${R0.fg[0]},${R0.fg[1]},${R0.fg[2]})`;
    lines.forEach((t, i) => {
      const r = R[Math.min(i, R.length - 1)];
      const base = base0 + i * lineH;
      const w = g.measureText(t).width;
      const x = j.align === 'center' ? (r.x0 + r.x1) / 2 - w / 2 : j.align === 'right' ? r.x1 - w : R0.x0;
      g.save();
      if (j.truncated || over) { g.beginPath(); g.rect(R0.lim_l - 2, R0.y0 - R0.h, (R0.lim_r - R0.lim_l) + 4, R0.h * 3); g.clip(); }
      g.fillText(t, x, base);
      g.restore();
    });
    log.push({id: j.id, px: Math.round(px*10)/10, used: Math.round(p*10)/10, weight, lines: lines.length, over, align: j.align});
  }
  return {data: c.toDataURL('image/png'), log};
}"""

async def main():
    tmp = f'{OUT}/_render.html'; open(tmp, 'w').write(PAGE)
    out_segments = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='chrome', args=['--allow-file-access-from-files'])
        pg = await b.new_page()
        await pg.goto('file://' + tmp)
        files = sorted(f for f in os.listdir(KO) if re.match(r's\d+_\d+_\d+\.png$', f))
        if a.only: files = [a.only]
        for f in files:
            lst = jobs.get(f, [])
            r = await pg.evaluate(JS, {'src': f'file://{KO}/{f}', 'jobs': lst, 'fam': FAM})
            open(f'{OUT}/{f}', 'wb').write(base64.b64decode(r['data'].split(',', 1)[1]))
            logs = {x['id']: x for x in r['log']}
            recs = []
            for j in lst:
                lg = logs[j['id']]; l0 = j['lines'][0]
                scale = round(lg['used'] / lg['px'], 3)
                flag = '' if scale >= 0.85 and not lg['over'] else ('[확인 필요] 45%로도 넘침' if lg['over'] else ('[확인 필요] 85% 미만 축소' if scale >= (0.65 if j['role'] in ('button', 'tab', 'badge', 'header', 'status') else 0.55) else '[확인 필요] 축소 한계 미만'))
                recs.append({'id': j['id'], 'ko': j['ko'], 'tr': j['tr'], 'box_px_orig': [round(l0['x0'] / 2, 1), round(l0['y0'] / 2, 1), round((l0['x1'] - l0['x0']) / 2, 1), round((l0['y1'] - l0['y0']) / 2, 1)],
                             'font_px': lg['used'], 'scale': scale, 'weight': lg['weight'], 'paragraph_lines': lg['lines'], 'lines_in_segment': len(j['lines']),
                             'align': lg['align'], 'role': j['role'], 'flag': flag})
            out_segments[f] = {'replaced': len(recs), 'segments': recs, 'flags': [x for x in recs if x['flag']]}
            print(f, len(lst), 'flag', len(out_segments[f]['flags']))
        await b.close()
    os.remove(tmp)
    json.dump({'lang': lang, 'method': '한국어 글자 자리를 바탕색으로 덮고 번역어를 Pretendard(일본어 Pretendard JP)로 다시 그림. 생성형 AI 사용 안 함', 'files': out_segments},
              open(f'{OUT}/replacements.json', 'w'), ensure_ascii=False, indent=1)
    tot = sum(v['replaced'] for v in out_segments.values()); fl = sum(len(v['flags']) for v in out_segments.values())
    print(json.dumps({'vol': a.vol, 'lang': lang, 'replaced': tot, 'flagged': fl}, ensure_ascii=False))

asyncio.run(main())
