import json
import sys
import traceback
import aiohttp
import discord
import logging
import datetime

from essentials.messagecache import MessageCache
from discord.ext import commands
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from essentials.multi_server import get_pre
from essentials.settings import SETTINGS
from utils.poll_schedule import start_scheduled_polls_loop

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

    start_scheduled_polls_loop(bot)

    print("Servers verified. Bot running.")


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
