import json
import requests
from pathlib import Path
import snscrape.modules.twitter as sntwitter
import os

USERNAME = "clavicular0"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

STATE_FILE = Path("state.json")


def load_state():
    if not STATE_FILE.exists():
        return {"last_tweet_id": ""}

    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def latest_tweet():
    scraper = sntwitter.TwitterUserScraper(USERNAME)

    for tweet in scraper.get_items():
        return {
            "id": str(tweet.id),
            "text": tweet.rawContent,
            "url": f"https://x.com/{USERNAME}/status/{tweet.id}",
        }

    return None


def send_discord(tweet):
    payload = {
        "content": (
            f"🚨 New tweet from @{USERNAME}\n\n"
            f"{tweet['text']}\n\n"
            f"{tweet['url']}"
        )
    }

    requests.post(WEBHOOK_URL, json=payload, timeout=15)


def main():
    state = load_state()
    tweet = latest_tweet()

    if tweet is None:
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
