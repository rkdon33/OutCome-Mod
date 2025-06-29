import nextcord
from nextcord.ext import commands
from nextcord import Interaction, ButtonStyle, Embed, SelectOption
from nextcord.ui import View, Button, Select

FF_POINTS = [12, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 0]  # Free Fire
PUBG_POINTS = [10, 6, 5, 4, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]  # PUBG, for 16 teams

user_sessions = {}

def make_embed(desc, red=True, title=None):
    embed = Embed(description=desc, color=nextcord.Color.red() if red else nextcord.Color.blue())
    if title:
        embed.title = title
    return embed

def pubg_team_name_format():
    # 16 slots for PUBG
    return (
        "Team 1 - Name Here\nTeam 2 - Name Here\nTeam 3 - Name Here\nTeam 4 - Name Here\n"
        "Team 5 - Name Here\nTeam 6 - Name Here\nTeam 7 - Name Here\nTeam 8 - Name Here\n"
        "Team 9 - Name Here\nTeam 10 - Name Here\nTeam 11 - Name Here\nTeam 12 - Name Here\n"
        "Team 13 - Name Here\nTeam 14 - Name Here\nTeam 15 - Name Here\nTeam 16 - Name Here"
    )

class GameSelectView(View):
    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id

    @nextcord.ui.button(label="Free Fire", style=ButtonStyle.danger)
    async def free_fire(self, button: Button, interaction: Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the command author can use this.", ephemeral=True)
            return
        await interaction.response.send_message(embed=make_embed("How many teams?\n```Minimum: 2 - Maximum 12```", red=True), ephemeral=True)
        user_sessions[self.author_id] = {"game": "freefire", "step": "team_count"}
        self.stop()

    @nextcord.ui.button(label="PUBG", style=ButtonStyle.danger)
    async def pubg(self, button: Button, interaction: Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the command author can use this.", ephemeral=True)
            return
        await interaction.response.send_message(embed=make_embed("How many teams?\n```Minimum: 2 - Maximum 16```", red=True), ephemeral=True)
        user_sessions[self.author_id] = {"game": "pubg", "step": "team_count"}
        self.stop()

class TeamDetailsView(View):
    def __init__(self, teams):
        super().__init__(timeout=60)
        self.teams = teams
        self.add_item(TeamSelect(teams))

class TeamSelect(Select):
    def __init__(self, teams):
        options = [SelectOption(label=team['name'], value=str(idx)) for idx, team in enumerate(teams)]
        super().__init__(placeholder="Select a team...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        team = self.view.teams[int(self.values[0])]
        embed = Embed(
            title=f"Team Details: {team['name']}",
            description=(
                f"**Team Name:** {team['name']}\n"
                f"**Total Kills:** {team['kills']}\n"
                f"**Position:** {team['position']}\n"
                f"**Total Points:** {team['total']}"
            ),
            color=nextcord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class DetailsButtonView(View):
    def __init__(self, teams):
        super().__init__(timeout=None)
        self.teams = teams

    @nextcord.ui.button(label="Details", style=ButtonStyle.primary)
    async def details(self, button: Button, interaction: Interaction):
        await interaction.response.send_message(
            "Select a team to view details:",
            view=TeamDetailsView(self.teams),
            ephemeral=True
        )

class ResultCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Result cog loaded as {self.bot.user}")

    @commands.command(name="result")
    @commands.has_permissions(administrator=True)
    async def result_prefix(self, ctx):
        await self.start_result(ctx)

    @result_prefix.error
    async def result_prefix_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=make_embed("You need to be an **Admin** to use this command!", red=True))

    @nextcord.slash_command(name="result", description="Start result making panel")
    async def result_slash(self, interaction: Interaction):
        # Check admin permission for slash command
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(embed=make_embed("You need to be an **Admin** to use this command!", red=True), ephemeral=True)
            return
        await self.start_result(interaction)

    async def start_result(self, ctx_or_interaction):
        if isinstance(ctx_or_interaction, commands.Context):
            author = ctx_or_interaction.author
            embed = make_embed("Which game points table do you want to make?", red=True)
            view = GameSelectView(author.id)
            await ctx_or_interaction.send(embed=embed, view=view)
        else:
            author = ctx_or_interaction.user
            embed = make_embed("Which game points table do you want to make?", red=True)
            view = GameSelectView(author.id)
            await ctx_or_interaction.send(embed=embed, view=view, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        session = user_sessions.get(message.author.id)
        if not session:
            return

        # Check admin permission for message-based steps
        if not message.author.guild_permissions.administrator:
            await message.channel.send(embed=make_embed("You need to be an **Admin** to use this feature!", red=True))
            user_sessions.pop(message.author.id, None)
            return

        # Team count step (supports both games)
        if session.get("step") == "team_count":
            try:
                num = int(message.content)
                game = session["game"]
                min_teams = 2
                max_teams = 12 if game == "freefire" else 16
                if min_teams <= num <= max_teams:
                    session["team_count"] = num
                    session["step"] = "team_names"
                    if game == "pubg":
                        format_msg = pubg_team_name_format()
                        max_show = 16
                    else:
                        format_msg = "\n".join([f"Team {i+1} - Name Here" for i in range(12)])
                        max_show = 12
                    await message.channel.send(embed=make_embed(
                        f"**Enter team names in the same format given below:\n- One Line per Team\n- Easy Tip:- Hold this message to copy it:**\n```{format_msg}```", red=True
                    ))
                else:
                    await message.channel.send(embed=make_embed(
                        f"Number must be between {min_teams} and {max_teams}.", red=True))
            except:
                await message.channel.send(embed=make_embed("Please enter a valid number.", red=True))
            return

        if session.get("step") == "team_names":
            lines = [l.strip() for l in message.content.split("\n") if l.strip()]
            if len(lines) != session["team_count"]:
                await message.channel.send(embed=make_embed(
                    f"Please enter exactly {session['team_count']} teams.", red=True
                ))
                return
            teams = []
            for line in lines:
                if "-" in line:
                    name = line.split("-", 1)[1].strip()
                    teams.append({"name": name})
                else:
                    await message.channel.send(embed=make_embed(
                        "Please use format: Team 1 - ABC", red=True
                    ))
                    return
            session["teams"] = teams
            session["current_team"] = 0
            session["used_positions"] = set()  # Track used positions
            session["step"] = "team_stats"
            await message.channel.send(embed=make_embed(
                f"Enter position and kills for:\n**- TEAM {teams[0]['name']}**\nFormat:\n```Position, Kill```\n**- eg: 1, 3\n- Here 1 means First position and 3 means total kill is 3**", red=True
            ))
            return

        if session.get("step") == "team_stats":
            idx = session["current_team"]
            team = session["teams"][idx]
            try:
                pos, kills = [int(x.strip()) for x in message.content.split(",")]
                game = session["game"]
                max_pos = 12 if game == "freefire" else 16
                if not (1 <= pos <= max_pos) or kills < 0:
                    raise ValueError
                # Position can only be used once!
                if pos in session["used_positions"]:
                    await message.channel.send(embed=make_embed(
                        f"Position {pos} has already been assigned to another team! Each position can only be used once.", red=True
                    ))
                    return
                session["used_positions"].add(pos)
                team["position"] = pos
                team["kills"] = kills
                session["teams"][idx] = team
                if idx + 1 < session["team_count"]:
                    session["current_team"] += 1
                    await message.channel.send(embed=make_embed(
                        f"Enter position and kills for:\n**- TEAM {session['teams'][idx+1]['name']}**", red=True
                    ))
                else:
                    session["step"] = "ask_channel"
                    await message.channel.send(embed=make_embed(
                        "Mention the channel to send result\n```e.g. #results```", red=True
                    ))
            except:
                await message.channel.send(embed=make_embed(
                    "Invalid format! Please enter as: position, kills (e.g., 3, 13)", red=True
                ))
            return

        if session.get("step") == "ask_channel":
            if message.channel_mentions:
                session["result_channel"] = message.channel_mentions[0].id
                session["step"] = "ask_title"
                await message.channel.send(embed=make_embed(
                    "What should be the result title? (This will be shown at the top of the embed)", red=True
                ))
            else:
                await message.channel.send(embed=make_embed(
                    "Please mention a channel (e.g., #results)", red=True
                ))
            return

        if session.get("step") == "ask_title":
            session["result_title"] = message.content.strip()
            await self.send_results(message, session)
            user_sessions.pop(message.author.id, None)
            return

    async def send_results(self, message, session):
        results = []
        game = session.get("game", "freefire")
        points_table = FF_POINTS if game == "freefire" else PUBG_POINTS
        for team in session["teams"]:
            pos_idx = team["position"] - 1
            pts = (points_table[pos_idx] if 0 <= pos_idx < len(points_table) else 0) + team["kills"]
            team["total"] = pts
            results.append(team)
        results.sort(key=lambda x: x["total"], reverse=True)
        lines = [f"Total {res['total']:<3}  ->  Team {res['name']}" for res in results]
        table = "```\n" + "\n".join(lines) + "\n```"
        embed = make_embed(table, red=True, title=session["result_title"])
        channel = message.guild.get_channel(session["result_channel"])
        if channel:
            await channel.send(embed=embed, view=DetailsButtonView(results))
            await message.channel.send(embed=make_embed("Result sent!", red=True))
        else:
            await message.channel.send(embed=make_embed("Failed to find channel.", red=True))

def setup(bot):
    bot.add_cog(ResultCog(bot))