def is_superboon_or_superbane(growthRates):
    superboons = []
    superbanes = []
    for stat in growthRates:
        growthRate = growthRates[stat]
        match growthRate:
            case 30 | 50 | 75 | 95:
                return superbanes.append(stat)
            case 25 | 45 | 70 | 90:
                superboons.append(stat)
    result = {
        "superbanes": superbanes,
        "superboons": superboons,
    }
    return result
                
        
# convert game titles as received from the db
def convert_game_title(title):
    match title:
        case "Fire Emblem Echoes: Shadows of Valentia":
            return "Echoes"
        case "Fire Emblem Warriors: Three Hopes":
            return "Three Houses"
        case _:
            return title.replace("Fire Emblem", "").replace(":", "").strip()