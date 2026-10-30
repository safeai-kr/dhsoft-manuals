#!/usr/bin/env python3
"""번역 파일 검사. 사용: python3 check_tr.py <분권> <lang>
data/units_ko.json 의 모든 key가 data/<lang>.json 에 있고, 태그(<b> <code> <span class="ref"> <span class="lcir …">) 개수가 같고,
참조 번호 숫자가 같고(장 → Ch./Kap./章 허용), 한글이 한 글자도 없는지 확인한다."""
import json, re, sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
vol, lang = sys.argv[1], sys.argv[2]
D = f'{ROOT}/manuals/{vol}/data'
src = json.load(open(f'{D}/units_ko.json')); tr = json.load(open(f'{D}/{lang}.json'))
HANGUL = re.compile(r'[가-힣ᄀ-ᇿ㄰-㆏ꥠ-꥿ힰ-퟿]')
CH = {'en': 'Ch.', 'de': 'Kap.', 'ja': '章'}[lang]
problems = []
def tags(h): return sorted(re.findall(r'<(b|code|span class="ref"|span class="lcir[^"]*")>', h))
def refs(h): return re.findall(r'<span class="ref">([^<]*)</span>', h)
for u in src:
    k = u['key']
    if k not in tr: problems.append(f'{k}: 번역 없음'); continue
    t = tr[k]
    if not isinstance(t, str): problems.append(f'{k}: 문자열 아님'); continue
    if not t.strip():
        if u['ko'].strip(): problems.append(f'{k}: 빈 값')
        continue
    if HANGUL.search(t): problems.append(f'{k}: 한글 남음 → {t[:60]}')
    if tags(u['ko']) != tags(t): problems.append(f'{k}: 태그 다름 {tags(u["ko"])} vs {tags(t)}')
    a, b = refs(u['ko']), refs(t)
    if len(a) != len(b): problems.append(f'{k}: 참조 수 다름 {a} vs {b}')
    else:
        for x, y in zip(a, b):
            xs = re.findall(r'\d+(?:\.\d+)?', x); ys = re.findall(r'\d+(?:\.\d+)?', y)
            if xs != ys: problems.append(f'{k}: 참조 숫자 다름 {x!r} vs {y!r}')
            if '장' in x and (CH not in y and '章' not in y): problems.append(f'{k}: 장 참조 표기 {x!r} → {y!r} ({CH} 필요)')
    if re.search(r'\[확인 필요\]|\[TBD\]|\(.*?[가-힣].*?\)', t): problems.append(f'{k}: 본문에 확인 표시·원문 병기 → {t[:60]}')
extra = [k for k in tr if k not in {u['key'] for u in src}]
if extra: problems.append(f'원문에 없는 key {len(extra)}개: {extra[:5]}')
print(f'{vol} {lang}: 단위 {len(src)} 문제 {len(problems)}')
for p in problems[:60]: print('  ', p)
sys.exit(1 if problems else 0)
