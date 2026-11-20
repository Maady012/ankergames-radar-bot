# AnkerGames Radar Bot

Automated real-time Discord release notifier for [AnkerGames](https://ankergames.net) pre-installed PC games.

## Features
- **Zero Cloudflare Blocks:** High-reliability schema scraping using Schema.org VideoGame JSON-LD + metadata fallback.
- **Categorized Channel Routing:** Automatically sorts games by genres:
  - ⚔️ Action & RPG
  - 👻 Horror & Survival
  - 👥 Co-Op & Multiplayer
  - 🏰 Sim & Strategy
  - 🎨 Indie & Casual
- **Rich Discord Cards:** File size, SteamDB build number, Steam Deck verified badge, and direct links.
- **100% Free 24/7 Hosting Ready:** Zero RAM overhead (uses lightweight Python worker with native Discord Webhooks).

## Deployment Options

### Option 1: Koyeb (100% Free Forever, Always-On)
1. Push this repository to your GitHub.
2. Go to [koyeb.com](https://www.koyeb.com), create a new app from GitHub.
3. Choose `Worker` service, set run command: `python3 worker.py`.
4. Add environment variable `DISCORD_WEBHOOK_URL`.

### Option 2: Render (Free Background Worker)
1. Link your repo to [render.com](https://render.com).
2. Create a **Background Worker**.
3. Build command: `pip install -r requirements.txt`.
4. Start command: `python3 worker.py`.
5. Add `DISCORD_WEBHOOK_URL` in Environment Variables.

### Option 3: Local Termux / Linux Service
```bash
pip install -r requirements.txt
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
python3 worker.py
```
