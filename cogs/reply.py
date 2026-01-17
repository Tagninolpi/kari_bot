import discord
from discord import app_commands
from discord.ext import commands

class Reply(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="reply",
        description="Answer that delphinian as the oracle"
    )
    @app_commands.describe(message="The message the oracle should send")
    async def reply(self, interaction: discord.Interaction, message: str):
        try:
            # ✅ Defer the interaction so Discord knows we're handling it
            await interaction.response.defer()
            # Send the actual message in the channel
            await interaction.channel.send(message)
        except discord.Forbidden:
            # Only send this if absolutely needed (you could skip it)
            await interaction.followup.send(
                "❌ I don't have permission to send messages here.",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.followup.send(
                f"❌ Failed to send message: {e}",
                ephemeral=True
            )

# Setup
async def setup(bot: commands.Bot):
    await bot.add_cog(Reply(bot))
