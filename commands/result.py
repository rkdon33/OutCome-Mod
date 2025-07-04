import nextcord
from nextcord.ext import commands
from nextcord import Embed, Interaction, ButtonStyle
from nextcord.ui import View, Button
import io
from PIL import Image, ImageDraw, ImageFont

FF_POINTS = [12, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 0]
PUBG_POINTS = [10, 6, 5, 4, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
CYAN_COLOR = nextcord.Colour.from_rgb(0, 255, 255)
user_sessions = {}

def make_embed(desc, red=True, title=None):
    embed = Embed(description=desc, color=nextcord.Color.red() if red else nextcord.Color.blue())
    if title:
        embed.title = title
    return embed

def has_result_permission(member):
    if member.guild_permissions.administrator:
        return True
    return any(role.name.lower() == "result-maker" for role in member.roles)

def pubg_team_name_format():
    return (
        "T1. Name Here\nT2. Name Here\nT3. Name Here\nT4. Name Here\n"
        "T5. Name Here\nT6. Name Here\nT7. Name Here\nT8. Name Here\n"
        "T9. Name Here\nT10. Name Here\nT11. Name Here\nT12. Name Here\n"
        "T13. Name Here\nT14. Name Here\nT15. Name Here\nT16. Name Here"
    )

def freefire_team_name_format(num_teams):
    return "\n".join([f"T{i+1}. Name Here" for i in range(num_teams)])

class GameSelectView(View):
    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id

    @nextcord.ui.button(label="Free Fire", style=ButtonStyle.danger)
    async def free_fire(self, button: Button, interaction: Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the command author can use this.", ephemeral=True)
            return
        await interaction.response.send_message(embed=make_embed("How many teams? (Minimum 2, Maximum 12)", red=True), ephemeral=True)
        user_sessions[self.author_id] = {"step": "team_count", "game": "freefire"}
        self.stop()

    @nextcord.ui.button(label="PUBG", style=ButtonStyle.primary)
    async def pubg(self, button: Button, interaction: Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the command author can use this.", ephemeral=True)
            return
        await interaction.response.send_message(embed=make_embed("How many teams? (Minimum 2, Maximum 16)", red=True), ephemeral=True)
        user_sessions[self.author_id] = {"step": "team_count", "game": "pubg"}
        self.stop()

class ResultCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if not any(r for r in guild.roles if r.name.lower() == "result-maker"):
            await guild.create_role(
                name="result-maker",
                color=CYAN_COLOR,
                mentionable=True,
                reason="Role for using result panel"
            )

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Result cog loaded as {self.bot.user}")

    @nextcord.slash_command(name="result", description="Start result panel (Free Fire or PUBG)")
    async def result_slash(self, interaction: Interaction):
        if not has_result_permission(interaction.user):
            await interaction.response.send_message(embed=make_embed("You need to be an **Admin** or have the @result-maker role to use this command!", red=True), ephemeral=True)
            return
        embed = make_embed("Which game points table do you want to make?", red=True)
        view = GameSelectView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @commands.command(name="result")
    async def result_prefix(self, ctx):
        if not has_result_permission(ctx.author):
            await ctx.send(embed=make_embed("You need to be an **Admin** or have the @result-maker role to use this command!", red=True))
            return
        embed = make_embed("Which game points table do you want to make?", red=True)
        view = GameSelectView(ctx.author.id)
        await ctx.send(embed=embed, view=view)

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

        if not has_result_permission(message.author):
            await message.channel.send(embed=make_embed("You need to be an **Admin** or have the @result-maker role to use this feature!", red=True))
            user_sessions.pop(message.author.id, None)
            return

        if session.get("game") == "freefire":
            await self.handle_ff(message, session)
        elif session.get("game") == "pubg":
            await self.handle_pubg(message, session)

    # ===============================
    # Free Fire Logic
    # ===============================
    async def handle_ff(self, message, session):
        await self._handle_game_common(
            message, session, FF_POINTS, 12, is_ff=True
        )

    # ===============================
    # PUBG Logic
    # ===============================
    async def handle_pubg(self, message, session):
        await self._handle_game_common(
            message, session, PUBG_POINTS, 16, is_ff=False
        )

    # ===============================
    # Common Handler for Both
    # ===============================
    async def _handle_game_common(self, message, session, points_table, max_teams, is_ff):
        if session.get("step") == "team_count":
            try:
                num = int(message.content)
                if not (2 <= num <= max_teams):
                    raise ValueError
                session["team_count"] = num
                session["step"] = "match_count"
                await message.channel.send(embed=make_embed(
                    "How many matches were played?\n(Enter a number, e.g., 4)", red=True
                ))
            except:
                await message.channel.send(embed=make_embed(f"Please enter a valid number (2-{max_teams}).", red=True))
            return

        if session.get("step") == "match_count":
            try:
                match_count = int(message.content)
                if match_count < 1:
                    raise ValueError
                session["match_count"] = match_count
                session["step"] = "team_names"
                if is_ff:
                    format_msg = freefire_team_name_format(session["team_count"])
                else:
                    format_msg = pubg_team_name_format()
                await message.channel.send(embed=make_embed(
                    f"Enter team names in the format below (one per line):\n```{format_msg}```", red=True
                ))
            except:
                await message.channel.send(embed=make_embed("Please enter a valid number of matches.", red=True))
            return

        if session.get("step") == "team_names":
            lines = [l.strip() for l in message.content.split("\n") if l.strip()]
            if len(lines) != session["team_count"]:
                await message.channel.send(embed=make_embed(
                    f"Please enter exactly {session['team_count']} teams.", red=True
                ))
                return
            session["team_list"] = []
            for line in lines:
                if "." in line:
                    name = line.split(".", 1)[1].strip()
                    session["team_list"].append({
                        "name": name,
                        "played": 0,
                        "won": 0,
                        "kills": 0,
                        "position_pts": 0,
                        "total": 0
                    })
                else:
                    await message.channel.send(embed=make_embed(
                        "Please use format: T1. Name Here", red=True
                    ))
                    return
            session["current_match"] = 1
            session["step"] = "match_stats"
            session["match_data"] = []
            await message.channel.send(embed=make_embed(
                f"**Match {session['current_match']}**\n\nEnter (position and kill) for:\n- **Team {session['team_list'][0]['name']}**\n\n"
                f"Format:\n```Position, Kill\neg. 1, 3```\n\nIf team haven't played than type (``NP``)\n", red=True
            ))
            session["current_team"] = 0
            return

        if session.get("step") == "match_stats":
            idx = session.get("current_team", 0)
            if "per_match_input" not in session:
                session["per_match_input"] = []
            input_line = message.content.strip()
            team_count = session["team_count"]
            if not input_line and idx < team_count:
                await message.channel.send(embed=make_embed(
                    f"**Match {session['current_match']}**\n\nEnter (Position, Kill) for:\n- **TEAM {session['team_list'][idx]['name']}**\n\nIf team haven't played than type (``NP``)\n", red=True
                ))
                return

            if idx < team_count:
                if input_line.upper() == "NP":
                    session["per_match_input"].append(None)
                else:
                    try:
                        pos, kills = [int(x.strip()) for x in input_line.split(",")]
                        if not (1 <= pos <= max_teams) or kills < 0:
                            raise ValueError
                        session["per_match_input"].append({
                            "position": pos,
                            "kills": kills
                        })
                    except:
                        await message.channel.send(embed=make_embed(
                            f"**Match {session['current_match']}**\n\nInvalid! Enter as: position, kills (e.g., 3, 13) or NP", red=True
                        ))
                        return
                session["current_team"] += 1
                idx = session["current_team"]
                if idx < team_count:
                    await message.channel.send(embed=make_embed(
                        f"**Match {session['current_match']}**\n\nEnter (Position, Kill) for:\n- **TEAM {session['team_list'][idx]['name']}**\n\nIf team haven't played than type (``NP``)\n", red=True
                    ))
                    return
            if session["current_team"] >= team_count:
                session["match_data"].append(session["per_match_input"])
                session["per_match_input"] = []
                session["current_team"] = 0
                session["current_match"] += 1
                if session["current_match"] <= session["match_count"]:
                    await message.channel.send(embed=make_embed(
                        f"**Match {session['current_match']}**\n\nEnter (position and kill) for:\n- **Team {session['team_list'][0]['name']}**\n\n"
                        f"If team haven't played than type (``NP``)\n", red=True
                    ))
                    return
                else:
                    session["step"] = "ask_channel"
                    await message.channel.send(embed=make_embed(
                        "Mention the channel to send result\nExample: #results", red=True
                    ))
            return

        if session.get("step") == "ask_channel":
            if message.channel_mentions:
                session["result_channel"] = message.channel_mentions[0].id
                session["step"] = "ask_title"
                await message.channel.send(embed=make_embed(
                    "What should be the Tournament Name? (shown at the top)", red=True
                ))
            else:
                await message.channel.send(embed=make_embed(
                    "Please mention a channel (e.g., #results)", red=True
                ))
            return

        if session.get("step") == "ask_title":
            session["result_title"] = message.content.strip()
            await self.send_results(message, session, points_table, is_ff)
            user_sessions.pop(message.author.id, None)
            return

    # ===============================
    # Results Output for Both
    # ===============================
    async def send_results(self, message, session, points_table, is_ff):
        teams = session["team_list"]
        match_count = session["match_count"]
        match_datas = session["match_data"]

        # Calculate stats
        for i, team in enumerate(teams):
            played = 0
            won = 0
            kills = 0
            position_pts = 0
            points = 0
            for m in range(match_count):
                match = match_datas[m]
                entry = match[i]
                if entry is not None:
                    played += 1
                    kills += entry["kills"]
                    if entry["position"] == 1:
                        won += 1
                    pos_idx = entry["position"] - 1
                    pos_points = points_table[pos_idx] if 0 <= pos_idx < len(points_table) else 0
                    position_pts += pos_points
                    match_points = pos_points + entry["kills"]
                    points += match_points
            team["played"] = played
            team["won"] = won
            team["kills"] = kills
            team["position_pts"] = position_pts
            team["total"] = points

        # Free Fire: sort by points, then kills
        if is_ff:
            sorted_teams = sorted(teams, key=lambda x: (x["total"], x["kills"]), reverse=True)
        else:
            sorted_teams = sorted(teams, key=lambda x: x["total"], reverse=True)

        if is_ff:
            # Output as image
            bg_path = "images/overall_standing_template.png"
            try:
                bg = Image.open(bg_path).convert("RGBA")
            except Exception as e:
                await message.channel.send(embed=make_embed(f"Image template not found: {e}", red=True))
                return

            draw = ImageDraw.Draw(bg)
            try:
                font_title = ImageFont.truetype("fonts/arialbd.ttf", 48)
                font_row = ImageFont.truetype("fonts/arialbd.ttf", 18)
                font_total = ImageFont.truetype("fonts/arialbd.ttf", 18)
            except Exception as e:
                await message.channel.send(embed=make_embed(f"Font not found: {e}", red=True))
                return

            title = session["result_title"]
            orange = (255, 140, 0)
            draw.text((374, 74), title, anchor="mm", font=font_title, fill=orange)

            x_name = 100
            x_played = 377
            x_won = 446
            x_kills = 504
            x_pospts = 568
            x_total = 649
            y_start = 350
            row_gap = 44

            for i, team in enumerate(sorted_teams):
                y = y_start + i * row_gap
                draw.text((x_name, y), team["name"], font=font_row, fill=(0,0,0), anchor="lm")
                draw.text((x_played, y), str(team["played"]), font=font_row, fill=(255,255,255), anchor="mm")
                draw.text((x_won, y), str(team["won"]), font=font_row, fill=(255,255,255), anchor="mm")
                draw.text((x_kills, y), str(team["kills"]), font=font_row, fill=(255,255,255), anchor="mm")
                draw.text((x_pospts, y), str(team["position_pts"]), font=font_row, fill=(255,255,255), anchor="mm")
                draw.text((x_total, y), str(team["total"]), font=font_total, fill=(0,0,0), anchor="mm")

            buffer = io.BytesIO()
            bg.save(buffer, format="PNG")
            buffer.seek(0)
            channel = message.guild.get_channel(session["result_channel"])
            if channel:
                file = nextcord.File(fp=buffer, filename="overall_standing.png")
                await channel.send(file=file)
                await message.channel.send(embed=make_embed("Result image sent!", red=True))
            else:
                await message.channel.send(embed=make_embed("Failed to find channel.", red=True))
        else:
            # Output as text
            result_lines = []
            result_lines.append(f"{'Rank':<5}{'Team':<20}{'Played':<7}{'Won':<5}{'Kills':<7}{'PosPts':<8}{'Total':<7}")
            for idx, team in enumerate(sorted_teams):
                result_lines.append(f"{idx+1:<5}{team['name']:<20}{team['played']:<7}{team['won']:<5}{team['kills']:<7}{team['position_pts']:<8}{team['total']:<7}")
            table = "```\n" + "\n".join(result_lines) + "\n```"
            channel = message.guild.get_channel(session["result_channel"])
            if channel:
                await channel.send(table)
                await message.channel.send(embed=make_embed("PUBG result sent!", red=True))
            else:
                await message.channel.send(embed=make_embed("Failed to find channel.", red=True))

def setup(bot):
    bot.add_cog(ResultCog(bot))