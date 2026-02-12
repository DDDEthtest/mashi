from io import BytesIO
import discord
from discord import app_commands
from discord.ext import commands
from balancer.balancer import Balancer
from bot.views.leaderboard_view import LeaderboardView
from configs.config import TEST_CHANNEL_ID
from data.firebase.mashers_dao import MashersDao
from data.firebase.reactions_dao import ReactionsDao
from data.remote.mashi_api import MashiApi
from data.firebase.tracking_dao import TrackingDao


class MashiModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._mashers_dao = MashersDao()
        self._tracking_dao = TrackingDao()
        self._reactions_dao = ReactionsDao()
        _mashi_api = MashiApi()

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

    @app_commands.command(name="mashi", description="Generates mashup")
    @app_commands.describe(img_type="Static/Animated")
    @app_commands.choices(img_type=[
        app_commands.Choice(name="PNG", value=0),
        app_commands.Choice(name="GIF", value=1),
    ])
    async def mashi(self, interaction: discord.Interaction, img_type: int = 0):
        msg = None

        try:
            await interaction.response.defer(ephemeral=False)

            id = interaction.user.id

            wallet = self._mashers_dao.get_wallet(id)
            if wallet:
                if img_type == 0:
                    ext = ".png"
                else:
                    ext = ".gif"

                data = await Balancer.instance().get_composite(wallet, img_type=img_type)
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

                    # view = Button(author=interaction.user)

                    buffer = BytesIO(data)
                    file = discord.File(fp=buffer, filename=f"composite{ext}")

                    color = discord.Color.random()

                    embed = discord.Embed(title=f"{interaction.user.display_name}'s mashup", color=color)
                    embed.set_image(url=f"attachment://composite{ext}")
                    embed.set_footer(text="© 2026 mash-it")

                    msg = await interaction.followup.send(embed=embed, file=file, ephemeral=False)
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

        finally:
            if msg:
                try:
                    self._tracking_dao.insert_mashup(msg_id=msg.id, channel_id=msg.channel.id)
                    await msg.add_reaction("🔥")
                except Exception as e:
                    print(e)
                    pass

    @app_commands.command(name="delete_mashup", description="Deletes mashup")
    @app_commands.describe(msg_id="Message id on right click")
    async def delete_mashup(self, interaction: discord.Interaction, msg_id: str):
        try:
            await interaction.response.defer(ephemeral=True)

            message = await interaction.channel.fetch_message(int(msg_id))
            metadata = message.interaction_metadata
            user = metadata.user
            user_id = user.id

            is_staff = interaction.user.guild_permissions.administrator or \
                       interaction.user.guild_permissions.manage_messages

            if user_id == interaction.user.id or is_staff:
                await message.delete()
                await interaction.followup.send("Mashup was deleted", ephemeral=True)
                self._tracking_dao.delete_mashup(message.id)
                return

            await interaction.followup.send(
                "You are not allowed to delete that mashup",
                ephemeral=True
            )
            return

        except Exception as e:
            print(e)
            await interaction.followup.send(
                "Something went wrong",
                ephemeral=True
            )

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
        await interaction.response.send_message(f"You got 🔥 x {reactions_count}, and are a lovely member of our community!")


async def setup(bot):
    await bot.add_cog(MashiModule(bot))
