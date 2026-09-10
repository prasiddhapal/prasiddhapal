"""Synchronise manually verified platform stats into README.md.

The platforms used here do not provide a stable public API for these profile
values, so the numbers are intentionally maintained in profile.yml. This
script keeps the README presentation consistent without pretending to scrape
or invent live data.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / "profile.yml"
DATA_FILE = ROOT / "data" / "platform_stats.json"
README_FILE = ROOT / "README.md"
START = "<!-- LIVE_PLATFORM_STATS:START -->"
END = "<!-- LIVE_PLATFORM_STATS:END -->"


def load_config() -> dict:
    config = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
    if not config:
        raise SystemExit("profile.yml is empty or invalid.")
    return config


def build_stats(config: dict) -> dict:
    platforms = config.get("platforms", {})
    result = {}
    for name in ("tryhackme", "letsdefend"):
        item = platforms.get(name, {})
        result[name] = {
            "streak": str(item.get("streak", "—")),
            "rank": str(item.get("rank", "—")),
            "profile_url": str(item.get("profile_url", "")),
        }
    result["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return result


def render_block(stats: dict) -> str:
    thm = stats["tryhackme"]
    ld = stats["letsdefend"]
    updated = stats["updated"]
    return f"""{START}

<div align="center">

| 🟢 TRYHACKME | 🔵 LETSDEFEND |
| :---: | :---: |
| **{thm['rank']}** · **{thm['streak']} day streak** | **{ld['rank']}** · **{ld['streak']} day streak** |

**Last verified:** {updated} UTC

</div>

{END}"""


def main() -> None:
    config = load_config()
    stats = build_stats(config)

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")

    text = README_FILE.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    block = render_block(stats)

    if pattern.search(text):
        updated_text = pattern.sub(block, text, count=1)
    else:
        marker = "---\n\n## 📊 GITHUB ACTIVITY"
        if marker not in text:
            raise SystemExit("Could not find a safe insertion point in README.md.")
        updated_text = text.replace(marker, f"{block}\n\n{marker}", 1)

    README_FILE.write_text(updated_text, encoding="utf-8")
    print(f"Platform stats synced: {stats['updated']} UTC")


if __name__ == "__main__":
    main()
