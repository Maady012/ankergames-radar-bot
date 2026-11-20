import json
import urllib.request
from typing import Dict, Any, Optional, List

# Category mappings & Color Themes (Decimal color codes for Discord)
# Purple (Action/RPG): 10181046, Red (Horror): 15158332, Green (Indie/Cozy): 3066993, Gold (AAA/Featured): 16766720
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
    """Matches game genres against predefined categories."""
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
        "color": 5793266, # Slate Dark
        "tag": "🎮 PC Game Release"
    }

def create_discord_payload(game: Dict[str, Any]) -> Dict[str, Any]:
    """Builds a rich Discord Embed with components/buttons."""
    cat_info = determine_category(game.get('genres', []))
    
    # Format genres as readable tags
    genre_str = ", ".join(game.get('genres', [])[:5]) or "Action / PC"
    deck_str = "✅ Verified / Playable" if game.get('deck_verified') else "❔ Unchecked"
    
    embed = {
        "title": f"🎮 {game['title']}",
        "url": game['url'],
        "description": f"*{game.get('description', '')[:220]}...*",
        "color": cat_info["color"],
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
                "name": "🏷 Category Feed",
                "value": f"`{cat_info['tag']}`",
                "inline": True
            }
        ],
        "footer": {
            "text": "AnkerGames Radar • Pre-installed & SteamDB Synced",
            "icon_url": "https://ankergames.net/favicon/favicon-96x96.png"
        }
    }

    if game.get('poster'):
        embed["image"] = {"url": game['poster']}

    # Action Row Buttons (Standard Discord Webhook / Bot Action Components)
    components = [
        {
            "type": 1, # Action Row
            "components": [
                {
                    "type": 2, # Link Button
                    "style": 5, # URL
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

    return {
        "username": "AnkerGames Radar",
        "avatar_url": "https://ankergames.net/favicon/apple-touch-icon.png",
        "embeds": [embed],
        "components": components
    }

def send_discord_webhook(webhook_url: str, payload: Dict[str, Any]) -> bool:
    """Delivers the payload to Discord webhook."""
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'AnkerRadar/1.0 DiscordBot'
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in [200, 204]
    except Exception as e:
        print(f"[Discord] Failed to send notification: {e}")
        return False
