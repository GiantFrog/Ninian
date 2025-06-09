import json
import weapon
import re
import skill_scrape
import utility
import portrait

with open('../database/feh/artist.json', 'r', encoding="utf-8") as f:
    artists = json.load(f)
with open('../database/feh/va.json', 'r', encoding="utf-8") as f:
    va = json.load(f)

with open('../database/feh/skill.json', 'r', encoding="utf-8") as f:
    skill = json.load(f)

with open('../database/feh/char.json', 'r', encoding="utf-8") as f:
        char = json.load(f)


# Add the artist and VA credits to artist.json and va.json
def credits(key, resp=False):
    with open('../database/feh/char.json', 'r', encoding="utf-8") as f:
        char = json.load(f)
    unit = char[key]
    alt = unit['ALT_NAME']
    hard_alt = unit['HARD_ALT_NAME']
    name = unit['name']
    display = unit['DISPLAY_NAME']

    # if we're adding resplendent credits
    if resp:
        alt = []
        alt.append(f'Resplendent {name}')
        alt.append(f'Resp {name}')
        alt.append(f'R {name}')
        alt.append(f'{name} (Resplendent)')
        display = unit['DISPLAY_NAME'] + " (Resplendent)"
        hard_alt = alt
        key = key + 'R'

    # look for artist and va
    done = False

    artkeys = artists.keys()

    # get the name of the artist from char.json entry
    a = unit['artist']
    if resp:
        a = unit['resplendent']
        print(a)

    print(a)

    # if artist is already in the database
    for i in artkeys:
        if artists[i]['name'] in a:
            done = True
            artists[i]['heroes'][key] = display
            artists[i]['heroes'] =  utility.sortDict(artists[i]['heroes'])
            for j in alt:
                artists[i]['ALT_NAME'].append(j)
            for j in hard_alt:
                artists[i]['HARD_ALT_NAME'].append(j)
            artists[i]['HARD_ALT_NAME'] = (artists[i]['HARD_ALT_NAME'])
            artists[i]['ALT_NAME'] = (artists[i]['ALT_NAME'])

    # artist not in the database, add a new entry
    if not done:
        artistcompressed = a
        if '(' in a:
            index = a.index(' (')
            artistcompressed = a[0:index]

        
        artistcompressed = utility.compress(artistcompressed)
        obj = {}
        obj['heroes'] = {}
        obj['heroes'][key] = display
        obj['name'] = a
        obj['ALT_NAME'] = alt
        obj['HARD_ALT_NAME'] = hard_alt
        artists[artistcompressed] = obj

    done = False

    # repeat for VA

    v = unit['voice']
    if resp:
        v = unit['resplendent_voice']

    vakeys = va.keys()
    for i in vakeys:
        if va[i]['name'] in v:
            done = True
            va[i]['heroes'][key] = display
            va[i]['heroes'] =  utility.sortDict(va[i]['heroes'])
            for j in alt:
                va[i]['ALT_NAME'].append(j)
            for j in hard_alt:
                va[i]['HARD_ALT_NAME'].append(j)
            va[i]['HARD_ALT_NAME'] = (va[i]['HARD_ALT_NAME'])
            va[i]['ALT_NAME'] = (va[i]['ALT_NAME'])


    
    if not done:
        vacompressed = unit['voice']
        if '(' in unit['voice']:
            index = unit['voice'].index(' (')
            vacompressed = unit['voice'][0:index]

        vacompressed = utility.compress(vacompressed)
        obj = {}
        obj['heroes'] = {}
        obj['heroes'][key] = display
        obj['name'] = unit['voice']
        obj['ALT_NAME'] = alt
        obj['HARD_ALT_NAME'] = hard_alt
        va[vacompressed] = obj

    # write out new files

    with open('../database/feh/artist.json', 'w', encoding="utf-8") as fp:
        json.dump(artists, fp, indent=2)
    with open('../database/feh/va.json', 'w', encoding="utf-8") as fp:
        json.dump(va, fp, indent=2)

    return


def weapon_get(key, new_weapon=None, new_rarity=5):
    # get the units list of weapons
    unit = char[key]
    weapons = unit["weapons"].keys()

    if new_weapon:
        rarity = new_rarity
        wep = new_weapon
        global skill
        with open('../database/feh/skill.json', 'r', encoding="utf-8") as f:
            skill = json.load(f)
    else:
        rarity = 0
        wep = ""

        # get their highest rarity weapon
        for i in weapons:
            temp_rarity = int(unit["weapons"][i])
            if temp_rarity >= rarity:
                rarity = temp_rarity
                wep = i

    # regex to determine the key used in skill.json

    wep_key = utility.compress(wep)

    all_keys = skill.keys()

    # choose the highest rarity between character's available rarity and the weapon's unlock rarity (its going to b4 5
    # star like 99% of the time)
    true_rarity = max(rarity, unit['rarity'])

    # if they're using an existing weapon
    if wep_key in all_keys:
        entry = skill[wep_key]
        entry['reference'][wep][key] = str(true_rarity)

    # new weapon, go scrape the wiki page
    else:
        if wep == 'Thief':
            entry = weapon.scrape_page('Thief_(weapon)')
        else:
            entry = weapon.scrape_page(wep)
        ref = {
            wep: {
                key: str(true_rarity)
            }
        }
        entry['reference'] = ref
        entry['skill'][0]['weapon_type'] = f"{unit['color']}_{unit['weapon']}"

    for i in unit['HARD_ALT_NAME']:
        entry['HARD_ALT_NAME'].append(i)

    entry['HARD_ALT_NAME'] = list(set(entry['HARD_ALT_NAME']))

    # strip the hero's name from the aliases of previous weapons
    for old_weapon in weapons:
        old_key = utility.compress(old_weapon)
        if old_key != wep_key:
            old_alts = skill[old_key]['HARD_ALT_NAME']
            unit_alts = unit["ALT_NAME"] + unit["HARD_ALT_NAME"]
            unit_alts.append(key)
            skill[old_key]['HARD_ALT_NAME'] = [alias for alias in old_alts if alias not in unit_alts]

    skill[wep_key] = entry
    with open('../database/feh/skill.json', 'w', encoding="utf-8") as fp:
        json.dump(skill, fp, indent=2)

def integrate_skills(key):
    unit = char[key]
    
    if any(unit['assist']):
        integrate_as_sp('assist', key)
    if any(unit['special']):
        integrate_as_sp('special', key)
   
    passives =  unit['passive']
    if any(passives['A']):
        integrate_passive('A', key)
    if any(passives['B']):
        integrate_passive('B', key)
    if any(passives['C']):
        integrate_passive('C', key)
    if any(passives['X']):
        integrate_passive('X', key)

def integrate_as_sp(slot, key):
    unit = char[key]
    skillobj = unit[slot]
    intobj = {}
    keys = skillobj.keys()
    for i in keys:
        compressed = utility.compress(i)
        compressed = re.sub(r'[^a-zA-Z]', '', compressed)
        #(re.sub(r'[^a-zA-Z]', '', i)).lower()
        intobj[compressed] = {}
        intobj[compressed]['name'] = i
        intobj[compressed]['rarity'] = skillobj[i]
    skillkeys = skill.keys()
    intkeys = intobj.keys()
    for i in intkeys:
        print(i)
        if i in skillkeys:
            refkeys = skill[i]['reference'].keys()
            if intobj[i]['name'] in refkeys:
                ref = skill[i]['reference']
                ref[intobj[i]['name']][key] =  intobj[i]['rarity']
                skill[i]['reference'] = ref
            else:
                print('new skill: ' + intobj[i]['name'])
        else: 
            print(intobj[i]['name'])
            newskill = skill_scrape.scrape_assist_special(intobj[i]['name'].replace('/', ' '))
            ref = newskill['reference']
            ref[intobj[i]['name']][key] =  intobj[i]['rarity']
            newskill['reference'] = ref
            skill[i] = newskill

def integrate_passive(slot, key):
    unit = char[key]
    skillobj = unit['passive'][slot]
    intobj = {}
    keys = skillobj.keys()
    for i in keys:
        compressed = utility.compress(i)
        compressed = re.sub(r'[^a-zA-Z]', '', compressed)
        intobj[compressed] = {}
        intobj[compressed]['name'] = i
        intobj[compressed]['rarity'] = skillobj[i]

    skillkeys = skill.keys()
    intkeys = intobj.keys()
    for i in intkeys:
        print(i)
        if i in skillkeys:
            refkeys = skill[i]['reference'].keys()
            if intobj[i]['name'] in refkeys:
                ref = skill[i]['reference']
                ref[intobj[i]['name']][key] =  intobj[i]['rarity']
                skill[i]['reference'] = ref
            else:
                print('new skill: ' + intobj[i]['name'])
        else: 
            s = intobj[i]['name']
            if s[-1].isdigit():
                s = s[:-2]
            
            newskill = skill_scrape.scrape_passive_skill(s.replace('/', ' '))
            ref = newskill['reference']
            ref[intobj[i]['name']][key] =  intobj[i]['rarity']
            newskill['reference'] = ref
            skill[i] = newskill

    with open('../database/feh/skill.json', 'w', encoding="utf-8") as fp:
        json.dump(skill, fp, indent=2)


    return


def main(units):
    keys = units.keys()

    for i in keys:
        char[i] = units[i]
        for j in units[i]['reference']:
            char[j]['reference'].append(i)


    with open('../database/feh/char.json', 'w', encoding="utf-8") as fp:
        json.dump(char, fp, indent=2)
  

    for i in keys:
        credits(i, False)
        weapon_get(i)
        integrate_skills(i)
        portrait.portrait(i, char[i])
    return

# Please put code to manually run in here, so it doesn't run when we import this package elsewhere!
if __name__ == "__main__":
    with open('update.json', 'r', encoding="utf-8") as f:
        units = json.load(f)

    main(units)

    #credits('robin14', False)
