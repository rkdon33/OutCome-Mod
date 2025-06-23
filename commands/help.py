import nextcord
from nextcord.ext import commands
from nextcord import Embed, ButtonStyle
from nextcord.ui import View, Button, button, Item

class SupportButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Support", style=ButtonStyle.link, url="https://discord.gg/ERYMCnhWjG"))

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx):
        embed = Embed(
            title="Help Menu",
            description=(
                "**Moderation Commands**\n"
                "`.kick @user [reason]` - Kick a member\n"
                "`.ban @user [reason]` - Ban a member\n"
                "`.mute @user <minutes> [reason]` - Timeout (mute) a member\n"
                "`.clear <number>` - Clear messages\n\n"
                "**Slash Commands** — Use `/kick`, `/ban`, `/mute`, `/clear`\n\n"
                "**Result Command**\n"
                "`.result` or `/result` - Start the result making process\n\n"
                "[Support Server](https://discord.gg/ERYMCnhWjG)"
            ),
            color=nextcord.Color.blurple()
        )
        await ctx.send(embed=embed, view=SupportButtonView())

    @nextcord.slash_command(name="help", description="Show the help menu")
    async def help_slash(self, interaction: nextcord.Interaction):
        embed = Embed(
            title="Help Menu",
            description=(
                "**Moderation Commands**\n"
                "`.kick @user [reason]` - Kick a member\n"
                "`.ban @user [reason]` - Ban a member\n"
                "`.mute @user <minutes> [reason]` - Timeout (mute) a member\n"
                "`.clear <number>` - Clear messages\n\n"
                "**Slash Commands** — Use `/kick`, `/ban`, `/mute`, `/clear`\n\n"
                "[Support Server](https://discord.gg/ERYMCnhWjG)"
            ),
            color=nextcord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=SupportButtonView(), ephemeral=True)

def setup(bot):
    bot.add_cog(Help(bot))