import json
import sys
import traceback
import threading
import aiohttp
import discord
import logging
import datetime
import asyncio

from essentials.messagecache import MessageCache
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from models.vote_stat import VotesStats

from essentials.multi_server import get_pre
from essentials.settings import SETTINGS
from models.poll import Poll

print(f'Started at {datetime.datetime.now()}', flush=True)

bot_config = {
    'command_prefix': get_pre,
    'pm_help': False,
    'status': discord.Status.online,
    'owner_id': SETTINGS.owner_id,
    'fetch_offline_members': False,
    'max_messages': 15000
}

bot = commands.AutoShardedBot(**bot_config)
bot.remove_command('help')

bot.message_cache = MessageCache(bot)
bot.refresh_blocked = {}
bot.refresh_queue = {}

# logger
# create logger with 'spam_application'
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('logs/pollmaster.log',  encoding='utf-8', mode='a+')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

extensions = ['cogs.config', 'cogs.poll_controls', 'cogs.help', 'cogs.db_api', 'cogs.admin']
for ext in extensions:
    bot.load_extension(ext)

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


@bot.event
async def on_ready():
    bot.owner = await bot.fetch_user(SETTINGS.owner_id)

    mongo = AsyncIOMotorClient(SETTINGS.mongo_db)
    bot.db = mongo.pollmaster
    bot.session = aiohttp.ClientSession()
    print(bot.db, flush=True)

    bot.db_sync_client = MongoClient(SETTINGS.mongo_db)
    print(bot.db_sync_client)

    # load emoji list
    with open('utils/emoji-compact.json', encoding='utf-8') as emojson:
        bot.emoji_dict = json.load(emojson)

    # check discord server configs
    try:
        db_server_ids = [entry['_id'] async for entry in bot.db.config.find({}, {})]
        print(db_server_ids)
        for server in bot.guilds:
            print(server)
            if str(server.id) not in db_server_ids:
                # create new config entry
                await bot.db.config.update_one(
                    {'_id': str(server.id)},
                    {'$set': {'prefix': 'pm!', 'admin_role': 'polladmin', 'user_role': 'polluser'}},
                    upsert=True
                )
    except:
        print("Problem verifying servers.")

    # cache prefixes
    bot.pre = {entry['_id']: entry['prefix'] async for entry in bot.db.config.find({}, {'_id', 'prefix'})}

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="pm!help"))

    # print(await bot.db.polls.count_documents({}))
    #
    # async for poll in bot.db.polls.find({}):
    #     print(poll)

    print("Servers verified. Bot running.")

    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_polls_loop())


@bot.event
async def on_command_error(ctx, e):

    if hasattr(ctx.cog, 'qualified_name') and ctx.cog.qualified_name == "Admin":
        # Admin cog handles the errors locally
        return

    if SETTINGS.log_errors:
        ignored_exceptions = (
            commands.MissingRequiredArgument,
            commands.CommandNotFound,
            commands.DisabledCommand,
            commands.BadArgument,
            commands.NoPrivateMessage,
            commands.CheckFailure,
            commands.CommandOnCooldown,
            commands.MissingPermissions
        )

        if isinstance(e, ignored_exceptions):
            # log warnings
            # logger.warning(f'{type(e).__name__}: {e}\n{"".join(traceback.format_tb(e.__traceback__))}')
            return

        # log error
        logger.error(f'{type(e).__name__}: {e}\n{"".join(traceback.format_tb(e.__traceback__))}')
        traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)

        if SETTINGS.msg_errors:
            # send discord message for unexpected errors
            e = discord.Embed(
                title=f"Error With command: {ctx.command.name}",
                description=f"```py\n{type(e).__name__}: {str(e)}\n```\n\nContent:{ctx.message.content}"
                            f"\n\tServer: {ctx.message.server}\n\tChannel: <#{ctx.message.channel}>"
                            f"\n\tAuthor: <@{ctx.message.author}>",
                timestamp=ctx.message.timestamp
            )
            await ctx.send(bot.owner, embed=e)

        # if SETTINGS.mode == 'development':
        raise e


@bot.event
async def on_guild_join(server):
    result = await bot.db.config.find_one({'_id': str(server.id)})
    if result is None:
        await bot.db.config.update_one(
            {'_id': str(server.id)},
            {'$set': {'prefix': 'pm!', 'admin_role': 'polladmin', 'user_role': 'polluser'}},
            upsert=True
        )
        bot.pre[str(server.id)] = 'pm!'

# config = bot.db.config
# for c in config:
#     print(c)

print('************************************************************')
print('Bot started')
print('************************************************************')
bot.run(SETTINGS.bot_token)

print('************************************************************')
print('Bot stopped')
print('************************************************************')
print(bot)
