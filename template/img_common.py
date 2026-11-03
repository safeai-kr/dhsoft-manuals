"""캡처 글자 교체·검사 스크립트가 같이 쓰는 함수."""
import numpy as np
from scipy import ndimage


def modal_bbox(im):
    """반투명 덮개 위에 뜬 모달 화면이면 모달(가장 큰 밝은 상자)의 경계 (x0, y0, x1, y1)를, 아니면 None을 준다.
    im: HxWx3 int 배열. 판정: 가장 큰 밝은 덩어리의 상자가 이미지의 25% 이상이고, 그 바깥 픽셀의 절반 이상이 무채색 중간 회색(밝기 60~215)이면 모달.
    (2026-10-30 hy0909 결정: 모달 바깥의 흐려진 배경 글자는 번역하지 않는다. 덮으면 덮개 색과 어긋나 모달 가장자리가 울퉁불퉁해진다)"""
    H, W = im.shape[:2]; k = 4
    small = im[::k, ::k]
    bright = small.min(-1) >= 240
    lab, n = ndimage.label(bright)
    if n == 0: return None
    sizes = np.asarray(ndimage.sum(bright, lab, range(1, n + 1)))
    # 모달은 머리(제목 띠)·몸통·바닥이 선으로 나뉘어 밝은 덩어리가 여럿이다. 이미지의 1% 넘는 밝은 덩어리를 모두 합친 상자를 모달로 본다
    keep = np.isin(lab, np.where(sizes >= 0.01 * small.shape[0] * small.shape[1])[0] + 1)
    if not keep.any(): return None
    ys, xs = np.where(keep)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    if (x1 - x0) * (y1 - y0) < 0.25 * small.shape[0] * small.shape[1]: return None
    outside = np.ones(small.shape[:2], bool); outside[y0:y1, x0:x1] = False
    if outside.sum() < 0.05 * outside.size: return None
    o = small[outside]; lum = o.mean(-1); sat = o.max(-1) - o.min(-1)
    if ((lum >= 60) & (lum <= 215) & (sat <= 18)).mean() < 0.5: return None
    return int(x0 * k), int(y0 * k), int(min(W, x1 * k)), int(min(H, y1 * k))
