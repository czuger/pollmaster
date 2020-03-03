from pymongo import MongoClient
from essentials.settings import SETTINGS
from pprint import pprint

db_sync_client = MongoClient(SETTINGS.mongo_db)

for p in db_sync_client.pollmaster.polls.find():
    print(f"short = {p['short']}, name = {p['name']}, active = {p['active']}, votes = {p['votes']}")
