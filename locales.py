"""題名と説明の翻訳(YouTube の localizations)。視聴者の言語が日本語・スペイン語・フランス語・ドイツ語・ポルトガル語なら、
その言語の題名と説明が表示される。ほかの3チャンネル(locales.py)と同じ仕組み。AI は使わない。

題名には答えを書かないので、題名の型(describe.TITLES と make_short.KITCHEN_TITLES)と、
型に入る値(年数・国・年代)だけを訳せばよい。国はスペイン語などで形容詞の性・冠詞が変わるので、「(国名)」の形にする。
説明は、その言語の1行目のあとに英語の説明(選択肢・答え・出典)をそのまま続ける。
訳のない型・値なら、その言語は入れない(YouTube には英語が出る)。
"""
import describe

LANGS = ["ja", "es", "fr", "de", "pt"]

# 型の名前(upload_history.json の title_style)ごと。{n}: 年数(切り下げ済み)、{country}: 国、{when}: 年代
TITLES = {
    "age": {
        "ja": "{n}年以上前のこれ、何かわかる？🔍",
        "es": "Este objeto tiene más de {n} años. ¿Sabes qué es? 🔍",
        "fr": "Cet objet a plus de {n} ans. Sauras-tu ce que c'est ? 🔍",
        "de": "Dieses Objekt ist über {n} Jahre alt. Weißt du, was es ist? 🔍",
        "pt": "Este objeto tem mais de {n} anos. Sabe o que é? 🔍",
    },
    "age_culture": {
        "ja": "{n}年以上前の{country}の品。これは何？🔍",
        "es": "Un objeto de más de {n} años ({country}). ¿Qué es? 🔍",
        "fr": "Un objet de plus de {n} ans ({country}). Qu'est-ce que c'est ? 🔍",
        "de": "Ein über {n} Jahre altes Objekt ({country}). Was ist das? 🔍",
        "pt": "Um objeto com mais de {n} anos ({country}). O que é? 🔍",
    },
    "over_age": {
        "ja": "これは{n}年以上前のもの。何かわかる？🔍",
        "es": "Tiene más de {n} años. ¿Adivinas qué es? 🔍",
        "fr": "Il a plus de {n} ans. Devineras-tu ce que c'est ? 🔍",
        "de": "Es ist über {n} Jahre alt. Errätst du, was es ist? 🔍",
        "pt": "Tem mais de {n} anos. Consegue adivinhar o que é? 🔍",
    },
    "made_when": {
        "ja": "{when}に作られたもの。何かわかる？🔍",
        "es": "Hecho {when}. ¿Adivinas qué es? 🔍",
        "fr": "Fabriqué {when}. Devineras-tu ce que c'est ? 🔍",
        "de": "Hergestellt {when}. Errätst du, was es ist? 🔍",
        "pt": "Feito {when}. Consegue adivinhar o que é? 🔍",
    },
    "zoom": {
        "ja": "ズームアウトする前に、これが何かわかる？🔍",
        "es": "¿Sabes qué es antes de que se aleje la cámara? 🔍",
        "fr": "Sauras-tu ce que c'est avant le zoom arrière ? 🔍",
        "de": "Erkennst du es, bevor herausgezoomt wird? 🔍",
        "pt": "Sabe o que é antes de a câmera se afastar? 🔍",
    },
    "treasure": {
        "ja": "{n}年以上前のお宝。ズームアウトで正体は？🔍",
        "es": "Un tesoro de más de {n} años. ¿Qué es? 🔍",
        "fr": "Un trésor de plus de {n} ans. Qu'est-ce que c'est ? 🔍",
        "de": "Ein über {n} Jahre alter Schatz. Was ist das? 🔍",
        "pt": "Um tesouro com mais de {n} anos. O que é? 🔍",
    },
    "country": {
        "ja": "{country}の謎の品。これは何？🔍",
        "es": "Un objeto misterioso ({country}). ¿Qué es? 🔍",
        "fr": "Un objet mystère ({country}). Qu'est-ce que c'est ? 🔍",
        "de": "Ein rätselhaftes Objekt ({country}). Was ist das? 🔍",
        "pt": "Um objeto misterioso ({country}). O que é? 🔍",
    },
    "look_closer": {
        "ja": "よく見て…これは{n}年以上前のもの 🔍",
        "es": "Mira bien... este objeto tiene más de {n} años 🔍",
        "fr": "Regarde bien... cet objet a plus de {n} ans 🔍",
        "de": "Schau genau hin... dieses Objekt ist über {n} Jahre alt 🔍",
        "pt": "Olhe bem... este objeto tem mais de {n} anos 🔍",
    },
    "museum": {
        "ja": "近すぎてわからない？美術館の品を当てよう 🔍",
        "es": "¿Demasiado cerca? Adivina este objeto de museo 🔍",
        "fr": "Trop près pour deviner ? Un objet de musée 🔍",
        "de": "Zu nah zum Erkennen? Errate dieses Museumsobjekt 🔍",
        "pt": "Perto demais? Adivinhe este objeto de museu 🔍",
    },
    "someone_made": {
        "ja": "{when}に誰かが作ったもの。これは何？🔍",
        "es": "Alguien hizo esto {when}. ¿Qué es? 🔍",
        "fr": "Quelqu'un a fabriqué ceci {when}. Qu'est-ce que c'est ? 🔍",
        "de": "Jemand hat das {when} gemacht. Was ist das? 🔍",
        "pt": "Alguém fez isto {when}. O que é? 🔍",
    },
    "mystery_culture": {
        "ja": "{n}年以上前、{country}の謎の品を当てよう 🔍",
        "es": "Adivina este objeto misterioso de más de {n} años ({country}) 🔍",
        "fr": "Devine cet objet mystère de plus de {n} ans ({country}) 🔍",
        "de": "Errate dieses über {n} Jahre alte Rätselobjekt ({country}) 🔍",
        "pt": "Adivinhe este objeto misterioso com mais de {n} anos ({country}) 🔍",
    },
    "five_seconds": {
        "ja": "5秒でこれが何かわかる？🔍",
        "es": "¿Puedes decir qué es en 5 segundos? 🔍",
        "fr": "Sauras-tu nommer cet objet en 5 secondes ? 🔍",
        "de": "Erkennst du dieses Objekt in 5 Sekunden? 🔍",
        "pt": "Consegue dizer o que é em 5 segundos? 🔍",
    },
    "plain": {
        "ja": "これ、何かわかる？🔍",
        "es": "¿Sabes qué es esto? 🔍",
        "fr": "Sauras-tu ce que c'est ? 🔍",
        "de": "Weißt du, was das ist? 🔍",
        "pt": "Sabe o que é isto? 🔍",
    },
    # 昔の台所・家事の道具の回(make_short.KITCHEN_TITLES)
    "kitchen_old": {
        "ja": "昔の日用品、近くで見ると不思議な形。これは何？🔍",
        "es": "Esta vieja herramienta cotidiana se ve rara de cerca. ¿Qué es? 🔍",
        "fr": "Ce vieil outil du quotidien est étrange de près. Qu'est-ce que c'est ? 🔍",
        "de": "Dieses alte Alltagswerkzeug sieht von nah seltsam aus. Was ist das? 🔍",
        "pt": "Esta velha ferramenta do dia a dia parece estranha de perto. O que é? 🔍",
    },
    "kitchen_long_ago": {
        "ja": "昔の人が毎日使っていたもの。何かわかる？🔍",
        "es": "Hace mucho, la gente usaba esto a diario. ¿Adivinas qué es? 🔍",
        "fr": "Autrefois, on s'en servait tous les jours. Devineras-tu ce que c'est ? 🔍",
        "de": "Früher benutzte man das jeden Tag. Errätst du, was es ist? 🔍",
        "pt": "Antigamente, usava-se isto todos os dias. Consegue adivinhar o que é? 🔍",
    },
    "kitchen_mystery": {
        "ja": "昔の謎の道具。何に使ったもの？🔍",
        "es": "Una herramienta misteriosa de antaño. ¿Para qué servía? 🔍",
        "fr": "Un outil mystère d'autrefois. À quoi servait-il ? 🔍",
        "de": "Ein rätselhaftes Werkzeug von früher. Wofür war es? 🔍",
        "pt": "Uma ferramenta misteriosa de antigamente. Para que servia? 🔍",
    },
}

LEAD = {
    "ja": "ズームアウトする前に当ててみてね！👀 美術館の品を超ドアップで見せるクイズです。",
    "es": "¡Adivina antes de que se aleje la cámara! 👀 Un quiz con objetos de museo vistos muy de cerca.",
    "fr": "Devine avant le zoom arrière ! 👀 Un quiz d'objets de musée vus de très près.",
    "de": "Rate, bevor herausgezoomt wird! 👀 Ein Quiz mit Museumsobjekten, ganz aus der Nähe.",
    "pt": "Adivinhe antes de a câmera se afastar! 👀 Um quiz com objetos de museu vistos bem de perto.",
}
KITCHEN_LEAD = {
    "ja": "昔の日用品を超ドアップで。何に使ったものか当ててみてね！🔍",
    "es": "Una vieja herramienta cotidiana, vista muy de cerca. ¿Sabes para qué servía? 🔍",
    "fr": "Un vieil outil du quotidien, vu de très près. Sauras-tu à quoi il servait ? 🔍",
    "de": "Ein altes Alltagswerkzeug, ganz aus der Nähe. Weißt du, wofür es war? 🔍",
    "pt": "Uma velha ferramenta do dia a dia, vista bem de perto. Sabe para que servia? 🔍",
}

# describe.COUNTRY の英語名 → 各言語
COUNTRIES = {
    "Germany": {"ja": "ドイツ", "es": "Alemania", "fr": "Allemagne", "de": "Deutschland", "pt": "Alemanha"},
    "Italy": {"ja": "イタリア", "es": "Italia", "fr": "Italie", "de": "Italien", "pt": "Itália"},
    "France": {"ja": "フランス", "es": "Francia", "fr": "France", "de": "Frankreich", "pt": "França"},
    "Britain": {"ja": "イギリス", "es": "Gran Bretaña", "fr": "Grande-Bretagne", "de": "Großbritannien",
                "pt": "Grã-Bretanha"},
    "England": {"ja": "イングランド", "es": "Inglaterra", "fr": "Angleterre", "de": "England", "pt": "Inglaterra"},
    "Spain": {"ja": "スペイン", "es": "España", "fr": "Espagne", "de": "Spanien", "pt": "Espanha"},
    "the Netherlands": {"ja": "オランダ", "es": "Países Bajos", "fr": "Pays-Bas", "de": "Niederlande",
                        "pt": "Países Baixos"},
    "Flanders": {"ja": "フランドル", "es": "Flandes", "fr": "Flandre", "de": "Flandern", "pt": "Flandres"},
    "Japan": {"ja": "日本", "es": "Japón", "fr": "Japon", "de": "Japan", "pt": "Japão"},
    "China": {"ja": "中国", "es": "China", "fr": "Chine", "de": "China", "pt": "China"},
    "India": {"ja": "インド", "es": "India", "fr": "Inde", "de": "Indien", "pt": "Índia"},
    "Iran": {"ja": "イラン", "es": "Irán", "fr": "Iran", "de": "Iran", "pt": "Irã"},
    "Turkey": {"ja": "トルコ", "es": "Turquía", "fr": "Turquie", "de": "Türkei", "pt": "Turquia"},
    "Austria": {"ja": "オーストリア", "es": "Austria", "fr": "Autriche", "de": "Österreich", "pt": "Áustria"},
    "Switzerland": {"ja": "スイス", "es": "Suiza", "fr": "Suisse", "de": "Schweiz", "pt": "Suíça"},
    "America": {"ja": "アメリカ", "es": "Estados Unidos", "fr": "États-Unis", "de": "USA", "pt": "Estados Unidos"},
    "Russia": {"ja": "ロシア", "es": "Rusia", "fr": "Russie", "de": "Russland", "pt": "Rússia"},
    "Korea": {"ja": "朝鮮半島", "es": "Corea", "fr": "Corée", "de": "Korea", "pt": "Coreia"},
    "Persia": {"ja": "ペルシア", "es": "Persia", "fr": "Perse", "de": "Persien", "pt": "Pérsia"},
    "Sweden": {"ja": "スウェーデン", "es": "Suecia", "fr": "Suède", "de": "Schweden", "pt": "Suécia"},
    "Denmark": {"ja": "デンマーク", "es": "Dinamarca", "fr": "Danemark", "de": "Dänemark", "pt": "Dinamarca"},
    "Poland": {"ja": "ポーランド", "es": "Polonia", "fr": "Pologne", "de": "Polen", "pt": "Polônia"},
}


def roman(n):
    out = ""
    for v, s in ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        while n >= v:
            out, n = out + s, n - v
    return out


def when(o, lang):
    """describe.year_phrase と同じ区切りで、各言語の年代。作れなければ None。"""
    b, e = o.get("objectBeginDate"), o.get("objectEndDate")
    if not isinstance(b, int) or not isinstance(e, int) or b <= 0 or e < b:
        return None
    if b == e:
        return {"ja": f"{b}年", "es": f"en {b}", "fr": f"en {b}", "de": f"{b}", "pt": f"em {b}"}[lang]
    if e - b <= 30:
        y = round((b + e) / 2 / 10) * 10
        return {"ja": f"{y}年ごろ", "es": f"hacia {y}", "fr": f"vers {y}", "de": f"um {y}",
                "pt": f"por volta de {y}"}[lang]
    if e - b <= 110:
        c = (b + e) // 2 // 100 + 1
        if not 4 <= c <= 20:
            return None
        return {"ja": f"{c}世紀", "es": f"en el siglo {roman(c)}", "fr": f"au {roman(c)}ᵉ siècle",
                "de": f"im {c}. Jahrhundert", "pt": f"no século {roman(c)}"}[lang]
    return None


def number_text(n, lang):
    """1500 → '1500'(日本語)/ '1.500'(es・de・pt)/ '1 500'(fr)。"""
    if lang == "ja" or n < 1000:
        return str(n)
    s = f"{n:,}"
    return s.replace(",", " " if lang == "fr" else ".")


def values(o, lang):
    _, age = describe.when(o)
    adj = describe.adjective(o)
    country = describe.COUNTRY.get(adj or "")
    return {
        "n": number_text(describe.round_age(age), lang) if age and age >= 100 else None,
        "country": COUNTRIES.get(country, {}).get(lang) if country else None,
        "when": when(o, lang),
    }


def build(style, number, o, description_en, kitchen=False):
    """Short の {言語: {"title", "description"}}。訳のない型・値の言語は入れない。"""
    if style not in TITLES:
        return {}
    out = {}
    for lang in LANGS:
        tpl = TITLES[style][lang]
        try:
            vals = values(o, lang) if o else {}
            q = tpl.format(**vals)
        except KeyError:
            continue
        if "None" in q:
            continue
        title = f"[{number}] {q}".replace("<", "‹").replace(">", "›")
        if len(title) > 100:
            continue
        desc = ((KITCHEN_LEAD if kitchen else LEAD)[lang] + "\n\n" + description_en)
        out[lang] = {"title": title, "description": desc.replace("<", "‹").replace(">", "›")[:4900]}
    return out


LONG_TITLES = {
    "ja": "超ドアップの美術館の品、{n}問わかる？ミステリー・オブジェクト #{number} 🔍",
    "es": "{n} objetos misteriosos #{number}: ¿sabes qué son vistos muy de cerca? 🔍",
    "fr": "{n} objets mystère #{number} : sauras-tu les reconnaître de très près ? 🔍",
    "de": "{n} rätselhafte Objekte #{number}: Erkennst du sie ganz aus der Nähe? 🔍",
    "pt": "{n} objetos misteriosos #{number}: sabe o que são vistos bem de perto? 🔍",
}
LONG_LEAD = {
    "ja": "どの品も近すぎるところから始まります。何問当たったか、コメントで教えてね！🔍",
    "es": "Cada objeto empieza demasiado cerca. ¡Cuenta cuántos aciertas y dímelo en los comentarios! 🔍",
    "fr": "Chaque objet commence beaucoup trop près. Compte tes points et dis-moi ton score en commentaire ! 🔍",
    "de": "Jedes Objekt beginnt viel zu nah. Zähl mit und schreib mir dein Ergebnis in die Kommentare! 🔍",
    "pt": "Cada objeto começa perto demais. Conte quantos acertou e me diga nos comentários! 🔍",
}


def build_long(n, number, description_en):
    """通常動画(longform.py)の {言語: {"title", "description"}}。"""
    out = {}
    for lang in LANGS:
        title = LONG_TITLES[lang].format(n=n, number=number)[:100]
        desc = (LONG_LEAD[lang] + "\n\n" + description_en).replace("<", "‹").replace(">", "›")[:4900]
        out[lang] = {"title": title, "description": desc}
    return out
