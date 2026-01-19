import discord
from discord.ext import commands

from bot.message_module import get_notify_embed
from configs.config import RELEASES_CHANNEL_ID, TEST_CHANNEL_ID, NEW_RELEASES_ROLE_ID


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

    async def notify(self, data: dict):
        try:
            if not data:
                return

            embed = get_notify_embed(data)

            channel = self.instance().get_channel(RELEASES_CHANNEL_ID)
            if not channel:
                channel = await self.instance().fetch_channel(RELEASES_CHANNEL_ID)

            role = channel.guild.get_role(NEW_RELEASES_ROLE_ID)
            if role is None:
                all_roles = await channel.guild.fetch_roles()
                role = discord.utils.get(all_roles, id=int(NEW_RELEASES_ROLE_ID))

            await channel.send(f"{role.mention}", embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))
        except Exception as e:
            print(e)
            channel = self.instance().get_channel(TEST_CHANNEL_ID)
            await channel.send(f"Notify: {e} for {data}")

    async def setup_hook(self):
        await self.load_extension("bot.mashi_module")
        await self.tree.sync()
