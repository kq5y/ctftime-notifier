import os

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL environment variable is not set.")

RSS_URL = os.getenv("CTFTIME_RSS_URL", "https://ctftime.org/event/list/upcoming/rss/")
if not RSS_URL:
    raise ValueError("CTFTIME_RSS_URL environment variable is not set.")

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 3600))
if CHECK_INTERVAL <= 0:
    raise ValueError("CHECK_INTERVAL must be a positive integer.")

TIMEZONE = os.getenv("TIMEZONE", "Asia/Tokyo")
if not TIMEZONE:
    raise ValueError("TIMEZONE environment variable is not set.")
