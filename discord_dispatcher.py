import json
import urllib.request
from typing import Dict, Any, Optional, List

# Weighted categories with dedicated color themes and keywords
CATEGORIES = {
    "sim_strategy": {
        "keywords": [
            "simulation", "simulator", "colony sim", "strategy", "tycoon", 
            "management", "building", "city builder", "automation", "turn-based",
            "resource management", "sandbox", "crafting", "farming"
        ],
        "color": 15844367, # Gold / Amber
        "tag": "🏰 Sim & Strategy"
    },
    "horror_survival": {
        "keywords": [
            "horror", "psychological horror", "survival horror", "zombies", 
            "post-apocalyptic", "spooky"
        ],
        "color": 15158332, # Crimson Red
        "tag": "👻 Horror & Survival"
    },
    "sports_racing": {
        "keywords": [
            "racing", "sports", "driving", "automotive", "football", "basketball", 
            "flight sim", "motorcycle"
        ],
        "color": 15105570, # Orange
        "tag": "🏎️ Sports & Racing"
    },
    "coop_multiplayer": {
        "keywords": [
            "co-op", "multiplayer", "online co-op", "local co-op", "pvp", "mmo", 
            "battle royale", "party game"
        ],
        "color": 3447003, # Dodger Blue
        "tag": "👥 Co-Op & Multiplayer"
    },
    "adventure_mystery": {
        "keywords": [
            "adventure", "puzzle", "detective", "mystery", "visual novel", 
            "story rich", "point & click", "investigation", "crime"
        ],
        "color": 9807270, # Cyan / Teal
        "tag": "🔍 Adventure & Mystery"
    },
    "action_rpg": {
        "keywords": [
            "action", "rpg", "action rpg", "souls", "souls-like", "hack and slash", 
            "open world", "fighting", "shooter", "fps", "tps", "slasher", "combat"
        ],
        "color": 10181046, # Blurple / Dark Violet
        "tag": "⚔️ Action & RPG"
    },
    "indie_casual": {
        "keywords": [
            "indie", "casual", "2d", "platformer", "pixel graphics", "anime", 
            "cute", "relaxing", "arcade"
        ],
        "color": 3066993, # Emerald Green
        "tag": "🎨 Indie & Casual"
    }
}

def determine_category(title: str, genres: List[str]) -> Dict[str, Any]:
    """
    Intelligently scores categories based on Title, Genre tags, and priority.
    Prevents simulators (e.g. 'Empires of the Undergrowth', 'Devices Tycoon')
    from getting falsely bucketed into Action & RPG just because of 'Open World' or 'Action'.
    """
    title_lower = title.lower()
    genres_lower = [g.lower() for g in genres]
    scores = {cat: 0 for cat in CATEGORIES}

    # 1. Title keyword matching gets an immediate high score (+6)
    for cat, cfg in CATEGORIES.items():
        for kw in cfg["keywords"]:
            if kw in title_lower:
                scores[cat] += 6

    # 2. Genre matching with position weighting (first 3 primary tags have higher weight)
    for idx, g in enumerate(genres_lower):
        weight = 3 if idx < 3 else 1
        for cat, cfg in CATEGORIES.items():
            for kw in cfg["keywords"]:
                if kw == g or (len(kw) > 4 and kw in g):
                    scores[cat] += weight

    best_cat = max(scores, key=scores.get)
    if scores[best_cat] == 0:
        return {
            "category": "general",
            "color": 5793266,
            "tag": "🎮 PC Game Release"
        }

    return {
        "category": best_cat,
        "color": CATEGORIES[best_cat]["color"],
        "tag": CATEGORIES[best_cat]["tag"]
    }

def create_discord_payload(game: Dict[str, Any], is_forum: bool = True) -> Dict[str, Any]:
    """Builds a rich Discord Embed with a 4-image screenshot collage grid + poster."""
    cat_info = determine_category(game.get('title', ''), game.get('genres', []))
    genre_str = ", ".join(game.get('genres', [])[:5]) or "Action / PC"
    deck_str = "✅ Verified / Playable" if game.get('deck_verified') else "❔ Unchecked"
    
    desc = game.get('description', '').strip()
    if len(desc) > 280:
        desc = desc[:280] + "..."

    main_embed = {
        "title": f"🎮 {game['title']}",
        "url": game['url'],
        "description": f"*{desc}*",
        "color": cat_info["color"],
        "thumbnail": {"url": game['poster']} if game.get('poster') else None,
        "fields": [
            {
                "name": "💾 File Size",
                "value": f"`{game.get('size', 'Unknown')}`",
                "inline": True
            },
            {
                "name": "🏷 Version",
                "value": f"`{game.get('version', 'Latest')}`",
                "inline": True
            },
            {
                "name": "⚙️ Steam Build",
                "value": f"`{game.get('build', 'N/A')}`",
                "inline": True
            },
            {
                "name": "📂 Genres",
                "value": f"{genre_str}",
                "inline": True
            },
            {
                "name": "🕹 Steam Deck",
                "value": deck_str,
                "inline": True
            },
            {
                "name": "🏷 Category",
                "value": f"`{cat_info['tag']}`",
                "inline": True
            }
        ],
        "footer": {
            "text": "AnkerGames Radar • Pre-installed & SteamDB Synced",
            "icon_url": "https://ankergames.net/favicon/favicon-96x96.png"
        }
    }

    if not main_embed.get("thumbnail"):
        del main_embed["thumbnail"]

    screenshots = game.get('screenshots', [])
    embeds = [main_embed]

    # Discord 4-image collage: sharing the exact same `url` creates a native mosaic gallery
    if screenshots:
        main_embed["image"] = {"url": screenshots[0]}
        for shot_url in screenshots[1:4]:
            embeds.append({
                "url": game['url'],
                "image": {"url": shot_url}
            })
    elif game.get('poster'):
        main_embed["image"] = {"url": game['poster']}

    components = [
        {
            "type": 1,
            "components": [
                {
                    "type": 2,
                    "style": 5,
                    "label": "🌐 Open on AnkerGames",
                    "url": game['url']
                }
            ]
        }
    ]

    if game.get('steam_url'):
        components[0]["components"].append({
            "type": 2,
            "style": 5,
            "label": "🎮 Steam Page",
            "url": game['steam_url']
        })

    payload = {
        "username": "AnkerGames Radar",
        "avatar_url": "https://ankergames.net/favicon/apple-touch-icon.png",
        "embeds": embeds,
        "components": components
    }

    if is_forum:
        payload["thread_name"] = f"{cat_info['tag']} | {game['title']} [{game.get('version', 'Latest')}]"

    return payload

def send_discord_webhook(webhook_url: str, payload: Dict[str, Any]) -> bool:
    """Delivers the payload to Discord webhook (supports both standard text and forum channels)."""
    try:
        target_url = webhook_url
        if "thread_name" in payload and "?wait=true" not in target_url:
            target_url += "?wait=true"

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            target_url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'AnkerRadar/1.0 DiscordBot'
            }
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            return resp.status in [200, 204]
    except Exception as e:
        print(f"[Discord] Failed to send notification: {e}")
        return False
