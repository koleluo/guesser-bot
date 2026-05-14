# Rank Guess Bot

A Discord bot for gaming servers where members submit gameplay clips with a hidden rank, others guess the rank, and a leaderboard tracks accuracy over time.

---

## Features

- Submit clips with a hidden LoL rank
- Others guess using dropdown slash commands
- Auto-reveal after 24 hours (background task runs every 5 minutes)
- Point scoring: 3pts exact match, 1pt correct tier, 0pts wrong
- All-time and weekly leaderboards
- Per-user profile stats with accuracy %
- Color-coded embeds per rank tier

---

## Setup

### 1. Create a Discord Application and Bot

1. Go to [https://discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **New Application** and give it a name (e.g. `RankGuessBot`)
3. In the left sidebar, click **Bot**
4. Click **Add Bot** → **Yes, do it!**
5. Under the bot's username, click **Reset Token** and copy the token — you'll need this for the `.env` file
6. Scroll down to **Privileged Gateway Intents** and leave them all **off** (this bot doesn't need any)

### 2. Invite the Bot to Your Server

1. In the left sidebar, click **OAuth2** → **URL Generator**
2. Under **Scopes**, check:
   - `bot`
   - `applications.commands`
3. Under **Bot Permissions**, check:
   - `Send Messages`
   - `Embed Links`
   - `Read Message History`
4. Copy the generated URL at the bottom and open it in your browser
5. Select your server and click **Authorize**

### 3. Configure the Environment

```bash
# Clone the repo and navigate into it
git clone https://github.com/lklklk7/guesser-bot.git
cd guesser-bot

# Copy the example env file
cp .env.example .env
```

Open `.env` and replace `your_bot_token_here` with the token you copied in step 1:

```
BOT_TOKEN=your_actual_token_here
```

### 4. Install Dependencies

Make sure you have Python 3.10+ installed, then:

```bash
pip install -r requirements.txt
```

### 5. Run the Bot

```bash
python bot.py
```

You should see:
```
Logged in as RankGuessBot#1234 (ID: ...)
Connected to 1 guild(s)
```

Slash commands are synced globally on startup. Discord may take up to an hour to propagate them to all clients, but they usually appear within a minute or two.

---

## Commands

| Command | Description |
|---|---|
| `/submitclip [video_url] [rank] [division]` | Submit a clip with your hidden rank. Division is optional for Master and above. |
| `/guess [clip_id] [rank] [division]` | Guess the rank on a clip. Response is ephemeral (only you can see it). |
| `/reveal [clip_id]` | Reveal the real rank and score all guesses. Only the submitter or an admin can use this. |
| `/leaderboard [scope]` | Show the top 10 guessers. Scope: `All Time` (default) or `Weekly`. |
| `/profile [@user]` | Show guessing stats for a user. Defaults to yourself. |
| `/history [limit]` | Show the last N revealed clips (default 5, max 20). |

---

## Scoring

| Result | Points |
|---|---|
| Exact match (correct tier **and** division) | 3 pts |
| Correct tier only | 1 pt |
| Wrong | 0 pts |

For **Master, Grandmaster, and Challenger** (which have no division), any correct tier guess counts as an exact match.

---

## Database

All data is stored in `database.db` (SQLite), created automatically on first run. The file is gitignored. To reset everything, delete it.

---

## Notes

- The bot checks for clips past their 24-hour window every **5 minutes** and auto-reveals them
- Guesses are hidden from other users (ephemeral responses)
- Submitters cannot guess on their own clips
