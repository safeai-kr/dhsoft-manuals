"""화면 위 번호 원이 글자·아이콘·다른 요소를 가리면 옆 빈자리로 옮긴다 (고정 프롬프트 11절, hy0909 결정 2026-10-30 · 2026-11-03).

번호 원은 캡처 기준 위치(%)로 HTML에 찍힌다. 한국어판도 포함해 모든 언어에 적용한다. 규칙:
- 원(반지름 + 2px)이 덮는 자리에 잉크(글자·아이콘·테두리처럼 색이 급하게 바뀌는 가장자리 픽셀)가 2% 넘게 있으면 요소를 가린 것이다. 옮긴다. 버튼·칸의 평평한 안쪽은 잉크가 아니다.
- 빈자리는 가리키던 요소 가까이: 같은 줄 오른쪽·왼쪽, 같은 열 아래·위로 2px씩 넓혀 가며 찾는다. 위아래 거리는 2.5배로 쳐서 같은 줄을 우선한다(위아래로 옮기면 다른 줄·다른 상자 안으로 들어가 엉뚱한 것을 가리킨다).
  최대 이동은 이미지 폭의 25%다. 그 안에 빈자리가 없으면 그대로 둔다(기록에 남긴다).
- 이미지 밖으로는 나가지 않는다(원 전체가 이미지 안, 가장자리 2px 여유).
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

    def free(self, cx, cy):
        return self.ink(cx, cy) <= INK_MAX

    def nearest_free(self, cx, cy):
        """같은 줄 오른쪽·왼쪽, 같은 열 아래·위로 2px씩 찾아 가장 가까운 빈자리. 없으면 None.
        원래 자리가 이미지 가장자리에 걸쳐 있으면(디자이너가 끝에 붙인 원) 안쪽으로 들어오는 방향에서 첫 빈자리를 찾는다."""
        limit = int(self.W * MAX_MOVE)
        best = None
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for d in range(STEP, limit + 1, STEP):
                x, y = cx + dx * d, cy + dy * d
                if not self.inside(x, y):
                    if self.inside(cx, cy): break      # 안에서 밖으로 나가는 방향이면 그만
                    continue                           # 밖에서 안으로 들어오는 중이면 계속
                if self.free(x, y):
                    cost = d if dy == 0 else d * V_PENALTY   # 같은 줄(좌우)을 위아래보다 우선: 위아래로 옮기면 다른 줄·다른 상자 안으로 들어간다
                    if best is None or cost < best[0]: best = (cost, x, y)
                    break
        return None if best is None else (best[1], best[2])


def process(manuals, vol, lang, dry):
    d = os.path.join(manuals, vol, lang)
    hp = [os.path.join(d, f) for f in os.listdir(d) if f.endswith('.html')]
    mf = os.path.join(d, 'img', 'quality-manifest.json')
    if not hp or not os.path.exists(mf): return 0, 0
    hp = hp[0]; html = open(hp).read(); man = json.load(open(mf))
    img_dir = os.path.join(d, 'img')
    moved_total = 0; stuck_total = 0

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
        # 1) 가리는 원은 가장 가까운 빈자리로
        for it in items:
            if it['ink0'] <= INK_MAX and F.inside(it['cx'], it['cy']): continue
            p = F.nearest_free(it['cx'], it['cy'])
            if p is None: it['stuck'] = True; continue
            it['nx'], it['ny'] = p
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
            for x in range(int(xs[0]), int(xs[-1]) - 1, -STEP):
                if all(F.free(x, i['ny']) for i in g): target = x; break
            if target is None:
                for x in range(int(xs[0]) + STEP, int(xs[0] + COL_TOL * W), STEP):
                    if all(F.free(x, i['ny']) for i in g): target = x; break
            if target is not None:
                for i in g: i['nx'] = target
        # 3) 기록·치환
        rec = []; out = inner
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
            if name in man.get('files', {}): man['files'][name]['markers_moved'] = list(reversed(rec))
        return m.group(0)[:m.start(3) - m.start()] + out + m.group(0)[m.end(3) - m.start():]

    new_html = RE_SHOT.sub(fix_shot, html)
    if not dry and new_html != html:
        open(hp, 'w').write(new_html); json.dump(man, open(mf, 'w'), ensure_ascii=False, indent=1)
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
