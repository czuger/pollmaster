from datetime import datetime
from collections import Counter


class VotesStats:

    @staticmethod
    async def get_stats_dict(bot):
        # print(await bot.db.list_collection_names())
        # print(await bot.db.vote_stats.find_one())
        # print(await bot.db.vote_stats.count_documents({}))

        c = bot.db.vote_stats.find()

        choices_list = []
        async for e in c:
            choices_list.append(e['choice'])
        stats = Counter(choices_list)

        print(stats)

        return stats

    @classmethod
    async def create(cls, bot, channel, vote):
        poll = await bot.db.polls.find_one({'_id': vote.poll_id})
        print(poll)

        poll_name = poll['name']
        poll_short = poll['short']
        choice = poll['options_reaction'][vote.choice]

        member = channel.guild.get_member(int(vote.user_id))
        if member.nick:
            member_name = member.nick
        else:
            member_name = member.name

        await bot.db.vote_stats.insert_one(
            {'poll_name': poll_name, 'poll_short': poll_short, 'choice': choice,
             'participant': member_name, 'created_at': datetime.now(), 'vote_uuid': vote.db_uuid}
        )

    @classmethod
    async def delete(cls, bot, vote_uuid):
        print("vote_uuid to delete = ", vote_uuid)
        await bot.db.vote_stats.delete_many({'vote_uuid': vote_uuid})
