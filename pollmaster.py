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
fh = logging.FileHandler('pollmaster.log',  encoding='utf-8', mode='w')
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


async def scheduled_polls_loop():
    print('In scheduled_polls_loop')
    while True:
        await asyncio.sleep(3600)

        now = datetime.datetime.now()

        cur_weekday = now.weekday()
        cur_hour = now.hour

        print("cur_weekday={}, cur_hour={}".format(cur_weekday, cur_hour))

        async for poll in bot.db.polls.find({"scheduled_time": {"$exists": True}}):
            print("poll['scheduled_time']={}".format(poll['scheduled_time']))

            sched_weekday = int(poll['scheduled_time']['weekday'])
            sched_hour = int(poll['scheduled_time']['hour'])

            print("sched_weekday={}, sched_hour={}".format(sched_weekday, sched_hour))

            if cur_weekday == sched_weekday and cur_hour == sched_hour:
                print('Poll should be launched')
                print(poll)

                channel = bot.get_channel(int(poll['channel_id']))
                print("channel")
                print(channel)
                await channel.send('Hello')

                p = await Poll.load_from_db(bot, poll['server_id'], poll['short'])
                await p.post_embed(channel)
                print("Poll posted")


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

bot.run(SETTINGS.bot_token)

print(bot)