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


LEADS = ["Can you tell what it is before it zooms out? 🔍", "Guess the object before the camera pulls back! 🔍",
         "How close is too close? Guess what this is! 🔎", "Pause and guess first, then watch it zoom out! 👀"]


def description(o, text):
    return "\n".join([
        LEADS[text.get("number", 1) % len(LEADS)],
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
        "Image: The Metropolitan Museum of Art, Open Access (CC0). This channel is not affiliated with the museum.",
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
    number = max([h["number"] for h in history], default=0) + 1
    now = datetime.now(TZ)
    rng = random.Random(f"{now.date()}:{number}")

    found, cat = None, None
    if args.object:
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
            cat = args.category or K.next_category(history + [{"category": c} for c in tried], rng)
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
    a, b, c3 = [x[:1].lower() + x[1:] if x.lower().startswith(("a ", "an ")) else x for x in text["choices"]]
    text["say_choices"] = f"{text['choices'][0]}, {b}, or {c3}?"
    seconds = video.render(img, s, text, M.make_tts(args.tts), out)
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
        "description": description(o, text),
        "tags": ["what is it", "guess the object", "close up", "zoom out", "museum", "quiz",
                 K.CATEGORIES[cat][4]],
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
