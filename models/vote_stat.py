from datetime import datetime


class VotesStats:

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
             'participant': member_name, 'created_at': datetime.now(), 'vote_uuid': vote.uuid}
        )
