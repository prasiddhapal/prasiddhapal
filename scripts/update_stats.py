import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml


ROOT = Path(__file__).resolve().parents[1]

CONFIG = yaml.safe_load(
    (ROOT / "profile.yml").read_text()
)

DATA_FILE = ROOT / "data/platform_stats.json"
README = ROOT / "README.md"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; PrasiddhaProfileUpdater/1.0)"
    )
}


def fetch(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()
    return response.text


def first_match(text, patterns):
    clean = re.sub(r"\s+", " ", text)

    for pattern in patterns:
        match = re.search(pattern, clean, re.I)

        if match:
            return match.group(1)

    return None


def extract_tryhackme_stats(html):

    streak = first_match(
        html,
        [
            r"(\d{1,5})\s*(?:day|days)\s*streak",
            r"streak[^0-9]{0,60}(\d{1,5})",
        ]
    )

    rank = first_match(
        html,
        [
            r"(top\s*\d+\s*%)",
            r"(top\s*\d+%)",
        ]
    )

    return streak, rank


def update_tryhackme(old, url):

    try:

        html = fetch(url)

        streak, rank = extract_tryhackme_stats(html)

        if streak:
            old["streak"] = streak

        if rank:
            old["rank"] = rank.upper()

        old["ok"] = bool(streak or rank)

        old["updated"] = datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%d")

    except Exception as exc:

        old["ok"] = False

        old["error"] = str(exc)[:180]

    return old


data = json.loads(
    DATA_FILE.read_text()
)


# --------------------------------------------------
# TRYHACKME
# --------------------------------------------------

data["tryhackme"] = update_tryhackme(
    data["tryhackme"],
    CONFIG["platforms"]["tryhackme"]["profile_url"]
)


# --------------------------------------------------
# LETSDEFEND
#
# Kept from automatic scraping.
# LetsDefend's official terms prohibit automated
# access, and the streak is not exposed through a
# documented public API.
# --------------------------------------------------

letsdefend = data["letsdefend"]

letsdefend.setdefault(
    "streak",
    "—"
)

letsdefend.setdefault(
    "rank",
    "SOC"
)

letsdefend["source"] = "manual"
letsdefend["updated"] = datetime.now(
    timezone.utc
).strftime("%Y-%m-%d")

data["letsdefend"] = letsdefend


# --------------------------------------------------
# SAVE DATA
# --------------------------------------------------

DATA_FILE.write_text(
    json.dumps(data, indent=2) + "\n"
)


# --------------------------------------------------
# README LIVE BLOCK
# --------------------------------------------------

t = data["tryhackme"]
l = data["letsdefend"]

thm_url = CONFIG[
    "platforms"
]["tryhackme"]["profile_url"]

ld_url = CONFIG[
    "platforms"
]["letsdefend"]["profile_url"]

updated = datetime.now(
    timezone.utc
).strftime("%Y-%m-%d %H:%M UTC")


block = f"""<!-- LIVE_PLATFORM_STATS:START -->
<div align="center">

| 🟢 TRYHACKME | 🔵 LETSDEFEND |
|:---:|:---:|
| **🔥 {t.get("streak", "—")} DAY STREAK** | **🔥 {l.get("streak", "—")} DAY STREAK** |
| **{t.get("rank", "—")}** | **{l.get("rank", "SOC")}** |
| [PROFILE]({thm_url}) | [PROFILE]({ld_url}) |

`TRYHACKME AUTO-REFRESHED • LETSDEFEND VALUE STORED SAFELY • {updated}`

</div>
<!-- LIVE_PLATFORM_STATS:END -->"""


text = README.read_text()

pattern = (
    r"<!-- LIVE_PLATFORM_STATS:START -->"
    r".*?"
    r"<!-- LIVE_PLATFORM_STATS:END -->"
)

new_text, count = re.subn(
    pattern,
    block,
    text,
    flags=re.S
)


if count != 1:
    raise SystemExit(
        "README live-stat markers were not found exactly once."
    )


README.write_text(new_text)

print("Cyber profile stats refreshed successfully.")
