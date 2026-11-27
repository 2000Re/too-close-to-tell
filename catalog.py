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
    "saddle": (["saddle"], ["saddle"], ["rug", "cloth", "bag", "steel", "plate", "pommel", "cantle", "fragment"],
               "a saddle", "saddle"),
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
    # 身近な物(2026-11-17 追加)
    "spoon": (["spoon"], ["spoon"], ["print", "drawing", "design"], "a spoon", "spoon"),
    "teacup": (["teacup", "cup and saucer"], ["cup"], ["stirrup", "drinking horn", "print", "nautilus"], "a teacup", "teacup"),
    "scissors": (["scissors"], ["scissors"], ["case", "sheath", "print", "drawing", "chatelaine"], "a pair of scissors",
                 "pair of scissors"),
    "candlestick": (["candlestick"], ["candlestick"], ["print", "drawing", "design"], "a candlestick", "candlestick"),
    "hat": (["hat"], ["hat"], ["hatpin", "print", "photograph", "drawing", "pin", "box"], "a hat", "hat"),
    "bottle": (["bottle"], ["bottle"], ["print", "drawing", "snuff"], "a bottle", "bottle"),
    # 昔の台所・家事の道具(2026-11-21 追加。KITCHEN_EVERY 本に1本)。どアップだと用途が分からない、見た目と用途の
    # ギャップを楽しむ回。答えは作品名(objectName)そのままの道具だけにする(作品名に need の語を含むものだけ)
    "jagging": (["jagging wheel"], ["jagging"], ["print", "drawing"], "a pie crimper", "pie crimper (jagging wheel)"),
    "nutmeg": (["nutmeg grater"], ["nutmeg"], ["print", "drawing"], "a nutmeg grater", "nutmeg grater"),
    "corkscrew": (["corkscrew"], ["corkscrew"], ["print", "drawing", "locks"], "a corkscrew", "corkscrew"),
    "sugar_tongs": (["sugar tongs"], ["sugar tongs"], ["print", "drawing"], "a pair of sugar tongs",
                    "pair of sugar tongs"),
    "mortar": (["mortar and pestle"], ["mortar and pestle", "mortar, pestle"], ["print", "drawing", "cosmetic"],
               "a mortar and pestle", "mortar and pestle"),
    "marrow": (["marrow scoop", "marrow spoon"], ["marrow"], ["print", "drawing", "?"], "a marrow spoon",
               "marrow spoon"),
    "trivet": (["trivet"], ["trivet"], ["print", "drawing"], "a trivet", "trivet"),
    "toaster": (["toaster"], ["toaster"], ["print", "drawing"], "a toaster", "toaster"),
}

# 昔の台所・家事の道具の回。番号が KITCHEN_EVERY の倍数の回は、ここから選ぶ(それ以外の回では選ばない)
KITCHEN = {"jagging", "nutmeg", "corkscrew", "sugar_tongs", "mortar", "marrow", "trivet", "toaster"}
KITCHEN_EVERY = 4
KITCHEN_TRIES = 3       # 昔の道具の回で、この種類だけ試してだめならふつうのカテゴリにする

# 今の暮らしで見かける身近な物。2026-11-17 の stats.md で、靴(422)は兜・盾・角笛(66〜108)の3倍以上見られていたので、
# 身近な物を中心に出す(EVERYDAY_SHARE の割合)。それ以外(武具・古い楽器・天文の道具など)もときどき出す
EVERYDAY = {"shoes", "teapot", "watch", "clock", "guitar", "violin", "drum", "trumpet", "fan", "lock", "chess", "basket",
            "globe", "spoon", "teacup", "scissors", "candlestick", "hat", "bottle"}
EVERYDAY_SHARE = 0.85

BANNED = ("bone", "human", "skull", "hair", "mask", "reliquary", "ritual", "ceremonial", "shrine", "sacred", "funerary",
          "mummy", "coffin", "ivory")     # 象牙も避ける(素材として扱いに配慮が要る)

RECENT = 8      # 直近この本数に出たカテゴリは選ばない

# 3択の外れは、ほかのカテゴリの答えから選ぶ(AI は使わない)。どアップで見分けがつかない仲間同士は、同じ回に並べない
GROUPS = [
    {"violin", "guitar", "lute", "mandolin"},
    {"trumpet", "horn"},
    {"helmet", "armor", "mail", "shield", "gauntlet"},
    {"watch", "clock", "sundial", "astrolabe", "globe"},
    {"saddle", "stirrup", "spur"},
    {"teapot", "teacup", "bottle", "nautilus", "spoon"},
    {"snuffbox", "lock"},
    {"shoes", "hat"},
    KITCHEN,            # 台所の道具どうしは並べない(外れは別の種類の物にして、見た目と用途のギャップを出す)
    {"marrow", "spoon"},    # 骨髄用スプーンもスプーンなので、「A spoon」と並べると答えが2つになる
    {"jagging", "scissors"},
]


def group_of(cat):
    """cat と同じ回に並べないカテゴリ(cat を含むすべての組を合わせたもの)。"""
    out = {cat}
    for g in GROUPS:
        if cat in g:
            out |= g
    return out


def choices_for(cat, rng):
    """(選択肢3つ, 正解の位置)。外れは別の仲間のカテゴリから2つ。身近な物(EVERYDAY)を優先する。"""
    taken = set(group_of(cat))
    wrong = []
    for _ in range(2):
        pool = [c for c in CATEGORIES if c not in taken and c not in KITCHEN]
        every = [c for c in pool if c in EVERYDAY]
        pick = rng.choice(every if every and rng.random() < 0.8 else pool)
        wrong.append(pick)
        taken |= group_of(pick)
    cats = [cat] + wrong
    rng.shuffle(cats)
    labels = [CATEGORIES[c][3][:1].upper() + CATEGORIES[c][3][1:] for c in cats]
    return labels, cats.index(cat)


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


def is_kitchen_turn(number):
    return number % KITCHEN_EVERY == 0


def next_category(history, rng, number=None, tried=()):
    """直近 RECENT 本に出ていないカテゴリから選ぶ。EVERYDAY_SHARE の割合で身近な物(EVERYDAY)から選ぶ。
    番号が KITCHEN_EVERY の倍数の回は、昔の台所・家事の道具(KITCHEN)から選ぶ(最近出したものは後回し)。
    tried: この回ですでに試して、使える写真がなかったカテゴリ。昔の道具を KITCHEN_TRIES 種類試してもだめなら、
    ふつうのカテゴリにする(2026-11-28: 昔の道具の多くは、美術館の写真がどアップに向かず、投稿が止まったため)。"""
    recent = [h.get("category") for h in history[-RECENT:]]
    if number and is_kitchen_turn(number) and sum(1 for c in tried if c in KITCHEN) < KITCHEN_TRIES:
        done = [h.get("category") for h in history if h.get("category") in KITCHEN]
        pool = [c for c in KITCHEN if c not in tried]
        fresh = [c for c in pool if c not in done[-3:]]
        if fresh or pool:
            # 最近出していない道具を先に。ただし、これまでに出せた道具(写真が向いていた)も候補に残す
            worked = [c for c in pool if c in done]
            pick_from = fresh if fresh and rng.random() < 0.5 else (worked or pool)
            return rng.choice(sorted(pick_from))
    tried_set = set(tried)
    cats = [c for c in CATEGORIES if c not in recent and c not in KITCHEN and c not in tried_set] or \
        [c for c in CATEGORIES if c not in KITCHEN and c not in tried_set]
    every = [c for c in cats if c in EVERYDAY]
    other = [c for c in cats if c not in EVERYDAY]
    if every and (not other or rng.random() < EVERYDAY_SHARE):
        return rng.choice(every)
    return rng.choice(other)
