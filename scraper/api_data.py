from mwbot import Bot
from dotenv import load_dotenv
import asyncio
import os
import json
import sys
from datetime import datetime
# prevent "runtime error" errors
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

def is_superboon_or_superbane(growthRate):
    match growthRate:
        case 30 | 50 | 75 | 95:
            return "superbane"
        case 25 | 45 | 70 | 90:
            return "superboon"
        case _:
            return ""
    
async def get_legendary(client, page):
    legendaryPayload = {
        "tables": "LegendaryHero",
        "fields": "LegendaryEffect, AllyBoostHP, AllyBoostAtk, AllyBoostSpd, AllyBoostDef, AllyBoostRes",
        "where": "_pageName = \"" + page + "\"",
    }
    legendaryQuery = await client.call_get_api("cargoquery", **legendaryPayload)
    legendaryData = legendaryQuery["cargoquery"][0]["title"]
    stats = {}
    if int(legendaryData["AllyBoostHP"] != 0):
        stats["hp"] = int(legendaryData["AllyBoostHP"])
    if int(legendaryData["AllyBoostAtk"] != 0):
        stats["atk"] = int(legendaryData["AllyBoostAtk"])
    if int(legendaryData["AllyBoostSpd"] != 0):
        stats["spd"] = int(legendaryData["AllyBoostSpd"])
    if int(legendaryData["AllyBoostDef"] != 0):
        stats["def"] = int(legendaryData["AllyBoostDef"])
    if int(legendaryData["AllyBoostRes"] != 0):
        stats["res"] = int(legendaryData["AllyBoostRes"])

    returnedData = {
        "type": "legendary",
        "blessing": legendaryData["LegendaryEffect"],
        "stats": stats,
    }
    return returnedData

async def get_emblem(client, page):
    emblemPayload = {
        "tables": "EmblemHero",
        "fields": "Effect",
        "where": "_pageName = \"" + page + "\"",
    }
    emblemQuery = await client.call_get_api("cargoquery", **emblemPayload)
    return emblemQuery["cargoquery"][0]["title"]["Effect"]

async def get_harmonized(client, page):
    harmonizedPayload = {
        "tables": "HarmonizedHero",
        "fields": "HarmonizedSkill",
        "where": "_pageName = \"" + page + "\"",
    }
    harmonizedQuery = await client.call_get_api("cargoquery", **harmonizedPayload)
    return harmonizedQuery["cargoquery"][0]["title"]["HarmonizedSkill"]

# convert game titles as received from the db
def convertGameTitle(title):
    match title:
        case "Fire Emblem Echoes: Shadows of Valentia":
            return "Echoes"
        case "Fire Emblem Warriors: Three Hopes":
            return "Three Houses"
        case _:
            return title.replace("Fire Emblem", "").replace(":", "").strip()

async def main():
    client = Bot(sitename="https://feheroes.fandom.com", api="https://feheroes.fandom.com/api.php", index="https://feheroes.fandom.com/wiki/Main_Page", username=os.environ["FEH_BOT_USERNAME"], password=os.environ["FEH_BOT_PASSWORD"])
    await client.login()
    jsonDict = {}


    today = datetime.today().strftime('%Y-%m-%d')

    unitIdentityPayload = {
         "tables": "Units",
        "fields": "_pageName=Page, Name, WikiName, Title, WeaponType, Description, Gender, MoveType, Origin, Gender, Artist, ActorEN, ActorJP, ReleaseDate, Properties, _ID=ID",
        "where": "ReleaseDate > " + today + " and Properties holds \"emblem\"",
        "order_by": "ReleaseDate DESC",
    }

    unitIdentityQuery = await client.call_get_api("cargoquery", **unitIdentityPayload)
    newUnitsForQueries = []
    for entry in unitIdentityQuery["cargoquery"]:
        unitProperties = {}
        dataInside = entry["title"]
        unitProperties["name"] = dataInside["Name"]
        unitProperties["title"] = dataInside["Title"]
        unitProperties["description"] = dataInside["Description"]
        unitProperties["origin"] = dataInside["Origin"]
        unitProperties["move"] = dataInside["MoveType"]
        unitProperties["artist"] = dataInside["Artist"]
        color, weapon = dataInside["WeaponType"].split(" ")
        unitProperties["color"] = color
        unitProperties["id"] = dataInside["ID"]
        unitProperties["weapon"] = weapon
        unitProperties["origin"] = " + ".join(convertGameTitle(title) for title in dataInside["Origin"].split(","))
        if len(dataInside["Gender"]) == 1:
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
        }
        if "emblem" in dbProperties:
            specialUnitProperties["emblem"] = await get_emblem(client, dataInside["Page"])
        elif "harmonized" in dbProperties:
            specialUnitProperties["harmonized"] = await get_harmonized(client, dataInside["Page"])
        elif "legendary" in dbProperties:
            specialUnitProperties = await get_legendary(client, page)
            

        unitProperties = {**unitProperties, **specialUnitProperties }

    for element in unitIdentityQuery["cargoquery"]:
        heroFullName = element['title']['Page']
        jsonDict[heroFullName] = {}
        newUnitsForQueries.append("\"" + heroFullName + "\"")

    unitStatsAndSkillsPayload = {
        "tables": "UnitStats",
        "fields": "_pageName=Page, Lv1HP5, HPGR3, Lv1Atk5, AtkGR3, Lv1Spd5, SpdGR3, Lv1Def5, DefGR3, Lv1Res5, ResGR3",
        "where": f"_pageName in ({', '.join(newUnitsForQueries)})"
    }
    
    unitStatsQuery = await client.call_get_api("cargoquery", **unitStatsAndSkillsPayload)    
    for element in unitStatsQuery["cargoquery"]:
        innerData = element["title"]
        page = innerData["Page"]
        jsonDict[page] = {
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

    jsonDict[dataInside["Page"]] = {**jsonDict[dataInside["Page"]], **unitProperties}        

    with open("test.json", "w") as f:
        json.dump(jsonDict, f)
    with open("marker.json", "w") as markerFile:
        json.dump({ "lastSuccessfulRun": today }, markerFile)
if __name__ == "__main__":
    asyncio.run(main())
