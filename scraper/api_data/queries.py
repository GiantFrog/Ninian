from aiohttp import payload
from datetime import datetime
import re

async def get_unit_skills(client, unit):
    unitSkillsPayload = {
        "tables": "UnitSkills, Skills",
        "fields": "UnitSkills._pageName=UnitPage, Skills.Name=SkillName, skillPos, unlockRarity, Scategory, Description",
        "where": f"UnitSkills._pageName = '{unit.replace("'", "''")}'",
        "join_on": "Skills.WikiName = UnitSkills.skill",
        "order_by": "Scategory DESC, defaultRarity ASC",
    }
    unitSkillsQuery = await client.call_get_api("cargoquery", **unitSkillsPayload)

    output = {
        "weapon": {},
        "assist": {},
        "special": {},
        "passive_a": {},
        "passive_b": {},
        "passive_c": {},
        "passive_x": {}
    }

    for result in unitSkillsQuery["cargoquery"]:
        content = result["title"]

        match content["Scategory"]:
            case "passivea":
                output["passive_a"][content["SkillName"]] = content["unlockRarity"]
            case "passiveb":
                output["passive_b"][content["SkillName"]] = content["unlockRarity"]
            case "passivec":
                output["passive_c"][content["SkillName"]] = content["unlockRarity"]
            case "passivex":
                output["passive_x"][content["SkillName"]] = content["unlockRarity"]
            case "weapon":
                output["weapon"][content["SkillName"]] = content["unlockRarity"]
            case "assist":
                output["assist"][content["SkillName"]] = content["unlockRarity"]
            case "special":
                output["special"][content["SkillName"]] = content["unlockRarity"]
    
    return output

async def get_unit_rarity(client, unit):
    payload = {
        "tables": "SummoningAvailability",
        "fields": "Rarity, Property",
        "where": f"_pageName like '{unit}' and EndTime > '{datetime.now()}'",
        "order_by": "Rarity ASC",
        "limit": "1"
    }
    query = await client.call_get_api("cargoquery", **payload)
    if re.match('.*specialrate', query["cargoquery"][0]["title"]["Property"], re.IGNORECASE):
        return int(query["cargoquery"][0]["title"]["Rarity"]) - 1
    else:
        return int(query["cargoquery"][0]["title"]["Rarity"])
  
async def get_unit_release_update(client, date):
    versionPayload = {
        "tables": "VersionUpdates",
        "fields": "Major, Minor",
        "where": f"Date(ReleaseTime) >= '{date}'",
        "limit": "1",
        "order_by": "ReleaseTime ASC",
    }
    versionQuery = await client.call_get_api("cargoquery", **versionPayload)
    return f'{versionQuery["cargoquery"][0]["title"]["Major"]}.{versionQuery["cargoquery"][0]["title"]["Minor"]}'

async def get_unit_stats(client, units):
    pass

# returns the date when units were added nearest to, but after, the given date. if that makes any sense.
#TODO this leaps ahead years at a time
async def get_next_hero_date(client, date):
    datePayload = {
        "tables": "Units",
        "fields": "ReleaseDate",
        "where": f"ReleaseDate > '{date}' and WikiName not like \"%ENEMY\"",
        "order_by": "WikiName ASC",
        "limit": 1
    }
    dateQuery = await client.call_get_api("cargoquery", **datePayload)
    return dateQuery["cargoquery"][0]["title"]["ReleaseDate"]

# returns all units released on the given day
async def get_new_units(client, date):
    unitIdentityPayload = {
        "tables": "Units",
        "fields": "_pageName=Page, Name, WikiName, Title, WeaponType, Description, Gender, MoveType, Origin, Gender, Artist, ActorEN, ActorJP, TagID, Properties, _ID=ID",
        "where": f"ReleaseDate = '{date}' and WikiName not like \"%ENEMY\"",
        "order_by": "WikiName DESC",
        "limit": 2  # 95 heroes existed on launch
    }
    unitIdentityQuery = await client.call_get_api("cargoquery", **unitIdentityPayload)
    return unitIdentityQuery["cargoquery"]

async def get_romanized_artist_name(client, name):
    payload = {
        "tables": "Artists",
        "fields": "NameUSEN",
        "where": f'Name like "{name}"',
        "limit": 1
    }
    query = await client.call_get_api("cargoquery", **payload)
    try:
        result = query["cargoquery"][0]['title']['NameUSEN']
    except:
        print(f"WARN: error looking up artist {name}")
        result = None
    if result:
        return result
    else:
        return None

async def get_romanized_va_name(client, name):
    payload = {
        "tables": "VoiceActors",
        "fields": "Name",
        "where": f'NameJPJA like "{name}"',
        "limit": 1
    }
    query = await client.call_get_api("cargoquery", **payload)
    try:
        result = query["cargoquery"][0]['title']['Name']
    except:
        print(f"WARN: error looking up VA {name}")
        result = None
    if result:
        return result
    else:
        return None
