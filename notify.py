#!/usr/bin/env python3
"""
Push a Telegram message with the top 3 headlines + link to the page.
This is the habit trigger — the page alone won't get opened daily.

Env vars required:
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
  DIGEST_URL  (your GitHub Pages URL, e.g. https://vishsd14.github.io/daily-digest/)
"""
import json
import os
import sys

import requests


def top_headlines(digest, n=3):
    """Pull the highest-relevance items across all categories, capped at n."""
    pool = []
    for category, items in digest["categories"].items():
        for it in items:
            pool.append((it.get("relevance", 0), it["title"], category))
    pool.sort(key=lambda x: x[0], reverse=True)
    return pool[:n]


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    digest_url = os.environ.get("DIGEST_URL", "")

    if not token or not chat_id:
        print("[notify] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing, skipping notify", file=sys.stderr)
        return

    with open("digest.json") as f:
        digest = json.load(f)

    headlines = top_headlines(digest)
    if not headlines:
        text = f"📰 Today's digest is up, but nothing scored relevant today.\n{digest_url}"
    else:
        lines = [f"📰 Today's digest — {digest['date']}\n"]
        for _, title, category in headlines:
            lines.append(f"• {title} ({category})")
        lines.append(f"\n{digest_url}")
        text = "\n".join(lines)

    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": text, "disable_web_page_preview": False},
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"[notify] Telegram send failed: {resp.status_code} {resp.text}", file=sys.stderr)
    else:
        print("[notify] Telegram push sent")


if __name__ == "__main__":
    main()
