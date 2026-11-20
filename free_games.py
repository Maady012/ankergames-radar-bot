import urllib.request
import json
import logging
from typing import List, Dict, Any

EPIC_API_URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US&allowCountries=US"

def fetch_epic_free_games() -> List[Dict[str, Any]]:
    """Scrapes 100% free claimable games directly from Epic Games Store API."""
    req = urllib.request.Request(
        EPIC_API_URL,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    results = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            elements = data.get('data', {}).get('Catalog', {}).get('searchStore', {}).get('elements', [])
            for el in elements:
                promotions = el.get('promotions') or {}
                offers = promotions.get('promotionalOffers') or []
                if offers:
                    for promo in offers[0].get('promotionalOffers', []):
                        discount = promo.get('discountSetting', {}).get('discountPercentage')
                        if discount == 0:
                            title = el.get('title')
                            desc = el.get('description', '')
                            page_slug = el.get('productSlug') or el.get('urlSlug')
                            if not page_slug:
                                mappings = el.get('catalogNs', {}).get('mappings', [])
                                if mappings:
                                    page_slug = mappings[0].get('pageSlug')

                            link = f"https://store.epicgames.com/p/{page_slug}" if page_slug else "https://store.epicgames.com/free-games"
                            end_date = promo.get('endDate')

                            imgs = el.get('keyImages', [])
                            image_url = ''
                            for img in imgs:
                                if img.get('type') in ['Thumbnail', 'OfferImageWide', 'DieselStoreFrontWide']:
                                    image_url = img.get('url')
                                    break
                            if not image_url and imgs:
                                image_url = imgs[0].get('url')

                            price = el.get('price', {}).get('totalPrice', {})
                            orig_price = price.get('fmtPrice', {}).get('originalPrice', 'Free')

                            results.append({
                                'id': f"epic:{el.get('id')}",
                                'title': title,
                                'description': desc,
                                'url': link,
                                'image': image_url,
                                'original_price': orig_price,
                                'end_date': end_date
                            })
    except Exception as e:
        logging.error(f"[FreeGames] Error fetching Epic promotions: {e}")
    return results

def create_free_game_payload(game: Dict[str, Any]) -> Dict[str, Any]:
    """Formats rich giveaway embed for #🎁-free-games."""
    embed = {
        "title": f"🎁 100% FREE GAME: {game['title']}",
        "url": game['url'],
        "description": f"**Limited-Time 100% Off Promotion on Epic Games Store!**\n\n*{game.get('description', '')[:250]}...*",
        "color": 65280, # Bright Lime Green
        "fields": [
            {
                "name": "💰 Original Price",
                "value": f"~~{game.get('original_price', '$19.99')}~~ ➔ **FREE ($0.00)**",
                "inline": True
            },
            {
                "name": "🏪 Platform",
                "value": "`Epic Games Store`",
                "inline": True
            },
            {
                "name": "⏳ Claim Expiry",
                "value": f"`{str(game.get('end_date', 'Limited Time'))[:10]}`",
                "inline": True
            }
        ],
        "image": {"url": game['image']} if game.get('image') else None,
        "footer": {
            "text": "Free Games Radar • Claim to keep in your library forever",
            "icon_url": "https://store.epicgames.com/favicon.ico"
        }
    }

    if not embed.get("image"):
        del embed["image"]

    components = [
        {
            "type": 1,
            "components": [
                {
                    "type": 2,
                    "style": 5,
                    "label": "🎁 Claim on Epic Games",
                    "url": game['url']
                }
            ]
        }
    ]

    return {
        "content": f"🚨 **FREE GAME ALERT** — **{game['title']}** is currently 100% FREE to claim!",
        "embeds": [embed],
        "components": components
    }
