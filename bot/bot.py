import discord
from discord.ext import commands


class MashiBot(commands.Bot):
    _instance = None

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)
        MashiBot._instance = self

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = MashiBot()
        return cls._instance

    async def setup_hook(self):
        await self.load_extension("bot.mashi_module")
        await self.tree.sync()
