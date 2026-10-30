"""번역본 캡처에 한글이 남았는지 OCR(한국어 우선)로 검사한다 (고정 프롬프트 11절).
한글이 잡힌 자리의 픽셀을 한국어판과 비교해, 픽셀이 그대로면 실제로 남은 한국어(실패), 바뀌었으면 번역 글자·아이콘 오인식(통과)으로 본다.
사용: python3 template/check_img_hangul.py <분권> <lang> [--ocr-bin 경로]   → manuals/<분권>/<lang>/img/hangul_check.json, 종료 코드 1이면 실패
"""
import json, re, sys, os, subprocess, argparse
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
ap = argparse.ArgumentParser(); ap.add_argument('vol'); ap.add_argument('lang'); ap.add_argument('--ocr-bin', default=os.environ.get('IMG_OCR_BIN', ''))
a = ap.parse_args()
V = f'{ROOT}/manuals/{a.vol}'; TR = f'{V}/{a.lang}/img'; KO = f'{V}/ko/img'
HAN = re.compile('[가-힣ㄱ-ㅎㅏ-ㅣ]')
files = sorted(f for f in os.listdir(TR) if re.match(r's\d+_\d+_\d+\.png$', f))
cmd = ([a.ocr_bin] if a.ocr_bin else ['swift', f'{HERE}/img_ocr.swift']) + ['--lang', 'ko'] + [f'{TR}/{f}' for f in files]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode: sys.exit(r.stderr)
fails = []; fp = []
for d in json.loads(r.stdout):
    hits = [it for it in d['items'] if HAN.search(it['t'])]
    if not hits: continue
    ko = np.asarray(Image.open(f'{KO}/{d["file"]}').convert('RGB')).astype(int)
    tr = np.asarray(Image.open(f'{TR}/{d["file"]}').convert('RGB')).astype(int)
    for it in hits:
        x, y, w, h = [int(round(v)) for v in it['box']]
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
        (fails if ratio < 0.15 else fp).append(rec)
json.dump({'vol': a.vol, 'lang': a.lang, 'remaining_korean': fails, 'false_positive_changed_pixels': fp}, open(f'{TR}/hangul_check.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({'vol': a.vol, 'lang': a.lang, 'images': len(files), 'remaining': len(fails), 'false_positive': len(fp)}, ensure_ascii=False))
for f_ in fails[:20]: print('  남은 한글:', f_['file'], f_['text'], f_['box'])
sys.exit(1 if fails else 0)
