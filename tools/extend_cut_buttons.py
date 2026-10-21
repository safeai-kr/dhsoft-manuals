"""번역본 캡처에서 이미지 오른쪽 끝에 잘린 버튼을 온전하게 만든다.

이미지 오른쪽에 흰 여백을 붙이고, 잘린 버튼은 오른쪽 모서리를 왼쪽 모서리와 같은 모양으로 마무리한다.
버튼 글자는 아이콘 바로 뒤(왼쪽)에 두고 원래 한글 크기의 90%로 키운다.
이미지 폭이 바뀌므로 HTML의 imgbox 비율과 화면 위 번호 위치(%)도 함께 고친다.

widen_buttons.py 다음에 돌린다. 사용: python3 extend_cut_buttons.py <manuals 폴더> [--only 분권/언어] [--dry] [--sheet 폴더]
"""
import json, re, os, argparse, glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from widen_buttons import dist, find_container, font_path, TOL_IN

WHITE = np.array([255, 255, 255], np.uint8)


def process(manuals, vol, lang, dry, sheet_dir, log):
    d = os.path.join(manuals, vol, lang)
    mf = os.path.join(d, 'img', 'quality-manifest.json')
    man = json.load(open(mf))
    hp = [os.path.join(d, f) for f in os.listdir(d) if f.endswith('.html')][0]
    html = open(hp).read()
    fdir = os.path.join(d, 'fonts')
    for name, info in man['files'].items():
        kp = os.path.join(manuals, vol, 'ko', 'img', name)
        tp = os.path.join(d, 'img', name)
        if not os.path.exists(kp) or not info.get('segments'):
            continue
        ko = np.asarray(Image.open(kp).convert('RGB'))
        tr0 = np.asarray(Image.open(tp).convert('RGB'))
        if ko.shape != tr0.shape:
            continue   # 이미 넓힌 이미지
        H, W = ko.shape[:2]
        sc = info.get('scale_from_orig', 2.0)
        diff = np.abs(ko.astype(int) - tr0.astype(int)).sum(-1) > 30
        hits = []
        for s in info['segments']:
            if s.get('lines_in_segment', 1) != 1:
                continue
            x, y, w, hh = [int(round(v * sc)) for v in s['box_px_orig']]
            if x + w > W or y + hh > H or w < 4 or hh < 4 or w >= 6 * hh:
                continue
            c = find_container(ko, [x, y, w, hh], hh)
            # 앞 단계(widen_buttons)에서 이미 넓힌 버튼, 한 글자·빈 번역은 건드리지 않는다
            if not c or s.get('button_widened_px') or len(s['tr'].strip()) < 2:
                continue
            # 오른쪽 끝에서 잘린 버튼, 또는 이미지 끝에 붙어 있어 넓힐 자리가 없어 글자가 85% 미만으로 줄어든 버튼
            cut = c['x1'] >= W - 1
            if not cut and not (c['x1'] >= W - 1 - 4 * hh and s.get('scale', 1) < 0.85):
                continue
            hits.append((s, c, (x, y, w, hh), cut))
        if not hits:
            continue
        tr = tr0.copy()
        new_right = W   # 필요한 새 이미지 폭
        jobs = []
        for s, c, (x, y, w, hh), cut in hits:
            # 번역 글자 범위(글자 띠에서 달라진 열) 지우기
            ry0, ry1 = max(c['y0'], y - 3), min(c['y1'], y + hh + 3) + 1
            cols = np.where(diff[ry0:ry1, c['x0']:].any(0))[0] + c['x0']
            ex0 = min(x, cols.min()) - 1 if len(cols) else x - 1
            ex1 = W if cut else c['x1'] + 1
            rows = np.where(diff[ry0:ry1, ex0:].any(1))[0]
            ey0 = min(y, ry0 + rows.min()) - 1 if len(rows) else y - 1
            ey1 = max(y + hh, ry0 + rows.max() + 1) + 1 if len(rows) else y + hh + 1
            sub = tr0[ey0:ey1, ex0:ex1]
            dd = dist(sub, c['bg'])
            ink = sub[np.unravel_index(dd.argmax(), dd.shape)]
            bgc = np.round(c['bg']).astype(np.uint8)
            tr[ey0:ey1, ex0:ex1] = bgc
            # 아이콘 오른쪽 끝 = 글자 띠에서 왼쪽으로 처음 만나는 배경 아닌 열
            band = tr[max(c['y0'], ey0 - 2):min(c['y1'], ey1 + 2) + 1]
            free = (dist(band, c['bg']) < TOL_IN).all(0)
            a = ex0
            while a > c['x0'] and free[a - 1]:
                a -= 1
            full = s['font_px'] / s['scale'] * 0.9
            f = ImageFont.truetype(font_path(fdir, lang, s.get('weight', 500)), int(round(full)))
            bb = f.getbbox(s['tr']); tw = bb[2] - bb[0]
            pad_icon = max(int(0.7 * hh), 8)
            text_x = (a + pad_icon) if a > c['x0'] else ex0
            # 버튼 왼쪽 바깥 테두리 찾기(안쪽 배경에서 왼쪽으로 걸어 바깥 흰색이 나올 때까지)
            yc = (c['y0'] + c['y1']) // 2
            le = c['x0']
            while le > 0 and np.abs(tr[yc, le - 1].astype(int) - WHITE).sum() > 30:
                le -= 1
            radius = int((c['y1'] - c['y0']) / 2) + 2
            pad_right = text_x - a if a > c['x0'] else (c['x0'] - le) + pad_icon   # 아이콘 앞 여백과 비슷하게
            pad_right = max(pad_right, int(0.9 * hh))
            # 지금 버튼 오른쪽 바깥 끝(잘린 버튼은 이미지 끝)
            old_right = W
            if not cut:
                old_right = c['x1']
                while old_right < W - 1 and np.abs(tr[yc, old_right + 1].astype(int) - WHITE).sum() > 30:
                    old_right += 1
                old_right += 1
            right_edge = max(old_right, int(text_x + tw + pad_right + radius))
            margin = max(int(1.2 * hh), 24)
            new_right = max(new_right, right_edge + margin)
            jobs.append(dict(s=s, c=c, ex0=ex0, le=le, radius=radius, right_edge=right_edge, text_x=text_x, f=f, bb=bb, ink=ink,
                             cy=(ey0 + ey1) / 2, bgc=bgc))
        W2 = new_right
        out = np.empty((H, W2, 3), np.uint8); out[:] = WHITE
        out[:, :W] = tr
        for j in jobs:
            c = j['c']
            # 버튼이 차지하는 행: 왼쪽 테두리 열에서 흰색이 아닌 행
            col = out[:, j['le'] + j['radius']]
            t = c['y0']
            while t > 0 and np.abs(col[t - 1].astype(int) - WHITE).sum() > 30: t -= 1
            b = c['y1']
            while b < H - 1 and np.abs(col[b + 1].astype(int) - WHITE).sum() > 30: b += 1
            t -= 1; b += 1
            # 안쪽 열을 늘려 채우고, 왼쪽 모서리를 좌우로 뒤집어 오른쪽 끝에 붙인다
            # 지운 글자 자리의 깨끗한 열을 기준으로 삼는다(원래 이미지 끝 열은 번짐이 있어 쓰지 않음)
            x_mid = j['ex0'] + 2
            mid = out[t:b + 1, x_mid:x_mid + 1]
            out[t:b + 1, x_mid:j['right_edge']] = mid
            # 실제 모서리 폭: 버튼 윗선 바로 안쪽 행에서 가운데 열과 같아지는 지점까지(아이콘이 섞이지 않게)
            rr = min(t + 3, b)
            cwid = 0
            for k in range(0, j['radius'] * 2):
                if np.abs(out[rr, j['le'] + k].astype(int) - out[rr, x_mid].astype(int)).sum() < 20:
                    cwid = k; break
            cwid = min(max(cwid + 2, 4), j['radius'])
            corner = out[t:b + 1, j['le'] - 2:j['le'] + cwid][:, ::-1]
            cw = corner.shape[1]
            out[t:b + 1, j['right_edge'] - cw + 2:j['right_edge'] + 2] = corner
            # 글자 쓰기
            im = Image.fromarray(out)
            capb = j['f'].getbbox('H')
            top = j['cy'] - (capb[1] + capb[3]) / 2
            ImageDraw.Draw(im).text((j['text_x'] - j['bb'][0], top), j['s']['tr'], font=j['f'], fill=tuple(int(v) for v in j['ink']))
            out = np.asarray(im).copy()
            s = j['s']
            full = s['font_px'] / s['scale']
            s['font_px'] = round(full * 0.9, 1); s['scale'] = 0.9; s['flag'] = ''
            s['button_completed'] = True
            log.append(f'{vol}/{lang}/{name}\t{s["tr"]}\t{W}→{W2}px')
        info['output_px'] = [W2, H]
        info['right_margin_added_px'] = W2 - W
        if 'flags' in info:
            ids = {x['id']: x for x in info['segments']}
            info['flags'] = [ids.get(x['id'], x) for x in info['flags'] if ids.get(x['id'], x).get('flag')]
        # HTML: 이 이미지의 imgbox 비율과 번호 위치(폭 기준 %)를 새 폭에 맞춘다
        k = W / W2
        def fix(m):
            blk = m.group(0)
            blk = re.sub(r'aspect-ratio:[\d.]+', f'aspect-ratio:{W2 / H:.5f}', blk, count=1)
            blk = re.sub(r'calc\(([\d.]+)% - 11px\)', lambda q: f'calc({float(q.group(1)) * k:.3f}% - 11px)', blk)
            return blk
        html, n = re.subn(r'<div class="imgbox"[^>]*><img src="img/' + re.escape(name) + r'".*?</div>', fix, html, flags=re.S)
        if sheet_dir:
            os.makedirs(sheet_dir, exist_ok=True)
            y0 = max(0, min(j['c']['y0'] for j in jobs) - 60); y1 = min(H, max(j['c']['y1'] for j in jobs) + 60)
            a = tr0[y0:y1, W - 700:]; b = out[y0:y1, W - 700:]
            a = np.pad(a, ((0, 0), (0, b.shape[1] - a.shape[1]), (0, 0)), constant_values=200)
            Image.fromarray(np.concatenate([a, np.full((8, b.shape[1], 3), 120, np.uint8), b], 0)).save(os.path.join(sheet_dir, f'{vol}_{lang}_{name}'))
        if not dry:
            Image.fromarray(out).save(tp, optimize=True)
    if not dry:
        json.dump(man, open(mf, 'w'), ensure_ascii=False, indent=1)
        open(hp, 'w').write(html)


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
    print('\n'.join(log)); print('total', len(log))
