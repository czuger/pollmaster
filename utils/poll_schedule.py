import datetime
import asyncio
import logging

from models.poll import Poll
# Will create a circular dependency if imported.
# resulting in an ImportError: Cannot import name X
# from pollmaster import bot


# logger for scheduled polls
scheduled_logger = logging.getLogger('scheduled_polls')
scheduled_logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
sch_fh = logging.FileHandler('logs/scheduled_polls.log',  encoding='utf-8', mode='a+')
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
sch_fh.setFormatter(formatter)
# add the handlers to the scheduled_logger
scheduled_logger.addHandler(sch_fh)

last_hour_show_key = None


def poll_shown_this_hour(cur_weekday, cur_hour):
    global last_hour_show_key

    last_hour_key = "{}_{}".format(cur_weekday, cur_hour)
    scheduled_logger.debug("last_hour_key={}, last_hour_show_key={}".format(last_hour_key, last_hour_show_key))
    if last_hour_key is None or last_hour_key != last_hour_show_key:
        last_hour_show_key = last_hour_key
        scheduled_logger.debug("Poll not shown this hour")
        return False

    scheduled_logger.debug("Poll shown this hour")
    return True


async def show_poll(poll):
    """asyncio.sleep is not precise. We can't rely on it."""
    scheduled_logger.debug('Poll should be launched')
    scheduled_logger.debug("poll={}".format(poll))

    channel = bot.get_channel(int(poll['channel_id']))
    scheduled_logger.debug("channel={}".format(channel))
    await channel.send('Hello')

    poll_from_db = await Poll.load_from_db(bot, poll['server_id'], poll['short'])
    await poll_from_db.clear_votes()

    await poll_from_db.post_embed(channel)
    scheduled_logger.debug("Poll posted")


async def scheduled_polls_loop():
    scheduled_logger.debug('In scheduled_polls_loop')
    while True:
        await asyncio.sleep(1800)

        now = datetime.datetime.now()

        cur_weekday = now.weekday()
        cur_hour = now.hour

        scheduled_logger.debug("Schedule log start {}".format(now))
        scheduled_logger.debug("cur_weekday={}, cur_hour={}".format(cur_weekday, cur_hour))

        if not poll_shown_this_hour(cur_weekday, cur_hour):
            async for poll in bot.db.polls.find({"scheduled_time": {"$exists": True}}):
                scheduled_logger.debug(
                    "poll['short']={}, poll['scheduled_time']={}".format(poll['short'], poll['scheduled_time']))

                sched_weekday = int(poll['scheduled_time']['weekday'])
                sched_hour = int(poll['scheduled_time']['hour'])

                scheduled_logger.debug("sched_weekday={}, sched_hour={}".format(sched_weekday, sched_hour))

                if cur_weekday == sched_weekday and cur_hour == sched_hour:
                    show_poll(poll)

        scheduled_logger.debug("Schedule log end")


def start_scheduled_polls_loop():
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_polls_loop())
