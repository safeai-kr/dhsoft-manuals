"""번역본 캡처에서 좁은 버튼·칩 안의 축소된 번역 글자를 키운다.

1) 버튼 안 빈 공간을 먼저 쓰고, 2) 그래도 모자라면 버튼 바깥 여백이 빈 쪽으로 버튼을 넓힌다.
버튼 바깥의 다른 요소·화면 위 번호·이미지 끝에는 간격을 남기고, 넘지 않는다.

사용: python3 widen_buttons.py <manuals 폴더> [--only 분권/언어] [--dry] [--sheet 폴더]
"""
import json, re, sys, os, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'template'))
from img_common import modal_bbox

TOL_FILL = 12    # 버튼 안쪽을 찾을 때 같은 색으로 볼 차이(RGB 합). 흰 칩과 연회색 묶음을 구분할 만큼 좁게
TOL_IN = 26      # 글자 칸이 비었는지 볼 때의 차이
TOL_OUT = 20     # 버튼 바깥 배경과 같은 색으로 볼 차이
MIN_SCALE_TODO = 0.85


def dist(a, c):
    return np.abs(a.astype(int) - np.array(c, int)).sum(-1)


def grow(seed, allowed, iters=4000):
    m = seed & allowed
    for _ in range(iters):
        n = m.copy()
        n[1:] |= m[:-1]; n[:-1] |= m[1:]; n[:, 1:] |= m[:, :-1]; n[:, :-1] |= m[:, 1:]
        n &= allowed
        if (n == m).all():
            return m
        m = n
    return m


def font_path(fdir, lang, w):
    if lang == 'ja':
        name = {400: 'Regular', 500: 'Medium', 700: 'Bold'}.get(w, 'Medium')
        return os.path.join(fdir, f'PretendardJP-{name}.ttf')
    return os.path.join(fdir, f'Pretendard-{w if w in (400, 500, 700) else 500}.ttf')


def markers(html, img_name, W):
    """화면 위 번호 원(이미지 픽셀 좌표 중심, 반지름)."""
    m = re.search(r'<div class="shot" style="width:([\d.]+)px"><div class="imgbox"[^>]*><img src="img/' + re.escape(img_name) + r'"(.*?)</div></div>', html, re.S)
    if not m:
        return []
    css_w = float(m.group(1)); k = W / css_w
    out = []
    for a, b in re.findall(r'margin-left:calc\(([\d.]+)% - 11px\);margin-top:calc\(([\d.]+)% - 11px\)', m.group(2)):
        out.append((float(a) / 100 * W, float(b) / 100 * W, 13 * k))   # 22px 원 + 테두리·그림자 여유
    return out


def find_container(ko, box, h):
    """ko 이미지에서 글자 상자를 둘러싼 닫힌 영역(버튼 안쪽)을 찾는다. 없으면 None."""
    H, W = ko.shape[:2]
    x, y, w, hh = box
    pad = int(10 * h); vpad = int(3 * h)
    X0, Y0 = max(0, x - pad), max(0, y - vpad); X1, Y1 = min(W, x + w + pad), min(H, y + hh + vpad)
    win = ko[Y0:Y1, X0:X1]
    # 글자 상자 바로 바깥 고리의 대표색 = 버튼 안 배경
    r = 4
    sides = [ko[max(0, y - r):y - 1, x:x + w].reshape(-1, 3), ko[y + hh + 1:y + hh + r, x:x + w].reshape(-1, 3),
             ko[y:y + hh, max(0, x - r):x - 1].reshape(-1, 3), ko[y:y + hh, x + w + 1:x + w + r].reshape(-1, 3)]
    sides = [v for v in sides if len(v)]
    if not sides:
        return None
    # 글자 상자가 버튼 위아래 테두리에 거의 닿으면 위·아래 고리에 바깥 흰색이 섞인다. 네 방향 고리의 대표색 가운데
    # 다른 고리와 가장 많이 일치하는 색을 버튼 안 배경으로 본다 (2026-10-30 워크스페이스 「신규 워크스페이스 생성」 검은 버튼이 회색으로 바뀐 문제)
    meds = [np.median(v, 0) for v in sides]
    agree = [sum(1 for o in meds if dist(np.array([m]), o)[0] < TOL_FILL) for m in meds]
    best = max(agree)
    bg = [m for m, a in zip(meds, agree) if a == best][-1]   # 동률이면 좌우 띠(뒤쪽 후보)를 우선: 글자가 칸을 거의 채운 버튼은 위·아래 띠가 바깥색이다
    allowed = dist(win, bg) < TOL_FILL
    allowed[y - Y0 - 2:y - Y0 + hh + 2, x - X0 - 2:x - X0 + w + 2] = True     # 원래 글자 자리(번짐 2px 포함)는 배경으로
    seed = np.zeros_like(allowed); seed[y - Y0 + hh // 2, x - X0 + w // 2] = True
    comp = grow(seed, allowed)
    ys, xs = np.where(comp)
    if len(ys) == 0:
        return None   # 글자 자리 가운데가 배경색이 아니면(아이콘·겹친 글) 버튼으로 보지 않는다
    # 창 경계에 닿으면 열린 공간(버튼 아님). 이미지 끝에서 잘린 버튼은 닫힌 것으로 본다
    if (ys.min() == 0 and Y0 > 0) or (ys.max() == comp.shape[0] - 1 and Y1 < H) or ys.min() == 0 and Y0 == 0 or ys.max() == comp.shape[0] - 1 and Y1 == H:
        return None
    if (xs.min() == 0 and X0 > 0) or (xs.max() == comp.shape[1] - 1 and X1 < W):
        return None
    cx0, cx1, cy0, cy1 = xs.min() + X0, xs.max() + X0, ys.min() + Y0, ys.max() + Y0
    if (cy1 - cy0) > 3.2 * h or (cy1 - cy0) < hh:
        return None
    return dict(bg=bg, x0=cx0, x1=cx1, y0=cy0, y1=cy1, comp=comp, X0=X0, Y0=Y0)


def outer_edge(img, x, yc, step, limit):
    """버튼 안 끝에서 바깥으로 걸어 테두리를 지나 바깥 배경이 안정되는 지점을 찾는다."""
    W = img.shape[1]
    prev = None; same = 0; px = x
    for i in range(1, limit):
        px = x + step * i
        if px < 0 or px >= W:
            return None, None
        c = img[yc, px].astype(int)
        if prev is not None and np.abs(c - prev).sum() < 8:
            same += 1
            if same >= 3:
                edge = px - step * 3
                return edge, c
        else:
            same = 0
        prev = c
    return None, None


def band_rows(img, xm, y0, y1, outer, limit=12):
    """버튼 열(xm)에서 위·아래로 테두리·그림자가 끝나는 행."""
    H = img.shape[0]
    t = y0
    for i in range(1, limit):
        if y0 - i < 0: break
        t = y0 - i
        if np.abs(img[t, xm].astype(int) - outer).sum() < TOL_OUT: break
    b = y1
    for i in range(1, limit):
        if y1 + i >= H: break
        b = y1 + i
        if np.abs(img[b, xm].astype(int) - outer).sum() < TOL_OUT: break
    return max(0, t - 1), min(H - 1, b + 1)


def free_run(img, rows, x_start, step, outer, limit, obstacles, gap):
    """바깥쪽으로 비어 있는 열 수(간격 gap을 뺀 값)."""
    W = img.shape[1]
    t, b = rows
    n = 0
    for i in range(1, limit + 1):
        px = x_start + step * i
        if px < 2 or px >= W - 2:
            break
        col = img[t:b + 1, px]
        if (np.abs(col.astype(int) - outer).sum(-1) >= TOL_OUT).any():
            break
        if any(abs(px - mx) < r and (t - r < my < b + r) for mx, my, r in obstacles):
            break
        n = i
    return max(0, n - gap)


def process(manuals, vol, lang, dry, sheet_dir, log):
    d = os.path.join(manuals, vol, lang)
    mf = os.path.join(d, 'img', 'quality-manifest.json')
    man = json.load(open(mf))
    html = open([os.path.join(d, f) for f in os.listdir(d) if f.endswith('.html')][0]).read()
    fdir = os.path.join(d, 'fonts')
    changed_files = 0
    for name, info in man['files'].items():
        segs = [s for s in info.get('segments', []) if s.get('scale', 1) < MIN_SCALE_TODO
                and s.get('paragraph_lines', 1) == 1 and s.get('lines_in_segment', 1) == 1]
        if not segs:
            continue
        kp = os.path.join(manuals, vol, 'ko', 'img', name)
        tp = os.path.join(d, 'img', name)
        if not os.path.exists(kp):
            continue
        ko = np.asarray(Image.open(kp).convert('RGB'))
        tr0 = np.asarray(Image.open(tp).convert('RGB'))
        if ko.shape != tr0.shape:
            continue
        tr = tr0.copy()
        sc = info.get('scale_from_orig', 2.0)
        H, W = ko.shape[:2]
        obst = markers(html, name, W)
        mb = modal_bbox(ko.astype(int))   # 모달 화면이면 버튼은 모달 안에서만 넓힌다 (2026-11-03 방문정의 1.2 ja)
        diff = np.abs(ko.astype(int) - tr0.astype(int)).sum(-1) > 30
        tasks = []
        for s in segs:
            bx = [int(round(v * sc)) for v in s['box_px_orig']]
            h = s['font_px'] / s['scale'] * 0.88    # 원래 글자 높이(잉크)
            x, y, w, hh = bx
            if x < 0 or y < 0 or x + w > W or y + hh > H or w < 4 or hh < 4:
                continue
            # 버튼·배지·탭처럼 짧은 덩어리만(원래 한글 폭이 글자 높이의 6배 미만). 입력칸 예시 글·긴 안내문은 제외
            if w >= 6 * hh:
                continue
            # 상자 안에 원래 한글 잉크가 없으면(좌표 기준 불일치) 건너뛴다
            if not diff[y:y + hh, x:x + w].any():
                continue
            c = find_container(ko, bx, hh)
            if not c:
                continue
            # 번역 글자가 그려진 범위 = 글자 띠에서 원래 상자와 이어진(빈틈 0.6배 이하) 달라진 열
            ry0, ry1 = max(c['y0'], y - 3), min(c['y1'], y + hh + 3) + 1
            colhit = diff[ry0:ry1, :].any(0)
            g = max(4, int(0.6 * hh))
            ex0, ex1 = x, x + w
            while True:
                k = [i for i in range(max(c['x0'], ex0 - g), ex0) if colhit[i]]
                if not k: break
                ex0 = k[0]
            while True:
                k = [i for i in range(ex1, min(c['x1'] + 1, ex1 + g)) if colhit[i]]
                if not k: break
                ex1 = k[-1] + 1
            rr = np.where(diff[ry0:ry1, ex0:ex1].any(1))[0]
            E = [ex0 - 1, min(y, ry0 + rr.min()) - 1, ex1 + 1, max(y + hh, ry0 + rr.max() + 1) + 1]
            sub = tr0[E[1]:E[3], E[0]:E[2]]
            dsub = dist(sub, c['bg'])
            ink = sub[np.unravel_index(dsub.argmax(), dsub.shape)]
            # 연한 회색 글자는 입력칸 예시 글(placeholder)이다. 버튼이 아니므로 제외
            if np.abs(ink.astype(int) - c['bg']).sum() < 260:
                continue
            tasks.append(dict(s=s, c=c, E=E, ink=ink, hh=hh))
        if not tasks:
            continue
        # 2단계: 버튼마다 글자 칸을 재고, 모자라면 넓힌 뒤 다시 쓴다
        results = []
        for t in tasks:
            s, c = t['s'], t['c']
            x0, y0, x1, y1 = t['E']
            snap = tr.copy()
            # 이 버튼의 글자를 지우고, 버튼 안 배경의 미세한 얼룩(이전 채움 경계 등)도 같은 색으로 고른다
            bgc = np.round(c['bg']).astype(np.uint8)
            tr[y0:y1, x0:x1] = bgc
            ch, cw = c['comp'].shape
            X0c = max(0, c['X0']); cw2 = min(W, c['X0'] + cw) - X0c
            win = tr[c['Y0']:c['Y0'] + ch, X0c:X0c + cw2]
            cm = c['comp'][:, X0c - c['X0']:X0c - c['X0'] + cw2]
            win[cm & (dist(win, c['bg']) < TOL_IN * 2)] = bgc
            yc = (y0 + y1) // 2
            # 목표 크기: 원래 한글 크기의 90%. 100%로 키우면 라틴 굵은 글자가 주변보다 커 보이고 버튼도 많이 늘어난다
            full = s['font_px'] / s['scale'] * 0.9
            if full <= s['font_px'] * 1.04:
                continue
            fnt_p = font_path(fdir, lang, s.get('weight', 500))
            # 글자 띠(행)에서 버튼 배경만 이어지는 열 = 쓸 수 있는 칸
            rows = slice(max(c['y0'], y0 - 2), min(c['y1'], y1 + 2) + 1)
            colfree = (dist(tr[rows, :], c['bg']) < TOL_IN).all(0)
            L = x0 + (x1 - x0) // 2
            if L < 0 or L >= len(colfree) or not colfree[L]:
                tr = snap; continue
            a = L
            while a > 0 and colfree[a - 1]: a -= 1
            b = L
            while b < W - 1 and colfree[b + 1]: b += 1
            # 화면 위 번호가 버튼 안쪽을 덮으면 그 앞에서 멈춘다
            for mx, my, r in obst:
                if c['y0'] - r < my < c['y1'] + r:
                    if a <= mx - r <= b and mx > L: b = min(b, int(mx - r) - 2)
                    if a <= mx + r <= b and mx < L: a = max(a, int(mx + r) + 2)
            # 둥근 칩은 글자 띠에서 안쪽이 bbox보다 좁으니 모서리 반지름만큼 봐준다
            rad = (c['y1'] - c['y0']) / 2 + 1
            hit_left = a <= c['x0'] + rad
            hit_right = b >= c['x1'] - rad
            # 왼쪽 정렬로 칸 왼쪽 끝에서 시작하고 오른쪽이 비면 입력칸이다. 버튼이 아니므로 건드리지 않는다
            if s.get('align') == 'left' and hit_left and not hit_right:
                tr = snap; continue
            # 양옆이 모두 다른 요소(체크박스 등)로 막힌 글자는 선택지 라벨이다. 버튼은 적어도 한쪽이 테두리에 닿는다
            if not hit_left and not hit_right:
                tr = snap; continue
            pad_side = max(int(0.55 * t['hh']), 6)
            # 아이콘·다른 칸 쪽은 0.7배, 테두리 쪽은 0.55배 여백
            pa = pad_side if hit_left else max(int(0.7 * t['hh']), 8)
            pb = pad_side if hit_right else max(int(0.7 * t['hh']), 8)
            avail = (b - pb) - (a + pa)

            def text_w(px):
                f = ImageFont.truetype(fnt_p, int(round(px)))
                bb = f.getbbox(s['tr'])
                return bb[2] - bb[0], f
            need_full, _ = text_w(full)
            size = full
            dl = dr = 0
            if need_full > avail:
                extra = need_full - avail
                # 넓히기는 글자 칸 가운데를 늘리는 방식이라, 아이콘이 있는 쪽도 버튼 바깥이 비어 있으면 넓힐 수 있다
                le, outer_l = outer_edge(tr, c['x0'], yc, -1, 30)
                re_, outer_r = outer_edge(tr, c['x1'], yc, 1, 30)
                gap = max(int(0.9 * t['hh']), 10)   # 바깥 요소와 글자 높이 0.9배 간격
                fl = fr = 0
                if le is not None:
                    rows_l = band_rows(tr, max(le + 4, c['x0'] + 2), c['y0'], c['y1'], outer_l)
                    fl = free_run(tr, rows_l, le, -1, outer_l, int(extra) + gap + 2, obst, gap)
                if re_ is not None:
                    rows_r = band_rows(tr, min(re_ - 4, c['x1'] - 2), c['y0'], c['y1'], outer_r)
                    fr = free_run(tr, rows_r, re_, 1, outer_r, int(extra) + gap + 2, obst, gap)
                if s.get('align') == 'center':
                    # 가운데 정렬 버튼은 양쪽을 똑같이 넓힌다. 한쪽만 넓히면 버튼이 위 아이콘·안내문의 중심에서 벗어난다
                    # (2026-10-30 워크스페이스 3.4 「Erneut versuchen」이 왼쪽으로만 115px 늘어난 문제). 한쪽이 막혀 있으면 넓히지 않고 글자를 줄인다
                    dl = dr = min(fl, fr, (extra + 1) // 2)
                else:
                    dr = min(fr, extra); dl = min(fl, extra - dr)
                dl, dr = int(dl), int(dr)
                # 넓히기 전 세 가지 확인 (hy0909 결정 2026-11-03, 방문정의 1.2 ja 「キャンセル」 회색이 모달 밖으로 나가고 옆 버튼을 침범한 문제):
                #  ① 모달 화면이면 모달 안에서만, 버튼 바깥 바탕이 모달 바탕과 다르면(흐린 회색) 넓히지 않는다
                #  ② 새로 덮을 열은 버튼 위아래 글자 높이 0.5배 여유 행까지 모두 바깥 바탕색이어야 한다(옆 버튼·글자·선 침범 금지)
                #  ③ 새로 덮을 자리에 한국어판 글자(잉크 2% 초과)가 있으면 넓히지 않는다
                skipped = []
                if dl or dr:
                    Lx0, Rx0 = (le if le is not None else c['x0']), (re_ if re_ is not None else c['x1'])
                    vm = max(int(0.5 * t['hh']), 4)
                    ry0, ry1 = max(0, c['y0'] - vm), min(H, c['y1'] + vm + 1)
                    def side_ok(xa, xb, outer):
                        if xa < 2 or xb > W - 2: return '이미지 끝'
                        if mb and not (mb[0] + 2 <= xa and xb <= mb[2] - 2): return '모달 밖'
                        if mb and outer is not None and dist(np.array([[outer]]), np.array(c['bg']))[0, 0] >= TOL_OUT * 2 and (np.abs(np.array(outer, float) - 255).max() > 30): return '모달 바탕 아님'
                        reg = tr[ry0:ry1, xa:xb]
                        if outer is None or (dist(reg, outer) >= TOL_OUT).any(): return '위아래 요소 침범'
                        kreg = ko[ry0:ry1, xa:xb].astype(int)
                        kbg = np.median(kreg.reshape(-1, 3), 0)
                        if (np.abs(kreg - kbg).max(-1) > 40).mean() > 0.02: return '한국어판 글자 덮음'
                        return ''
                    if dl:
                        why = side_ok(Lx0 - dl, Lx0, outer_l)
                        if why: skipped.append('왼쪽: ' + why); dl = 0
                    if dr:
                        why = side_ok(Rx0 + 1, Rx0 + 1 + dr, outer_r)
                        if why: skipped.append('오른쪽: ' + why); dr = 0
                    if s.get('align') == 'center' and (dl == 0 or dr == 0): dl = dr = 0   # 가운데 정렬 버튼은 양쪽이 같이 가야 한다
                    if skipped:
                        s['widen_skipped'] = skipped
                        # 넓히지 못하면 칸에 맞게 줄인다
                        lo, hi = s['font_px'], full
                        for _ in range(14):
                            mid = (lo + hi) / 2
                            if text_w(mid)[0] <= avail + dl + dr: lo = mid
                            else: hi = mid
                        size = lo
                avail += dl + dr
                # 그래도 모자라면 칸에 맞게 줄인다
                lo, hi = s['font_px'], full
                if need_full > avail:
                    size = lo
                    for _ in range(14):
                        mid = (lo + hi) / 2
                        if text_w(mid)[0] <= avail: lo = mid
                        else: hi = mid
                    size = lo
            if size <= s['font_px'] * 1.04 and not (dl or dr):
                tr = snap; continue   # 키울 수 없음: 원래대로
            # 넓히기: 글자 칸 가운데 열을 늘리고 양쪽을 바깥으로 민다
            if dl or dr:
                le, outer_l = outer_edge(tr, c['x0'], yc, -1, 30)
                re_, outer_r = outer_edge(tr, c['x1'], yc, 1, 30)
                outer = outer_r if outer_r is not None else outer_l
                t_, b_ = band_rows(tr, L, c['y0'], c['y1'], outer)
                band = tr[t_:b_ + 1].copy()
                Lx, Rx = (le or c['x0']), (re_ or c['x1'])
                newb = band.copy()
                if dl:
                    newb[:, Lx - dl:L - dl + 1] = band[:, Lx:L + 1]
                if dr:
                    newb[:, L + dr:Rx + dr + 1] = band[:, L:Rx + 1]
                newb[:, L - dl:L + dr + 1] = band[:, L:L + 1]
                tr[t_:b_ + 1] = newb
                a -= dl; b += dr
                # 같은 띠의 다른 대상 좌표도 함께 옮긴다
                for o in tasks:
                    if o is t: continue
                    oy0, oy1 = o['E'][1], o['E'][3]
                    if oy1 < t_ or oy0 > b_: continue
                    k = dr if o['E'][0] > L else (-dl if o['E'][2] < L else 0)
                    o['E'][0] += k; o['E'][2] += k
                    for key in ('x0', 'x1', 'X0'): o['c'][key] += k
            # 글자 쓰기
            tw_, f = text_w(size)
            bb = f.getbbox(s['tr'])
            capb = f.getbbox('H')
            # 양옆이 모두 테두리인 칩·버튼은 가운데에 둔다
            if s.get('align') == 'center' or (hit_left and hit_right):
                left = (a + pa + b - pb) / 2 - tw_ / 2
            else:
                left = max(a + pa, min(x0 + 1 - dl, b - pb - tw_))
            cy = (y0 + 1 + y1 - 1) / 2
            top = cy - (capb[1] + capb[3]) / 2
            im = Image.fromarray(tr)
            ImageDraw.Draw(im).text((left - bb[0], top), s['tr'], font=f, fill=tuple(int(v) for v in t['ink']))
            tr = np.asarray(im).copy()
            new_scale = round(size / (full / 0.9), 3)
            results.append((s, size, new_scale, dl + dr))
            s['font_px'] = round(size, 1); s['scale'] = new_scale
            if dl or dr:
                s['button_widened_px'] = dl + dr
            s['flag'] = '' if new_scale >= 0.85 else ('[확인 필요] 85% 미만 축소' if new_scale >= 0.65 else s['flag'])
        if results and 'flags' in info:
            ids = {x['id']: x for x in info['segments']}
            info['flags'] = [ids.get(x['id'], x) for x in info['flags'] if ids.get(x['id'], x).get('flag')]
        if results:
            changed_files += 1
            for s, size, ns, wpx in results:
                log.append(f'{vol}/{lang}/{name}\t{s["tr"]}\t{ns}\t+{wpx}px')
            if sheet_dir:
                os.makedirs(sheet_dir, exist_ok=True)
                rows = []
                for s, size, ns, wpx in results:
                    bx = [int(round(v * sc)) for v in s['box_px_orig']]
                    m = 70
                    X0, Y0 = max(0, bx[0] - m * 3), max(0, bx[1] - m)
                    X1, Y1 = min(W, bx[0] + bx[2] + m * 3), min(H, bx[1] + bx[3] + m)
                    rows.append(np.concatenate([tr0[Y0:Y1, X0:X1], np.full((Y1 - Y0, 8, 3), 255, np.uint8), tr[Y0:Y1, X0:X1]], 1))
                mw = max(r.shape[1] for r in rows)
                rows = [np.pad(r, ((0, 6), (0, mw - r.shape[1]), (0, 0)), constant_values=200) for r in rows]
                Image.fromarray(np.concatenate(rows, 0)).save(os.path.join(sheet_dir, f'{vol}_{lang}_{name}'))
            if not dry:
                Image.fromarray(tr).save(tp, optimize=True)
    if not dry:
        json.dump(man, open(mf, 'w'), ensure_ascii=False, indent=1)
    return changed_files


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('manuals'); ap.add_argument('--only'); ap.add_argument('--dry', action='store_true'); ap.add_argument('--sheet')
    a = ap.parse_args()
    log = []
    for vol in sorted(os.listdir(a.manuals)):
        for lang in ('en', 'de', 'ja'):
            if a.only and a.only != f'{vol}/{lang}':
                continue
            if os.path.exists(os.path.join(a.manuals, vol, lang, 'img', 'quality-manifest.json')):
                process(a.manuals, vol, lang, a.dry, a.sheet, log)
    print('\n'.join(log))
    print('total', len(log))
