import time
import os
import json
import logging
from typing import Set, Dict, Any

from scraper import fetch_recent_game_urls, parse_game_page
from discord_dispatcher import create_discord_payload, send_discord_webhook, determine_category

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

SEEN_FILE = os.environ.get('SEEN_FILE', 'seen_games.json')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', '')
CHECK_INTERVAL_SECONDS = int(os.environ.get('CHECK_INTERVAL_SECONDS', '180')) # 3 minutes

# Optional category-specific webhooks
CATEGORY_WEBHOOKS = {
    'action_rpg': os.environ.get('WEBHOOK_ACTION_RPG', ''),
    'horror_survival': os.environ.get('WEBHOOK_HORROR', ''),
    'coop_multiplayer': os.environ.get('WEBHOOK_COOP', ''),
    'sim_strategy': os.environ.get('WEBHOOK_STRATEGY', ''),
    'indie_casual': os.environ.get('WEBHOOK_INDIE', '')
}

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
        # Keep recent 2000 entries
        trimmed = list(seen)[-2000:]
        with open(SEEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(trimmed, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving {SEEN_FILE}: {e}")

def run_scan_cycle(seen: Set[str]) -> int:
    logging.info("Checking AnkerGames for new game builds...")
    urls = fetch_recent_game_urls()
    if not urls:
        logging.warning("No game links returned from games-list.")
        return 0

    new_count = 0
    # Process older to newest from the scraped page
    for url in reversed(urls):
        slug = url.rstrip('/').split('/')[-1]
        
        # Quick check if slug already seen
        # To detect version updates, we check full game ID (slug + build)
        game_data = parse_game_page(url)
        if not game_data:
            continue

        game_id = game_data['id']
        if game_id in seen:
            continue

        logging.info(f"✨ NEW GAME DETECTED: {game_data['title']} (Build: {game_data['build']}, Size: {game_data['size']})")
        payload = create_discord_payload(game_data)

        # Dispatch to main webhook
        delivered = False
        if DISCORD_WEBHOOK_URL:
            delivered = send_discord_webhook(DISCORD_WEBHOOK_URL, payload)

        # Dispatch to category webhook if configured
        cat_info = determine_category(game_data.get('genres', []))
        cat_webhook = CATEGORY_WEBHOOKS.get(cat_info['category'])
        if cat_webhook and cat_webhook != DISCORD_WEBHOOK_URL:
            send_discord_webhook(cat_webhook, payload)

        seen.add(game_id)
        new_count += 1
        time.sleep(1) # Gentle rate limit between messages

    if new_count > 0:
        save_seen_games(seen)
        logging.info(f"Cycle completed. Published {new_count} new games.")
    else:
        logging.info("Scan complete. Library is up to date.")

    return new_count

def main():
    logging.info("🚀 AnkerGames Radar Background Worker Started!")
    seen = load_seen_games()
    logging.info(f"Loaded {len(seen)} previously indexed games.")

    # If first run with empty seen list, seed without spamming all 28 games
    if not seen:
        logging.info("First run detected. Pre-indexing current library to avoid spamming...")
        urls = fetch_recent_game_urls()
        for u in urls:
            slug = u.rstrip('/').split('/')[-1]
            seen.add(f"{slug}:initial")
        save_seen_games(seen)
        logging.info(f"Pre-seeded {len(seen)} games. Next scan will notify only fresh releases.")

    while True:
        try:
            run_scan_cycle(seen)
        except Exception as e:
            logging.error(f"Unexpected error during scan cycle: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == '__main__':
    main()
