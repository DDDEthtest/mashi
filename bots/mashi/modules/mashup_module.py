from io import BytesIO
import discord
from discord import app_commands
from discord.ext import commands
from balancer.balancer import request_composite_async
from configs.bot_config import TEST_CHANNEL_ID
from data.models.download_type import DownloadType
from data.postgres.daos.tracking_dao import TrackingDao
from data.postgres.daos.user_dao import UserDao


class MashupModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._user_dao = UserDao()
        self._tracking_dao = TrackingDao()

    @app_commands.command(name="mashi", description="Generates mashup")
    @app_commands.describe(image="Image type")
    @app_commands.choices(image=[
        app_commands.Choice(name="PNG", value="PNG"),
        app_commands.Choice(name="GIF", value="GIF"),
    ])
    async def mashi(self, interaction: discord.Interaction, image: str = "PNG"):
        msg = None

        try:
            await interaction.response.defer(ephemeral=False)

            user_id = interaction.user.id
            wallet = self._user_dao.get_wallet(user_id)
            if wallet:
                download_type = DownloadType[image]
                if download_type is DownloadType.PNG:
                    ext = ".png"
                else:
                    ext = ".gif"

                data = await request_composite_async(wallet=wallet, download_type=download_type)
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

                    color = discord.Color.random()
                    embed = discord.Embed(title=f"{interaction.user.display_name}'s mashup", color=color)
                    embed.set_image(url=f"attachment://composite{ext}")
                    embed.set_footer(text="© 2026 mash-it")

                    msg = await interaction.followup.send(embed=embed, file=file, ephemeral=False)
                    return

            await interaction.followup.send(
                f"use /connect_wallet command",
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
    async def delete_mashup_async(self, interaction: discord.Interaction, msg_id: str):
        try:
            await interaction.response.defer(ephemeral=True)

            message = await interaction.channel.fetch_message(int(msg_id))
            metadata = message.interaction_metadata
            user = metadata.user
            user_id = user.id

            is_staff = (
                    interaction.user.guild_permissions.administrator or
                    interaction.user.guild_permissions.manage_messages or
                    interaction.user.id == interaction.guild.owner_id
            )

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


async def setup(bot):
    await bot.add_cog(MashupModule(bot))
