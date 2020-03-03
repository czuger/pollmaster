from bson import ObjectId
from datetime import datetime

class VotesStats:
    def __init__(
            self,
            poll_id,
            user_id,
            choice: int
    ):
        self.poll_id = poll_id
        self.user_id = str(user_id)
        self.choice = choice

    async def save_to_db(self, bot, channel):

        print(self.poll_id)
        poll = await bot.db.polls.find_one({'_id': self.poll_id})
        print(poll)

        poll_name = poll['name']
        poll_short = poll['short']
        choice = poll['options_reaction'][self.choice]

        member = channel.guild.get_member(int(self.user_id))
        if member.nick:
            member_name = member.nick
        else:
            member_name = member.name

        result = await bot.db.vote_stats.insert_one(
            {'poll_name': poll_name, 'poll_short': poll_short, 'choice': choice,
             'participant': member_name, 'created_at': datetime.now()}
        )
