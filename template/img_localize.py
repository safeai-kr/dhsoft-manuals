"""번역본 화면 캡처 만들기: 한국어 글자 자리를 바탕색으로 덮고 번역어를 같은 자리에 다시 그린다 (고정 프롬프트 11절 2순위).

사용: python3 template/img_localize.py <분권> <en|de|ja> [--only s1_1_1.png] [--dump]
입력: manuals/<분권>/ko/img/s*.png (한국어판 2배 확대본, 이 해상도에서 바로 글자를 바꾼다)
      manuals/<분권>/img/loc/segments.json, verified.json
      manuals/<분권>/i18n/image_<lang>.json  ({한국어: 번역어})
출력: manuals/<분권>/img/<lang>/s*.png
      manuals/<분권>/img/<lang>/replacements.json  (덩어리별 원문·번역어·위치·크기·굵기·정렬·축소율·플래그; build.py가 품질 기록에 넣는다)
--dump 는 번역 없이 덩어리(원문 묶음) 목록만 manuals/<분권>/img/loc/strings_ko.json 에 적는다.
"""
import asyncio, json, sys, os, base64, re, argparse
import numpy as np
from PIL import Image
from playwright.async_api import async_playwright
from img_common import modal_bbox
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ap = argparse.ArgumentParser()
ap.add_argument('vol'); ap.add_argument('lang', nargs='?', default='')
ap.add_argument('--only', default=''); ap.add_argument('--dump', action='store_true')
a = ap.parse_args()
V = f'{ROOT}/manuals/{a.vol}'; KO = f'{V}/ko/img'; LOC = f'{V}/img/loc'
segs = {s['id']: s for s in json.load(open(f'{LOC}/segments.json'))}
ver = {v['id']: v for v in json.load(open(f'{LOC}/verified.json'))}
missing_ver = [k for k in segs if k not in ver]
if missing_ver: sys.exit(f'verified.json에 없는 id {len(missing_ver)}개: {missing_ver[:5]}')

lang = a.lang
OUT = f'{V}/img/{lang}' if lang else ''
if lang and not a.dump:
    os.makedirs(OUT, exist_ok=True)
    tr = json.load(open(f'{V}/i18n/image_{lang}.json'))
else:
    tr = None

_imcache = {}
def im_of(f):
    if f not in _imcache:
        _imcache.clear(); _imcache[f] = np.asarray(Image.open(f'{KO}/{f}').convert('RGB')).astype(int)
    return _imcache[f]

def ring_color(im, x0, x1, y0, y1, gap=2, width=4):
    """상자(x0..x1, y0..y1) 바깥 gap~gap+width px 띠 네 방향의 대표색 가운데 서로 가장 많이 일치하는 색.
    좁은 버튼·칩은 글자 상자가 위아래 테두리에 거의 닿아 위·아래 띠에 바깥색이 섞이므로, 한 방향만 믿지 않는다."""
    H, W = im.shape[:2]
    sides = [im[max(0, y0 - gap - width):max(0, y0 - gap), x0:x1].reshape(-1, 3), im[min(H, y1 + gap):min(H, y1 + gap + width), x0:x1].reshape(-1, 3),
             im[y0:y1, max(0, x0 - gap - width):max(0, x0 - gap)].reshape(-1, 3), im[y0:y1, min(W, x1 + gap):min(W, x1 + gap + width)].reshape(-1, 3)]
    sides = [v for v in sides if len(v)]
    if not sides: return None
    meds = [np.median(v, 0) for v in sides]
    # 상자 안 최빈색도 후보로. 선택된 표 행처럼 글자 상자가 색 띠를 꽉 채우면 네 방향 띠가 모두 띠 바깥이라 서로 맞지 않는다 (2026-10-30 데이터내보내기 파일 목록 선택 행)
    box = im[y0:y1, x0:x1].reshape(-1, 3)
    if len(box):
        q = (box // 8).astype(int); keys = q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2]
        vals, cnt = np.unique(keys, return_counts=True); inside = box[keys == vals[cnt.argmax()]].mean(0)
        # 상자의 절반 이상이 한 색이면 그 색이 바탕이다. 테두리 있는 버튼은 상자가 버튼 안쪽 전체라 네 방향 띠가 테두리 색이 된다 (2026-10-30 플랫폼관리 「편집」 버튼이 회색으로 덮인 문제)
        # 글자가 빽빽한 배지는 배지 색이 상자의 35~50%뿐이지만, 상자가 배지 자체라 네 방향 띠는 모두 배지 바깥 흰색이다 (2026-11-03 Query 「3/3 완료」 배지)
        if cnt.max() >= 0.35 * len(box): return [int(v) for v in inside]
        meds.append(inside)
    agree = [sum(1 for o in meds if np.abs(m - o).sum() < 24) for m in meds]
    best = max(agree)
    # 동률이면 뒤쪽 후보(상자 안 최빈색 → 좌우 띠) 우선
    return [int(v) for v in [m for m, a in zip(meds, agree) if a == best][-1]]

# ---------- 자동 규칙 (검수 결과 위에 덧씌운다. verified.json 은 고치지 않는다)
auto_skip = []; auto_center = []; auto_bg = []
for sid, s_ in segs.items():
    # 덩어리의 바탕색이 잘못 잡혔으면(작은 버튼·칩의 글자 상자가 칸을 거의 채워 crop 테두리가 칸 바깥이었던 경우) 글자 옆 띠로 다시 잰다
    # (2026-10-30 워크스페이스 「워크스페이스 삭제」 분홍 버튼이 연분홍 바탕·진분홍 글자로 뒤집힌 문제)
    if ver[sid].get('skip'): continue
    im_ = im_of(s_['file'])
    # 진한 칩(검은 바탕에 흰 글자)이 통째로 '글자'로 잡힌 경우: 상자 안이 거의 다 잉크(바탕과 다른 색)면 칩이다.
    # 칩 색을 바탕으로, 칩 안의 밝은 글자 잉크 상자를 글자 자리로 바꾼다 (2026-10-30 워크스페이스 「지금 할 차례」 칩이 지워지고 검은 글자가 된 문제)
    box0 = im_[s_['y0']:s_['y1'], s_['x0']:s_['x1']]
    ink0 = (np.abs(box0 - np.array(s_['bg'])).max(2) > 40) if box0.size else None
    # 상자 테두리(첫·끝 행과 열)가 대부분 잉크면 글자가 아니라 채워진 칩이다 (흰 글자는 연한 바탕과 차이가 작아 잉크로 안 잡힌다)
    edge_ink = np.concatenate([ink0[0], ink0[-1], ink0[:, 0], ink0[:, -1]]).mean() if ink0 is not None and ink0.size else 0
    chip = None
    if box0.size:   # 칩 색은 최빈색으로(중앙값은 흰 글자 번짐이 섞여 어긋난다, 2026-10-30 SAE통보 「테이블」 칩)
        qb = (box0.reshape(-1, 3) // 8).astype(int); kb = qb[:, 0] * 10000 + qb[:, 1] * 100 + qb[:, 2]
        vb, cb = np.unique(kb, return_counts=True); chip = box0.reshape(-1, 3)[kb == vb[cb.argmax()]].mean(0)
    # 칩 판정: 상자 테두리가 대부분 잉크이고, 상자 안의 대표색이 바깥 바탕색과 뚜렷이 다를 때만 (글자 상자가 꽉 찬 보통 글자는 대표색이 바탕색과 같다)
    chip_touch = 0
    if box0.size and chip is not None:
        cm = np.abs(box0 - chip).max(2) <= 40
        chip_touch = min(cm[0].mean(), cm[-1].mean(), cm[:, 0].mean(), cm[:, -1].mean())
    # 칩은 칩 색이 상자 네 변 모두에 절반 넘게 닿는다. 「필수」 라벨 + 배지처럼 왼쪽 변이 흰 바탕·검은 글자면 칩이 아니다 (2026-11-03 Query 3.2)
    if box0.size and (ink0.mean() > 0.8 or edge_ink > 0.6) and np.abs(chip - np.array(s_['bg'])).max() > 40 and chip_touch > 0.5:
        inner = np.abs(box0 - chip).max(2) > 40
        # 상자 테두리에 닿은 덩어리(칩 바깥 모서리의 바탕색)는 빼고, 칩 안에 갇힌 덩어리(글자)만 남긴다
        lab_, n_ = ndimage.label(inner)
        if n_:
            border_ids = set(np.unique(np.concatenate([lab_[0], lab_[-1], lab_[:, 0], lab_[:, -1]]))) - {0}
            inner &= ~np.isin(lab_, list(border_ids))
        ys_, xs_ = np.where(inner)
        if len(ys_) and (xs_.max() - xs_.min()) < (s_['x1'] - s_['x0']) - 4:
            px = box0[inner]; dd = np.abs(box0 - chip).max(2)[inner]; col = px[dd >= np.percentile(dd, 90)].mean(0)
            s_['x0'], s_['x1'] = int(s_['x0'] + xs_.min()), int(s_['x0'] + xs_.max() + 1)
            s_['y0'], s_['y1'] = int(s_['y0'] + ys_.min()), int(s_['y0'] + ys_.max() + 1)
            s_['words'] = [[s_['x0'], s_['x1']]]; s_['bg'] = [int(v) for v in chip]; s_['fg'] = [int(round(v)) for v in col]
            auto_bg.append(sid + '(chip)'); continue
    rc = ring_color(im_, s_['x0'], s_['x1'], s_['y0'], s_['y1'])
    if rc is None or np.abs(np.array(rc) - np.array(s_['bg'])).sum() < 24: continue
    box = im_[s_['y0']:s_['y1'], s_['x0']:s_['x1']]
    if box.size == 0: continue
    # 띠로 잰 색과 저장된 바탕색 가운데 상자 안에 더 많이 있는 색을 쓴다. 상자가 배지 자체이면 띠는 배지 바깥 흰색이라 저장된 배지 색이 맞다 (2026-11-03 Query 「3/3 완료」 배지)
    f_old = (np.abs(box - np.array(s_['bg'])).max(2) < 24).mean(); f_new = (np.abs(box - np.array(rc)).max(2) < 24).mean()
    if f_new <= f_old: continue
    diff = np.abs(box - np.array(rc)).max(2); ink = diff > 40
    if not ink.any(): continue
    px = box[ink]; dd = diff[ink]; col = px[dd >= np.percentile(dd, 90)].mean(0)
    if col.max() - col.min() < 45: col = np.array([col.mean()] * 3)
    s_['bg'] = rc; s_['fg'] = [int(round(v)) for v in col]; auto_bg.append(sid)
_byfile = {}
for s_ in segs.values(): _byfile.setdefault(s_['file'], []).append(s_)
_modal = {f: modal_bbox(np.asarray(Image.open(f'{KO}/{f}').convert('RGB')).astype(int)) for f in _byfile}
for sid, s_ in segs.items():
    v = ver[sid]
    if v.get('skip'): continue
    bg = np.array(s_['bg']); fg = np.array(s_['fg'])
    # (0) 모달 화면이면 모달 상자 바깥(덮개 뒤 흐려진 배경)의 덩어리는 모두 그대로 둔다
    mb = _modal.get(s_['file'])
    if mb and not (mb[0] <= (s_['x0'] + s_['x1']) / 2 < mb[2] and mb[1] <= (s_['y0'] + s_['y1']) / 2 < mb[3]):
        v['skip'] = True; auto_skip.append(sid); continue
    # (1) 반투명 덮개(모달 뒤 어두워진 화면) 뒤의 글자: 바탕이 무채색 중간 회색이고 글자가 그보다 어두우면 번역하지 않고 그대로 둔다.
    #     잘려 있어 읽히지 않는 배경 글이라, 덮으면 덮개 색과 어긋나 울퉁불퉁한 얼룩이 생긴다 (2026-10-30 워크스페이스 s1_2_1 왼쪽 가장자리)
    if 70 <= bg.mean() <= 205 and (bg.max() - bg.min()) <= 18 and fg.mean() < bg.mean() - 30:
        v['skip'] = True; auto_skip.append(sid); continue
    # (2) 가운데 정렬 보정: 왼쪽 정렬로 검수된 안내문·제목이 바로 위아래 가운데 정렬 글(제목·버튼·안내문)과 중심이 2px 안에서 같으면 가운데 정렬로 본다
    #     (2026-10-30 로그인 s2_1_1 '가입 이메일을 입력하시면…' 두 줄이 왼쪽으로 쏠렸던 문제)
    if v.get('align', 'left') in ('', 'left') and not v.get('join_next') and v.get('role') in ('text', 'title'):
        cx = (s_['x0'] + s_['x1']) / 2
        for c in _byfile[s_['file']]:
            cv = ver[c['id']]
            if c is s_ or cv.get('skip') or cv.get('align') != 'center' or cv.get('role') not in ('title', 'button', 'text'): continue
            if abs(cx - (c['x0'] + c['x1']) / 2) <= 2 and abs(s_['y0'] - c['y0']) <= 3.5 * s_['line_h'] and (s_['x1'] - s_['x0']) > 0.3 * (c['x1'] - c['x0']):
                v['align'] = 'center'; auto_center.append(sid); break
if auto_skip or auto_center or auto_bg:
    print(json.dumps({'auto_skip_overlay': auto_skip, 'auto_center': auto_center, 'auto_bg_fixed': auto_bg}, ensure_ascii=False))

def ink_rows(s, x0, x1, exclude=(), ko_text=''):
    im = im_of(s['file']); h = s['line_h']
    ya = max(0, int(s['y0'] - 0.08 * h)); yb = min(im.shape[0], int(s['y1'] + 0.08 * h))
    ink = np.abs(im[ya:yb, x0:x1] - np.array(s['bg'])).max(2) > 40
    # 글자 바로 아래·위의 입력칸 테두리 같은 가로줄(글자 오른쪽 바깥까지 이어진 잉크)은 글자 줄에서 뺀다
    xr0, xr1 = x1 + 2, min(im.shape[1], x1 + 2 + int(h))
    beyond = (np.abs(im[ya:yb, xr0:xr1] - np.array(s['bg'])).max(2) > 40).mean(1) if xr1 > xr0 else np.zeros(yb - ya)
    rule = (beyond > 0.8) & (ink.mean(1) > 0.8)
    # 다른 덩어리(같은 파일의 더 작은 글자 상자)가 이 상자 안에 들어 있으면 그 줄들은 그 덩어리의 몫이다. OCR이 제목+설명+아이콘을 한 덩어리로 묶고
    # 검수가 설명만 적은 경우, 제목 줄까지 지우고 번역을 겹쳐 그리게 된다 (2026-11-03 배정 「배정 설정 / 설정 완료」). 그 줄은 가로줄처럼 경계로 취급한다
    for (ey0, ey1) in exclude:
        a_, b_ = max(0, ey0 - 2 - ya), min(len(rule), ey1 + 2 - ya)
        if b_ > a_: rule[a_:b_] = True
    # 행의 잉크가 5% 미만이면(입력칸 세로 테두리가 상자 안에 한 줄 걸친 것) 글자 줄이 아니다. 이를 세면 자리표시 글의 줄 높이가 입력칸 전체가 돼 글자가 거대해지고 테두리가 지워진다 (2026-10-30 AuditTrail 「예: age」)
    keep = (ink.mean(1) >= 0.05) & ~rule
    # 두께 3px 이하이고 상자 폭을 거의 다 채운(잉크 80% 이상) 가로줄 덩어리는 좁은 버튼의 위아래 테두리다. 글자 오른쪽 바깥(beyond)이 짧아
    # 위 규칙에 안 걸려도 선으로 본다 (2026-11-03 방문정의 1.1 「수정」 버튼: 윗선 2px이 글자 줄에 들어가 글자가 거대해지고 윗선이 지워짐)
    i = 0
    while i < len(keep):
        if keep[i]:
            j = i
            while j < len(keep) and keep[j]: j += 1
            if j - i <= 3 and (ink[i:j].mean(1) > 0.8).all(): rule[i:j] = True; keep[i:j] = False
            i = j
        else: i += 1
    if not keep.any(): return s['y0'], s['y1']
    # 가로줄(테두리)로 끊긴 구간 가운데 잉크가 가장 많은 구간만 글자 줄로 본다. 빈 줄로만 나뉜 두 줄 글(제목+설명)은 한 구간이다.
    # 테두리 아래 둥근 모서리의 몇 픽셀까지 잉크로 잡으면 지우는 범위가 테두리를 덮어 입력칸 윗선이 지워진다 (2026-10-30 플랫폼관리 2.2 「라벨 *」).
    # 빈 줄에서도 끊으면 두 줄 덩어리의 번역이 한 줄에 겹쳐 그려진다 (2026-11-03 배정 「배정 설정 / 설정 완료」)
    segs_ = []; cur = []
    for i in range(len(keep)):
        if rule[i]:
            if cur: segs_.append(cur); cur = []
        elif keep[i]: cur.append(i)
    if cur: segs_.append(cur)
    best = max(segs_, key=lambda rows_: sum(ink[i].sum() for i in rows_))
    # 구간 안에 빈 줄로 나뉜 글 줄이 둘 이상이고 검수 글이 그중 한 줄 폭에만 맞으면 그 줄만 쓴다.
    # OCR이 제목+설명을 한 덩어리로 묶고 검수가 한 줄만 적은 경우, 두 줄 높이로 그리면 글자가 거대해지고 다른 줄이 지워진다 (2026-11-03 배정 「삼중 맹검」)
    lines_ = []; cur = [best[0]]
    for i in best[1:]:
        if i == cur[-1] + 1: cur.append(i)
        elif i - cur[-1] <= 2: cur.append(i)     # 1~2px 틈은 같은 줄
        else: lines_.append(cur); cur = [i]
    lines_.append(cur)
    lines_ = [l_ for l_ in lines_ if len(l_) >= 4]
    # 상자 위·아래 끝에 걸친 낮은 줄(가장 높은 줄의 0.4배 미만)은 이웃 덩어리 글자의 윗부분·아랫부분이 잘려 들어온 것이다.
    # 이 조각을 줄로 세면 줄 높이 중앙값이 작아져 조각 줄이 뽑히고, 진짜 한글 줄은 안 지워진 채 번역이 조각 높이로 아주 작게 그려진다
    # (2026-11-13 AE지정 「해제하면 이 양식은…」 두 줄 문단, 기관관리 「통합병원 제1기관」 아래 영문 작은 글자)
    if len(lines_) >= 2:
        tall = max(len(l_) for l_ in lines_)
        frag = [l_ for l_ in lines_ if len(l_) < 0.4 * tall and (l_[0] <= 2 or l_[-1] >= len(keep) - 3)]
        if frag:
            lines_ = [l_ for l_ in lines_ if l_ not in frag]
            if len(lines_) == 1: return int(ya + lines_[0][0]), int(ya + lines_[0][-1] + 1)
    if len(lines_) >= 2 and ko_text:
        hh_ = float(np.median([len(l_) for l_ in lines_]))
        est = est_width(ko_text) * hh_ / 0.88        # 잉크 높이 → 글자 크기 → 예상 폭
        def wid(l_):
            cols = np.where(ink[l_[0]:l_[-1] + 1].any(0))[0]
            return float(cols.max() - cols.min() + 1) if len(cols) else 0.0
        total = wid(best)
        cand = [(abs(wid(l_) - est) / max(est, 1), l_) for l_ in lines_]
        err, l_ = min(cand, key=lambda t: t[0])
        if err < 0.35 and abs(total - est) / max(est, 1) > err + 0.15:
            return int(ya + l_[0]), int(ya + l_[-1] + 1)
    return int(ya + best[0]), int(ya + best[-1] + 1)


def est_width(t):
    """글자 크기(em) 단위의 대략 폭: 한글 1.0, 라틴·숫자 0.55, 공백 0.3, 그 밖 0.5"""
    w = 0.0
    for ch in t:
        if '가' <= ch <= '힣': w += 1.0
        elif ch.isalnum(): w += 0.55
        elif ch == ' ': w += 0.3
        else: w += 0.5
    return w

# ---------- 작업 묶음: 한 덩어리, 또는 join_next 로 이어진 문단
jobs = {}; done = set(); dump = []
order = list(segs)
heads = set(order) - {ver[k].get('join_next') for k in order if ver[k].get('join_next')}
for sid in order:
    v = ver[sid]
    if v.get('skip') or sid in done or sid not in heads: continue
    chain = [sid]
    while ver[chain[-1]].get('join_next') and ver[chain[-1]]['join_next'] in ver and ver[chain[-1]]['join_next'] not in chain:
        chain.append(ver[chain[-1]]['join_next'])
    done.update(chain)
    lines = []
    for cid in chain:
        s, cv = segs[cid], ver[cid]
        if cv.get('skip'): continue
        words = s['words']
        x0, x1 = words[0][0], words[-1][1]
        # 아이콘이 앞에 붙은 덩어리: 첫 낱말이 좁으면(글자 높이 1.5배 미만) 그 다음부터.
        # 앞에 테두리·아이콘이 낱말 둘 이상으로 잡혔으면(2026-11-03 방문정의 1.1 「수정」: 버튼 왼쪽 선 + 연필 + 글자) 검수 글의 낱말 수만 남을 때까지 앞 낱말을 뺀다
        if cv.get('icon_lead') and len(words) > 1:
            n_ko = max(1, len(cv['ko'].split()))
            k = 0
            while len(words) - k > n_ko and k < len(words) - 1 and (words[k][1] - words[k][0]) < 1.5 * s['line_h']: k += 1
            if k == 0 and (words[0][1] - words[0][0]) < 1.5 * s['line_h']: k = 1
            x0 = words[k][0]
        excl = []
        for oid, o in segs.items():
            if oid == cid or o['file'] != s['file'] or ver[oid].get('skip') or oid in chain: continue
            oh, sh_ = o['y1'] - o['y0'], s['y1'] - s['y0']
            if oh < sh_ * 0.8 and o['y0'] >= s['y0'] - 2 and o['y1'] <= s['y1'] + 2 and min(o['x1'], x1) - max(o['x0'], x0) > 0:
                excl.append((o['y0'], o['y1']))
        y0r, y1r = ink_rows(s, x0, x1, excl, cv['ko'].strip())
        # 글자 줄(y0r..y1r) 안에서 실제 잉크가 있는 열로 좌우를 다시 좁힌다. OCR 상자가 입력칸 테두리·둥근 모서리까지 안았을 때
        # 그 부분은 글자 줄에 잉크가 없으므로 빠진다 (2026-10-30 AuditTrail 「예: age」 자리표시 글이 칸 왼쪽 밖에서 시작한 문제). 넓히지는 않는다
        im_ = im_of(s['file']); band = im_[y0r:y1r, x0:x1]
        if band.size:
            cink = np.abs(band - np.array(s['bg'])).max(2) > 40
            # 세로줄(입력칸 왼쪽 테두리): 글자 줄 거의 전체에 잉크가 있고 줄 위아래 바깥까지 이어지는 열은 글자가 아니다
            Hh = im_.shape[0]; ya_, yb_ = max(0, y0r - 6), min(Hh - 1, y1r + 5)
            vrule = (cink.mean(0) > 0.9) & (np.abs(im_[ya_, x0:x1] - np.array(s['bg'])).max(1) > 40) & (np.abs(im_[yb_, x0:x1] - np.array(s['bg'])).max(1) > 40)
            cols = np.where(cink.any(0) & ~vrule)[0]
            if len(cols): x0, x1 = int(x0 + cols.min()), int(x0 + cols.max() + 1)
            # 끝에 아이콘이 붙은 덩어리(검수 `icon_trail`, 2026-11-03 달력·× 아이콘이 글자와 함께 지워진 10곳): 잉크 높이의 0.15배 넘는 틈으로 나뉜 마지막 열 묶음이
            # 잉크 높이 1.3배보다 좁으면 아이콘으로 보고 뺀다(두 번까지). 틈이 없으면 검수 글의 예상 폭(한글 1em·라틴 0.55em)의 1.1배에서 자른다
            if cv.get('icon_trail') and len(cols):
                hh_ = y1r - y0r
                for _ in range(2):
                    cink2 = np.abs(im_[y0r:y1r, x0:x1] - np.array(s['bg'])).max(2) > 40
                    cc = np.where(cink2.any(0))[0]
                    if len(cc) < 2: break
                    gaps = np.where(np.diff(cc) - 1 >= 0.15 * hh_)[0]
                    if len(gaps) == 0:
                        x1 = min(x1, int(x0 + est_width(cv['ko'].strip()) * hh_ / 0.88 * 1.1)); break
                    tail0 = cc[gaps[-1] + 1]; tw = cc[-1] - tail0 + 1
                    if tw <= 1.3 * hh_: x1 = int(x0 + cc[gaps[-1]] + 1)
                    else: break
        lines.append({'id': cid, 'x0': int(x0), 'x1': int(x1), 'y0': y0r, 'y1': y1r, 'ko': cv['ko'].strip(), 'bg': s['bg'], 'fg': s['fg'], 'h': s['line_h']})
        if os.environ.get('IMG_DEBUG') == cid: print('DEBUG', cid, 'x', x0, x1, 'rows', y0r, y1r, 'excl', excl, 'words', s['words'], file=sys.stderr)
    if not lines: continue
    ko = ' '.join(l['ko'] for l in lines if l['ko'])
    if not ko: continue
    rec = {'id': sid, 'ko': ko, 'role': v.get('role', ''), 'lines': len(lines), 'truncated': bool(v.get('truncated'))}
    dump.append(rec)
    if tr is None: continue
    t = tr.get(f"{ko}@{v.get('role', '')}", tr.get(ko))   # 같은 한국어가 역할에 따라 다르게 번역되면 '원문@역할' 키를 먼저 본다
    if t is None:
        print('MISSING', sid, ko); continue
    jobs.setdefault(segs[sid]['file'], []).append({'id': sid, 'lines': lines, 'ko': ko, 'tr': t, 'align': v.get('align', 'left') or 'left',
                                                  'bold': bool(v.get('bold')), 'truncated': bool(v.get('truncated')), 'role': v.get('role', '')})
if tr is None:
    json.dump(dump, open(f'{LOC}/strings_ko.json', 'w'), ensure_ascii=False, indent=0)
    print(json.dumps({'vol': a.vol, 'jobs': len(dump), 'unique': len({d['ko'] for d in dump})}, ensure_ascii=False)); sys.exit()

# ---------- 자리 재기: 좌우 빈 공간, 덮을 색, 줄 묶음
for f, lst in jobs.items():
    im = im_of(f); H, W = im.shape[:2]
    for j in lst:
        for l in j['lines']:
            bg = np.array(l['bg']); ya, yb = max(0, l['y0']), min(H, l['y1'])
            def free(x): return np.abs(im[ya:yb, x] - bg).max() <= 30
            r = min(W - 1, l['x1'] + 2)   # 글자 오른쪽 번짐 2px 는 건너뛴다 (2026-10-30 '설명'→'Description' 잘림)
            while r < W - 1 and free(r): r += 1
            q = max(0, l['x0'] - 3)
            while q > 0 and free(q): q -= 1
            l['free_r'] = int(r); l['free_l'] = int(q + 1)
            # 덮는 색: 글자 잉크 바로 옆 띠(위·아래·좌·우) 가운데 서로 일치하는 색. 위·아래 줄만 보면 좁은 버튼에서 바깥색이 섞인다
            # 덩어리 바탕색은 위에서 글자 옆 띠로 이미 바로잡았으므로 그 색으로 덮는다 (띠를 또 재면 바로 옆 강조 칸·선 색이 섞인다)
            l['fill'] = l['bg']
    allboxes = [(j['id'], l) for j in lst for l in j['lines']]
    for j in lst:
        rows = []
        for l in sorted(j['lines'], key=lambda l: (l['y0'], l['x0'])):
            cy = (l['y0'] + l['y1']) / 2
            if rows and abs(cy - rows[-1]['cy']) < 0.5 * l['h']:
                r = rows[-1]; r['x0'] = min(r['x0'], l['x0']); r['x1'] = max(r['x1'], l['x1'])
                r['y0'] = min(r['y0'], l['y0']); r['y1'] = max(r['y1'], l['y1']); r['free_r'] = max(r['free_r'], l['free_r']); r['free_l'] = min(r['free_l'], l['free_l'])
            else:
                rows.append({'cy': cy, 'x0': l['x0'], 'x1': l['x1'], 'y0': l['y0'], 'y1': l['y1'], 'h': l['h'], 'fg': l['fg'], 'ko': l['ko'],
                             'free_r': l['free_r'], 'free_l': l['free_l']})
        for r in rows:
            m = 0.35 * r['h']
            nb_r = any(oid != j['id'] and abs(ol['x0'] - r['free_r']) < 0.6 * r['h'] and ol['y0'] < r['y1'] and ol['y1'] > r['y0'] for oid, ol in allboxes)
            nb_l = any(oid != j['id'] and abs(ol['x1'] - r['free_l']) < 0.6 * r['h'] and ol['y0'] < r['y1'] and ol['y1'] > r['y0'] for oid, ol in allboxes)
            edge_r = min(r['free_r'], int(W - 0.6 * r['h']))   # 이미지 오른쪽 끝에서 글자 높이 0.6배 안쪽까지만
            r['lim_r'] = int(r['x1'] + (r['free_r'] - r['x1']) * 0.5) if nb_r else int(max(r['x1'], edge_r - m))
            r['lim_l'] = int(r['x0'] - (r['x0'] - r['free_l']) * 0.5) if nb_l else int(min(r['x0'], r['free_l'] + m))
        r = rows[-1]; ya, yb = int(r['y1'] + 0.25 * r['h']), int(r['y1'] + 1.6 * r['h'])
        j['below_free'] = bool(yb < H and r['lim_r'] > r['x0'] and np.abs(im[ya:yb, r['x0']:r['lim_r']] - np.array(j['lines'][0]['bg'])).max() <= 12)
        if len(rows) > 1:
            pw = max(r['x1'] for r in rows)
            for r in rows: r['lim_r'] = min(r['lim_r'], pw + int(0.02 * (pw - rows[0]['x0'])))
        j['rows'] = rows

FONTS = f'file://{HERE}/assets/fonts'; FONTS_JA = f'file://{HERE}/assets/fonts_ja'
FAM = 'PretendardJP, PretendardS, sans-serif' if lang == 'ja' else 'PretendardS, sans-serif'
PAGE = f"""<!doctype html><html><head><meta charset=utf-8><style>
@font-face{{font-family:PretendardS;src:url({FONTS}/Pretendard-400.ttf);font-weight:400}}
@font-face{{font-family:PretendardS;src:url({FONTS}/Pretendard-500.ttf);font-weight:500}}
@font-face{{font-family:PretendardS;src:url({FONTS}/Pretendard-700.ttf);font-weight:700}}
@font-face{{font-family:PretendardJP;src:url({FONTS_JA}/PretendardJP-Regular.ttf);font-weight:400}}
@font-face{{font-family:PretendardJP;src:url({FONTS_JA}/PretendardJP-Medium.ttf);font-weight:500}}
@font-face{{font-family:PretendardJP;src:url({FONTS_JA}/PretendardJP-Bold.ttf);font-weight:700}}
</style></head><body><canvas id=c></canvas></body></html>"""
JS = r"""async ({src, jobs, fam}) => {
  for (const w of [400,500,700]) { await document.fonts.load(`${w} 40px PretendardS`, '가A'); await document.fonts.load(`${w} 40px PretendardJP`, 'あ亜'); }
  const img = new Image(); await new Promise((res, rej) => { img.onload = res; img.onerror = () => rej(new Error('load fail ' + src)); img.src = src; });
  const c = document.getElementById('c'); c.width = img.naturalWidth; c.height = img.naturalHeight;
  const g = c.getContext('2d'); g.drawImage(img, 0, 0);
  const log = [];
  const rgb = a => `rgb(${a[0]},${a[1]},${a[2]})`;
  for (const j of jobs) for (const l of j.lines) {
    const pad = Math.max(2, Math.round(l.h * 0.1)), vpad = Math.max(1, Math.round(l.h * 0.05));
    g.fillStyle = rgb(l.fill);
    g.fillRect(l.x0 - pad, l.y0 - vpad, (l.x1 - l.x0) + 2 * pad, (l.y1 - l.y0) + 2 * vpad);
  }
  for (const j of jobs) {
    const R = j.rows, R0 = R[0];
    g.textBaseline = 'alphabetic';
    // 굵기: 원래 한글을 400·500·700으로 같은 높이에 그려 잉크 밀도가 가장 가까운 것
    const inkDensity = (w) => { g.font = `${w} 100px PretendardS`; const m = g.measureText(R0.ko); return (m.actualBoundingBoxAscent + m.actualBoundingBoxDescent) > 0 ? m.width : 1; };
    let weight = j.bold ? 700 : 500;
    if (!j.bold && j.role !== 'title' && j.role !== 'header') weight = 400;
    g.font = `${weight} 100px PretendardS`;
    const km = g.measureText(R0.ko);
    const kInk = km.actualBoundingBoxAscent + km.actualBoundingBoxDescent;
    const kMid = (km.actualBoundingBoxDescent - km.actualBoundingBoxAscent) / 2;
    const pxH = (R0.y1 - R0.y0) / kInk * 100;
    const pxW = (j.lines[0].x1 - j.lines[0].x0) / (km.actualBoundingBoxRight + km.actualBoundingBoxLeft) * 100;
    const px = Math.min(pxH * 1.05, pxW * 1.05, Math.max(pxH, pxW) * 0.95);
    const base0 = (R0.y0 + R0.y1) / 2 - kMid * px / 100;
    const lineH = R.length > 1 ? (R[R.length-1].cy - R[0].cy) / (R.length - 1) : px * 1.45;
    const fixedBox = ['button','tab','badge','header','status'].includes(j.role);
    const floor = fixedBox ? 0.65 : 0.55;
    const setFont = p => { g.font = `${weight} ${p}px ${fam}`; };
    const wrap = (p, widths) => {
      setFont(p);
      const words = j.tr.split(/(?<=\s)|(?=[぀-ヿ一-鿿])|(?<=[぀-ヿ一-鿿、。])/);
      const out = []; let cur = '';
      for (const w of words) { const t = cur + w; const lim = widths[Math.min(out.length, widths.length - 1)]; if (cur && g.measureText(t.trimEnd()).width > lim) { out.push(cur.trimEnd()); cur = w.trimStart(); } else cur = t; }
      if (cur) out.push(cur.trimEnd());
      return out;
    };
    const rowAvail = r => {
      if (j.truncated) return r.x1 - r.x0;
      if (j.align === 'center') { const cx = (r.x0 + r.x1) / 2; return Math.max(r.x1 - r.x0, 2 * Math.min(cx - r.lim_l, r.lim_r - cx)); }
      if (j.align === 'right') return Math.max(r.x1 - r.x0, r.x1 - r.lim_l);
      return Math.max(r.x1 - r.x0, r.lim_r - R0.x0);
    };
    let widths = R.map(rowAvail), maxLines = R.length;
    const fits = (ls, ws) => ls.length <= maxLines && ls.every((t, i) => g.measureText(t).width <= ws[Math.min(i, ws.length - 1)] + 0.5);
    let p = px, lines = wrap(p, widths);
    while (!fits(lines, widths) && p > px * 0.85) { p -= px * 0.02; lines = wrap(p, widths); }
    if (!fits(lines, widths) && R.length === 1 && j.below_free && !fixedBox && !j.truncated && maxLines === 1) { maxLines = 2; p = px; lines = wrap(p, widths); while (!fits(lines, widths) && p > px * 0.85) { p -= px * 0.02; lines = wrap(p, widths); } }
    if (!fits(lines, widths) && j.align === 'center' && R.length === 1) {
      const alt = [Math.max(R0.x1 - R0.x0, R0.lim_r - R0.x0)]; let q = px, l2 = wrap(q, alt);
      while (!fits(l2, alt) && q > px * 0.85) { q -= px * 0.02; l2 = wrap(q, alt); }
      if (fits(l2, alt) && q > p) { j.align = 'left'; widths = alt; p = q; lines = l2; }
    }
    while (!fits(lines, widths) && p > px * floor) { p -= px * 0.02; lines = wrap(p, widths); }
    while (!fits(lines, widths) && p > px * 0.45) { p -= px * 0.02; lines = wrap(p, widths); }
    let over = fits(lines, widths) ? 0 : 1;
    if (j.truncated) { lines = [j.tr]; over = 0; }
    else if (maxLines === 1 && lines.length > 1) lines = [j.tr];
    else if (lines.length > maxLines) lines = [...lines.slice(0, maxLines - 1), lines.slice(maxLines - 1).join(' ')];
    setFont(p);
    g.fillStyle = `rgb(${R0.fg[0]},${R0.fg[1]},${R0.fg[2]})`;
    lines.forEach((t, i) => {
      const r = R[Math.min(i, R.length - 1)];
      const base = base0 + i * lineH;
      const w = g.measureText(t).width;
      const x = j.align === 'center' ? (r.x0 + r.x1) / 2 - w / 2 : j.align === 'right' ? r.x1 - w : R0.x0;
      g.save();
      if (j.truncated || over) { g.beginPath(); g.rect(R0.lim_l - 2, R0.y0 - R0.h, (R0.lim_r - R0.lim_l) + 4, R0.h * 3); g.clip(); }
      g.fillText(t, x, base);
      g.restore();
    });
    log.push({id: j.id, px: Math.round(px*10)/10, used: Math.round(p*10)/10, weight, lines: lines.length, over, align: j.align});
  }
  return {data: c.toDataURL('image/png'), log};
}"""

async def main():
    tmp = f'{OUT}/_render.html'; open(tmp, 'w').write(PAGE)
    out_segments = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='chrome', args=['--allow-file-access-from-files'])
        pg = await b.new_page()
        await pg.goto('file://' + tmp)
        files = sorted(f for f in os.listdir(KO) if re.match(r's\d+_\d+[a-z]?_\d+\.png$', f))
        if a.only: files = [a.only]
        for f in files:
            lst = jobs.get(f, [])
            r = None
            for attempt in range(3):   # 그리기가 멈추면(기계가 바쁠 때 Chrome이 응답을 안 함) 60초 뒤 페이지를 다시 열고 다시 그린다
                try:
                    r = await asyncio.wait_for(pg.evaluate(JS, {'src': f'file://{KO}/{f}', 'jobs': lst, 'fam': FAM}), timeout=60)
                    break
                except (asyncio.TimeoutError, Exception) as e:
                    print(f'retry {f} ({attempt + 1}): {type(e).__name__}', file=sys.stderr)
                    try: await pg.close()
                    except Exception: pass
                    pg = await b.new_page(); await pg.goto('file://' + tmp)
            if r is None: raise SystemExit(f'render failed: {f}')
            open(f'{OUT}/{f}', 'wb').write(base64.b64decode(r['data'].split(',', 1)[1]))
            logs = {x['id']: x for x in r['log']}
            recs = []
            for j in lst:
                lg = logs[j['id']]; l0 = j['lines'][0]
                scale = round(lg['used'] / lg['px'], 3)
                flag = '' if scale >= 0.85 and not lg['over'] else ('[확인 필요] 45%로도 넘침' if lg['over'] else ('[확인 필요] 85% 미만 축소' if scale >= (0.65 if j['role'] in ('button', 'tab', 'badge', 'header', 'status') else 0.55) else '[확인 필요] 축소 한계 미만'))
                recs.append({'id': j['id'], 'ko': j['ko'], 'tr': j['tr'], 'box_px_orig': [round(l0['x0'] / 2, 1), round(l0['y0'] / 2, 1), round((l0['x1'] - l0['x0']) / 2, 1), round((l0['y1'] - l0['y0']) / 2, 1)],
                             'font_px': lg['used'], 'scale': scale, 'weight': lg['weight'], 'paragraph_lines': lg['lines'], 'lines_in_segment': len(j['lines']),
                             'align': lg['align'], 'role': j['role'], 'flag': flag})
            out_segments[f] = {'replaced': len(recs), 'segments': recs, 'flags': [x for x in recs if x['flag']]}
            print(f, len(lst), 'flag', len(out_segments[f]['flags']))
        await b.close()
    os.remove(tmp)
    json.dump({'lang': lang, 'method': '한국어 글자 자리를 바탕색으로 덮고 번역어를 Pretendard(일본어 Pretendard JP)로 다시 그림. 생성형 AI 사용 안 함', 'files': out_segments},
              open(f'{OUT}/replacements.json', 'w'), ensure_ascii=False, indent=1)
    tot = sum(v['replaced'] for v in out_segments.values()); fl = sum(len(v['flags']) for v in out_segments.values())
    print(json.dumps({'vol': a.vol, 'lang': lang, 'replaced': tot, 'flagged': fl}, ensure_ascii=False))

asyncio.run(main())
