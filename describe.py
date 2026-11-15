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


def video_title(o, number):
    """YouTube の題名(答えは書かない)。年代が分かれば「〇〇年前の物」として毎回変える。"""
    _, age = when(o)
    adj = adjective(o)
    if age and age >= 100:
        years = f"{round_age(age):,}-year-old"
        if adj and number % 2 == 0:
            return f"What is this {years} {adj} object? 🔍"
        return f"Can you guess this {years} object? 🔍"
    if adj:
        return f"Can you guess this {adj} object? 🔍"
    return "Can you tell what this is? 🔍"


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
    if age and age >= 100:
        sentence += f" That's over {age // 10 * 10} years old!"
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
