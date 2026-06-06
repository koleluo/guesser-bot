# Guesser Bot

A Discord bot for gaming servers where members submit gameplay clips with a hidden rank, others guess the rank by clicking a button, and a leaderboard tracks accuracy over time.

---

## Screenshots

> Replace the images below with your own screenshots. Drop the files into a `screenshots/` folder in the repo and update the paths.

| Submitting a Clip | Rank Guess Buttons | Reveal & Results |
|:---:|:---:|:---:|
| ![Submitting a clip](https://cdn.discordapp.com/attachments/1512542345646571614/1512646418861527130/image.png?ex=6a24d941&is=6a2387c1&hm=f221aa667fad9b7f167c7ad8bb6fe9553164d76e89eb51b9cada51687cc6044d&) | ![Rank guess buttons](https://cdn.discordapp.com/attachments/1512542345646571614/1512647317931557105/image.png?ex=6a24da18&is=6a238898&hm=76e577259a2d8b93fa2f9fbc471d61d52d1f4139e9fa33e160f9070ff8cd4c09&)|

---

## Features

- Submit clips for **League of Legends, Valorant, Counter-Strike 2 (FACEIT), or Overwatch 2**
- Rank guessing via **one-click buttons** with custom rank emoji icons — no slash command needed
- Clip submitter is **anonymous** until the reveal
- Buttons persist across bot restarts
- Auto-reveal after 24 hours (background task checks every 5 minutes)
- Point scoring: **3 pts** for correct rank, **0 pts** for wrong
- Reveal embed shows a **guess distribution** (% of players who picked each rank)
- All-time and weekly leaderboards
- Per-user profile stats with accuracy %

---

## Supported Games & Ranks

| Game | Ranks |
|---|---|
| League of Legends | Iron, Bronze, Silver, Gold, Platinum, Emerald, Diamond, Master, Grandmaster, Challenger |
| Valorant | Iron, Bronze, Silver, Gold, Platinum, Diamond, Ascendant, Immortal, Radiant |
| Counter-Strike 2 | FACEIT Level 1 – Level 10 |
| Overwatch 2 | Bronze, Silver, Gold, Platinum, Diamond, Master, Grandmaster, Champion |

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
Synced commands to YourServer
```

Slash commands sync automatically on startup.

---

## Commands

| Command | Description |
|---|---|
| `/submitclip` | Submit a clip. Pick a game, paste the video URL, then type your rank (autocomplete will suggest valid options). The bot posts the video anonymously with rank buttons for others to guess. |
| `/reveal [clip_id]` | Reveal the real rank and score all guesses. Only the submitter or a server admin can do this. |
| `/leaderboard [scope]` | Show the top 10 guessers. Scope: `All Time` (default) or `Weekly`. |
| `/profile [@user]` | Show guessing stats for a user. Defaults to yourself. |
| `/history [limit]` | Show the last N revealed clips in this server (default 5, max 20). |

### How guessing works

There is no `/guess` command. When a clip is submitted, the bot posts it with a row of rank buttons. Click the button for your rank guess — it's locked in immediately. Your guess is private (ephemeral) so other players can't see it. The submitter's identity is hidden until the reveal.

---

## Scoring

| Result | Points |
|---|---|
| Correct rank | 3 pts |
| Wrong | 0 pts |

After revealing, the embed shows a breakdown of what percentage of guessers picked each rank.

---

## Database

All data is stored in `database.db` (SQLite), created automatically on first run. The file is gitignored. To reset everything, delete it.

---

## Notes

- The bot checks every **5 minutes** for clips past their 24-hour reveal window and auto-reveals them
- Guess responses are ephemeral — other players can't see what you picked
- Submitters cannot guess on their own clips
- Rank buttons survive bot restarts — pending clips stay interactive after a reboot
- Custom rank emoji icons are supported for all four games
