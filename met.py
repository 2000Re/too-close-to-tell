"""メトロポリタン美術館 Collection API(キー不要)から、パブリックドメイン(CC0)の作品の情報と写真を取る。

https://metmuseum.github.io/ 。リクエストは1秒に5回まで(MIN_INTERVAL)に抑える。
"""
import io
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image

BASE = "https://collectionapi.metmuseum.org/public/collection"
USER_AGENT = os.environ.get("TCTT_USER_AGENT", "too-close-to-tell/1.0 (daily close-up quiz video)")
MIN_INTERVAL = 0.2
_last = [0.0]


def get(url, tries=4):
    url = urllib.parse.quote(url, safe=":/?&=%#+,;@~!$'()*")      # 画像の URL に空白が入っていることがある
    for k in range(tries):
        wait = MIN_INTERVAL - (time.monotonic() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.monotonic()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 500, 502, 503, 504) and k < tries - 1:
                time.sleep(2 ** (k + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if k < tries - 1:
                time.sleep(2 ** (k + 1))
                continue
            raise


def search(q):
    """写真があり、パブリックドメインの作品の ID の一覧。"""
    params = urllib.parse.urlencode({"q": q, "hasImages": "true", "isPublicDomain": "true"})
    data = json.loads(get(f"{BASE}/v1.1/search?{params}"))
    items = data if isinstance(data, list) else next(
        (data[k] for k in ("objectIDs", "objectIds", "results", "data", "items", "objects")
         if isinstance(data, dict) and isinstance(data.get(k), list)), [])
    ids = []
    for it in items:
        v = it if isinstance(it, (int, str)) else (it.get("objectID", it.get("objectId", it.get("id")))
                                                   if isinstance(it, dict) else None)
        if v is not None and str(v).isdigit():
            ids.append(int(v))
    return list(dict.fromkeys(ids))


def obj(object_id):
    try:
        return json.loads(get(f"{BASE}/v1/objects/{object_id}"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def image(o):
    return Image.open(io.BytesIO(get(o["primaryImage"]))).convert("RGB")
