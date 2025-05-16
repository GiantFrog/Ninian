import requests
from bs4 import BeautifulSoup
import json
import portrait
import integrate
import utility


def scrape_resp(key):

    with open('../database/feh/char.json', 'r') as f:
        char = json.load(f)

    unit = char[str(key)]
    del unit['resplendent_images']
    del unit['resplendent']
    del unit['resplendent_voice']
    del unit['quotes']['resplendent']

    resp = {
    'resplendent_images' : {},
    'resplendent' : "",
    'quotes' : {
    'resplendent' : {}
    }
    }

    page_name = unit['name'] + ': ' + unit['title']

    # Follow the same steps for feheroes.fandom
    fandom = requests.get(f'https://feheroes.fandom.com/wiki/{page_name}')
    soup = BeautifulSoup(fandom.text, 'html.parser')

    # The information we want on the page is stored under '<div role="document" class="page">
    document = soup.find(class_="mw-parser-output")

    # get the unit's name, images, and other info found in the first table
    wiki_info = document.find(class_="wikitable hero-infobox").find_all('tr')
    ogname = list(wiki_info[0].stripped_strings)[0]
   
    art = list(wiki_info[1].stripped_strings)  # art
    art_full = wiki_info[1]
    atags = art_full.find_all('a')
    voice = ""


    # determine if there is a Resplendent alt
    if art[0] == 'Standard Attire':
        # if there is, get the alt info
        unit['resplendent'] = art[art.index("Art by:", 6) + 1]  # Resplendent artist's name
        i = 5
        if "https" not in atags[5]['href']:  # This check accounts for cases with an artist + Intelligent Systems
            i += 1
        resp['resplendent_images']['portrait'] = atags[i]['href']
        i += 1
        resp['resplendent_images']['attack'] = atags[i]['href']
        i += 1
        resp['resplendent_images']['special'] = atags[i]['href']
        i += 1
        resp['resplendent_images']['damage'] = atags[i]['href']
        i += 1
        unit['resplendent_images'] = resp['resplendent_images']


    # Iterate through each table in wiki_info to search for the other wiki box entries
    for i in wiki_info:
       
        if " EN" in i.text:
            strings = list(i.stripped_strings)
            if strings[2] != '(Resplendent Attire)':
                voice = strings[2]
        if "(Resplendent Attire)" in i.text:
            strings = list(i.stripped_strings)
            unit['resplendent_voice'] = strings[3]
        

    if 'resplendent_voice' not in resp.keys():
        unit['resplendent_voice'] = voice
 

    # Quotes stuff
    fandomquote = requests.get(f'https://feheroes.fandom.com/wiki/{page_name}/Quotes')
    soupquote = BeautifulSoup(fandomquote.text, 'html.parser')

    documentquote = soupquote.find(class_="mw-parser-output")

    quotes = documentquote.find_all('blockquote')


    # Create a dictionary for the Resplendent quotes where applicable
    quotedict = {'Summon': False, 'Level': False, 'Castle Hall': False, 'Visit': False, 'Learn Skill': False, 'Confession': False,
                 'Special': [], 'Status': [], 'Map Select': []}

    a = 0
    #if utility.is_brave(unit):
        #a = 1

    q_table = documentquote.find_all(class_="wikitable")
    spc = q_table[16+a].find_all('td')
    spc_clean = []
    for i in range(0, len(spc)):
        spc_clean.append(list(spc[i].stripped_strings)[0])
        



    quotedict['Special'].append(spc_clean[1])
    quotedict['Special'].append(spc_clean[3])
    quotedict['Special'].append(spc_clean[5])
    quotedict['Special'].append(spc_clean[7])

    spc = q_table[18+a].find_all('td')
    spc_clean = []
    for i in range(0, len(spc)):
        spc_clean.append(list(spc[i].stripped_strings)[0])

    spc = q_table[20+a].find_all('td')
    spc_clean = []
    for i in range(0, len(spc)):
        if i == ((len(spc_clean)) * 3 + 1) and len(list(spc[i].stripped_strings)) != 0:
            spc_clean.append(list(spc[i].stripped_strings)[0])
        elif i == ((len(spc_clean)) * 3 + 1):
            spc_clean.append('')

    for i in spc_clean:
        quotedict['Status'].append(i)

    spc = q_table[22+a].find_all('td')
    for i in range(0, len(spc)):
        if i % 2 == 1:
            quotedict['Map Select'].append(list(spc[i].stripped_strings)[0])

    unit['quotes']['resplendent'] = quotedict

    char[key] = unit
    
    file = './../database/feh/char.json'

    portrait.portrait(key, unit, True)

    with open(file, 'w') as fp:
        json.dump(char, fp, indent=2)

    integrate.credits(key, True)

    return

scrape_resp('athena')