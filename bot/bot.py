import asyncio

import discord
from discord.ext import commands
from bot.message_module import get_notify_embed
from configs.config import RELEASES_CHANNEL_ID, TEST_CHANNEL_ID, NEW_RELEASES_ROLE_ID, APPROVALS_ROLE_ID, \
    APPROVALS_CHANNEL_ID
from data.postgres.daos.reactions_dao import ReactionsDao
from services import caching_service
from services.caching_service import CachingService


class MashiBot(commands.Bot):
    _instance = None

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        intents.reactions = True
        super().__init__(command_prefix="!", intents=intents)
        self._reactions_dao = ReactionsDao()
        MashiBot._instance = self

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = MashiBot()
        return cls._instance

    async def notify(self, data: dict, is_release: bool = True):
        try:
            if not data:
                return

            embed = get_notify_embed(data, is_release=is_release)

            if is_release:
                channel = await self.instance().fetch_channel(RELEASES_CHANNEL_ID)
            else:
                channel = await self.instance().fetch_channel(APPROVALS_CHANNEL_ID)

            all_roles = await channel.guild.fetch_roles()
            if is_release:
                role = discord.utils.get(all_roles, id=int(NEW_RELEASES_ROLE_ID))
            else:
                role = discord.utils.get(all_roles, id=int(APPROVALS_ROLE_ID))

            if role is None:
                return

            await channel.send(f"{role.mention}", embed=embed, allowed_mentions=discord.AllowedMentions(roles=True))

            await CachingService.instance().fetch_and_cache_item(data['docId'])
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
                self._reactions_dao.update_reaction_count(poster_id, 1)
                total_count = self._reactions_dao.get_reaction_count(poster_id)

                if total_count > 0 and total_count % 25 == 0:
                    mention = f"<@{poster_id}>"
                    await channel.send(f"🔥! {mention} just hit {total_count} reactions!")

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
                self._reactions_dao.update_reaction_count(poster_id, -1)

        except (discord.NotFound, discord.Forbidden):
            pass

    async def setup_hook(self):
        await self.load_extension("bot.mashi_module")
        await self.tree.sync()
