import requests
from bs4 import BeautifulSoup
import json
import portrait
import re
import utility

refines = [
    "ash",
    "xander5",
    "asbel",
    "innes3",
    "tiki7",
]

path = "../database/feh/images/passive/"

with open('../database/feh/char.json', 'r') as f:
    char = json.load(f)

with open('../database/feh/skill.json', 'r') as f:
    skills = json.load(f)


def ref(key):

    unit = char[key]
    page_name = unit['name'] + ': ' + unit['title']
    # Follow the same steps for feheroes.fandom
    fandom = requests.get(f'https://feheroes.fandom.com/wiki/{page_name}')
    soup = BeautifulSoup(fandom.text, 'html.parser')

    # The information we want on the page is stored under '<div role="document" class="page">
    document = soup.find(class_="mw-parser-output")


    # get the name and title of the unit and append both to the unit_info
    wiki_info = document.find(class_="wikitable hero-infobox").find_all('tr')




    skill_tables = document.find_all(class_="wikitable default unsortable skills-table")
    weapons = {};
    link = ""
    wep_table = skill_tables[0].find_all('tr')
    for i in range(1, len(wep_table)):
        #print(cols)
        cols = wep_table[i].find_all('td')
        link = cols[0].find_all('a')[0]['href']
        wep = list(cols[0].stripped_strings)[0]
        unlock = list(cols[6].stripped_strings)[0]
        weapons[wep] = unlock

    last = list(weapons.keys()).pop();

    wep_key = utility.compress(last)


    
    weapon = skills[wep_key]   



    fandom = requests.get(f'https://feheroes.fandom.com/{link}')
    soup = BeautifulSoup(fandom.text, 'html.parser')

    wep_document = soup.find(class_="mw-parser-output")
    refine_info = wep_document.find(class_="wikitable default").find_all('tr')

    cols = refine_info[1].find_all('td')
    url = cols[0].find_all('a')[0]['href']
    eff = cols[2].find_all('span')[0]
    eff = '\n'.join(list(eff.stripped_strings))
    
    desc = '\n'.join(list(cols[2].stripped_strings))
    desc = desc[0:desc.index(eff)]
    desc = desc[0: len(desc)-2]
    og_desc = weapon['skill'][0]['description']

    refine = {
    "special" : []
    }

    if (desc == og_desc):
        refine['description'] = False
    else:
        refine['description'] = desc

    refine['special'].append(eff)
    weapon['refine'] = refine




    try:
        file_counter = open("counter.txt", "r+")
        count = file_counter.read()
        count = int(count)
    except Exception as e:
        print("Something went wrong with opening the file. Error: ", e)

    if count:
    
        data = requests.get(url).content
        f = open(path + str(count) + '.png', 'wb')
        f.write(data)
        f.close()
        weapon['icon'] = count
        count = count+1
        count = (str(count))
        file_counter.truncate(0)
        file_counter.seek(0)
        file_counter.write(count)
        file_counter.close()


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


   
    #print(blank)
    return

for i in range(0, len(refines)):
    ref(refines[i])
#print(scrape_page('/wiki/Lucina:_Future_Witness'))


