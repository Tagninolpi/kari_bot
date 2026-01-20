import discord
from discord.ext import commands
from discord import app_commands
from cogs.db.database_editor import generate_request_summary
import datetime

ORACLE_TZ = datetime.timezone(datetime.timedelta(hours=8))

def now_utc8():
    return datetime.datetime.now(ORACLE_TZ)


class OracleMetrics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="oracle_metrics", description="View Oracle request metrics")
    async def oracle_metrics(self, interaction: discord.Interaction):
        now = now_utc8()
        summary = generate_request_summary(now=now)

        if not summary:
            await interaction.response.send_message("❌ Failed to generate metrics.")
            return
        if "message" in summary:
            await interaction.response.send_message(summary["message"])
            return

        embed = discord.Embed(
            title="🔮 Oracle Metrics",
            color=discord.Color.purple(),
            timestamp=now
        )

        # Global stats
        g = summary["global_stats"]
        embed.add_field(
            name="🌐 Global Stats",
            value=(
                f"Total requests: **{g['total_requests']}**\n"
                f"Average per day: **{g['average_requests_per_day']}**\n"
                f"Max requests in a single day: **{g['max_requests_per_day']}**"
            ),
            inline=False
        )

        # Today's stats (UTC+8)
        t = summary["today_stats"]
        today_text = f"Total requests today: **{t['total_requests_today']}**\n"
        for uid, info in t["requests_per_user_today"].items():
            today_text += f"- {info['username']}: **{info['count']}**\n"
        embed.add_field(name="📅 Today (UTC+8)", value=today_text, inline=False)

        # Per-player stats
        per_player_text = ""
        for uid, p in summary["per_player_stats"].items():
            per_player_text += (
                f"{p['username']}: Total **{p['total_requests']}**, "
                f"Avg/day **{p['average_per_day']}**, "
                f"Max/day **{p['max_requests_per_day']}**\n"
            )
        embed.add_field(name="👤 Per Player", value=per_player_text, inline=False)

        await interaction.response.send_message(embed=embed)



async def setup(bot):
    await bot.add_cog(OracleMetrics(bot))
