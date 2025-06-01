import re
import json
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import feedparser
import requests

import config


STATE_FILE = "state.json"


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
            if "new_notified" not in state:
                state["new_notified"] = []
            if "pre_notified" not in state:
                state["pre_notified"] = []
            return state
    except FileNotFoundError:
        return {"new_notified": [], "pre_notified": []}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def send_discord_embed(embed: dict):
    payload = {"embeds": [embed]}
    try:
        resp = requests.post(config.WEBHOOK_URL, json=payload)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Failed to send Discord embed: {e}")


def parse_entry_date(entry, key) -> datetime:
    raw = entry.get(key)
    if not raw:
        return None
    try:
        dt_utc = datetime.strptime(raw, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        return dt_utc
    except Exception:
        return None


def format_datetime(dt: datetime, tz_name: str) -> str:
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = timezone.utc
    local_dt = dt.astimezone(tz)
    tz_abbr = local_dt.tzname() or ""
    return local_dt.strftime(f"%Y-%m-%d %H:%M {tz_abbr}")


def strip_html_tags(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"<.*?>", "", text)
    return text.strip()


def extract_organizers(entry) -> str:
    raw = entry.get("organizers")
    if not raw:
        return "N/A"
    try:
        org_list = json.loads(raw)
        names = [ org.get("name", "") for org in org_list if "name" in org ]
        return ", ".join(names) if names else "N/A"
    except Exception:
        return "N/A"
    

def build_event_embed(entry, title: str, link: str, start_local: str | None, finish_local: str | None, is_pre: bool) -> dict:
    # raw_desc = entry.get("description", "")
    # desc_text = strip_html_tags(raw_desc)
    fmt = entry.get("format_text", "N/A")
    print(entry)
    onsite = entry.get("onsite", "False").lower() == "true"
    if onsite:
        loc = entry.get("location", "")
        loc = loc if loc else "N/A"
    else:
        loc = "On-line"
    organizers = extract_organizers(entry)
    official_url = entry.get("url", "")
    logo_rel = entry.get("logo_url", "")
    if logo_rel:
        logo_url = "https://ctftime.org" + logo_rel
    else:
        logo_url = "https://ctftime.org/static/images/ctftime-logo-avatar.png"
    if is_pre:
        embed_title = f"⏰ CTF starts in 24h: {title}"
        color = 0xFFA500
    else:
        embed_title = f"🔥 New CTF Added: {title}"
        color = 0x00FF00
    embed: dict = {
        "title": embed_title,
        "url": link,
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fields": [
            {
                "name": "Format",
                "value": fmt,
                "inline": True
            },
            {
                "name": "Location",
                "value": loc,
                "inline": True
            },
            {
                "name": "Organizers",
                "value": organizers,
                "inline": True
            },
            {
                "name": "Official URL",
                "value": official_url or "N/A",
                "inline": False
            },
        ],
        # "description": desc_text,
        "thumbnail": {"url": logo_url}
    }
    if finish_local:
        embed["fields"].insert(0, {
            "name": "End Time",
            "value": finish_local,
            "inline": True
        })
    if start_local:
        embed["fields"].insert(0, {
            "name": "Start Time",
            "value": start_local,
            "inline": True
        })
    if start_local and finish_local:
        embed["fields"].insert(2, {
            "name": "\u200b",
            "value": "\u200b",
            "inline": True
        })
    return embed


def main():
    state = load_state()
    print(f"[INFO] Launch: interval={config.CHECK_INTERVAL}, timezone={config.TIMEZONE}")

    while True:
        try:
            feed = feedparser.parse(config.RSS_URL)
            now_utc = datetime.now(timezone.utc)

            for entry in feed.entries:
                guid = entry.get("id") or entry.get("guid") or entry.get("link")
                title = entry.get("title", "No Title")
                link = entry.get("link", "")
                start_dt_utc = parse_entry_date(entry, "start_date")
                finish_dt_utc = parse_entry_date(entry, "finish_date")

                if guid and guid not in state["new_notified"]:
                    if start_dt_utc:
                        start_local = format_datetime(start_dt_utc, config.TIMEZONE)
                        finish_local = format_datetime(finish_dt_utc, config.TIMEZONE) if finish_dt_utc else None
                        embed = build_event_embed(entry, title, link, start_local, finish_local, is_pre=False)
                    else:
                        embed = build_event_embed(entry, title, link, None, None, is_pre=False)
                    send_discord_embed(embed)
                    state["new_notified"].append(guid)
            
                if start_dt_utc and guid:
                    notify_time = start_dt_utc - timedelta(days=1)
                    if now_utc >= notify_time and guid not in state["pre_notified"]:
                        start_local = format_datetime(start_dt_utc, config.TIMEZONE)
                        finish_local = format_datetime(finish_dt_utc, config.TIMEZONE) if finish_dt_utc else None
                        embed = build_event_embed(entry, title, link, start_local, finish_local, is_pre=True)
                        send_discord_embed(embed)
                        state["pre_notified"].append(guid)

            save_state(state)
            print(f"[INFO] Checked feed at {datetime.now(timezone.utc).isoformat()}")

        except Exception as e:
            print(f"[ERROR] An error occurred: {e}")
        
        time.sleep(config.CHECK_INTERVAL)


if __name__ == "__main__":
    main()
