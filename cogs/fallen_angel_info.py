import discord
from discord.ext import commands
from discord import app_commands

from KariGPT_ai import PERSONALITIES


class FallenAngelInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="angel",
        description="View details about a fallen angel"
    )
    @app_commands.describe(name="Select a fallen angel")
    async def angel(
        self,
        interaction: discord.Interaction,
        name: str
    ):
        angel_key = name.lower()

        if angel_key not in PERSONALITIES:
            await interaction.response.send_message(
                f"❌ Fallen angel `{name}` not found.",
                ephemeral=True
            )
            return

        description = PERSONALITIES[angel_key]

        embed = discord.Embed(
            title=f"😈 Fallen Angel: {angel_key}",
            description=description,
            color=discord.Color.dark_red()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    @angel.autocomplete("name")
    async def angel_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ):
        return [
            app_commands.Choice(name=key, value=key)
            for key in PERSONALITIES.keys()
            if current.lower() in key.lower()
        ]


async def setup(bot):
    await bot.add_cog(FallenAngelInfo(bot))
