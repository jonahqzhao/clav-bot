import json
import os
from pathlib import Path

import feedparser
import requests

USERNAME = "clav0updates"
RSS_URL = f"https://nitter.poast.org/{USERNAME}/rss"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

STATE_FILE = Path("state.json")


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)

    return {"last_tweet_id": ""}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def latest_tweet():
    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        raise RuntimeError("RSS feed empty")

    entry = feed.entries[0]

    # Example RSS link:
    # https://nitter.poast.org/clavicular/status/1931234567890123456

    tweet_id = entry.link.rstrip("/").split("/")[-1]

    return {
        "id": tweet_id,
        "title": entry.title,
        "x_url": f"https://x.com/{USERNAME}/status/{tweet_id}",
    }


def send_discord(tweet):
    payload = {
        "username": "Clav's Disciple",
        "content": (
            f"🚨 New tweet from @{USERNAME}\n\n"
            f"{tweet['title']}\n\n"
            f"{tweet['x_url']}"
        ),
    }

    r = requests.post(WEBHOOK_URL, json=payload, timeout=15)
    r.raise_for_status()


def main():
    state = load_state()

    tweet = latest_tweet()

    if not state["last_tweet_id"]:
        state["last_tweet_id"] = tweet["id"]
        save_state(state)
        print("Initialized state.")
        return

    if tweet["id"] == state["last_tweet_id"]:
        print("No new tweet.")
        return
    
    send_discord(tweet)

    state["last_tweet_id"] = tweet["id"]
    save_state(state)

    print("New tweet sent.")


if __name__ == "__main__":
    main()
