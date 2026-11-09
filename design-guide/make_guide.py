"""SMART EDC 사용자 매뉴얼 디자인 가이드(제출용 PDF)를 만든다 (2026-11-09, hy0909).

만드는 것
  design-guide/SMART-EDC_매뉴얼_디자인_가이드.html        가이드 HTML (쪽마다 A4 + 재단 여백 3mm = 216×303mm)
  design-guide/SMART-EDC_매뉴얼_디자인_가이드_RGB.pdf     Chrome으로 찍은 화면용 PDF
  design-guide/SMART-EDC_매뉴얼_디자인_가이드_CMYK.pdf    모든 색을 DeviceCMYK로 바꾼 인쇄용 PDF (PyMuPDF recolor)
  design-guide/preview/p*.png                            확인용 쪽 그림
사용: python3 design-guide/make_guide.py
"""
import asyncio, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, f'{ROOT}/template')

DATE = '2026-11-09'
VER = '템플릿 v6 · 2026-11-09'


def cmyk(hexv):
    """RGB → CMYK(검정 분리 K = min). 인쇄 참고값이며, 최종 인쇄소 프로파일로 다시 맞춘다."""
    h = hexv.lstrip('#'); r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    k = 1 - max(r, g, b)
    if k >= 0.999: return (0, 0, 0, 100)
    c = (1 - r - k) / (1 - k); m = (1 - g - k) / (1 - k); y = (1 - b - k) / (1 - k)
    return tuple(int(round(v * 100)) for v in (c, m, y, k))


def rgb(hexv):
    h = hexv.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


COLORS = [
    ('표지 바탕', 'cover-bg', '#071426', '표지·뒤표지 바탕'),
    ('목차 헤더', 'toc-header', '#0B1B3A', '목차 쪽 윗띠'),
    ('본문 헤더 덧색', 'header-tint', '#102B72', '웨이브 이미지 위 그라데이션 (92% → 55% → 24%)'),
    ('간지 바탕', 'divider-bg', '#EFF1FA', '장 간지 바탕'),
    ('간지 번호·막대', 'divider-accent', '#45517E', '큰 장 번호, 오른쪽 세로 막대'),
    ('간지 제목', 'divider-title', '#15233A', '간지 큰 제목'),
    ('목차 장 번호', 'toc-number', '#3349CA', '목차 큰 장 번호(800)'),
    ('번호 원 설정', 'marker-set', '#3C55EB', '화면 위 설정 번호 채움, 결과 번호 테두리·숫자 (hy0909 결정 2026-10-30)'),
    ('번호 원 참고', 'marker-note', '#64748B', '참고 번호 채움'),
    ('결과 설명 글', 'result-text', '#1D4ED8', '결과 항목 앞 기호와 결과 설명 (원본 색 그대로)'),
    ('결과 설명 진한 글', 'result-dark', '#1E3A8A', '결과 설명 강조'),
    ('본문 글', 'text', '#202630', '본문 기본 글자'),
    ('강조 글', 'text-strong', '#111B2B', '굵은 글자, 표 안 강조'),
    ('보조 글', 'text-muted', '#475569', '표 첫 열, 카드 본문, 참고 카드 제목'),
    ('경로 글', 'path-text', '#64748B', '경로 항목'),
    ('경로 바탕', 'path-bg', '#EEF1FB', '경로 상자'),
    ('소제목 탭', 'tab', '#191F29', '소제목 탭 채움과 밑선'),
    ('캡처 틀 바탕', 'fig-bg', '#F6F7F9', '화면 캡처 둘레'),
    ('표 머리 바탕', 'table-head', '#EDF0F5', '표 머리글 칸'),
    ('표 구분선', 'table-line', '#DCE1E8', '표 행 사이 선'),
    ('구분선', 'line', '#E2E8F0', '목차·범례 선, 상자 테두리'),
    ('참조 번호', 'ref', '#5268B5', '본문 안 위첨자 참조'),
    ('키값 글·바탕', 'code', '#202F86', '코드 강조 글자 (바탕 #F1F3FE)'),
    ('필수 확인 카드', 'card-must', '#FDF2F3', '바탕. 제목 #B91C1C, 강조 바탕 #F6DCDE'),
    ('오해하기 쉬운 동작 카드', 'card-misc', '#FEF9F0', '바탕. 제목 #885910, 강조 바탕 #FCE8BF'),
    ('참고 카드', 'card-note', '#F1F5F9', '바탕. 제목 #475569, 강조 바탕 #E2E8F0'),
    ('유의사항 빨강', 'notice-red', '#B91C1C', '유의사항 글씨 빨강 (원본 색)'),
    ('푸터 글', 'footer', '#8C96A8', '푸터 장 제목, 쪽번호, 푸터 로고'),
]

TYPO = [
    ('표지 제목', '82.5px / 61.9pt', '800', '#FFFFFF', '100px', '-3%'),
    ('표지 분류 문구', '28.5px / 21.4pt', '700', '#A6B5FF', '36px', '-3%'),
    ('표지 보조 설명', '20px / 15pt', '400', '#DCE5F1', '26px', '-3%'),
    ('목차 제목', '33.5px / 25.1pt', '700', '#FFFFFF', '40px', '-3%'),
    ('목차 장 제목 · 번호', '16px / 12pt', '700 · 800', '#111B2B · #3349CA', '24px', '-3%'),
    ('목차 항목', '15.5px / 11.6pt', '400 (번호 700)', '#263341 (번호 #94A3B8)', '24px', '-3%'),
    ('간지 큰 번호', '99.6px / 74.7pt', '800', '#45517E', '1.2', '-3%'),
    ('간지 제목', '52px / 39pt', '700', '#15233A', '1.25', '-3%'),
    ('간지 목록', '18.5px / 13.9pt', '400 (번호 16.5px 700)', '#26374B (번호 #94A3B8)', '1.3', '-3%'),
    ('본문 헤더 제목', '31.5px / 23.6pt', '700', '#FFFFFF (번호 #B6C1D2)', '44px', '-3%'),
    ('경로', '12.5px / 9.4pt', '400 (라벨 700)', '#64748B (라벨 #6B7689)', '19.33px', '0'),
    ('소제목 탭', '17px / 12.8pt', '700', '#FFFFFF', '23px', '-3%'),
    ('개요 · 번호 설명', '14.5px / 10.9pt', '400 (강조 700)', '#202630 · #111B2B', '1.5 · 1.55', '-3%'),
    ('캡션', '12px / 9pt', '400', '#475364', '1.45', '0'),
    ('유의사항 카드 제목 · 본문', '14.5px · 13.5px', '700 · 500', '카드별 · #475569', '20px · 1.52', '-3%'),
    ('표 머리 · 표 본문', '12px · 13.5px', '700 · 400', '#263341', '1.45', '0'),
    ('참조 번호', '10.5px / 7.9pt', '700', '#5268B5', '0 (위첨자 3px)', '0'),
    ('푸터', '12.5px / 9.4pt', '400', '#8C96A8', '19px', '0'),
]

SPACING = [
    ('쪽 크기', '210 × 297mm (A4). CSS 794 × 1123px, 1px = 0.75pt'),
    ('재단 여백(인쇄)', '사방 3mm. 인쇄 PDF는 216 × 303mm, 재단선은 여백 모서리에 표시'),
    ('좌우 여백', '56px ≈ 14.8mm. 표지·목차·간지·본문·푸터 모두 같다'),
    ('안전 영역', '재단선 안쪽 5mm 안에는 글자를 두지 않는다. 좌우 여백 14.8mm와 본문 위아래 여백이 이를 채운다'),
    ('본문 헤더', '한 줄 98px(위 38 + 줄 44 + 아래 16). 제목이 길면 줄 수만큼 커지고 아래 내용이 함께 내려간다'),
    ('본문 영역', '헤더 아래끝 + 22px부터 푸터 위(쪽 아래 84px)까지'),
    ('푸터', '쪽 위 1064px, 왼쪽 상위 장 제목, 오른쪽 로고(높이 14px) + 20px + 쪽번호. 선은 긋지 않는다'),
    ('모서리', '카드·경로·캡처 틀 8px. 소제목 탭은 위 두 모서리만 8px'),
    ('소제목 탭 간격', '위 40px(경로 다음은 38px), 아래 12px'),
    ('유의사항 카드', '안쪽 14 / 14.7 / 15px, 카드 사이 7.33px, 제목↔본문 6px, 항목 사이 4px'),
    ('번호 설명', '항목 위아래 10px, 원 23px(결과 22px), 원↔글 10px, 항목 사이 1px 선 #F1F5F9'),
    ('화면 캡처', '틀 안쪽 14 / 16 / 16px, 캡처 사이 16px, 캡처 모서리 8px, 캡션 위 10px'),
    ('번호 원(화면 위)', '지름 22px, 흰 테두리 2px, 숫자 11.4px 700. 글자·아이콘을 가리면 옆 빈자리로, 원끼리 지름 + 4px 이상 띄움'),
    ('자간', '한국어 10pt 초과 -3%, 영어·독일어 -1%, 일본어 0. 10pt 이하 기본값'),
]

MARKERS = [
    ('설정', '#3C55EB 채움, 흰 숫자', '직접 조작하는 위치'),
    ('결과', '흰 채움, #3C55EB 테두리·숫자', '바로 위 설정으로 바뀌는 위치'),
    ('참고', '#64748B 채움, 흰 숫자', '참고 위치'),
]


def esc(t): return t.replace('&', '&amp;').replace('<', '&lt;')


def color_rows(rows):
    out = []
    for name, token, hexv, use in rows:
        r = rgb(hexv); c = cmyk(hexv)
        out.append(f'<tr><td><span class="sw" style="background:{hexv}"></span></td><td><b>{esc(name)}</b><br><span class="tk">{token}</span></td>'
                   f'<td class="mono">{hexv.upper()}</td><td class="mono">{r[0]} {r[1]} {r[2]}</td><td class="mono">{c[0]} {c[1]} {c[2]} {c[3]}</td><td>{esc(use)}</td></tr>')
    return ''.join(out)


def typo_rows():
    return ''.join(f'<tr><td><b>{esc(a)}</b></td><td class="mono">{esc(b)}</td><td class="mono">{esc(c)}</td><td class="mono">{esc(d)}</td><td class="mono">{esc(e)}</td><td class="mono">{esc(f)}</td></tr>' for a, b, c, d, e, f in TYPO)


def spacing_rows():
    return ''.join(f'<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td></tr>' for a, b in SPACING)


# ---------- 쪽 공통: 재단 여백 3mm + 재단선 ----------
PN = [1]
def page(cls, inner, pno=None, dark=False, label=''):
    if pno is not None: PN[0] += 1; pno = PN[0]
    marks = ''.join(f'<i class="cm {p}"></i>' for p in ('tl', 'tr', 'bl', 'br'))
    foot = '' if pno is None else f'<div class="gfoot{" dk" if dark else ""}"><span>SMART EDC 사용자 매뉴얼 디자인 가이드 · {esc(label)}</span><img src="img/smart-edc-logo-footer.png" alt="SMART EDC"><span class="pn">{pno}</span></div>'
    return f'<section class="gp {cls}">{marks}<div class="trim">{inner}{foot}</div></section>\n'


def tmpl_page(pno, title, intro, specs, img, caption, scale_note=''):
    """페이지 템플릿 소개 쪽: 왼쪽 설명, 오른쪽 A4 틀 안의 실제 쪽 그림(재단·안전 영역 표시)"""
    sp = ''.join(f'<li><b>{esc(k)}</b><span>{esc(v)}</span></li>' for k, v in specs)
    return page('tmpl', f'''
<div class="ghead"><span class="gnum">{title[0]}</span><h2>{esc(title[1])}</h2></div>
<div class="tcols">
 <div class="tleft">
  <p class="intro">{esc(intro)}</p>
  <ul class="specs">{sp}</ul>
 </div>
 <div class="tright">
  <div class="a4frame">
   <div class="bleedbox"><span class="dim dtop">216mm (A4 210 + 재단 여백 3mm × 2)</span><span class="dim dleft">303mm</span></div>
   <div class="trimbox"><span class="dim dtrim">재단선 210 × 297mm</span></div>
   <div class="safebox"><span class="dim dsafe">안전 영역 · 재단선 안쪽 5mm</span></div>
   <img class="sample" src="{img}" alt="">
  </div>
  <p class="cap">{esc(caption)}{(' · ' + esc(scale_note)) if scale_note else ''}</p>
 </div>
</div>''', pno, label=title[1])


def build_html():
    css = open(f'{ROOT}/template/style.css').read()
    # 템플릿 CSS의 글꼴 경로는 fonts/ 상대 경로라 그대로 쓴다. 쪽 크기만 재단 여백을 더한 값으로 바꾼다.
    css = css.replace('@page{size:210mm 297mm;margin:0}', '@page{size:216mm 303mm;margin:0}')
    gcss = open(f'{HERE}/guide.css').read()

    toc_items = [('1', '인쇄 사양과 쪽 구조'), ('2', '디자인 토큰 — 색 (바탕 · 구조)'), ('3', '디자인 토큰 — 색 (글 · 카드 · 표)'), ('4', '디자인 토큰 — 글자'), ('5', '디자인 토큰 — 간격 · 번호 원'),
                 ('6', '페이지 템플릿 — 표지'), ('7', '페이지 템플릿 — 목차'), ('8', '페이지 템플릿 — 장 간지'), ('9', '페이지 템플릿 — 본문 A (캡처 1장)'),
                 ('10', '페이지 템플릿 — 본문 B (전후 비교 2장)'), ('11', '페이지 템플릿 — 부록 표'), ('12', '페이지 템플릿 — 뒤표지'), ('13', '파일 구성과 제작 순서')]
    pages = []
    # 표지
    pages.append(page('gcover', f'''
<div class="cv-wave"></div><div class="cv-grad"></div>
<div class="cv-top"><img class="cv-brand" src="img/smart-edc-logo.png" alt="SMART EDC"><span class="cv-sys">임상시험 전자자료수집 시스템</span></div>
<div class="cv-main noclass"><p class="cv-class">사용자 매뉴얼 템플릿</p><h1 class="cv-title">디자인 가이드</h1><p class="cv-sub">표지 · 목차 · 장 간지 · 본문 · 부록 표 · 뒤표지와 디자인 토큰, 인쇄 사양</p></div>
<div class="cv-bottom"><span class="cv-kind">{VER} · 작성 hy0909</span><img class="cv-logo" src="img/logo.png" alt="DH"></div>''', None, dark=True))
    # 차례
    toc = ''.join(f'<li><span class="tn">{n}</span><span class="tt">{esc(t)}</span><span class="tp">{i + 3}</span></li>' for i, (n, t) in enumerate(toc_items))
    pages.append(page('gtoc', f'''
<div class="toc-h"><h1>차례</h1><img class="brand" src="img/smart-edc-logo-gray.png" alt="SMART EDC"></div>
<div class="area"><p class="lead">이 문서는 SMART EDC 사용자 매뉴얼 템플릿(화면별 분권 18권 · CRF 필드 16권 · 4개 언어)의 디자인 기준을 한 권에 모았다. 가이드와 매뉴얼은 같은 원본에서 화면용(RGB)과 인쇄용(CMYK) 두 판으로 만든다. 화면용은 sRGB 그대로, 인쇄용은 재단 여백 3mm를 더한 216 × 303mm에 모든 색을 DeviceCMYK로 바꿔 낸다. 수치는 CSS px이고 pt는 0.75배다.</p>
<ul class="gtoclist">{toc}</ul></div>''', True, label='차례'))
    # 1. 인쇄 사양
    pages.append(page('spec', f'''
<div class="ghead"><span class="gnum">1</span><h2>인쇄 사양과 쪽 구조</h2></div>
<div class="tcols">
 <div class="tleft">
  <p class="intro">매뉴얼은 A4 세로다. 인쇄용 PDF는 사방 3mm 재단 여백을 더한 216 × 303mm로 내고, 모서리에 재단선을 둔다. 바탕색이 끝까지 닿는 표지·간지·본문 헤더는 재단 여백까지 채운다.</p>
  <ul class="specs">
   <li><b>쪽 크기</b><span>210 × 297mm. 화면용 CSS 794 × 1123px (1px = 0.75pt)</span></li>
   <li><b>재단 여백</b><span>사방 3mm. 끝까지 닿는 바탕과 이미지는 여백까지 늘린다</span></li>
   <li><b>안전 영역</b><span>재단선 안쪽 5mm. 글자·번호 원은 이 안에만 둔다. 좌우 기본 여백 56px(14.8mm)이 이를 채운다</span></li>
   <li><b>두 판 제작</b><span>화면용(RGB)과 인쇄용(CMYK)을 같은 HTML에서 만든다. 화면용은 sRGB 그대로 Chrome PDF로 내고, 인쇄용은 그 PDF의 글·선·이미지를 모두 DeviceCMYK로 바꾼다(검정 분리 K = min). 인쇄소 프로파일로 최종 확인한다</span></li>
   <li><b>이미지</b><span>화면 캡처는 2배 확대본(300dpi 기준 충족), 웨이브·로고는 원본. 캡처 안 글자는 언어별로 글자 교체본을 쓴다</span></li>
   <li><b>글꼴</b><span>Pretendard 400 · 500 · 700 · 800 (일본어 Pretendard JP). 모두 PDF에 포함한다. 외곽선으로 바꾸지 않는다</span></li>
   <li><b>검사</b><span>글자·띄어쓰기(check.py), 색(check_colors.py), 미리보기 복사(check_copy.py) 불일치 0일 때만 넘긴다</span></li>
  </ul>
 </div>
 <div class="tright">
  <div class="a4frame diagram">
   <div class="bleedbox"><span class="dim dtop">216 × 303mm · 재단 여백 3mm</span></div>
   <div class="trimbox"><span class="dim dtrim">재단선 210 × 297mm</span></div>
   <div class="safebox"><span class="dim dsafe">안전 영역 (재단선 안쪽 5mm)</span></div>
   <div class="zone hdr-z"><span>본문 헤더 98px · 재단 여백까지 채움</span></div>
   <div class="zone body-z"><span>본문 영역 · 좌우 56px, 헤더 + 22px ~ 아래 84px</span></div>
   <div class="zone ftr-z"><span>푸터 1064px</span></div>
   <div class="mark-z"><span>재단선</span></div>
  </div>
  <p class="cap">본문 쪽의 구역과 재단 여백. 파선은 재단 여백 끝, 실선은 재단선, 점선은 안전 영역이다.</p>
 </div>
</div>''', True, label='인쇄 사양과 쪽 구조'))
    # 2·3. 색 (두 쪽)
    head = '<thead><tr><th style="width:34px"></th><th style="width:150px">이름 · 토큰</th><th style="width:72px">HEX</th><th style="width:84px">RGB</th><th style="width:84px">CMYK</th><th>쓰임</th></tr></thead>'
    pages.append(page('tokens', f'''
<div class="ghead"><span class="gnum">2</span><h2>디자인 토큰 — 색 (바탕 · 구조)</h2></div>
<p class="intro">토큰마다 화면용 값(HEX·RGB)과 인쇄용 값(CMYK)을 함께 둔다. 화면용 판은 HEX 값을, 인쇄용 판은 같은 색을 CMYK로 바꾼 값을 쓴다. 색은 뜻이 있는 자리에만 쓰고, 원본 화면에서 색으로 뜻을 나눈 곳(유의사항 글씨, 결과 설명)은 원본 값을 그대로, 번호 원만 템플릿 파랑 #3C55EB로 통일한다(hy0909 결정, 2026-10-30). CMYK는 K = min 검정 분리 계산값이라 인쇄소 프로파일로 다시 맞춘다.</p>
<div class="tblwrap gtbl"><table>{head}<tbody>{color_rows(COLORS[:14])}</tbody></table></div>''', True, label='디자인 토큰 — 색'))
    pages.append(page('tokens', f'''
<div class="ghead"><span class="gnum">3</span><h2>디자인 토큰 — 색 (글 · 카드 · 표)</h2></div>
<p class="intro">글자색은 본문 #202630, 강조 #111B2B, 보조 #475569 세 단계다. 유의사항 카드는 바탕·제목·강조 바탕이 한 계열로 묶이고, 표와 구분선은 회색 계열만 쓴다.</p>
<div class="tblwrap gtbl"><table>{head}<tbody>{color_rows(COLORS[14:])}</tbody></table></div>''', True, label='디자인 토큰 — 색'))
    # 3. 글자
    pages.append(page('tokens', f'''
<div class="ghead"><span class="gnum">4</span><h2>디자인 토큰 — 글자</h2></div>
<p class="intro">글꼴은 모든 자리에서 Pretendard 하나다(일본어판은 Pretendard JP). 코드·키값에도 고정폭 글꼴을 쓰지 않는다. 크기는 px가 기준이고 pt는 0.75배다. 글이 길어지면 크기를 줄이지 않고 줄을 늘려 영역이 커진다.</p>
<div class="tblwrap gtbl"><table><thead><tr><th style="width:150px">자리</th><th style="width:108px">크기</th><th style="width:96px">굵기</th><th style="width:150px">색</th><th style="width:78px">줄 높이</th><th>자간</th></tr></thead><tbody>{typo_rows()}</tbody></table></div>
<div class="gnote"><b>글꼴 파일</b> Pretendard-400 · 500 · 700 · 800.ttf, PretendardJP-Regular · Medium · Bold · ExtraBold.ttf (template/assets/fonts, fonts_ja). PDF에 모두 포함한다.</div>''', True, label='디자인 토큰 — 글자'))
    # 4. 간격·번호 원
    mk = ''.join(f'<li><span class="mkdemo {c}">{i + 1}</span><b>{esc(a)}</b><span class="mkd">{esc(b)}</span><span class="mkd2">{esc(d)}</span></li>' for i, ((a, b, d), c) in enumerate(zip(MARKERS, ('mset', 'mres', 'mnote'))))
    pages.append(page('tokens', f'''
<div class="ghead"><span class="gnum">5</span><h2>디자인 토큰 — 간격 · 번호 원</h2></div>
<p class="intro">여백과 간격은 모든 쪽에서 같다. 영역 높이는 고정하지 않고 글 줄 수만큼 늘어나며, 아래 영역은 간격을 유지한 채 내려간다.</p>
<div class="tblwrap gtbl"><table><thead><tr><th style="width:150px">항목</th><th>값</th></tr></thead><tbody>{spacing_rows()}</tbody></table></div>
<h3 class="gsub">번호 원</h3>
<ul class="mklist">{mk}</ul>
<p class="gsmall">화면 위 번호 원은 글자·아이콘·테두리를 가리지 않는 가장 가까운 빈자리로 옮기고, 같은 열의 원은 같은 x에서 시작한다. 원끼리는 중심 거리가 지름 + 4px 이상이어야 하고 이미지 밖으로 나가지 않는다.</p>''', True, label='디자인 토큰 — 간격 · 번호 원'))
    # 5~10 템플릿
    pages.append(tmpl_page(True, ('6', '페이지 템플릿 — 표지'), '어두운 남색 바탕에 데이터 웨이브 이미지와 그라데이션을 겹친다. 위에는 SMART EDC 로고와 시스템 설명, 가운데 제목·보조 설명, 아래 선과 매뉴얼 구분 문구·회사 로고를 둔다. 제목 위 파란 네모와 날짜는 넣지 않는다.',
        [('바탕', '#071426. 재단 여백까지 채운다'), ('웨이브', 'wave.jpg, 쪽 위 484px부터, 위아래 그라데이션으로 제목 대비 확보'), ('로고', 'SMART EDC 원색 로고 높이 34px, 왼쪽 56px · 위 73px, 설명 글 16px #D2DCEB, 간격 24px'),
         ('제목', '82.5px 800 흰색, 위 378px(분류 문구가 있으면 322px + 분류 28.5px #A6B5FF)'), ('보조 설명', '20px #DCE5F1, 제목 아래 14px'), ('아래 묶음', '선 1021px rgba(214,227,249,.35), 구분 문구 15px #CBD5E1와 DH 로고 110px의 세로 중심 1057px')],
        'img/sample_cover.png', '실제 분권 표지(데이터 내보내기 · 한국어판)'))
    pages.append(tmpl_page(True, ('7', '페이지 템플릿 — 목차'), '윗띠는 이미지 없이 남색 단색이다. 장 번호는 점 없이 큰 파란 숫자, 항목은 번호·제목·쪽번호 세 칸이다. 목차 쪽에는 별도 쪽번호를 두지 않는다.',
        [('윗띠', '높이 100px #0B1B3A, 「목차」 33.5px 700 흰색, 오른쪽 회색 로고 높이 22px'), ('본문 영역', '위 152px, 좌우 56px, 아래 60px'), ('장 묶음', '번호 16px 800 #3349CA(칸 20px) + 제목 16px 700, 밑선 1px #E2E8F0, 묶음 아래 37.33px'),
         ('항목', '번호 15.5px 700 #94A3B8(칸 26px, 왼쪽 27.33px) + 제목 15.5px #263341, 위아래 3.33px'), ('쪽번호', '13.5px #8C96A8, 24px 칸 가운데, 제목 첫 줄에 세로 중심'), ('두 자리 번호', '실제 글자 폭만큼 번호 칸을 넓히고 목차 전체에 같은 칸을 쓴다')],
        'img/sample_toc.png', '실제 분권 목차(데이터 내보내기 · 한국어판)'))
    pages.append(tmpl_page(True, ('8', '페이지 템플릿 — 장 간지'), '연한 청보라 바탕에 큰 장 번호와 제목, 오른쪽 세로 막대, 아래 절 목록을 둔다. 번호는 01이 아니라 1이다.',
        [('바탕', '#EFF1FA. 재단 여백까지 채운다'), ('구분 문구', '14.5px #405169, 왼쪽 56px · 위 43px'), ('큰 번호 · 제목', '99.6px 800 #45517E, 제목 52px 700 #15233A, 왼쪽 52px · 위 140px'),
         ('막대', '오른쪽 끝 폭 19px #45517E, 번호+제목 묶음의 위치와 높이에 맞춤'), ('절 목록', '위 665px, 윗선 1px #C8D0DD, 번호 16.5px 700 #94A3B8(칸 34px) + 제목 18.5px #26374B, 항목 사이 20px'), ('쪽번호', '13.5px #8590AE, 오른쪽 56px · 위 1063px')],
        'img/sample_divider.png', '실제 분권 간지(데이터 내보내기 · 한국어판)'))
    pages.append(tmpl_page(True, ('9', '페이지 템플릿 — 본문 A (캡처 1장)'), '절 제목 헤더, 경로, 소제목 탭, 범례, 화면 캡처 한 장과 번호 설명, 유의사항 카드 순서다. 캡처 위 번호 원이 가리키는 요소를 아래 번호 설명이 같은 번호로 풀이한다.',
        [('헤더', '98px, 웨이브 이미지 + #102B72 그라데이션, 제목 31.5px 700 흰색(번호 #B6C1D2)'), ('경로', '#EEF1FB 8px, 12.5px, 라벨 700 #6B7689, 꺾쇠 아이콘 12px #A3ADBF'), ('소제목 탭', '#191F29 위 모서리 8px, 17px 700 흰색, 아래 1.5px 선'),
         ('범례', '테두리 1px #E2E8F0 8px, 13px, 설정·결과·참고 원 14px'), ('캡처 틀', '#F6F7F9 8px, 안쪽 14/16/16px, 캡처 모서리 8px, 캡션 12px #475364'), ('번호 설명', '원 23px(결과 22px), 글 14.5px, 항목 사이 1px #F1F5F9'), ('유의사항', '필수 확인 #FDF2F3 · 오해하기 쉬운 동작 #FEF9F0 · 참고 #F1F5F9, 모서리 8px, 왼쪽 세로선 없음')],
        'img/sample_bodyA.png', '실제 분권 본문(로그인 1.3 계정 잠금 · 한국어판)'))
    pages.append(tmpl_page(True, ('10', '페이지 템플릿 — 본문 B (전후 비교 2장)'), '한 캡처 틀 안에 두 장을 나란히 두어 조작 전과 후를 비교한다. 두 장의 폭은 비율대로 나누고 사이 간격은 16px이다. 캡션은 틀 아래 한 줄로 두 장을 함께 설명한다.',
        [('캡처 배치', '한 틀 안 가로 배치, 사이 16px, 세로 가운데 맞춤'), ('폭', '원본 픽셀 비율대로 나눠 틀 안쪽 폭(762 − 32px)을 채움'), ('번호 원', '두 장에 이어서 번호를 매기고 겹치지 않게 옮김'),
         ('캡션', '12px #475364, 「전 — 후」 순서로 한 줄'), ('표', '캡처 아래 표는 머리글 #EDF0F5 12px 700, 본문 13.5px, 행 선 1px #DCE1E8, 첫 열 #475569'), ('첫 열 너비', '낱말이 잘리거나 한 낱말만 떨어지면 96px~표 폭 30% 사이에서 4px씩 조절. 표가 길어지거나 어느 칸이 3줄이 되는 너비는 쓰지 않음')],
        'img/sample_bodyB.png', '실제 분권 본문(데이터 내보내기 2.1 · 한국어판)'))
    pages.append(tmpl_page(True, ('11', '페이지 템플릿 — 부록 표'), '표가 중심인 쪽이다. 머리글 아래 진한 선은 두지 않고 행 사이 선만 연하게 긋는다. 모든 칸은 위 정렬이며 참조 번호도 위에 맞춘다.',
        [('표 글자', '머리글 12px 700 #263341 바탕 #EDF0F5, 본문 13.5px #263341, 첫 열 #475569 700'), ('칸 안쪽', '머리글 11 / 10.7px, 본문 12 / 10.7px (넓은 표 9·8px)'), ('행 선', '1px #DCE1E8, 머리글 아래 진한 선 없음'),
         ('첫 열', '항목명. 너비는 글에 맞춰 96px~30% 사이 조절, 하이픈은 사전식(영어·독일어)'), ('참조 번호', '10.5px 700 #5268B5, 위첨자 3px'), ('쪽 나눔', '표가 쪽을 넘으면 행 단위로 나누고 머리글을 다음 쪽에 다시 둔다')],
        'img/sample_appendix.png', '실제 분권 표 쪽(데이터 내보내기 1.1 화면 구성 · 한국어판)'))
    # 11 뒤표지 템플릿
    pages.append(tmpl_page(True, ('12', '페이지 템플릿 — 뒤표지'), '표지와 같은 남색 바탕에 회사 로고와 문서 정보만 둔다. 웨이브 이미지는 쓰지 않아 표지보다 조용하다. 발행 정보는 분권마다 같은 자리에 적는다.',
        [('바탕', '#071426. 재단 여백까지 채운다'), ('로고', 'DH 로고 폭 110px, 왼쪽 56px · 위 73px'), ('문서 정보', '왼쪽 56px · 위 1021px 선 위에 「SMART EDC 사용자 매뉴얼 · 템플릿 v6」 15px #CBD5E1'),
         ('발행 정보', '회사명 디에이치소프트, 연락처·주소·발행일 [확인 필요]. 16px #D2DCEB, 줄 22px'), ('저작권 문구', '13.5px #8590AE, 아래 묶음 세로 중심 1057px'), ('쪽번호', '두지 않는다')],
        'img/sample_backcover.png', '뒤표지 시안(이 가이드에서 새로 설계, 분권에는 아직 없음)'))
    # 12 파일 구성
    pages.append(page('tokens', f'''
<div class="ghead"><span class="gnum">13</span><h2>파일 구성과 제작 순서</h2></div>
<p class="intro">템플릿은 저장소 safeai-kr/dhsoft-manuals에 있다. 디자인 규칙은 고정 프롬프트 한 파일에 모으고, CSS와 쪽 나눔 스크립트 하나를 전 분권·전 언어가 같이 쓴다.</p>
<div class="tblwrap gtbl"><table><thead><tr><th style="width:230px">파일</th><th>역할</th></tr></thead><tbody>
<tr><td><b>prompt/SMART-EDC_매뉴얼_디자인_고정프롬프트.md</b></td><td>모든 디자인 규칙과 결정 기록. 바뀐 규칙은 날짜·사례와 함께 여기에 먼저 적는다</td></tr>
<tr><td><b>template/style.css</b></td><td>표지·목차·간지·본문·표·카드의 모든 토큰 값</td></tr>
<tr><td><b>template/paginate.js</b></td><td>쪽 나눔, 헤더 가변 높이, 표 첫 열 너비, 제목 끝 줄 보정</td></tr>
<tr><td><b>template/build.py · make_all.sh</b></td><td>분권 데이터(data/&lt;lang&gt;.json)로 HTML을 만들고 검사까지 한 번에</td></tr>
<tr><td><b>template/img_localize.py · localize_all.sh</b></td><td>번역본 화면 캡처의 글자 교체(OCR → 검수 → 번역 → 다시 그리기 → 검사)</td></tr>
<tr><td><b>tools/place_markers.py</b></td><td>화면 위 번호 원 자리 잡기(가림·겹침 없이)</td></tr>
<tr><td><b>tools/widen_buttons.py · extend_cut_buttons.py</b></td><td>번역 글자가 긴 버튼·칩 넓히기, 잘린 버튼 완성</td></tr>
<tr><td><b>template/check*.py</b></td><td>글자·색·복사·얼룩·남은 한글 검사. 모두 불일치 0이어야 넘긴다</td></tr>
</tbody></table></div>
<h3 class="gsub">제작 순서</h3>
<ol class="steps">
<li>원본 PDF에서 글과 색을 뽑고 고정 프롬프트의 색 표와 맞는지 확인한다. 다르면 멈추고 묻는다.</li>
<li>분권 데이터를 만들고 build.py로 HTML을 만든다. 캡처 위 번호 원은 place_markers.py가 자리를 잡는다.</li>
<li>번역본은 캡처 글자를 OCR → 검수 → 번역 → 다시 그리기로 바꾸고, 한글 0 · 얼룩 0을 확인한다.</li>
<li>Chrome으로 PDF를 만들고 check.py · check_colors.py · check_copy.py를 통과시킨다.</li>
<li>인쇄용은 216 × 303mm로 내고 DeviceCMYK로 바꾼 뒤 재단선·안전 영역을 눈으로 확인한다.</li>
</ol>''', True, label='파일 구성과 제작 순서'))
    # 가이드 뒤표지
    pages.append(page('gback', f'''
<div class="cv-top"><img class="cv-logo" src="img/logo.png" alt="DH"></div>
<div class="bk-info"><p class="bk-t">SMART EDC 사용자 매뉴얼 디자인 가이드</p><p class="bk-s">{VER}<br>작성 hy0909 · 디에이치소프트<br>연락처 · 주소 [확인 필요]</p></div>
<div class="cv-bottom"><span class="cv-kind">© 디에이치소프트. 이 문서의 디자인 토큰과 템플릿은 SMART EDC 매뉴얼 제작에만 쓴다.</span><img class="cv-logo" src="img/logo.png" alt="DH"></div>''', None, dark=True))

    html = (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>SMART EDC 사용자 매뉴얼 디자인 가이드</title>'
            f'<style>{css}</style><style>{gcss}</style></head><body class="lang-ko">\n{"".join(pages)}</body></html>')
    out = f'{HERE}/SMART-EDC_매뉴얼_디자인_가이드.html'
    open(out, 'w').write(html); return out


def back_cover_sample():
    """뒤표지 시안 그림: 가이드 안의 뒤표지 템플릿 쪽을 보여 주기 위해 A4(794×1123) 크기로 따로 찍는다"""
    css = open(f'{ROOT}/template/style.css').read()
    html = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{css}
.page.cover .bk-info{{position:absolute;left:56px;right:56px;top:860px;color:#D2DCEB;font-size:16px;line-height:22px}}
.page.cover .bk-t{{font-size:15px;color:#CBD5E1;margin-bottom:10px}} .page.cover .bk-c{{position:absolute;left:56px;top:1046px;font-size:13.5px;color:#8590AE}}
</style></head><body class="lang-ko"><div class="page cover">
<div class="cv-top"><img class="cv-logo" src="img/logo.png" alt="DH" style="width:110px"></div>
<div class="bk-info"><p class="bk-t">SMART EDC 사용자 매뉴얼 · 템플릿 v6</p><p>디에이치소프트<br>연락처 · 주소 · 발행일 [확인 필요]</p></div>
<div class="cv-bottom"><span class="cv-kind">© 디에이치소프트</span><img class="cv-logo" src="img/logo.png" alt="DH"></div>
</div></body></html>'''
    p = f'{HERE}/_backcover.html'; open(p, 'w').write(html); return p


async def render(html_path, back_path):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='chrome', args=['--allow-file-access-from-files'])
        pg = await b.new_page(device_scale_factor=2)
        await pg.goto('file://' + back_path); await pg.wait_for_timeout(800)
        el = await pg.query_selector('.page'); await el.screenshot(path=f'{HERE}/img/sample_backcover.png')
        await pg.goto('file://' + html_path); await pg.wait_for_timeout(1500)
        await pg.evaluate('document.fonts.ready')
        await pg.pdf(path=f'{HERE}/SMART-EDC_매뉴얼_디자인_가이드_RGB.pdf', width='216mm', height='303mm', print_background=True, prefer_css_page_size=True)
        await b.close()


def to_cmyk(src, dst):
    import pymupdf
    doc = pymupdf.open(src)
    for pg in doc: pg.recolor(4)
    doc.save(dst, garbage=3, deflate=True)
    # 확인: 바뀐 뒤 RGB 연산자(rg/RG)가 남았는지
    left = 0
    for pg in doc:
        s = pg.read_contents().decode('latin-1')
        left += len(re.findall(r'(?<![A-Za-z])(rg|RG)\b', s))
    return len(doc), left


def previews(pdf):
    import pymupdf
    os.makedirs(f'{HERE}/preview', exist_ok=True)
    doc = pymupdf.open(pdf)
    for i, pg in enumerate(doc, 1):
        pg.get_pixmap(dpi=72).save(f'{HERE}/preview/p{i:02d}.png')
    return len(doc)


if __name__ == '__main__':
    html = build_html(); back = back_cover_sample()
    asyncio.run(render(html, back))
    n, left = to_cmyk(f'{HERE}/SMART-EDC_매뉴얼_디자인_가이드_RGB.pdf', f'{HERE}/SMART-EDC_매뉴얼_디자인_가이드_CMYK.pdf')
    m = previews(f'{HERE}/SMART-EDC_매뉴얼_디자인_가이드_CMYK.pdf')
    os.remove(back)
    print(f'pages {n}, RGB operators left after recolor {left}, previews {m}')
