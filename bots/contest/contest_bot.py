import discord
from discord.ext import commands


class ContestBot(commands.Bot):
    _instance = None

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        intents.message_content = True
        intents.reactions = True
        super().__init__(command_prefix="!", intents=intents)
        ContestBot._instance = self

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = ContestBot()
        return cls._instance

    async def setup_hook(self):
        await self.load_extension("bots.contest.contest_module")
        await self.tree.sync()
