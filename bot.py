import asyncio
import os
import discord
from discord.ext import commands
from aiohttp import web

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

# ---------- Discord Bot ----------

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=None, intents=discord.Intents.default())

    async def setup_hook(self):
        # Load all cogs
        if os.path.isdir("cogs"):
            for file in os.listdir("cogs"):
                if file.endswith(".py") and not file.startswith("_"):
                    await self.load_extension(f"cogs.{file[:-3]}")
        # Sync slash commands
        await self.tree.sync()

    async def on_ready(self):
        print(f"✅ Logged in as {self.user} ({self.user.id})")

# ---------- Web Server ----------

async def handle(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    port = int(os.environ.get("PORT", 5000))  # Render provides PORT env variable
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Web server running on port {port}")

# ---------- Main ----------

async def main():
    bot = Bot()
    # Start web server in background
    await start_web_server()
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
