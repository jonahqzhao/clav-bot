import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "Clav0Updates"
NITTER_URL = f"https://nitter.poast.org/{USERNAME}"

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

STATE_FILE = Path("state.json")


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_tweet_id": ""}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def fetch_latest_tweet():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(NITTER_URL, headers=headers, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # find all tweet links
    links = soup.select('a[href*="/status/"]')

    for link in links:
        href = link.get("href")
        if not href:
            continue

        match = re.search(r"/status/(\d+)", href)
        if match:
            tweet_id = match.group(1)

            return {
                "id": tweet_id,
                "url": f"https://x.com/{USERNAME}/status/{tweet_id}",
            }

    raise RuntimeError("No tweet found on Nitter page")


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

    print("LATEST:", tweet["id"])

    # first run init
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

    print("Sent new tweet")


if __name__ == "__main__":
    main()
