import re
import unidecode
import json
import string

def removeDuplicates(myDict):
    return list(dict.fromkeys(myDict))

def sortDict(myDict):
    sortedDict = dict(sorted(myDict.items()))
    return sortedDict

def sortById():
    f = open('../database/feh/char.json')
    list = json.load(f)
    sortedList = dict(sorted(list.items(), key=lambda x: int(x[1]['id'])))
    with open('../database/feh/char.json', 'w', encoding="utf-8") as fp:
        json.dump(sortedList, fp, indent=2)
    return sortedList

def compress(string):
    new_string = unidecode.unidecode(string)
    new_string = re.sub(r'[^a-zA-Z0-9]','', new_string)
    if (string.endswith(' II')):
        new_string = re.sub('II$', '', new_string)
    new_string = new_string.lower()
    return(new_string)

def skill_family_id(skill):
    return compress(skill).rstrip(string.digits)

def skill_family_name(skill):
    return skill.replace('+', '').replace('/', ' ').rstrip(string.digits)

def is_brave(unit):
    res = [i for i in unit['ALT_NAME'] if 'Brave' in i]
    if (len(res) > 0):
        return True
    else:
        return False

def remove_num(arg):
    return arg.rstrip(string.digits)
    

#sortById()