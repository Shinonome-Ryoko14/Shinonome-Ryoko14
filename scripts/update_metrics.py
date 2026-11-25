#!/usr/bin/env python3
"""Refresh the local animated GitHub metrics cards used by this profile.

Only the Python standard library is required. In GitHub Actions the automatic
GITHUB_TOKEN is enough: the script reads public repository metadata, language
byte counts and the public contribution calendar, then rewrites
``assets/generated/metrics-{light,dark}.svg``.

Local preview (no token needed, writes to a temporary directory by default):

    python3 scripts/update_metrics.py --demo --out /tmp/ryoko-preview

Normal run (used by the workflow):

    python3 scripts/update_metrics.py
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

API = "https://api.github.com"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
GENERATED = ASSETS / "generated"
AVATAR = ASSETS / "images" / "chibi-avatar.jpg"

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Nunito', 'Quicksand', Roboto, Helvetica, Arial, sans-serif"

LIGHT = {
    "scheme": "light",
    "prefix": "l_",
    "card": "#FFFFFF",
    "text": "#18394C",
    "muted": "#6C8A9B",
    "border": "#D5E8F3",
    "accent": "#3388BB",
    "accent2": "#EE8FBE",
    "accent3": "#9B8BF4",
    "track": "#E8F3F9",
    "empty": "#EAF4FA",
    "shadow": "#B5C9EE",
    "border_stops": ["#7FC4E8", "#F2A6C6", "#C8B6FF"],
    "heat_a": "#F2A6C6",
    "heat_b": "#4FA6D2",
    "ring_a": "#F2A6C6",
    "ring_b": "#7FC4E8",
    "lang_text": "#274A5D",
}

DARK = {
    "scheme": "dark",
    "prefix": "d_",
    "card": "#101F2C",
    "text": "#EAF7FF",
    "muted": "#8FB3C4",
    "border": "#234252",
    "accent": "#7FC4E8",
    "accent2": "#F49BC7",
    "accent3": "#B99BFF",
    "track": "#1B3040",
    "empty": "#1A2C3A",
    "shadow": "#02080D",
    "border_stops": ["#7FC4E8", "#F49BC7", "#B99BFF"],
    "heat_a": "#F49BC7",
    "heat_b": "#6BE5FF",
    "ring_a": "#F49BC7",
    "ring_b": "#6BE5FF",
    "lang_text": "#D5EAF6",
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


def demo_days(end: date = date(2026, 11, 24)) -> list[dict]:
    days = []
    for i in range(365):
        d = end - timedelta(days=364 - i)
        value = int(max(0, round(2.4 + 3.6 * math.sin(i * 0.19) + 2.2 * math.cos(i * 0.47))))
        if (i * 7 + d.weekday()) % 13 == 0:
            value = 0
        days.append({"date": d.isoformat(), "count": value})
    return days


DEMO_DATA = {
    "login": "Shinonome-Ryoko14",
    "generated_at": "2026-11-24T00:00:00Z",
    "stats": {
        "contributions": 864,
        "public_repos": 11,
        "languages": 6,
        "top_language": "Go",
        "followers": 12,
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
    "days": demo_days(),
}


def language_color(name: str, index: int) -> str:
    if name == "Other":
        return OTHER_COLOR
    return LANG_COLORS.get(name, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])


def api_get(path: str, token: str | None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ryoko-profile-metrics/2.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + path, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def fetch_contributions_page(login: str) -> tuple[int | None, list[dict]]:
    """Read the public contribution total and daily calendar without a token.

    GitHub renders the calendar as one <td> per day, with the human-readable
    count in a paired <tool-tip>. Parsing that public page keeps the script
    token-free while still giving us real daily data for the heatmap.
    """
    url = f"https://github.com/users/{login}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "ryoko-profile-metrics/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            page = response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError):
        return None, []

    total = None
    match = re.search(
        r"<h2[^>]*>\s*([\d,]+)\s*contributions?\s+in\s+the\s+last\s+year",
        page,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        total = int(match.group(1).replace(",", ""))

    tips = {
        key: re.sub(r"<[^>]+>", " ", value)
        for key, value in re.findall(
            r"<tool-tip[^>]*for=\"([^\"]+)\"[^>]*>(.*?)</tool-tip>", page, re.S
        )
    }
    days: dict[str, int] = {}
    for cell in re.findall(r"<td\b[^>]*ContributionCalendar-day[^>]*>", page):
        date_match = re.search(r'data-date="([0-9-]{10})"', cell)
        id_match = re.search(r'id="([^"]+)"', cell)
        if not date_match:
            continue
        count = 0
        if id_match:
            label = tips.get(id_match.group(1), "")
            count_match = re.search(r"(\d+)\s+contributions?", label)
            if count_match:
                count = int(count_match.group(1))
        days[date_match.group(1)] = count

    ordered = [
        {"date": d, "count": c}
        for d, c in sorted(days.items())
        if d <= date.today().isoformat()
    ]
    return total, ordered


def compute_streaks(days: list[dict]) -> tuple[int, int]:
    if not days:
        return 0, 0
    parsed = []
    for item in days:
        try:
            parsed.append((date.fromisoformat(str(item["date"])[:10]), int(item.get("count", 0))))
        except (ValueError, TypeError):
            continue
    parsed.sort()
    if not parsed:
        return 0, 0

    active = [d for d, count in parsed if count > 0]
    best = 0
    run = 0
    previous = None
    for d in active:
        if previous is not None and (d - previous).days == 1:
            run += 1
        else:
            run = 1
        best = max(best, run)
        previous = d

    counts = {d: count for d, count in parsed}
    today = date.today()
    end = max((d for d in counts if d <= today), default=today)
    current = 0
    cursor = end
    if counts.get(cursor, 0) == 0:
        cursor = end - timedelta(days=1)
    while counts.get(cursor, 0) > 0:
        current += 1
        cursor -= timedelta(days=1)
    return current, best


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

    contributions, days = fetch_contributions_page(login)
    current_streak, best_streak = compute_streaks(days)

    stats = {
        "contributions": contributions if contributions is not None else sum(d["count"] for d in days),
        "public_repos": int(user.get("public_repos", len(repos))),
        "languages": len(language_rows),
        "top_language": language_rows[0]["name"] if language_rows else "—",
        "followers": int(user.get("followers", 0)),
        "streak": current_streak,
        "best_streak": best_streak,
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
        "days": days,
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


def mix_hex(a: str, b: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    ar, ag, ab = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    br, bg, bb = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)
    return "#{:02x}{:02x}{:02x}".format(
        round(ar + (br - ar) * t),
        round(ag + (bg - ag) * t),
        round(ab + (bb - ab) * t),
    )


def build_odometer(
    prefix: str,
    uid: str,
    value: str,
    x: float,
    baseline: float,
    size: float,
    fill: str,
    weight: int = 800,
    delay: float = 0.15,
    duration: float = 1.25,
    align: str = "left",
) -> tuple[str, str, str]:
    """Pure-CSS odometer that gracefully falls back to the final value."""
    line_h = size * 1.30
    digit_w = size * 0.62
    comma_w = size * 0.30
    widths = [digit_w if ch.isdigit() else comma_w for ch in value]
    total_w = sum(widths)
    if align == "center":
        start_x = x - total_w / 2.0
    elif align == "right":
        start_x = x - total_w
    else:
        start_x = x

    clips: list[str] = []
    rules: list[str] = []
    parts: list[str] = []
    cursor = start_x

    for index, char in enumerate(value):
        width = widths[index]
        if char.isdigit():
            target = int(char)
            clip_id = f"odc_{prefix}{uid}_{index}"
            cls = f"od_{prefix}{uid}_{index}"
            top = baseline - size * 0.82
            clips.append(
                f'<clipPath id="{clip_id}"><rect x="{cursor - 2:.1f}" y="{top:.1f}" '
                f'width="{width + 4:.1f}" height="{size * 0.96:.1f}"/></clipPath>'
            )
            dy = target * line_h
            if target > 0:
                rules.append(
                    f"@keyframes {cls} {{ from {{ transform: translate3d(0, {dy:.1f}px, 0); }} }}\n"
                    f".{cls} {{ animation: {cls} {duration:.2f}s cubic-bezier(.16, 1, .3, 1) "
                    f"{delay + index * 0.05:.2f}s both; }}"
                )
            digits = "".join(
                f'<text x="{cursor + width / 2:.1f}" y="{baseline + row * line_h:.1f}" '
                f'text-anchor="middle" font-family="{SANS}" font-size="{size}" '
                f'font-weight="{weight}" fill="{fill}">{row}</text>'
                for row in range(10)
            )
            parts.append(
                f'<g clip-path="url(#{clip_id})"><g transform="translate(0 -{dy:.1f})">'
                f'<g class="{cls}">{digits}</g></g></g>'
            )
        else:
            parts.append(
                f'<text x="{cursor + width / 2:.1f}" y="{baseline:.1f}" text-anchor="middle" '
                f'font-family="{SANS}" font-size="{size}" font-weight="{weight}" '
                f'fill="{fill}">{escape(char)}</text>'
            )
        cursor += width
    return "\n".join(clips), "\n".join(rules), "\n".join(parts)


def contribution_grid(days: list[dict], end: date) -> list[list[dict]]:
    counts: dict[date, int] = {}
    for item in days:
        try:
            counts[date.fromisoformat(str(item["date"])[:10])] = int(item.get("count", 0))
        except (ValueError, TypeError):
            continue
    end = max((d for d in counts if d <= date.today()), default=date.today())
    week_start = end - timedelta(days=(end.weekday() + 1) % 7)
    start = week_start - timedelta(days=7 * 51)
    grid: list[list[dict]] = []
    for column in range(52):
        week = []
        for row in range(7):
            d = start + timedelta(days=column * 7 + row)
            week.append({"date": d, "count": counts.get(d, 0), "future": d > end})
        grid.append(week)
    return grid


def metrics_svg(data: dict, theme: dict) -> str:
    width, height = 1200, 560
    prefix = theme["prefix"]
    rows = prepare_rows(data.get("languages", []))
    stats = data.get("stats", {})
    login = escape(str(data.get("login", "Shinonome-Ryoko14")))
    updated = str(data.get("generated_at", ""))[:10]
    days = data.get("days", []) or []
    current_streak = int(stats.get("streak") or 0)
    best_streak = int(stats.get("best_streak") or 0)
    streak = current_streak or best_streak
    streak_label = "CURRENT STREAK" if current_streak else "BEST STREAK"

    def text(
        x: float,
        y: float,
        value: object,
        size: float = 13,
        weight: int = 400,
        fill: str | None = None,
        anchor: str = "start",
        spacing: float | None = None,
        opacity: float | None = None,
    ) -> str:
        attributes = (
            f'x="{x}" y="{y}" fill="{fill or theme["text"]}" font-family="{SANS}" '
            f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}"'
        )
        if spacing is not None:
            attributes += f' letter-spacing="{spacing}"'
        if opacity is not None:
            attributes += f' opacity="{opacity}"'
        return f"<text {attributes}>{escape(str(value))}</text>"

    defs: list[str] = [
        f'<linearGradient id="{prefix}border" x1="26" y1="26" x2="1174" y2="534" gradientUnits="userSpaceOnUse">'
        + "".join(
            f'<stop offset="{offset}%" stop-color="{colour}"/>'
            for offset, colour in zip((0, 45, 100), theme["border_stops"])
        )
        + "</linearGradient>",
        f'<linearGradient id="{prefix}ring" x1="980" y1="140" x2="1100" y2="260" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0%" stop-color="{theme["ring_a"]}"/>'
        f'<stop offset="100%" stop-color="{theme["ring_b"]}"/>'
        "</linearGradient>",
        f'<radialGradient id="{prefix}glowA" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0%" stop-color="{theme["accent2"]}" stop-opacity=".24"/>'
        f'<stop offset="100%" stop-color="{theme["accent2"]}" stop-opacity="0"/>'
        "</radialGradient>",
        f'<radialGradient id="{prefix}glowB" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0%" stop-color="{theme["accent"]}" stop-opacity=".22"/>'
        f'<stop offset="100%" stop-color="{theme["accent"]}" stop-opacity="0"/>'
        "</radialGradient>",
        f'<linearGradient id="{prefix}shine" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0%" stop-color="#FFFFFF" stop-opacity="0"/>'
        '<stop offset="50%" stop-color="#FFFFFF" stop-opacity=".32"/>'
        '<stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>'
        "</linearGradient>",
        f'<clipPath id="{prefix}barclip"><rect x="64" y="492" width="1072" height="10" rx="5"/></clipPath>',
        f'<clipPath id="{prefix}avatarclip"><circle cx="1096" cy="58" r="50"/></clipPath>',
    ]

    avatar_uri = ""
    if AVATAR.exists():
        avatar_uri = "data:image/jpeg;base64," + base64_encode(AVATAR)

    contributions = fmt_int(stats.get("contributions"))
    repos = fmt_int(stats.get("public_repos"))
    languages = fmt_int(stats.get("languages"))
    followers = fmt_int(stats.get("followers"))

    odometer_parts: list[str] = []
    odometer_css: list[str] = []
    for uid, value, x, baseline, size, fill, align in (
        ("contrib", contributions, 64, 238, 62, theme["text"], "left"),
        ("repos", repos, 418, 232, 40, theme["text"], "left"),
        ("langs", languages, 598, 232, 40, theme["text"], "left"),
        ("followers", followers, 778, 232, 40, theme["text"], "left"),
        ("streak", str(streak), 1040, 208, 24, theme["text"], "center"),
    ):
        clips, rules, parts = build_odometer(
            prefix, uid, value, x, baseline, size, fill,
            delay=0.12 if uid == "contrib" else 0.22,
            duration=1.25,
            align=align,
        )
        defs.append(clips)
        odometer_css.append(rules)
        odometer_parts.append(parts)

    # --- contribution heatmap -------------------------------------------------
    grid = contribution_grid(days, date.today())
    max_count = max((cell["count"] for week in grid for cell in week), default=1) or 1
    cell_size, cell_gap = 16.2, 3.6
    gx0, gy0 = 64.0, 316.0
    heat_parts: list[str] = []
    for column, week in enumerate(grid):
        t = column / 51.0
        base = mix_hex(theme["heat_a"], theme["heat_b"], t)
        rects = []
        for row, cell in enumerate(week):
            x = gx0 + column * (cell_size + cell_gap)
            y = gy0 + row * (cell_size + cell_gap)
            if cell["count"] <= 0:
                fill = theme["empty"]
                opacity = 0.9
                stroke = "none"
            else:
                intensity = 0.55 + 0.45 * min(1.0, cell["count"] / max_count)
                if theme["scheme"] == "light":
                    fill = mix_hex(base, "#FFFFFF", 0.42 * (1.0 - intensity))
                else:
                    fill = mix_hex(base, theme["card"], 0.35 * (1.0 - intensity))
                opacity = 0.95
                stroke = "#FFFFFF" if theme["scheme"] == "light" else "none"
            stroke_attr = (
                f' stroke="{stroke}" stroke-opacity=".35" stroke-width=".6"' if stroke != "none" else ""
            )
            rects.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_size}" height="{cell_size}" '
                f'rx="4" fill="{fill}" fill-opacity="{opacity}"{stroke_attr}/>'
            )
        heat_parts.append(
            f'<g transform="translate(0 0)"><g>'
            + "".join(rects)
            + "</g></g>"
        )

    legend_cells = []
    for i in range(5):
        fill = theme["empty"] if i == 0 else mix_hex(theme["heat_a"], theme["heat_b"], i / 4)
        legend_cells.append(
            f'<rect x="{1012 + i * 15}" y="296" width="10" height="10" rx="2.5" fill="{fill}"/>'
        )

    # --- language bar ---------------------------------------------------------
    bar_parts: list[str] = []
    legend_parts: list[str] = []
    if rows:
        cursor = 64.0
        bar_parts.append(f'<rect x="64" y="492" width="1072" height="10" rx="5" fill="{theme["track"]}"/>')
        for index, row in enumerate(rows[:6]):
            segment = 1072 * float(row["percent"]) / 100.0
            colour = language_color(str(row["name"]), index)
            bar_parts.append(
                f'<rect x="{cursor:.2f}" y="492" width="{segment + 0.6:.2f}" height="10" '
                f'fill="{colour}"/>'
            )
            cursor += segment

        step = 1072 / 6.0
        for index, row in enumerate(rows[:6]):
            colour = language_color(str(row["name"]), index)
            lx = 64 + index * step
            name = str(row["name"])
            legend_parts.append(
                f'<circle cx="{lx + 4:.1f}" cy="521" r="4" fill="{colour}"/>'
                + text(lx + 15, 525, name[:11], 12.5, 650, theme["lang_text"])
                + text(lx + 15 + len(name[:11]) * 7.0 + 6, 525, pct_label(float(row["percent"])), 12, 600, theme["muted"])
            )
    else:
        bar_parts.append(f'<rect x="64" y="492" width="1072" height="10" rx="5" fill="{theme["track"]}"/>')
        legend_parts.append(text(64, 524, "No language data yet. Run the workflow once.", 13, 500, theme["muted"]))

    # --- ring -----------------------------------------------------------------
    ring_cx, ring_cy, ring_r = 1040.0, 200.0, 51.0
    circumference = round(2 * math.pi * ring_r, 2)
    pct = max(0.04, min(1.0, streak / 7.0))
    offset = round(circumference * (1.0 - pct), 2)

    style = '''
    text { font-family: @FONT@; }
    .ring { stroke-dashoffset: @OFFSET@; }
    .lang-bar { transform-box: fill-box; transform-origin: left center; }
    @media (prefers-reduced-motion: no-preference) {
      @keyframes @P@ring {
        from { stroke-dashoffset: @CIRC@; }
      }
      @keyframes @P@bar {
        from { transform: scaleX(0); }
      }
      @keyframes @P@bob {
        0%, 100% { transform: translateY(0) rotate(-1deg); }
        50% { transform: translateY(-4px) rotate(1deg); }
      }
      @keyframes @P@twinkle {
        0%, 100% { opacity: .35; transform: scale(.82); }
        50% { opacity: 1; transform: scale(1.15); }
      }
      @keyframes @P@borderRun {
        to { stroke-dashoffset: -100; }
      }
      @keyframes @P@sweep {
        0% { transform: translateX(-320px) skewX(-16deg); }
        60%, 100% { transform: translateX(1300px) skewX(-16deg); }
      }
      .ring { animation: @P@ring 1.5s cubic-bezier(.16,1,.3,1) .2s both; }
      .lang-bar { animation: @P@bar 1.1s cubic-bezier(.16,1,.3,1) .3s both; }
      .avatar-bob { transform-box: fill-box; transform-origin: center; animation: @P@bob 4.8s ease-in-out infinite; }
      .sparkle { transform-box: fill-box; transform-origin: center; animation: @P@twinkle 3.8s ease-in-out infinite; }
      .sparkle.s2 { animation-duration: 4.6s; animation-delay: -1.3s; }
      .sparkle.s3 { animation-duration: 4.2s; animation-delay: -2.5s; }
      .border-run { animation: @P@borderRun 7s linear infinite; }
      .sheen { animation: @P@sweep 9s ease-in-out infinite; }
    }
    '''.replace("@P@", prefix).replace("@FONT@", SANS).replace("@OFFSET@", str(offset)).replace("@CIRC@", str(circumference))

    border_halo = (
        f'<rect x="20" y="20" width="1160" height="520" rx="36" fill="none" '
        f'stroke="url(#{prefix}border)" stroke-width="12" opacity=".16"/>'
    )
    body = f'''
  {border_halo}
  <rect x="28" y="32" width="1144" height="504" rx="30" fill="{theme["shadow"]}" opacity="{'.26' if theme["scheme"] == 'light' else '.45'}"/>
  <rect x="26" y="26" width="1148" height="508" rx="30" fill="{theme["card"]}" stroke="url(#{prefix}border)" stroke-width="3"/>
  <rect x="34" y="34" width="1132" height="492" rx="24" fill="none" stroke="{theme["border"]}" stroke-width="1.2" opacity=".65"/>
  <ellipse cx="1110" cy="90" rx="260" ry="180" fill="url(#{prefix}glowA)"/>
  <ellipse cx="120" cy="500" rx="280" ry="170" fill="url(#{prefix}glowB)"/>
  <rect class="sheen" x="0" y="0" width="150" height="560" fill="url(#{prefix}shine)" opacity=".16" transform="translate(-320 0) skewX(-16)"/>
  <rect class="border-run" x="32" y="32" width="1136" height="496" rx="26" fill="none" stroke="#FFFFFF" stroke-opacity=".55" stroke-width="2.2" pathLength="100" stroke-dasharray="6 94" stroke-linecap="round"/>

  <rect x="40" y="58" width="3" height="22" rx="1.5" fill="{theme["accent"]}"/>
  {text(54, 74, "RYOKO", 12, 800, theme["accent"], spacing=3.2)}
  {text(54, 106, f"@{login}", 25, 800, theme["text"], spacing=-0.2)}
  {text(54, 126, f"UPDATED {updated} · VIA GITHUB ACTIONS", 10.5, 600, theme["muted"], spacing=1.1)}

  <g class="avatar-bob">
    <circle cx="1096" cy="58" r="60" fill="url(#{prefix}glowA)"/>
    <circle cx="1096" cy="58" r="56" fill="{theme["card"]}" opacity=".95"/>
    <g clip-path="url(#{prefix}avatarclip)">
      <image href="{avatar_uri}" x="1046" y="8" width="100" height="100" preserveAspectRatio="xMidYMid slice"/>
    </g>
    <circle cx="1096" cy="58" r="50" fill="none" stroke="#FFFFFF" stroke-width="4.5"/>
    <circle cx="1096" cy="58" r="54" fill="none" stroke="url(#{prefix}border)" stroke-width="2.6"/>
  </g>
  <g class="sparkle" transform="translate(1046 18)"><path d="M0 -7 L2 -2 L7 0 L2 2 L0 7 L-2 2 L-7 0 L-2 -2 Z" fill="{theme["accent2"]}"/></g>
  <g class="sparkle s2" transform="translate(1156 112)"><circle r="3.2" fill="{theme["accent3"]}"/></g>

  <g>
    {text(64, 166, "CONTRIBUTIONS · LAST YEAR", 11.5, 700, theme["muted"], spacing=1.3)}
    {odometer_parts[0]}
    <rect x="64" y="252" width="28" height="2.4" rx="1.2" fill="{theme["accent"]}" opacity=".8"/>
  </g>

  <g>
    {text(418, 166, "PUBLIC REPOS", 11.5, 700, theme["muted"], spacing=1.3)}
    {odometer_parts[1]}
  </g>
  <g>
    {text(598, 166, "LANGUAGES", 11.5, 700, theme["muted"], spacing=1.3)}
    {odometer_parts[2]}
  </g>
  <g>
    {text(778, 166, "FOLLOWERS", 11.5, 700, theme["muted"], spacing=1.3)}
    {odometer_parts[3]}
  </g>

  <g>
    <circle cx="{ring_cx}" cy="{ring_cy}" r="{ring_r}" fill="none" stroke="{theme["track"]}" stroke-width="11"/>
    <circle class="ring" cx="{ring_cx}" cy="{ring_cy}" r="{ring_r}" fill="none" stroke="url(#{prefix}ring)" stroke-width="11" stroke-linecap="round" stroke-dasharray="{circumference}" transform="rotate(-90 {ring_cx} {ring_cy})"/>
    {odometer_parts[4]}
    {text(ring_cx, ring_cy + 26, streak_label, 9.2, 700, theme["muted"], anchor="middle", spacing=1.1)}
  </g>

  <g>
    {text(64, 300, "CONTRIBUTION ACTIVITY · LAST 52 WEEKS", 11.5, 700, theme["muted"], spacing=1.3)}
    {text(997, 304, "LESS", 9.5, 600, theme["muted"], spacing=.8)}
    {"".join(legend_cells)}
    {text(1099, 304, "MORE", 9.5, 600, theme["muted"], spacing=.8)}
    {"".join(heat_parts)}
  </g>

  <g>
    {text(64, 482, "TOP LANGUAGES", 11.5, 700, theme["muted"], spacing=1.3)}
    <g clip-path="url(#{prefix}barclip)"><g class="lang-bar">{"".join(bar_parts)}</g></g>
    {"".join(legend_parts)}
  </g>

  <g class="sparkle s3" transform="translate(1120 470)"><path d="M0 -6 L1.8 -1.8 L6 0 L1.8 1.8 L0 6 L-1.8 1.8 L-6 0 L-1.8 -1.8 Z" fill="{theme["accent"]}"/></g>
    '''

    defs_text = "\n".join(defs)
    style_text = (
        style
        + "\n@media (prefers-reduced-motion: no-preference) {\n"
        + "\n".join(odometer_css)
        + "\n}\n"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="GitHub metrics and language distribution">\n'
        f"<title>GitHub metrics and language distribution</title>\n"
        f"<desc>Contribution activity, streak, repository and language statistics, and an illustrated avatar.</desc>\n"
        f"<defs>\n{defs_text}\n</defs>\n<style>\n{style_text}\n</style>\n{body}\n</svg>\n"
    )


def base64_encode(path: Path) -> str:
    import base64

    return base64.b64encode(path.read_bytes()).decode("ascii")


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
    parser.add_argument("--out", default=str(GENERATED), help="output directory for the generated SVGs/JSON")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.demo:
        data = json.loads(json.dumps(DEMO_DATA))
        current, best = compute_streaks(data["days"])
        data["stats"]["streak"] = current
        data["stats"]["best_streak"] = best
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
        if not data.get("days"):
            old = previous_data()
            if old and old.get("days"):
                data["days"] = old["days"]
                old_stats = old.get("stats", {})
                data.setdefault("stats", {})
                data["stats"]["streak"] = old_stats.get("streak", 0)
                data["stats"]["best_streak"] = old_stats.get("best_streak", 0)

    for name, svg in (
        ("metrics-light.svg", metrics_svg(data, LIGHT)),
        ("metrics-dark.svg", metrics_svg(data, DARK)),
    ):
        cleaned = "\n".join(line.rstrip() for line in svg.splitlines()) + "\n"
        (out_dir / name).write_text(cleaned, encoding="utf-8")
    (out_dir / "metrics.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"updated animated metrics for {data.get('login')} ({len(data.get('languages', []))} languages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
