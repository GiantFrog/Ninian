async def get_unit_skills(client, units):
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
  
async def get_unit_release_update(client, unit):
    versionPayload = {
        "tables": "VersionUpdates",
        "fields": "CONCAT(Major, '&period;', Minor) = Version",
        "where": "Date(ReleaseTime) >= '" + json[newUnit]["release"] + "'",
        "limit": "1",
        "order_by": "ReleaseTime DESC",
    }
    versionQuery = await client.call_get_api("cargoquery", **versionPayload)
    version = versionQuery["cargoquery"][0]["title"]["Version"]
    return version

async def get_unit_stats(client, units) {
    
}