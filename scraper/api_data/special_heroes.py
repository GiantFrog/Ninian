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