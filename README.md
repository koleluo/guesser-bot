# Guesser Bot

A Discord bot for gaming servers where members submit gameplay clips with a hidden rank, others guess the rank using buttons, and a leaderboard tracks accuracy over time.

---

## Features

- Submit clips for **League of Legends, Valorant, Counter-Strike 2, or Overwatch 2**
- Rank guessing via **clickable buttons** — no slash command required
- Two-step button flow for ranks with divisions (pick tier → pick division)
- Buttons persist across bot restarts
- Auto-reveal after 24 hours (background task checks every 5 minutes)
- Point scoring: 3pts exact match, 1pt correct tier, 0pts wrong
- Reveal embed shows a **guess distribution** (% of players who picked each rank)
- All-time and weekly leaderboards
- Per-user profile stats with accuracy %

---

## Supported Games & Rank Systems

| Game | Tiers | Divisions |
|---|---|---|
| League of Legends | Iron → Challenger | IV–I (Iron through Diamond) |
| Valorant | Iron → Radiant | 1–3 (Iron through Immortal) |
| Counter-Strike 2 | Silver I → Global Elite | None (18 flat ranks) |
| Overwatch 2 | Bronze → Champion | 5–1 (Bronze through Grandmaster) |

---

## Setup

### 1. Create a Discord Application and Bot

1. Go to [https://discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **New Application** and give it a name
3. In the left sidebar, click **Bot**
4. Click **Add Bot** → **Yes, do it!**
5. Under the bot's username, click **Reset Token** and copy the token — you'll need this for the `.env` file
6. Scroll down to **Privileged Gateway Intents** and leave them all **off**

### 2. Invite the Bot to Your Server

1. In the left sidebar, click **OAuth2** → **URL Generator**
2. Under **Scopes**, check:
   - `bot`
   - `applications.commands`
3. Under **Bot Permissions**, check:
   - `Send Messages`
   - `Embed Links`
   - `Read Message History`
4. Copy the generated URL, open it in your browser, select your server, and click **Authorize**

### 3. Configure the Environment

```bash
git clone https://github.com/lklklk7/guesser-bot.git
cd guesser-bot
cp .env.example .env
```

Open `.env` and replace `your_bot_token_here` with your bot token:

```
BOT_TOKEN=your_actual_token_here
```

### 4. Install Dependencies

Requires Python 3.10+.

```bash
py -m pip install -r requirements.txt
```

### 5. Run the Bot

```bash
py bot.py
```

You should see:
```
Logged in as YourBot#1234 (ID: ...)
Connected to 1 guild(s)
```

Slash commands sync on startup and usually appear in Discord within a minute or two.

---

## Commands

| Command | Description |
|---|---|
| `/submitclip` | Submit a clip. Pick a game, paste the video URL, then type your rank (autocomplete helps). The bot posts the video with rank buttons for others to guess. |
| `/reveal [clip_id]` | Reveal the real rank and score all guesses. Only the submitter or a server admin can do this. |
| `/leaderboard [scope]` | Show the top 10 guessers. Scope: `All Time` (default) or `Weekly`. |
| `/profile [@user]` | Show guessing stats for a user. Defaults to yourself. |
| `/history [limit]` | Show the last N revealed clips in this server (default 5, max 20). |

### How guessing works

There is no `/guess` command. When a clip is submitted, the bot posts it with a row of rank buttons. Click the button for your guess — if that rank has divisions, a second set of buttons appears (ephemeral, only you see it) for you to pick the division.

---

## Scoring

| Result | Points |
|---|---|
| Exact match (correct tier **and** division) | 3 pts |
| Correct tier only | 1 pt |
| Wrong | 0 pts |

For ranks with no division (Master+, Radiant, Global Elite, Champion), matching the tier counts as an exact match.

After revealing, the embed shows a breakdown of how all guessers spread across each rank.

---

## Database

All data is stored in `database.db` (SQLite), created automatically on first run. The file is gitignored. To reset everything, delete it.

If you were running an older version of this bot, the database will be automatically migrated to add the `game` column on next startup — no action needed.

---

## Notes

- The bot checks every **5 minutes** for clips past their 24-hour reveal window and auto-reveals them
- Guess responses are ephemeral — other players can't see what you picked
- Submitters cannot guess on their own clips
- Rank buttons survive bot restarts — any pending clip's buttons will still work after a reboot
