import json
import urllib.request
from typing import Dict, Any, Optional, List

CATEGORIES = {
    "sim_strategy": {
        "channel_name": "🏰-sim-strategy",
        "keywords": [
            "simulation", "simulator", "colony sim", "strategy", "tycoon", 
            "management", "building", "city builder", "automation", "turn-based",
            "resource management", "sandbox", "crafting", "farming"
        ],
        "color": 15844367, # Gold
        "tag": "🏰 Sim & Strategy"
    },
    "horror_survival": {
        "channel_name": "👻-horror-survival",
        "keywords": [
            "horror", "psychological horror", "survival horror", "zombies", 
            "post-apocalyptic", "spooky"
        ],
        "color": 15158332, # Crimson Red
        "tag": "👻 Horror & Survival"
    },
    "sports_racing": {
        "channel_name": "🏎️-sports-racing",
        "keywords": [
            "racing", "sports", "driving", "automotive", "football", "basketball", 
            "flight sim", "motorcycle"
        ],
        "color": 15105570, # Orange
        "tag": "🏎️ Sports & Racing"
    },
    "coop_multiplayer": {
        "channel_name": "⚔️-action-rpg",
        "keywords": [
            "co-op", "multiplayer", "online co-op", "local co-op", "pvp", "mmo", 
            "battle royale", "party game"
        ],
        "color": 3447003, # Dodger Blue
        "tag": "👥 Co-Op & Multiplayer"
    },
    "adventure_mystery": {
        "channel_name": "🔍-adventure-mystery",
        "keywords": [
            "adventure", "puzzle", "detective", "mystery", "visual novel", 
            "story rich", "point & click", "investigation", "crime"
        ],
        "color": 9807270, # Cyan / Teal
        "tag": "🔍 Adventure & Mystery"
    },
    "action_rpg": {
        "channel_name": "⚔️-action-rpg",
        "keywords": [
            "action", "rpg", "action rpg", "souls", "souls-like", "hack and slash", 
            "open world", "fighting", "shooter", "fps", "tps", "slasher", "combat"
        ],
        "color": 10181046, # Blurple / Violet
        "tag": "⚔️ Action & RPG"
    },
    "indie_casual": {
        "channel_name": "🎨-indie-casual",
        "keywords": [
            "indie", "casual", "2d", "platformer", "pixel graphics", "anime", 
            "cute", "relaxing", "arcade"
        ],
        "color": 3066993, # Emerald Green
        "tag": "🎨 Indie & Casual"
    }
}

def determine_category(title: str, genres: List[str], steam_genres: List[str] = None) -> Dict[str, Any]:
    title_lower = title.lower()
    genres_lower = [g.lower() for g in genres]
    steam_genres_lower = [g.lower() for g in (steam_genres or [])]
    scores = {cat: 0 for cat in CATEGORIES}

    for sg in steam_genres_lower:
        for cat, cfg in CATEGORIES.items():
            for kw in cfg["keywords"]:
                if kw == sg or (len(kw) > 4 and kw in sg):
                    scores[cat] += 8

    for cat, cfg in CATEGORIES.items():
        for kw in cfg["keywords"]:
            if kw in title_lower:
                scores[cat] += 6

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
            "channel_name": "📢-all-releases",
            "color": 5793266,
            "tag": "🎮 PC Game Release"
        }

    return {
        "category": best_cat,
        "channel_name": CATEGORIES[best_cat]["channel_name"],
        "color": CATEGORIES[best_cat]["color"],
        "tag": CATEGORIES[best_cat]["tag"]
    }

def create_discord_payload(game: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
    """
    Builds a rich Discord Embed with crystal-clear Status Headings:
    - ✨ NEW RELEASE | <Title> [<Version>]
    - 🔄 BUILD UPDATE | <Title> [<Version>]
    """
    cat_info = determine_category(
        game.get('title', ''),
        game.get('genres', []),
        game.get('steam_genres', [])
    )
    
    all_genres = []
    for g in (game.get('steam_genres', []) + game.get('genres', [])):
        if g not in all_genres:
            all_genres.append(g)
    genre_str = ", ".join(all_genres[:5]) or "Action / PC"

    deck_str = "✅ Verified / Playable" if game.get('deck_verified') else "❔ Unchecked"
    rating_str = game.get('steam_rating', 'N/A')
    
    desc = game.get('description', '').strip()
    if len(desc) > 240:
        desc = desc[:240] + "..."

    # High-Visibility Banner Header
    badge = "🔄 [BUILD UPDATE]" if is_update else "✨ [NEW RELEASE]"
    status_header = f"**{badge}** • {cat_info['tag']}"
    embed_title = f"{badge} {game['title']} [{game.get('version', 'Latest')}]"

    fields = [
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
            "name": "🌟 Steam Rating",
            "value": f"`{rating_str}`",
            "inline": True
        },
        {
            "name": "🕹 Steam Deck",
            "value": deck_str,
            "inline": True
        },
        {
            "name": "🏷 Folder Category",
            "value": f"`{cat_info['tag']}`",
            "inline": True
        },
        {
            "name": "📂 Genres",
            "value": f"{genre_str}",
            "inline": False
        }
    ]

    top_review = game.get('top_review', '').strip()
    if top_review:
        fields.append({
            "name": "💬 Top Steam Review",
            "value": f"> *\"{top_review}\"*",
            "inline": False
        })

    main_embed = {
        "title": embed_title,
        "url": game['url'],
        "description": f"{status_header}\n\n*{desc}*",
        "color": 16753920 if is_update else cat_info["color"], # Amber color for updates
        "thumbnail": {"url": game['poster']} if game.get('poster') else None,
        "fields": fields,
        "footer": {
            "text": "AnkerGames Radar • Pre-installed & SteamDB Synced",
            "icon_url": "https://ankergames.net/favicon/favicon-96x96.png"
        }
    }

    if not main_embed.get("thumbnail"):
        del main_embed["thumbnail"]

    screenshots = game.get('screenshots', [])
    embeds = [main_embed]

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

    return {
        "payload": {
            "content": f"{status_header} — **{game['title']}**",
            "embeds": embeds,
            "components": components
        },
        "target_channel": cat_info["channel_name"]
    }

def send_bot_message(bot_token: str, channel_id: str, payload: Dict[str, Any]) -> bool:
    try:
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Authorization': f'Bot {bot_token}',
                'Content-Type': 'application/json',
                'User-Agent': 'DiscordBot (https://github.com/Maady012, 1.0)'
            }
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            return resp.status in [200, 201]
    except Exception as e:
        print(f"[DiscordBot] Failed to send message to channel {channel_id}: {e}")
        return False
