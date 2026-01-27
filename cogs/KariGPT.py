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
# Timezone (UTC-8)
# =========================
KariGPT_TZ = datetime.timezone(datetime.timedelta(hours=-8))

def now_utc8():
    return datetime.datetime.now(KariGPT_TZ)

# =========================
# Helpers
# =========================
def normalize_question(q: str) -> str:
    return re.sub(r"[^a-zA-Z]", "", q).lower()

def build_memory_key(personality: str, question: str) -> str:
    raw = f"{personality}:{question}"
    return normalize_question(raw)

async def send_error_with_status(channel, now, current_count, daily_limit, message):
    await channel.send(message)
    await channel.send(
        fallen_angel_status_message(
            now=now,
            current_count=current_count,
            daily_limit=daily_limit,
        )
    )

def fallen_angel_status_message(now, current_count, daily_limit):
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
        f"🕯️ **Fallen Angel System Status**\n"
        f"Requests remaining today: **{remaining_requests}**\n"
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
        f"⏳ **Daily request limit reached**.\n"
        f"Access will be restored in {hours}h {minutes}m {seconds}s."
    )

# =========================
# Cog
# =========================
class KariGPT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.WATCH_CHANNEL_ID = [1445080995480076441, 1465442662470389914]
        self.DAILY_LIMIT = 20

        # personality : question ?
        self.trigger_regex = re.compile(
            r"^([a-zA-Z]+)\s*:\s*(.+?)\s*\?\s*$",
            re.IGNORECASE,
        )

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        traceback.print_exc()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel.id not in self.WATCH_CHANNEL_ID:
            return

        match = self.trigger_regex.match(message.content.strip())
        if not match:
            await self.bot.process_commands(message)
            return

        personality = match.group(1).strip().lower()
        question = match.group(2).strip()

        memory_key = build_memory_key(personality, question)

        # =========================
        # Memory lookup
        # =========================
        previous = find_previous_response(memory_key)
        if previous:
            await message.channel.send(
                f"📘 **{personality.capitalize()}** (stored response):\n{previous}"
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
                current_count = 0

        if not last_request_date or now.date() > last_request_date:
            current_count = 0
            last_request_time = None

        if last_request_time:
            delta = (now - last_request_time).total_seconds()
            if delta < 120:
                remaining = int(120 - delta)
                minutes, seconds = divmod(remaining, 60)
                await message.channel.send(
                    f"⏳ **Cooldown active**. Please wait {minutes}m {seconds}s before submitting another request."
                )
                return

        if current_count >= self.DAILY_LIMIT:
            await send_daily_limit_message(message.channel, now, self.DAILY_LIMIT)
            return

        # =========================
        # AI call
        # =========================
        async with message.channel.typing():
            try:
                response_text = await asyncio.to_thread(
                    ask_KariGPT,
                    question,
                    personality=personality,
                )
                current_count += 1

            except ValueError as ve:
                await message.channel.send(f"❌ {ve}")
                return

            except Exception as e:
                await send_error_with_status(
                    channel=message.channel,
                    now=now,
                    current_count=current_count,
                    daily_limit=self.DAILY_LIMIT,
                    message=(
                        f"❌ **System error while invoking `{personality}`**:\n"
                        f"```{e}```"
                    ),
                )
                return

        # =========================
        # Send + store
        # =========================
        await message.channel.send(
            f"🕯️ **{personality.capitalize()}** response:\n{response_text}"
        )
        await message.channel.send(
            fallen_angel_status_message(now, current_count, self.DAILY_LIMIT)
        )

        insert_request(
            user_id=message.author.id,
            username=str(message.author),
            question=memory_key,
            ai_response=response_text,
            daily_limit=self.DAILY_LIMIT,
            current_count=current_count,
        )

        await self.bot.process_commands(message)


async def setup(bot):
    await bot.add_cog(KariGPT(bot))
