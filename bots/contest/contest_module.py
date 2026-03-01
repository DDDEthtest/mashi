import asyncio
from collections import defaultdict
from typing import List, Dict, Optional, Any

import discord
from discord import app_commands
from discord.ext import commands

from configs.config import MASHI_BOT_ID
from data.postgres.daos.content_dao import ContestDao


class ContestModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.contest_dao = ContestDao()
        self.staff_id = 1167694222120468553

    def _is_staff(self, interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.manage_messages or interaction.user.id == self.staff_id

    async def _process_entry(self, message: discord.Message) -> Optional[Dict[str, Any]]:
        """Processes a single message. Only counts if sent by MASHI_BOT_ID."""
        try:
            # Only process messages actually sent by the bot
            if message.author.id != MASHI_BOT_ID:
                return None

            # Refresh for current reaction state
            msg = await message.channel.fetch_message(message.id)
            metadata = msg.interaction_metadata

            # Identify the actual participant (from metadata or author)
            poster_id = metadata.user.id if metadata else msg.author.id

            reaction = discord.utils.get(msg.reactions, emoji="🔥")
            count = 0
            if reaction:
                u_ids = [u.id async for u in reaction.users(limit=None)]
                # Filter out the bot and the poster from the final count
                count = len([uid for uid in u_ids if uid != poster_id and uid != MASHI_BOT_ID])

            return {
                "user_id": poster_id,
                "count": count,
                "url": msg.jump_url
            }
        except Exception as e:
            print(f"[Internal] Error processing {message.id}: {e}")
            return None

    async def _get_contest_data(self, channel: discord.TextChannel, anchor_id: int) -> List[Dict[str, Any]]:
        """Fetches anchor + history. The anchor is only added to the process list if it's a bot message."""
        messages = []
        try:
            # 1. Fetch the Anchor message
            anchor = await channel.fetch_message(anchor_id)
            # Only add to the list if the bot sent it
            if anchor.author.id == MASHI_BOT_ID:
                messages.append(anchor)

            # 2. Fetch History After Anchor (bot messages only)
            async for msg in channel.history(limit=300, after=discord.Object(id=anchor_id), oldest_first=True):
                if msg.author.id == MASHI_BOT_ID:
                    messages.append(msg)
        except discord.NotFound:
            return []

        # Process all gathered bot messages in parallel
        tasks = [self._process_entry(m) for m in messages]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r]

    @app_commands.command(name="entry_point", description="Sets the contest anchor")
    async def entry_point(self, interaction: discord.Interaction, msg_id: str):
        await interaction.response.defer(ephemeral=True)
        try:
            if not self._is_staff(interaction):
                return await interaction.followup.send("❌ Unauthorized.", ephemeral=True)

            tid = int(msg_id)
            await interaction.channel.fetch_message(tid)
            self.contest_dao.init(msg_id=tid)
            await interaction.followup.send(f"✅ Entry point set to `{tid}`", ephemeral=True)
        except Exception as e:
            print(f"Entry Error: {e}")
            await interaction.followup.send("Something went wrong", ephemeral=True)

    @app_commands.command(name="ongoing", description="Shows top 3 score tiers")
    async def ongoing(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        try:
            aid = self.contest_dao.get_contest_id()
            if not aid: return await interaction.followup.send("❌ No active contest.")

            data = await self._get_contest_data(interaction.channel, aid)
            if not data: return await interaction.followup.send("⚠️ No valid bot entries found.")

            groups = defaultdict(list)
            for r in data:
                groups[r['count']].append(f"<@{r['user_id']}> — [View Post]({r['url']})")

            scores = sorted(groups.keys(), reverse=True)
            embed = discord.Embed(title="🏆 Contest Leaderboard", color=0xFF4500)
            medals = ["🥇 1st Place", "🥈 2nd Place", "🥉 3rd Place"]

            for i, label in enumerate(medals):
                if i < len(scores):
                    s = scores[i]
                    embed.add_field(name=label, value=f"**{s} 🔥**\n" + "\n".join(groups[s]), inline=False)
                else:
                    embed.add_field(name=label, value="*Empty*", inline=False)

            await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"Ongoing Error: {e}");
            await interaction.followup.send("Something went wrong")

    @app_commands.command(name="winner", description="Declares the winner(s)")
    async def winner(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            if not self._is_staff(interaction): return await interaction.followup.send("❌ Unauthorized.",
                                                                                       ephemeral=True)
            aid = self.contest_dao.get_contest_id()
            if not aid: return await interaction.followup.send("❌ No active contest.")

            data = await self._get_contest_data(interaction.channel, aid)
            if not data: return await interaction.followup.send("No entries found.")

            scores = {}
            for r in data:
                scores[r['user_id']] = max(scores.get(r['user_id'], 0), r['count'])

            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            top = sorted_scores[0][1]
            winners = [f"<@{uid}>" for uid, s in sorted_scores if s == top]

            await interaction.followup.send(f"🏆 **Winner(s)** (Score: {top} 🔥)\n{', '.join(winners)}")
        except Exception as e:
            print(f"Winner Error: {e}");
            await interaction.followup.send("Something went wrong", ephemeral=True)

    @app_commands.command(name="finish", description="Reset contest")
    async def finish(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            if not self._is_staff(interaction): return await interaction.followup.send("❌ Unauthorized.",
                                                                                       ephemeral=True)
            self.contest_dao.reset()
            await interaction.followup.send("✅ Reset complete.", ephemeral=True)
        except Exception as e:
            print(e);
            await interaction.followup.send("Something went wrong", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ContestModule(bot))