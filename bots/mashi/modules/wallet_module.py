import discord
from discord import app_commands
from discord.ext import commands

from data.postgres.daos.user_dao import UserDao


class WalletModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._user_dao = UserDao()

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

            has_wallet = self._user_dao.get_wallet(interaction.user.id) is not None
            if has_wallet:
                await interaction.response.send_message(
                    "You already have wallet",
                    ephemeral=True
                )
                return

            is_another_user_wallet = self._user_dao.check_if_wallet_taken(wallet)
            if is_another_user_wallet:
                await interaction.response.send_message(
                    "Wallet already taken",
                    ephemeral=True
                )
                return

            self._user_dao.connect_wallet(interaction.user.id, wallet.lower())
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
            self._user_dao.disconnect_wallet(interaction.user.id)
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

async def setup(bot):
    await bot.add_cog(WalletModule(bot))