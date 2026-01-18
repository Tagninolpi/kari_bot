import re
import traceback
import discord
from discord.ext import commands
from oracle_ai import ask_oracle
import datetime
from cogs.db.database_editor import insert_request, find_previous_response, get_last_request_for_user

# Helper function for UTC+8
def now_utc8():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)

# Helper function to normalize questions for repeat detection
def normalize_question(q: str) -> str:
    # Keep only letters, convert to lowercase
    return re.sub(r'[^a-zA-Z]', '', q).lower()


class Oracle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.WATCH_CHANNEL_ID = 1454904537067294870#1445080995480076441
        self.DAILY_LIMIT = 20

    @commands.Cog.listener()
    async def on_message(self, message):
        #print(f"📨 Received message from {message.author}: '{message.content}'")

        # Ignore bot messages
        if message.author.bot:
            #print("⛔ Ignored: message from a bot")
            return

        # Only watch the specific channel
        if message.channel.id != self.WATCH_CHANNEL_ID:
            #print(f"⛔ Ignored: message from channel {message.channel.id}")
            return

        content = message.content.strip()
        #print(f"🔍 Checking message content: '{content}'")

        # --- Match trigger "Oracle:" with optional spaces, ending with "?" ---
        match = re.match(r"^Oracle\s*:\s*(.+)\?$", content, re.IGNORECASE)
        if not match:
            print("⛔ Ignored: does not match trigger pattern")
            return

        # Extract question text
        question = match.group(1).strip()
        normalized_question = normalize_question(question)
        #print(f"✅ Matched trigger. Original question: '{question}', Normalized: '{normalized_question}'")

        # --- 1️⃣ Check if question already exists in DB ---
        previous_response = find_previous_response(normalized_question)
        if previous_response:
            #print(f"🧠 Found previous response in DB: '{previous_response}'")
            await message.channel.send(f"🔮 **Oracle**: {previous_response} (from memory)")
            return
        else:
            #print("🧠 No previous response found in DB")
            pass

        # --- 2️⃣ Check daily limits and 2-minute interval based on last request ---
        last_request = get_last_request_for_user(message.author.id)
        now = now_utc8()

        current_count = 0
        last_request_time = None

        if last_request:
            last_request_ts = datetime.datetime.fromisoformat(last_request["timestamp"])
            last_request_time = last_request_ts + datetime.timedelta(hours=8)  # UTC+8
            last_request_date = last_request_time.date()
            current_count = last_request.get("current_count", 0)
            #print(f"🕒 Last request at {last_request_time}, current_count={current_count}")
        else:
            last_request_date = None
            #print("🕒 No previous requests found for user")

        # Reset count if new day
        if not last_request_date or now.date() > last_request_date:
            #print("🔄 New day detected, resetting count")
            current_count = 0
            last_request_time = None

        # --- 2a️⃣ Minimum 2-minute interval ---
        if last_request_time:
            # Convert both to naive UTC+8 for comparison
            now_naive = now.replace(tzinfo=None)
            last_naive = last_request_time.replace(tzinfo=None)
            delta = now_naive - last_naive
            #print(f"⏱ Time since last request: {delta.total_seconds()} seconds")
            if delta.total_seconds() < 120:
                remaining_sec = 120 - int(delta.total_seconds())
                minutes, seconds = divmod(remaining_sec, 60)
                await message.channel.send(
                    f"⏳ Oracle: Patience is needed. You must wait {minutes}m {seconds}s before asking again."
                )
                return


        # --- 2b️⃣ Daily limit ---
        if current_count >= self.DAILY_LIMIT:
            tomorrow = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time(0, 0))
            remaining = tomorrow - now
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            #print(f"🔒 Daily limit reached, cannot ask AI until tomorrow")
            await message.channel.send(
                f"🔮 Oracle: The stars must rest until tomorrow. "
                f"(Daily limit {self.DAILY_LIMIT} reached)\n"
                f"Time remaining: {hours}h {minutes}m {seconds}s"
            )
            return

        # --- 3️⃣ Ask AI ---
        async with message.channel.typing():
            try:
                #print(f"🤖 Asking AI for question: '{question}'")
                prophecy = ask_oracle(question)
                current_count += 1
                #print(f"✅ AI returned response: '{prophecy}'")
            except Exception as e:
                print("❌ ORACLE ERROR:")
                print(e)
                traceback.print_exc()
                prophecy = "The stars are silent… (an error was revealed in the void)"

        # Send the AI response
        await message.channel.send(f"🔮 **Oracle**: {prophecy}")

        # --- 4️⃣ Save request to database ---
        insert_request(
            user_id=message.author.id,
            username=str(message.author),
            question=normalized_question,  # store normalized version for repeat detection
            ai_response=prophecy,
            daily_limit=self.DAILY_LIMIT,
            current_count=current_count
        )
        #print(f"📥 Logged question for user {message.author}")


async def setup(bot):
    await bot.add_cog(Oracle(bot))
