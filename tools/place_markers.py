"""화면 위 번호 원이 글자·아이콘·다른 요소를 가리면 옆 빈자리로 옮긴다 (고정 프롬프트 11절, hy0909 결정 2026-10-30 · 2026-11-03).

번호 원은 캡처 기준 위치(%)로 HTML에 찍힌다. 한국어판도 포함해 모든 언어에 적용한다. 규칙:
- 원(반지름 + 2px)이 덮는 자리에 잉크(글자·아이콘·테두리처럼 색이 급하게 바뀌는 가장자리 픽셀)가 2% 넘게 있으면 요소를 가린 것이다. 옮긴다. 버튼·칸의 평평한 안쪽은 잉크가 아니다.
- 빈자리는 가리키던 요소 가까이: 같은 줄 오른쪽·왼쪽, 같은 열 아래·위로 2px씩 넓혀 가며 찾는다. 위아래 거리는 2.5배로 쳐서 같은 줄을 우선한다(위아래로 옮기면 다른 줄·다른 상자 안으로 들어가 엉뚱한 것을 가리킨다).
  최대 이동은 이미지 폭의 25%다. 그 안에 빈자리가 없으면 그대로 둔다(기록에 남긴다).
- 이미지 밖으로는 나가지 않는다(원 전체가 이미지 안, 가장자리 2px 여유).
- 원끼리 겹치지 않는다(2026-11-09, Query 2.1 일본어 「1·①」「4·6」「5·5」가 포개짐): 원 중심 사이 거리가 지름 + 4px 이상이어야 한다. 4px은 화면(CSS) px 기준이다(같은 날, 검사패널 3.4·3.8에서 이미지 px로 재서 틈이 1~2px만 남음). 먼저 놓인 원이 자리를 차지하고, 뒤 원이 빈자리를 찾는다.
- 세로로 비슷한 열에 있는 원들(x 차가 이미지 폭의 4% 안)은 같은 x에서 시작하게 맞춘다. 묶음 가운데 가장 오른쪽 x부터 시도해, 모두 빈자리인 x를 찾으면 거기에 맞춘다.
  없으면 각자 자리에 둔다.
사용: python3 tools/place_markers.py manuals [--only <분권>/<lang>] [--dry]   (lang: ko en de ja)
출력: HTML의 margin-left·margin-top 값을 고치고, quality-manifest.json 의 files[*].markers_moved 에 원별 이동 기록을 남긴다.
"""
import json, re, os, sys, argparse
import numpy as np
from PIL import Image
from scipy.signal import fftconvolve

RE_SHOT = re.compile(r'<div class="shot" style="width:([\d.]+)px"><div class="imgbox"[^>]*><img src="img/([^"]+)" alt="">(.*?)</div>', re.S)
RE_MK = re.compile(r'(<span class="mk mk-\w+" style="margin-left:calc\()([\d.]+)(% - 11px\);margin-top:calc\()([\d.]+)(% - 11px\)">)')
R_CSS = 11        # 원 반지름(CSS px)
INK_MAX = 0.02    # 이 비율까지는 빈자리로 본다(번짐 픽셀)
STEP = 2
V_PENALTY = 2.5   # 위아래 이동 거리에 곱하는 가중치
MARGIN = 4        # 원 둘레 여유(px): 이만큼 떨어진 글자도 가린 것으로 본다
MAX_MOVE = 0.25   # 이미지 폭 대비 최대 이동
COL_TOL = 0.04    # 같은 열로 묶는 x 차(이미지 폭 대비)
MK_GAP = 4        # 원과 원 사이 최소 틈(px)


def dominant(a):
    q = (a.reshape(-1, 3) // 8).astype(int); keys = q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2]
    vals, cnt = np.unique(keys, return_counts=True)
    return a.reshape(-1, 3)[keys == vals[cnt.argmax()]].mean(0)


class Field:
    """한 이미지의 잉크 판정. 48px 블록마다 최빈색을 바탕으로 보고, 바탕과 40 넘게 다른 픽셀을 잉크(글자·아이콘·테두리)로 본다.
    원 자리마다의 잉크 비율은 디스크 합성곱으로 한 번에 구한다."""
    B = 48
    def __init__(self, im, r):
        self.im = im; self.r = r; self.H, self.W = im.shape[:2]
        self.gap = MK_GAP * r / R_CSS   # 틈 4px은 화면(CSS) 기준이라 이미지 배율만큼 키운다(2026-11-09, 큰 캡처에서 원이 1~2px 틈으로 붙어 보임)
        B = self.B; H, W = self.H, self.W
        bg = np.zeros((H, W, 3))
        for y in range(0, H, B):
            for x in range(0, W, B):
                blk = im[y:y + B, x:x + B]
                bg[y:y + B, x:x + B] = dominant(blk)
        ink = (np.abs(im - bg).max(2) > 40).astype(float)
        k = int(r + MARGIN); yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
        disk = ((xx ** 2 + yy ** 2) <= (r + MARGIN) ** 2).astype(float)
        self.ratio = fftconvolve(ink, disk, mode='same') / disk.sum()

    def inside(self, cx, cy):
        m = self.r + 2
        return cx - m >= 0 and cy - m >= 0 and cx + m <= self.W - 1 and cy + m <= self.H - 1

    def ink(self, cx, cy):
        if not self.inside(cx, cy): return 1.0
        return float(max(0.0, self.ratio[int(round(cy)), int(round(cx))]))

    def clear_of(self, cx, cy, occupied):
        # 다른 원과 겹치지 않는다: 중심 거리 >= 지름 + MK_GAP
        d = 2 * self.r + self.gap
        return all((cx - ox) ** 2 + (cy - oy) ** 2 >= d * d for ox, oy in occupied)

    def free(self, cx, cy, occupied=()):
        return self.ink(cx, cy) <= INK_MAX and self.clear_of(cx, cy, occupied)

    def clamp(self, cx, cy):
        m = self.r + 2
        return min(max(cx, m), self.W - 1 - m), min(max(cy, m), self.H - 1 - m)

    def nearest_free(self, cx, cy, occupied=()):
        """가장 가까운 빈자리(모든 방향, 위아래 거리는 V_PENALTY배로 침). 없으면 None.
        원래 자리가 이미지 가장자리에 걸쳐 있으면(디자이너가 끝에 붙인 원) 먼저 이미지 안으로 끌어들인 자리에서 찾는다.
        2026-11-09: 네 방향 직선으로만 찾던 것을 격자 전체에서 찾게 바꿈(Query 2.1 일본어 「1·①」「3·4」가 서로 피하지 못하고 겹침)."""
        limit = int(self.W * MAX_MOVE)
        cx, cy = self.clamp(cx, cy)
        if self.free(cx, cy, occupied): return (cx, cy)
        m = int(self.r + 2)
        y0, y1 = max(m, int(cy - limit)), min(self.H - 1 - m, int(cy + limit))
        x0, x1 = max(m, int(cx - limit)), min(self.W - 1 - m, int(cx + limit))
        if y1 < y0 or x1 < x0: return None
        Y, X = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        mask = self.ratio[y0:y1 + 1, x0:x1 + 1] <= INK_MAX
        d2 = (2 * self.r + self.gap) ** 2
        for ox, oy in occupied: mask &= ((X - ox) ** 2 + (Y - oy) ** 2) >= d2
        if not mask.any(): return None
        cost = np.abs(X - cx) + V_PENALTY * np.abs(Y - cy)
        cost = np.where(mask, cost, np.inf)
        k = int(cost.argmin()); yy, xx = divmod(k, cost.shape[1])
        return (float(X[yy, xx]), float(Y[yy, xx]))

    def least_ink(self, cx, cy, occupied=()):
        """빈자리가 없을 때의 차선: 다른 원과 겹치지 않는 자리 가운데 글자를 가장 덜 가리는 곳(거리도 조금 침). 겹치는 것보다 글자를 조금 가리는 쪽이 낫다(2026-11-09)."""
        limit = int(self.W * MAX_MOVE)
        cx, cy = self.clamp(cx, cy)
        m = int(self.r + 2)
        y0, y1 = max(m, int(cy - limit)), min(self.H - 1 - m, int(cy + limit))
        x0, x1 = max(m, int(cx - limit)), min(self.W - 1 - m, int(cx + limit))
        if y1 < y0 or x1 < x0: return None
        Y, X = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        mask = np.ones(Y.shape, bool); d2 = (2 * self.r + self.gap) ** 2
        for ox, oy in occupied: mask &= ((X - ox) ** 2 + (Y - oy) ** 2) >= d2
        if not mask.any(): return None
        cost = self.ratio[y0:y1 + 1, x0:x1 + 1] + (np.abs(X - cx) + V_PENALTY * np.abs(Y - cy)) / (limit * 20.0)
        cost = np.where(mask, cost, np.inf)
        k = int(cost.argmin()); yy, xx = divmod(k, cost.shape[1])
        return (float(X[yy, xx]), float(Y[yy, xx]))


def process(manuals, vol, lang, dry):
    d = os.path.join(manuals, vol, lang)
    hp = [os.path.join(d, f) for f in os.listdir(d) if f.endswith('.html')]
    mf = os.path.join(d, 'img', 'quality-manifest.json')
    if not hp or not os.path.exists(mf): return 0, 0
    hp = hp[0]; html = open(hp).read(); man = json.load(open(mf))
    img_dir = os.path.join(d, 'img')
    moved_total = 0; stuck_total = 0; nonlocal_left = []

    def fix_shot(m):
        nonlocal moved_total, stuck_total
        css_w = float(m.group(1)); name = m.group(2); inner = m.group(3)
        mks = list(RE_MK.finditer(inner))
        if not mks or not os.path.exists(os.path.join(img_dir, name)): return m.group(0)
        im = np.asarray(Image.open(os.path.join(img_dir, name)).convert('RGB')).astype(int)
        W = im.shape[1]; k = W / css_w; r = R_CSS * k
        F = Field(im, r)
        items = []
        for mk in mks:
            X, Y = float(mk.group(2)), float(mk.group(4))
            cx, cy = X / 100 * W, Y / 100 * W      # margin-top % 도 폭 기준
            items.append({'mk': mk, 'X': X, 'Y': Y, 'cx': cx, 'cy': cy, 'ink0': F.ink(cx, cy), 'nx': cx, 'ny': cy, 'stuck': False})
        # 처음 자리에서 서로 겹치는 원 수(기록용)
        overlap0 = sum(1 for a in range(len(items)) for b in range(a) if not F.clear_of(items[a]['cx'], items[a]['cy'], [(items[b]['cx'], items[b]['cy'])]))
        # 1) 가리는 원, 또는 앞서 놓인 원과 겹치는 원은 가장 가까운 빈자리로 (앞 원이 자리를 차지한다)
        placed = []
        for it in items:
            if not (it['ink0'] <= INK_MAX and F.inside(it['cx'], it['cy']) and F.clear_of(it['cx'], it['cy'], placed)):
                p = F.nearest_free(it['cx'], it['cy'], placed)
                if p is None: it['stuck'] = True; placed.append((it['cx'], it['cy'])); continue
                it['nx'], it['ny'] = p
            placed.append((it['nx'], it['ny']))
        # 1-2) 그래도 서로 겹치는 원이 있으면 뒤 원을, 안 되면 앞 원을 다른 원 전부를 피해 옮긴다(세 번까지)
        for _ in range(3):
            moved_any = False
            for bi in range(len(items)):
                for ai in range(bi):
                    a, b_ = items[ai], items[bi]
                    if F.clear_of(b_['nx'], b_['ny'], [(a['nx'], a['ny'])]): continue
                    done_ = False
                    for who in (b_, a):
                        occ = [(o['nx'], o['ny']) for o in items if o is not who]
                        p = F.nearest_free(who['cx'], who['cy'], occ)
                        if p is not None: who['nx'], who['ny'] = p; who['stuck'] = False; moved_any = done_ = True; break
                    if not done_:   # 빈자리가 없으면 뒤 원을 글자를 가장 덜 가리는 자리로라도 옮긴다
                        occ = [(o['nx'], o['ny']) for o in items if o is not b_]
                        p = F.least_ink(b_['cx'], b_['cy'], occ)
                        if p is not None: b_['nx'], b_['ny'] = p; b_['stuck'] = False; moved_any = True
            if not moved_any: break
        # 2) 비슷한 열의 원들은 같은 x로: 가장 오른쪽 x부터 왼쪽으로 2px씩 내려가며 모두 빈자리인 x를 찾는다
        groups = []
        for it in sorted(items, key=lambda i: i['nx']):
            if groups and it['nx'] - groups[-1][-1]['nx'] <= COL_TOL * W: groups[-1].append(it)
            else: groups.append([it])
        for g in groups:
            if len(g) < 2: continue
            xs = sorted({round(i['nx']) for i in g}, reverse=True)
            if len(xs) == 1: continue
            target = None
            others = [(i['nx'], i['ny']) for i in items if i not in g]
            def col_ok(x):
                pts = [(x, i['ny']) for i in g]
                return all(F.free(x, i['ny'], others) for i in g) and all(F.clear_of(pts[k][0], pts[k][1], pts[:k] + pts[k + 1:]) for k in range(len(pts)))
            for x in range(int(xs[0]), int(xs[-1]) - 1, -STEP):
                if col_ok(x): target = x; break
            if target is None:
                for x in range(int(xs[0]) + STEP, int(xs[0] + COL_TOL * W), STEP):
                    if col_ok(x): target = x; break
            if target is not None:
                for i in g: i['nx'] = target
        # 3) 기록·치환
        rec = []; out = inner
        left = sum(1 for a in range(len(items)) for b in range(a) if not F.clear_of(items[a]['nx'], items[a]['ny'], [(items[b]['nx'], items[b]['ny'])]))
        if (overlap0 or left) and isinstance(man.get('files'), dict):   # CRF 권의 manifest는 files가 목록이라 기록을 건너뛴다
            man['files'].setdefault(name, {})['markers_overlapped'] = overlap0; man['files'][name]['markers_overlap_left'] = left
            if left: nonlocal_left.append((name, left))
        for it in reversed(items):
            moved = abs(it['nx'] - it['cx']) >= 1 or abs(it['ny'] - it['cy']) >= 1
            if it['stuck']:
                rec.append({'from_pct': [round(it['X'], 3), round(it['Y'], 3)], 'stuck': True, 'ink': round(it['ink0'], 3)}); continue
            if not moved: continue
            nX, nY = it['nx'] / W * 100, it['ny'] / W * 100
            mk = it['mk']
            out = out[:mk.start()] + mk.group(1) + f'{nX:.3f}' + mk.group(3) + f'{nY:.3f}' + mk.group(5) + out[mk.end():]
            rec.append({'from_pct': [round(it['X'], 3), round(it['Y'], 3)], 'to_pct': [round(nX, 3), round(nY, 3)],
                        'dx_px': int(round(it['nx'] - it['cx'])), 'dy_px': int(round(it['ny'] - it['cy'])),
                        'ink_before': round(it['ink0'], 3), 'ink_after': round(F.ink(it['nx'], it['ny']), 3)})
        if rec:
            moved_total += sum(1 for x in rec if 'to_pct' in x); stuck_total += sum(1 for x in rec if x.get('stuck'))
            if isinstance(man.get('files'), dict) and name in man['files']: man['files'][name]['markers_moved'] = list(reversed(rec))
        return m.group(0)[:m.start(3) - m.start()] + out + m.group(0)[m.end(3) - m.start():]

    new_html = RE_SHOT.sub(fix_shot, html)
    if not dry and new_html != html:
        open(hp, 'w').write(new_html); json.dump(man, open(mf, 'w'), ensure_ascii=False, indent=1)
    if nonlocal_left: print(vol, lang, '겹침 남음', nonlocal_left)
    return moved_total, stuck_total


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('manuals'); ap.add_argument('--only', default=''); ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    total = 0; stuck = 0
    for vol in sorted(os.listdir(a.manuals)):
        for lang in ('ko', 'en', 'de', 'ja'):
            if a.only and a.only != f'{vol}/{lang}': continue
            if not os.path.exists(os.path.join(a.manuals, vol, lang, 'img', 'quality-manifest.json')): continue
            n, s = process(a.manuals, vol, lang, a.dry); total += n; stuck += s
            if n or s: print(vol, lang, 'moved', n, 'stuck', s)
    print('total', total, 'stuck', stuck)
