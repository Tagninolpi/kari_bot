import discord
from discord.ext import commands
from discord import app_commands

from KariGPT_ai import PERSONALITIES


class FallenAngels2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="angels",
        description="View available fallen angels"
    )
    async def angels(self, interaction: discord.Interaction):
        if not PERSONALITIES:
            await interaction.response.send_message(
                "❌ No fallen angels are currently available.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="😈 Fallen Angels",
            description="Invoke one by starting your message with:\n`angel_name: your question?`",
            color=discord.Color.dark_red()
        )

        angels_list = ""
        for key in sorted(PERSONALITIES.keys()):
            angels_list += f"• **{key}**\n"

        embed.add_field(
            name="🔥 Available Angels",
            value=angels_list,
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(FallenAngels2(bot))
