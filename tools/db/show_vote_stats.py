from pymongo import MongoClient
from essentials.settings import SETTINGS
from pprint import pprint

db_sync_client = MongoClient(SETTINGS.mongo_db)

for p in db_sync_client.pollmaster.vote_stats.find():
    if 'participant' in p and 'created_at' in p:
        print(f"poll_name = {p['poll_name']}, poll_short = {p['poll_short']}, choice = {p['choice']}, "
              f"participant = {p['participant']}, created_at = {p['created_at']}")

