# bot.py - Gorklaud: Grok-powered X mention explainer bot
# Public template version – fill your secrets in .env

import requests
import json
import time
import base64
import datetime
import random
from requests_oauthlib import OAuth1
from datetime import timezone
from dotenv import load_dotenv
import os

# Load secrets from .env file
load_dotenv()

# ────────────────────────────────────────────────
#   FILL THESE IN YOUR .env FILE (never commit it!)
# ────────────────────────────────────────────────
# TWITTER_CONSUMER_KEY=xxx
# TWITTER_CONSUMER_SECRET=xxx
# TWITTER_ACCESS_TOKEN=xxx
# TWITTER_ACCESS_TOKEN_SECRET=xxx
# XAI_API_KEY=xxx
# YOUR_USERNAME=yourhandlewithout@

CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
XAI_API_KEY = os.getenv("XAI_API_KEY")
USERNAME = os.getenv("YOUR_USERNAME")

# Basic check for missing secrets
required = ["TWITTER_CONSUMER_KEY", "TWITTER_CONSUMER_SECRET", "TWITTER_ACCESS_TOKEN",
            "TWITTER_ACCESS_TOKEN_SECRET", "XAI_API_KEY", "YOUR_USERNAME"]
missing = [k for k in required if not os.getenv(k)]
if missing:
    print("Missing env variables:", ", ".join(missing))
    print("Create .env file and fill the values.")
    exit(1)

# ────────────────────────────────────────────────
#                Gorklaud system prompt
# ────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are Gorklaud, a Grok AI bot made with Clawdbot. "
    "Your only identity: if asked who you are or about yourself, say exactly: "
    "'I am Gorklaud, a Grok AI bot made with Clawdbot.' "
    "Your job is to read the tweet you're replying to (and the original post if this is a reply), "
    "then give a short, clear summary that explains it simply so anyone can understand better. "
    "Always respond in a concise, straightforward style with a touch of humor. "
    "Output ONLY the reply text — no roleplay, no extra framing. "
    "Keep every reply under 280 characters. "
    "No emojis. No hashtags. No self-promotion. "
    "Just direct, clever, straightforward help."
)

def get_bearer_token():
    auth_string = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"
    auth_encoded = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    headers = {
        "Authorization": f"Basic {auth_encoded}",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
    response = requests.post(
        "https://api.twitter.com/oauth2/token",
        headers=headers,
        data="grant_type=client_credentials"
    )
    if response.status_code != 200:
        raise Exception(f"Bearer token failed: {response.status_code} - {response.text}")
    print("Bearer token obtained")
    return response.json()["access_token"]

def fetch_tweet_by_id(bearer_token, tweet_id):
    url = f"https://api.twitter.com/2/tweets/{tweet_id}"
    params = {
        "tweet.fields": "text,author_id,created_at",
        "expansions": "author_id",
        "user.fields": "username"
    }
    headers = {"Authorization": f"Bearer {bearer_token}"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            tweet = data["data"]
            users = data.get("includes", {}).get("users", [])
            author = next((u["username"] for u in users if u["id"] == tweet["author_id"]), "unknown")
            return f"Original post by @{author}: {tweet['text']}"
        else:
            print(f"Failed to fetch parent {tweet_id}: {resp.status_code}")
            return ""
    except Exception as e:
        print(f"Parent fetch error: {e}")
        return ""

def generate_ai_response(mention_text, parent_context=""):
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"}
    user_content = mention_text
    if parent_context:
        user_content = f"Original post: {parent_context}\n\nReply/mention: {mention_text}\n\nExplain both simply."
    payload = {
        "model": "grok-4-1-fast-reasoning",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()[:277] + ("..." if len(r.json()["choices"][0]["message"]["content"]) > 280 else "")
    except Exception as e:
        print(f"Grok API error: {e}")
        return None

def reply_to_tweet(tweet_id, reply_text):
    url = "https://api.twitter.com/2/tweets"
    auth = OAuth1(CONSUMER_KEY, client_secret=CONSUMER_SECRET,
                  resource_owner_key=ACCESS_TOKEN, resource_owner_secret=ACCESS_TOKEN_SECRET)
    payload = {"text": reply_text, "reply": {"in_reply_to_tweet_id": tweet_id}}
    resp = requests.post(url, auth=auth, json=payload)
    if resp.status_code == 201:
        print(f"Replied to {tweet_id}")
    else:
        print(f"Reply failed ({resp.status_code}): {resp.text}")

# ────────────────────────────────────────────────
#                     MAIN
# ────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Gorklaud starting – monitoring @{USERNAME}")
    bearer = get_bearer_token()

    last_checked = datetime.datetime.now(timezone.utc) - datetime.timedelta(minutes=15)

    while True:
        try:
            url = "https://api.twitter.com/2/tweets/search/recent"
            query = f"@{USERNAME} -from:{USERNAME}"
            params = {
                "query": query,
                "tweet.fields": "created_at,conversation_id,referenced_tweets",
                "expansions": "author_id",
                "user.fields": "username",
                "max_results": 10,
                "start_time": last_checked.isoformat()
            }
            headers = {"Authorization": f"Bearer {bearer}"}
            resp = requests.get(url, headers=headers, params=params, timeout=20)
            resp.raise_for_status()

            data = resp.json()
            if "data" in data:
                for tweet in sorted(data["data"], key=lambda t: t.get("created_at", "")):
                    tweet_id = tweet["id"]
                    text = tweet["text"]
                    author = "unknown"
                    if "includes" in data and "users" in data["includes"]:
                        for u in data["includes"]["users"]:
                            if u["id"] == tweet["author_id"]:
                                author = u["username"]
                                break

                    print(f"Mention from @{author}: {text}")

                    parent_context = ""
                    parent_id = None
                    if "referenced_tweets" in tweet:
                        for ref in tweet["referenced_tweets"]:
                            if ref.get("type") == "replied_to":
                                parent_id = ref["id"]
                                break

                    if parent_id:
                        parent_context = fetch_tweet_by_id(bearer, parent_id)

                    reply_text = generate_ai_response(text, parent_context)
                    if reply_text:
                        print(f"→ {reply_text}")
                        reply_to_tweet(tweet_id, reply_text)

            if "meta" in data and data["meta"].get("newest_id"):
                last_checked = datetime.datetime.now(timezone.utc)

            time.sleep(30 + random.uniform(-8, 8))

        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(60)
