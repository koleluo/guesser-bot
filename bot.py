import os
import discord
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from typing import Optional

import database as db
import embeds as emb
import ranks

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

GAME_CHOICES = [app_commands.Choice(name=g, value=g) for g in ranks.GAME_CHOICES]


# ── button views ───────────────────────────────────────────────────────────────

class TierButton(discord.ui.Button):
    def __init__(self, clip_id: int, game: str, tier: str, label: str, row: int):
        raw = ranks.get_emoji(game, tier)
        emoji = discord.PartialEmoji.from_str(raw) if raw.startswith("<") else raw
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=label,
            emoji=emoji,
            custom_id=f"tier|{clip_id}|{tier}",
            row=row,
        )
        self.clip_id = clip_id
        self.game    = game
        self.tier    = tier

    async def callback(self, interaction: discord.Interaction):
        await _handle_tier(interaction, self.clip_id, self.game, self.tier)


class GuessView(discord.ui.View):
    def __init__(self, clip_id: int, game: str):
        super().__init__(timeout=None)
        tiers  = ranks.get_tiers(game)
        labels = ranks.get_btn_labels(game)
        for i, (tier, label) in enumerate(zip(tiers, labels)):
            self.add_item(TierButton(clip_id, game, tier, label, row=i // 5))




# ── button handlers ────────────────────────────────────────────────────────────

async def _check_guess_eligible(interaction: discord.Interaction, clip_id: int) -> dict | None:
    """Returns the clip dict if guessing is allowed, otherwise sends an error and returns None."""
    clip = await db.get_clip(clip_id)

    if not clip or clip["status"] != "pending":
        await interaction.response.send_message(
            "❌ This clip is no longer accepting guesses.", ephemeral=True
        )
        return None

    if clip["submitter_id"] == interaction.user.id:
        await interaction.response.send_message(
            "❌ You cannot guess on your own clip!", ephemeral=True
        )
        return None

    existing = await db.get_existing_guess(clip_id, interaction.user.id)
    if existing:
        prior = ranks.format_rank(
            clip.get("game", "League of Legends"),
            existing["guessed_tier"], existing["guessed_rank"]
        )
        await interaction.response.send_message(
            f"❌ You already guessed **{prior}** on this clip.", ephemeral=True
        )
        return None

    return dict(clip)


async def _handle_tier(interaction: discord.Interaction, clip_id: int, game: str, tier: str):
    clip = await _check_guess_eligible(interaction, clip_id)
    if clip is None:
        return

    await db.insert_guess(clip_id, interaction.user.id, tier, "")
    await interaction.response.send_message(
        f"✅ Guess locked in: **{ranks.format_rank(game, tier)}**!", ephemeral=True
    )


# ── bot ────────────────────────────────────────────────────────────────────────

class RankBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await db.create_tables()
        # Re-register persistent views for all clips still awaiting guesses
        pending = await db.get_all_pending_clips()
        for clip in pending:
            clip = dict(clip)
            self.add_view(GuessView(clip["id"], clip.get("game", "League of Legends")))
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

    await db.reveal_clip(clip_id)
    clip = dict(clip)

    game = clip.get("game", "League of Legends")
    results = await db.score_and_update_leaderboard(
        clip_id, game, clip["actual_tier"], clip["actual_rank"], clip["guild_id"]
    )

    channel = bot.get_channel(clip["channel_id"])
    if channel is None:
        try:
            channel = await bot.fetch_channel(clip["channel_id"])
        except Exception:
            return

    try:
        submitter      = await bot.fetch_user(clip["submitter_id"])
        submitter_name = submitter.display_name
    except Exception:
        submitter_name = f"User {clip['submitter_id']}"

    await channel.send(embed=emb.reveal_embed(dict(clip), results, submitter_name))

    if clip["message_id"]:
        try:
            msg = await channel.fetch_message(clip["message_id"])
            await msg.edit(embed=emb.revealed_closed_embed(clip_id), view=discord.ui.View())
        except Exception:
            pass


# ── /submitclip ────────────────────────────────────────────────────────────────

@client.tree.command(name="submitclip", description="Submit a gameplay clip — others will guess your rank")
@app_commands.describe(
    game="Which game is this clip from?",
    video_url="Link to the clip",
    rank="Your actual rank (start typing for suggestions)",
)
@app_commands.choices(game=GAME_CHOICES)
async def submit_clip(
    interaction: discord.Interaction,
    game: app_commands.Choice[str],
    video_url: str,
    rank: str,
):
    game_name = game.value
    tier      = rank.strip()
    div       = ""

    valid_tiers = ranks.get_tiers(game_name)
    if tier not in valid_tiers:
        await interaction.response.send_message(
            f"❌ **{tier}** is not a valid {game_name} rank.\nValid options: {', '.join(valid_tiers)}",
            ephemeral=True,
        )
        return

    reveal_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    clip_id   = await db.insert_clip(
        submitter_id=interaction.user.id,
        video_url=video_url,
        game=game_name,
        actual_tier=tier,
        actual_rank=div,
        channel_id=interaction.channel_id,
        guild_id=interaction.guild_id,
        reveal_at=reveal_at,
    )

    view    = GuessView(clip_id, game_name)
    content = emb.submission_content(clip_id, game_name, interaction.user.display_name, reveal_at)
    await interaction.response.send_message(content=f"{content}\n{video_url}", view=view)
    client.add_view(view)  # register for persistence after this message is sent

    msg = await interaction.original_response()
    await db.update_clip_message_id(clip_id, msg.id)


@submit_clip.autocomplete("rank")
async def rank_autocomplete(interaction: discord.Interaction, current: str):
    try:
        game_name = getattr(interaction.namespace, "game", None)
        if not isinstance(game_name, str) or game_name not in ranks.GAMES:
            game_name = "League of Legends"
        tiers = ranks.get_tiers(game_name)
        return [
            app_commands.Choice(name=t, value=t)
            for t in tiers if current.lower() in t.lower()
        ][:25]
    except Exception:
        return []




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
        await interaction.response.send_message(f"❌ Clip #{clip_id} is already revealed.", ephemeral=True)
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
@app_commands.describe(scope="All-time or weekly stats")
@app_commands.choices(scope=[
    app_commands.Choice(name="All Time", value="alltime"),
    app_commands.Choice(name="Weekly",   value="weekly"),
])
async def leaderboard(
    interaction: discord.Interaction,
    scope: Optional[app_commands.Choice[str]] = None,
):
    scope_val = scope.value if scope else "alltime"
    rows      = await (db.get_leaderboard_weekly if scope_val == "weekly" else db.get_leaderboard)(
        interaction.guild_id, limit=10
    )
    embed = emb.leaderboard_embed([dict(r) for r in rows], scope_val, interaction.guild.name)
    await interaction.response.send_message(embed=embed)


# ── /profile ───────────────────────────────────────────────────────────────────

@client.tree.command(name="profile", description="View a user's guessing stats")
@app_commands.describe(user="The user to look up — defaults to yourself")
async def profile(interaction: discord.Interaction, user: Optional[discord.Member] = None):
    target = user or interaction.user
    stats  = await db.get_user_stats(target.id, interaction.guild_id)
    embed  = emb.profile_embed(target, dict(stats) if stats else None)
    await interaction.response.send_message(embed=embed)


# ── /history ───────────────────────────────────────────────────────────────────

@client.tree.command(name="history", description="View recently revealed clips in this server")
@app_commands.describe(limit="Number of clips to show (default 5, max 20)")
async def history(interaction: discord.Interaction, limit: int = 5):
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
