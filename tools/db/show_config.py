from pymongo import MongoClient
from essentials.settings import SETTINGS
from pprint import pprint

db_sync_client = MongoClient(SETTINGS.mongo_db)

for c in db_sync_client.pollmaster.config.find():
    pprint(c)
