import nextcord
from nextcord.ext import commands

OFFICIAL_LOG_CHANNEL_ID = 1386397028354887882 # Replace with your real channel ID

class GuildLogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        channel = self.bot.get_channel(OFFICIAL_LOG_CHANNEL_ID)
        if channel:
            bot_name = self.bot.user.name
            server_name = guild.name
            await channel.send(f"**{bot_name} just landed to {server_name}**")

def setup(bot):
    bot.add_cog(GuildLogCog(bot))