import discord
from discord.ext import commands

from bot.message_module import get_notify_embed
from configs.config import RELEASES_CHANNEL_ID, TEST_CHANNEL_ID, NEW_RELEASES_ROLE_ID
from data.firebase.tracking_dao import TrackingDao


class MashiBot(commands.Bot):
    _instance = None

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        intents.reactions = True
        super().__init__(command_prefix="!", intents=intents)
        self._tracking_dao = TrackingDao()
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

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        try:
            # 1. Ignore reactions added by the bot itself (to avoid loops)
            if payload.user_id == self.user.id:
                return

            # 2. Get the channel
            channel = self.get_channel(payload.channel_id)
            if not channel:
                # If the channel isn't in cache, we fetch it
                channel = await self.fetch_channel(payload.channel_id)

            # 3. Fetch the actual message to check the author
            try:
                message = await channel.fetch_message(payload.message_id)
            except discord.NotFound:
                return  # Message was deleted

            # 4. Check if the message was sent by a bot
            if not message.author.bot:
                return  # Ignore reactions on messages sent by regular users

            # 5. (Optional) Check if it was sent by YOUR bot specifically
            if message.author.id != self.user.id:
                return  # Ignore reactions on other bots' messages

            # Example Logic: Only run if it's a bot message and specific emoji
            if str(payload.emoji) == "🔥":
                footer = message.embeds[0].footer
                if not footer or not footer.text:
                    return

                metadata = message.interaction_metadata
                poster = metadata.user
                poster_id = poster.id

                if poster_id == payload.user_id:
                    return

                self._tracking_dao.update_tracking(msg_id=message.id, poster_id=poster_id, user_id=payload.user_id)

        except Exception as e:
            print(e)
            channel = self.instance().get_channel(TEST_CHANNEL_ID)
            await channel.send(f"Reaction: {e}")


    async def setup_hook(self):
        await self.load_extension("bot.mashi_module")
        await self.tree.sync()
