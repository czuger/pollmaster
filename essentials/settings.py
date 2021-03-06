import discord

from essentials.secrets import SECRETS


class Settings:
    def __init__(self):
        self.color = discord.Colour(int('7289da', 16))
        self.title_icon = "https://i.imgur.com/vtLsAl8.jpg" #PM
        self.author_icon = "https://i.imgur.com/TYbBtwB.jpg" #tag
        self.report_icon = "https://i.imgur.com/YksGRLN.png" #report
        self.msg_errors = False
        self.log_errors = True

        self.load_secrets()

    def load_secrets(self):
        # secret
        self.dbl_token = SECRETS.dbl_token
        self.mongo_db = SECRETS.mongo_db
        self.bot_token = SECRETS.bot_token
        self.mode = SECRETS.mode
        self.owner_id = SECRETS.owner_id
        self.invite_link = SECRETS.invite_link



SETTINGS = Settings()
