"""通常動画(横 1920x1080)「10 Mystery Objects」を作る。週1本、10問。

Shorts と同じメトロポリタン美術館のオープンデータ(CC0)・カテゴリ・3択・説明の作り方・声を使い、横長の画面用に
組み直したもの。右に美術館の写真、左の帯に問題・3択・残り時間を出す。

  0:00  導入  「Welcome to 10 Mystery Objects! Each one starts way too close. 5 seconds each. Keep score!」
  各問  どアップから少しずつ引く → 「Is it A, B, or C?」→ 5秒 → 一気に全体まで引いて答えと作品の情報
  最後  10点を並べて、点数の目安

答えと説明は美術館のデータ(describe.py)だけで作る。チャプターは「Object 1」などにして、答えは書かない。

使い方:
  python longform.py --tts dummy --rounds 3 --out out_long          試し(仮の声・3問)
  python longform.py --history longform_history.json --out out_long  本番(meta.json も書く)
  python longform.py --upload --dir out_long --privacy unlisted      投稿して longform_history.json に記録
"""
import argparse
import json
import math
import random
import subprocess
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image, ImageDraw

import catalog as K
import describe
import make_short as MS
import media as M

ROOT = Path(__file__).resolve().parent
HISTORY = ROOT / "longform_history.json"
SHORTS_HISTORY = ROOT / "upload_history.json"
TZ = ZoneInfo("Asia/Tokyo")
W, H, FPS = 1920, 1080, 30
SR = M.SR
ROUNDS = 10
THINK = 5.0
MIN_CHAPTER = 11.0              # YouTube のチャプターは1つ10秒以上
PANEL_W = 620
AW, AH = W - PANEL_W, H
NAVY = (10, 12, 18)
BG = (12, 14, 20)
GOLD, WHITE = M.GOLD, M.WHITE
HINT_ZOOM = 2.0                 # 考えている間に、最初の幅のこの倍まで引く
EVERYDAY_N = 7                  # 10問のうち、身近な物(catalog.EVERYDAY)の数
MAX_KITCHEN = 2                 # 昔の道具(catalog.KITCHEN)は2問まで
CHANNEL = "https://www.youtube.com/@too-close-to-tell"
SITE = MS.SITE
CREDIT_TEXT = "The Metropolitan Museum of Art · Open Access (CC0)"


# ---------------------------------------------------------------- 画面の部品


def font(size, bold=True):
    return M.font(M.SANS_BOLD if bold else M.SANS, size)


def text(lines, fnt, fill, width=PANEL_W, spacing=1.15, shadow=200):
    return M.text_layer(lines, fnt, fill, width=width, spacing=spacing, shadow=shadow)


def wrap(s, size, bold=True, max_lines=3):
    lines, fnt = M.fit_lines(s, M.SANS_BOLD if bold else M.SANS, PANEL_W - 110, [size, size - 4, size - 8],
                             max_lines=2)
    return lines[:max_lines], fnt


CREDIT = None


def chrome(img, no=None, total=ROUNDS):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, PANEL_W, H], fill=NAVY + (255,))
    d.text((PANEL_W / 2, 64), "10 MYSTERY OBJECTS" if total == 10 else f"{total} MYSTERY OBJECTS",
           font=font(30), fill=GOLD + (255,), anchor="mm")
    if no:
        d.text((PANEL_W / 2, 118), f"OBJECT {no} / {total}", font=font(40), fill=WHITE + (255,), anchor="mm")
        x0 = PANEL_W / 2 - (total - 1) * 24 / 2
        for k in range(total):
            c = GOLD if k < no else (70, 74, 90)
            d.ellipse([x0 + k * 24 - 6, 156 - 6, x0 + k * 24 + 6, 156 + 6], fill=c + (255,))
    band = Image.new("RGBA", (AW, 40), NAVY + (170,))          # 明るい写真の上でも出典が読めるように
    img.alpha_composite(band, (PANEL_W, H - 44))
    img.alpha_composite(CREDIT, (PANEL_W, H - 46))


def countdown(img, t, start, end, y=800):
    if not (start <= t < end + 0.3):
        return
    a = 1 - M.ease((t - end) / 0.3)
    left = max(0.0, end - t)
    d = ImageDraw.Draw(img)
    n = math.ceil(left) if left > 0 else 0
    if n:
        d.text((PANEL_W / 2, y), str(n), font=font(120), fill=GOLD + (int(255 * a),), anchor="mm",
               stroke_width=5, stroke_fill=NAVY + (255,))
    x0, x1, yb = 90, PANEL_W - 90, y + 95
    d.rounded_rectangle([x0, yb, x1, yb + 10], radius=5, fill=(255, 255, 255, int(60 * a)))
    frac = left / (end - start)
    if frac > 0:
        col = GOLD if frac > 0.3 else (235, 110, 90)
        d.rounded_rectangle([x0, yb, x0 + max(10, int((x1 - x0) * frac)), yb + 10], radius=5, fill=col + (int(255 * a),))


def info_box(tx):
    """答えのあとの説明(作品名・作り手と年代・何年前か)。どれも美術館のデータから(describe.texts)。"""
    t_lines, t_font = wrap(tx["title"], 40)
    m_lines, m_font = wrap(tx["meta"], 26, bold=False)
    layers = [text(t_lines, t_font, WHITE + (255,), spacing=1.1),
              text(m_lines, m_font, (225, 228, 236, 255))]
    if tx.get("age_line"):
        layers.append(text([tx["age_line"]], font(40), GOLD + (255,)))
    hgt = sum(x.height for x in layers) + 36
    box = Image.new("RGBA", (W, hgt + 10), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([36, 0, PANEL_W - 36, hgt], radius=20, fill=(22, 26, 40, 240),
                                          outline=GOLD + (200,), width=3)
    y = 16
    for x in layers:
        box.alpha_composite(x, (0, y))
        y += x.height - 2
    return box


# ---------------------------------------------------------------- 写真の表示


class Photo:
    """美術館の写真の一部(中心 cx, cy、幅 w、元の写真の画素)を、右の範囲(AW×AH)に描く。はみ出す部分は背景色。"""

    def __init__(self, img):
        self.img = img
        self.pyramid = [img]
        while max(self.pyramid[-1].size) > 1400:
            p = self.pyramid[-1]
            self.pyramid.append(p.resize((p.width // 2, p.height // 2), Image.LANCZOS))

    def view(self, cx, cy, w):
        h = w * AH / AW
        out = Image.new("RGB", (AW, AH), BG)
        src = self.pyramid[0]
        for p in self.pyramid:                      # 表示の大きさに足りる、いちばん小さい段
            if p.width / self.img.width * w >= AW:
                src = p
        kx, ky = src.width / self.img.width, src.height / self.img.height   # 縮小は //2 なので縦横で少し違う
        x0, y0 = cx - w / 2, cy - h / 2
        bx0, by0 = max(0.0, x0), max(0.0, y0)
        bx1, by1 = min(float(self.img.width), x0 + w), min(float(self.img.height), y0 + h)
        if bx1 - bx0 < 1 or by1 - by0 < 1:
            return out
        s = AW / w
        dx0, dy0 = int(round((bx0 - x0) * s)), int(round((by0 - y0) * s))
        dw, dh = max(1, int(round((bx1 - bx0) * s))), max(1, int(round((by1 - by0) * s)))
        box = (bx0 * kx, by0 * ky, min(float(src.width), bx1 * kx), min(float(src.height), by1 * ky))
        piece = src.resize((dw, dh), Image.BICUBIC, box=box)
        out.paste(piece, (dx0, dy0))
        return out


# ---------------------------------------------------------------- 1問


def round_object(o, img, spot, cat, no, total, tts, rng):
    tx = describe.texts(o, cat)
    labels, correct = K.choices_for(cat, rng)
    b, c = [x[:1].lower() + x[1:] if x.lower().startswith(("a ", "an ")) else x for x in labels[1:]]
    photo = Photo(img)
    sx, sy, start_w = spot[0], spot[1], spot[2]          # spot.choose は 9:16 の枠を返す。横長でも同じ幅で寄る
    x0, y0, x1, y1 = spot[3]
    ex, ey = (x0 + x1) / 2, (y0 + y1) / 2
    end_w = max((x1 - x0) * 1.25, (y1 - y0) * 1.25 * AW / AH)
    lines = {
        "q": f"Object {no}. What is it?",
        "c": f"Is it {labels[0][:1].lower() + labels[0][1:] if labels[0].lower().startswith(('a ', 'an ')) else labels[0]}"
             f", {b}, or {c}?",
        "ans": tx["say_answer"],
    }
    clips, dur = M.say_all(tts, lines)
    at = {"q": 0.3}
    at["c"] = at["q"] + dur["q"] + 0.25
    think = (at["c"] + dur["c"] + 0.2, at["c"] + dur["c"] + 0.2 + THINK)
    reveal = think[1] + 0.1
    pull = (reveal, reveal + 1.4)
    at["ans"] = pull[1] - 0.2
    info_t = at["ans"] + 0.4
    end = max(MIN_CHAPTER, info_t + 3.6)
    effects = [(M.sfx_whoosh(), 0.05), (M.sfx_pop(), at["c"])]
    effects += [(M.sfx_tick(), think[0] + k) for k in range(int(THINK))]
    effects += [(M.sfx_whoosh(), pull[0]), (M.sfx_ding(), at["ans"])]

    q = text(["What is it?"], font(56), WHITE + (255,))
    sub = text(["Guess before it zooms out!"], font(30), GOLD + (255,))
    pills = [M.pill(lb, (200, 205, 220), w=460, size=36) for lb in labels]
    right = M.pill(labels[correct], (200, 205, 220), w=460, size=36, glow=True)
    box = info_box(tx)
    w_hint = start_w * HINT_ZOOM

    def camera(t):
        if t < pull[0]:
            e = (min(t, think[1]) / think[1]) ** 1.3
            return sx, sy, start_w * HINT_ZOOM ** e
        u = M.ease((t - pull[0]) / (pull[1] - pull[0]))
        return sx + (ex - sx) * u, sy + (ey - sy) * u, math.exp(math.log(w_hint) + (math.log(end_w) - math.log(w_hint)) * u)

    def frame(t):
        img2 = Image.new("RGBA", (W, H), BG + (255,))
        img2.paste(photo.view(*camera(t)), (PANEL_W, 0))
        chrome(img2, no, total)
        r = M.ease((t - at["ans"]) / 0.3)
        qa = 1 - M.ease((t - info_t) / 0.4)
        if qa > 0:
            img2.alpha_composite(M.with_alpha(q, qa), (0, 220))
            img2.alpha_composite(M.with_alpha(sub, qa), (0, 300))
        for k, p in enumerate(pills):
            px, py = (PANEL_W - p.width) // 2, 390 + k * 110
            if t >= info_t:                                    # 答えのあとは、正解だけを上に残す
                if k == correct:
                    img2.alpha_composite(right, ((PANEL_W - right.width) // 2, 230))
                continue
            a_in = M.ease((t - at["c"] - 0.3 * k) / 0.3)
            if k == correct and r > 0:
                img2.alpha_composite(M.with_alpha(p, 1 - r), (px, py))
                img2.alpha_composite(M.with_alpha(right, r), (px, py))
            elif a_in > 0:
                img2.alpha_composite(M.with_alpha(p, a_in * (1 - 0.7 * r)), (px, py))
        countdown(img2, t, think[0], think[1], y=800)
        ia = M.ease((t - info_t) / 0.5)
        if ia > 0:
            img2.alpha_composite(M.with_alpha(box, ia), (0, 370))
        return img2

    thumb = photo.view(ex, ey, end_w)
    thumb.thumbnail((300, 300))
    return dict(clips=clips, at=at, effects=effects, end=end, frame=frame, key=f"met:{o['objectID']}", cat=cat,
                label=tx["answer"], thumb=thumb, thumb_t=(think[0] + think[1]) / 2,
                answer=f"{tx['answer']} — {tx['title']} ({tx['meta']}) {o.get('objectURL') or ''}".strip())


# ---------------------------------------------------------------- 導入と最後


def intro(tts, total, bg):
    lines = {"hi": f"Welcome to {total} Mystery Objects! Every object starts way too close. "
                   f"You get {int(THINK)} seconds each. Keep score, and see how many you can name!"}
    clips, dur = M.say_all(tts, lines)
    at = {"hi": 0.4}
    end = max(MIN_CHAPTER, at["hi"] + dur["hi"] + 0.8)
    t1 = text([str(total), "MYSTERY", "OBJECTS"], font(70), GOLD + (255,), spacing=1.05)
    t2 = text([f"from museum collections · {int(THINK)} seconds each"], font(28, bold=False), WHITE + (255,))
    t3 = text(["Keep score!"], font(44), WHITE + (255,))

    def frame(t):
        img = Image.new("RGBA", (W, H), BG + (255,))
        img.paste(bg, (PANEL_W, 0))
        chrome(img)
        img.alpha_composite(M.with_alpha(t1, M.ease(t / 0.6)), (0, 280))
        img.alpha_composite(M.with_alpha(t2, M.ease((t - 0.8) / 0.5)), (0, 560))
        img.alpha_composite(M.with_alpha(t3, M.ease((t - 1.6) / 0.5)), (0, 660))
        return img
    return dict(clips=clips, at=at, effects=[(M.sfx_whoosh(), 0.1)], end=end, frame=frame)


def outro(tts, rounds):
    total = len(rounds)
    lines = {"how": "How many did you get right? Tell me your score in the comments! "
                    "And follow for a new mystery object every day."}
    clips, dur = M.say_all(tts, lines)
    at = {"how": 0.4}
    end = max(MIN_CHAPTER, at["how"] + dur["how"] + 2.5)
    t1 = text(["How many did", "you get right?"], font(54), WHITE + (255,), spacing=1.1)
    hi, mid = math.ceil(total * 0.8), math.ceil(total * 0.5)
    tiers = text([f"{hi}–{total}: Museum curator", f"{mid}–{hi - 1}: Sharp eye", f"0–{mid - 1}: Too close to tell!"],
                 font(34), GOLD + (255,), spacing=1.5)
    cols = 5
    rows = math.ceil(total / cols)
    cw, chh = (AW - 80) / cols, (AH - 120) / rows
    f_lab = font(22)

    def frame(t):
        img = Image.new("RGBA", (W, H), BG + (255,))
        d = ImageDraw.Draw(img)
        for k, r in enumerate(rounds):
            a = M.ease((t - 0.3 - 0.15 * k) / 0.4)
            if a <= 0:
                continue
            cx = PANEL_W + 40 + cw * (k % cols + 0.5)
            cy = 60 + chh * (k // cols + 0.45)
            th = r["thumb"]
            img.alpha_composite(M.with_alpha(th.convert("RGBA"), a), (int(cx - th.width / 2), int(cy - th.height / 2)))
            d.text((cx, cy + 165), r["label"], font=f_lab, fill=WHITE + (int(255 * a),), anchor="mm")
        chrome(img)
        img.alpha_composite(M.with_alpha(t1, M.ease(t / 0.5)), (0, 260))
        img.alpha_composite(M.with_alpha(tiers, M.ease((t - 0.8) / 0.5)), (0, 460))
        return img
    return dict(clips=clips, at=at, effects=[(M.sfx_ding(), 0.2)], end=end, frame=frame)


# ---------------------------------------------------------------- 物の選び方


def pick(n, shorts_history, long_history, rng, log=print):
    """カテゴリが重ならない n 点。身近な物 EVERYDAY_N 点、昔の道具は MAX_KITCHEN 点まで、残りはそれ以外。
    Shorts と過去の通常動画で使った作品は使わない。どアップに向かない写真の作品は飛ばす(make_short.find)。"""
    used = {h["key"] for h in shorts_history} | {k for h in long_history for k in h.get("keys", [])}
    every = sorted(K.EVERYDAY)
    kitchen = sorted(K.KITCHEN)
    other = sorted(set(K.CATEGORIES) - K.EVERYDAY - K.KITCHEN)
    for xs in (every, kitchen, other):
        rng.shuffle(xs)
    n_every = min(EVERYDAY_N, n - 1)
    plan = every[:n_every + 3] + kitchen[:MAX_KITCHEN] + other
    chosen, groups_used, counts = [], set(), {"every": 0, "kitchen": 0, "other": 0}
    for cat in plan:
        if len(chosen) >= n:
            break
        kind = "every" if cat in K.EVERYDAY else "kitchen" if cat in K.KITCHEN else "other"
        limit = {"every": n_every, "kitchen": MAX_KITCHEN, "other": n}[kind]
        if counts[kind] >= limit or cat in groups_used:
            continue
        log(f"  カテゴリ: {cat}")
        found = MS.find(cat, used, rng, log)
        if not found:
            continue
        o, img, s = found
        chosen.append((o, img, s, cat))
        used.add(f"met:{o['objectID']}")
        groups_used |= (K.group_of(cat) - K.KITCHEN) | {cat}   # 似た物(楽器どうし等)は1つまで。昔の道具は上限で数える
        counts[kind] += 1
    if len(chosen) < n:
        raise SystemExit(f"使える作品が足りません({len(chosen)}/{n})")
    rng.shuffle(chosen)
    return chosen


# ---------------------------------------------------------------- 組み立て


def mix(segments):
    total = sum(s["end"] for s in segments)
    nn = int(math.ceil(total * SR)) + SR
    voice, fx = np.zeros(nn, np.float32), np.zeros(nn, np.float32)

    def put(buf, x, t):
        i = int(t * SR)
        x = x[: max(0, nn - i)]
        buf[i:i + len(x)] += x
    t0 = 0.0
    for s in segments:
        for k, x in s["clips"].items():
            put(voice, x, t0 + s["at"][k])
        for x, t in s["effects"]:
            put(fx, x, t0 + t)
        t0 += s["end"]
    m = voice / max(1e-6, float(np.abs(voice).max())) * 0.8 + fx * 0.35
    m /= max(1.0, float(np.abs(m).max()) / 0.95)
    return m, total


def write_wav(path, m):
    pcm = (np.clip(np.stack([m, m], 1), -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def starts_of(segments):
    out, t0 = [], 0.0
    for s in segments:
        out.append(t0)
        t0 += s["end"]
    return out


def render(mp4, wav, segments, total):
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", str(wav), "-map", "0:v", "-map", "1:a", "-shortest",
                          "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(mp4)], stdin=subprocess.PIPE)
    starts = starts_of(segments)
    try:
        k = 0
        for f in range(int(round(total * FPS))):
            t = f / FPS
            while k + 1 < len(segments) and t >= starts[k + 1]:
                k += 1
            p.stdin.write(segments[k]["frame"](t - starts[k]).convert("RGB").tobytes())
            if f % (FPS * 30) == 0:
                print(f"  {t:.0f}/{total:.0f} 秒", flush=True)
    finally:
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg が失敗しました")


def stamp(sec):
    sec = int(sec)
    return f"{sec // 60}:{sec % 60:02d}"


def check_chapters(starts, total):
    ends = starts[1:] + [total]
    short = [(stamp(a), round(b - a, 1)) for a, b in zip(starts, ends) if b - a < 10]
    if len(starts) < 3 or short:
        raise SystemExit(f"チャプターが YouTube の決まりを満たしません(10秒未満: {short})")


def thumbnail(seg, number, total, path, style="a"):
    """サムネイル(1280x720)。どアップのコマ(答えはまだ)に大きな文字。
    a = 題名(投稿のときに設定)/ b = 「What is it?」/ c = 「Can you get 10/10?」"""
    img = seg["frame"](0.5).convert("RGBA")
    ImageDraw.Draw(img).rectangle([0, 0, PANEL_W, H], fill=NAVY + (255,))
    if style == "b":
        img.alpha_composite(text(["What", "is it?"], font(120), WHITE + (255,), spacing=1.0, shadow=255), (0, 190))
        img.alpha_composite(text([f"{total} Mystery Objects #{number}"], font(40), GOLD + (255,), shadow=255), (0, 760))
    elif style == "c":
        img.alpha_composite(text(["Can you get", f"{total}/{total}?"], font(96), GOLD + (255,), spacing=1.0, shadow=255),
                            (0, 220))
        img.alpha_composite(text(["Museum objects,", "way too close"], font(54), WHITE + (255,), spacing=1.08,
                                 shadow=255), (0, 600))
    else:
        img.alpha_composite(text([str(total), "MYSTERY", "OBJECTS"], font(86), GOLD + (255,), spacing=1.0, shadow=255),
                            (0, 120))
        img.alpha_composite(text([f"#{number}"], font(52), WHITE + (255,), shadow=255), (0, 500))
        img.alpha_composite(text(["Can you name", "them all?"], font(64), WHITE + (255,), spacing=1.05, shadow=255),
                            (0, 660))
    img.convert("RGB").crop((0, 0, W - 96, H - 54)).resize((1280, 720), Image.LANCZOS).save(path, quality=90)


def description(number, rounds, starts):
    lines = [
        f"{len(rounds)} Mystery Objects #{number}: every museum object starts way too close. You get {int(THINK)} "
        "seconds to guess each one. Keep score and tell me how many you got right! 🔍",
        "",
        "Chapters:",
        f"{stamp(starts[0])} Intro",
    ]
    for i, st in enumerate(starts[1:-1], 1):
        lines.append(f"{stamp(st)} Object {i}")
    lines.append(f"{stamp(starts[-1])} Your score")
    lines += ["", "⬇️ Answers below (spoilers!) ⬇️", ".", ".", "."]
    lines += [f"{i}. {r['answer']}" for i, r in enumerate(rounds, 1)]
    lines += ["", "Images: The Metropolitan Museum of Art, Open Access (CC0). This channel is not affiliated with "
              "the museum.", "", f"A new mystery object every day: {CHANNEL}", f"Website: {SITE}/",
              "", "#whatisit #museum #guess #closeup"]
    return "\n".join(lines)


def build(args):
    global CREDIT
    CREDIT = text([CREDIT_TEXT], font(22, bold=False), (200, 205, 215, 230), width=AW, shadow=200)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    hp = Path(args.history) if args.history else None
    long_history = json.loads(hp.read_text().strip() or "[]") if hp and hp.exists() else []
    shorts = json.loads(SHORTS_HISTORY.read_text()) if SHORTS_HISTORY.exists() else []
    number = max([h["number"] for h in long_history], default=0) + 1
    rng = random.Random(f"long:{number}:{args.seed or ''}")
    n = args.rounds or ROUNDS
    print(f"#{number}: 作品を選んでいます", flush=True)
    chosen = pick(n, shorts, long_history, rng)
    tts = M.make_tts(args.tts)
    rounds = [round_object(o, img, s, cat, i, n, tts, rng) for i, (o, img, s, cat) in enumerate(chosen, 1)]
    bg = rounds[0]["frame"](0.0).crop((PANEL_W, 0, W, H)).convert("RGB")
    segments = [intro(tts, n, bg)] + rounds + [outro(tts, rounds)]
    m, total = mix(segments)
    starts = starts_of(segments)
    check_chapters(starts, total)
    wav = out / "audio.wav"
    write_wav(wav, m)
    print(f"動画を書き出しています({total:.0f} 秒)", flush=True)
    render(out / "video.mp4", wav, segments, total)
    wav.unlink()
    thumb_seg = next((r for r in rounds if r["cat"] in K.EVERYDAY), rounds[0])
    thumbnail(thumb_seg, number, n, out / "thumbnail.jpg")
    for style in ("b", "c"):
        thumbnail(thumb_seg, number, n, out / f"thumbnail_{style}.jpg", style)
    meta = {
        "number": number,
        "keys": [r["key"] for r in rounds],
        "categories": [r["cat"] for r in rounds],
        "date": datetime.now(TZ).date().isoformat(),
        "video": "video.mp4",
        "thumbnail": "thumbnail.jpg",
        "seconds": round(total, 1),
        "title": f"{n} Mystery Objects #{number}: Can You Tell What They Are From Extreme Close-Ups? 🔍"[:100],
        "description": description(number, rounds, starts).replace("<", "‹").replace(">", "›")[:4900],
        "tags": ["what is it", "guess the object", "close up", "zoom out", "museum", "quiz", "mystery objects"],
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    print(f"完了: {out / 'video.mp4'}({total:.0f} 秒)")
    print(meta["description"])


# ---------------------------------------------------------------- 投稿


THUMB_URL = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={}"
PUBLISH_WEEKDAY = 3             # 予約投稿の曜日(月曜が 0)。木曜
PUBLISH_TIME = (8, 13)             # 予約投稿の時刻(日本時間)。2026-11-28 に 19:13 から朝へ(アメリカ東部の前日の夜 18:13)


def scheduled_publish(now=None):
    """定期実行で作った回を公開する時刻(UTC の RFC3339)。GitHub の定期実行は数時間遅れることがあるので、
    早めに作って非公開で上げ、この時刻に YouTube が公開する(publishAt)。もう間に合わなければ None(すぐ公開する)。"""
    from datetime import timedelta
    now = now or datetime.now(TZ)
    if 1 <= (now.weekday() - PUBLISH_WEEKDAY) % 7 <= 2:      # 定期実行が日付をまたいで遅れた: 来週にせず、すぐ公開
        return None
    day = now.date() + timedelta(days=(PUBLISH_WEEKDAY - now.weekday()) % 7)
    target = datetime(day.year, day.month, day.day, *PUBLISH_TIME, tzinfo=TZ)
    if now > target - timedelta(minutes=10):
        return None
    return target.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def upload(args):
    import youtube_upload as Y
    out = Path(args.dir)
    meta = json.loads((out / "meta.json").read_text())
    hist_path = Path(args.history)
    history = json.loads(hist_path.read_text().strip() or "[]") if hist_path.exists() else []
    if any(h["number"] == meta["number"] for h in history):
        raise SystemExit(f"投稿済みの回です: #{meta['number']}")
    token = Y.connect()
    publish_at = scheduled_publish() if args.schedule else None
    if args.schedule and not publish_at:
        print("予約の時刻を過ぎたので、すぐ公開します")
    res = Y.upload(token, out / meta["video"], meta, args.privacy, publish_at)
    vid = res["id"]
    privacy = "public" if publish_at else res.get("status", {}).get("privacyStatus", args.privacy)
    if publish_at:
        print(f"予約投稿: {publish_at} に公開")
    print(f"uploaded: https://youtu.be/{vid} ({privacy})")
    Y.set_output("video_id", vid)
    thumb = out / meta.get("thumbnail", "thumbnail.jpg")
    if thumb.exists():
        try:
            Y.request(THUMB_URL.format(vid), data=thumb.read_bytes(), method="POST",
                      headers={"Authorization": f"Bearer {token}", "Content-Type": "image/jpeg"})
            print("thumbnail ok")
        except Exception as e:
            detail = e.read().decode(errors="replace")[:300] if hasattr(e, "read") else str(e)
            print(f"警告: サムネイルを設定できませんでした(YouTube Studio で設定してください): {detail}", file=sys.stderr)
    history.append({
        "number": meta["number"], "keys": meta["keys"], "categories": meta.get("categories"), "date": meta["date"],
        "title": meta["title"], "seconds": meta["seconds"], "video_id": vid, "privacy": privacy, "publish_at": publish_at,
        "uploaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    hist_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n")
    import playlists
    playlists.add_after_upload(token, history[-1])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--history", default=str(HISTORY))
    ap.add_argument("--tts", choices=["google", "dummy"], default="google")
    ap.add_argument("--rounds", type=int, help=f"問題の数(既定 {ROUNDS})")
    ap.add_argument("--seed")
    ap.add_argument("--out", default="out_long")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--dir", default="out_long")
    ap.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    ap.add_argument("--schedule", action="store_true", help="予約投稿にする(定期実行。scheduled_publish の時刻に公開)")
    args = ap.parse_args()
    if args.upload:
        upload(args)
    else:
        build(args)


if __name__ == "__main__":
    main()
