"""번역본 캡처에서 글자를 덮은 자리의 색이 주변 바탕과 어긋나 얼룩(울퉁불퉁한 테두리)이 생겼는지 검사한다 (고정 프롬프트 11절).
한국어판과 번역본을 비교해 바뀐 픽셀 덩어리마다, 덩어리 안의 번역 글자 잉크를 뺀 '덮은 바탕' 색과 덩어리 바로 바깥 테두리 색을 비교한다.
차이가 큰 자리(RGB 합 차 24 이상, 덩어리 폭·높이 8px 이상)는 얼룩으로 본다.
사용: python3 template/check_img_patch.py <분권> <lang>   → manuals/<분권>/<lang>/img/patch_check.json, 종료 코드 1이면 얼룩 있음
"""
import json, re, sys, os
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from img_common import modal_bbox
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
vol, lang = sys.argv[1], sys.argv[2]
V = f'{ROOT}/manuals/{vol}'; TR = f'{V}/{lang}/img'; KO = f'{V}/ko/img'
files = sorted(f for f in os.listdir(TR) if re.match(r's\d+_\d+[a-z]?_\d+\.png$', f))
bad = []
for f in files:
    ko = np.asarray(Image.open(f'{KO}/{f}').convert('RGB')).astype(int)
    tr = np.asarray(Image.open(f'{TR}/{f}').convert('RGB')).astype(int)
    h = min(ko.shape[0], tr.shape[0]); w = min(ko.shape[1], tr.shape[1]); ko = ko[:h, :w]; tr = tr[:h, :w]
    changed = np.abs(ko - tr).sum(-1) > 20
    # 모달 화면에서 모달 바깥이 바뀌었으면 얼룩이다 (2026-11-03 방문정의 1.2 ja: 넓힌 버튼의 회색이 모달 밖으로 나감)
    mb = modal_bbox(ko)
    if mb:
        outside = changed.copy(); outside[mb[1]:mb[3], mb[0]:mb[2]] = False
        if outside.sum() >= 30:
            ys, xs = np.where(outside)
            bad.append({'file': f, 'box': [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)], 'pixels': int(outside.sum()), 'kind': '모달 바깥 변경'})
    lab, n = ndimage.label(ndimage.binary_dilation(changed, iterations=3))
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        y0, y1 = sl[0].start, sl[0].stop; x0, x1 = sl[1].start, sl[1].stop
        if y1 - y0 < 12 or x1 - x0 < 12: continue
        box = tr[y0:y1, x0:x1]
        # 덮은 바탕색: 덩어리 안에서 가장 흔한 색 (번역 글자 잉크는 적어서 빠진다)
        q = (box.reshape(-1, 3) // 6); keys = q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2]
        vals, cnt = np.unique(keys, return_counts=True); fill = box.reshape(-1, 3)[keys == vals[cnt.argmax()]].mean(0)
        # 바로 바깥 테두리(2px 띠)의 중앙값. 이미지 끝에 닿은 쪽은 뺀다
        ring = []
        if y0 >= 2: ring.append(tr[y0 - 2:y0, x0:x1].reshape(-1, 3))
        if y1 + 2 <= h: ring.append(tr[y1:y1 + 2, x0:x1].reshape(-1, 3))
        if x0 >= 2: ring.append(tr[y0:y1, x0 - 2:x0].reshape(-1, 3))
        if x1 + 2 <= w: ring.append(tr[y0:y1, x1:x1 + 2].reshape(-1, 3))
        if not ring: continue
        ring = np.concatenate(ring)
        # 테두리 가운데 '덮은 바탕색에 가까운 픽셀'이 하나도 없는 띠가 있으면 얼룩. 테두리 전체가 아니라 띠별로 본다 (한쪽이 선·글자에 닿을 수 있다)
        sides = []
        if y0 >= 2: sides.append(tr[y0 - 2:y0, x0:x1].reshape(-1, 3))
        if y1 + 2 <= h: sides.append(tr[y1:y1 + 2, x0:x1].reshape(-1, 3))
        if x0 >= 2: sides.append(tr[y0:y1, x0 - 2:x0].reshape(-1, 3))
        if x1 + 2 <= w: sides.append(tr[y0:y1, x1:x1 + 2].reshape(-1, 3))
        off = 0
        for s_ in sides:
            d = np.abs(s_ - fill).sum(-1)
            # 띠의 절반 이상이 덮은 색과 24 이상 다르고, 그 띠가 한 가지 색(선·글자가 아니라 바탕)이면 어긋난 것
            if (d >= 24).mean() > 0.5 and (np.abs(s_ - np.median(s_, 0)).sum(-1) < 12).mean() > 0.7: off += 1
        # 한국어판에서도 그 자리가 같은 색(버튼·칩을 넓힌 자리)이면 얼룩이 아니다
        kfill = ko[y0:y1, x0:x1]; kq = (kfill.reshape(-1, 3) // 6); kk = kq[:, 0] * 10000 + kq[:, 1] * 100 + kq[:, 2]
        kv, kc = np.unique(kk, return_counts=True); kdom = kfill.reshape(-1, 3)[kk == kv[kc.argmax()]].mean(0)
        kfrac = (np.abs(kfill - fill).sum(-1) < 24).mean()   # 그 색이 한국어판 같은 자리에 이미 10% 이상 있었으면(칩·버튼을 넓힌 자리) 얼룩이 아니다
        if off and np.abs(kdom - fill).sum() >= 24 and kfrac < 0.1:
            bad.append({'file': f, 'box': [int(x0), int(y0), int(x1 - x0), int(y1 - y0)], 'fill': [int(v) for v in fill], 'off_sides': off, 'kind': '덮은 색 어긋남'})
        # 글자가 사라진 자리: 한국어판에는 글자(바탕과 40 넘게 다른 픽셀 3% 이상)가 있었는데 번역본의 같은 자리에 아무 글자도 없으면(0.3% 이하) 덮기만 하고 안 쓴 것이다
        # (2026-11-03 빈 버튼 41곳, 넓힌 버튼이 옆 글자를 덮은 경우)
        kq2 = ko[y0:y1, x0:x1]; kb = np.median(kq2.reshape(-1, 3), 0); tb = np.median(box.reshape(-1, 3), 0)
        kink = (np.abs(kq2 - kb).max(-1) > 40).mean()
        # 번역 글자는 같은 줄에서 좌우로 옮겨 그려질 수 있으니(가운데 정렬 두 줄 → 왼쪽 정렬) 덩어리 폭만큼 양옆을 넓혀 잰다
        ex0, ex1 = max(0, x0 - (x1 - x0)), min(w, x1 + (x1 - x0)); tbox = tr[y0:y1, ex0:ex1]
        tink = (np.abs(tbox - np.median(tbox.reshape(-1, 3), 0)).max(-1) > 40).mean()
        if kink >= 0.03 and tink <= 0.003 and (y1 - y0) >= 14:
            bad.append({'file': f, 'box': [int(x0), int(y0), int(x1 - x0), int(y1 - y0)], 'ko_ink': round(float(kink), 3), 'kind': '덮은 자리 글자 사라짐'})
        # 지워진 가로선: 한국어판에서 덩어리 좌우 바깥까지 이어지던 선이 번역본의 덩어리 안에서 사라졌으면 잡는다 (입력칸 테두리)
        for y in range(y0, y1):
            if x0 < 12 or x1 + 12 > w: continue
            kl = np.abs(ko[y, x0 - 12:x0] - ko[y - 3, x0 - 12:x0]).max(-1) > 40 if y >= 3 else np.zeros(12, bool)
            kr = np.abs(ko[y, x1:x1 + 12] - ko[y - 3, x1:x1 + 12]).max(-1) > 40 if y >= 3 else np.zeros(12, bool)
            if kl.mean() < 0.9 or kr.mean() < 0.9: continue
            kin = np.abs(ko[y, x0:x1] - ko[y - 3, x0:x1]).max(-1) > 40; tin = np.abs(tr[y, x0:x1] - tr[y - 3, x0:x1]).max(-1) > 40
            if kin.mean() > 0.8 and tin.mean() < 0.5:
                bad.append({'file': f, 'box': [int(x0), int(y), int(x1 - x0), 1], 'kind': '가로선 지워짐'}); break
json.dump({'vol': vol, 'lang': lang, 'patches_off': bad}, open(f'{TR}/patch_check.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({'vol': vol, 'lang': lang, 'images': len(files), 'patches_off': len(bad)}, ensure_ascii=False))
for b in bad[:15]: print('  얼룩:', b['kind'], b['file'], b['box'], b.get('fill', ''))
sys.exit(1 if bad else 0)
