import json
import os
import re
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

USERNAME = "Clav0Updates"
PROFILE_URL = f"https://x.com/{USERNAME}"

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

STATE_FILE = Path("state.json")


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)

    return {"last_tweet_id": ""}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_latest_tweet():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            )
        )

        page.goto(
            PROFILE_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(5000)

        # Debug artifacts
        page.screenshot(path="debug.png", full_page=True)

        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(page.content())

        print("URL:", page.url)
        print("TITLE:", page.title())

        links = page.locator('a[href*="/status/"]')
        count = links.count()

        print("STATUS LINK COUNT:", count)

        tweet_id = None

        for i in range(count):
            href = links.nth(i).get_attribute("href")

            print("HREF:", href)

            if not href:
                continue

            match = re.search(r"/status/(\d+)", href)

            if match:
                tweet_id = match.group(1)
                break

        browser.close()

        if tweet_id is None:
            raise RuntimeError(
                "Could not find a tweet id in any status link."
            )

        return {
            "id": tweet_id,
            "url": f"https://x.com/{USERNAME}/status/{tweet_id}",
        }


def send_discord(tweet):
    payload = {
        "username": "Clav's Disciple",
        "content": f"🚨 New tweet\n\n{tweet['url']}",
    }

    response = requests.post(
        WEBHOOK_URL,
        json=payload,
        timeout=15,
    )

    response.raise_for_status()


def main():
    state = load_state()

    tweet = get_latest_tweet()

    print("LATEST TWEET:", tweet["id"])

    # First run: initialize only
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
