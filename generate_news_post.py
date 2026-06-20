"""
run_news_daily.py
--------------------
Pura news automation ka SECOND half chalata hai (Instagram pe post +
Telegram notify + state update). News fetch aur carousel image
generation workflow ke pehle step mein already ho chuka hai (taaki
images git-push ho saken Instagram fetch karne se pehle) -- uska
result `.carousel_meta.json` mein saved hai, yahan se load hota hai.

Standalone testing ke liye (is file ko directly chalane par), agar
.carousel_meta.json nahi milta to khud fetch+generate kar leta hai.
"""

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from telegram_utils import send_telegram_message
from post_news_to_instagram import post_carousel, InstagramPostError

META_FILE = ".carousel_meta.json"


def load_state() -> dict:
    if not os.path.exists(config.STATE_FILE):
        return {"posted_headline_hashes": [], "posts": []}
    with open(config.STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    with open(config.STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def notify(text: str) -> None:
    send_telegram_message(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, text)


def _load_or_generate_meta() -> dict:
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    # Fallback: standalone run (e.g. local testing) -- fetch + generate khud
    from fetch_news import fetch_top_headlines, NewsFetchError
    from generate_news_post import generate_carousel

    state = load_state()
    already_posted = set(state.get("posted_headline_hashes", []))
    try:
        headlines = fetch_top_headlines(already_posted)
    except NewsFetchError as e:
        notify(f"⚠️ News fetch FAIL ho gaya:\n{e}")
        print(f"NewsFetchError: {e}")
        sys.exit(1)

    if not headlines:
        print("Koi fresh headline nahi mili (sab duplicate). Post skip kar rahe hain.")
        notify("ℹ️ Is baar koi nayi headline nahi mili, news post skip ho gaya.")
        sys.exit(0)

    return generate_carousel(headlines)


def main():
    meta = _load_or_generate_meta()
    state = load_state()

    if not config.GITHUB_REPOSITORY:
        print("GITHUB_REPOSITORY env var set nahi hai -- public image URLs nahi ban sakte.")
        sys.exit(1)

    # Public raw URLs banao -- images is workflow run mein already git-push
    # ho chuki hain isse pehle step mein
    image_urls = [
        f"https://raw.githubusercontent.com/{config.GITHUB_REPOSITORY}/"
        f"{config.GITHUB_BRANCH}/{path}"
        for path in meta["slide_paths"]
    ]
    caption = config.build_caption(meta["headline_titles"])

    print("Publishing carousel to Instagram...")
    try:
        result = post_carousel(image_urls, caption)
    except InstagramPostError as e:
        notify(f"⚠️ Aaj ka News carousel post FAIL ho gaya:\n{e}")
        raise

    permalink = result["permalink"] or "(permalink not returned yet)"
    print(f"Published! media_id={result['media_id']} permalink={permalink} slides={result['child_count']}")

    headline_list_text = "\n".join(f"- {s}" for s in meta["headline_titles"])
    notify(
        f"✅ News carousel upload ho gaya! ({result['child_count']} slides)\n\n"
        f"{headline_list_text}\n\n"
        f"🔗 {permalink}"
    )

    state.setdefault("posted_headline_hashes", []).extend(meta["source_hashes"])
    state.setdefault("posts", []).append({
        "media_id": result["media_id"],
        "permalink": permalink,
        "headlines": meta["headline_titles"],
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "views_notified": False,
    })
    save_state(state)
    print("state.json updated.")

    # Cleanup temp meta file
    if os.path.exists(META_FILE):
        os.remove(META_FILE)


if __name__ == "__main__":
    main()
