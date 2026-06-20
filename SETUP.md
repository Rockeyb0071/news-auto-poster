"""
fetch_news.py
--------------
NewsAPI.org se top headlines fetch karta hai (India, general category).
Jo headlines pehle already post ho chuki hain (state.json mein hash
saved hai) unko skip karta hai -- taaki same news dobara na aaye jab
din mein 4 baar (6am/10am/5pm/8pm) script chalti hai.

Agar fresh headlines kam milti hain (sab duplicate nikal jaayen), to
jitni mil jaayen utni hi use karta hai -- agar ZERO milti hain to
caller (run_news_daily.py) ko bata deta hai taaki wo post skip kare
aur galat/purani news na chale.
"""

import hashlib
import requests

import config


class NewsFetchError(Exception):
    pass


def _headline_hash(title: str) -> str:
    """Har headline ka ek chhota unique fingerprint, duplicate check ke liye."""
    return hashlib.sha256(title.strip().lower().encode("utf-8")).hexdigest()


def fetch_top_headlines(already_posted_hashes: set) -> list:
    if not config.NEWS_API_KEY:
        raise NewsFetchError("NEWS_API_KEY set nahi hai -- GitHub Secrets check karo.")

    params = {
        "apiKey": config.NEWS_API_KEY,
        "country": config.NEWS_COUNTRY,
        "pageSize": 20,  # zyada fetch karo taaki duplicates hatne ke baad bhi 3-5 bachen
    }
    resp = requests.get(config.NEWS_API_URL, params=params, timeout=30)
    data = resp.json()

    if data.get("status") != "ok":
        raise NewsFetchError(f"NewsAPI error: {data}")

    fresh_headlines = []
    for article in data.get("articles", []):
        title = (article.get("title") or "").strip()
        if not title or title == "[Removed]":
            continue

        h = _headline_hash(title)
        if h in already_posted_hashes:
            continue  # already post ho chuki hai, skip

        fresh_headlines.append({
            "title": title,
            "description": (article.get("description") or "").strip(),
            "source": (article.get("source", {}) or {}).get("name", ""),
            "url": article.get("url", ""),
            "hash": h,
        })

        if len(fresh_headlines) >= config.NEWS_PAGE_SIZE:
            break

    return fresh_headlines


if __name__ == "__main__":
    # Quick manual test
    headlines = fetch_top_headlines(set())
    for h in headlines:
        print(f"- {h['title']} ({h['source']})")
