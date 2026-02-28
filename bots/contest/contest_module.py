import discord
from discord import app_commands
from discord.ext import commands
import asyncio

# Assuming MASHI_BOT_ID is in your config
from configs.config import MASHI_BOT_ID


class ContestModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="contest", description="shows the top contest winner starting from a message ID")
    @app_commands.describe(msg_id="The ID of the first message to include in the contest")
    async def contest(self, interaction: discord.Interaction, msg_id: str):
        await interaction.response.defer(ephemeral=True)

        async def get_result(message: discord.Message) -> tuple[int, int]:
            try:
                # Fetch fresh state for accurate reactions
                temp_msg = await interaction.channel.fetch_message(message.id)
                metadata = temp_msg.interaction_metadata

                if not metadata:
                    return (0, 0)

                poster_id = metadata.user.id
                target_emoji = "🔥"
                reaction = discord.utils.get(temp_msg.reactions, emoji=target_emoji)

                if not reaction:
                    return (poster_id, 0)

                # Count unique users excluding the poster and the bot
                user_ids = [user.id async for user in reaction.users(limit=None)]
                count = len([uid for uid in user_ids if uid != poster_id and uid != MASHI_BOT_ID])

                return (poster_id, count)
            except Exception:
                return (0, 0)

        try:
            # 1. Permissions Check (Permissions + Owner + Specific User ID)
            SPECIFIC_USER_ID = 1167694222120468553

            is_staff = (
                    interaction.user.guild_permissions.administrator or
                    interaction.user.guild_permissions.manage_messages or
                    interaction.user.id == interaction.guild.owner_id or
                    interaction.user.id == SPECIFIC_USER_ID
            )

            if not is_staff:
                return await interaction.followup.send("Unauthorized: You do not have permission to run this command.",
                                                       ephemeral=True)

            # 2. Convert and validate msg_id
            try:
                start_id = int(msg_id)
                after_obj = discord.Object(id=start_id)
            except ValueError:
                return await interaction.followup.send("Please provide a valid numeric Message ID.", ephemeral=True)

            messages = []

            # Include the starting message (the anchor)
            try:
                anchor_msg = await interaction.channel.fetch_message(start_id)
                messages.append(anchor_msg)
            except Exception as e:
                print(e)
                return await interaction.followup.send(str(e), ephemeral=True)

            # 3. Fetch all bot messages sent AFTER the anchor
            async for msg in interaction.channel.history(limit=300, after=after_obj, oldest_first=True):
                if msg.author.id == MASHI_BOT_ID:
                    messages.append(msg)

            if not messages:
                return await interaction.followup.send("No valid bot messages found starting from that point.",
                                                       ephemeral=True)

            # 4. Process results concurrently
            tasks = [get_result(msg) for msg in messages]
            raw_results = await asyncio.gather(*tasks)

            # 5. Aggregate (One best score per user)
            user_scores = {}
            for user_id, count in raw_results:
                if user_id == 0: continue
                user_scores[user_id] = max(user_scores.get(user_id, 0), count)

            if not user_scores:
                return await interaction.followup.send("No entries with reactions were found.", ephemeral=True)

            # 6. Sorting and Winner Logic
            sorted_users = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
            top_score = sorted_users[0][1]
            winners = [f"<@{uid}>" for uid, score in sorted_users if score == top_score]

            # 7. Final Response
            if len(winners) > 1:
                result_text = f"🏆 **Tie Detected!**\nScore: 🔥 x {top_score}\nWinners: {', '.join(winners)}"
            else:
                result_text = f"🏆 **Contest Winner**\nUser: {winners[0]}\nScore: 🔥 x {top_score}"

            await interaction.followup.send(result_text, ephemeral=True)

        except Exception as e:
            print(f"Error in contest command: {e}")
            await interaction.followup.send("An unexpected error occurred while processing the contest.",
                                            ephemeral=True)


async def setup(bot):
    await bot.add_cog(ContestModule(bot))