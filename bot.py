import os
import discord
from discord import app_commands
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

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print(f"Connected to {len(self.guilds)} guild(s)")


client = RankBot()


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


# ── entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN is not set. Copy .env.example to .env and add your token.")
        raise SystemExit(1)
    client.run(BOT_TOKEN)
