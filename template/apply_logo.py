"""이미 만들어진 HTML에 2026-10-30 표지·목차·푸터 변경을 넣는다(다시 빌드하지 않는 권용. 여러 번 돌려도 같은 결과).
- 표지: 왼쪽 위 SMART EDC 로고(34px), 설명 글 16px·로고와 24px, 하단 선 1021px·글·로고 중심 1057px, DH 로고 110px
- 목차 머리 오른쪽 회색 로고 22px · 본문 푸터 로고 14px(1px 위)
- 소제목 「이 화면으로 가는 다른 길」 → 「접근 경로」(언어별 고정 표기)
사용: python3 template/apply_logo.py <html 파일 ...>
"""
import sys, os, shutil, re, json
HERE = os.path.dirname(os.path.abspath(__file__))
FIXED = json.load(open(f'{HERE}/fixed.json'))
R = [('<span class="cv-brand"><span class="sm">SMART</span> EDC</span>', '<img class="cv-brand" src="img/smart-edc-logo.png" alt="SMART EDC">'),
     ('<span class="brand">SMART EDC</span></div><div class="area"></div>`;', '<img class="brand" src="img/smart-edc-logo-gray.png" alt="SMART EDC"></div><div class="area"></div>`;'),
     ('<span class="brand">SMART EDC</span><span class="pg">', '<img class="brand" src="img/smart-edc-logo-footer.png" alt="SMART EDC"><span class="pg">'),
     ('.cv-top{position:absolute;left:56px;top:73px;display:flex;align-items:center;gap:20px}', '.cv-top{position:absolute;left:56px;top:73px;display:flex;align-items:center;gap:24px}'),
     ('.cv-sys{font-size:18px;', '.cv-sys{font-size:16px;'),
     ('.cv-bottom{position:absolute;left:56px;right:56px;top:1005px;border-top:1px solid rgba(214,227,249,.35);display:flex;justify-content:space-between;align-items:center;padding-top:16px}',
      '.cv-bottom{position:absolute;left:56px;right:56px;top:1021px;height:71px;border-top:1px solid rgba(214,227,249,.35);display:flex;justify-content:space-between;align-items:center;padding-top:0}'),
     ('.cv-logo{width:138px;height:auto}', '.cv-logo{width:110px;height:auto}'),
     ('.ftr .brand{font-weight:700;margin-right:20px}', '.ftr .brand{height:14px;width:auto;align-self:center;margin-right:20px;position:relative;top:-1px}')]
RX = [(r'\.cv-brand\{font-size:28\.5px;[^}]*\}\s*\.cv-brand \.sm\{color:#65E5D1\}', '.cv-brand{height:34px;width:auto;display:block}'),
      (r'\.toc-h \.brand\{font-size:12\.5px;[^}]*\}', '.toc-h .brand{height:22px;width:auto;display:block}')]
for f in sys.argv[1:]:
    s = open(f).read(); d = os.path.dirname(f); n = 0
    for fn in ('smart-edc-logo.png', 'smart-edc-logo-gray.png', 'smart-edc-logo-footer.png'): shutil.copy(f'{HERE}/assets/img/{fn}', f'{d}/img/{fn}')
    for a, b in R:
        if a in s: s = s.replace(a, b); n += 1
    for a, b in RX:
        s, k = re.subn(a, b, s); n += k
    # 소제목 고정 표기: 한국어판은 원문으로, 번역본은 data/<lang>.json 의 번역으로 찾는다
    lang = os.path.basename(d); vol = os.path.basename(os.path.dirname(d))
    names = {'이 화면으로 가는 다른 길'}
    dp = os.path.join(os.path.dirname(d), 'data', f'{lang}.json'); up = os.path.join(os.path.dirname(d), 'data', 'units_ko.json')
    if lang != 'ko' and os.path.exists(dp) and os.path.exists(up):
        tr = json.load(open(dp))
        for u in json.load(open(up)):
            if u['ko'] == '이 화면으로 가는 다른 길' and u['key'] in tr: names.add(tr[u['key']])
    for nm in names:
        a = f'<div class="blk tab kwn"><h3><span>{nm}</span></h3></div>'
        if a in s and lang in FIXED: s = s.replace(a, f'<div class="blk tab kwn"><h3><span>{FIXED[lang]["접근 경로"]}</span></h3></div>'); n += 1
    open(f, 'w').write(s); print(f, n)
