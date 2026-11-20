import urllib.request
import json
import re
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

def fetch_steam_metadata(app_id: str) -> Dict[str, Any]:
    """Fetches official genre and category metadata directly from the official Steam Store API."""
    if not app_id:
        return {}
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            entry = data.get(str(app_id), {})
            if entry.get('success'):
                app_data = entry.get('data', {})
                genres = [g['description'] for g in app_data.get('genres', [])]
                categories = [c['description'] for c in app_data.get('categories', [])]
                return {
                    'genres': genres,
                    'categories': categories,
                    'is_free': app_data.get('is_free', False),
                    'header_image': app_data.get('header_image', '')
                }
    except Exception as e:
        print(f"[SteamAPI] Error fetching AppID {app_id}: {e}")
    return {}

def fetch_recent_game_urls() -> List[str]:
    """Scrapes the latest games list from AnkerGames."""
    url = "https://ankergames.net/games-list"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'https://ankergames.net/game/' in href and href not in links:
                    links.append(href)
            return links
    except Exception as e:
        print(f"[AnkerScraper] Error fetching games list: {e}")
        return []

def parse_game_page(game_url: str) -> Optional[Dict[str, Any]]:
    """Fetches and parses a single AnkerGames release using JSON-LD + Steam AppID API verification."""
    req = urllib.request.Request(game_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            
            # 1. Primary extraction via Schema.org VideoGame JSON-LD
            video_game = {}
            for s in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(s.string)
                    if isinstance(data, list):
                        data = data[0]
                    if data.get('@type') == 'VideoGame':
                        video_game = data
                        break
                except Exception:
                    pass
            
            title = video_game.get('name')
            if not title:
                h1 = soup.find('h1')
                title = h1.text.strip() if h1 else 'Unknown Game'
            
            version = video_game.get('softwareVersion', 'Latest')
            size = video_game.get('fileSize', 'Unknown')
            genres = video_game.get('genre', [])
            if not isinstance(genres, list):
                genres = [genres] if genres else []
            
            images = video_game.get('image', [])
            poster = images[0] if (isinstance(images, list) and images) else ''
            
            screenshots = video_game.get('screenshot', [])
            if not isinstance(screenshots, list):
                screenshots = [screenshots] if screenshots else []
            
            if not poster and screenshots:
                poster = screenshots[0]

            text_all = soup.get_text()
            build_match = re.search(r'Current Build\s*([0-9]+)', text_all)
            build = build_match.group(1) if build_match else 'N/A'

            # Steam Store link & App ID
            steam_url = ''
            steam_app_id = ''
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'store.steampowered.com/app/' in href:
                    steam_url = href
                    m = re.search(r'store\.steampowered\.com/app/(\d+)', href)
                    if m:
                        steam_app_id = m.group(1)
                    break
            
            # 2. Enrich with Official Steam Genres if Steam AppID exists
            steam_genres = []
            if steam_app_id:
                steam_meta = fetch_steam_metadata(steam_app_id)
                steam_genres = steam_meta.get('genres', [])

            deck_verified = 'Deck' in text_all and ('DeckPlayable' in text_all or 'Deck Verified' in text_all)
            slug = game_url.rstrip('/').split('/')[-1]

            return {
                'id': f"{slug}:{build}",
                'slug': slug,
                'title': title,
                'version': version,
                'build': build,
                'size': size,
                'genres': genres,
                'steam_genres': steam_genres,
                'steam_app_id': steam_app_id,
                'poster': poster,
                'screenshots': screenshots[:4],
                'url': game_url,
                'steam_url': steam_url,
                'deck_verified': deck_verified,
                'description': video_game.get('description', '')[:300]
            }
    except Exception as e:
        print(f"[AnkerScraper] Error parsing {game_url}: {e}")
        return None
