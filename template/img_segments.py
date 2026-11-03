"""화면 캡처에서 한국어 글자 덩어리를 찾아 적는다 (고정 프롬프트 11절 '번역본 화면 이미지' 2순위의 1단계).

사용: python3 template/img_segments.py <분권> [--ocr-bin 경로]
입력: manuals/<분권>/ko/img/s*.png (한국어판 2배 확대본)
출력: manuals/<분권>/img/loc/ocr.json        OCR 원문(1배 + 2배 확대본 합침)
      manuals/<분권>/img/loc/segments.json   한글 덩어리(위치·바탕색·글자색·낱말 경계)
      manuals/<분권>/img/loc/sheets/*.png     교정용 확인 시트
      manuals/<분권>/img/loc/strings.json     덩어리 OCR 글(교정 전) 목록
"""
import json, re, sys, os, subprocess, argparse, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HAN = re.compile('[가-힣ㄱ-ㅎㅏ-ㅣ]')

ap = argparse.ArgumentParser()
ap.add_argument('vol')
ap.add_argument('--ocr-bin', default=os.environ.get('IMG_OCR_BIN', ''))
ap.add_argument('--add', action='store_true', help='이미 segments.json 에 있는 파일은 건너뛰고 새 파일 덩어리만 덧붙인다')
ap.add_argument('--reocr', action='store_true', help='가로로 긴 캡처(폭이 높이의 2.5배 넘고 1200px 넘음)를 조각 OCR로 다시 읽어, 기존 덩어리와 겹치지 않는 것만 r_ id로 덧붙인다 (2026-11-03)')
ap.add_argument('--files', nargs='*', default=None, help='--reocr 에서 다시 읽을 파일만 고른다')
a = ap.parse_args()
V = f'{ROOT}/manuals/{a.vol}'
KO = f'{V}/ko/img'
LOC = f'{V}/img/loc'
os.makedirs(f'{LOC}/sheets', exist_ok=True)
files = sorted(f for f in os.listdir(KO) if re.match(r's\d+_\d+[a-z]?_\d+\.png$', f))   # s2_4b_1.png 처럼 절 번호에 글자가 붙은 파일도 포함
old_segs = json.load(open(f'{LOC}/segments.json')) if (a.add or a.reocr) and os.path.exists(f'{LOC}/segments.json') else []
if a.add:
    have = {s['file'] for s in old_segs}; files = [f for f in files if f not in have]
if a.reocr:
    def wide(f):
        im = Image.open(f'{KO}/{f}'); return im.width > 2.5 * im.height and im.width > 1200
    files = [f for f in files if (f in a.files if a.files else wide(f))]
    if not files: sys.exit('새 파일 없음')


def ocr(paths, lang='ko'):
    if not a.ocr_bin:
        r = subprocess.run(['swift', f'{HERE}/img_ocr.swift', '--lang', lang] + paths, capture_output=True, text=True)
    else:
        r = subprocess.run([a.ocr_bin, '--lang', lang] + paths, capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr)
    return json.loads(r.stdout)


# ---------- 1. OCR: 1배와 2배 확대본을 따로 읽고 합친다 (작은 회색 글자는 한쪽에서만 잡힌다)
res1 = {d['file']: d for d in ocr([f'{KO}/{f}' for f in files])}
with tempfile.TemporaryDirectory() as td:
    big = []
    for f in files:
        im = Image.open(f'{KO}/{f}').convert('RGB')
        im.resize((im.width * 2, im.height * 2), Image.LANCZOS).save(f'{td}/{f}')
        big.append(f'{td}/{f}')
    res2 = {d['file']: d for d in ocr(big)}


def overlap(a, b):
    ax, ay, aw, ah = a; bx, by, bw, bh = b
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx)); iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    return ix * iy / max(1e-6, min(aw * ah, bw * bh))


merged = []
for f in files:
    items = [dict(it, src=1) for it in res1[f]['items']]
    for it in res2[f]['items']:
        it = dict(it, src=2, box=[v / 2 for v in it['box']], chars=[[v / 2 for v in c] for c in it['chars']])
        if not HAN.search(it['t']): continue
        if any(overlap(it['box'], o['box']) > 0.5 for o in items): continue
        items.append(it)
    merged.append({'file': f, 'W': res1[f]['W'], 'H': res1[f]['H'], 'items': items})
if (a.add or a.reocr) and os.path.exists(f'{LOC}/ocr.json'):
    redo = {d['file'] for d in merged}
    merged_all = [d for d in json.load(open(f'{LOC}/ocr.json')) if d['file'] not in redo] + merged
else: merged_all = merged
json.dump(merged_all, open(f'{LOC}/ocr.json', 'w'), ensure_ascii=False)


# ---------- 2. 한글이 든 줄을 픽셀 간격으로 덩어리로 나눈다
def bgcolor(a):
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    q = (border // 8).astype(int)
    keys = q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2]
    vals, counts = np.unique(keys, return_counts=True)
    return border[keys == vals[counts.argmax()]].mean(0)


def runs_of(cols):
    runs = []; st = None
    for i, c in enumerate(cols):
        if c and st is None: st = i
        if not c and st is not None: runs.append([st, i]); st = None
    if st is not None: runs.append([st, len(cols)])
    return runs


segs = []
n_old = len(old_segs)
def covered(f, gx0, gx1, ty0, ty1):
    # --reocr: 이미 있는 덩어리(검수 끝난 것)와 겹치면 새로 만들지 않는다
    for o in old_segs:
        if o['file'] != f: continue
        ix = max(0, min(gx1, o['x1']) - max(gx0, o['x0'])); iy = max(0, min(ty1, o['y1']) - max(ty0, o['y0']))
        if ix * iy > 0.3 * min((gx1 - gx0) * (ty1 - ty0), (o['x1'] - o['x0']) * (o['y1'] - o['y0'])): return True
    return False
for d in merged:
    im = np.asarray(Image.open(f'{KO}/{d["file"]}').convert('RGB')).astype(float)
    H, W = im.shape[:2]
    for li, it in enumerate(d['items']):
        if not HAN.search(it['t']): continue
        x, y, w, h = it['box']
        pad = max(3, h * 0.15)
        x0, y0, x1, y1 = int(max(0, x - pad)), int(max(0, y - pad)), int(min(W, x + w + pad)), int(min(H, y + h + pad))
        a_ = im[y0:y1, x0:x1]
        if a_.size == 0: continue
        bg = bgcolor(a_)
        diff = np.abs(a_ - bg).max(2)
        ink = diff > 40
        runs = runs_of(ink.any(0))
        if not runs: continue
        gap = 0.6 * h
        blobs = [runs[0][:]]
        for r in runs[1:]:
            if r[0] - blobs[-1][1] < gap: blobs[-1][1] = r[1]
            else: blobs.append(r[:])
        for bs, be in blobs:
            gx0, gx1 = x0 + bs, x0 + be
            txt = ''
            for ch, cb in zip(it['t'], it['chars']):
                if cb[2] <= 0: txt += ch; continue
                cx = cb[0] + cb[2] / 2
                if gx0 - 2 <= cx <= gx1 + 2: txt += ch
            txt = re.sub(r'\s+', ' ', txt).strip()
            if not HAN.search(txt): continue
            sub = ink[:, bs:be]; rows = np.where(sub.any(1))[0]
            ty0, ty1 = y0 + rows.min(), y0 + rows.max() + 1
            # 낱말 경계 (글자 높이의 0.28배 넘는 빈틈)
            wr = runs_of(sub.any(0)); words = [wr[0][:]]
            for r in wr[1:]:
                if r[0] - words[-1][1] < 0.28 * h: words[-1][1] = r[1]
                else: words.append(r[:])
            if a.reocr and covered(d['file'], gx0, gx1, ty0, ty1): continue
            px = a_[:, bs:be][sub]; dd = diff[:, bs:be][sub]
            col = px[dd >= np.percentile(dd, 90)].mean(0) if len(px) else np.array([0, 0, 0])
            if col.max() - col.min() < 45: col = np.array([col.mean()] * 3)
            segs.append({'id': ('r_' if a.reocr else '') + f'{d["file"][:-4]}_{n_old + len(segs):03d}', 'file': d['file'], 'line': li, 'ocr': txt, 'line_text': it['t'],
                         'x0': int(gx0), 'x1': int(gx1), 'y0': int(ty0), 'y1': int(ty1), 'line_y0': int(y), 'line_h': round(h, 1),
                         'words': [[int(gx0 + p), int(gx0 + q)] for p, q in words],
                         'bg': [int(round(v)) for v in bg], 'fg': [int(round(v)) for v in col], 'conf': round(it['conf'], 2), 'src': it['src']})
json.dump(old_segs + segs, open(f'{LOC}/segments.json', 'w'), ensure_ascii=False, indent=0)

# ---------- 3. 확인 시트 (덩어리마다 확대 crop + id + OCR 글)
F = ImageFont.truetype(f'{HERE}/assets/fonts/Pretendard-700.ttf', 15)
FS = ImageFont.truetype(f'{HERE}/assets/fonts/Pretendard-500.ttf', 13)
TH, SW = 56, 1400
by = {}
for s in segs: by.setdefault(s['file'], []).append(s)
sheets = []
for f, lst in by.items():
    base = Image.open(f'{KO}/{f}').convert('RGB')
    rows = []
    for s in lst:
        h = s['line_h']; pad = int(1.2 * h)
        X0 = max(0, s['x0'] - pad); X1 = min(base.width, s['x1'] + pad); Y0 = max(0, int(s['y0'] - 0.6 * h)); Y1 = min(base.height, int(s['y1'] + 0.6 * h))
        crop = base.crop((X0, Y0, X1, Y1)).copy()
        sc = TH / crop.height; crop = crop.resize((max(1, int(crop.width * sc)), TH), Image.LANCZOS)
        if crop.width > SW - 300:
            sc2 = (SW - 300) / crop.width; crop = crop.resize((SW - 300, max(1, int(TH * sc2)))); sc *= sc2
        dr = ImageDraw.Draw(crop)
        dr.rectangle([(s['x0'] - X0) * sc - 1, (s['y0'] - Y0) * sc - 2, (s['x1'] - X0) * sc + 1, (s['y1'] - Y0) * sc + 2], outline=(255, 0, 0), width=1)
        row = Image.new('RGB', (SW, crop.height + 22), 'white')
        row.paste(crop, (290, 18))
        d2 = ImageDraw.Draw(row)
        d2.text((4, 4), s['id'], fill=(0, 0, 0), font=F)
        d2.text((4, 24), s['ocr'][:34], fill=(90, 90, 90), font=FS)
        d2.line([(0, row.height - 1), (SW, row.height - 1)], fill=(200, 200, 200))
        rows.append(row)
    cur = []; hh = 0; n = 0
    def flush():
        global cur, hh, n
        if not cur: return
        S = Image.new('RGB', (SW, sum(r.height for r in cur)), 'white'); y = 0
        for r in cur: S.paste(r, (0, y)); y += r.height
        p = f'{LOC}/sheets/{"r_" if a.reocr else ""}{f[:-4]}_{n}.png'; S.save(p); sheets.append(os.path.relpath(p, ROOT)); cur = []; hh = 0; n += 1
    for r in rows:
        if hh + r.height > 1800: flush()
        cur.append(r); hh += r.height
    flush()
json.dump({s['id']: s['ocr'] for s in old_segs + segs}, open(f'{LOC}/strings.json', 'w'), ensure_ascii=False, indent=0)
print(json.dumps({'vol': a.vol, 'images': len(files), 'segments': len(segs), 'sheets': len(sheets)}, ensure_ascii=False))
