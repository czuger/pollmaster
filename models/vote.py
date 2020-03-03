from bson import ObjectId
import uuid
from .vote_stat import VotesStats


class Vote:
    def __init__(
            self,
            bot,
            poll_id: ObjectId,
            user_id,
            choice: int,
            weight: int = 1,
            answer: str = '',
            _id: ObjectId = None,
            db_uuid: str = None
    ):
        self._id = _id
        self.poll_id = poll_id
        self.bot = bot
        self.user_id = str(user_id)
        self.choice = choice
        self.weight = weight
        self.answer = answer
        self.db_uuid = db_uuid

    @staticmethod
    async def load_from_db(bot, poll_id: ObjectId, user_id, choice: int):
        user_id = str(user_id)
        query = await bot.db.votes.find_one(
            {'poll_id': poll_id, 'user_id': user_id, 'choice': choice})
        if query is not None:
            db_uuid = None
            if 'db_uuid' in query:
                db_uuid = query['db_uuid']
            v = Vote(bot, poll_id, user_id, choice, query['weight'], query['answer'], query['_id'], db_uuid)
            return v
        else:
            return None

    @staticmethod
    async def load_all_votes_for_poll(bot, poll_id: ObjectId,):
        query = bot.db.votes.find({'poll_id': poll_id})
        if query is not None:
            votes = [Vote(bot, poll_id, v['user_id'], v['choice'], v['weight'], v['answer'], v['_id'])
                     async for v in query]
            return votes
        else:
            return None

    @staticmethod
    async def load_vote_counts_for_poll(bot, poll_id: ObjectId,):
        pipeline = [
            {"$match": {'poll_id': poll_id}},
            {"$group": {"_id": "$choice", "count": {"$sum": 1}}}
        ]
        query = bot.db.votes.aggregate(pipeline)
        result = {}
        async for q in query:
            result[q['_id']] = q['count']
        return result

    @staticmethod
    async def load_votes_for_poll_and_user(bot, poll_id: ObjectId, user_id):
        user_id = str(user_id)
        query = bot.db.votes.find({'poll_id': poll_id, 'user_id': user_id})
        if query is not None:
            votes = [Vote(bot, poll_id, v['user_id'], v['choice'], v['weight'], v['answer'], v['_id'])
                     async for v in query]
            return votes
        else:
            return None

    @staticmethod
    async def load_number_of_voters_for_poll(bot, poll_id: ObjectId):
        query = await bot.db.votes.distinct('user_id', {'poll_id': poll_id})
        if query:
            return len(query)
        else:
            return 0

    def to_dict(self):
        return ({
            'poll_id': self.poll_id,
            'user_id': self.user_id,
            'choice': self.choice,
            'weight': self.weight,
            'answer': self.answer,
            'db_uuid': self.db_uuid
        })

    async def save_to_db(self):
        self.db_uuid = str(uuid.uuid1())
        await self.bot.db.votes.update_one(
            {'poll_id': self.poll_id, 'user_id': str(self.user_id), 'choice': self.choice},
            {'$set': self.to_dict()},
            upsert=True
        )

    async def delete_from_db(self):
        if self._id:
            self.bot.db.votes.delete_one({'_id': self._id})
            await VotesStats.delete(self.bot, self.db_uuid)

    def __str__(self):
        return f'{self._id}, poll_id={self.poll_id}, user_id={self.user_id}, choice={self.choice}, answer={self.answer}'

