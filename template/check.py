#!/usr/bin/env python3
"""HTML 자동 검사(고정프롬프트 13절). 사용: python3 check.py <분권> <lang> [--png 출력폴더]
검사: 쪽 수 · 헤더 y=0 과 헤더–첫 블록 22px · 영역 넘침 0 · 이어지는 쪽 채움 60% · 제목 끝 줄 1~3글자 0 · 참조 번호가 실제 절과 일치 · 번역본 한글 0
결과: manuals/<분권>/<lang>/checks.json"""
import json, sys, os, re
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
vol, lang = sys.argv[1], sys.argv[2]
png = sys.argv[sys.argv.index('--png') + 1] if '--png' in sys.argv else None
OUT = f'{ROOT}/manuals/{vol}/{lang}'; F = f'{OUT}/SMART-EDC_사용자매뉴얼_{vol}_{lang}.html'
if not os.path.exists(F): F = f'{OUT}/SMART-EDC_사용자매뉴얼_CRF_{vol}_{lang}.html'   # CRF 필드 분권은 파일 이름에 CRF_가 붙는다
JS = r'''() => {
  const pages = [...document.querySelectorAll('.page')];
  const r = {pages: pages.length, header: [], overflow: [], fill: [], balanced: [], refs: [], hangul: 0, badTitles: []};
  const secOf = p => p.querySelector('.hdr .ht')?.textContent;
  for (const p of pages) {
    const pr = p.getBoundingClientRect(); const no = +p.dataset.pno;
    const area = p.querySelector('.area');
    if (area && area.scrollHeight > area.clientHeight + 0.5) r.overflow.push(no);
    const hdr = p.querySelector('.hdr');
    if (hdr) {
      const hr = hdr.getBoundingClientRect(); const first = area.firstElementChild?.getBoundingClientRect();
      r.header.push({page: no, top: +(hr.top - pr.top).toFixed(2), h: +hr.height.toFixed(1), gap: first ? +(first.top - hr.bottom).toFixed(1) : null});
      // 같은 절이 다음 쪽으로 이어지는 쪽은 본문 영역의 60% 이상 차 있어야 한다(절의 마지막 쪽은 짧아도 된다)
      const sec = secOf(p); const nxt = pages[pages.indexOf(p) + 1];
      if (nxt && secOf(nxt) === sec && area.lastElementChild) {
        const ar = area.getBoundingClientRect(); const lr = area.lastElementChild.getBoundingClientRect();
        r.fill.push({page: no, fill: +((lr.bottom - ar.top) / ar.height).toFixed(3)});
      }
    }
  }
  for (const el of document.querySelectorAll('[data-balanced]')) r.balanced.push(el.dataset.balanced);
  const ids = new Set([...document.querySelectorAll('.page.body')].map(p => p.id).filter(Boolean));
  const chs = new Set([...document.querySelectorAll('.page.divider .dtitle')].map(e => e.id));
  for (const el of document.querySelectorAll('.ref')) {
    for (const t of el.textContent.split('·').map(s => s.trim())) {
      const m = t.match(/^(\d+)\.(\d+)$/); const c = t.match(/^(?:Ch\.|Kap\.|第)?\s*(\d+)\s*(?:장|章)?$/);
      const ok = m ? ids.has(`s${m[1]}-${m[2]}`) : c ? chs.has(`ch${c[1]}`) : false;
      if (!ok) r.refs.push(t);
    }
  }
  const txt = document.body.innerText + document.title;
  r.hangul = (txt.match(/[가-힣ᄀ-ᇿ㄰-㆏ꥠ-꥿ힰ-퟿]/g) || []).length;
  return r;
}'''
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    pg = b.new_page(viewport={'width': 900, 'height': 1200})
    errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto('file://' + F); pg.wait_for_function('window.__done === true', timeout=120000)
    r = pg.evaluate(JS)
    if png:
        os.makedirs(png, exist_ok=True)
        for el in pg.query_selector_all('.page'):
            el.screenshot(path=f'{png}/{vol}_{lang}_p{int(el.get_attribute("data-pno")):02d}.png', scale='css')
    b.close()
bad_top = [h['page'] for h in r['header'] if abs(h['top']) > 0.5]
bad_gap = [h['page'] for h in r['header'] if h['gap'] is None or h['gap'] < 21.5]
sparse = [x for x in r['fill'] if x['fill'] < 0.6]
checks = dict(manual=vol, lang=lang, pages=r['pages'], js_errors=errors, checks=dict(
    header_position=dict(**{'pass': not bad_top and not bad_gap}, pages=len(r['header']), bad_top=bad_top, bad_gap=bad_gap, header_heights=sorted({h['h'] for h in r['header']})),
    no_overflow={'pass': not r['overflow'], 'pages': r['overflow']},
    no_large_blank={'pass': not sparse, 'sparse': sparse, 'min_fill_mid_pages': min([x['fill'] for x in r['fill']], default=None)},
    short_last_line={'pass': all(int(x.split('→')[1]) > 3 for x in r['balanced']), 'balanced': r['balanced']},
    refs={'pass': not r['refs'], 'unresolved': r['refs']},
    no_hangul={'pass': lang == 'ko' or r['hangul'] == 0, 'count': r['hangul'], 'applies': lang != 'ko'}))
checks['pass'] = all(c['pass'] for c in checks['checks'].values()) and not errors
json.dump(checks, open(f'{OUT}/checks.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: (v if k != 'checks' else {kk: vv['pass'] for kk, vv in v.items()}) for k, v in checks.items()}, ensure_ascii=False))
