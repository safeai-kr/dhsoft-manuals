#!/usr/bin/env python3
"""index.html 의 「화면별 사용자 매뉴얼」 표를 분권별 checks.json 으로 다시 쓴다. 사용: python3 index_update.py"""
import json, os, re, html as H
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
ORDER = ['로그인', '내계정', '플랫폼관리', '워크스페이스', '프로젝트', '참여기관', '기관관리', '사용자관리', 'SAE통보_권한관리',
         '방문정의', '배정', '피험자', '데이터입력', 'Query', 'AE지정', 'Lock', 'AuditTrail', '데이터내보내기']
LANGS = [('ko', '한국어'), ('en', 'English'), ('de', 'Deutsch'), ('ja', '日本語')]
rows = ''
for vol in ORDER:
    m = json.load(open(f'{ROOT}/manuals/{vol}/data/model.json'))
    title = [l for l in m['pages'][0]['lines'] if l.strip() not in ('SMART', 'EDC')][1].strip()
    cells = ''
    for lang, label in LANGS:
        f = f'{ROOT}/manuals/{vol}/{lang}/SMART-EDC_사용자매뉴얼_{vol}_{lang}.html'
        c = f'{ROOT}/manuals/{vol}/{lang}/checks.json'
        if os.path.exists(f) and os.path.exists(c):
            pages = json.load(open(c))['pages']
            cells += f'<td><a href="manuals/{vol}/{lang}/SMART-EDC_사용자매뉴얼_{vol}_{lang}.html"><em>{label}</em><span>{pages}쪽</span></a></td>'
        else:
            cells += f'<td><a aria-disabled="true"><em>{label}</em><span>준비 중</span></a></td>'
    rows += f'<tr><th>{H.escape(title)}</th>{cells}</tr>\n'
table = ('<!-- screen-manuals:start -->\n<h2>화면별 사용자 매뉴얼</h2>\n<table>\n<thead><tr><th>분권</th><th>한국어</th><th>English</th><th>Deutsch</th><th>日本語</th></tr></thead>\n<tbody>\n'
         + rows + '</tbody>\n</table>\n<!-- screen-manuals:end -->')
P = f'{ROOT}/index.html'; s = open(P).read()
if '<!-- screen-manuals:start -->' in s:
    s = re.sub(r'<!-- screen-manuals:start -->.*?<!-- screen-manuals:end -->', lambda _: table, s, flags=re.S)
else:
    s = s.replace('<table>\n<thead><tr><th>분권</th>', '<h2>CRF 필드 타입별 매뉴얼</h2>\n<table>\n<thead><tr><th>분권</th>', 1)
    s = s.replace('</table>\n</div></main>', '</table>\n' + table + '\n</div></main>', 1)
    s = s.replace('<h1><b>SMART</b> EDC · CRF 필드 타입별 사용자 매뉴얼</h1>', '<h1><b>SMART</b> EDC · 사용자 매뉴얼</h1>', 1)
    s = s.replace('td a{display:flex;', 'h2{font-size:18px;font-weight:700;letter-spacing:-0.02em;margin:0 0 12px}\ntable+h2{margin-top:40px}\ntd a[aria-disabled]{color:#A3ADBF;cursor:default}td a[aria-disabled] span{color:#A3ADBF;text-decoration:none}td a[aria-disabled]:hover{background:none}\ntd a{display:flex;', 1)
open(P, 'w').write(s)

# README: 「현재 올라간 것」 아래에 화면별 분권 표 (배포 주소 링크)
from urllib.parse import quote
BASE = 'https://safeai-kr.github.io/dhsoft-manuals/'
md = '<!-- screen-manuals:start -->\n### 화면별 사용자 매뉴얼 (18개 분권)\n\n| 분권 | 한국어 | 영어 | 독일어 | 일본어 |\n| --- | --- | --- | --- | --- |\n'
for vol in ORDER:
    m = json.load(open(f'{ROOT}/manuals/{vol}/data/model.json'))
    title = [l for l in m['pages'][0]['lines'] if l.strip() not in ('SMART', 'EDC')][1].strip()
    cells = []
    for lang, label in LANGS:
        rel = f'manuals/{vol}/{lang}/SMART-EDC_사용자매뉴얼_{vol}_{lang}.html'
        cells.append(f'[{label}]({BASE}{quote(rel)})' if os.path.exists(f'{ROOT}/{rel}') and os.path.exists(f'{ROOT}/manuals/{vol}/{lang}/checks.json') else '준비 중')
    md += f'| {title} | ' + ' | '.join(cells) + ' |\n'
md += '<!-- screen-manuals:end -->'
R = f'{ROOT}/README.md'; r = open(R).read()
if '<!-- screen-manuals:start -->' in r:
    r = re.sub(r'<!-- screen-manuals:start -->.*?<!-- screen-manuals:end -->', lambda _: md, r, flags=re.S)
else:
    r = r.replace('## 보는 법', md + '\n\n## 보는 법', 1)
open(R, 'w').write(r)
print('index.html + README updated', len(ORDER), 'rows')
