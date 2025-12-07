from mwbot import Bot
from dotenv import load_dotenv
import asyncio
import os
import json
import sys
# prevent "runtime error" errors
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

load_dotenv()

async def get_emblem(client, page):
    emblemPayload = {
        "tables": "EmblemHero",
        "fields": "Effect",
        "where": "_pageName = \"" + page + "\"",
    }
    emblemQuery = await client.call_get_api("cargoquery", **emblemPayload)
    return emblemQuery["cargoquery"][0]["title"]["Effect"]

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

    unitIdentityPayload = {
         "tables": "Units",
        "fields": "_pageName=Page, Name, WikiName, Title, WeaponType, Description, Gender, MoveType, Origin, Gender, Artist, ActorEN, ActorJP, ReleaseDate, Properties, _ID=ID",
        "where": "ReleaseDate > 2025-10-10 and Properties holds \"emblem\"",
        "order_by": "ReleaseDate DESC",
        "limit": "5",
    }

    dict = {}
    unitIdentityQuery = await client.call_get_api("cargoquery", **unitIdentityPayload)
    newUnits = [
        element["title"]["Page"]
        for element in unitIdentityQuery["cargoquery"]
    ]

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
        extraProperties = {}
        if "emblem" in dbProperties:
            extraProperties["emblem"] = await get_emblem(client, dataInside["Page"])

        unitProperties = {**unitProperties, **extraProperties }
        dict[dataInside["Page"]] = unitProperties
        

    with open("test.json", "w") as f:
        json.dump(dict, f)

if __name__ == "__main__":
    asyncio.run(main())
