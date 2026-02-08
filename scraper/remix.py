import requests
from bs4 import BeautifulSoup
import json
import integrate

def main(mainkey):
	with open('../database/feh/char.json', 'r', encoding="utf-8") as f:
		char = json.load(f)

	unit = char[mainkey]
	page_name = unit['name'] + ": " + unit['title']

	fandom = requests.get(f'https://feheroes.fandom.com/wiki/{page_name}')
	soup = BeautifulSoup(fandom.text, 'html.parser')
	document = soup.find(class_="mw-parser-output")

	skill_tables = document.find_all(class_="wikitable default unsortable skills-table")
	unit['weapons'] = {}
	wep_table = skill_tables[0].find_all('tr')
	for i in range(1, len(wep_table)):
		cols = wep_table[i].find_all('td')
		wep = list(cols[0].stripped_strings)[0]
		unlock = list(cols[6].stripped_strings)[0]
		unit['weapons'][wep] = unlock

	key = 'assist'
	table2 = skill_tables[1].find_all('tr')
	headers = list(table2[0].stripped_strings)

	if 'Cooldown' in headers:
		key = 'special'

	unit['special'] = {}
	unit['assist'] = {}
	for i in range(1, len(table2)):
		cols = table2[i].find_all('td')
		skill = list(cols[0].stripped_strings)[0]
		unlock = list(cols[5].stripped_strings)[0]
		unit[key][skill] = unlock

	if len(skill_tables) > 2:
		key = 'special'
		table2 = skill_tables[2].find_all('tr')
		for i in range(1, len(table2)):
			cols = table2[i].find_all('td')
			skill = list(cols[0].stripped_strings)[0]
			unlock = list(cols[5].stripped_strings)[0]
			unit[key][skill] = unlock

	passive_table = document.find_all(class_="wikitable default")[-1]

	ptable = passive_table.find_all('tr')
	slot = 'A'
	from collections import defaultdict
	skills = defaultdict(dict)
	skills['A'] = {}
	skills['B'] = {}
	skills['C'] = {}
	skills['X'] = {}
	for i in range(1, len(ptable)):
		cols = list(ptable[i].stripped_strings)

		if cols[0] == 'A' or cols[0] == 'B' or cols[0] == 'C' or cols[0] == 'X':
			slot = cols[0]
			name = cols[1]
			unlock = cols[len(cols) - 1]

		else:
			name = cols[0]
			unlock = cols[len(cols) - 1]
		skills[slot][name] = unlock
	unit['passive'] = skills

	char[mainkey] = unit

	with open('../database/feh/char.json', 'w', encoding="utf-8") as fp:
		json.dump(char, fp, indent=2)
		integrate.integrate_skills(mainkey)

	



main('medeus')
main('shez3')