import requests
from bs4 import BeautifulSoup
import json

path = '../database/feh/images/wpn/'

def scrape_page(page_name):
    with open('templates/wep.json', 'r') as f:
        template = json.load(f)
    blank = template
    # Follow the same steps for feheroes.fandom
    fandom = requests.get(f'https://feheroes.fandom.com/wiki/{page_name}')
    soup = BeautifulSoup(fandom.text, 'html.parser')

    # The information we want on the page is stored under '<div role="document" class="page">
    document = soup.find(class_="mw-parser-output")
    # get the name and title of the unit and append both to the unit_info

    wiki_info = document.find(class_="wikitable default ibox").find_all('tr')
    #print(wiki_info)
    
    blank['name'] = list(wiki_info[0].stripped_strings)[0]
    blank['skill'][0]['name'] = list(wiki_info[0].stripped_strings)[0]

    art_full = wiki_info[1]
    atags = art_full.find_all('a')
    url = atags[0]['href']
    name = url[68:77].lower() 
    
    try:
        data = requests.get(url).content
    except:
        blank['wpn'] = False 
    else:
        f = open(path + name + '.png','wb')
        f.write(data)
        f.close()
        blank['wpn'] = name.lower()


    for i in wiki_info:
        if "Weapon type" in i.text.replace(u'\xa0', ' '):
            blank['skill'][0]['weapon_type'] = i.find_all('a')[0]['title'].replace(' ', '_')
        if "Might" in i.text:
            strings = list(i.stripped_strings)
            blank['skill'][0]['stats']["mt"] = strings[1]
        if "Range" in i.text:
            strings = list(i.stripped_strings)
            if strings[0] == 'Range':
                blank['skill'][0]['stats']["rng"] = strings[1]
        if "SP" in i.text:
            strings = list(i.stripped_strings)
            blank['skill'][0]['stats']["sp"] = strings[1]
        if "Exclusive" in i.text:
            strings = list(i.stripped_strings)
            if strings[1] == 'No':
                blank['skill'][0]['exclusive'] = False
            else:
                blank['skill'][0]['exclusive'] = True
        if "Description" in i.text:
            desc = list(i.stripped_strings)
            desc2 = '\n'.join(desc)

            if '[\nExpand\nCollapse\n]' in desc2:
                parts = str(i).split('style="text-align:left;">')
                desc2 = parts[2][0:-10]
                desc2 = desc2.replace('<br/>', '\n')
                desc2 = desc2.replace('\n\n', '\n')

            
            blank['skill'][0]['description'] = desc2

    obj = {
        list(wiki_info[0].stripped_strings)[0]: {}
    }
    blank['reference'] = obj
    


    return blank


#scrape_page('Wildflower_Edge')
#scrape_page('Binding_Blade')

#scrape_page('Deliverer%27s_Brand')
