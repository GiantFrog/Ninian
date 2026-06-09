import os

import psycopg
from psycopg.types import TypeInfo
from psycopg.types.hstore import register_hstore

from scraper.api_data.queries import get_romanized_artist_name, get_romanized_va_name
from scraper.api_data.utils import is_japanese
from scraper.maps import entrymap, wepmap, restrictions
from scraper.utility import compress, skill_family_id, skill_family_name
import scraper.maps


class LocalDB:
    def __init__(self, wiki_client, user='ninian', password=os.environ['DB_PASSWORD'], address='127.0.0.1', dbname='ninian'):
        self.connection = psycopg.connect(f"user={user} password={password} hostaddr={address} dbname={dbname} gssencmode=disable")
        type_info = TypeInfo.fetch(self.connection, "hstore")
        register_hstore(type_info, self.connection)
        self.wiki = wiki_client     # we still gotta look some things up on-the-fly

    async def add_unit(self, unit):
        # SKILLS
        if 'weapon' in unit:
            for skill in unit['weapon']:
                self.add_skill(skill, 'Weapon')
        if 'assist' in unit:
            for skill in unit['assist']:
                self.add_skill(skill, 'Assist')
        if 'special' in unit:
            for skill in unit['special']:
                self.add_skill(skill, 'Special')
        if 'passive_a' in unit:
            for skill in unit['passive_a']:
                self.add_skill(skill, 'Passive A')
        if 'passive_b' in unit:
            for skill in unit['passive_b']:
                self.add_skill(skill, 'Passive B')
        if 'passive_c' in unit:
            for skill in unit['passive_c']:
                self.add_skill(skill, 'Passive C')
        if 'passive_x' in unit:
            for skill in unit['passive_x']:
                self.add_skill(skill, 'Passive X')

        # ARTISTS AND VAs
        with self.connection.cursor() as db:
            for artist in ['artist', 'resplendent']:
                if unit[artist]:
                    if is_japanese(unit[artist]):
                        jp_name = unit[artist]
                        en_name = await get_romanized_artist_name(self.wiki, unit[artist])
                        unit[artist] = en_name
                    else:
                        jp_name = None
                        en_name = unit[artist]
                    db.execute("""
                        insert into artists (english_name, japanese_name)
                        values (%s::text, %s::text)
                        on conflict do nothing;""",
                        [en_name, jp_name]
                    )
            for va in ['voice_en', 'resplendent_voice', 'voice_jp', 'resplendent_voice_jp']:
                if unit[va]:
                    if is_japanese(unit[va]):
                        jp_name = unit[va]
                        en_name = await get_romanized_va_name(self.wiki, unit[va])
                        unit[va] = en_name
                    else:
                        jp_name = None
                        en_name = unit[va]
                    db.execute("""
                        insert into voice_actors (english_name, japanese_name)
                        values (%s::text, %s::text)
                        on conflict do nothing;""",
                        [en_name, jp_name]
                    )
            self.connection.commit()

        #TODO  1. query for all skills missing a description  2. pull skill info for all these new skills
        titles = unit['origin'].split(',')
        continents = ['']
        chibi = ''
        for title in entrymap:
            if title in titles[0] and title != '':
                continents[0] = entrymap[title]['pool'].capitalize()
                chibi = entrymap[title]['chibi']
            elif len(titles) > 1 and title in titles[1] and title != '':
                continents.append(entrymap[title]['pool'].capitalize())
        if not continents:
            print(f"WARN: no origin found for {unit['name']} ({unit['origin']})!")

        with self.connection.cursor() as db:
            db.execute("select continent, name from characters where %s=any(array_append(aliases, name)) limit 1;", [unit['name']])
            database_row = db.fetchone()
            # If we already have a character with the same name or alias...
            if database_row is not None and continents[0] == database_row[0] and unit['name'] == database_row[1]:
                new_character = False
            elif database_row is not None and (continents[0] == database_row[0] or unit['name'] == database_row[1]):
                if input(f"Is {continents[0]} {unit['name']} the same person as {database_row[0]} {database_row[1]}? (y/n) - ")[0].lower() == 'y':
                    new_character = False
            else:
                new_character = True
            if new_character:
                db.execute("""
                    insert into characters (continent, name)
                    values (%s::text, %s::text);""",
                    [continents[0], unit['name']]
                )
                character_origin = continents[0]
                character_fkey = unit['name']
            else:
                character_origin = database_row[0]
                character_fkey = database_row[1]

            weapon_classification = f"{unit['color']} {unit['weapon_type']}"
            emoji = f"<:{restrictions[weapon_classification]}:{wepmap[weapon_classification]}>"
            db.execute("select count(*) from feh_units where simplified_name like %s;", [compress(unit['name'])])
            alt_count = db.fetchone()[0]
            if alt_count > 0:
                alt_count += 1
            else:
                alt_count = None
            # TODO MISSING: rarity, summon_pool, quotes, prf, resplendent voice, unit_type
            db.execute("""
                insert into feh_units (id, simplified_name, alt_number, name, emoji, title, description, artist, move_type, weapon_type, color, version, bases, growths, superboons, superbanes, images, resplendent_images, gender, rarity, internal_id, resplendent_artist, resplendent_english_va, resplendent_japanese_va, continents, chibi, character_fkey, character_origin, english_voice_actor, japanese_voice_actor, origin_games, duel_bst, duo_skill, harmonized_skill, emblem_effect, weapon, assist, special, passive_a, passive_b, passive_c, passive_x, backpack_fkey, backpack_origin, backpack_english_va, backpack_japanese_va)
                values (%s::integer, %s::text, %s::integer, %s::text, %s::text, %s::text, %s::text, %s::text, %s::text, %s::text, %s::text, %s::text, %s::hstore, %s::hstore, %s::text[], %s::text[], %s::hstore, %s::hstore, %s::char, %s::integer, %s::text, %s::text, %s::text, %s::text, %s::text[], %s::text, %s::text, %s::text, %s::text, %s::text, %s::text[], %s::integer, %s::text, %s::text, %s::text, %s::hstore, %s::hstore, %s::hstore, %s::hstore, %s::hstore, %s::hstore, %s::hstore, %s::text, %s::text, %s::text, %s::text)
                on conflict (id) do nothing;""",
                [unit['id'], compress(unit['name']), alt_count, unit['name'], emoji, unit['title'], unit['description'], unit['artist'], unit['move'], unit['weapon_type'], unit['color'], unit['version'], hstore(unit['base']), hstore(unit['growth']), unit['superboons'], unit['superbanes'], hstore(unit['images']), hstore(unit['resplendent_images']), unit['gender'], unit['rarity'], unit['internal_id'], unit['resplendent'], unit['resplendent_voice'], unit['resplendent_voice_jp'], continents, chibi, character_fkey, character_origin, unit['voice_en'], unit['voice_jp'], titles, unit['duel'], unit['duo'], unit['harmonized'], unit['emblem'], hstore(unit['weapon']), hstore(unit['assist']), hstore(unit['special']), hstore(unit['passive_a']), hstore(unit['passive_b']), hstore(unit['passive_c']), hstore(unit['passive_x']), None, None, unit['backpack_voice'], unit['backpack_voice_jp']]
            )
            self.connection.commit()

    def add_skill(self, skill_name, slot):
        with self.connection.cursor() as db:
            db.execute("""
                insert into skill_families (id, name, slot)
                values (%s::text, %s::text, %s::text)
                on conflict do nothing;""",
                [skill_family_id(skill_name), skill_family_name(skill_name), slot]
            )
            db.execute("""
                insert into skills (name, skill_family)
                values (%s::text, %s::text)
                on conflict do nothing;""",
                [skill_name, skill_family_id(skill_name)]
            )
            self.connection.commit()

def hstore(dict):
    if not dict:
        return None
    string = ''
    for key, value in dict.items():
        string += f'"{key}" => "{value}",\n'
    return string[:-2]    # remove final newline and comma

