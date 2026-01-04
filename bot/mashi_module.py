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

    @app_commands.command(name="connect_wallet", description="Connect wallet")
    @app_commands.describe(wallet="Wallet")
    async def connect_wallet(self, interaction: discord.Interaction, wallet: str):
        try:
            if len(wallet) != 42:
                await interaction.response.send_message(
                    "Invalid wallet",
                    ephemeral=True
                )
                return

            has_wallet = self._mashers_dao.get_wallet(interaction.user.id) is not None
            if has_wallet:
                await interaction.response.send_message(
                    "You have wallet",
                    ephemeral=True
                )
                return

            is_another_user_wallet = self._mashers_dao.check_if_wallet_taken(wallet)
            if is_another_user_wallet:
                await interaction.response.send_message(
                    "Wallet already taken",
                    ephemeral=True
                )
                return

            self._mashers_dao.connect_wallet(interaction.user.id, wallet.lower())
            await interaction.response.send_message(
                "Wallet connected",
                ephemeral=True
            )

        except Exception as e:
            print(e)
            await interaction.response.send_message(
                "Something went wrong",
                ephemeral=True
            )

    @app_commands.command(name="disconnect_wallet", description="Disconnect wallet")
    async def disconnect_wallet(self, interaction: discord.Interaction):
        try:
            self._mashers_dao.disconnect_wallet(interaction.user.id)
            await interaction.response.send_message(
                "Wallet disconnected",
                ephemeral=True
            )

        except Exception as e:
            print(e)
            await interaction.response.send_message(
                "Something went wrong",
                ephemeral=True
            )

    @app_commands.command(name="mashi", description="Get mashup")
    @app_commands.describe(img_type="Static/Animated", mint="#Mint")
    @app_commands.choices(img_type=[
        app_commands.Choice(name="Static", value=0),
        app_commands.Choice(name="Shorter GIF", value=1),
        app_commands.Choice(name="Longer GIF", value=2)
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

                    await interaction.followup.send(embed=embed, file=file, ephemeral=False)
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
