"""이미 만들어진 HTML에 SMART EDC 로고를 넣는다(표지 왼쪽 위 + 목차 머리 오른쪽). 다시 빌드하지 않는 권(CRF 분권)용.
사용: python3 template/apply_logo.py <html 파일 ...>
"""
import sys, os, shutil, re
HERE = os.path.dirname(os.path.abspath(__file__))
for f in sys.argv[1:]:
    s = open(f).read(); d = os.path.dirname(f); n = 0
    for fn in ('smart-edc-logo.png', 'smart-edc-logo-gray.png'): shutil.copy(f'{HERE}/assets/img/{fn}', f'{d}/img/{fn}')
    a = '<span class="cv-brand"><span class="sm">SMART</span> EDC</span>'
    if a in s: s = s.replace(a, '<img class="cv-brand" src="img/smart-edc-logo.png" alt="SMART EDC">'); n += 1
    b = '<span class="brand">SMART EDC</span></div><div class="area"></div>`;'
    if b in s: s = s.replace(b, '<img class="brand" src="img/smart-edc-logo-gray.png" alt="SMART EDC"></div><div class="area"></div>`;'); n += 1
    s, k = re.subn(r'\.cv-brand\{font-size:28\.5px;[^}]*\}\s*\.cv-brand \.sm\{color:#65E5D1\}', '.cv-brand{height:34px;width:auto;display:block}', s); n += k
    s, k = re.subn(r'\.toc-h \.brand\{font-size:12\.5px;[^}]*\}', '.toc-h .brand{height:22px;width:auto;display:block}', s); n += k
    open(f, 'w').write(s); print(f, n)
