import discord
from discord.ext import commands
from discord import app_commands
from cogs.db.database_editor import supabase, TABLE_NAME, KariGPT_TZ, now_utc8
import datetime

DAILY_LIMIT = 20  # Global daily limit


class KariGPTDailyLimit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="daily_status",
        description="Check how many KariGPT requests are left today and time until reset"
    )
    async def daily_status(self, interaction: discord.Interaction):
        now = now_utc8()

        # Compute today's start and next reset (UTC-8)
        today_start = datetime.datetime.combine(now.date(), datetime.time(0, 0), tzinfo=KariGPT_TZ)
        next_reset = today_start + datetime.timedelta(days=1)
        time_left = next_reset - now

        # Count requests today
        try:
            res = supabase.table(TABLE_NAME).select("id", "timestamp").execute()
            rows = res.data or []

            used_today = 0
            for r in rows:
                ts = datetime.datetime.fromisoformat(r["timestamp"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=datetime.timezone.utc)
                ts_utc8 = ts.astimezone(KariGPT_TZ)
                if today_start <= ts_utc8 < next_reset:
                    used_today += 1

            remaining = max(DAILY_LIMIT - used_today, 0)

            # Format time left
            hours, remainder = divmod(int(time_left.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)

            embed = discord.Embed(
                title="🌟 KariGPT Daily Status",
                color=discord.Color.green(),
                timestamp=now
            )
            embed.add_field(name="✅ Requests used today", value=str(used_today), inline=True)
            embed.add_field(name="🟢 Requests remaining", value=str(remaining), inline=True)
            embed.add_field(name="⏳ Time until next reset (UTC-8)", value=f"{hours}h {minutes}m", inline=False)

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to fetch daily status: {e}")


async def setup(bot):
    await bot.add_cog(KariGPTDailyLimit(bot))
