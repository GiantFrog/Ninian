from datetime import datetime, timedelta
import os
import psycopg
from psycopg.types import TypeInfo
from psycopg.types.hstore import register_hstore

connection = psycopg.connect(os.getenv('DATABASE_CONNECTION'))
type_info = TypeInfo.fetch(connection, "hstore")
register_hstore(type_info, connection)
with connection.cursor() as cursor:
    cursor.execute("""
        create table if not exists users (
            id bigint primary key not null,
            sommie_pets int default 0,
            favorite_hero varchar(64),
            custom_aliases hstore default hstore(''),
            banned_until timestamp,
            ban_message text
    );""")
    connection.commit()

def sommie_pets():
    with connection.cursor() as db:
        db.execute("select sum(sommie_pets) from users;")
        return db.fetchone()[0]


class User:
    def __init__(self, user_id):
        try:
            self.id = int(user_id)
            with connection.cursor() as db:
                db.execute(f"select * from users where id = {self.id};")
                database_row = db.fetchone()
                if database_row is None:    # Never seen this person before.
                    db.execute(f"insert into users(id) values ({self.id});")
                    connection.commit()
                    self.sommie_pets = 0
                    self.favorite_hero = None
                    self.custom_aliases = {}
                    self.banned_until = None
                    self.ban_message = None
                else:   # Unwrap a tuple fetched from the DB into a nice python object!
                    self.sommie_pets = database_row[1]
                    self.favorite_hero = database_row[2]
                    self.custom_aliases = database_row[3] or {}
                    self.banned_until = database_row[4]
                    self.ban_message = database_row[5]
        except Exception as e:
            print(f"ERROR: Couldn't make a User for ID {self.id}.\n{e}")

    # You may read from this class's variables all you want, but please only modify them using the below functions!
    # Is one missing? Add it here! This way, we can keep the database synced and only updated in intentional ways.
    def pet_sommie(self):
        with connection.cursor() as db:
            db.execute(f"update users set sommie_pets = sommie_pets + 1 where id = {self.id};")
            connection.commit()
        self.sommie_pets += 1

    def set_favorite_hero(self, hero: str):
        if self.favorite_hero == hero:
            return
        with connection.cursor() as db:
            db.execute(
                f"update users set favorite_hero = (%s::text) where id = {self.id};",
                [hero]                        # This silly little thing should fight SQL injection.
            )                                 # I trust self.id because in init we make sure it's an int.
            connection.commit()
        self.favorite_hero = hero

    def add_alias(self, alias: str, real_name: str):
        if self.custom_aliases.get(alias) == real_name:
            return
        with connection.cursor() as db:
            db.execute(
                f"update users set custom_aliases = custom_aliases || (%s::hstore) where id = {self.id};",
                [f'"{alias}"=>"{real_name}"']  # god it took forever to get the quotes and typing right
            )
            connection.commit()
        self.custom_aliases[alias] = real_name

    def remove_alias(self, alias: str):
        if alias not in self.custom_aliases:
            return
        with connection.cursor() as db:
            db.execute(
                f"update users set custom_aliases = custom_aliases - (%s::text) where id = {self.id};",
                [alias]
            )
            connection.commit()
        del self.custom_aliases[alias]

    def ban(self, duration=timedelta(weeks=2871), reason=None):  # default: 400 years
        ban_timestamp = datetime.now() + duration
        with connection.cursor() as db:
            db.execute(
                f"update users set banned_until = (%s::timestamp), ban_message = (%s::text) where id = {self.id};",
                [ban_timestamp, reason]
            )
            connection.commit()
        self.banned_until = ban_timestamp
        self.ban_message = reason

    def unban(self):
        with connection.cursor() as db:
            db.execute(f"update users set banned_until = null where id = {self.id};")
            connection.commit()
        self.banned_until = None

    def is_banned(self) -> bool:
        if self.banned_until is None:
            return False
        return self.banned_until > datetime.now()
