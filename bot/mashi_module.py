from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands

from configs.config import TEST_CHANNEL_ID
from data.firebase.mashers_dao import MashersDao
from data.remote.mashi_api import MashiApi
from data.repos.mashi_repo import MashiRepo


class MashiModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._mashers_dao = MashersDao()
        _mashi_api = MashiApi()
        self._mashi_repo = MashiRepo.instance()

    @app_commands.command(name="better_mashi", description="Get mashup")
    @app_commands.describe(img_type="Static/Animated")
    @app_commands.choices(img_type=[
        app_commands.Choice(name="Static", value=0),
        app_commands.Choice(name="GIF", value=1),
    ])
    async def mashi(self, interaction: discord.Interaction, img_type: int = 0, mint: int | None = None):
        try:
            await interaction.response.defer(ephemeral=False)

            id = interaction.user.id
            wallet = self._mashers_dao.get_wallet(id)
            if wallet:
                if img_type == 0:
                    ext = ".png"
                else:
                    ext = ".gif"

                data = await self._mashi_repo.get_composite(wallet, img_type=img_type, mint=mint)
                if data:
                    if type(data) is not bytes:
                        msg = data.error_msg
                        msg_data = data.data

                        if msg_data:
                            channel = await interaction.guild.fetch_channel(TEST_CHANNEL_ID)
                            await channel.send(data)

                        await interaction.followup.send(
                            msg,
                            ephemeral=True
                        )
                        return

                    buffer = BytesIO(data)
                    file = discord.File(fp=buffer, filename=f"composite{ext}")

                    embed = discord.Embed(title=f"{interaction.user.display_name}'s Mashi", color=discord.Color.green())
                    embed.set_image(url=f"attachment://composite{ext}")

                    await interaction.followup.send(content=interaction.user.mention, embed=embed, file=file, ephemeral=False)
                    return

            await interaction.followup.send(
                f"/connect_wallet command",
                ephemeral=True
            )

        except Exception as e:
            channel = await interaction.guild.fetch_channel(TEST_CHANNEL_ID)
            await channel.send(f"/mashi: {e}")
            await interaction.followup.send(
                "Something went wrong",
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(MashiModule(bot))
