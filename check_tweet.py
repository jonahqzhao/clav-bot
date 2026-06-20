import json
import os
from pathlib import Path

import feedparser
import requests

USERNAME = "Clav0Updates"
FEED_URL = f"https://rsshub.app/twitter/user/{USERNAME}"

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
STATE_FILE = Path("state.json")


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_tweet_id": ""}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def fetch_latest_tweet():
    feed = feedparser.parse(FEED_URL)

    if not feed.entries:
        raise RuntimeError("RSS feed returned no entries")

    entry = feed.entries[0]

    tweet_url = entry.link

    # extract tweet id from URL
    tweet_id = tweet_url.rstrip("/").split("/")[-1]

    return {
        "id": tweet_id,
        "url": tweet_url,  # already a proper x.com link usually
    }


def send_discord(tweet):
    requests.post(
        WEBHOOK_URL,
        json={
            "username": "Tweet Tracker",
            "content": f"New tweet:\n{tweet['url']}",
        },
        timeout=15,
    ).raise_for_status()


def main():
    state = load_state()
    tweet = fetch_latest_tweet()

    print("LATEST:", tweet)

    # init state without spam
    if not state["last_tweet_id"]:
        state["last_tweet_id"] = tweet["id"]
        save_state(state)
        print("Initialized")
        return

    if tweet["id"] == state["last_tweet_id"]:
        print("No new tweet")
        return

    send_discord(tweet)

    state["last_tweet_id"] = tweet["id"]
    save_state(state)

    print("Sent")


if __name__ == "__main__":
    main()
