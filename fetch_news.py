"""
translate_headline.py
-----------------------
Har English news headline (+ optional short description) ko natural
Hinglish mein rewrite karta hai, Anthropic API (Claude) use karke.

ANTHROPIC_API_KEY environment variable / GitHub Secret se aana chahiye.
"""

import requests

import config

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-sonnet-4-6"


class TranslationError(Exception):
    pass


def translate_to_hinglish(title: str, description: str = "") -> str:
    if not config.ANTHROPIC_API_KEY:
        raise TranslationError("ANTHROPIC_API_KEY set nahi hai -- GitHub Secrets check karo.")

    source_text = title if not description else f"{title}\n\n{description}"

    prompt = (
        "Neeche ek English news headline (aur shayad chhota description) diya hai. "
        "Ise natural Hinglish mein 1-2 short lines mein rewrite karo -- jaise koi "
        "Indian Instagram news page likhta hai. Roman script use karo (Devanagari nahi). "
        "Sirf Hinglish text wapas karo, koi extra explanation ya quotes nahi.\n\n"
        f"News:\n{source_text}"
    )

    headers = {
        "content-type": "application/json",
        "x-api-key": config.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 200,
        "messages": [{"role": "user", "content": prompt}],
    }

    resp = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload, timeout=30)
    data = resp.json()

    if "content" not in data:
        raise TranslationError(f"Translation failed: {data}")

    text_parts = [block["text"] for block in data["content"] if block.get("type") == "text"]
    hinglish_text = "".join(text_parts).strip()

    if not hinglish_text:
        raise TranslationError(f"Empty translation response: {data}")

    return hinglish_text
