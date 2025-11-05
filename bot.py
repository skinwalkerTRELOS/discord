import discord
from discord.ext import commands
from discord.ui import View, Select
import time

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
#   CONFIG
# ==============================
LOBBY_CHANNEL_ID = 1414314047804801206
DUTY_CHANNEL_ID = 1435650177418526891

temp_channels = {}
total_time = {}           # {user_id: seconds}
currently_on_duty = {}    # {user_id: timestamp}

# ==============================
#   DUTY PANEL (DROPDOWN MENU)
# ==============================
class DutySelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="On Duty", description="Ξεκίνα να μετράς χρόνο On Duty", emoji="🟢"),
            discord.SelectOption(label="Off Duty", description="Σταμάτα το χρόνο On Duty", emoji="🔴"),
            discord.SelectOption(label="Show Me Time", description="Δες τον συνολικό σου χρόνο", emoji="⏱"),
            discord.SelectOption(label="Active Staff", description="Δείξε ποιοι είναι On Duty τώρα", emoji="👀")
        ]
        super().__init__(placeholder="Επιλογή λειτουργίας...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        choice = self.values[0]

        # =========== ON DUTY ===========
        if choice == "On Duty":
            if user_id in currently_on_duty:
                await interaction.response.send_message("ξεκολιάρη είσαι ήδη στο on duty!!! 💀", ephemeral=True)
                return
            currently_on_duty[user_id] = time.time()
            await interaction.response.send_message("Η Λιτουργία ενεργοποιήθηκε ✅.", ephemeral=True)

        # =========== OFF DUTY ===========
        elif choice == "Off Duty":
            if user_id not in currently_on_duty:
                await interaction.response.send_message("Δεν είσαι καν στο on duty ηλίθιε", ephemeral=True)
                return
            
            start_time = currently_on_duty.pop(user_id)
            elapsed = int(time.time() - start_time)
            total_time[user_id] = total_time.get(user_id, 0) + elapsed
            await interaction.response.send_message(f"Τέλιοσε ο χρονος 🕓 `{elapsed}s` προστέθηκαν.", ephemeral=True)

        # =========== SHOW TIME ===========
        elif choice == "Show Me Time":
            total = total_time.get(user_id, 0)
            if user_id in currently_on_duty:
                total += int(time.time() - currently_on_duty[user_id])

            h, r = divmod(total, 3600)
            m, s = divmod(r, 60)

            if h == 0 and m == 0 and s == 0:
                await interaction.response.send_message("Δεν εχεις βαλει καν on duty ηλίθιε!!!")

            await interaction.response.send_message(
                f"⏱ Συνολικος χρονος: **{h}h {m}m {s}s**\nStay HARD!!!’ 💪",
                ephemeral=True
            )

        # =========== ACTIVE STAFF ===========
        elif choice == "Active Staff":
            if not currently_on_duty:
                await interaction.response.send_message("Κανεις δεν εχει βαλει on duty γαμω το σπιτι μου!!!", ephemeral=True)
                return
            
            now = time.time()
            rows = []

            for uid, start in currently_on_duty.items():
                elapsed = int(now - start)
                h, r = divmod(elapsed, 3600)
                m, s = divmod(r, 60)
                user = await bot.fetch_user(uid)
                rows.append(f"**{user.name}** | `{h}h {m}m {s}s`")

            embed = discord.Embed(
                title="🟢 Active Duty Staff",
                description="\n".join(rows),
                color=discord.Color.green()
            )
            embed.set_footer(text="Σφίξτε κώλους, δουλεύετε.")

            await interaction.response.send_message(embed=embed, ephemeral=True)

class DutyPanel(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(DutySelect())

# ==============================
#   DUTY COMMAND
# ==============================
@bot.command()
async def duty(ctx):
    if ctx.channel.id != DUTY_CHANNEL_ID:
        await ctx.send("Πηγεναι στο channel του duty ρε βλακα!! ⚠️", delete_after=4)
        return
    
    embed = discord.Embed(
        title="📋 Duty Panel",
        description="Pick your vibe.",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Stay active king 👑")

    await ctx.send(embed=embed, view=DutyPanel())

# ==============================
#   AUTO OFF DUTY IF MEMBER LEAVES
# ==============================
@bot.event
async def on_member_remove(member):
    user_id = member.id
    if user_id in currently_on_duty:
        start_time = currently_on_duty.pop(user_id)
        elapsed = int(time.time() - start_time)
        total_time[user_id] = total_time.get(user_id, 0) + elapsed
        print(f"{member} left, added {elapsed}s to duty total.")

# ==============================
#   TEMP VOICE SYSTEM
# ==============================
@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == LOBBY_CHANNEL_ID:
        guild = member.guild
        category = after.channel.category

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=False),
            member: discord.PermissionOverwrite(connect=True, speak=True, manage_channels=True)
        }

        new = await guild.create_voice_channel("📲 interview", category=category, overwrites=overwrites)
        temp_channels[new.id] = True
        await member.move_to(new)

    if before.channel and before.channel.id in temp_channels:
        if len(before.channel.members) == 0:
            await before.channel.delete()
            del temp_channels[before.channel.id]

# ==============================
#   YOUR FUN COMMANDS (unchanged)
# ==============================
@bot.command()
async def hello(ctx):
    await ctx.send("Τι γεια ρε μοναχικε μαλακα!!!")

@bot.command()
async def fuck(ctx, member: discord.Member):
    if member.id == 1132432682337435689:
        await ctx.send("Τον μαριο κανεις δεν τον γαμαει, αντε μην σας γαμησο το σπιτι")
    elif member.id == 1384936135679283350:
        await ctx.send("Error: Τα perms για αυτον τον χρηστη ειναι απενεργοποιημενα στην χρηση αυτης της εντολης")
    else:
        await ctx.send(f"Πιπα κολο σε πανε {member.mention}!")

@bot.command()
async def p(ctx, num1: float, op: str, num2: float):
    result = None
    if op == "+": result = num1 + num2
    elif op == "-": result = num1 - num2
    elif op == "*": result = num1 * num2
    elif op == "/":
        if num2 != 0: result = num1 / num2
        else:
            await ctx.send("Βρε ξεκολιαρη ανεργε σχολειο δεν σου μαθαν οτι δεν γινονται διαιρεσης με το 0!!!")
            return
    else:
        await ctx.send(f"Βρε ανυπαντρε αμεα, πως σκατα θα κανω πραξεις με {op}")
        return

    await ctx.send(f"Βρε αρχιδαρα σχολειο δεν πηγες? τοσο κανει: **{result}**")

@bot.command()
async def info(ctx):
    await ctx.send("Εντολες:")
    await ctx.send("  !hello")
    await ctx.send("  !fuck @ονομα χρηστη")
    await ctx.send("  !loop \"Eνα μηνημα\" <εναν αριθμο>")
    await ctx.send("  !p <εναν αριθμο> <ενα συμβολο αριθμομηχανης> <εναν αλο αριθμο>")
    await ctx.send("  Επησης πήγαινε να βαλεις on duty!!")

@bot.command()
async def loop(ctx, text: str, times: int):
    if times > 25:
        await ctx.send("Πολλα δεν θες αμεα, ο υπολιστης του γυφτου θα εκραγη!!!")
        return
    for _ in range(times):
        await ctx.send(text)

# ==============================
#   READY EVENT
# ==============================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    duty_channel = bot.get_channel(DUTY_CHANNEL_ID)
    if duty_channel:
        try:
            await duty_channel.send("📋 Duty Panel Online", view=DutyPanel())
        except:
            pass

# ==============================
#   RUN BOT
# ==============================
token = os.environ.get("DISCORD_TOKEN")
bot.run(token)

