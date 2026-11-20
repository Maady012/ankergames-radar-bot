import os
import json
import logging
import urllib.request
import time
import random
from typing import Set, Dict

from scraper import fetch_recent_game_urls, parse_game_page
from discord_dispatcher import create_discord_payload, send_bot_message
from free_games import fetch_epic_free_games, create_free_game_payload

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

SEEN_FILE = os.environ.get('SEEN_FILE', 'seen_games.json')
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')
GUILD_ID = os.environ.get('GUILD_ID', '643124604914630656')
CYCLE_MAX_DURATION = int(os.environ.get('CYCLE_MAX_DURATION', '19800'))  # ~5.5 hours per runner

def get_channel_mapping(bot_token: str, guild_id: str) -> Dict[str, str]:
    url = f"https://discord.com/api/v10/guilds/{guild_id}/channels"
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': f'Bot {bot_token}',
            'User-Agent': 'DiscordBot (https://github.com/Maady012, 1.0)'
        }
    )
    mapping = {}
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            channels = json.loads(resp.read().decode('utf-8'))
            for c in channels:
                mapping[c['name']] = c['id']
    except Exception as e:
        logging.error(f"Error fetching guild channels: {e}")
    return mapping

def load_seen_games() -> Set[str]:
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception as e:
            logging.error(f"Error loading {SEEN_FILE}: {e}")
    return set()

def save_seen_games(seen: Set[str]):
    try:
        trimmed = list(seen)[-3000:]
        with open(SEEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(trimmed, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving {SEEN_FILE}: {e}")

def run_single_scan(channels: Dict[str, str], seen: Set[str], seen_slugs: Set[str]) -> int:
    all_releases_ch = channels.get('📢-all-releases')
    free_games_ch = channels.get('🎁-free-games')
    new_count = 0

    # 1. Check Epic Games Free Promotions
    try:
        epic_games = fetch_epic_free_games()
        for fg in epic_games:
            fg_id = fg['id']
            if fg_id not in seen:
                logging.info(f"🎁 NEW EPIC FREE GIVEAWAY: {fg['title']}")
                payload = create_free_game_payload(fg)
                
                # A) Post into #🎁-free-games
                if free_games_ch:
                    send_bot_message(DISCORD_BOT_TOKEN, free_games_ch, payload)
                    time.sleep(1)

                # B) ALSO mirror into #📢-all-releases
                if all_releases_ch:
                    send_bot_message(DISCORD_BOT_TOKEN, all_releases_ch, payload)
                    time.sleep(1)

                seen.add(fg_id)
                new_count += 1
    except Exception as e:
        logging.error(f"Error checking free games: {e}")

    # 2. Check AnkerGames Releases & Updates
    urls = fetch_recent_game_urls()
    if not urls:
        return new_count

    for url in reversed(urls):
        slug = url.rstrip('/').split('/')[-1]
        game_data = parse_game_page(url)
        if not game_data:
            continue

        game_id = game_data['id']
        actual_slug = game_data.get('slug', slug)

        if game_id in seen:
            continue

        is_update = (actual_slug in seen_slugs)
        status_text = "BUILD UPDATE" if is_update else "NEW GAME"
        logging.info(f"✨ {status_text} DETECTED: {game_data['title']} (Build: {game_data['build']})")

        dispatch_info = create_discord_payload(game_data, is_update=is_update)
        payload = dispatch_info['payload']
        target_name = dispatch_info['target_channel']
        target_ch_id = channels.get(target_name)

        # A) Post into #📢-all-releases
        if all_releases_ch:
            send_bot_message(DISCORD_BOT_TOKEN, all_releases_ch, payload)
            time.sleep(1)

        # B) Post into its specific folder category channel
        if target_ch_id and target_ch_id != all_releases_ch:
            send_bot_message(DISCORD_BOT_TOKEN, target_ch_id, payload)
            time.sleep(1)

        seen.add(game_id)
        seen_slugs.add(actual_slug)
        new_count += 1

    return new_count

def main_continuous_loop():
    if not DISCORD_BOT_TOKEN:
        logging.error("DISCORD_BOT_TOKEN is not set.")
        return

    logging.info("🚀 Starting AnkerGames Radar 24/7 Continuous Polling Loop...")
    start_time = time.time()
    channels = get_channel_mapping(DISCORD_BOT_TOKEN, GUILD_ID)
    seen = load_seen_games()
    seen_slugs = {entry.split(':')[0] for entry in seen}

    logging.info(f"Loaded {len(seen)} previously indexed game versions ({len(seen_slugs)} unique titles).")

    # Initial scan immediately on startup
    initial_new = run_single_scan(channels, seen, seen_slugs)
    if initial_new > 0:
        save_seen_games(seen)

    last_scan_time = time.time()
    scan_interval = random.randint(120, 180)  # Every 2 to 3 minutes

    while time.time() - start_time < CYCLE_MAX_DURATION:
        time.sleep(2)
        if time.time() - last_scan_time >= scan_interval:
            last_scan_time = time.time()
            scan_interval = random.randint(120, 180)
            try:
                # Refresh channel mapping periodically if empty
                if not channels:
                    channels = get_channel_mapping(DISCORD_BOT_TOKEN, GUILD_ID)

                new_found = run_single_scan(channels, seen, seen_slugs)
                if new_found > 0:
                    save_seen_games(seen)
                    logging.info(f"Dispatched {new_found} new releases. State saved.")
                else:
                    logging.info(f"Heartbeat scan complete. Library up to date ({len(seen)} indexed).")
            except Exception as e:
                logging.error(f"Scan loop error: {e}")

    save_seen_games(seen)
    logging.info("Worker completed 5.5 hour cycle. Exiting for scheduled seamless handoff.")

if __name__ == '__main__':
    main_continuous_loop()
