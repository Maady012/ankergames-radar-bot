# Project Context & Architecture

**Project:** AnkerGames Radar Bot & Discord Gaming Hub  
**Owner:** Maady012  
**Repository:** [github.com/Maady012/ankergames-radar-bot](https://github.com/Maady012/ankergames-radar-bot)  
**Discord Server (Guild):** `SK` (`643124604914630656`)  
**Bot Client:** `AnkerGames Radar` (App ID `1573202327454752788`)  
**Hardware Profile:** MSI Katana GF66 12UC-881IN (i5-12450H, RTX 3050 Laptop 4GB, 1080p 144Hz)  

---

## 1. System Components

- **`scraper.py`**:
  - Scrapes `ankergames.net/games-list`.
  - Extracts Schema.org VideoGame JSON-LD, game cover, version, size, and build numbers.
  - Queries Valve Steam Store API for official publisher genres, player ratings, and PC hardware requirements.
  - Benchmarks games against user's MSI Katana GF66 laptop specs.
  - Scrapes top player review from Steam Community.

- **`free_games.py`**:
  - Scrapes 100% free limited-time game promotions from Epic Games Store API.
  - Formats claim alerts with original price, claim countdown, and direct link.

- **`discord_dispatcher.py`**:
  - Intelligently routes games into category channels using Steam genres + title keywords.
  - Distinguishes `✨ [NEW RELEASE]` vs `🔄 [BUILD UPDATE]` with color bars.
  - Formats Discord cards with 4-screenshot collage grids, specs, and action buttons (`AnkerGames`, `Steam`, `TorBox Cloud`).

- **`run_once.py`**:
  - Orchestrates the radar scan cycle for both AnkerGames and Epic Games.
  - Posts to `#📢-all-releases` (unified feed) and dedicated category channels in parallel.
  - Updates and trims `seen_games.json`.

---

## 2. Server Channel Directory

- **`💬 COMMUNITY HUB`**:
  - `#💬-chat`, `#🎁-free-games`, `#🎯-valorant`, `#⚙️-nvidia-updates`, `#📺-youtube`
- **`🎮 ANKERGAMES RADAR`**:
  - `#📢-all-releases` (Unified stream for all games, updates & giveaways)
  - `#🏰-sim-strategy` (Simulators, Tycoons, Management)
  - `#⚔️-action-rpg` (Action, RPG, Shooters, Combat)
  - `#🔍-adventure-mystery` (Story-rich, Detective, Narrative)
  - `#🏎️-sports-racing` (Racing & Sports)
  - `#👻-horror-survival` (Horror & Survival)
  - `#🎨-indie-casual` (Indie, 2D, Cozy)
- **`🔊 VOICE LOUNGE`**:
  - Voice channels

---

## 3. Automation & Quota Specs
- Runs every 10 minutes on GitHub Actions (`.github/workflows/radar.yml`).
- Average runtime: 15–20 seconds per run.
- Zero extra bandwidth/memory overhead.
- Native Discord AutoMod Active: Phishing link blocker + mass mention anti-raid shield with 1-hour user timeouts.
