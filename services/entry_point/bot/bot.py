import discord
from discord.ext import commands

from bot.message_module import get_notify_embed
from configs.config import RELEASES_CHANNEL_ID, TEST_CHANNEL_ID, NEW_RELEASES_ROLE_ID
from data.firebase.mashers_dao import MashersDao


class MashiBot(commands.Bot):
    _instance = None

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        intents.reactions = True
        super().__init__(command_prefix="!", intents=intents)
        self._mashers_dao = MashersDao()
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

    def _get_poster_id_from_message(self, message: discord.Message) -> int | None:
        # Priority 1: Interaction Metadata
        if message.interaction_metadata:
            return message.interaction_metadata.user.id

        # Priority 2: Embed Footer Fallback
        if message.embeds and message.embeds[0].footer:
            footer_text = message.embeds[0].footer.text
            try:
                # Assuming footer format is "User ID: 123456789"
                # We split by colon and take the last part
                return int(footer_text.split(':')[-1].strip())
            except (ValueError, IndexError):
                return None

        return None

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "🔥" or payload.user_id == self.user.id:
            return

        try:
            channel = self.get_channel(payload.channel_id) or await self.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            if not message.author.bot or message.author.id != self.user.id:
                return

            poster_id = self._get_poster_id_from_message(message)

            if poster_id and poster_id != payload.user_id:
                self._mashers_dao.update_reaction_count(poster_id, 1)

        except (discord.NotFound, discord.Forbidden):
            pass

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "🔥" or payload.user_id == self.user.id:
            return

        try:
            channel = self.get_channel(payload.channel_id) or await self.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            if not message.author.bot or message.author.id != self.user.id:
                return

            poster_id = self._get_poster_id_from_message(message)

            if poster_id and poster_id != payload.user_id:
                # Note: Your DAO transaction logic ensures this never goes below 0
                self._mashers_dao.update_reaction_count(poster_id, -1)

        except (discord.NotFound, discord.Forbidden):
            pass


    async def setup_hook(self):
        await self.load_extension("bot.mashi_module")
        await self.tree.sync()
