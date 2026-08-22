import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

CONFIG_FILE = ROOT / "profile.yml"
DATA_FILE = ROOT / "data" / "platform_stats.json"
README_FILE = ROOT / "README.md"


# ============================================================
# LOAD CONFIG
# ============================================================

CONFIG = yaml.safe_load(
    CONFIG_FILE.read_text(encoding="utf-8")
)

if not CONFIG:
    raise SystemExit("profile.yml is empty or invalid.")


# ============================================================
# HELPERS
# ============================================================

def today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def now_utc():
    return datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )


def load_json():
    if not DATA_FILE.exists():
        return {
            "tryhackme": {},
            "letsdefend": {}
        }

    try:
        return json.loads(
            DATA_FILE.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError:
        return {
            "tryhackme": {},
            "letsdefend": {}
        }


def save_json(data):
    DATA_FILE.write_text(
        json.dumps(data, indent=2) + "\n",
        encoding="utf-8"
    )


def get_platform_config(name):
    platforms = CONFIG.get("platforms", {})
    return platforms.get(name, {})


# ============================================================
# PLATFORM VALUES
#
# These values come from profile.yml.
#
# This avoids scraping platforms that do not provide a
# documented public API for this purpose.
# ============================================================

def build_platform_stats(old, platform_name):

    config = get_platform_config(platform_name)

    result = dict(old or {})

    # --------------------------------------------------------
    # Preserve the previous successful value
    # --------------------------------------------------------

    if "streak" not in result:
        result["streak"] = "—"

    if "rank" not in result:
        result["rank"] = "—"

    # --------------------------------------------------------
    # Optional values from profile.yml
    # --------------------------------------------------------

    if config.get("streak") is not None:
        result["streak"] = str(
            config["streak"]
        )

    if config.get("rank") is not None:
        result["rank"] = str(
            config["rank"]
        )

    result["profile_url"] = config.get(
        "profile_url",
        ""
    )

    result["source"] = "profile.yml"

    result["updated"] = today()

    result["ok"] = (
        result["streak"] != "—"
        or result["rank"] != "—"
    )

    return result


# ============================================================
# LOAD EXISTING DATA
# ============================================================

data = load_json()


# ============================================================
# TRYHACKME
# ============================================================

data["tryhackme"] = build_platform_stats(
    data.get("tryhackme", {}),
    "tryhackme"
)


# ============================================================
# LETSDEFEND
# ============================================================

data["letsdefend"] = build_platform_stats(
    data.get("letsdefend", {}),
    "letsdefend"
)


# ============================================================
# SAVE PLATFORM DATA
# ============================================================

save_json(data)


# ============================================================
# VALUES FOR README
# ============================================================

thm = data["tryhackme"]
ld = data["letsdefend"]

thm_url = thm.get(
    "profile_url",
    "https://tryhackme.com/p/famous33"
)

ld_url = ld.get(
    "profile_url",
    "https://app.letsdefend.io/user/PrasiddhaPal"
)


# ============================================================
# README LIVE PLATFORM BLOCK
# ============================================================

block = f"""<!-- LIVE_PLATFORM_STATS:START -->

<div align="center">

## 🔥 PLATFORM COMMAND CENTRE

<table>
<tr>

<td align="center">

### 🟢 TRYHACKME

🔥 **{thm.get("streak", "—")} DAY STREAK**

🏆 **{thm.get("rank", "—")}**

<a href="{thm_url}">
PROFILE
</a>

</td>

<td align="center">

### 🔵 LETSDEFEND

🔥 **{ld.get("streak", "—")} DAY STREAK**

🛡️ **{ld.get("rank", "SOC")}**

<a href="{ld_url}">
PROFILE
</a>

</td>

</tr>
</table>

<br>

`PLATFORM DATA • LAST UPDATED {now_utc()}`

</div>

<!-- LIVE_PLATFORM_STATS:END -->"""


# ============================================================
# UPDATE README
# ============================================================

if not README_FILE.exists():
    raise SystemExit("README.md was not found.")


text = README_FILE.read_text(
    encoding="utf-8"
)


pattern = re.compile(
    r"<!-- LIVE_PLATFORM_STATS:START -->"
    r".*?"
    r"<!-- LIVE_PLATFORM_STATS:END -->",
    re.S
)


new_text, count = pattern.subn(
    block,
    text
)


if count != 1:
    raise SystemExit(
        "README live-stat markers must exist exactly once."
    )


README_FILE.write_text(
    new_text,
    encoding="utf-8"
)


print("======================================")
print(" CYBER PROFILE UPDATE")
print("======================================")
print(
    f"TryHackMe : "
    f"{thm.get('streak', '—')} days | "
    f"{thm.get('rank', '—')}"
)
print(
    f"LetsDefend: "
    f"{ld.get('streak', '—')} days | "
    f"{ld.get('rank', 'SOC')}"
)
print(
    f"Updated   : {now_utc()}"
)
print("======================================")
