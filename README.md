# CF Tracker Bot 🏆

A Discord bot that tracks Codeforces handles and sends daily performance reports to your server.

## Features
- Daily automated reports at a custom time
- Tracks problems solved in the last 24 hours and 7 days
- Shows current rating and rank for each handle
- Per-server settings stored in PostgreSQL
- Supports both slash commands (`/add`) and prefix commands (`!add`)

## Commands

| Command | Description | Permission |
|---|---|---|
| `/add <handle>` | Add a CF handle to track | Everyone |
| `/remove <handle>` | Remove a CF handle | Everyone |
| `/list` | List all tracked handles | Everyone |
| `/report` | Trigger an instant report | Everyone |
| `/setchannel #channel` | Set the report channel | Admin |
| `/settime <hour>` | Set report hour in UTC (0–23) | Admin |

All commands also work with the `!` prefix (e.g. `!add tourist`).

## Add to Your Server

Click the link below to add CF Tracker Bot to your Discord server:

[**Invite CF Tracker Bot**](https://discord.com/oauth2/authorize?client_id=1502250829002838056&permissions=84992&scope=bot+applications.commands)

After adding the bot, run these commands to get started:
```
!setchannel #your-channel
!settime 3
!add your_cf_handle
!report
```

## Self Hosting

### Requirements
- Python 3.11
- PostgreSQL database

### Setup
1. Clone the repo:
   ```bash
   git clone https://github.com/yourusername/cf-tracker-bot
   cd cf-tracker-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   export DISCORD_TOKEN=your_bot_token
   export DATABASE_URL=your_postgresql_url
   ```

4. Run:
   ```bash
   python bot.py
   ```

### Deploy on Railway
1. Fork this repo
2. Create a new project on [Railway](https://railway.app)
3. Add a **PostgreSQL** database service
4. Add your GitHub repo as a service
5. Set environment variables:
   - `DISCORD_TOKEN` — your Discord bot token
   - `DATABASE_URL` — your PostgreSQL public URL
6. Railway will auto-deploy using the `Procfile`

## Tech Stack
- [discord.py](https://discordpy.readthedocs.io/) — Discord API wrapper
- [psycopg2](https://www.psycopg.org/) — PostgreSQL driver
- [APScheduler](https://apscheduler.readthedocs.io/) — task scheduler
- [Codeforces API](https://codeforces.com/apiHelp) — CF data
