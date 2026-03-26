from io import BytesIO
import discord
from discord import app_commands
from discord.ext import commands
from balancer.balancer import Balancer
from bots.mashi.views.leaderboard_view import LeaderboardView
from configs.config import TEST_CHANNEL_ID
from data.postgres.daos.user_dao import UserDao
from data.postgres.daos.reactions_dao import ReactionsDao
from data.remote.mashi_api import MashiApi
from data.postgres.daos.tracking_dao import TrackingDao


class MashiModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self._reactions_dao = ReactionsDao()







    @app_commands.command(name="leaderboard", description="Top users by received 🔥")
    async def leaderboard(self, interaction: discord.Interaction):
        try:
            view = LeaderboardView(bot=self.bot)
            embed = await view.create_embed()
            await interaction.response.send_message(embed=embed, view=view)
        except Exception as e:
            print(e)

    @app_commands.command(name="reactions_received", description="🔥 received")
    async def reactions_received(self, interaction: discord.Interaction):
        reactions_count = self._reactions_dao.get_reaction_count(interaction.user.id)
        await interaction.response.send_message(
            f"You got 🔥 x {reactions_count}, and are a lovely member of our community!")


async def setup(bot):
    await bot.add_cog(MashiModule(bot))
