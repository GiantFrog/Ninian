import Webscraper

import weapon
import json
import skill_scrape

obj = {}

file =  './sk.json'


#skill_scrape.upgrade_sp('')
#skill_scrape.upgrade_passive('Swift Slice')
#skill_scrape.upgrade_passive('Assured Rebirth')

with open(file, 'w') as fp:
    json.dump(obj, fp)
    


units = [
    "Azura: Lady of the Sky",
    "Hilda: Skyward Wings",
    "Mia: Zenith Challenger",
    "Minerva: Above the Stars"
]



alts = ["Cosplay", "Pegknight"]  # 'None' (as in null) uses defaults such as "normal" and "regular". use [] for no alts. maybe this is unintuitive.
#alts = ["Winter", "Christmas", "W"]

version = None  # will calculate the book & chapter the game is currently on when this is run
#version = "9.0"

for i in range(0, len(units)):
    Webscraper.scrape_page(f"/wiki/{units[i]}", provided_alts=alts, version=version)