import discord
from discord import app_commands
from discord.ext import commands
import asyncio

from configs.config import MASHI_BOT_ID


class ContestModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="contest", description="shows the top contest winner")
    async def contest(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async def get_result(message: discord.Message) -> tuple[int, int]:
            try:
                # Fetch fresh state to get interaction_metadata and accurate reactions
                temp_msg = await interaction.channel.fetch_message(message.id)
                metadata = temp_msg.interaction_metadata

                if not metadata:
                    return (0, 0)

                poster_id = metadata.user.id
                target_emoji = "🔥"
                reaction = discord.utils.get(temp_msg.reactions, emoji=target_emoji)

                if not reaction:
                    return (poster_id, 0)

                # Count unique users excluding the author and the bot
                user_ids = [user.id async for user in reaction.users(limit=None)]
                count = len([uid for uid in user_ids if uid != poster_id and uid != MASHI_BOT_ID])

                return (poster_id, count)
            except Exception:
                return (0, 0)

        try:
            # 1. Permissions Check
            is_staff = (
                    interaction.user.guild_permissions.administrator or
                    interaction.user.guild_permissions.manage_messages
            )

            if not is_staff:
                return await interaction.followup.send("Unauthorized access", ephemeral=True)

            # 2. Search for messages sent by the specific BOT_ID
            messages = [
                msg async for msg in interaction.channel.history(limit=150)
                if msg.author.id == MASHI_BOT_ID
            ]

            if not messages:
                return await interaction.followup.send("No bot messages found in history.", ephemeral=True)

            # 3. Gather results concurrently
            tasks = [get_result(msg) for msg in messages]
            raw_results = await asyncio.gather(*tasks)

            # 4. Aggregate Scores (Highest Single Post per User)
            user_scores = {}
            for user_id, count in raw_results:
                if user_id == 0: continue
                # Update if this post has a higher score than previously recorded for this user
                user_scores[user_id] = max(user_scores.get(user_id, 0), count)

            if not user_scores:
                return await interaction.followup.send("No valid entries with reactions detected.", ephemeral=True)

            # 5. Sort and get the Top Winner
            sorted_users = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)

            # 6. Formatting the result for 1 winner
            top_user_id, top_score = sorted_users[0]

            # Check for ties at the #1 spot
            ties = [f"<@{uid}>" for uid, score in sorted_users if score == top_score]

            if len(ties) > 1:
                result_text = f"🏆 **It's a Tie!**\nScore: 🔥 x {top_score}\nWinners: {', '.join(ties)}"
            else:
                result_text = f"🏆 **Contest Winner**\nUser: <@{top_user_id}>\nScore: 🔥 x {top_score}"

            await interaction.followup.send(result_text, ephemeral=True)

        except Exception as e:
            print(f"General error: {e}")
            await interaction.followup.send("An error occurred while calculating the results.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ContestModule(bot))