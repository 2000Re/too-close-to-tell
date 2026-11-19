"""写真から、どアップで映す場所を自動で選ぶ。

美術館の写真は背景が無地なので、
  1. 写真の縁の色を「背景」とみなして、物の形(マスク)を切り出す
  2. 9:16 の枠が物の内側に完全に収まり(輪郭が写らない)、模様が細かい場所を選ぶ
写真が小さい・ぼけている・背景が無地でない、などのときは None を返す(その作品は使わない)。
"""
import cv2
import numpy as np

MIN_SIDE = 2400            # 写真の短い辺がこれ未満なら使わない(拡大するとぼける)
MIN_START_W = 300          # 最初に映す幅(元の写真の画素)。これより狭くは寄らない
START_FRAC = 0.16          # 最初に映す幅 = 物の幅のこの割合(ただし MIN_START_W 以上)
PICK_PERCENTILE = 1.0      # どアップにする場所: 点数のいちばん高い場所(上位 20〜60% も試したが、正体の分かりやすさは変わらなかった)
ANALYSIS = 700             # 解析は長い辺をこの画素に縮めて行う


def object_mask(small):
    """縮めた写真(RGB, uint8)から、物の部分を True にしたマスク。失敗なら None。"""
    h, w, _ = small.shape
    f = small.astype(np.float32)
    b = max(4, int(min(h, w) * 0.03))
    # 背景のモデル: 各行の左端と右端の色を、横方向に直線でつなぐ(上下のグラデーションの背景に対応)
    left = np.median(f[:, :b], axis=1)                 # (h, 3)
    right = np.median(f[:, -b:], axis=1)
    t = np.linspace(0, 1, w)[None, :, None]
    bg = left[:, None, :] * (1 - t) + right[:, None, :] * t
    top = float(np.median(np.linalg.norm(f[:b] - bg[:b], axis=2)))
    bottom = float(np.median(np.linalg.norm(f[-b:] - bg[-b:], axis=2)))
    spread = min(top, bottom)               # 台座などで下の縁(または上の縁)に物がかかることはあるので、どちらかが合えばよい
    if spread > 12 or max(top, bottom) > 45:   # 上下とも背景のモデルと合わない = 無地の背景ではない
        return None
    diff = np.linalg.norm(f - bg, axis=2)
    thr = max(20.0, 4 * spread + 10)
    m = (diff > thr).astype(np.uint8)
    k = max(3, int(min(h, w) * 0.015)) | 1
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    if n < 2:
        return None
    big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    m = (lab == big).astype(np.uint8)
    # 穴を埋める(物の中の、背景と似た色の部分)
    ff = m.copy()
    mask2 = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(ff, mask2, (0, 0), 1)
    m = m | (1 - ff)
    frac = m.mean()
    touch = np.concatenate([m[0], m[-1], m[:, 0], m[:, -1]]).mean()
    if not 0.06 < frac < 0.85 or touch > 0.3:
        return None
    return m.astype(bool)


def choose(img):
    """(中心x, 中心y, 映す幅, 物の範囲(x0, y0, x1, y1)) を元の写真の画素で返す。使えない写真なら None。"""
    W, H = img.size
    if min(W, H) < MIN_SIDE:
        return None
    s = ANALYSIS / max(W, H)
    small = np.asarray(img.resize((int(W * s), int(H * s))))
    m = object_mask(small)
    if m is None:
        return None
    ys, xs = np.nonzero(m)
    obj_w = (xs.max() - xs.min()) / s
    bbox = (xs.min() / s, ys.min() / s, xs.max() / s, ys.max() / s)
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY).astype(np.float32)
    grad = np.hypot(cv2.Sobel(gray, cv2.CV_32F, 1, 0), cv2.Sobel(gray, cv2.CV_32F, 0, 1))
    ii_m = cv2.integral(m.astype(np.uint8))
    ii_g = cv2.integral(grad)
    # 最初の1枚が目を引くように: 模様の細かさに加えて、明暗の差と色の鮮やかさも見る
    ii_l, ii_l2 = cv2.integral(gray), cv2.integral(gray * gray)
    sat = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)[:, :, 1].astype(np.float32)
    ii_s = cv2.integral(sat)

    def box_sum(ii, x0, y0, x1, y1):
        return ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0]
    hs, ws = m.shape
    for start_w in sorted({max(MIN_START_W, START_FRAC * obj_w), MIN_START_W}, reverse=True):
        cw = start_w * s
        ch = cw * 16 / 9
        if cw < 8 or ch >= hs or cw >= ws:
            continue
        cands = []
        step = max(2, int(cw / 4))
        for y0 in range(0, int(hs - ch), step):
            for x0 in range(0, int(ws - cw), step):
                x1, y1 = int(x0 + cw), int(y0 + ch)
                area = (x1 - x0) * (y1 - y0)
                inside = ii_m[y1, x1] - ii_m[y0, x1] - ii_m[y1, x0] + ii_m[y0, x0]
                if inside < 0.995 * area:              # 輪郭(背景)が写る場所は使わない
                    continue
                detail = box_sum(ii_g, x0, y0, x1, y1) / area
                mean_l = box_sum(ii_l, x0, y0, x1, y1) / area
                contrast = max(0.0, box_sum(ii_l2, x0, y0, x1, y1) / area - mean_l ** 2) ** 0.5
                vivid = box_sum(ii_s, x0, y0, x1, y1) / area
                score = detail + 0.6 * contrast + 0.15 * vivid
                cands.append((score, (x0 + x1) / 2 / s, (y0 + y1) / 2 / s, detail))
        # 点数 = 模様の細かさ + 明暗の差 + 色の鮮やかさ。PICK_PERCENTILE の位置の場所を使う
        cands = [x for x in cands if x[3] > 6]
        cands.sort(key=lambda x: x[0])
        best = cands[min(len(cands) - 1, int(len(cands) * PICK_PERCENTILE))] if cands else None
        if best:                       # 模様がほとんどない(のっぺりした)場所しかないなら使わない
            cx, cy = best[1], best[2]
            # ピントの確認(元の解像度で、選んだ場所がぼけていないか)
            box = (int(cx - start_w / 2), int(cy - start_w * 8 / 9), int(cx + start_w / 2), int(cy + start_w * 8 / 9))
            crop = cv2.cvtColor(np.asarray(img.crop(box)), cv2.COLOR_RGB2GRAY)
            if cv2.Laplacian(crop, cv2.CV_64F).var() < 25:
                return None
            return cx, cy, start_w, bbox
    return None
