import re
import traceback
import asyncio
import datetime
import discord
from discord.ext import commands

from KariGPT_ai import ask_KariGPT
from cogs.db.database_editor import (
    insert_request,
    find_previous_response,
    get_last_request_for_user,
)

# =========================
# Timezone (UTC+8)
# =========================
KariGPT_TZ = datetime.timezone(datetime.timedelta(hours=8))


def now_utc8():
    return datetime.datetime.now(KariGPT_TZ)


# =========================
# Helpers
# =========================
def normalize_question(q: str) -> str:
    return re.sub(r"[^a-zA-Z]", "", q).lower()

async def send_error_with_status(channel, now, current_count, daily_limit, message):
    await channel.send(message)
    await channel.send(
        KariGPT_status_message(
            now=now,
            current_count=current_count,
            daily_limit=daily_limit,
        )
    )


def KariGPT_status_message(now, current_count, daily_limit):
    remaining_requests = daily_limit - current_count
    tomorrow = datetime.datetime.combine(
        now.date() + datetime.timedelta(days=1),
        datetime.time(0, 0),
        tzinfo=KariGPT_TZ,
    )

    remaining_time = tomorrow - now
    hours, remainder = divmod(int(remaining_time.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)

    return (
    f"✨ **KariGPT**\n"
    f"You’ve got **{remaining_requests}** requests left today\n"
    f"Reset in **{hours}h {minutes}m**"
)




async def send_daily_limit_message(channel, now, daily_limit):
    tomorrow = datetime.datetime.combine(
        now.date() + datetime.timedelta(days=1),
        datetime.time(0, 0),
        tzinfo=KariGPT_TZ,
    )

    remaining = tomorrow - now
    hours, remainder = divmod(int(remaining.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    await channel.send(
    f"⏳ **KariGPT**: That’s today’s limit.\n"
    f"Come back in {hours}h {minutes}m {seconds}s."
)



# =========================
# Cog
# =========================
class KariGPT(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
        self.WATCH_CHANNEL_ID = [1445080995480076441,1465442662470389914]
        self.DAILY_LIMIT = 20

        # Precompiled regex (safer + faster)
        self.trigger_regex = re.compile(
            r"^KariGPT\s*:\s*(.+?)\s*\?\s*$",
            re.IGNORECASE,
        )

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        traceback.print_exc()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not (message.channel.id in self.WATCH_CHANNEL_ID):
            return

        match = self.trigger_regex.match(message.content.strip())
        if not match:
            print("[KariGPT] Ignored:", message.content)
            await self.bot.process_commands(message)
            return

        question = match.group(1).strip()
        normalized_question = normalize_question(question)

        # =========================
        # Memory lookup
        # =========================
        previous = find_previous_response(normalized_question)
        if previous:
            await message.channel.send(
                f"🔮 **KariGPT**: {previous} *(from memory)*"
            )
            return

        # =========================
        # Rate limiting
        # =========================
        now = now_utc8()
        last_request = get_last_request_for_user(message.author.id)

        current_count = 0
        last_request_time = None
        last_request_date = None

        if last_request:
            try:
                ts = datetime.datetime.fromisoformat(last_request["timestamp"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=datetime.timezone.utc)
                last_request_time = ts.astimezone(KariGPT_TZ)
                last_request_date = last_request_time.date()
                current_count = last_request.get("current_count", 0)
            except Exception:
                # Corrupt timestamp should never kill the KariGPT
                last_request_time = None
                last_request_date = None
                current_count = 0

        if not last_request_date or now.date() > last_request_date:
            current_count = 0
            last_request_time = None

        # 2-minute cooldown
        if last_request_time:
            delta = (now - last_request_time).total_seconds()
            if delta < 120:
                remaining = int(120 - delta)
                minutes, seconds = divmod(remaining, 60)
                await message.channel.send(
                    f"⏳ KariGPT: Patience. {minutes}m {seconds}s remain."
                )
                return

        # Daily limit
        if current_count >= self.DAILY_LIMIT:
            await send_daily_limit_message(
                message.channel,
                now,
                self.DAILY_LIMIT,
            )
            return

        # =========================
        # AI call (NON-BLOCKING)
        # =========================
        async with message.channel.typing():
            try:
                prophecy = await asyncio.to_thread(
                    ask_KariGPT,
                    question,
                )
                current_count += 1

            except Exception as e:
                error_text = str(e)
                traceback.print_exc()

                overload_signals = (
                    "RESOURCE_EXHAUSTED",
                    "Quota",
                    "overloaded",
                    "503",
                    "UNAVAILABLE",
                )

                if any(signal in error_text for signal in overload_signals):
                    await send_error_with_status(
                        channel=message.channel,
                        now=now,
                        current_count=current_count,
                        daily_limit=self.DAILY_LIMIT,
                        message = (
    "⚠️ **KariGPT**: Things are moving too fast right now.\n"
    "Try again in a sec."
)
,
                    )
                    return

                # All other errors
                await send_error_with_status(
                    channel=message.channel,
                    now=now,
                    current_count=current_count,
                    daily_limit=self.DAILY_LIMIT,
                    message=f"❌ **KariGPT Error**:\n```{error_text}```",
                )
                return





        # =========================
        # Send response
        # =========================
        try:
            await message.channel.send(f"🔮 **KariGPT**: {prophecy}")
            await message.channel.send(
                KariGPT_status_message(
                    now,
                    current_count,
                    self.DAILY_LIMIT,
                )
            )

            insert_request(
                user_id=message.author.id,
                username=str(message.author),
                question=normalized_question,
                ai_response=prophecy,
                daily_limit=self.DAILY_LIMIT,
                current_count=current_count,
            )

        except Exception as e:
            traceback.print_exc()
            await message.channel.send(
                "❌ **KariGPT** hit an error after generating a response."
            )
            raise


        await self.bot.process_commands(message)


async def setup(bot):
    await bot.add_cog(KariGPT(bot))
