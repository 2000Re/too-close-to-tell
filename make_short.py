"""次の作品を選んで動画を作り、out/meta.json(題名・説明・タグなど)を書く。

使い方:
  python make_short.py --history upload_history.json --out out             # 本番(Google の声)
  python make_short.py --tts dummy --category violin --out /tmp/x           # 試し(仮の声・カテゴリを指定)
  python make_short.py --tts dummy --object 503045 --category violin --out /tmp/x
"""
import argparse
import json
import random
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import catalog as K
import describe
import media as M
import met
import spot
import video

TZ = ZoneInfo("Asia/Tokyo")
MAX_LOOKUPS = 40            # 1つのカテゴリで作品を何点まで調べるか
HASHTAGS = "#whatisit #guess #closeup #museum #shorts"
SITE = "https://2000re.github.io/too-close-to-tell"


def candidates(cat, rng):
    ids = []
    for q in K.CATEGORIES[cat][0]:
        try:
            ids += met.search(q)
        except Exception as e:
            print(f"  検索できません({q}): {e}")
    ids = list(dict.fromkeys(ids))
    if cat not in K.KITCHEN:        # 台所の道具は、検索結果の中で当てはまる物が少なく上の方に集まるので、順番のまま調べる
        rng.shuffle(ids)
    return ids


def find(cat, used, rng, log):
    """カテゴリの中から、使える作品を1点探す。(作品, 写真, 寄る場所) か None。"""
    for i in candidates(cat, rng)[:MAX_LOOKUPS]:
        if f"met:{i}" in used:
            continue
        try:
            o = met.obj(i)
        except Exception as e:          # Met は一時的に 403 を返し続けることがある。1点取れなくても次の候補へ
            log(f"  {i}: 作品の情報を取れません ({e})")
            continue
        if not K.ok_object(o, cat):
            continue
        try:
            img = met.image(o)
        except Exception as e:
            log(f"  {i}: 写真を取れません ({e})")
            continue
        s = spot.choose(img)
        log(f"  {i}: {o.get('objectName')} / {describe.clean(o.get('title'))[:40]} -> {'OK' if s else '写真が向かない'}")
        if s:
            return o, img, s
    return None


# 昔の台所・家事の道具の回の題名(その回の中で順に回す)
KITCHEN_TITLES = [
    ("kitchen_old", "This old everyday tool looks strange up close. What is it? 🔍"),
    ("kitchen_long_ago", "People used this every day long ago. Can you guess what it is? 🔍"),
    ("kitchen_mystery", "A mystery tool from long ago. What was it for? 🔍"),
]

LEADS = ["Can you tell what it is before it zooms out? 🔍", "Guess the object before the camera pulls back! 🔍",
         "How close is too close? Guess what this is! 🔎", "Pause and guess first, then watch it zoom out! 👀"]


# 姉妹チャンネル(説明欄の終わりで紹介する。上級者向け機能でリンクがクリックできる)
SISTERS = [
    ("🗺️ Wait, That Big? — the true size of countries on the map", "https://www.youtube.com/@wait-that-big"),
    ("🎨 Painted When? — guess the year a famous painting was made", "https://www.youtube.com/@painted-when"),
    ("🛰️ Guess From Space — name famous places from satellite images", "https://www.youtube.com/@guess-from-space"),
]


def latest_long():
    """いちばん新しい公開の通常動画(10 Mystery Objects)の (番号, URL)。なければ None。"""
    try:
        hist = json.loads((Path(__file__).resolve().parent / "longform_history.json").read_text() or "[]")
    except (OSError, ValueError):
        return None
    now = datetime.now().astimezone()
    pub = [h for h in hist if h.get("video_id") and h.get("privacy") == "public"      # 予約投稿で、まだ公開前の回は出さない
           and (not h.get("publish_at") or datetime.fromisoformat(h["publish_at"].replace("Z", "+00:00")) <= now)]
    return (pub[-1]["number"], f"https://youtu.be/{pub[-1]['video_id']}") if pub else None


TEASER_DAYS = 3         # 通常動画を投稿してからこの日数のうちに、予告編の Short を1本出す


def teaser_plan(history, now=None):
    """(通常動画の番号, URL, 作品の key, カテゴリ, 何問目, 問題の数) か None。
    いちばん新しい通常動画(10 Mystery Objects)を投稿してから TEASER_DAYS 日以内で、まだ予告編を出していなければ、
    その動画の作品から1点(最初の2問と、Shorts に出した作品は避ける)を選ぶ。"""
    from datetime import timezone
    now = now or datetime.now(timezone.utc)
    try:
        hist = json.loads((Path(__file__).resolve().parent / "longform_history.json").read_text() or "[]")
    except (OSError, ValueError):
        return None
    hist = [h for h in hist if h.get("video_id") and h.get("categories")]
    if not hist:
        return None
    lg = max(hist, key=lambda x: x["number"])
    if any(h.get("teaser") == lg["number"] for h in history):
        return None
    start = datetime.fromisoformat((lg.get("publish_at") or lg["uploaded_at"]).replace("Z", "+00:00"))     # 予約投稿なら公開の時刻から
    if now < start or (now - start).total_seconds() > TEASER_DAYS * 86400:
        return None
    used = {h["key"] for h in history}
    keys, cats = lg["keys"], lg["categories"]
    for i in sorted(range(len(keys)), key=lambda i: (i < 2, i)):
        if keys[i] not in used and cats[i] in K.CATEGORIES:
            return lg["number"], f"https://youtu.be/{lg['video_id']}", keys[i], cats[i], i + 1, len(keys)
    return None


def teaser_overlay(n_long, round_no, total):
    """最後の約2.5秒、上に「Object 4 of 10 · 10 Mystery Objects #1 / Play all 10 objects!」。"""
    from PIL import Image, ImageDraw
    l1 = M.text_layer([f"Object {round_no} of {total} · {total} Mystery Objects #{n_long}"], M.font(M.SANS_BOLD, 40),
                      M.WHITE, shadow=230)
    l2 = M.text_layer([f"Play all {total} objects!"], M.font(M.SANS_BOLD, 64), M.GOLD + (255,), shadow=230)
    hgt = l1.height + l2.height + 36
    band = Image.new("RGBA", (M.W, hgt), (0, 0, 0, 0))
    ImageDraw.Draw(band).rounded_rectangle([40, 0, M.W - 40, hgt], radius=28, fill=(8, 12, 24, 232),
                                           outline=M.GOLD + (220,), width=4)
    band.alpha_composite(l1, (0, 12))
    band.alpha_composite(l2, (0, 12 + l1.height))

    def overlay(img, t, end):
        a = M.ease((t - (end - 2.6)) / 0.4)
        if a > 0:
            img.alpha_composite(M.with_alpha(band, a), (0, 80))
        return img
    return overlay


def description(o, text):
    lead = ("An old everyday tool, seen far too close. Can you tell what it was for? 🔍" if text.get("kitchen")
            else LEADS[text.get("number", 1) % len(LEADS)])
    tz = text.get("teaser")
    return "\n".join([
        *([f"▶️ This is object {tz['round']} of {tz['total']} Mystery Objects #{tz['long']}. "
           f"Play all {tz['total']} objects: {tz['url']}", ""] if tz else []),
        lead,
        "",
        "Choices: " + " / ".join(text["choices"]),
        "",
        "Answer (spoiler!) ↓",
        "",
        "",
        f"{text['answer']}: {text['title']}",
        text["say_info"],
        "",
        f"Details: {o.get('objectURL') or 'https://www.metmuseum.org/'}",
        f"More mystery close-ups: {SITE}/",
        *([f"▶️ Try the full 10 Mystery Objects challenge #{latest_long()[0]}: {latest_long()[1]}"]
          if latest_long() else []),
        "Image: The Metropolitan Museum of Art, Open Access (CC0). This channel is not affiliated with the museum.",
        "",
        ("💬 Would you still use this today? Tell me in the comments!" if text.get("kitchen")
         else "💬 What did you guess? Tell me in the comments!"),
        "🔔 Follow for a new mystery object every day.",
        "",
        "More quizzes from the same creator:",
        *[f"{t}: {u}" for t, u in SISTERS],
        "",
        HASHTAGS,
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", default="upload_history.json")
    ap.add_argument("--out", default="out")
    ap.add_argument("--tts", default="google", choices=["google", "dummy"])
    ap.add_argument("--category", choices=list(K.CATEGORIES))
    ap.add_argument("--object", type=int, help="作品の ID を指定する(--category も必要)")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    hp = Path(args.history)
    history = json.loads(hp.read_text()) if hp.exists() else []
    used = {h["key"] for h in history}
    lp = Path(__file__).resolve().parent / "longform_history.json"      # 通常動画(longform.py)で使った作品も選ばない
    if lp.exists():
        used |= {k for h in json.loads(lp.read_text() or "[]") for k in h.get("keys", [])}
    number = max([h["number"] for h in history], default=0) + 1
    now = datetime.now(TZ)
    rng = random.Random(f"{now.date()}:{number}")

    found, cat = None, None
    teaser = teaser_plan(history) if not args.object and not args.category else None
    if teaser:
        # 通常動画の予告編の回(週1本): 通常動画の1点を、いつもの Shorts と同じ形で出し、最後に通常動画へ誘う
        print(f"予告編: 10 Mystery Objects #{teaser[0]} の {teaser[4]}問目 → {teaser[2]}")
        try:
            o = met.obj(int(teaser[2].split(":")[1]))
            img = met.image(o)
            s = spot.choose(img)
        except Exception as e:  # noqa: BLE001
            print(f"  予告編の作品を取れません({e})")
            s = None
        if s:
            found, cat = (o, img, s), teaser[3]
            M.OVERLAY = teaser_overlay(teaser[0], teaser[4], teaser[5])
        else:
            print("  予告編をやめて、ふつうの回にします")
            teaser = None
    if found:
        pass
    elif args.object:
        cat = args.category
        o = met.obj(args.object)
        img = met.image(o)
        s = spot.choose(img)
        if not s:
            raise SystemExit("この作品の写真は、どアップに向きません")
        found = (o, img, s)
    else:
        tried = []
        for _ in range(6):
            cat = args.category or K.next_category(history + [{"category": c} for c in tried], rng, number)
            print("カテゴリ:", cat)
            found = find(cat, used, rng, print)
            if found:
                break
            tried.append(cat)
        if not found:
            raise SystemExit("使える作品が見つかりませんでした")

    o, img, s = found
    text = describe.texts(o, cat)
    text["choices"], text["correct"] = K.choices_for(cat, rng)
    text["number"] = number
    text["kitchen"] = cat in K.KITCHEN
    if teaser:
        text["teaser"] = {"long": teaser[0], "url": teaser[1], "round": teaser[4], "total": teaser[5],
                          "outro": f"That was object {teaser[4]}. Want {teaser[5] - 1} more? "
                                   "Tap the link to play the full challenge!"}
    a, b, c3 = [x[:1].lower() + x[1:] if x.lower().startswith(("a ", "an ")) else x for x in text["choices"]]
    text["say_choices"] = f"{text['choices'][0]}, {b}, or {c3}?"
    seconds = video.render(img, s, text, M.make_tts(args.tts), out)
    if cat in K.KITCHEN:
        style_i = number // K.KITCHEN_EVERY % len(KITCHEN_TITLES)
        title_style, title = KITCHEN_TITLES[style_i]
    else:
        title, title_style = describe.video_title(o, number, [h.get("title", "") for h in history],
                                                  history[-1].get("title_style") if history else None)
    meta = {
        "number": number,
        "key": f"met:{o['objectID']}",
        "category": cat,
        "object_id": o["objectID"],
        "object_title": text["title"],
        "object_url": o.get("objectURL"),
        "date": now.date().isoformat(),
        "title": f"[{number}] {title}",
        "title_style": title_style,
        "ending": "short_quiet",
        "teaser": teaser[0] if teaser else None,     # 予告編の回なら通常動画の番号(teaser_plan が二度出さないため)
        "format": "kitchen" if cat in K.KITCHEN else "object",   # 昔の台所・家事の道具の回と、ふつうの回を比べる       # 説明を読み上げない短い版(2026-11-21〜。stats.md で比べる)
        "description": description(o, text),
        "tags": ["what is it", "guess the object", "close up", "zoom out", "museum", "quiz",
                 K.CATEGORIES[cat][4]] + (["antique kitchen tools", "old kitchen gadgets", "history"]
                                          if cat in K.KITCHEN else []),
        "answer": text["answer"],
        "spot": [round(v) for v in s[:3]],
        "site": {
            "answer": text["answer"],
            "title": text["title"],
            "info": text["say_info"],
            "meta": text["meta"],
            "image": o.get("primaryImageSmall") or o.get("primaryImage"),
            "museum_url": o.get("objectURL") or f"https://www.metmuseum.org/art/collection/search/{o['objectID']}",
            "category": cat,
        },
        "video": "video.mp4",
        "seconds": round(seconds, 1),
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: meta[k] for k in ("number", "key", "category", "object_title", "seconds")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
