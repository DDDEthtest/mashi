import asyncio
from io import BytesIO
import discord
from discord import app_commands
from discord.ext import commands
from pyasn1_modules.rfc3280 import ub_serial_number

from balancer.balancer import Balancer
from bot.views.leaderboard_view import LeaderboardView
from configs.config import TEST_CHANNEL_ID
from data.postgres.daos.user_dao import UserDao
from data.postgres.daos.reactions_dao import ReactionsDao
from data.remote.mashi_api import MashiApi
from data.postgres.daos.tracking_dao import TrackingDao


class MashiModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._user_dao = UserDao()
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

            has_wallet = self._user_dao.get_wallet(interaction.user.id) is not None
            if has_wallet:
                await interaction.response.send_message(
                    "You have wallet",
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

            wallet = self._user_dao.get_wallet(id)
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

    @app_commands.command(name="gif", description="Generates gif")
    @app_commands.describe(is_higher_res="2x res", is_longer="2x length", is_smoother="2x fps", playback_speed="playback speed")
    @app_commands.choices(
        is_higher_res=[
            app_commands.Choice(name="YES", value=1),
            app_commands.Choice(name="NO", value=0),
        ],
        is_longer=[
            app_commands.Choice(name="YES", value=1),
            app_commands.Choice(name="NO", value=0),
        ],
        is_smoother=[
            app_commands.Choice(name="YES", value=1),
            app_commands.Choice(name="NO", value=0),
        ],
        playback_speed=[
            app_commands.Choice(name="NORMAL", value=0),
            app_commands.Choice(name="FASTER", value=1),
            app_commands.Choice(name="SLOWER", value=-1),
        ]
    )
    async def gif(self, interaction: discord.Interaction, is_higher_res: int = 0, is_longer: int = 0,
                         is_smoother: int = 0, playback_speed: int = 0):
        msg = None

        try:
            await interaction.response.defer(ephemeral=False)

            id = interaction.user.id

            wallet = self._user_dao.get_wallet(id)
            if wallet:
                ext = ".gif"

                data = await Balancer.instance().get_composite(wallet, img_type=1, is_higher_res = bool(is_higher_res), is_longer = bool(is_longer),
                         is_smoother = bool(is_smoother), playback_speed = playback_speed)
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
                       interaction.user.guild_permissions.manage_messagesor or \
                       interaction.user.id == 1167694222120468553

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
        await interaction.response.send_message(
            f"You got 🔥 x {reactions_count}, and are a lovely member of our community!")

    @app_commands.command(name="contest", description="shows contest progress")
    @app_commands.describe(
        winners_count="Winners count",
        is_all_sum="True - sum of all post reactions"
    )
    @app_commands.choices(is_all_sum=[
        app_commands.Choice(name="FALSE", value=0),
        app_commands.Choice(name="TRUE", value=1),
    ])
    async def contest(
            self,
            interaction: discord.Interaction,
            winners_count: int,
            is_all_sum: int = 0  # Default to 0 (Highest Single Post)
    ):
        await interaction.response.defer(ephemeral=True)

        BOT_ID = 1428847584965034154

        async def get_result(message: discord.Message) -> tuple[int, int]:
            """Processes a message to return (user_id, reaction_count)."""
            try:
                # Refresh message state to get accurate reaction counts
                temp_msg = await interaction.channel.fetch_message(message.id)
                metadata = temp_msg.interaction_metadata
                if not metadata:
                    return (0, 0)

                poster_id = metadata.user.id
                target_emoji = "🔥"
                reaction = discord.utils.get(temp_msg.reactions, emoji=target_emoji)

                if not reaction:
                    return (poster_id, 0)

                # Get user IDs who reacted
                user_ids = [user.id async for user in reaction.users(limit=None)]

                # Count valid reactions (exclude author and the bot)
                count = len([
                    uid for uid in user_ids
                    if uid != poster_id and uid != BOT_ID
                ])

                return (poster_id, count)
            except Exception:
                return (0, 0)

        try:
            # 1. Permissions Check
            is_staff = interaction.user.guild_permissions.administrator or \
                       interaction.user.guild_permissions.manage_messages or \
                       interaction.user.id == 1167694222120468553

            if not is_staff:
                return await interaction.followup.send("Unauthorized access", ephemeral=True)

            # 2. Identify bot-sent contest entries (limit search to 150 messages)
            messages = [msg async for msg in interaction.channel.history(limit=150) if msg.author.id == BOT_ID]

            # 3. Gather results concurrently
            tasks = [get_result(msg) for msg in messages]
            raw_results = await asyncio.gather(*tasks)

            # 4. Aggregate Scores by User
            # Key: user_id, Value: score
            user_scores = {}
            for user_id, count in raw_results:
                if user_id == 0:
                    continue

                if is_all_sum == 1:  # Sum of All Posts
                    user_scores[user_id] = user_scores.get(user_id, 0) + count
                else:  # 0: Highest Single Post
                    user_scores[user_id] = max(user_scores.get(user_id, 0), count)

            # 5. Sort by score descending
            sorted_users = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)

            if not sorted_users:
                return await interaction.followup.send("No valid entries detected.", ephemeral=True)

            # 6. Top N Unique Users + Ties for the last spot
            winners = []
            unique_count = 0
            for user_id, count in sorted_users:
                if unique_count < winners_count:
                    winners.append((user_id, count))
                    unique_count += 1
                elif winners and count == winners[-1][1]:
                    winners.append((user_id, count))
                else:
                    break

            # 7. Formatting the Leaderboard
            leaderboard_msg = f"🏆\n"

            for i, (user_id, count) in enumerate(winners):
                leaderboard_msg += f"{i + 1}. <@{user_id}> : 🔥 x {count}\n"

            await interaction.followup.send(leaderboard_msg, ephemeral=True)

        except Exception as e:
            print(f"General error: {e}")
            await interaction.followup.send("Something went wrong", ephemeral=True)

    @app_commands.command(name="contest_public", description="Shows the current contest leaderboard")
    @app_commands.describe(
        limit="How many top posts to show"
    )
    async def contest_public(
            self,
            interaction: discord.Interaction,
            limit: int = 10
    ):
        # Publicly visible: ephemeral=False (default)
        await interaction.response.defer(ephemeral=False)

        BOT_ID = 1428847584965034154

        async def get_entry_data(message: discord.Message):
            """Processes a message and returns specific post details."""
            try:
                # Refresh to get current reactions
                temp_msg = await interaction.channel.fetch_message(message.id)
                metadata = temp_msg.interaction_metadata

                if not metadata:
                    return None

                poster_id = metadata.user.id
                target_emoji = "🔥"
                reaction = discord.utils.get(temp_msg.reactions, emoji=target_emoji)

                if not reaction:
                    count = 0
                else:
                    user_ids = [user.id async for user in reaction.users(limit=None)]
                    # Filter out the author and the bot from the count
                    count = len([uid for uid in user_ids if uid != poster_id and uid != BOT_ID])

                return {
                    "user_id": poster_id,
                    "count": count,
                    "url": temp_msg.jump_url
                }
            except Exception:
                return None

        try:
            # Search the last 200 messages for bot-sent entries
            messages = [msg async for msg in interaction.channel.history(limit=200) if msg.author.id == BOT_ID]

            # Gather data for every post individually
            tasks = [get_entry_data(msg) for msg in messages]
            raw_results = await asyncio.gather(*tasks)

            # Filter out None results and sort by reaction count
            valid_entries = [res for res in raw_results if res is not None]
            sorted_entries = sorted(valid_entries, key=lambda x: x['count'], reverse=True)

            if not sorted_entries:
                return await interaction.followup.send("No contest entries found in recent history.")

            # Build the leaderboard message
            leaderboard_msg = "## 🏆 Contest Leaderboard\n"

            # Take the top N entries (plus ties for the last spot)
            display_list = sorted_entries[:limit]

            for i, entry in enumerate(display_list):
                user_mention = f"<@{entry['user_id']}>"
                leaderboard_msg += f"{i + 1}. {user_mention}: 🔥 x {entry['count']} - [View Post]({entry['url']})\n"

            await interaction.followup.send(leaderboard_msg)

        except Exception as e:
            print(f"Leaderboard error: {e}")
            await interaction.followup.send("An error occurred while fetching the leaderboard.")


async def setup(bot):
    await bot.add_cog(MashiModule(bot))
