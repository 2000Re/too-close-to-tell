"""Too Close to Tell の再生リストの決め方(playlists.py が使う)。物の種類(catalog のカテゴリ)でまとめる。"""
HISTORIES = ["upload_history.json"]

GROUPS = [
    ({"jagging", "nutmeg", "corkscrew", "sugar_tongs", "mortar", "marrow", "trivet", "toaster"},
     ("Strange Old Everyday Tools Up Close", "Old everyday tools that look strange up close. Can you tell what they were for?")),
    ({"violin", "guitar", "lute", "mandolin", "trumpet", "horn", "drum"},
     ("Musical Instruments Too Close to Tell", "Extreme close-ups of historic musical instruments. Can you name them?")),
    ({"helmet", "armor", "mail", "shield", "gauntlet", "saddle", "stirrup", "spur"},
     ("Armor and Riding Gear Too Close to Tell", "Extreme close-ups of armor, helmets and riding gear from museum collections.")),
    ({"watch", "clock", "astrolabe", "globe", "sundial"},
     ("Clocks and Old Science Tools Too Close to Tell", "Clocks, watches, astrolabes and globes, seen far too close.")),
]
OTHER = ("Everyday Objects Too Close to Tell",
         "Shoes, teapots, spoons, hats and more from museum collections, seen far too close.")


def for_record(rec):
    cat = rec.get("category")
    if not cat:
        return []
    return [next((lst for cats, lst in GROUPS if cat in cats), OTHER)]
