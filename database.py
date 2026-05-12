import aiosqlite
from datetime import datetime, timedelta, timezone

DB_PATH = "database.db"

TIERS_WITH_DIVISION = {"Iron", "Bronze", "Silver", "Gold", "Platinum", "Emerald", "Diamond"}


async def create_tables():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS clips (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                submitter_id INTEGER NOT NULL,
                video_url    TEXT    NOT NULL,
                actual_tier  TEXT    NOT NULL,
                actual_rank  TEXT    NOT NULL DEFAULT '',
                channel_id   INTEGER NOT NULL,
                message_id   INTEGER,
                guild_id     INTEGER NOT NULL,
                status       TEXT    NOT NULL DEFAULT 'pending',
                submitted_at TEXT    NOT NULL,
                reveal_at    TEXT    NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS guesses (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                clip_id        INTEGER NOT NULL,
                guesser_id     INTEGER NOT NULL,
                guessed_tier   TEXT    NOT NULL,
                guessed_rank   TEXT    NOT NULL DEFAULT '',
                is_correct     INTEGER NOT NULL DEFAULT 0,
                exact_match    INTEGER NOT NULL DEFAULT 0,
                points_awarded INTEGER NOT NULL DEFAULT 0,
                guessed_at     TEXT    NOT NULL,
                FOREIGN KEY (clip_id) REFERENCES clips(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS leaderboard (
                user_id         INTEGER NOT NULL,
                guild_id        INTEGER NOT NULL,
                total_guesses   INTEGER NOT NULL DEFAULT 0,
                correct_guesses INTEGER NOT NULL DEFAULT 0,
                exact_matches   INTEGER NOT NULL DEFAULT 0,
                total_points    INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        await db.commit()


async def insert_clip(submitter_id, video_url, actual_tier, actual_rank, channel_id, guild_id, reveal_at):
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO clips
               (submitter_id, video_url, actual_tier, actual_rank, channel_id, guild_id, submitted_at, reveal_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (submitter_id, video_url, actual_tier, actual_rank, channel_id, guild_id, now, reveal_at),
        )
        await db.commit()
        return cursor.lastrowid


async def update_clip_message_id(clip_id, message_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE clips SET message_id = ? WHERE id = ?", (message_id, clip_id))
        await db.commit()


async def get_clip(clip_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM clips WHERE id = ?", (clip_id,))
        return await cursor.fetchone()


async def get_pending_clips_to_reveal():
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM clips WHERE status = 'pending' AND reveal_at <= ?", (now,)
        )
        return await cursor.fetchall()


async def reveal_clip(clip_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE clips SET status = 'revealed' WHERE id = ?", (clip_id,))
        await db.commit()


async def insert_guess(clip_id, guesser_id, guessed_tier, guessed_rank):
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO guesses (clip_id, guesser_id, guessed_tier, guessed_rank, guessed_at)
               VALUES (?, ?, ?, ?, ?)""",
            (clip_id, guesser_id, guessed_tier, guessed_rank, now),
        )
        await db.commit()
        return cursor.lastrowid


async def get_existing_guess(clip_id, guesser_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM guesses WHERE clip_id = ? AND guesser_id = ?", (clip_id, guesser_id)
        )
        return await cursor.fetchone()


async def get_clip_guess_count(clip_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM guesses WHERE clip_id = ?", (clip_id,))
        row = await cursor.fetchone()
        return row[0] if row else 0


async def score_and_update_leaderboard(clip_id, actual_tier, actual_rank, guild_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM guesses WHERE clip_id = ?", (clip_id,))
        guesses = await cursor.fetchall()

        results = []
        for guess in guesses:
            tier_match = guess["guessed_tier"].lower() == actual_tier.lower()
            no_division = actual_rank == ""
            rank_match = guess["guessed_rank"].lower() == actual_rank.lower()

            exact   = tier_match and (rank_match or no_division)
            correct = tier_match
            points  = 3 if exact else (1 if correct else 0)

            await db.execute(
                "UPDATE guesses SET is_correct = ?, exact_match = ?, points_awarded = ? WHERE id = ?",
                (1 if correct else 0, 1 if exact else 0, points, guess["id"]),
            )

            await db.execute(
                """INSERT INTO leaderboard (user_id, guild_id, total_guesses, correct_guesses, exact_matches, total_points)
                   VALUES (?, ?, 1, ?, ?, ?)
                   ON CONFLICT(user_id, guild_id) DO UPDATE SET
                       total_guesses   = total_guesses   + 1,
                       correct_guesses = correct_guesses + ?,
                       exact_matches   = exact_matches   + ?,
                       total_points    = total_points    + ?""",
                (
                    guess["guesser_id"], guild_id,
                    1 if correct else 0, 1 if exact else 0, points,
                    1 if correct else 0, 1 if exact else 0, points,
                ),
            )

            results.append({
                "guesser_id":   guess["guesser_id"],
                "guessed_tier": guess["guessed_tier"],
                "guessed_rank": guess["guessed_rank"],
                "is_correct":   correct,
                "exact_match":  exact,
                "points":       points,
            })

        await db.commit()
        return results


async def get_leaderboard(guild_id, limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM leaderboard
               WHERE guild_id = ?
               ORDER BY total_points DESC, exact_matches DESC, correct_guesses DESC
               LIMIT ?""",
            (guild_id, limit),
        )
        return await cursor.fetchall()


async def get_leaderboard_weekly(guild_id, limit=10):
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT
                   g.guesser_id          AS user_id,
                   COUNT(g.id)           AS total_guesses,
                   SUM(g.is_correct)     AS correct_guesses,
                   SUM(g.exact_match)    AS exact_matches,
                   SUM(g.points_awarded) AS total_points
               FROM guesses g
               JOIN clips c ON g.clip_id = c.id
               WHERE c.guild_id = ? AND g.guessed_at >= ? AND c.status = 'revealed'
               GROUP BY g.guesser_id
               ORDER BY total_points DESC, exact_matches DESC, correct_guesses DESC
               LIMIT ?""",
            (guild_id, week_ago, limit),
        )
        return await cursor.fetchall()


async def get_user_stats(user_id, guild_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM leaderboard WHERE user_id = ? AND guild_id = ?", (user_id, guild_id)
        )
        return await cursor.fetchone()


async def get_history(guild_id, limit=5):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT c.*, COUNT(g.id) AS guess_count
               FROM clips c
               LEFT JOIN guesses g ON c.id = g.clip_id
               WHERE c.guild_id = ? AND c.status = 'revealed'
               GROUP BY c.id
               ORDER BY c.submitted_at DESC
               LIMIT ?""",
            (guild_id, limit),
        )
        return await cursor.fetchall()
