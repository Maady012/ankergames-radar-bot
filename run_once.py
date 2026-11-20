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

    # Extract all seen slugs so we can distinguish brand NEW games from Steam BUILD UPDATES
    seen_slugs = {entry.split(':')[0] for entry in seen}

    new_count = 0
    for url in reversed(urls):
        game_data = parse_game_page(url)
        if not game_data:
            continue

        game_id = game_data['id']
        slug = game_data['slug']

        # If this exact (slug + build) was already published, skip
        if game_id in seen:
            continue

        # If slug exists in our database but build is different, it is a BUILD UPDATE!
        is_update = (slug in seen_slugs)

        status_text = "BUILD UPDATE" if is_update else "NEW GAME"
        logging.info(f"✨ {status_text} DETECTED: {game_data['title']} (Build: {game_data['build']})")

        dispatch_info = create_discord_payload(game_data, is_update=is_update)
        payload = dispatch_info['payload']
        target_name = dispatch_info['target_channel']
        target_ch_id = channels.get(target_name)

        # 1. Post to category folder channel
        if target_ch_id:
            send_bot_message(DISCORD_BOT_TOKEN, target_ch_id, payload)
            time.sleep(1)

        # 2. Stream to #📢-all-releases
        if all_releases_ch and all_releases_ch != target_ch_id:
            send_bot_message(DISCORD_BOT_TOKEN, all_releases_ch, payload)
            time.sleep(1)

        seen.add(game_id)
        seen_slugs.add(slug)
        new_count += 1

    if new_count > 0:
        save_seen_games(seen)
        logging.info(f"Scan complete. Dispatched {new_count} releases into folder channels.")
    else:
        logging.info("Scan complete. Library is up to date.")

if __name__ == '__main__':
    main()
