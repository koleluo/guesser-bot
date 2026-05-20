import discord
from datetime import datetime, timezone
from typing import Optional

import ranks


def _parse_dt(dt_str: str) -> datetime:
    dt = datetime.fromisoformat(dt_str)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# ── submission ─────────────────────────────────────────────────────────────────

def submission_content(clip_id: int, game: str, submitter_name: str, reveal_at: str) -> str:
    """Plain-text content for the submission message (Discord auto-embeds the URL)."""
    ts = int(_parse_dt(reveal_at).timestamp())
    return (
        f"\U0001f3ae **{game} — Clip #{clip_id}**\n"
        f"Submitted by **{submitter_name}** | Reveals <t:{ts}:R>\n"
        f"Click a button below to guess the rank!"
    )


# ── reveal ─────────────────────────────────────────────────────────────────────

def reveal_embed(clip: dict, results: list, submitter_name: str) -> discord.Embed:
    game      = clip.get("game", "League of Legends")
    tier      = clip["actual_tier"]
    division  = clip["actual_rank"]
    full_rank = ranks.format_rank(game, tier, division)
    emoji     = ranks.get_emoji(game, tier)

    embed = discord.Embed(
        title=f"\U0001f513 {game} — Clip #{clip['id']} Revealed!",
        color=ranks.get_color(game, tier),
    )
    embed.add_field(name="Real Rank",    value=f"{emoji} **{full_rank}**", inline=True)
    embed.add_field(name="Submitted by", value=submitter_name,             inline=True)
    embed.add_field(name="Guesses",      value=str(len(results)),          inline=True)

    if results:
        # Score breakdown
        exact   = [r for r in results if r["exact_match"]]
        correct = [r for r in results if r["is_correct"] and not r["exact_match"]]
        wrong   = [r for r in results if not r["is_correct"]]

        lines = []
        if exact:
            lines.append("⭐ **Exact match (3 pts):** " + " ".join(f"<@{r['guesser_id']}>" for r in exact))
        if correct:
            lines.append("✅ **Correct tier (1 pt):** " + " ".join(f"<@{r['guesser_id']}>" for r in correct))
        if wrong:
            lines.append("❌ **Wrong (0 pts):** " + " ".join(f"<@{r['guesser_id']}>" for r in wrong))

        embed.add_field(name="Results", value="\n".join(lines), inline=False)

        # Guess distribution — show % per tier across all tiers
        all_tiers = ranks.get_tiers(game)
        counts: dict[str, int] = {}
        for r in results:
            counts[r["guessed_tier"]] = counts.get(r["guessed_tier"], 0) + 1

        total = len(results)
        dist_parts = []
        for t in all_tiers:
            if counts.get(t, 0) > 0:
                pct  = round(counts[t] / total * 100, 1)
                em   = ranks.get_emoji(game, t)
                dist_parts.append(f"{em} {t}: **{pct}%**")

        if dist_parts:
            # 3 columns per row
            rows = [dist_parts[i:i+3] for i in range(0, len(dist_parts), 3)]
            embed.add_field(
                name="How everyone guessed:",
                value="\n".join("  │  ".join(row) for row in rows),
                inline=False,
            )

    embed.set_footer(text=f"GuesserBot • Clip #{clip['id']}")
    return embed


def revealed_closed_embed(clip_id: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"\U0001f513 Clip #{clip_id} — Revealed!",
        description="Guessing is closed. See the results below.",
        color=0x2ecc71,
    )
    embed.set_footer(text=f"GuesserBot • Clip #{clip_id}")
    return embed


# ── leaderboard ────────────────────────────────────────────────────────────────

def leaderboard_embed(scores: list, scope: str, guild_name: str) -> discord.Embed:
    label = "Weekly" if scope == "weekly" else "All Time"
    embed = discord.Embed(
        title=f"\U0001f3c6 Leaderboard — {label} | {guild_name}",
        color=0xffd700,
    )

    if not scores:
        embed.description = "No scores yet! Submit a clip to get started."
        return embed

    medals = ["\U0001f947", "\U0001f948", "\U0001f949"]
    lines  = []
    for i, row in enumerate(scores):
        prefix = medals[i] if i < 3 else f"`{i + 1}.`"
        total  = row["total_guesses"] or 0
        acc    = round(row["correct_guesses"] / total * 100, 1) if total else 0.0
        lines.append(
            f"{prefix} <@{row['user_id']}> — **{row['total_points']} pts**  "
            f"| ✅ {row['correct_guesses']}  "
            f"| ⭐ {row['exact_matches']}  "
            f"| {acc}% acc"
        )

    embed.description = "\n".join(lines)
    embed.set_footer(text="GuesserBot • /leaderboard")
    return embed


# ── profile ────────────────────────────────────────────────────────────────────

def profile_embed(user: discord.User, stats: Optional[dict]) -> discord.Embed:
    embed = discord.Embed(title=f"\U0001f4ca {user.display_name}'s Stats", color=0x7289da)
    embed.set_thumbnail(url=user.display_avatar.url)

    if not stats:
        embed.description = "No stats yet!"
    else:
        total = stats["total_guesses"] or 0
        acc   = round(stats["correct_guesses"] / total * 100, 1) if total else 0.0
        embed.add_field(name="Total Guesses",   value=str(stats["total_guesses"]),   inline=True)
        embed.add_field(name="Correct",         value=str(stats["correct_guesses"]), inline=True)
        embed.add_field(name="Accuracy",        value=f"{acc}%",                     inline=True)
        embed.add_field(name="Exact Matches",   value=str(stats["exact_matches"]),   inline=True)
        embed.add_field(name="Total Points",    value=str(stats["total_points"]),     inline=True)

    embed.set_footer(text="GuesserBot • /profile")
    return embed


# ── history ────────────────────────────────────────────────────────────────────

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
        game      = clip.get("game", "?")
        full_rank = ranks.format_rank(game, clip["actual_tier"], clip["actual_rank"])
        emoji     = ranks.get_emoji(game, clip["actual_tier"])
        lines.append(
            f"**Clip #{clip['id']}** — {game} — <@{clip['submitter_id']}> "
            f"| {emoji} **{full_rank}** | \U0001f465 {clip['guess_count']}"
        )

    embed.description = "\n".join(lines)
    embed.set_footer(text="GuesserBot • /history")
    return embed
