"""번역본 캡처 눈 검토용 시트: 한국어판과 번역본을 위아래로 붙여 한 장씩 만든다 (고정 프롬프트 11절, 2026-10-30).
사용: python3 template/img_review_sheets.py <lang> <출력 폴더> [분권 ...]
출력: <출력 폴더>/<분권>_<파일>.png  (위 한국어, 아래 번역본, 폭 1400px 안으로 줄임)
"""
import os, re, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
lang, out = sys.argv[1], sys.argv[2]
vols = sys.argv[3:] or sorted(v for v in os.listdir(f'{ROOT}/manuals') if os.path.isdir(f'{ROOT}/manuals/{v}/{lang}/img'))
os.makedirs(out, exist_ok=True); n = 0
for v in vols:
    KO = f'{ROOT}/manuals/{v}/ko/img'; TR = f'{ROOT}/manuals/{v}/{lang}/img'
    for f in sorted(x for x in os.listdir(TR) if re.match(r's\d+_\d+[a-z]?_\d+\.png$', x)):
        a = Image.open(f'{KO}/{f}').convert('RGB'); b = Image.open(f'{TR}/{f}').convert('RGB')
        W = max(a.width, b.width); sc = min(1.0, 1400 / W)
        a = a.resize((int(a.width * sc), int(a.height * sc)), Image.LANCZOS); b = b.resize((int(b.width * sc), int(b.height * sc)), Image.LANCZOS)
        S = Image.new('RGB', (max(a.width, b.width), a.height + b.height + 40), (255, 80, 80))
        S.paste(a, (0, 20)); S.paste(b, (0, a.height + 40))
        ImageDraw.Draw(S).text((6, 4), f'{v} / {f}  위: ko  아래: {lang}', fill=(255, 255, 255))
        S.save(f'{out}/{v}_{f}'); n += 1
print('sheets', n)
