import sys
from pymongo import MongoClient
from essentials.settings import SETTINGS
from pprint import pprint

print(sys.argv[1])

db_sync_client = MongoClient(SETTINGS.mongo_db)

poll = db_sync_client.pollmaster.polls.find_one({'short': sys.argv[1]})
pprint(poll)
print()

for v in db_sync_client.pollmaster.votes.find({'poll_id': poll['_id']}):
    pprint(v)
    print()

# for c in db_sync_client.pollmaster.config.find():
#     pprint(c)
#
# print()
# for c in db_sync_client.pollmaster.polls.find():
#     pprint(c)
#
# print()
