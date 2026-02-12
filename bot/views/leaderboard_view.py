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
                title="Leaderboard of users by received 🔥",
                color=discord.Color.green()
            )

            description = ""
            for i, entry in enumerate(display_data, start=offset + 1):
                user_id = entry["user_id"]
                user = await self.bot.fetch_user(user_id)

                description += f"{i}. {user.display_name} : 🔥 x {entry['reaction_count']}\n"

            embed.description = description or "No data found."
            embed.set_footer(text="© 2026 mash-it")

            # Update button states
            self.prev_button.disabled = (self.page == 1)
            self.next_button.disabled = not has_next

            return embed
        except Exception as e:
            print(e)

    @discord.ui.button(label="Prev page", style=discord.ButtonStyle.gray)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next page", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        embed = await self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
