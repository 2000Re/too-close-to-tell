"""出す物の種類(カテゴリ)と、作品の選び方。

各カテゴリ: 検索語、作品名(objectName)の条件、答えの言い方。
答えと説明は、美術館のデータと下の表だけで作る(AI は使わない)。

扱わないもの:
  - 宗教・儀式で大切にされている物(仮面、儀式の道具など)
  - 人の骨・遺骸を使った物(素材や作品名に bone / human / skull などを含む物)
"""
import random

# key: (検索語のリスト, 作品名に含むべき語, 作品名に含んではいけない語, 答え(冠詞つき), 名詞)
CATEGORIES = {
    "violin": (["violin"], ["violin"], ["miniature", "kit", "bow"], "a violin", "violin"),
    "guitar": (["guitar"], ["guitar"], ["harp"], "a guitar", "guitar"),
    "lute": (["lute"], ["lute"], [], "a lute", "lute"),
    "mandolin": (["mandolin"], ["mandolin"], [], "a mandolin", "mandolin"),
    "trumpet": (["trumpet"], ["trumpet"], [], "a trumpet", "trumpet"),
    "horn": (["horn instrument", "french horn", "hunting horn"], ["horn"], ["powder", "drinking", "cup"], "a horn", "horn"),
    "drum": (["drum"], ["drum"], [], "a drum", "drum"),
    "helmet": (["helmet", "armet", "close helmet"], ["helmet", "armet", "burgonet", "sallet"], ["sketch", "drawing"],
               "a helmet", "helmet"),
    "armor": (["armor"], ["armor"], ["horse", "fragment", "sketch", "design", "drawing"], "a suit of armor", "suit of armor"),
    "mail": (["mail shirt", "shirt of mail"], ["mail"], ["mail-order"], "chain mail", "chain mail shirt"),
    "shield": (["shield"], ["shield"], ["boss", "design"], "a shield", "shield"),
    "gauntlet": (["gauntlet"], ["gauntlet"], [], "an armored glove", "armored glove"),
    "watch": (["pocket watch", "watch movement"], ["watch"], ["stand", "key", "print", "chatelaine"], "a pocket watch",
              "pocket watch"),
    "clock": (["table clock", "clock"], ["clock"], ["print", "drawing", "design"], "a clock", "clock"),
    "astrolabe": (["astrolabe"], ["astrolabe"], [], "an astrolabe", "astrolabe"),
    "globe": (["celestial globe", "terrestrial globe"], ["globe"], [], "a globe", "globe"),
    "sundial": (["sundial"], ["sundial"], [], "a sundial", "sundial"),
    "fan": (["folding fan", "fan"], ["fan"], ["fanfare", "print", "design", "drawing"], "a folding fan", "folding fan"),
    "saddle": (["saddle"], ["saddle"], ["rug", "cloth", "bag"], "a saddle", "saddle"),
    "shoes": (["shoes", "slippers", "boots"], ["shoe", "slipper", "boot"], ["buckle", "print", "photograph"],
              "a shoe", "shoe"),
    "teapot": (["teapot"], ["teapot"], [], "a teapot", "teapot"),
    "nautilus": (["nautilus cup", "nautilus shell"], ["nautilus"], [], "a seashell cup", "nautilus shell cup"),
    "snuffbox": (["snuffbox"], ["snuffbox"], [], "a snuffbox", "snuffbox"),
    "lock": (["lock and key", "padlock"], ["lock"], ["locket", "hair"], "a lock", "lock"),
    "stirrup": (["stirrup"], ["stirrup"], [], "a stirrup", "stirrup"),
    "spur": (["spur"], ["spur"], [], "a riding spur", "riding spur"),
    "chess": (["chess piece", "chessman"], ["chess"], ["board", "table", "print"], "a chess piece", "chess piece"),
    "basket": (["basket"], ["basket"], [], "a basket", "basket"),
}

BANNED = ("bone", "human", "skull", "hair", "mask", "reliquary", "ritual", "ceremonial", "shrine", "sacred", "funerary",
          "mummy", "coffin", "ivory")     # 象牙も避ける(素材として扱いに配慮が要る)

RECENT = 8      # 直近この本数に出たカテゴリは選ばない


def ok_object(o, cat):
    """カテゴリの作品として使ってよいか(写真の良し悪しは spot.py で見る)。"""
    if not o or not o.get("isPublicDomain") or not o.get("primaryImage"):
        return False
    _, need, avoid, _, _ = CATEGORIES[cat]
    name = (o.get("objectName") or "").lower()
    if not any(w in name for w in need) or any(w in name for w in avoid):
        return False
    text = " ".join(str(o.get(k) or "") for k in ("objectName", "title", "medium", "classification", "tags")).lower()
    return not any(b in text for b in BANNED)


def next_category(history, rng):
    recent = [h.get("category") for h in history[-RECENT:]]
    cats = [c for c in CATEGORIES if c not in recent] or list(CATEGORIES)
    return rng.choice(cats)
