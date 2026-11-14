"""どアップから始めて、答えで一気に引く動画(1080x1920・30fps)。

  0秒〜      どアップ。「WHAT IS IT? / Guess before it zooms out!」少しずつ引く(ヒントが増える)
  残り3秒    3・2・1
  答え       一気に全体まで引いて、答え(金色の帯)と作品の情報
  最後       「What did you guess? Tell me in the comments!」
"""
import math

from PIL import Image, ImageDraw, ImageFilter

import media as M
from media import W, H

CREDIT = "The Metropolitan Museum of Art · Open Access (CC0)"
HINT_ZOOM = 2.3          # 答えまでに、最初の幅のこの倍まで引く
THINK = 3.0              # 「Last chance」から答えまでの秒数(3・2・1)


def make_canvas(img):
    """写真を暗い背景(展示ケースのよう)の上に、縁をなじませて置く。引ききったときに全体が 9:16 に収まる大きさ。"""
    iw, ih = img.size
    full_w = max(iw, ih * W / H) * 1.06
    cwi, chi = int(full_w), int(full_w * H / W)
    pad_x, pad_y = (cwi - iw) // 2, (chi - ih) // 2
    canvas = Image.new("RGB", (cwi, chi), (12, 14, 20))
    mask = Image.new("L", img.size, 0)
    feather = int(min(iw, ih) * 0.07)
    ImageDraw.Draw(mask).rounded_rectangle([feather, feather, iw - feather, ih - feather], radius=feather, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(feather * 0.7))
    canvas.paste(img, (pad_x, pad_y), mask)
    return canvas, pad_x, pad_y


def render(img, spot, text, tts, out):
    """img: 写真、spot: spot.choose() の結果、text: describe.texts() の結果。秒数を返す。"""
    canvas, pad_x, pad_y = make_canvas(img)
    cw, ch = canvas.size
    sx, sy, start_w = spot[0] + pad_x, spot[1] + pad_y, spot[2]
    # 引ききったときは、物全体がゆとりをもって収まる範囲(写真全体ではなく)。上の文字と下の答えの帯の分も空ける
    x0, y0, x1, y1 = spot[3]
    ex, ey = (x0 + x1) / 2 + pad_x, (y0 + y1) / 2 + pad_y + (y1 - y0) * 0.10
    end_w = min(max((x1 - x0) * 1.3, (y1 - y0) * 1.85 * W / H), cw, ch * W / H)

    lines = {
        "q": "What is it?",
        "c": "Can you tell yet?",
        "lock": "Last chance to guess!",
        "ans": text["say_answer"],
        "info": text["say_info"],
        "outro": "What did you guess? Tell me in the comments!",
    }
    clips, dur = M.say_all(tts, lines)
    at = {"q": 0.1}
    at["c"] = at["q"] + dur["q"] + 0.3
    at["lock"] = at["c"] + dur["c"] + 0.3
    reveal = at["lock"] + dur["lock"] + THINK
    pull = (reveal, reveal + 1.6)
    at["ans"] = pull[1] - 0.2
    at["info"] = at["ans"] + dur["ans"] + 0.3
    at["outro"] = at["info"] + dur["info"] + 0.5
    end = at["outro"] + dur["outro"] + 1.0
    effects = [(M.sfx_whoosh(), 0.0), *M.countdown_ticks(reveal), (M.sfx_whoosh(), pull[0]), (M.sfx_ding(), at["ans"])]
    wav = out / "audio.wav"
    M.write_audio(wav, end, clips, at, effects)

    def camera(t):
        w_hint = start_w * HINT_ZOOM
        if t < pull[0]:
            return sx, sy, start_w * HINT_ZOOM ** ((t / pull[0]) ** 1.3)
        u = M.ease((t - pull[0]) / (pull[1] - pull[0]))
        return sx + (ex - sx) * u, sy + (ey - sy) * u, math.exp(math.log(w_hint) + (math.log(end_w) - math.log(w_hint)) * u)

    def view(t):
        cx, cy, w = camera(t)
        w = min(w, cw, ch * W / H)
        h = w * H / W
        x0 = min(max(0.0, cx - w / 2), cw - w)
        y0 = min(max(0.0, cy - h / 2), ch - h)
        return canvas.resize((W, H), Image.Resampling.BICUBIC, box=(x0, y0, x0 + w, y0 + h)).convert("RGBA")

    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))            # 上下の暗い帯(文字を読みやすく)
    sd = ImageDraw.Draw(shade)
    for y in range(0, 360):
        sd.line([0, y, W, y], fill=(6, 8, 14, int(215 * (1 - y / 360) ** 1.4)))
    for y in range(H - 520, H):
        sd.line([0, y, W, y], fill=(6, 8, 14, int(225 * ((y - (H - 520)) / 520) ** 1.2)))

    kicker = M.text_layer(["WHAT IS IT?"], M.font(M.SANS_BOLD, 88), M.WHITE, shadow=230)
    sub = M.text_layer(["Guess before it zooms out!"], M.font(M.SANS_BOLD, 40), M.GOLD + (255,), shadow=220)
    answer = M.pill(text["answer"], (220, 220, 230), w=860, hgt=110, size=56, glow=True)
    f_count = M.font(M.SANS_BOLD, 150)
    t_lines, t_font = M.fit_lines(text["title"], M.SANS_BOLD, W - 160, [56, 50, 44, 40], max_lines=2)
    title = M.text_layer(t_lines, t_font, M.GOLD + (255,), shadow=230, spacing=1.1)
    m_lines, m_font = M.fit_lines(text["meta"], M.SANS, W - 160, [32, 28, 26], max_lines=2)
    meta = M.text_layer(m_lines, m_font, (235, 235, 240, 255), shadow=220)
    credit = M.text_layer([CREDIT], M.font(M.SANS, 24), (190, 195, 210, 235), shadow=180)
    info_h = title.height + meta.height + 10
    info_y = 1665                                  # 答えの帯の下

    def frame(t):
        im = view(t)
        im.alpha_composite(shade)
        im.alpha_composite(kicker, (0, 90))
        a_sub = 1 - M.ease((t - pull[0]) / 0.3)
        if a_sub > 0:
            im.alpha_composite(M.with_alpha(sub, a_sub), (0, 200))
        if 0 < reveal - t <= THINK:                            # 3・2・1
            n = math.ceil(reveal - t)
            ph = (reveal - t) - (n - 1)
            a = M.ease(ph / 0.25) * M.ease((1 - ph + 0.6) / 0.6)
            ImageDraw.Draw(im).text((W / 2, 1600), str(n), font=f_count, fill=(255, 255, 255, int(255 * a)),
                                    anchor="mm", stroke_width=8, stroke_fill=(10, 12, 18, int(255 * a)))
        rr = M.ease((t - at["ans"]) / 0.3)
        if rr > 0:
            im.alpha_composite(M.with_alpha(answer, rr), ((W - answer.width) // 2, 1505))
        M.timer_bar(im, t, 0.0, reveal, y=1690)
        ri = M.ease((t - at["info"]) / 0.4)
        if ri > 0:
            M.band(im, info_y - 14, info_y + info_h + 4, ri, x0=60, x1=W - 60)
            im.alpha_composite(M.with_alpha(title, ri), (0, info_y - 8))
            im.alpha_composite(M.with_alpha(meta, ri), (0, info_y + title.height))
        im.alpha_composite(credit, (0, 1868))
        return im

    M.render(out / "video.mp4", wav, end, frame)
    # サイトの一覧に出す、どアップの1枚(文字なし・答えが分からない)
    view(0.0).convert("RGB").resize((360, 640), Image.Resampling.LANCZOS).save(out / "closeup.jpg", quality=85)
    # サムネイル用に、答えの場面の1枚も残す
    frame(at["info"] + 1.0).convert("RGB").save(out / "reveal.jpg", quality=90)
    return end
