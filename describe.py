"""美術館のデータから、答え・読み上げ・画面の説明を型にはめて作る(AI は使わない)。

例: "It's a violin!" / "A violin by Antonio Stradivari, from 1693. That's over 330 years old!"
"""
import html
import re
from datetime import date

import catalog as K

ORD = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth",
       10: "tenth", 11: "eleventh", 12: "twelfth", 13: "thirteenth", 14: "fourteenth", 15: "fifteenth",
       16: "sixteenth", 17: "seventeenth", 18: "eighteenth", 19: "nineteenth", 20: "twentieth"}
VAGUE = ("possibly", "probably", "or ", "?", "/", "style", "type", "and")


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(s or ""))).strip()


def adjective(o):
    """'German'、'Italian (Cremona)' → 'German'、'Italian'。あいまいなもの(possibly ... など)は使わない。"""
    c = clean(o.get("culture"))
    c = re.sub(r"\s*\(.*?\)", "", c).strip()
    if not c or any(v in c.lower() for v in VAGUE) or not re.fullmatch(r"[A-Z][a-z]+(?: [A-Z][a-z]+)?", c):
        return None
    return c


def place(o):
    """'from Germany' のような場所。culture が使えないときに country を使う。"""
    c = clean(o.get("country"))
    if c and not any(v in c.lower() for v in VAGUE) and re.fullmatch(r"[A-Z][A-Za-z ]+", c):
        return c
    return None


def maker(o):
    a = clean(o.get("artistDisplayName"))
    if not a or any(w in a.lower() for w in ("unknown", "workshop", "unidentified", "anonymous", "possibly", "attributed")):
        return None
    return a


def when(o):
    """(読み上げの時期, 何年前か)。'from 1693' / 'from around 1550' / 'from the fifteenth century'。"""
    b, e = o.get("objectBeginDate"), o.get("objectEndDate")
    if not isinstance(b, int) or not isinstance(e, int) or b <= 0 or e < b or e > date.today().year:
        return None, None
    age = date.today().year - e
    if b == e:
        phrase = f"from {b}"
    elif e - b <= 30:
        phrase = f"from around {round((b + e) / 2 / 10) * 10}"
    elif e - b <= 110:
        cent = (b + e) // 2 // 100 + 1
        if cent not in ORD:
            return None, age
        phrase = f"from the {ORD[cent]} century"
    else:
        return None, age
    return phrase, age


def article(word):
    return "an" if word[:1].lower() in "aeiou" else "a"


def round_age(age):
    """題名に出す年数(実際の年数を超えないように切り下げる): 254 → 250、516 → 500、137 → 130。"""
    if age >= 200:
        return age // 50 * 50
    return age // 10 * 10


def year_phrase(o):
    """'around 1550' / 'in 1693' / 'in the 15th century'(題名用、短く)。"""
    b, e = o.get("objectBeginDate"), o.get("objectEndDate")
    if not isinstance(b, int) or not isinstance(e, int) or b <= 0 or e < b:
        return None
    if b == e:
        return f"in {b}"
    if e - b <= 30:
        return f"around {round((b + e) / 2 / 10) * 10}"
    if e - b <= 110:
        c = (b + e) // 2 // 100 + 1
        return f"in the {c}th century" if 4 <= c <= 20 else None
    return None


# 題名の型(答えは書かない)。{years}: '500-year-old'、{n}: '500'、{adj}: 'German'、{when}: 'around 1550'
TITLES = [   # (必要な値, 型の名前[stats で型ごとに比べる], 題名)
    ("years", "age", "Can you guess this {years} object? 🔍"),
    ("years adj", "age_culture", "What is this {years} {adj} object? 🔍"),
    ("years", "over_age", "This is over {n} years old. Can you tell what it is? 🔍"),
    ("when", "made_when", "Made {when}. Can you guess what it is? 🔍"),
    ("", "zoom", "Can you tell what this is before it zooms out? 🔍"),
    ("years", "treasure", "Zoom out to reveal: what is this {years} treasure? 🔍"),
    ("country", "country", "A mystery object from {country}. What is it? 🔍"),
    ("years", "look_closer", "Look closer... this object is over {n} years old 🔍"),
    ("", "museum", "Too close to tell? Guess this museum object 🔍"),
    ("when", "someone_made", "Someone made this {when}. What is it? 🔍"),
    ("years adj", "mystery_culture", "Guess this {years} {adj} mystery object 🔍"),
    ("", "five_seconds", "Can you name this object in 5 seconds? 🔍"),
]
COUNTRY = {"German": "Germany", "Italian": "Italy", "French": "France", "British": "Britain", "English": "England",
           "Spanish": "Spain", "Dutch": "the Netherlands", "Flemish": "Flanders", "Japanese": "Japan",
           "Chinese": "China", "Indian": "India", "Iranian": "Iran", "Turkish": "Turkey", "Austrian": "Austria",
           "Swiss": "Switzerland", "American": "America", "Russian": "Russia", "Korean": "Korea", "Persian": "Persia",
           "Netherlandish": "the Netherlands", "Swedish": "Sweden", "Danish": "Denmark", "Polish": "Poland"}


def video_title(o, number, used=(), last_style=None):
    """(YouTube の題名, 型の名前)。答えは書かない。番号で型を順に回し(毎回ちがう型)、
    作品のデータで埋められない型と、過去と同じ題名は飛ばす。型は upload_history.json の title_style に残る。"""
    _, age = when(o)
    adj = adjective(o)
    old = age and age >= 100
    vals = {"years": f"{round_age(age):,}-year-old" if old else None, "n": f"{round_age(age):,}" if old else None,
            "adj": adj, "country": COUNTRY.get(adj or ""), "when": year_phrase(o)}
    used = {re.sub(r"^\[\d+\]\s*", "", t) for t in used}
    for k in range(len(TITLES)):
        need, style, tpl = TITLES[(number - 1 + k) % len(TITLES)]
        if any(not vals.get(w) for w in need.split()):
            continue
        t = tpl.format(**{k2: v for k2, v in vals.items() if v})
        if t not in used and style != last_style:      # 前の回と同じ型は使わない
            return t, style
    return "Can you tell what this is? 🔍", "plain"


def materials(o):
    """'Steel, gold' → 'steel and gold'。素材の書き方が長い・複雑なものは None(技法の説明などは読まない)。"""
    m = clean(o.get("medium")).split(";")[0]
    if not m or re.search(r"[\d()\[\]/]", m):
        return None
    parts = [p.strip().lower() for p in re.split(r",| and ", m) if p.strip()]
    if not parts or len(parts) > 4 or any(len(p.split()) > 3 for p in parts):
        return None
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


MATERIAL_LINES = ["Made of {m}.", "It's made of {m}."]


def texts(o, cat):
    _, _, _, answer, noun = K.CATEGORIES[cat]
    adj, who = adjective(o), maker(o)
    phrase, age = when(o)
    head = f"{adj} {noun}" if adj else noun
    sentence = f"{article(head).capitalize()} {head}"
    if who:
        sentence += f" by {who}"
    elif not adj and place(o):
        sentence += f" from {place(o)}"
    if phrase:
        sentence += f", {phrase}" if who or not adj else f" {phrase}"
    sentence += "."
    # 一言は1つだけ(動画を短く保つ): 100年以上前なら年数、そうでなければ素材
    mat = materials(o)
    if age and age >= 100:
        sentence += f" That's over {age // 10 * 10} years old!"
    elif mat:
        tpl = MATERIAL_LINES[(o.get("objectID") or 0) % len(MATERIAL_LINES)]
        sentence += " " + tpl.format(m=mat)
    meta_bits = [b for b in (who or clean(o.get("culture")) or place(o), clean(o.get("objectDate"))) if b]
    meta = ", ".join(meta_bits)
    medium = clean(o.get("medium"))
    if medium and len(medium) <= 60:
        meta += f" · {medium}"
    return {
        "answer": answer[:1].upper() + answer[1:],
        "say_answer": f"It's {answer}!",
        "say_info": sentence,
        "title": clean(o.get("title")) or noun.capitalize(),
        "meta": meta,
    }
