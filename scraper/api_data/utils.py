def is_superboon_or_superbane(growthRate):
    match growthRate:
        case 30 | 50 | 75 | 95:
            return "superbane"
        case 25 | 45 | 70 | 90:
            return "superboon"
        case _:
            return ""
        
# convert game titles as received from the db
def convert_game_title(title):
    match title:
        case "Fire Emblem Echoes: Shadows of Valentia":
            return "Echoes"
        case "Fire Emblem Warriors: Three Hopes":
            return "Three Houses"
        case _:
            return title.replace("Fire Emblem", "").replace(":", "").strip()