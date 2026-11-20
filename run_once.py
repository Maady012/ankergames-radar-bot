import os
import json
import logging
import urllib.request
import time
from typing import Set, Dict

from scraper import fetch_recent_game_urls, parse_game_page
from discord_dispatcher import create_discord_payload, send_bot_message

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

SEEN_FILE = os.environ.get('SEEN_FILE', 'seen_games.json')
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN', '')
GUILD_ID = os.environ.get('GUILD_ID', '643124604914630656')

def get_channel_mapping(bot_token: str, guild_id: str) -> Dict[str, str]:
    """Finds channel IDs by name in the server."""
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

def main():
    if not DISCORD_BOT_TOKEN:
        logging.error("DISCORD_BOT_TOKEN is not set.")
        return

    logging.info("Starting AnkerGames Radar scan...")
    channels = get_channel_mapping(DISCORD_BOT_TOKEN, GUILD_ID)
    all_releases_ch = channels.get('📢-all-releases')

    seen = load_seen_games()
    urls = fetch_recent_game_urls()
    if not urls:
        logging.warning("No game links returned.")
        return

    if not seen:
        logging.info("First run: initializing baseline...")
        for u in urls:
            slug = u.rstrip('/').split('/')[-1]
            seen.add(f"{slug}:baseline")
        save_seen_games(seen)
        logging.info("Baseline saved.")
        return

    new_count = 0
    for url in reversed(urls):
        game_data = parse_game_page(url)
        if not game_data:
            continue

        game_id = game_data['id']
        if game_id in seen:
            continue

        logging.info(f"✨ NEW GAME DETECTED: {game_data['title']} (Build: {game_data['build']})")
        dispatch_info = create_discord_payload(game_data)
        payload = dispatch_info['payload']
        target_name = dispatch_info['target_channel']
        target_ch_id = channels.get(target_name)

        # 1. Post to category folder channel (e.g. #🏰-sim-strategy)
        if target_ch_id:
            send_bot_message(DISCORD_BOT_TOKEN, target_ch_id, payload)
            time.sleep(1)

        # 2. Also stream to #📢-all-releases
        if all_releases_ch and all_releases_ch != target_ch_id:
            send_bot_message(DISCORD_BOT_TOKEN, all_releases_ch, payload)
            time.sleep(1)

        seen.add(game_id)
        new_count += 1

    if new_count > 0:
        save_seen_games(seen)
        logging.info(f"Scan complete. Dispatched {new_count} new games into folder channels.")
    else:
        logging.info("Scan complete. Library is up to date.")

if __name__ == '__main__':
    main()
