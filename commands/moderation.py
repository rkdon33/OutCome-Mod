import nextcord
from nextcord.ext import commands
from nextcord import Interaction, Member
from nextcord.errors import Forbidden
from nextcord.ext.commands import has_permissions, BotMissingPermissions, MissingPermissions, MissingRequiredArgument

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # KICK COMMANDS
    @commands.command(name="kick")
    @has_permissions(kick_members=True)
    async def kick(self, ctx, member: nextcord.Member, *, reason="No reason provided"):
        try:
            await member.kick(reason=reason)
            await ctx.send(f"✅ {member} was kicked. Reason: {reason}")
        except Forbidden:
            await ctx.send("❌ I do not have permission to kick this user.")

    @nextcord.slash_command(name="kick", description="Kick a member from the server")
    async def kick_slash(self, interaction: Interaction, member: nextcord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("❌ You don't have permission to do this.", ephemeral=True)
            return
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f"✅ {member} was kicked. Reason: {reason}")
        except Forbidden:
            await interaction.response.send_message("❌ I do not have permission to kick this user.", ephemeral=True)

    # BAN COMMANDS
    @commands.command(name="ban")
    @has_permissions(ban_members=True)
    async def ban(self, ctx, member: nextcord.Member, *, reason="No reason provided"):
        try:
            await member.ban(reason=reason)
            await ctx.send(f"✅ {member} was banned. Reason: {reason}")
        except Forbidden:
            await ctx.send("❌ I do not have permission to ban this user.")

    @nextcord.slash_command(name="ban", description="Ban a member from the server")
    async def ban_slash(self, interaction: Interaction, member: nextcord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("❌ You don't have permission to do this.", ephemeral=True)
            return
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"✅ {member} was banned. Reason: {reason}")
        except Forbidden:
            await interaction.response.send_message("❌ I do not have permission to ban this user.", ephemeral=True)

    # MUTE COMMANDS (Timeout)
    @commands.command(name="mute")
    @has_permissions(moderate_members=True)
    async def mute(self, ctx, member: nextcord.Member, duration: int, *, reason="No reason provided"):
        try:
            await member.edit(timeout=nextcord.utils.utcnow() + nextcord.timedelta(minutes=duration), reason=reason)
            await ctx.send(f"✅ {member} has been muted for {duration} minutes. Reason: {reason}")
        except Exception as e:
            await ctx.send(f"❌ Failed to mute: {e}")

    @nextcord.slash_command(name="mute", description="Mute (timeout) a member")
    async def mute_slash(self, interaction: Interaction, member: nextcord.Member, duration: int, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("❌ You don't have permission to do this.", ephemeral=True)
            return
        try:
            await member.edit(timeout=nextcord.utils.utcnow() + nextcord.timedelta(minutes=duration), reason=reason)
            await interaction.response.send_message(f"✅ {member} has been muted for {duration} minutes. Reason: {reason}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to mute: {e}", ephemeral=True)

    # CLEAR COMMANDS
    @commands.command(name="clear")
    @has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹 Cleared {len(deleted)-1} messages.", delete_after=5)

    @nextcord.slash_command(name="clear", description="Clear a number of messages")
    async def clear_slash(self, interaction: Interaction, amount: int):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You don't have permission to do this.", ephemeral=True)
            return
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"🧹 Cleared {len(deleted)} messages.", ephemeral=True)

    # ERROR HANDLER
    @kick.error
    @ban.error
    @mute.error
    @clear.error
    async def mod_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            await ctx.send("❌ You do not have the required permissions.")
        elif isinstance(error, BotMissingPermissions):
            await ctx.send("❌ I do not have the required permissions.")
        elif isinstance(error, MissingRequiredArgument):
            await ctx.send("❌ Missing member or required argument.")
        else:
            await ctx.send(f"❌ An error occurred: {error}")

def setup(bot):
    bot.add_cog(Moderation(bot))