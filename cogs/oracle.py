import traceback
import discord
from discord.ext import commands
from oracle_ai import ask_oracle
import datetime
from cogs.db.database_editor import insert_request, find_previous_response, get_last_request_for_user

# Helper function for UTC+8
def now_utc8():
    return datetime.datetime.utcnow() + datetime.timedelta(hours=8)

class Oracle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.WATCH_CHANNEL_ID = 1445080995480076441
        self.DAILY_LIMIT = 20

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot messages
        if message.author.bot:
            return

        # Only watch the specific channel
        if message.channel.id != self.WATCH_CHANNEL_ID:
            return

        content = message.content.strip()

        # Only process messages that match the pattern
        if not (content.startswith("Oracle :") and content.endswith("?")):
            return

        # Extract the question text between "Oracle :" and "?"
        question = content[len("Oracle :"):].strip()

        # --- 1️⃣ Check if question already exists in DB ---
        previous_response = find_previous_response(question) 
        if previous_response:
            await message.channel.send(f"🔮 **Oracle**: {previous_response} (from memory)")
            return

        # --- 2️⃣ Check daily limits based on last request in DB ---
        last_request = get_last_request_for_user(message.author.id)
        now = now_utc8()

        # Default values if no previous request
        current_count = 0
        last_request_date = None

        if last_request:
            last_request_ts = datetime.datetime.fromisoformat(last_request["timestamp"])
            last_request_date = (last_request_ts + datetime.timedelta(hours=8)).date()  # convert to UTC+8 date
            current_count = last_request.get("current_count", 0)

        # Reset count if new day
        if not last_request_date or now.date() > last_request_date:
            current_count = 0

        if current_count >= self.DAILY_LIMIT:
            # Calculate time until next day in UTC+8
            now = now_utc8()
            tomorrow = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time(0, 0))
            remaining = tomorrow - now
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            await message.channel.send(
                f"🔮 Oracle: The stars must rest until tomorrow. "
                f"(Daily limit {self.DAILY_LIMIT} reached)\n"
                f"Time remaining: {hours}h {minutes}m {seconds}s"
            )
            return


        # --- 3️⃣ Ask AI ---
        async with message.channel.typing():
            try:
                prophecy = ask_oracle(question)
                current_count += 1
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
            question=question,
            ai_response=prophecy,
            daily_limit=self.DAILY_LIMIT,
            current_count=current_count
        )
        print(f"📥 Logged question for user {message.author}")

async def setup(bot):
    await bot.add_cog(Oracle(bot))
