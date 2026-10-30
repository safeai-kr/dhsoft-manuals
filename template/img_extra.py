"""2차 덩어리 찾기: 번역본 캡처의 한글 검사(check_img_hangul.py)에서 '픽셀 그대로'로 잡힌 자리를 한국어판에서 다시 잘라 덩어리로 만든다.
1차 OCR이 놓친 표 안 글자(상태·활성·편집 등)가 대상이다. 읽을 수 없는 글(자모 섞임, 한글 1자)은 뺀다.

사용: python3 template/img_extra.py <분권>
입력: manuals/<분권>/{en,de,ja}/img/hangul_check.json, manuals/<분권>/img/loc/{segments,verified}.json, i18n/image_<lang>.json
출력: segments.json·verified.json 에 x_ 로 시작하는 덩어리를 덧붙이고,
      번역이 없는 원문은 manuals/<분권>/img/loc/extra_todo.json 에 적는다.
"""
import json, re, sys, os
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
vol = sys.argv[1]; V = f'{ROOT}/manuals/{vol}'; KO = f'{V}/ko/img'; LOC = f'{V}/img/loc'
SYL = re.compile('[가-힣]'); JAMO = re.compile('[ㄱ-ㅎㅏ-ㅣ]')
LEAD = re.compile(r'^[\s•·\-~+✓✔×✕UOQGhT#‡()\[\]|_.,:;0-9A-Za-z]{0,3}(?=[가-힣])')   # 아이콘을 글자로 읽은 머리 기호
segs = json.load(open(f'{LOC}/segments.json')); ver = json.load(open(f'{LOC}/verified.json'))
have = {(s['file'], s['x0'], s['y0']) for s in segs}
existing = {s['id'] for s in segs}
trs = {l: json.load(open(f'{V}/i18n/image_{l}.json')) for l in ('en', 'de', 'ja') if os.path.exists(f'{V}/i18n/image_{l}.json')}
hits = {}
for l in ('en', 'de', 'ja'):
    p = f'{V}/{l}/img/hangul_check.json'
    if not os.path.exists(p): continue
    for r in json.load(open(p))['remaining_korean']:
        t = r['text'].strip()
        if JAMO.search(t) or len(SYL.findall(t)) < 2: continue
        key = (r['file'], tuple(r['box']))
        hits.setdefault(key, t)

def bgcolor(a):
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    q = (border // 8).astype(int); keys = q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2]
    vals, counts = np.unique(keys, return_counts=True)
    return border[keys == vals[counts.argmax()]].mean(0)

def runs_of(cols):
    runs = []; st = None
    for i, c in enumerate(cols):
        if c and st is None: st = i
        if not c and st is not None: runs.append([st, i]); st = None
    if st is not None: runs.append([st, len(cols)])
    return runs

added = 0; todo = {}
n0 = sum(1 for s in segs if s['id'].startswith('x_'))
for (f, box), t in sorted(hits.items()):
    if any(s['file'] == f and abs(s['x0'] - box[0]) < 6 and abs(s['y0'] - box[1]) < 6 for s in segs): continue
    im = np.asarray(Image.open(f'{KO}/{f}').convert('RGB')).astype(float); H, W = im.shape[:2]
    x, y, w, h = box; pad = max(3, h * 0.15)
    x0, y0, x1, y1 = int(max(0, x - pad)), int(max(0, y - pad)), int(min(W, x + w + pad)), int(min(H, y + h + pad))
    a_ = im[y0:y1, x0:x1]
    if a_.size == 0: continue
    bg = bgcolor(a_); diff = np.abs(a_ - bg).max(2); ink = diff > 40
    cols = ink.any(0)
    if not cols.any(): continue
    xs = np.where(cols)[0]; gx0, gx1 = x0 + xs.min(), x0 + xs.max() + 1
    rows = np.where(ink.any(1))[0]; ty0, ty1 = y0 + rows.min(), y0 + rows.max() + 1
    wr = runs_of(cols); words = [wr[0][:]]
    for r in wr[1:]:
        if r[0] - words[-1][1] < 0.28 * h: words[-1][1] = r[1]
        else: words.append(r[:])
    px = a_[ink]; dd = diff[ink]
    col = px[dd >= np.percentile(dd, 90)].mean(0) if len(px) else np.array([0, 0, 0])
    if col.max() - col.min() < 45: col = np.array([col.mean()] * 3)
    ko = LEAD.sub('', t).strip()
    icon = ko != t.strip() and len(words) > 1 and (words[0][1] - words[0][0]) < 1.5 * h
    sid = f'x_{f[:-4]}_{n0 + added:03d}'
    segs.append({'id': sid, 'file': f, 'line': -1, 'ocr': t, 'line_text': t, 'x0': int(gx0), 'x1': int(gx1), 'y0': int(ty0), 'y1': int(ty1),
                 'line_y0': int(y), 'line_h': round(float(h), 1), 'words': [[int(x0 + p), int(x0 + q)] for p, q in words],
                 'bg': [int(round(v)) for v in bg], 'fg': [int(round(v)) for v in col], 'conf': 0, 'src': 'extra'})
    ver.append({'id': sid, 'ko': ko, 'skip': False, 'join_next': None, 'bold': False, 'align': 'left', 'role': 'label',
                'truncated': False, 'icon_lead': bool(icon), 'note': '2차(한글 잔존 검사)에서 추가'})
    added += 1
    for l, tr in trs.items():
        if ko not in tr: todo.setdefault(ko, []).append(l)
json.dump(segs, open(f'{LOC}/segments.json', 'w'), ensure_ascii=False, indent=0)
json.dump(ver, open(f'{LOC}/verified.json', 'w'), ensure_ascii=False, indent=0)
json.dump(todo, open(f'{LOC}/extra_todo.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({'vol': vol, 'added': added, 'need_translation': len(todo), 'todo': list(todo)[:12]}, ensure_ascii=False))
