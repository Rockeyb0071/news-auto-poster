"""
telegram_utils.py
-------------------
Telegram Bot API se message bhejne ka simple helper. Same bot use
hota hai jo quotes wale automation mein use ho rha hai -- bas alag
caption/content news ke liye.
"""

import requests


def send_telegram_message(bot_token: str, chat_id: str, text: str) -> None:
    if not bot_token or not chat_id:
        print("TELEGRAM_BOT_TOKEN ya TELEGRAM_CHAT_ID missing -- notification skip ho rahi hai.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code != 200:
            print(f"Telegram notification fail: {resp.text}")
    except requests.RequestException as e:
        print(f"Telegram notification error: {e}")
