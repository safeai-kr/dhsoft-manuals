"""화면용 RGB PDF(A4) → 인쇄용 CMYK PDF(216×303mm, 재단 여백 3mm, 모서리 재단선, DeviceCMYK).
재단 여백은 쪽 가장자리 1pt 띠를 늘려 채운다(바탕·헤더·이미지가 끝까지 이어짐). 글자는 안전 영역 안이라 영향 없다.
사용: python3 tools/pdf_cmyk_print.py <rgb.pdf> <cmyk.pdf>"""
import sys, re, pymupdf
MM = 72 / 25.4
B = 3 * MM            # 재단 여백
src = pymupdf.open(sys.argv[1]); out = pymupdf.open()
for i, sp in enumerate(src):
    W, H = sp.rect.width, sp.rect.height
    pg = out.new_page(width=W + 2 * B, height=H + 2 * B)
    e = 1.0  # 가장자리 띠 두께(pt)
    # 네 변 띠 늘리기
    pg.show_pdf_page(pymupdf.Rect(B, 0, B + W, B), src, i, clip=pymupdf.Rect(0, 0, W, e), keep_proportion=False)
    pg.show_pdf_page(pymupdf.Rect(B, B + H, B + W, H + 2 * B), src, i, clip=pymupdf.Rect(0, H - e, W, H), keep_proportion=False)
    pg.show_pdf_page(pymupdf.Rect(0, B, B, B + H), src, i, clip=pymupdf.Rect(0, 0, e, H), keep_proportion=False)
    pg.show_pdf_page(pymupdf.Rect(B + W, B, W + 2 * B, B + H), src, i, clip=pymupdf.Rect(W - e, 0, W, H), keep_proportion=False)
    # 네 모서리
    for (x0, y0, cx, cy) in ((0, 0, 0, 0), (B + W, 0, W - e, 0), (0, B + H, 0, H - e), (B + W, B + H, W - e, H - e)):
        pg.show_pdf_page(pymupdf.Rect(x0, y0, x0 + B, y0 + B), src, i, clip=pymupdf.Rect(cx, cy, cx + e, cy + e), keep_proportion=False)
    # 본 쪽
    pg.show_pdf_page(pymupdf.Rect(B, B, B + W, B + H), src, i)
    # 재단선: 재단 여백 안 모서리, 재단선 연장선 방향으로 2.5mm, 0.25pt, 맞춤 검정(인쇄 뒤 recolor로 CMYK)
    L = 2.5 * MM
    sh = pg.new_shape()
    for x in (B, B + W):
        sh.draw_line((x, 0), (x, B - 0.5 * MM)); sh.draw_line((x, B + H + 0.5 * MM), (x, H + 2 * B))
    for y in (B, B + H):
        sh.draw_line((0, y), (B - 0.5 * MM, y)); sh.draw_line((B + W + 0.5 * MM, y), (W + 2 * B, y))
    sh.finish(color=(0, 0, 0), width=0.25); sh.commit()
    pg.set_trimbox(pymupdf.Rect(B, B, B + W, B + H))
    pg.set_bleedbox(pg.rect)
out.set_toc(src.get_toc())
out.set_metadata({**src.metadata, 'title': src.metadata.get('title', '') + ' (인쇄용 CMYK)'})
for pg in out:
    pg.recolor(4)
# recolor가 이미지에 붙인 ICC(CMYK, N=4) 색 공간을 DeviceCMYK로 바꾼다(데이터는 그대로 CMYK 4채널)
for x in range(1, out.xref_length()):
    try:
        if out.xref_get_key(x, 'Subtype')[1] != '/Image': continue
        t, v = out.xref_get_key(x, 'ColorSpace')
        arr = out.xref_object(int(v.split()[0])) if t == 'xref' else v
        m = re.search(r'/ICCBased (\d+) 0 R', arr)
        if m and out.xref_get_key(int(m.group(1)), 'N')[1] == '4':
            out.xref_set_key(x, 'ColorSpace', '/DeviceCMYK')
    except Exception: pass
out.save(sys.argv[2], garbage=3, deflate=True)
# 확인: RGB 연산자·RGB 이미지가 남았는지
left = 0; rgbimg = 0
for pg in out:
    for xref in pg.get_contents():
        left += len(re.findall(r'(?<![A-Za-z])(rg|RG)\b', out.xref_stream(xref).decode('latin-1')))
for x in range(1, out.xref_length()):
    try:
        if out.xref_get_key(x, 'Subtype')[1] == '/Image' and out.xref_get_key(x, 'ColorSpace')[1] not in ('/DeviceCMYK', '/DeviceGray'): rgbimg += 1
    except Exception: pass
print('pages', len(out), 'size_mm', round(out[0].rect.width / MM, 1), round(out[0].rect.height / MM, 1), 'rgb_ops_left', left, 'rgb_images_left', rgbimg)
