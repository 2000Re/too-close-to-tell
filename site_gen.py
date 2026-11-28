"""Too Close to Tell のサイト(GitHub Pages、docs/)に、動画の一覧と動画ごとのページを作る。

データは docs/data/videos.json(投稿のたびに youtube_upload.py が1件足す)。そこから次を作り直す:
  docs/v/<番号>-<作品名>/index.html  動画ごとのページ(動画・「答えを見る」・作品の写真と情報・美術館へのリンク)
  docs/v/<番号>-<作品名>/closeup.jpg 一覧に出す、どアップの1枚(答えが分からないように)
  docs/v/index.html                  全部の一覧(新しい順)
  docs/index.html                    トップの「最新の動画」(<!-- LATEST:START --> 〜 END の間だけ書き換える)
  docs/sitemap.xml                   検索エンジン向けのページ一覧

作品の写真はリポジトリに保存せず、美術館の画像配信(primaryImageSmall)から表示する。
GitHub Actions の upload ジョブ(外部ライブラリなし)から使うので、標準ライブラリだけで書く。

使い方: python site_gen.py   (docs/data/videos.json からページを作り直す)
"""
import html
import json
import re
import shutil
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
DATA = DOCS / "data" / "videos.json"
SITE = "https://2000re.github.io/too-close-to-tell"
CHANNEL = "https://www.youtube.com/@too-close-to-tell"
LATEST = 12

e = html.escape


def slugify(text, limit=60):
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:limit].rstrip("-") or "object"


def entry_from(meta, video_id, uploaded_at):
    """make_short.py の meta.json とアップロード結果から、サイト用の1件を作る。"""
    s = meta["site"]
    return {
        "number": meta["number"],
        "slug": f"{meta['number']}-{slugify(s['title'])}",
        "video_id": video_id,
        "uploaded_at": uploaded_at,
        **s,
    }


def load():
    return json.loads(DATA.read_text()) if DATA.exists() else []


def save(entries):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(sorted(entries, key=lambda x: x["number"]), ensure_ascii=False, indent=1) + "\n")


def add(entry, closeup=None):
    """1件を足す。closeup はどアップの画像ファイル(一覧に出す)。"""
    entries = [x for x in load() if x["number"] != entry["number"]]
    entries.append(entry)
    save(entries)
    if closeup and Path(closeup).exists():
        d = DOCS / "v" / entry["slug"]
        d.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(closeup, d / "closeup.jpg")


# ---------------------------------------------------------------- 部品


def page(title, description, body, depth, canonical, extra_head=""):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
<link rel="icon" href="{up}icon.png">
<link rel="stylesheet" href="{up}style.css">
{extra_head}</head>
<body>
<header><div class="bar">
  <img src="{up}icon.png" alt="">
  <a class="name" href="{up}">Too Close to Tell</a>
  <nav><a href="{up}v/">All videos</a><a href="{up}privacy.html">Privacy</a><a href="{up}terms.html">Terms</a></nav>
</div></header>
<main>
{body}
</main>
<footer><div class="bar">© 2026 Too Close to Tell · <a href="{up}privacy.html">Privacy Policy</a> · <a href="{up}terms.html">Terms of Service</a></div></footer>
</body>
</html>
"""


# 作品の写真が開けないとき(美術館が画像を差し替えたなど)は、崩れた画像の代わりにこの表示を出す。
# 週1回の site_images.py が URL を直すまでのつなぎ
def on_error(text):
    return ("this.onerror=null;var d=document.createElement('div');d.className='img-missing';"
            f"d.textContent='{text}';this.replaceWith(d)")


def card(x, prefix):
    """一覧のカード。答えが分からないよう、どアップの1枚と番号だけを出す。"""
    return f"""<a class="card" href="{prefix}{e(x['slug'])}/">
  <img src="{prefix}{e(x['slug'])}/closeup.jpg" alt="Mystery close-up #{x['number']}" loading="lazy">
  <span class="card-no">#{x['number']}</span>
  <span class="card-title">What is it?</span>
</a>"""


def video_page(x, prev, nxt):
    title = f"What is it? Mystery close-up #{x['number']} — Too Close to Tell"
    desc = (f"Mystery close-up #{x['number']}: can you tell what this museum object is before the camera zooms out? "
            "Watch the video, then reveal the answer, the object and the museum link.")
    nav = []
    if prev:
        nav.append(f'<a href="../{e(prev["slug"])}/">← #{prev["number"]}</a>')
    nav.append('<a href="../">All videos</a>')
    if nxt:
        nav.append(f'<a href="../{e(nxt["slug"])}/">#{nxt["number"]} →</a>')
    body = f"""  <p class="muted">#{x['number']} · The Metropolitan Museum of Art</p>
  <h1>What is it?</h1>
  <div class="quiz-layout">
    <div class="short">
      <iframe src="https://www.youtube-nocookie.com/embed/{e(x['video_id'])}" title="Too Close to Tell #{x['number']}"
        loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen></iframe>
    </div>
    <div class="quiz">
      <img class="closeup" src="closeup.jpg" alt="Mystery close-up">
      <p>Make your guess, then check the answer.</p>
      <button type="button" class="reveal">Show the answer</button>
      <div class="answer" hidden>
        <p class="answer-year">It's <strong>{e(x['answer'].lower())}</strong>!</p>
        <img class="artwork" src="{e(x['image'])}" alt="{e(x['title'])}" loading="lazy"
          onerror="{e(on_error('Photo not available here. See it at the museum link below.'))}">
        <h2>{e(x['title'])}</h2>
        <p>{e(x['info'])}</p>
        <p class="muted">{e(x['meta'])}</p>
        <p><a href="{e(x['museum_url'])}">See it at The Metropolitan Museum of Art</a></p>
        <p class="muted">Image: The Metropolitan Museum of Art, Open Access (CC0). This site is not affiliated with the museum.</p>
      </div>
    </div>
  </div>
  <p class="pager">{' · '.join(nav)}</p>
  <p><a href="{CHANNEL}">New mystery close-ups every day on YouTube: @too-close-to-tell</a></p>
  <script>
  (function () {{
    var panel = document.querySelector(".answer"), btn = document.querySelector(".reveal");
    btn.addEventListener("click", function () {{ panel.hidden = false; btn.hidden = true; }});
  }})();
  </script>"""
    return page(title, desc, body, 2, f"{SITE}/v/{x['slug']}/")


def list_page(entries):
    cards = "\n".join(card(x, "") for x in reversed(entries))
    body = f"""  <h1>All videos</h1>
  <p>Every Too Close to Tell close-up so far, newest first. Can you tell what each one is? Open one to see the answer.</p>
  <div class="cards">
{cards}
  </div>"""
    return page("All videos — Too Close to Tell",
                "Every Too Close to Tell mystery close-up: museum objects from The Met's Open Access collection, "
                "so close you can't tell what they are.", body, 1, f"{SITE}/v/")


def latest_block(entries):
    cards = "\n".join(card(x, "v/") for x in list(reversed(entries))[:LATEST])
    return f"""<!-- LATEST:START (site_gen.py が書き換える) -->
  <h2>Latest videos</h2>
  <div class="cards">
{cards}
  </div>
  <p><a href="v/">See all videos →</a></p>
  <!-- LATEST:END -->"""


def sitemap(entries):
    urls = [f"{SITE}/", f"{SITE}/v/"] + [f"{SITE}/v/{x['slug']}/" for x in entries]
    items = "\n".join(f"  <url><loc>{e(u)}</loc></url>" for u in urls)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{items}
</urlset>
"""


def build(docs=DOCS):
    entries = sorted(load(), key=lambda x: x["number"])
    vdir = docs / "v"
    for i, x in enumerate(entries):
        d = vdir / x["slug"]
        d.mkdir(parents=True, exist_ok=True)
        prev = entries[i - 1] if i > 0 else None
        nxt = entries[i + 1] if i + 1 < len(entries) else None
        (d / "index.html").write_text(video_page(x, prev, nxt))
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "index.html").write_text(list_page(entries))
    top = docs / "index.html"
    s = top.read_text()
    s2 = re.sub(r"<!-- LATEST:START.*?<!-- LATEST:END -->", lambda m: latest_block(entries), s, flags=re.S)
    if "LATEST:START" not in s:
        raise SystemExit("docs/index.html に <!-- LATEST:START --> 〜 <!-- LATEST:END --> がありません")
    top.write_text(s2)
    (docs / "sitemap.xml").write_text(sitemap(entries))
    print(f"site: {len(entries)} videos")


if __name__ == "__main__":
    build()
