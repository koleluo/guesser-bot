import discord
from datetime import datetime, timezone
from typing import Optional

TIER_COLORS = {
    "Iron":        0x8e8e8e,
    "Bronze":      0xcd7f32,
    "Silver":      0xc0c0c0,
    "Gold":        0xffd700,
    "Platinum":    0x00e5cc,
    "Emerald":     0x50c878,
    "Diamond":     0x0070dd,
    "Master":      0x9d50bb,
    "Grandmaster": 0xff4444,
    "Challenger":  0x00e5ff,
}

TIER_EMOJIS = {
    "Iron":        "⬛",
    "Bronze":      "\U0001f7eb",
    "Silver":      "⬜",
    "Gold":        "\U0001f7e8",
    "Platinum":    "\U0001fa75",
    "Emerald":     "\U0001f7e9",
    "Diamond":     "\U0001f537",
    "Master":      "\U0001f7e3",
    "Grandmaster": "\U0001f534",
    "Challenger":  "\U0001f3c6",
}


def get_color(tier: str) -> int:
    return TIER_COLORS.get(tier, 0x7289da)


def format_rank(tier: str, division: str) -> str:
    return f"{tier} {division}" if division else tier


def _parse_dt(dt_str: str) -> datetime:
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def clip_submission_embed(
    clip_id: int,
    video_url: str,
    submitter_name: str,
    reveal_at: str,
    guess_count: int,
) -> discord.Embed:
    reveal_ts = int(_parse_dt(reveal_at).timestamp())
    embed = discord.Embed(
        title=f"\U0001f3ae Guess the Rank! — Clip #{clip_id}",
        description=(
            f"**Submitter:** {submitter_name}\n"
            f"**[▶ Watch Clip]({video_url})**\n\n"
            f"What rank is this player? Use `/guess {clip_id}` to submit your guess."
        ),
        color=0x7289da,
    )
    embed.add_field(name="⏱ Reveals", value=f"<t:{reveal_ts}:R>", inline=True)
    embed.add_field(name="\U0001f465 Guesses", value=str(guess_count), inline=True)
    embed.set_footer(text=f"RankBot • Clip #{clip_id}")
    return embed


def reveal_embed(clip: dict, results: list, submitter_name: str) -> discord.Embed:
    tier     = clip["actual_tier"]
    division = clip["actual_rank"]
    full_rank = format_rank(tier, division)
    emoji    = TIER_EMOJIS.get(tier, "\U0001f3ae")

    embed = discord.Embed(
        title=f"\U0001f513 Rank Revealed! — Clip #{clip['id']}",
        description=(
            f"**Submitter:** {submitter_name}\n"
            f"**[▶ Watch Clip]({clip['video_url']})**\n\n"
            f"**Actual Rank: {emoji} {full_rank}**"
        ),
        color=get_color(tier),
    )

    if not results:
        embed.add_field(name="Results", value="No guesses were submitted.", inline=False)
    else:
        exact   = [r for r in results if r["exact_match"]]
        correct = [r for r in results if r["is_correct"] and not r["exact_match"]]
        wrong   = [r for r in results if not r["is_correct"]]

        lines = []
        if exact:
            mentions = " ".join(f"<@{r['guesser_id']}>" for r in exact)
            lines.append(f"⭐ **Exact match (3 pts):** {mentions}")
        if correct:
            mentions = " ".join(f"<@{r['guesser_id']}>" for r in correct)
            lines.append(f"✅ **Correct tier (1 pt):** {mentions}")
        if wrong:
            mentions = " ".join(f"<@{r['guesser_id']}>" for r in wrong)
            lines.append(f"❌ **Wrong (0 pts):** {mentions}")

        embed.add_field(name="Results", value="\n".join(lines), inline=False)
        embed.add_field(name="Total Guesses", value=str(len(results)), inline=True)

    embed.set_footer(text=f"RankBot • Clip #{clip['id']}")
    return embed


def leaderboard_embed(scores: list, scope: str, guild_name: str) -> discord.Embed:
    label = "Weekly" if scope == "weekly" else "All Time"
    embed = discord.Embed(
        title=f"\U0001f3c6 Leaderboard — {label} | {guild_name}",
        color=0xffd700,
    )

    if not scores:
        embed.description = "No scores yet! Start guessing with `/guess`."
        return embed

    medals = ["\U0001f947", "\U0001f948", "\U0001f949"]
    lines  = []
    for i, row in enumerate(scores):
        prefix = medals[i] if i < 3 else f"`{i + 1}.`"
        total  = row["total_guesses"] or 0
        acc    = round(row["correct_guesses"] / total * 100, 1) if total else 0.0
        lines.append(
            f"{prefix} <@{row['user_id']}> — **{row['total_points']} pts** "
            f"| ✅ {row['correct_guesses']} correct "
            f"| ⭐ {row['exact_matches']} exact "
            f"| {acc}% acc"
        )

    embed.description = "\n".join(lines)
    embed.set_footer(text="RankBot • /leaderboard")
    return embed


def profile_embed(user: discord.User, stats: Optional[dict]) -> discord.Embed:
    embed = discord.Embed(
        title=f"\U0001f4ca {user.display_name}'s Stats",
        color=0x7289da,
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    if not stats:
        embed.description = "No stats yet! Start guessing with `/guess`."
    else:
        total = stats["total_guesses"] or 0
        acc   = round(stats["correct_guesses"] / total * 100, 1) if total else 0.0
        embed.add_field(name="Total Guesses",   value=str(stats["total_guesses"]),   inline=True)
        embed.add_field(name="Correct Guesses", value=str(stats["correct_guesses"]), inline=True)
        embed.add_field(name="Accuracy",        value=f"{acc}%",                     inline=True)
        embed.add_field(name="Exact Matches",   value=str(stats["exact_matches"]),   inline=True)
        embed.add_field(name="Total Points",    value=str(stats["total_points"]),     inline=True)

    embed.set_footer(text="RankBot • /profile")
    return embed


def history_embed(clips: list, guild_name: str) -> discord.Embed:
    embed = discord.Embed(
        title=f"\U0001f4dc Recent Clips — {guild_name}",
        color=0x7289da,
    )

    if not clips:
        embed.description = "No revealed clips yet."
        return embed

    lines = []
    for clip in clips:
        full_rank = format_rank(clip["actual_tier"], clip["actual_rank"])
        emoji     = TIER_EMOJIS.get(clip["actual_tier"], "\U0001f3ae")
        lines.append(
            f"**Clip #{clip['id']}** — <@{clip['submitter_id']}> "
            f"| {emoji} **{full_rank}** "
            f"| \U0001f465 {clip['guess_count']} guess(es)"
        )

    embed.description = "\n".join(lines)
    embed.set_footer(text="RankBot • /history")
    return embed
