"""캡처 글자 번역(i18n/image_<lang>.json) 검사: 빠진 키, 한글 잔존, 빈 값, 비문자열, 같은 원문 다른 번역(본문 용어집과 어긋남).
사용: python3 template/check_img_tr.py <분권> [en de ja]
"""
import json, re, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
vol = sys.argv[1]; langs = sys.argv[2:] or ['en', 'de', 'ja']
V = f'{ROOT}/manuals/{vol}'
HAN = re.compile('[가-힣ㄱ-ㅎㅏ-ㅣ]')
strings = json.load(open(f'{V}/img/loc/strings_ko.json'))
need = {s['ko'] for s in strings}
rc = 0
for lang in langs:
    p = f'{V}/i18n/image_{lang}.json'
    probs = []
    if not os.path.exists(p):
        print(f'{vol} {lang}: 파일 없음'); rc = 1; continue
    try: tr = json.load(open(p))
    except Exception as e:
        print(f'{vol} {lang}: JSON 오류 {e}'); rc = 1; continue
    for k in sorted(need):
        if k not in tr: probs.append(f'빠짐: {k}'); continue
        t = tr[k]
        if not isinstance(t, str): probs.append(f'문자열 아님: {k}'); continue
        if not t.strip(): probs.append(f'빈 값: {k}'); continue
        if HAN.search(t): probs.append(f'한글 남음: {k} → {t}')
    # 용어집과 어긋남 (볼륨 용어집에 같은 ko가 있는데 번역이 다르면)
    gp = f'{V}/i18n/glossary_{lang}.json'
    if os.path.exists(gp):
        g = {e['ko']: e['tr'] for e in json.load(open(gp)) if isinstance(e, dict) and 'ko' in e}
        for k in sorted(need):
            if k in g and k in tr and isinstance(tr[k], str) and g[k].strip().lower() != tr[k].strip().lower():
                probs.append(f'용어집과 다름: {k} → 캡처 {tr[k]} / 용어집 {g[k]}')
    for pr in probs[:40]: print(f'  {pr}')
    print(f'{vol} {lang}: 문제 {len(probs)} (원문 {len(need)}개)')
    rc = rc or (1 if probs else 0)
sys.exit(rc)
