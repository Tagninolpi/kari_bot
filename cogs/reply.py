import discord
from discord import app_commands
from discord.ext import commands

# -------- Cog --------
class Reply(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="reply",
        description="Answer that delphinian as the oracle"
    )
    @app_commands.describe(message="The message the oracle should send")
    async def reply(self, interaction: discord.Interaction, message: str):
        # Send the message as the bot
        try:
            await interaction.channel.send(message)
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to send messages here.",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"❌ Failed to send message: {e}",
                ephemeral=True
            )

# -------- Setup --------
async def setup(bot: commands.Bot):
    await bot.add_cog(Reply(bot))
