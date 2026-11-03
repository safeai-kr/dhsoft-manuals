"""번역본 캡처에 한글이 남았는지 OCR(한국어 우선)로 검사한다 (고정 프롬프트 11절).
한글이 잡힌 자리의 픽셀을 한국어판과 비교해, 픽셀이 그대로면 실제로 남은 한국어(실패), 바뀌었으면 번역 글자·아이콘 오인식(통과)으로 본다.
사용: python3 template/check_img_hangul.py <분권> <lang> [--ocr-bin 경로]   → manuals/<분권>/<lang>/img/hangul_check.json, 종료 코드 1이면 실패
"""
import json, re, sys, os, subprocess, argparse
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from img_common import modal_bbox
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
ap = argparse.ArgumentParser(); ap.add_argument('vol'); ap.add_argument('lang'); ap.add_argument('--ocr-bin', default=os.environ.get('IMG_OCR_BIN', ''))
a = ap.parse_args()
V = f'{ROOT}/manuals/{a.vol}'; TR = f'{V}/{a.lang}/img'; KO = f'{V}/ko/img'
HAN = re.compile('[가-힣ㄱ-ㅎㅏ-ㅣ]')
files = sorted(f for f in os.listdir(TR) if re.match(r's\d+_\d+[a-z]?_\d+\.png$', f))
cmd = ([a.ocr_bin] if a.ocr_bin else ['swift', f'{HERE}/img_ocr.swift']) + ['--lang', 'ko'] + [f'{TR}/{f}' for f in files]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode: sys.exit(r.stderr)
fails = []; fp = []; overlay = []
# 번역 안 된 캡처: 한국어판에는 있는데 번역본에 없거나 픽셀이 같은 파일 (2026-10-30 로그인 s2_4b_1 누락)
ko_files = sorted(f for f in os.listdir(KO) if re.match(r's\d+_\d+[a-z]?_\d+\.png$', f))
untranslated = [f for f in ko_files if f not in files or open(f'{KO}/{f}', 'rb').read() == open(f'{TR}/{f}', 'rb').read()]
for d in json.loads(r.stdout):
    hits = [it for it in d['items'] if HAN.search(it['t'])]
    if not hits: continue
    ko = np.asarray(Image.open(f'{KO}/{d["file"]}').convert('RGB')).astype(int)
    tr = np.asarray(Image.open(f'{TR}/{d["file"]}').convert('RGB')).astype(int)
    mb = modal_bbox(ko)
    for it in hits:
        x, y, w, h = [int(round(v)) for v in it['box']]
        if mb and not (mb[0] <= x + w / 2 < mb[2] and mb[1] <= y + h / 2 < mb[3]):
            overlay.append({'file': d['file'], 'text': it['t'], 'box': [x, y, w, h], 'why': '모달 바깥'}); continue
        # 오른쪽에 흰 여백을 붙여 넓힌 이미지(extend_cut_buttons)는 겹치는 부분만 비교한다
        hh = min(ko.shape[0], tr.shape[0]); ww = min(ko.shape[1], tr.shape[1])
        if y >= hh or x >= ww: continue
        a_ = ko[y:min(y + h, hh), x:min(x + w, ww)]; b_ = tr[y:min(y + h, hh), x:min(x + w, ww)]
        if a_.size == 0: continue
        # 글자 픽셀(바탕과 다른 픽셀) 가운데 바뀐 비율로 본다. 상자 전체로 재면 빈 바탕이 많아 글자가 바뀌어도 '그대로'로 나온다
        bg = np.median(a_.reshape(-1, 3), 0)
        ink = (np.abs(a_ - bg).max(-1) > 40) | (np.abs(b_ - bg).max(-1) > 40)
        changed = (np.abs(a_ - b_).sum(-1) > 30)
        ratio = float(changed[ink].mean()) if ink.any() else 0.0
        rec = {'file': d['file'], 'text': it['t'], 'box': [x, y, w, h], 'changed_ink_ratio': round(ratio, 3)}
        # 반투명 덮개 뒤의 어두워진 배경 글(무채색 중간 회색 바탕 + 더 어두운 글자)은 일부러 두는 자리(img_localize.py 자동 skip)
        dim_overlay = ink.any() and 70 <= bg.mean() <= 205 and (bg.max() - bg.min()) <= 18 and a_[ink].mean() < bg.mean() - 30
        if ratio < 0.15 and dim_overlay:
            overlay.append(rec); continue
        (fails if ratio < 0.15 else fp).append(rec)
json.dump({'vol': a.vol, 'lang': a.lang, 'untranslated_images': untranslated, 'remaining_korean': fails, 'behind_overlay_kept': overlay, 'false_positive_changed_pixels': fp}, open(f'{TR}/hangul_check.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({'vol': a.vol, 'lang': a.lang, 'images': len(files), 'untranslated_images': len(untranslated), 'remaining': len(fails), 'behind_overlay': len(overlay), 'false_positive': len(fp)}, ensure_ascii=False))
for f_ in fails[:20]: print('  남은 한글:', f_['file'], f_['text'], f_['box'])
for f_ in untranslated: print('  번역 안 된 캡처:', f_)
sys.exit(1 if fails or untranslated else 0)
