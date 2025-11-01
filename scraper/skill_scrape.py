from os import listdir
import requests
from bs4 import BeautifulSoup
import json
import maps
import utility
import re
import copy
import string

path = "../database/feh/images/passive/"


def passive_icon_number():
    count = 0
    for file in listdir(path):
        try:
            file_number = int(file[:-4])
            if file_number > count:
                count = file_number
        except (ValueError, TypeError):
            pass
    return count + 1

def scrape_passive_skill(page_name):
    if page_name.endswith('?'):
        page_name = f'{page_name[:-1]}%3F'
    if page_name == 'Pair Up':
        page_name = "Pair Up (Passive)"
    with open('templates/skill_temp.json', 'r') as f:
        template = json.load(f)
    blank = template
    # Follow the same steps for feheroes.fandom
    fandom = requests.get(f'https://feheroes.fandom.com/wiki/{page_name}')
    soup = BeautifulSoup(fandom.text, 'html.parser')

    # The information we want on the page is stored under '<div role="document" class="page">
    document = soup.find(class_="mw-parser-output")

    # Create a list that will hold all the info we want to export to the Excel file
    blank['name'] = page_name.replace('_', " ")

    # get the name and title of the unit and append both to the unit_info
    table = document.find(class_="wikitable default skills-table")
    if table is None:
        table = document.find(class_="wikitable default")
    wiki_info = table.find_all('tr')

    # print(len(wiki_info))
    slot = ""
    blank['reference'] = {}

    # print(list(wiki_info[0].stripped_strings))

    for i in range(1, len(wiki_info) - 1):
        info = list(wiki_info[i].stripped_strings)
        if i == 1:
            slot = info.pop(0)
            if slot == 'A' or slot == 'B' or slot == 'C' or slot == 'X':
                slot = 'Passive ' + slot
            if slot == 'S':
                slot = 'Sacred Seal'
        obj = {'name': info[0]}

        name = info.pop(0)
        blank['HARD_ALT_NAME'].append(name)
        blank['reference'][name] = {}
        obj['stats'] = {}
        obj['stats']['sp'] = info.pop(0)
        obj['slot'] = slot

        # Find the restrictions
        restriction = wiki_info[len(wiki_info) - 1]
        if "original unit" in restriction.text:
            obj['exclusive'] = True
        else:
            obj['exclusive'] = False

        obj["restriction_weapon"] = False
        obj["restriction_movement"] = False

        if "staff" in restriction.text:
            obj['restriction_weapon'] = ["**Can only** be used by: "]
            obj['restriction_weapon'].append("Staff")

        full_restrict_icons = restriction.find_all('a')
        restrict_icons = []
        for j in full_restrict_icons:
            restrict_icons.append(j['title'])
        if restrict_icons:
            # determine if over 50% of potential weapon and movements are restricted
            restrict_moves = 0
            restrict_weapons = 0
            moves = ["Infantry", "Cavalry", "Flying", "Armored"]
            weapons = ["Red Sword", "Red Dagger", "Red bow", "Red Tome", "Red Breath", "Red Beast", "Blue Lance",
                       "Blue Dagger", "Blue bow", "Blue Tome", "Blue Breath", "Blue Beast", "Green Axe", "Green Dagger",
                       "Green bow", "Green Tome", "Green Breath", "Green Beast", "Staff", "Colorless Dagger",
                       "Colorless bow", "Colorless Tome", "Colorless Breath", "Colorless Beast"]
            for j in restrict_icons:
                if any(x in j for x in moves):
                    restrict_moves = restrict_moves + 1
            for j in restrict_icons:
                if any(x in j for x in weapons):
                    restrict_weapons = restrict_weapons + 1

            if restrict_moves > (len(moves) / 2):
                obj["restriction_movement"] = []
                obj["restriction_movement"].append("**Can only** be used by: ")
                temp = []

                for j in moves:
                    if not any(x in j for x in restrict_icons):
                        temp.append(j)
                obj["restriction_movement"].append(temp)
            elif restrict_moves > 0:
                obj["restriction_movement"] = []
                obj["restriction_movement"].append("**Cannot** be used by: ")
                temp = []
                for j in moves:
                    if any(x in j for x in restrict_icons):
                        temp.append(j)
                obj["restriction_movement"].append(temp)

            if restrict_weapons > (len(weapons) / 2):
                temp = []
                obj["restriction_weapon"] = []
                obj["restriction_weapon"].append("**Can only** be used by: ")
                for j in weapons:
                    if not any(x in j for x in restrict_icons):
                        temp.append(maps.restrictions[j])
                obj["restriction_weapon"].append(temp)
            elif restrict_weapons > 0:
                temp = []
                obj["restriction_weapon"] = []
                obj["restriction_weapon"].append("**Cannot** be used by: ")
                for j in weapons:
                    if any(x in j for x in restrict_icons):
                        temp.append(maps.restrictions[j])
                obj["restriction_weapon"].append(temp)

        blank['skill'].append(obj)

        # Get the full description
        info.pop(0)  # all other text should be the description now
        info = utility.removeDuplicates(info)
        if ('<td style="text-align:left;" class="full-desc">' in str(i)):
            print('Long Desc')
        description = ""
        for j in info:
            description = description + j + "\n"

        obj['description'] = description[:-2]
        

    count = passive_icon_number()

    highest = info = wiki_info[len(wiki_info) - 2]
    url = highest.find_all('td')[0].find_all('a')[0]['href']

    data = requests.get(url).content
    f = open(path + str(count) + '.png', 'wb')
    f.write(data)
    f.close()
    blank['icon'] = count
    blank['slot'] = slot

    return blank


def scrape_assist_special(page_name):
    # This method is used for gathering info for Supports and Special type skills
    with open('templates/skill_temp.json', 'r') as f:
        template = json.load(f)
    blank = template
    # Follow the same steps for feheroes.fandom
    fandom = requests.get(f'https://feheroes.fandom.com/wiki/{page_name}')
    soup = BeautifulSoup(fandom.text, 'html.parser')

    # The information we want on the page is stored under '<div role="document" class="page">
    document = soup.find(class_="mw-parser-output")

    # Create a list that will hold all the info we want to export to the Excel file
    blank['name'] = page_name.replace('_', " ")
    blank['reference'] = {}
    # determine if the skill is an assist or a special
    slot = ""
    header_info = soup.find(class_="page-header__categories").find_all('a')
    if "Assists" in header_info[0]:
        slot = "Assist"
    elif "Specials" in header_info[0]:
        slot = "Special"
    blank['slot'] = slot

    # get the information on the skill from the main table
    wiki_info = document.find(class_="wikitable skills-table").find_all('tr')

    for i in range(1, len(wiki_info) - 1):
        info = list(wiki_info[i].stripped_strings)

        obj = {'name': info[0]}
        name = info.pop(0)
        blank['HARD_ALT_NAME'].append(name)
        blank['reference'][name] = {}
        obj['stats'] = {}
        if slot == "Special":
            obj['stats']['cooldown'] = info.pop(0)
        else:
            obj['stats']['rng'] = info.pop(0)
        obj['stats']['sp'] = info.pop(len(info)-2)
        obj['slot'] = slot

        # Find the restrictions
        restriction = wiki_info[len(wiki_info) - 1]
        if "original unit" in restriction.text:
            obj['exclusive'] = True
        else:
            obj['exclusive'] = False

        obj["restriction_weapon"] = False
        obj["restriction_movement"] = False

        if "staff" in restriction.text:
            obj['restriction_weapon'] = ["**Can only** be used by: "]
            obj['restriction_weapon'].append("Staff")

        full_restrict_icons = restriction.find_all('a')
        restrict_icons = []
        for j in full_restrict_icons:
            restrict_icons.append(j['title'])
        if restrict_icons:
            # determine if over 50% of potential weapon and movements are restricted
            restrict_moves = 0
            restrict_weapons = 0
            moves = ["Infantry", "Cavalry", "Flying", "Armored"]
            weapons = ["Red Sword", "Red Dagger", "Red bow", "Red Tome", "Red Breath", "Red Beast", "Blue Lance",
                       "Blue Dagger", "Blue bow", "Blue Tome", "Blue Breath", "Blue Beast", "Green Axe", "Green Dagger",
                       "Green bow", "Green Tome", "Green Breath", "Green Beast", "Staff", "Colorless Dagger",
                       "Colorless bow", "Colorless Tome", "Colorless Breath", "Colorless Beast"]
            for j in restrict_icons:
                if any(x in j for x in moves):
                    restrict_moves = restrict_moves + 1
            for j in restrict_icons:
                if any(x in j for x in weapons):
                    restrict_weapons = restrict_weapons + 1

            if restrict_moves > (len(moves) / 2):
                obj["restriction_movement"] = []
                obj["restriction_movement"].append("**Can only** be used by: ")
                temp = []

                for j in moves:
                    if not any(x in j for x in restrict_icons):
                        temp.append(j)
                obj["restriction_movement"].append(temp)
            elif restrict_moves > 0:
                obj["restriction_movement"] = []
                obj["restriction_movement"].append("**Cannot** be used by: ")
                temp = []
                for j in moves:
                    if any(x in j for x in restrict_icons):
                        temp.append(j)
                obj["restriction_movement"].append(temp)

            if restrict_weapons > (len(weapons) / 2):
                temp = []
                obj["restriction_weapon"] = []
                obj["restriction_weapon"].append("**Can only** be used by: ")
                for j in weapons:
                    if not any(x in j for x in restrict_icons):
                        temp.append(maps.restrictions[j])
                obj["restriction_weapon"].append(temp)
            elif restrict_weapons > 0:
                temp = []
                obj["restriction_weapon"] = []
                obj["restriction_weapon"].append("**Cannot** be used by: ")
                for j in weapons:
                    if any(x in j for x in restrict_icons):
                        temp.append(maps.restrictions[j])
                obj["restriction_weapon"].append(temp)

        # Get the full description
        description = info[0]
        info = utility.removeDuplicates(info)
        for j in range(1, len(info)-1):
            description = description + " " + info[j]
        obj['description'] = description

        blank['skill'].append(obj)

    return blank

def upgrade_passive(name):

    with open('../database/feh/skill.json', 'r', encoding="utf-8") as f:
        skill = json.load(f)
    #get all skill data
    name = name.replace('+', '')
    new_skill = scrape_passive_skill(name.replace('/', ' ').rstrip(string.digits))


    #find the current skill
    key = utility.compress(copy.deepcopy(name))
    key = re.sub(r'[^a-zA-Z]', '', key)

    old_skill = skill[key]
    old_skill['icon'] = new_skill['icon']
    old_skill['skill'] = new_skill['skill']
    ref = {name: {}}
    old_skill['reference'].update(ref)
    old_skill['HARD_ALT_NAME'].append(name)

    skill[key] = old_skill

    with open('../database/feh/skill.json', 'w', encoding="utf-8") as fp:
        json.dump(skill, fp, indent=2)

def upgrade_sp(name):
   
    with open('../database/feh/skill.json', 'r', encoding="utf-8") as f:
        skill = json.load(f)
    #get all skill data
    new_skill =  scrape_assist_special(name.replace('/', ' '))

    #find the current skill

    key = utility.compress(copy.deepcopy(name))
    key = re.sub(r'[^a-zA-Z]', '', key)

    old_skill = skill[key]

    print(len(new_skill['skill']))

    if (len(new_skill['skill']) == 1):
        new_skill['skill'] =  old_skill['skill'] + new_skill['skill'] 
   
    old_skill['skill'] = new_skill['skill']
    ref = {name: {}}
    #old_skill['reference'].update(ref)
    res = {**ref, **old_skill['reference']}
    old_skill['reference'] = res
    old_skill['HARD_ALT_NAME'].append(name)
    old_skill['name'] = name


    skill[key] = old_skill
    
    with open('../database/feh/skill.json', 'w', encoding="utf-8") as fp:
        json.dump(skill, fp, indent=2)

def scrape_captain(page_name):
    with open('templates/skill_temp.json', 'r') as f:
        template = json.load(f)
    blank = template
    # Follow the same steps for feheroes.fandom
    fandom = requests.get(f'https://feheroes.fandom.com/wiki/{page_name}')
    soup = BeautifulSoup(fandom.text, 'html.parser')

    # The information we want on the page is stored under '<div role="document" class="page">
    document = soup.find(class_="mw-parser-output")

    # Create a list that will hold all the info we want to export to the Excel file
    blank['name'] = page_name.replace('_', " ")

    # get the name and title of the unit and append both to the unit_info
    wiki_info = document.find(class_="wikitable default skills-table").find_all('tr')

    # print(len(wiki_info))
    blank['reference'] = {}
    blank['slot'] = "Captain Skill"

    info = list(wiki_info[1].stripped_strings)
    print(info)

    obj = {'name': info[0]}

    name = info.pop(0)
    blank['HARD_ALT_NAME'].append(name)
    

    # Get the full description
    # all other text should be the description now
    info = utility.removeDuplicates(info)
    if ('<td style="text-align:left;" class="full-desc">' in str(wiki_info[1])):
        print('Long Desc')
    description = ""
    for j in info:
        description = description + j + "\n"

    obj['description'] = description[:-2]
    obj['stats'] = {
    "sp" : 0
    }
    obj['slot'] = 'Captain Skill'
    blank['skill'].append(obj)
    

    count = passive_icon_number()
    highest = wiki_info[1]
    url = highest.find_all('td')[0].find_all('a')[0]['href']

    data = requests.get(url).content
    f = open(path + str(count) + '.png', 'wb')
    f.write(data)
    f.close()
    blank['icon'] = count

    return blank
# print(scrape_passive_skill('/wiki/Armored_Wall'))
# print(scrape_passive_skill('/wiki/Armored_Stride'))
# print(scrape_passive_skill('/wiki/Beast_Sense'))
# print(scrape_passive_skill('/wiki/AR-D_Spd_Res'))
# print(scrape_passive_skill('/wiki/Blaze_Dance'))
# print(scrape_passive_skill('/wiki/Dazzling_Staff'))
# print(scrape_assist_special('/wiki/Aegis'))
# print(scrape_assist_special('/wiki/Recover'))
# print(scrape_assist_special('/wiki/Vital_Astra'))
#(scrape_passive_skill('Spd_Res_Hexblade'))
#(scrape_passive_skill('Divine_Deceit'))


