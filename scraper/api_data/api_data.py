from mwbot import Bot
from dotenv import load_dotenv
import asyncio
import os
import json
import sys
from datetime import datetime
from special_heroes import get_harmonized, get_emblem, get_legendary, get_duo
from utils import is_superboon_or_superbane, convert_game_title
from queries import get_unit_skills, get_unit_release_update, get_new_units
# prevent "runtime error" errors
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

async def main():
    client = Bot(sitename="https://feheroes.fandom.com", api="https://feheroes.fandom.com/api.php", index="https://feheroes.fandom.com/wiki/Main_Page", username=os.environ["FEH_BOT_USERNAME"], password=os.environ["FEH_BOT_PASSWORD"])
    await client.login()
    scraping_output = {}

    last_successful_run = 0

    with open("marker.json", "r") as markerFile:
        marker_data = json.load(markerFile)
        last_successful_run = marker_data.get("lastSuccessfulRun", 0)

    unit_data = await get_new_units(client, last_successful_run)

    new_units_for_queries = []

    for entry in unit_data:
        unitProperties = {}
        dataInside = entry["title"]
        formattedWikipage = dataInside["WikiName"].replace(" ", "_")

        unitProperties["name"] = dataInside["Name"]
        unitProperties["title"] = dataInside["Title"]
        unitProperties["description"] = dataInside["Description"]
        unitProperties["move"] = dataInside["MoveType"]
        unitProperties["artist"] = dataInside["Artist"]
        color, weapon = dataInside["WeaponType"].split(" ")
        unitProperties["color"] = color
        unitProperties["id"] = dataInside["ID"]
        unitProperties["weapon"] = weapon
        unitProperties["voice"] = dataInside["ActorEN"]
        unitProperties["internal_id"] = dataInside["TagID"]
        unitProperties["resplendent"] = False
        unitProperties["resplendent_voice"] = False
        unitProperties["images"] = {
            "portrait": "https://feheroes.fandom.com/Special:Filepath/" + formattedWikipage + "_Face.webp",
            "attack": "https://feheroes.fandom.com/Special:Filepath/" + formattedWikipage + "_BtlFace.webp",
            "special": "https://feheroes.fandom.com/Special:Filepath/" + formattedWikipage + "_BtlFace_C.webp",
            "damage": "https://feheroes.fandom.com/Special:Filepath/" + formattedWikipage + "_BtlFace_D.webp",
        }
        unitProperties["resplendent_images"] = False
        unitProperties["release"] = dataInside["ReleaseDate"]
        unitProperties["origin"] = " + ".join(convert_game_title(title) for title in dataInside["Origin"].split(","))
        if len(dataInside["Gender"]) != 1:
            unitProperties["gender"] = dataInside["Gender"][0]
            # database data is either Female, Male or N
        else:
            unitProperties["gender"] = ""

        dbProperties = dataInside["Properties"]
        specialUnitProperties = {
            "emblem": False,
            "harmonized": False,
            "duo": False,
            "duel": False,
            "aided": False,
        }

        page = dataInside["Page"]
        
        if "emblem" in dbProperties:
            specialUnitProperties["emblem"] = await get_emblem(client, page)
        elif "harmonized" in dbProperties:
            specialUnitProperties["harmonized"] = await get_harmonized(client, page)
        elif "legendary" in dbProperties:
            legendaryProperties = await get_legendary(client, page)
            specialUnitProperties = {**specialUnitProperties, **legendaryProperties}
        elif "duo" in dbProperties:
            specialUnitProperties["duo"] = await get_duo(client, page)
        elif "aided" in dbProperties:
            specialUnitProperties["type"] = "aided"
        elif "chosen" in dbProperties:
            specialUnitProperties["type"] = "chosen"
        elif "entwined" in dbProperties
            specialUnitProperties["type"] = "entwined"

        unitProperties = {**unitProperties, **specialUnitProperties }

    for element in unitIdentityQuery["cargoquery"]:
        heroFullName = element['title']['Page']
        scraping_output[heroFullName] = {}
        new_units_for_queries.append("\"" + heroFullName + "\"")

    unitStatsPayload = {
        "tables": "UnitStats",
        "fields": "_pageName=Page, Lv1HP5, HPGR3, Lv1Atk5, AtkGR3, Lv1Spd5, SpdGR3, Lv1Def5, DefGR3, Lv1Res5, ResGR3",
        "where": f"_pageName in ({', '.join(new_units_for_queries)})"
    }
    
    unitStatsQuery = await client.call_get_api("cargoquery", **unitStatsPayload)

    for newUnit in new_units_for_queries:
        version = await get_unit_release_update(client, newUnit)
        del json[newUnit]["release"]
        json[newUnit]["version"] = version

    for element in unitStatsQuery["cargoquery"]:
        innerData = element["title"]
        page = innerData["Page"]
        scraping_output[page] = {
            "base": {
                "hp": int(innerData["Lv1HP5"]),
                "atk": int(innerData["Lv1Atk5"]),
                "spd": int(innerData["Lv1Spd5"]),
                "def": int(innerData["Lv1Def5"]),
                "res": int(innerData["Lv1Res5"])
            },
            "growth": {
                "hp": int(innerData["HPGR3"]),
                "atk": int(innerData["AtkGR3"]),
                "spd": int(innerData["SpdGR3"]),
                "def": int(innerData["DefGR3"]),
                "res": int(innerData["ResGR3"])
            }
        }

    growthRates = {
        "hp": int(innerData["HPGR3"]),
        "atk": int(innerData["AtkGR3"]),
        "spd": int(innerData["SpdGR3"]),
        "def": int(innerData["DefGR3"]),
        "res": int(innerData["ResGR3"])
    }
    supertraits = is_superboon_or_superbane(growthRates)
    scraping_output[dataInside["Page"]] = {**scraping_output[dataInside["Page"]], **supertraits}        
    
    skills = await get_unit_skills(client, new_units_for_queries)

    scraping_output[dataInside["Page"]] = {**scraping_output[dataInside["Page"]], **skills, **unitProperties}

    with open("marker.json", "w") as markerFile:
        today = datetime.now().timestamp()
        json.dump({ "lastSuccessfulRun": today }, markerFile)

    return scraping_output

if __name__ == "__main__":
    asyncio.run(main())
