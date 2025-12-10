from os import listdir
import requests
from bs4 import BeautifulSoup
import json
import utility
from scraper import integrate
from skill_scrape import passive_icon_number

refines = [
    "hapi",
    "orochi",
    "malice",
    "riev",
    "myrrh3",
]

path = "../database/feh/images/passive/"

with open('../database/feh/char.json', 'r') as f:
    char = json.load(f)

with open('../database/feh/skill.json', 'r') as f:
    skills = json.load(f)


def ref(key):
    # TODO would be real cool to use a pool search to look up char keys, but then it loads oifey.__init__ and that's no good
    unit = char[key]
    page_name = unit['name'] + ': ' + unit['title']
    # Follow the same steps for feheroes.fandom
    fandom = requests.get(f'https://feheroes.fandom.com/wiki/{page_name}')
    soup = BeautifulSoup(fandom.text, 'html.parser')

    # The information we want on the page is stored under '<div role="document" class="page">
    document = soup.find(class_="mw-parser-output")

    skill_tables = document.find_all(class_="wikitable default unsortable skills-table")
    weapons = {}
    link = ""
    wep_table = skill_tables[0].find_all('tr')
    for i in range(1, len(wep_table)):
        cols = wep_table[i].find_all('td')
        link = cols[0].find_all('a')[0]['href']
        wep = list(cols[0].stripped_strings)[0]
        unlock = list(cols[6].stripped_strings)[0]
        weapons[wep] = unlock

    last = list(weapons.keys()).pop()
    wep_key = utility.compress(last)

    global skills
    if wep_key not in skills:
        integrate.weapon_get(key, new_weapon=last)
        with open('../database/feh/skill.json', 'r') as f:
            skills = json.load(f)
    weapon = skills[wep_key]

    fandom = requests.get(f'https://feheroes.fandom.com/{link}')
    soup = BeautifulSoup(fandom.text, 'html.parser')

    wep_document = soup.find(class_="mw-parser-output")
    refine_info = wep_document.find(class_="cargoTable").find_all('tr')

    cols = refine_info[1].find_all('td')
    url = cols[0].find_all('a')[0]['href']
    eff = cols[2].find_all('span')[0]
    eff = '\n'.join(list(eff.stripped_strings))
    
    desc = '\n'.join(list(cols[2].stripped_strings))
    desc = desc[0:desc.index(eff)]
    desc = desc[0: len(desc)-2]
    og_desc = weapon['skill'][0]['description']

    refine = {
        "special": [],
        "description": False if desc == og_desc else desc
    }

    refine['special'].append(eff)
    weapon['refine'] = refine

    try:
        count = passive_icon_number()
        data = requests.get(url).content
        f = open(path + str(count) + '.png', 'wb')
        f.write(data)
        f.close()
        weapon['icon'] = count
    except Exception as e:
        print("Something went wrong and no new skill icon was written. Error: ", e)


    unit['prf'][''] = wep_key + 'eff'
    unit['prf']['eff'] = wep_key + 'eff'
    unit['prf']['atk'] = wep_key + 'atk'
    unit['prf']['spd'] = wep_key + 'spd'
    unit['prf']['def'] = wep_key + 'def'
    unit['prf']['res'] = wep_key + 'res'

    char[key] = unit
    skills[wep_key] = weapon

    print(char[key]['prf'])
    print(skills[wep_key]['refine'])

    with open('../database/feh/char.json', 'w') as fp:
        json.dump(char, fp, indent=2)
    with open('../database/feh/skill.json', 'w') as fp:
        json.dump(skills, fp, indent=2)

for hero in refines:
    ref(hero)
