import discord
from data.firebase.reactions_dao import ReactionsDao


class LeaderboardView(discord.ui.View):
    def __init__(self, bot: discord.Client, page: int = 1):
        super().__init__(timeout=None)
        self.bot = bot
        self._reactions_dao = ReactionsDao()
        self.page = page
        self.per_page = 10

    async def create_embed(self):
        try:
            offset = (self.page - 1) * self.per_page
            # Fetch per_page + 1 to check if another page exists
            data = self._reactions_dao.get_reaction_leaderboard(limit=self.per_page + 1, offset=offset)

            has_next = len(data) > self.per_page
            display_data = data[:self.per_page]

            embed = discord.Embed(
                title="Leaderboard",
                color=discord.Color.green()
            )

            description_lines = []
            for i, entry in enumerate(display_data, start=offset + 1):
                user_id = entry["user_id"]
                count = entry['reaction_count']

                # Using the ID directly in a mention format <@ID>
                # This is much faster than 'await bot.fetch_user' because it
                # doesn't require an API call for every single row.
                description_lines.append(f"{i}. <@{user_id}> : 🔥 x {count}")

            embed.description = "\n".join(description_lines) if description_lines else "No data found."
            embed.set_footer(text="© 2026 mash-it")

            # Update button states
            self.prev_button.disabled = (self.page == 1)
            self.next_button.disabled = not has_next

            return embed
        except Exception as e:
            # Better to log errors properly in a real app
            print(f"Error in LeaderboardView: {e}")
            return discord.Embed(title="Error", description="Could not load leaderboard.")

    @discord.ui.button(label="Prev page", style=discord.ButtonStyle.gray)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        embed = await self.create_embed()
        # Passing self (the view) back ensures button states (disabled/enabled) update
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next page", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)