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

def export(browser, html, out_rgb):
    pg = browser.new_page(viewport={'width': 900, 'height': 1200})
    pg.goto('file://' + os.path.abspath(html)); pg.wait_for_function('window.__done === true', timeout=180000)
    raw = tempfile.mktemp(suffix='.pdf')
    pg.pdf(path=raw, prefer_css_page_size=True, print_background=True, tagged=True, outline=True); pg.close()
    os.makedirs(os.path.dirname(os.path.abspath(out_rgb)), exist_ok=True)
    to_srgb(raw, out_rgb); os.remove(raw)

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
