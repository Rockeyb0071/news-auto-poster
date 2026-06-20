"""
post_news_to_instagram.py
----------------------------
Instagram Graph API se ek CAROUSEL post banata hai (multiple slides,
swipe karke dekhne wali). Single-image post se ye different hai:

  1. Har slide ke liye ek "child" media container banao
     (is_carousel_item=true)
  2. Sab child container IDs ko ek "parent" carousel container mein
     daalo (children=[id1, id2, ...])
  3. Parent container ko publish karo -- yahi actual post create hota hai

Image URLs PUBLIC honi chahiye (raw.githubusercontent.com se), kyunki
Instagram ke servers khud fetch karte hain -- file upload nahi hota.
"""

import time

import requests

import config

GRAPH_BASE = f"https://graph.facebook.com/{config.GRAPH_API_VERSION}"


class InstagramPostError(Exception):
    pass


def _create_child_container(image_url: str) -> str:
    url = f"{GRAPH_BASE}/{config.IG_USER_ID}/media"
    params = {
        "image_url": image_url,
        "is_carousel_item": "true",
        "access_token": config.IG_ACCESS_TOKEN,
    }
    resp = requests.post(url, params=params, timeout=60)
    data = resp.json()
    if "id" not in data:
        raise InstagramPostError(f"Child container banane mein fail: {data}")
    return data["id"]


def _create_carousel_container(child_ids: list, caption: str) -> str:
    url = f"{GRAPH_BASE}/{config.IG_USER_ID}/media"
    params = {
        "media_type": "CAROUSEL",
        "children": ",".join(child_ids),
        "caption": caption,
        "access_token": config.IG_ACCESS_TOKEN,
    }
    resp = requests.post(url, params=params, timeout=60)
    data = resp.json()
    if "id" not in data:
        raise InstagramPostError(f"Carousel container banane mein fail: {data}")
    return data["id"]


def _publish_container(creation_id: str) -> str:
    url = f"{GRAPH_BASE}/{config.IG_USER_ID}/media_publish"
    params = {
        "creation_id": creation_id,
        "access_token": config.IG_ACCESS_TOKEN,
    }
    resp = requests.post(url, params=params, timeout=60)
    data = resp.json()
    if "id" not in data:
        raise InstagramPostError(f"Publish karne mein fail: {data}")
    return data["id"]


def _get_permalink(media_id: str) -> str:
    url = f"{GRAPH_BASE}/{media_id}"
    params = {"fields": "permalink", "access_token": config.IG_ACCESS_TOKEN}
    resp = requests.get(url, params=params, timeout=30)
    data = resp.json()
    return data.get("permalink", "")


def post_carousel(image_urls: list, caption: str) -> dict:
    if not image_urls:
        raise InstagramPostError("Koi image URL nahi diya gaya carousel ke liye.")

    child_ids = []
    for image_url in image_urls:
        child_id = _create_child_container(image_url)
        child_ids.append(child_id)
        time.sleep(2)  # Instagram ko container process karne ka time dena

    carousel_id = _create_carousel_container(child_ids, caption)
    time.sleep(3)  # carousel container ready hone ka time

    media_id = _publish_container(carousel_id)
    permalink = _get_permalink(media_id)

    return {"media_id": media_id, "permalink": permalink, "child_count": len(child_ids)}
