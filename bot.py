import os
import discord
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from typing import Optional

import database as db
import embeds as emb

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

TIERS = [
    "Iron", "Bronze", "Silver", "Gold", "Platinum",
    "Emerald", "Diamond", "Master", "Grandmaster", "Challenger",
]
TIERS_WITH_DIVISION = {"Iron", "Bronze", "Silver", "Gold", "Platinum", "Emerald", "Diamond"}
DIVISIONS = ["I", "II", "III", "IV"]

TIER_CHOICES     = [app_commands.Choice(name=t, value=t) for t in TIERS]
DIVISION_CHOICES = [app_commands.Choice(name=d, value=d) for d in DIVISIONS]


class RankBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await db.create_tables()
        await self.tree.sync()
        self.auto_reveal_loop.start()

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print(f"Connected to {len(self.guilds)} guild(s)")

    @tasks.loop(minutes=5)
    async def auto_reveal_loop(self):
        clips = await db.get_pending_clips_to_reveal()
        for clip in clips:
            try:
                await do_reveal(self, clip["id"])
            except Exception as e:
                print(f"[auto-reveal] Error on clip #{clip['id']}: {e}")

    @auto_reveal_loop.before_loop
    async def before_auto_reveal(self):
        await self.wait_until_ready()


client = RankBot()


# ── shared reveal logic ────────────────────────────────────────────────────────

async def do_reveal(bot: discord.Client, clip_id: int):
    clip = await db.get_clip(clip_id)
    if not clip or clip["status"] != "pending":
        return

    # Mark revealed first to prevent double-runs from the background task
    await db.reveal_clip(clip_id)
    results = await db.score_and_update_leaderboard(
        clip_id, clip["actual_tier"], clip["actual_rank"], clip["guild_id"]
    )

    channel = bot.get_channel(clip["channel_id"])
    if channel is None:
        try:
            channel = await bot.fetch_channel(clip["channel_id"])
        except Exception:
            return

    try:
        submitter = await bot.fetch_user(clip["submitter_id"])
        submitter_name = submitter.display_name
    except Exception:
        submitter_name = f"User {clip['submitter_id']}"

    await channel.send(embed=emb.reveal_embed(dict(clip), results, submitter_name))

    if clip["message_id"]:
        try:
            msg = await channel.fetch_message(clip["message_id"])
            closed = discord.Embed(
                title=f"\U0001f513 Clip #{clip_id} — Revealed!",
                description="This clip has been revealed. Check the message below for results.",
                color=0x2ecc71,
            )
            closed.set_footer(text=f"RankBot • Clip #{clip_id}")
            await msg.edit(embed=closed, view=None)
        except Exception:
            pass


# ── /submitclip ────────────────────────────────────────────────────────────────

@client.tree.command(name="submitclip", description="Submit a gameplay clip for others to guess your rank")
@app_commands.describe(
    video_url="Link to your gameplay clip",
    rank="Your actual rank tier",
    division="Your division — leave empty for Master, Grandmaster, or Challenger",
)
@app_commands.choices(rank=TIER_CHOICES, division=DIVISION_CHOICES)
async def submit_clip(
    interaction: discord.Interaction,
    video_url: str,
    rank: app_commands.Choice[str],
    division: Optional[app_commands.Choice[str]] = None,
):
    tier = rank.value
    div  = division.value if division else ""

    if tier in TIERS_WITH_DIVISION and not div:
        await interaction.response.send_message(
            f"❌ **{tier}** requires a division (I, II, III, or IV).", ephemeral=True
        )
        return

    if tier not in TIERS_WITH_DIVISION:
        div = ""

    reveal_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    clip_id = await db.insert_clip(
        submitter_id=interaction.user.id,
        video_url=video_url,
        actual_tier=tier,
        actual_rank=div,
        channel_id=interaction.channel_id,
        guild_id=interaction.guild_id,
        reveal_at=reveal_at,
    )

    embed = emb.clip_submission_embed(clip_id, video_url, interaction.user.display_name, reveal_at, 0)
    await interaction.response.send_message(embed=embed)

    msg = await interaction.original_response()
    await db.update_clip_message_id(clip_id, msg.id)


# ── /guess ─────────────────────────────────────────────────────────────────────

@client.tree.command(name="guess", description="Guess the rank of a submitted clip")
@app_commands.describe(
    clip_id="The clip ID you want to guess",
    rank="Your rank tier guess",
    division="Your division guess — leave empty for Master and above",
)
@app_commands.choices(rank=TIER_CHOICES, division=DIVISION_CHOICES)
async def guess(
    interaction: discord.Interaction,
    clip_id: int,
    rank: app_commands.Choice[str],
    division: Optional[app_commands.Choice[str]] = None,
):
    clip = await db.get_clip(clip_id)

    if not clip:
        await interaction.response.send_message(f"❌ Clip #{clip_id} does not exist.", ephemeral=True)
        return

    if clip["guild_id"] != interaction.guild_id:
        await interaction.response.send_message("❌ That clip is not from this server.", ephemeral=True)
        return

    if clip["status"] == "revealed":
        await interaction.response.send_message(
            f"❌ Clip #{clip_id} has already been revealed. Guessing is closed.", ephemeral=True
        )
        return

    if clip["submitter_id"] == interaction.user.id:
        await interaction.response.send_message("❌ You cannot guess on your own clip!", ephemeral=True)
        return

    existing = await db.get_existing_guess(clip_id, interaction.user.id)
    if existing:
        prior = emb.format_rank(existing["guessed_tier"], existing["guessed_rank"])
        await interaction.response.send_message(
            f"❌ You already guessed **{prior}** on Clip #{clip_id}.", ephemeral=True
        )
        return

    tier = rank.value
    div  = division.value if division else ""

    if tier in TIERS_WITH_DIVISION and not div:
        await interaction.response.send_message(
            f"❌ **{tier}** requires a division (I, II, III, or IV).", ephemeral=True
        )
        return

    if tier not in TIERS_WITH_DIVISION:
        div = ""

    await db.insert_guess(clip_id, interaction.user.id, tier, div)

    full_rank  = emb.format_rank(tier, div)
    reveal_ts  = int(datetime.fromisoformat(clip["reveal_at"]).timestamp())
    await interaction.response.send_message(
        f"✅ Guess recorded: **{full_rank}** for Clip #{clip_id}.\n"
        f"Results reveal <t:{reveal_ts}:R>.",
        ephemeral=True,
    )


# ── /reveal ────────────────────────────────────────────────────────────────────

@client.tree.command(name="reveal", description="Reveal the rank of a clip and score all guesses")
@app_commands.describe(clip_id="The clip ID to reveal")
async def reveal(interaction: discord.Interaction, clip_id: int):
    clip = await db.get_clip(clip_id)

    if not clip:
        await interaction.response.send_message(f"❌ Clip #{clip_id} does not exist.", ephemeral=True)
        return

    if clip["guild_id"] != interaction.guild_id:
        await interaction.response.send_message("❌ That clip is not from this server.", ephemeral=True)
        return

    if clip["status"] == "revealed":
        await interaction.response.send_message(
            f"❌ Clip #{clip_id} has already been revealed.", ephemeral=True
        )
        return

    is_admin     = isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator
    is_submitter = clip["submitter_id"] == interaction.user.id

    if not is_admin and not is_submitter:
        await interaction.response.send_message(
            "❌ Only the clip submitter or a server admin can reveal this clip.", ephemeral=True
        )
        return

    await interaction.response.defer(thinking=True)
    await do_reveal(client, clip_id)
    await interaction.followup.send(f"✅ Clip #{clip_id} has been revealed!", ephemeral=True)


# ── /leaderboard ───────────────────────────────────────────────────────────────

@client.tree.command(name="leaderboard", description="View the rank guessing leaderboard")
@app_commands.describe(scope="View all-time or weekly performance")
@app_commands.choices(scope=[
    app_commands.Choice(name="All Time", value="alltime"),
    app_commands.Choice(name="Weekly",   value="weekly"),
])
async def leaderboard(
    interaction: discord.Interaction,
    scope: Optional[app_commands.Choice[str]] = None,
):
    scope_val = scope.value if scope else "alltime"

    if scope_val == "weekly":
        rows = await db.get_leaderboard_weekly(interaction.guild_id, limit=10)
    else:
        rows = await db.get_leaderboard(interaction.guild_id, limit=10)

    scores = [dict(r) for r in rows]
    embed  = emb.leaderboard_embed(scores, scope_val, interaction.guild.name)
    await interaction.response.send_message(embed=embed)


# ── /profile ───────────────────────────────────────────────────────────────────

@client.tree.command(name="profile", description="View a user's rank guessing stats")
@app_commands.describe(user="The user to view — defaults to yourself")
async def profile(
    interaction: discord.Interaction,
    user: Optional[discord.Member] = None,
):
    target = user or interaction.user
    stats  = await db.get_user_stats(target.id, interaction.guild_id)
    embed  = emb.profile_embed(target, dict(stats) if stats else None)
    await interaction.response.send_message(embed=embed)


# ── /history ───────────────────────────────────────────────────────────────────

@client.tree.command(name="history", description="View recently revealed clips in this server")
@app_commands.describe(limit="Number of clips to show (default: 5, max: 20)")
async def history(
    interaction: discord.Interaction,
    limit: int = 5,
):
    limit = max(1, min(limit, 20))
    clips = await db.get_history(interaction.guild_id, limit)
    embed = emb.history_embed([dict(c) for c in clips], interaction.guild.name)
    await interaction.response.send_message(embed=embed)


# ── entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is not set. Copy .env.example to .env and add your token.")
        raise SystemExit(1)
    client.run(BOT_TOKEN)
