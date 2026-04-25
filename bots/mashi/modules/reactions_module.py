import discord
from discord import app_commands
from discord.ext import commands
from bots.mashi.views.leaderboard_view import LeaderboardView
from data.postgres.daos.reactions_dao import ReactionsDao


class ReactionsModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._reactions_dao = ReactionsDao()

    @app_commands.command(name="leaderboard", description="Top users by 🔥 received")
    async def get_leaderboard_async(self, interaction: discord.Interaction):
        try:
            view = LeaderboardView(bot=self.bot)
            embed = await view.create_embed()
            await interaction.response.send_message(embed=embed, view=view)
        except Exception as e:
            print(e)

    @app_commands.command(name="reactions_received", description="🔥 received")
    async def reactions_received_async(self, interaction: discord.Interaction):
        reactions_count = self._reactions_dao.get_reaction_count(interaction.user.id)
        await interaction.response.send_message(
            f"You got 🔥 x {reactions_count}, and are a lovely member of our community!")

async def setup(bot):
    await bot.add_cog(ReactionsModule(bot))
