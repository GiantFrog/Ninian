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

async def get_skills(client, units):
    unitSkillsPayload = {
        "tables": "UnitSkills, Skills",
        "fields": "UnitSkills._pageName=UnitPage, Skills.Name=SkillName, skillPos, unlockRarity, Scategory, Description",
        "where": f"UnitSkills._pageName in ({', '.join(units)})",
        "join_on": "Skills.WikiName = UnitSkills.skill",
        "order_by": "Scategory DESC, defaultRarity ASC",
    }
    unitSkillsQuery = await client.call_get_api("cargoquery", **unitSkillsPayload)

    output = {}

    for result in unitSkillsQuery["cargoquery"]:
        content = result["title"]
        unit = content["UnitPage"]
        if unit not in output:
            output[unit] = {
                "weapons": {},
                "assist": {},
                "special": {},
                "passive": {
                    "A": {},
                    "B": {},
                    "C": {},
                    "X": {},
                }
            }
        match content["Scategory"]:
            case "passivea":
                output[unit]["passive"]["A"][content["SkillName"]] = content["unlockRarity"]
                break
            case "passiveb":
                output[unit]["passive"]["B"][content["SkillName"]] = content["unlockRarity"]
                break
            case "passivec":
                output[unit]["passive"]["C"][content["SkillName"]] = content["unlockRarity"]
                break
            case "passivex":
                output[unit]["passive"]["X"][content["SkillName"]] = content["unlockRarity"]
            case "weapon":
                output[unit]["weapons"][content["SkillName"]] = content["unlockRarity"]
                break
            case "assist":
                output[unit]["assist"][content["SkillName"]] = content["unlockRarity"]
                break
            case "special":
                output[unit]["special"][content["SkillName"]] = content["unlockRarity"]
    
    return output
    




async def get_duo(client, page):
    duoPayload = {
        "tables": "DuoHero",
        "fields": "DuoSkill, Duel",
        "where": "_pageName = \"" + page + "\"",
    }
    duoQuery = await client.call_get_api("cargoquery", **duoPayload)
    return duoQuery["cargoquery"][0]["title"]["DuoSkill"]

async def get_legendary(client, page):
    legendaryPayload = {
        "tables": "LegendaryHero",
        "fields": "LegendaryEffect, AllyBoostHP, AllyBoostAtk, AllyBoostSpd, AllyBoostDef, AllyBoostRes, Duel",
        "where": "_pageName = \"" + page + "\"",
    }
    legendaryQuery = await client.call_get_api("cargoquery", **legendaryPayload)
    legendaryData = legendaryQuery["cargoquery"][0]["title"]
    stats = {}
    boost_map = {
        "AllyBoostHP": "hp",
        "AllyBoostAtk": "atk",
        "AllyBoostSpd": "spd",
        "AllyBoostDef": "def",
        "AllyBoostRes": "res",
    }

    for src, dst in boost_map.items():
        value = int(legendaryData.get(src, 0))
        if value != 0:
            stats[dst] = value
    returnedData = {
        "type": "legendary",
        "blessing": legendaryData["LegendaryEffect"],
        "stats": stats,
        "duel": legendaryData["Duel"],
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
        "fields": "_pageName=Page, Name, WikiName, Title, WeaponType, Description, Gender, MoveType, Origin, Gender, Artist, ActorEN, ActorJP, ReleaseDate, TagID, Properties, _ID=ID",
        "where": "ReleaseDate > " + today + " and WikiName not like \"%ENEMY\"",
        "order_by": "ReleaseDate DESC",
    }

    unitIdentityQuery = await client.call_get_api("cargoquery", **unitIdentityPayload)
    newUnitsForQueries = []
    for entry in unitIdentityQuery["cargoquery"]:
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
        unitProperties["origin"] = " + ".join(convertGameTitle(title) for title in dataInside["Origin"].split(","))
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
        }
        if "emblem" in dbProperties:
            specialUnitProperties["emblem"] = await get_emblem(client, dataInside["Page"])
        elif "harmonized" in dbProperties:
            specialUnitProperties["harmonized"] = await get_harmonized(client, dataInside["Page"])
        elif "legendary" in dbProperties:
            legendaryProperties = await get_legendary(client, page)
            specialUnitProperties = {**specialUnitProperties, **legendaryProperties}
        elif "duo" in dbProperties:
            specialUnitProperties["duo"] = await get_duo(client, page)
        
            

        unitProperties = {**unitProperties, **specialUnitProperties }

    for element in unitIdentityQuery["cargoquery"]:
        heroFullName = element['title']['Page']
        jsonDict[heroFullName] = {}
        newUnitsForQueries.append("\"" + heroFullName + "\"")

    unitStatsPayload = {
        "tables": "UnitStats",
        "fields": "_pageName=Page, Lv1HP5, HPGR3, Lv1Atk5, AtkGR3, Lv1Spd5, SpdGR3, Lv1Def5, DefGR3, Lv1Res5, ResGR3",
        "where": f"_pageName in ({', '.join(newUnitsForQueries)})"
    }
    
    unitStatsQuery = await client.call_get_api("cargoquery", **unitStatsPayload)

    for newUnit in newUnitsForQueries:
        versionPayload = {
            "tables": "VersionUpdates",
            "fields": "CONCAT(Major, '&period;', Minor) = Version",
            "where": "Date(ReleaseTime) <= '" + json[newUnit]["release"] + "'",
            "limit": "1",
            "order_by": "ReleaseTime DESC",
        }
        versionQuery = await client.call_get_api("cargoquery", **versionPayload)
        version = versionQuery["cargoquery"][0]["title"]["Version"]
        del json[newUnit]["release"]
        json[newUnit]["version"] = version

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
    
    skills = await get_skills(client, newUnitsForQueries)

    jsonDict[dataInside["Page"]] = {**jsonDict[dataInside["Page"]], **skills, **unitProperties}        

    with open("test.json", "w") as f:
        json.dump(jsonDict, f)
    with open("marker.json", "w") as markerFile:
        json.dump({ "lastSuccessfulRun": today }, markerFile)
if __name__ == "__main__":
    asyncio.run(main())
