from time import sleep
from pprint import pprint
from mwbot import Bot
from dotenv import load_dotenv
import asyncio
import os
import json
import sys
from special_heroes import get_harmonized, get_emblem, get_legendary, get_duo
from utils import is_superboon_or_superbane, convert_game_title, image_asset_url
import queries
from local_db import LocalDB
# prevent "runtime error" errors
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

async def main():
    client = Bot(sitename="https://feheroes.fandom.com", api="https://feheroes.fandom.com/api.php", index="https://feheroes.fandom.com/wiki/Main_Page", username=os.environ["WIKI_BOT_USERNAME"], password=os.environ["WIKI_BOT_PASSWORD"])
    await client.login()
    scraping_output = {}

    try:
        with open("marker.json", "r") as markerFile:
            marker_data = json.load(markerFile)
            last_successful_run = marker_data.get("lastSuccessfulRun", '1990-01-01')
    except:
        last_successful_run = '1990-01-01'

    current_run = await queries.get_next_hero_date(client, last_successful_run)
    version = await queries.get_unit_release_update(client, current_run)
    unit_data = await queries.get_new_units(client, current_run)
    new_units_for_queries = []

    for entry in unit_data:
        heroFullName = entry['title']['Page']
        unitProperties = {}
        dataInside = entry["title"]
        formattedWikipage = dataInside["WikiName"].replace(" ", "_")

        unitProperties["name"] = dataInside["Name"]
        unitProperties["title"] = dataInside["Title"]
        unitProperties["description"] = dataInside["Description"]
        unitProperties["move"] = dataInside["MoveType"]
        unitProperties["artist"] = dataInside["Artist"]
        unitProperties["color"], unitProperties["weapon_type"] = dataInside["WeaponType"].split(" ")
        unitProperties["id"] = dataInside["ID"]
        en_voices = dataInside["ActorEN"].split(' • ')
        jp_voices = dataInside["ActorJP"].split(' • ')
        unitProperties["voice_en"] = en_voices[0]
        if len(en_voices) > 1:
            unitProperties["backpack_voice"] = en_voices[1]
        else: unitProperties["backpack_voice"] = None
        unitProperties["voice_jp"] = jp_voices[0]
        if len(jp_voices) > 1:
            unitProperties["backpack_voice_jp"] = jp_voices[1]
        else: unitProperties["backpack_voice_jp"] = None
        unitProperties["internal_id"] = dataInside["TagID"]
        unitProperties["resplendent"] = None
        unitProperties["resplendent_voice"] = None
        unitProperties["resplendent_voice_jp"] = None
        unitProperties["images"] = {
            "portrait": image_asset_url(f"{formattedWikipage}_Face.webp"),
            "attack": image_asset_url(f"{formattedWikipage}_BtlFace.webp"),
            "special": image_asset_url(f"{formattedWikipage}_BtlFace_C.webp"),
            "damage": image_asset_url(f"{formattedWikipage}_BtlFace_D.webp"),
        }
        unitProperties["resplendent_images"] = None
        unitProperties["release"] = current_run
        unitProperties["version"] = version
        unitProperties["origin"] = " + ".join(convert_game_title(title) for title in dataInside["Origin"].split(","))
        if len(dataInside["Gender"]) != 1:
            # database data is either Female, Male or N, but we only store the first letter
            unitProperties["gender"] = dataInside["Gender"][0]
        else:
            unitProperties["gender"] = ""
        unitProperties["rarity"] = await queries.get_unit_rarity(client, heroFullName)

        dbProperties = dataInside["Properties"]
        specialUnitProperties = {
            "emblem": None,
            "harmonized": None,
            "duo": None,
            "duel": None,
            "aided": None,
            "type": ""
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
        elif "entwined" in dbProperties:
            specialUnitProperties["type"] = "entwined"

        unitProperties = {**unitProperties, **specialUnitProperties }

        scraping_output[heroFullName] = {}
        new_units_for_queries.append("\"" + heroFullName + "\"")

        sleep(1)
        skills = await queries.get_unit_skills(client, heroFullName)
        scraping_output[dataInside["Page"]] = {**scraping_output[dataInside["Page"]], **skills, **unitProperties}

    if new_units_for_queries:
        unitStatsPayload = {
            "tables": "UnitStats",
            "fields": "_pageName=Page, Lv1HP5, HPGR3, Lv1Atk5, AtkGR3, Lv1Spd5, SpdGR3, Lv1Def5, DefGR3, Lv1Res5, ResGR3",
            "where": f"_pageName in ({', '.join(new_units_for_queries)})"
        }
        unitStatsQuery = await client.call_get_api("cargoquery", **unitStatsPayload)

        for element in unitStatsQuery["cargoquery"]:
            innerData = element["title"]
            page = innerData["Page"]
            scraping_output[page]["base"] = {
                    "hp": int(innerData["Lv1HP5"]),
                    "atk": int(innerData["Lv1Atk5"]),
                    "spd": int(innerData["Lv1Spd5"]),
                    "def": int(innerData["Lv1Def5"]),
                    "res": int(innerData["Lv1Res5"])
            }
            scraping_output[page]["growth"] = {
                    "hp": int(innerData["HPGR3"]),
                    "atk": int(innerData["AtkGR3"]),
                    "spd": int(innerData["SpdGR3"]),
                    "def": int(innerData["DefGR3"]),
                    "res": int(innerData["ResGR3"])
            }
            supertraits = is_superboon_or_superbane(scraping_output[page]["growth"])
            scraping_output[innerData["Page"]] = {**scraping_output[innerData["Page"]], **supertraits}
    else:
        print(f"WARN: No units found for date {current_run}")

    # time to write to the local DB!
    db = LocalDB(wiki_client=client)

    for unit_name, unit_dict in scraping_output.items():
        await db.add_unit(unit_dict)


    with open("marker.json", "w") as markerFile:
        json.dump({ "lastSuccessfulRun": current_run }, markerFile)

    pprint(scraping_output)
    return scraping_output

if __name__ == "__main__":
    asyncio.run(main())
