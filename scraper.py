import urllib.request
import json
import re
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

# USER LAPTOP HARDWARE PROFILE: MSI Katana GF66 12UC-881IN
# CPU: Intel Core i5-12450H (8 Cores, 12 Threads, 4.4 GHz Turbo)
# GPU: NVIDIA GeForce RTX 3050 Laptop (4GB GDDR6, DLSS support)
# RAM: 8GB - 16GB DDR4 3200MHz | Screen: 15.6" 1080p 144Hz

def benchmark_katana_performance(min_text: str, rec_text: str) -> str:
    """Evaluates how a game will run on user's MSI Katana GF66 (i5-12450H / RTX 3050 4GB)."""
    text = (min_text + " " + rec_text).lower()
    
    is_ultra_demanding = any(k in text for k in ['rtx 3080', 'rtx 4070', 'rtx 4080', 'rtx 3070 ti', 'rx 6800', '12 gb vram', '16 gb vram'])
    is_heavy_vram = any(k in text for k in ['rtx 3060 (12gb)', 'rtx 3070', '8 gb vram', '8gb vram', '6 gb vram', 'rx 6700'])
    is_easy = any(k in text for k in ['gtx 750', 'gtx 760', 'gtx 960', 'gtx 1050', 'gtx 1060', 'intel hd', 'vega'])

    if is_ultra_demanding:
        return "⚠️ Heavy (1080p Medium/Low + DLSS Performance, ~40-50 FPS)"
    elif is_heavy_vram:
        return "🟢 High Performance (1080p High + DLSS Quality, ~60 FPS)"
    elif is_easy:
        return "⚡ Ultra / Max Settings (1080p 80-144 FPS Smooth)"
    else:
        return "🟢 Smooth 1080p High (~60+ FPS with DLSS)"

def fetch_steam_metadata(app_id: str) -> Dict[str, Any]:
    """Fetches genres, rating summary, top review, and PC requirements from Steam."""
    if not app_id:
        return {}
    
    res = {
        'genres': [],
        'rating': 'N/A',
        'top_review': '',
        'laptop_perf': '🟢 1080p Playable'
    }

    # 1. Official Steam Store API for Genres & Requirements
    min_req_raw = ''
    rec_req_raw = ''
    try:
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            entry = data.get(str(app_id), {})
            if entry.get('success'):
                app_data = entry.get('data', {})
                res['genres'] = [g['description'] for g in app_data.get('genres', [])]
                pc_req = app_data.get('pc_requirements', {})
                min_req_raw = pc_req.get('minimum', '')
                rec_req_raw = pc_req.get('recommended', '')
    except Exception:
        pass

    # 2. Benchmark on MSI Katana
    clean_min = BeautifulSoup(min_req_raw or '', 'html.parser').get_text(separator=' ')
    clean_rec = BeautifulSoup(rec_req_raw or '', 'html.parser').get_text(separator=' ')
    res['laptop_perf'] = benchmark_katana_performance(clean_min, clean_rec)

    # 3. Steam Store Page for Overall Rating
    try:
        store_url = f"https://store.steampowered.com/app/{app_id}"
        req = urllib.request.Request(
            store_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
                'Cookie': 'wants_mature_content=1; birthtime=786240001'
            }
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            for div in soup.find_all(lambda t: t.has_attr('class') and any('review' in c for c in t['class'])):
                txt = div.get_text(separator=' ', strip=True)
                if 'All Reviews:' in txt or 'English Reviews:' in txt:
                    m = re.search(r'([0-9]{1,3}%\s+of\s+[\d,]+)', txt)
                    score_m = re.search(r'(Overwhelmingly Positive|Very Positive|Positive|Mostly Positive|Mixed|Mostly Negative|Negative)', txt)
                    if m and score_m:
                        res['rating'] = f"⭐ {score_m.group(1)} ({m.group(1)})"
                        break
    except Exception:
        pass

    # 4. Steam Community for Top Helpful User Review
    try:
        com_url = f"https://steamcommunity.com/app/{app_id}/reviews/?browsefilter=toprated&l=english"
        com_req = urllib.request.Request(com_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'})
        with urllib.request.urlopen(com_req, timeout=4) as resp:
            com_html = resp.read().decode('utf-8', errors='ignore')
            com_soup = BeautifulSoup(com_html, 'html.parser')
            card = com_soup.find('div', class_='apphub_Card')
            if card:
                text_div = card.find('div', class_='apphub_CardTextContent')
                if text_div:
                    raw = text_div.get_text(separator=' ', strip=True)
                    clean = re.sub(r'^Posted:\s*[^A-Za-z0-9]*[0-9]+(?:\s+[A-Za-z]+,?\s+[0-9]+)?', '', raw).strip()
                    clean = re.sub(r'\s+', ' ', clean)
                    if len(clean) > 160:
                        clean = clean[:157] + '...'
                    res['top_review'] = clean
    except Exception:
        pass

    return res

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
    """Fetches and parses an AnkerGames release, enriching with MSI Katana Performance Estimates."""
    req = urllib.request.Request(game_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            
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
            
            steam_genres = []
            steam_rating = 'N/A'
            top_review = ''
            laptop_perf = '🟢 1080p Playable'

            if steam_app_id:
                steam_meta = fetch_steam_metadata(steam_app_id)
                steam_genres = steam_meta.get('genres', [])
                steam_rating = steam_meta.get('rating', 'N/A')
                top_review = steam_meta.get('top_review', '')
                laptop_perf = steam_meta.get('laptop_perf', '🟢 1080p Playable')

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
                'steam_rating': steam_rating,
                'top_review': top_review,
                'laptop_perf': laptop_perf,
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
