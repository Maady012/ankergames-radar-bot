import os
import json
import logging
import urllib.request
import time
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

    logging.info("Starting Radar Scan (All-Releases Unified Stream + Category Routing)...")
    channels = get_channel_mapping(DISCORD_BOT_TOKEN, GUILD_ID)
    all_releases_ch = channels.get('📢-all-releases')
    free_games_ch = channels.get('🎁-free-games')

    seen = load_seen_games()
    seen_slugs = {entry.split(':')[0] for entry in seen}

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

                # B) ALSO mirror into #📢-all-releases so all-releases has EVERY single drop
                if all_releases_ch:
                    send_bot_message(DISCORD_BOT_TOKEN, all_releases_ch, payload)
                    time.sleep(1)

                seen.add(fg_id)
    except Exception as e:
        logging.error(f"Error checking free games: {e}")

    # 2. Check AnkerGames Releases & Updates
    urls = fetch_recent_game_urls()
    if not urls:
        logging.warning("No game links returned from AnkerGames.")
        save_seen_games(seen)
        return

    new_count = 0
    for url in reversed(urls):
        game_data = parse_game_page(url)
        if not game_data:
            continue

        game_id = game_data['id']
        slug = game_data['slug']

        if game_id in seen:
            continue

        is_update = (slug in seen_slugs)
        status_text = "BUILD UPDATE" if is_update else "NEW GAME"
        logging.info(f"✨ {status_text} DETECTED: {game_data['title']} (Build: {game_data['build']})")

        dispatch_info = create_discord_payload(game_data, is_update=is_update)
        payload = dispatch_info['payload']
        target_name = dispatch_info['target_channel']
        target_ch_id = channels.get(target_name)

        # A) ALWAYS post into #📢-all-releases (Main unified hub for all categories + updates)
        if all_releases_ch:
            send_bot_message(DISCORD_BOT_TOKEN, all_releases_ch, payload)
            time.sleep(1)

        # B) Post into its specific folder category channel (e.g. #🏰-sim-strategy, #⚔️-action-rpg)
        if target_ch_id and target_ch_id != all_releases_ch:
            send_bot_message(DISCORD_BOT_TOKEN, target_ch_id, payload)
            time.sleep(1)

        seen.add(game_id)
        seen_slugs.add(slug)
        new_count += 1

    save_seen_games(seen)
    logging.info(f"Scan complete. Dispatched {new_count} new entries to both #📢-all-releases and categories. State saved.")

if __name__ == '__main__':
    main()
