import json
import os
import re
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

USERNAME = "Clav0Updates"

NITTER_BASE = "https://nitter.net"  # swap if needed
PROFILE_URL = f"{NITTER_BASE}/{USERNAME}"

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
STATE_FILE = Path("state.json")


# ---------------- STATE ----------------

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_tweet_id": ""}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ---------------- SCRAPER ----------------

def fetch_latest_tweet():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        )

        print("[OPEN]", PROFILE_URL)

        page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=60000)

        # give Nitter time to render
        page.wait_for_timeout(3000)

        # DEBUG (optional but useful)
        print("[TITLE]", page.title())
        print("[URL]", page.url)

        links = page.locator('a[href*="/status/"]')

        count = links.count()
        print("[STATUS LINKS]", count)

        tweet_id = None
        tweet_href = None

        for i in range(count):
            href = links.nth(i).get_attribute("href")

            if not href:
                continue

            match = re.search(r"/status/(\d+)", href)
            if match:
                tweet_id = match.group(1)
                tweet_href = href
                break

        browser.close()

        if not tweet_id:
            raise RuntimeError("No tweet found on Nitter page")

        return {
            "id": tweet_id,
            "url": f"https://x.com/{USERNAME}/status/{tweet_id}",
            "raw": tweet_href,
        }


# ---------------- DISCORD ----------------

def send_discord(tweet):
    requests.post(
        WEBHOOK_URL,
        json={
            "username": "Tweet Tracker",
            "content": f"New tweet:\n{tweet['url']}",
        },
        timeout=15,
    ).raise_for_status()


# ---------------- MAIN ----------------

def main():
    state = load_state()
    tweet = fetch_latest_tweet()

    print("[LATEST]", tweet)

    # first run init
    if not state["last_tweet_id"]:
        state["last_tweet_id"] = tweet["id"]
        save_state(state)
        print("Initialized state")
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
