import discord


class Button(discord.ui.View):
    def __init__(self, author: discord.Member | discord.User):
        super().__init__(timeout=None)
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Check permissions
        is_author = interaction.user.id == self.author.id
        # Admin or Manage Messages (Moderator)
        is_staff = interaction.user.guild_permissions.administrator or \
                   interaction.user.guild_permissions.manage_messages

        if is_author or is_staff:
            return True

        await interaction.response.send_message(
            "Only the owner, a Moderator, or an Admin can delete this!",
            ephemeral=True
        )
        return False

    @discord.ui.button(label="Drop it", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()