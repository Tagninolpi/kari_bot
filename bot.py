import asyncio
import os
import discord
from discord.ext import commands

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")  # <- get token from Render env

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=None, intents=discord.Intents.default())

    async def setup_hook(self):
        # Load all cogs
        import os
        if os.path.isdir("cogs"):
            for file in os.listdir("cogs"):
                if file.endswith(".py") and not file.startswith("_"):
                    await self.load_extension(f"cogs.{file[:-3]}")
        # Sync slash commands
        await self.tree.sync()

    async def on_ready(self):
        print(f"✅ Logged in as {self.user} ({self.user.id})")

async def main():
    bot = Bot()
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
