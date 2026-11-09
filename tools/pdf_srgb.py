"""PDF 안의 모든 RGB 색을 sRGB 하나로 읽게 만든다.
- 표준 sRGB ICC 프로필을 한 번 넣는다
- 기존 ICC 프로필(Skia)은 같은 sRGB 프로필로 바꾼다
- 쪽·폼 리소스에 /DefaultRGB = sRGB 를 넣어 프로필 없는 DeviceRGB도 sRGB로 읽게 한다
- 카탈로그에 sRGB OutputIntent를 넣는다
본문 글자·그림·태그는 건드리지 않는다."""
import sys, pymupdf, re
ICC = open('/System/Library/ColorSync/Profiles/sRGB Profile.icc', 'rb').read()

def ensure_dict_key(doc, xref, key):
    """xref 객체의 key 가 딕셔너리면 그 xref(간접) 를 돌려준다. 직접 딕셔너리면 간접 객체로 뽑아낸다."""
    t, v = doc.xref_get_key(xref, key)
    if t == 'xref':
        return int(v.split()[0])
    nx = doc.get_new_xref()
    doc.update_object(nx, v if t == 'dict' else '<<>>')
    doc.xref_set_key(xref, key, f'{nx} 0 R')
    return nx

def add_default(doc, res_xref, cs_ref):
    t, v = doc.xref_get_key(res_xref, 'ColorSpace')
    if t == 'xref':
        cx = int(v.split()[0]); doc.xref_set_key(cx, 'DefaultRGB', cs_ref)
    elif t == 'dict':
        doc.xref_set_key(res_xref, 'ColorSpace/DefaultRGB', cs_ref)
    else:
        doc.xref_set_key(res_xref, 'ColorSpace', f'<</DefaultRGB {cs_ref}>>')

def fix(src, dst):
    doc = pymupdf.open(src)
    icc = doc.get_new_xref()
    doc.update_object(icc, '<</N 3>>'); doc.update_stream(icc, ICC)
    csx = doc.get_new_xref(); doc.update_object(csx, f'[/ICCBased {icc} 0 R]')
    cs_ref = f'{csx} 0 R'
    n_icc = 0
    for x in range(1, doc.xref_length()):
        if x in (icc, csx): continue
        try: obj = doc.xref_object(x)
        except Exception: continue
        # 기존 ICC 프로필 스트림 → 표준 sRGB
        if doc.xref_is_stream(x) and doc.xref_get_key(x, 'N')[1] == '3' and doc.xref_get_key(x, 'Subtype')[0] == 'null' \
                and doc.xref_get_key(x, 'Type')[0] == 'null' and doc.xref_get_key(x, 'Width')[0] == 'null':
            doc.update_stream(x, ICC); n_icc += 1
        # 폼 XObject·타일 패턴 리소스
        if doc.xref_get_key(x, 'Subtype')[1] == '/Form' or doc.xref_get_key(x, 'PatternType')[1] == '1':
            add_default(doc, ensure_dict_key(doc, x, 'Resources'), cs_ref)
    for pg in doc:
        add_default(doc, ensure_dict_key(doc, pg.xref, 'Resources'), cs_ref)
    cat = doc.pdf_catalog()
    oi = doc.get_new_xref()
    doc.update_object(oi, f'<</Type/OutputIntent/S/GTS_PDFA1/OutputConditionIdentifier(sRGB IEC61966-2.1)/Info(sRGB IEC61966-2.1)/RegistryName(http://www.color.org)/DestOutputProfile {icc} 0 R>>')
    doc.xref_set_key(cat, 'OutputIntents', f'[{oi} 0 R]')
    doc.save(dst, garbage=1, deflate=True)
    return n_icc

if __name__ == '__main__':
    print(fix(sys.argv[1], sys.argv[2]))
