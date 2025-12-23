import io
from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands

from config.config import TEST_CHANNEL_ID
from data.db.daos.mashers_dao import MashersDao
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

            is_another_user_wallet = self._mashers_dao.get_user_by_wallet(wallet) is not None
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
    @app_commands.describe(mint="#Mint")
    async def mashi(self, interaction: discord.Interaction, mint: int | None = None):
        try:
            await interaction.response.defer(ephemeral=False)

            id = interaction.user.id
            wallet = self._mashers_dao.get_wallet(id)
            if wallet:
                data = await self._mashi_repo.get_composite(wallet, mint)
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
                    file = discord.File(fp=buffer, filename="composite.png")

                    embed = discord.Embed(title=f"{interaction.user.display_name}'s Mashi", color=discord.Color.green())
                    embed.set_image(url="attachment://composite.png")

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

    @app_commands.command(name="animated_mashi", description="Get animated mashup")
    @app_commands.choices(type=[
        app_commands.Choice(name="GIF", value=0),
        app_commands.Choice(name="WEBP", value=1),
    ])
    async def animated_mashi(self, interaction: discord.Interaction, type: int = 0):
        try:
            await interaction.response.defer(ephemeral=False)

            id = interaction.user.id
            wallet = self._mashers_dao.get_wallet(id)
            if wallet:
                data = await self._mashi_repo.get_composite(wallet, is_animated=True, img_type=type)
                if data:
                    if not isinstance(data, (bytes, io.BytesIO)):
                        msg = getattr(data, 'error_msg', "Unknown error")
                        await interaction.followup.send(msg, ephemeral=True)
                        return

                    buffer = io.BytesIO(data)
                    buffer.seek(0)

                    file_ext = "gif" if type == 0 else "webp"
                    file = discord.File(fp=buffer, filename=f"mashi_composite.{file_ext}")
                    embed = discord.Embed(
                        title=f"{interaction.user.display_name}'s Mashi",
                        color=discord.Color.green()
                    )
                    embed.set_image(url=f"attachment://mashi_composite.{file_ext}")

                    await interaction.followup.send(embed=embed, file=file)
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

    @app_commands.command(name="test_mashi", description="Get test mashup")
    @app_commands.choices(type=[
        app_commands.Choice(name="GIF", value=0),
        app_commands.Choice(name="WEBP", value=1),
    ])
    async def test_mashi(self, interaction: discord.Interaction, type: int = 0):
        try:

            await interaction.response.defer(ephemeral=False)

            id = interaction.user.id
            wallet = self._mashers_dao.get_wallet(id)
            if wallet:
                data = await self._mashi_repo.get_composite(wallet, is_animated=True, img_type=type, is_test = True)
                if data:
                    if not isinstance(data, (bytes, io.BytesIO)):
                        msg = getattr(data, 'error_msg', "Unknown error")
                        await interaction.followup.send(msg, ephemeral=True)
                        return

                    buffer = io.BytesIO(data)
                    buffer.seek(0)

                    file_ext = "gif" if type == 0 else "webp"
                    file = discord.File(fp=buffer, filename=f"mashi_composite.{file_ext}")
                    embed = discord.Embed(
                        title=f"{interaction.user.display_name}'s Mashi",
                        color=discord.Color.green()
                    )
                    embed.set_image(url=f"attachment://mashi_composite.{file_ext}")

                    await interaction.followup.send(embed=embed, file=file)
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
