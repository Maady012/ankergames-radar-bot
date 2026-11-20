import os
import json
import logging
from typing import Set

from scraper import fetch_recent_game_urls, parse_game_page
from discord_dispatcher import create_discord_payload, send_discord_webhook

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

SEEN_FILE = os.environ.get('SEEN_FILE', 'seen_games.json')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', '')

def load_seen_games() -> Set[str]:
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data)
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
    logging.info("Starting single radar scan...")
    seen = load_seen_games()
    logging.info(f"Loaded {len(seen)} indexed entries.")

    urls = fetch_recent_game_urls()
    if not urls:
        logging.warning("No game links returned.")
        return

    # If first run, seed initial list so we don't spam 28 cards at once
    if not seen:
        logging.info("First run: indexing current library as baseline...")
        for u in urls:
            slug = u.rstrip('/').split('/')[-1]
            seen.add(f"{slug}:baseline")
        save_seen_games(seen)
        logging.info("Pre-seeded baseline successfully.")
        return

    new_count = 0
    for url in reversed(urls):
        game_data = parse_game_page(url)
        if not game_data:
            continue

        game_id = game_data['id']
        if game_id in seen:
            continue

        logging.info(f"✨ NEW GAME DETECTED: {game_data['title']} (Build: {game_data['build']}, Size: {game_data['size']})")
        payload = create_discord_payload(game_data, is_forum=True)

        if DISCORD_WEBHOOK_URL:
            send_discord_webhook(DISCORD_WEBHOOK_URL, payload)

        seen.add(game_id)
        new_count += 1

    if new_count > 0:
        save_seen_games(seen)
        logging.info(f"Scan complete. Dispatched {new_count} new games.")
    else:
        logging.info("Scan complete. No new games since last check.")

if __name__ == '__main__':
    main()
