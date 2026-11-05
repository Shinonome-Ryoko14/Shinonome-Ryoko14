#!/usr/bin/env python3
"""Refresh the local GitHub metrics cards used by this profile README.

The script uses only the Python standard library. In GitHub Actions the
automatic GITHUB_TOKEN is enough: it reads public repository metadata and
language byte counts, then rewrites assets/generated/metrics-{light,dark}.svg.

Local preview (no token needed):

    python scripts/update_metrics.py --demo

The generated cards are ordinary SVG files committed to the repository, so the
README never depends on a third-party card service being online.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

API = "https://api.github.com"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
GENERATED = ASSETS / "generated"

# Accent colour (#3388BB) and a restrained palette around it.
LIGHT = {
    "bg": "#F7FBFD",
    "border": "#CFE6F2",
    "text": "#12344A",
    "muted": "#6B8A9B",
    "accent": "#3388BB",
    "glow": 0.13,
    "track": "#E3F1F8",
}
DARK = {
    "bg": "#0D2230",
    "border": "#1D4A63",
    "text": "#E8F4FA",
    "muted": "#8FB3C4",
    "accent": "#7FC4E8",
    "glow": 0.20,
    "track": "#17384B",
}


LANG_COLORS = {
    "Go": "#00ADD8",
    "C++": "#F34B7D",
    "Python": "#3572A5",
    "Lua": "#6A5ACD",
    "C": "#8A8A8A",
    "SQL": "#E38C00",
    "Shell": "#89E051",
    "Bash": "#4EAA25",
    "TypeScript": "#3178C6",
    "JavaScript": "#F1E05A",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "ArkTS": "#3178C6",
    "Dockerfile": "#4A6A75",
    "Jupyter Notebook": "#DA5B0B",
    "Java": "#B07219",
    "Rust": "#DEA584",
    "C#": "#178600",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "Vim Script": "#199F4B",
    "Makefile": "#427819",
    "Nix": "#7E7EFF",
}
OTHER_COLOR = "#6B8A9B"
FALLBACK_COLORS = ["#3388BB", "#5FA8CF", "#1E5F82", "#8CCBE8", "#6E8FCB", "#A78BC9"]


def language_color(name: str, index: int) -> str:
    if name == "Other":
        return OTHER_COLOR
    return LANG_COLORS.get(name, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])

DEMO_DATA = {
    "login": "Shinonome-Ryoko14",
    "generated_at": "2026-11-04T00:00:00Z",
    "stats": {
        "contributions": 69,
        "public_repos": 11,
        "languages": 6,
        "top_language": "Go",
        "followers": 1,
    },
    "latest_repo": {"name": "harmony-eldercare", "pushed_at": "2026-11-03T00:00:00Z"},
    "languages": [
        {"name": "Go", "bytes": 136300},
        {"name": "Python", "bytes": 61000},
        {"name": "Lua", "bytes": 16700},
        {"name": "C++", "bytes": 13300},
        {"name": "C", "bytes": 5200},
        {"name": "SQL", "bytes": 3500},
    ],
}


def api_get(path: str, token: str | None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ryoko-profile-metrics/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + path, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def fetch_contributions(login: str) -> int | None:
    """Read the public contribution total without requiring an API token."""
    url = f"https://github.com/users/{login}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "ryoko-profile-metrics/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            page = response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError):
        return None

    match = re.search(
        r"<h2[^>]*>\s*([\d,]+)\s*contributions?\s+in\s+the\s+last\s+year",
        page,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def collect(login: str, token: str | None) -> dict:
    user = api_get(f"/users/{login}", token)
    repos: list[dict] = []
    page = 1
    while True:
        batch = api_get(
            f"/users/{login}/repos?per_page=100&page={page}&type=owner&sort=updated",
            token,
        )
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    own_repos = [
        repo
        for repo in repos
        if not repo.get("fork") and repo.get("name", "").lower() != login.lower()
    ]

    languages: dict[str, int] = {}
    for repo in own_repos:
        name = repo.get("name")
        if not name:
            continue
        try:
            data = api_get(f"/repos/{login}/{name}/languages", token)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            continue
        if isinstance(data, dict):
            for language, size in data.items():
                if isinstance(size, int):
                    languages[language] = languages.get(language, 0) + size

    language_rows = [
        {"name": name, "bytes": size}
        for name, size in sorted(languages.items(), key=lambda item: item[1], reverse=True)
    ]

    stats = {
        "contributions": fetch_contributions(login),
        "public_repos": int(user.get("public_repos", len(repos))),
        "languages": len(language_rows),
        "top_language": language_rows[0]["name"] if language_rows else "—",
        "followers": int(user.get("followers", 0)),
    }

    latest = max(own_repos, key=lambda repo: repo.get("pushed_at") or "", default=None)
    latest_repo = None
    if latest:
        latest_repo = {"name": latest.get("name"), "pushed_at": latest.get("pushed_at")}

    return {
        "login": login,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "stats": stats,
        "latest_repo": latest_repo,
        "languages": language_rows,
    }


def fmt_int(value: int | None) -> str:
    if value is None:
        return "—"
    if value >= 1000:
        return f"{value / 1000:.1f}k".replace(".0k", "k")
    return str(value)


def prepare_rows(languages: list[dict], limit: int = 6) -> list[dict]:
    rows = [dict(item) for item in languages if item.get("bytes", 0) > 0]
    rows.sort(key=lambda item: item["bytes"], reverse=True)
    if not rows:
        return []
    if len(rows) > limit:
        head = rows[: limit - 1]
        rest = rows[limit - 1 :]
        head.append({"name": "Other", "bytes": sum(item["bytes"] for item in rest)})
        rows = head
    total = sum(item["bytes"] for item in rows) or 1
    for item in rows:
        item["percent"] = item["bytes"] / total * 100
    return rows


def pct_label(percent: float) -> str:
    if percent >= 10:
        return f"{percent:.0f}%"
    if percent >= 1:
        return f"{percent:.1f}%"
    return "<1%"


def metrics_svg(data: dict, theme: dict) -> str:
    width, height = 1200, 340
    rows = prepare_rows(data.get("languages", []))
    stats = data.get("stats", {})
    updated = str(data.get("generated_at", ""))[:10]

    font = "Inter, Segoe UI, Helvetica Neue, Arial, sans-serif"
    mono = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

    def text(x, y, value, size=13, weight=400, fill=None, anchor="start", family=font, spacing=None, extra=""):
        spacing_attr = f' letter-spacing="{spacing}"' if spacing is not None else ""
        return (
            f'<text x="{x}" y="{y}" fill="{fill or theme["text"]}" '
            f'font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}"{spacing_attr}{extra}>{escape(str(value))}</text>'
        )

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">GitHub metrics and language distribution</title>',
        '<desc id="desc">Contribution count, public repositories, languages, and a colored language distribution bar.</desc>',
        "<defs>",
        '<linearGradient id="top" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{theme["accent"]}" stop-opacity=".9"/>'
        f'<stop offset=".5" stop-color="{theme["accent"]}" stop-opacity=".28"/>'
        f'<stop offset="1" stop-color="{theme["accent"]}" stop-opacity="0"/>'
        '</linearGradient>',
        '<radialGradient id="halo" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0" stop-color="{theme["accent"]}" stop-opacity="{theme.get("glow", 0.16)}"/>'
        f'<stop offset=".55" stop-color="{theme["accent"]}" stop-opacity="{theme.get("glow", 0.16) / 2}"/>'
        f'<stop offset="1" stop-color="{theme["accent"]}" stop-opacity="0"/>'
        '</radialGradient>',
        '<clipPath id="barclip"><rect x="48" y="248" width="1104" height="10" rx="5"/></clipPath>',
        "</defs>",
        f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="18" fill="{theme["bg"]}" stroke="{theme["border"]}"/>',
        f'<ellipse cx="330" cy="112" rx="360" ry="120" fill="url(#halo)"/>',
        f'<ellipse cx="760" cy="112" rx="300" ry="100" fill="url(#halo)" opacity=".55"/>',
        f'<rect x="48" y="26" width="3" height="18" rx="1.5" fill="{theme["accent"]}"/>',
        text(62, 41, "GITHUB", 15, 700, spacing="2.6"),
        text(1152, 40, f"UPDATED {updated}", 10.5, 500, theme["muted"], "end", spacing="0.9"),
    ]

    stat_items = [
        ("CONTRIBUTIONS, LAST YEAR", fmt_int(stats.get("contributions"))),
        ("PUBLIC REPOSITORIES", fmt_int(stats.get("public_repos"))),
        ("LANGUAGES", fmt_int(stats.get("languages"))),
    ]
    for x, (label, value) in zip((48, 416, 784), stat_items):
        parts.append(text(x, 132, value, 56, 800, theme["text"]))
        parts.append(f'<rect x="{x}" y="148" width="24" height="2" rx="1" fill="{theme["accent"]}" opacity=".78"/>')
        parts.append(text(x, 172, label, 10.5, 600, theme["muted"], spacing="1.2"))

    parts.append(f'<rect x="48" y="202" width="{width - 96}" height="1" fill="{theme["border"]}" opacity=".75"/>')
    parts.append(text(48, 232, "LANGUAGE DISTRIBUTION", 10.5, 700, theme["muted"], spacing="1.4"))

    if rows:
        parts.append(f'<rect x="48" y="248" width="1104" height="10" rx="5" fill="{theme["track"]}"/>')
        cursor = 48.0
        for index, row in enumerate(rows[:6]):
            segment = 1104 * float(row["percent"]) / 100.0
            colour = language_color(str(row["name"]), index)
            parts.append(
                f'<rect x="{cursor:.2f}" y="248" width="{segment:.2f}" height="10" '
                f'fill="{colour}" clip-path="url(#barclip)"/>'
            )
            cursor += segment

        for index, row in enumerate(rows[:6]):
            cx = 48 + index * 184
            colour = language_color(str(row["name"]), index)
            parts.append(f'<circle cx="{cx + 4}" cy="283" r="4" fill="{colour}"/>')
            name_x = cx + 14
            parts.append(text(name_x, 287, row["name"], 13, 600, theme["text"]))
            pct_x = name_x + len(str(row["name"])) * 7.3 + 8
            parts.append(text(pct_x, 287, pct_label(float(row["percent"])), 12.5, 600, theme["muted"]))
    else:
        parts.append(f'<rect x="48" y="248" width="1104" height="10" rx="5" fill="{theme["track"]}"/>')
        parts.append(text(48, 287, "No language data yet. Run the workflow once.", 15, 400, theme["muted"]))

    parts.append(f'<rect x="0" y="0" width="{width}" height="2" rx="1" fill="url(#top)"/>')
    parts.append("</svg>")
    return "\n".join(parts)

def previous_data() -> dict | None:
    path = GENERATED / "metrics.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="render preview cards from sample data")
    parser.add_argument("--user", default=os.environ.get("PROFILE_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER"))
    args = parser.parse_args()

    GENERATED.mkdir(parents=True, exist_ok=True)

    if args.demo:
        data = DEMO_DATA
    else:
        login = args.user
        if not login:
            print("PROFILE_USER or GITHUB_REPOSITORY_OWNER is required", file=sys.stderr)
            return 2
        token = os.environ.get("GITHUB_TOKEN")
        try:
            data = collect(login, token)
        except Exception as exc:  # keep the last good card rather than breaking the page
            print(f"metrics refresh failed: {exc}", file=sys.stderr)
            if previous_data():
                print("keeping the last good metrics cards", file=sys.stderr)
                return 0
            return 1

        if not data.get("languages"):
            old = previous_data()
            if old and old.get("languages"):
                data["languages"] = old["languages"]
                old_stats = old.get("stats", {})
                data.setdefault("stats", {})
                data["stats"]["languages"] = old_stats.get("languages", len(old["languages"]))
                data["stats"]["top_language"] = old_stats.get(
                    "top_language", old["languages"][0].get("name", "—")
                )

    (GENERATED / "metrics-light.svg").write_text(metrics_svg(data, LIGHT), encoding="utf-8")
    (GENERATED / "metrics-dark.svg").write_text(metrics_svg(data, DARK), encoding="utf-8")
    (GENERATED / "metrics.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"updated metrics for {data.get('login')} ({len(data.get('languages', []))} languages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
