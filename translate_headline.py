"""
fetch_unsplash_image.py
-------------------------
News headline ke topic se related ek background photo Unsplash se
fetch karta hai (free API). Agar koi match na mile ya request fail
ho jaye, ek generic "newspaper" fallback query use karta hai.
"""

import requests

import config


class ImageFetchError(Exception):
    pass


def _extract_keyword(title: str) -> str:
    """
    Headline se ek simple search keyword banata hai. Pura headline
    Unsplash search mein daalna noisy results deta hai, isliye sirf
    pehle 3-4 significant words use karte hain.
    """
    stopwords = {
        "the", "a", "an", "of", "in", "on", "to", "for", "and", "is",
        "are", "amid", "after", "over", "as", "with", "by",
    }
    words = [w for w in title.split() if w.lower() not in stopwords]
    return " ".join(words[:4]) if words else title


def fetch_background_image(title: str) -> bytes:
    if not config.UNSPLASH_ACCESS_KEY:
        raise ImageFetchError("UNSPLASH_ACCESS_KEY set nahi hai -- GitHub Secrets check karo.")

    keyword = _extract_keyword(title)
    headers = {"Authorization": f"Client-ID {config.UNSPLASH_ACCESS_KEY}"}

    for query in (keyword, "news newspaper"):  # fallback agar specific keyword fail ho
        params = {"query": query, "orientation": "squarish"}
        resp = requests.get(config.UNSPLASH_API_URL, headers=headers, params=params, timeout=30)

        if resp.status_code != 200:
            continue

        data = resp.json()
        image_url = (data.get("urls") or {}).get("regular")
        if not image_url:
            continue

        img_resp = requests.get(image_url, timeout=30)
        if img_resp.status_code == 200:
            return img_resp.content

    raise ImageFetchError(f"Koi background image nahi mili keyword='{keyword}' ke liye.")
