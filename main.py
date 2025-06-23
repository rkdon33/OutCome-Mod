import os
import nextcord
from nextcord.ext import commands

# (Optional: Only use if you rely on .env locally. On Replit, use the Secrets tab)
# from dotenv import load_dotenv
# load_dotenv()

import keep_alive  # Only if you use this for uptime

intents = nextcord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents)

# REMOVE THE DEFAULT HELP COMMAND
bot.remove_command("help")

# Bot status configuration - Set bot activity when it comes online
@bot.event
async def on_ready():
    await bot.change_presence(activity=nextcord.Activity(type=nextcord.ActivityType.listening, name="| .help | /help"))
    print(f"Bot is ready! Logged in as {bot.user}")

# Automatically load all Cogs from the commands folder
for filename in os.listdir('./commands'):
    if filename.endswith('.py'):
        bot.load_extension(f'commands.{filename[:-3]}')

keep_alive.keep_alive()  # Only if you use this for uptime

# Run the bot with the token from environment variable (Replit Secret or OS env)
bot.run(os.environ['BOT_TOKEN'])