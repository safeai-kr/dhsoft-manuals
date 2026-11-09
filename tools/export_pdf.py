"""분권 HTML → 화면용 RGB PDF(sRGB 선언) · 인쇄용 CMYK PDF(216×303mm, 재단 여백 3mm, DeviceCMYK).
사용:
  python3 tools/export_pdf.py <html> <out_rgb.pdf> [--cmyk <out_cmyk.pdf>]
  python3 tools/export_pdf.py --all <출력폴더> [en de ja ...]   (manuals/*/<lang>/ 전 권을 <출력폴더>/<lang>/ 에 RGB로)
화면용: Chrome tagged PDF(책갈피 포함) → pdf_srgb.py 로 모든 RGB를 sRGB 하나로 읽게 선언(DefaultRGB · OutputIntent).
인쇄용: 화면용 PDF → pdf_cmyk_print.py 로 재단 여백·재단선·TrimBox를 붙이고 DeviceCMYK로 변환."""
import sys, os, glob, subprocess, tempfile
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from pdf_srgb import fix as to_srgb
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

def clean_outline(pdf_path, html):
    """Chrome이 만든 책갈피를 손본다(2026-11-09, 검사패널 v107 검토).
    - 절 번호와 제목 사이 띄어쓰기: 「1.1필드」 → 「1.1 필드」
    - 줄바꿈으로 붙은 낱말: 「2축구성과」처럼 공백이 빠진 제목은 HTML 원문 글자로 되돌린다
    - 제목 단계는 HTML의 h1~h4를 따른다(이어지는 쪽에서 Chrome이 단계를 당겨 넣는 것을 되돌림)
    - 한 절이 여러 쪽에 걸쳐 같은 항목이 잇달아 들어가면 첫 항목만 남긴다
    - 메타데이터의 Chrome 이름(Creator·Producer)을 지운다"""
    import re, html as H, pymupdf
    src = open(html, encoding='utf-8').read()
    texts = {re.sub(r'\s+', ' ', H.unescape(t)).strip() for t in re.findall(r'>([^<>]{2,300})<', src)}
    nospace = {t.replace(' ', ''): t for t in texts}
    # 제목 단계는 HTML 태그(h1~h4)를 따른다. Chrome은 윗단계 제목이 없는 쪽(이어지는 쪽)에서 단계를 당겨 넣는다
    hlv = {re.sub(r'<[^>]+>|\s+', '', H.unescape(m.group(2))): int(m.group(1)) for m in re.finditer(r'<h([1-6])[^>]*>(.*?)</h\1>', src, re.S)}
    doc = pymupdf.open(pdf_path); out = []; last = {}; prev = 0
    for lvl, title, page, *rest in doc.get_toc(simple=False):
        lvl = max(1, min(hlv.get(re.sub(r'\s+', '', title), lvl), prev + 1))
        t = re.sub(r'\s+', ' ', title).strip()
        m = re.match(r'^(\d+(?:\.\d+)+)\s*(.*)$', t)
        num, body = (m.group(1), m.group(2)) if m else ('', t)
        if body not in texts and body.replace(' ', '') in nospace: body = nospace[body.replace(' ', '')]
        t = f'{num} {body}' if num else body
        if last.get(lvl) == t: continue          # 같은 부모 아래 잇단 같은 항목
        last[lvl] = t
        for k in [k for k in last if k > lvl]: del last[k]
        out.append([lvl, t, page] + rest); prev = lvl
    doc.set_toc(out)
    meta = doc.metadata; meta.update(creator='', producer=''); doc.set_metadata(meta)
    doc.saveIncr() if doc.can_save_incrementally() else None
    doc.close()

def export(browser, html, out_rgb):
    pg = browser.new_page(viewport={'width': 900, 'height': 1200})
    pg.goto('file://' + os.path.abspath(html)); pg.wait_for_function('window.__done === true', timeout=180000)
    raw = tempfile.mktemp(suffix='.pdf')
    pg.pdf(path=raw, prefer_css_page_size=True, print_background=True, tagged=True, outline=True); pg.close()
    os.makedirs(os.path.dirname(os.path.abspath(out_rgb)), exist_ok=True)
    to_srgb(raw, out_rgb); os.remove(raw); clean_outline(out_rgb, html)

if __name__ == '__main__':
    a = sys.argv[1:]
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME)
        if a[0] == '--all':
            out, langs = a[1], a[2:] or ['en', 'de', 'ja']
            for l in langs:
                for h in sorted(glob.glob(f'{ROOT}/manuals/*/{l}/SMART-EDC_*_{l}.html')):
                    dst = f'{out}/{l}/' + os.path.basename(h)[:-5] + '.pdf'; export(b, h, dst); print(l, os.path.basename(dst), flush=True)
        else:
            export(b, a[0], a[1]); print('rgb', a[1])
        b.close()
    if '--cmyk' in a:
        rgb = a[1]; cm = a[a.index('--cmyk') + 1]
        subprocess.run([sys.executable, '-W', 'ignore', f'{HERE}/pdf_cmyk_print.py', rgb, cm], check=True)
