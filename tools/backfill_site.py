"""サイトの仕組みを入れる前に投稿した動画を、upload_history.json から docs/ に足す(美術館のデータを取り直す)。

使い方: python tools/backfill_site.py
"""
import json
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import describe  # noqa: E402
import met  # noqa: E402
import site_gen  # noqa: E402
import spot  # noqa: E402
import video  # noqa: E402
from media import W, H  # noqa: E402


def closeup(img, s, path):
    canvas, pad_x, pad_y = video.make_canvas(img)
    cx, cy, w = s[0] + pad_x, s[1] + pad_y, s[2]
    h = w * H / W
    canvas.resize((360, 640), Image.Resampling.LANCZOS,
                  box=(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)).save(path, quality=85)


def main():
    history = json.loads((ROOT / "upload_history.json").read_text())
    have = {x["number"] for x in site_gen.load()}
    for h in history:
        if h["number"] in have:
            continue
        o = met.obj(h["object_id"])
        text = describe.texts(o, h["category"])
        img = met.image(o)
        s = spot.choose(img)
        meta = {"number": h["number"], "site": {
            "answer": text["answer"], "title": text["title"], "info": text["say_info"], "meta": text["meta"],
            "image": o.get("primaryImageSmall") or o.get("primaryImage"),
            "museum_url": o.get("objectURL"), "category": h["category"]}}
        with tempfile.TemporaryDirectory() as d:
            cp = Path(d) / "closeup.jpg"
            closeup(img, s, cp)
            site_gen.add(site_gen.entry_from(meta, h["video_id"], h["uploaded_at"]), cp)
        print("added", h["number"], text["title"])
    site_gen.build()


if __name__ == "__main__":
    main()
