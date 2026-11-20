import json
import urllib.request
from typing import Dict, Any, Optional, List

GENRE_ROUTING = {
    "action_rpg": {
        "keywords": ["action", "rpg", "souls", "adventure", "hack and slash", "open world", "fighting"],
        "color": 10181046, # Blurple/Purple
        "tag": "⚔️ Action & RPG"
    },
    "horror_survival": {
        "keywords": ["horror", "survival", "psychological", "zombies", "mystery"],
        "color": 15158332, # Crimson Red
        "tag": "👻 Horror & Survival"
    },
    "coop_multiplayer": {
        "keywords": ["co-op", "multiplayer", "online", "pvp", "local multiplayer"],
        "color": 3447003, # Blue
        "tag": "👥 Co-Op & Multiplayer"
    },
    "sim_strategy": {
        "keywords": ["simulation", "strategy", "management", "building", "sandbox", "turn-based"],
        "color": 15844367, # Gold / Yellow
        "tag": "🏰 Sim & Strategy"
    },
    "indie_casual": {
        "keywords": ["indie", "casual", "puzzle", "2d", "platformer", "anime", "cute"],
        "color": 3066993, # Emerald Green
        "tag": "🎨 Indie & Casual"
    }
}

def determine_category(genres: List[str]) -> Dict[str, Any]:
    genres_lower = [g.lower() for g in genres]
    for cat_id, cfg in GENRE_ROUTING.items():
        for kw in cfg["keywords"]:
            if any(kw in g for g in genres_lower):
                return {
                    "category": cat_id,
                    "color": cfg["color"],
                    "tag": cfg["tag"]
                }
    return {
        "category": "general",
        "color": 5793266,
        "tag": "🎮 PC Game Release"
    }

def create_discord_payload(game: Dict[str, Any], is_forum: bool = True) -> Dict[str, Any]:
    """Builds a rich Discord Embed with a 4-image screenshot collage grid + poster."""
    cat_info = determine_category(game.get('genres', []))
    genre_str = ", ".join(game.get('genres', [])[:5]) or "Action / PC"
    deck_str = "✅ Verified / Playable" if game.get('deck_verified') else "❔ Unchecked"
    
    # Clean description
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

    # Forum channel post title
    if is_forum:
        payload["thread_name"] = f"{cat_info['tag']} | {game['title']} [{game.get('version', 'Latest')}]"

    return payload

def send_discord_webhook(webhook_url: str, payload: Dict[str, Any]) -> bool:
    """Delivers the payload to Discord webhook (supports both standard text and forum channels)."""
    try:
        # Append ?wait=true for forum channels if not present
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
