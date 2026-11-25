#!/usr/bin/env python3
"""Build the animated SVG assets used by the profile README.

Only the Python standard library is required. The source photographs live in
``assets/images/`` already resized/optimised; this script embeds them into the
SVG wrappers so the README keeps working as plain <img> tags (SVG loaded as an
image cannot fetch external files).

Run from the repository root:

    python3 scripts/build_profile_assets.py
"""

from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "assets" / "images"
BRANDING = ROOT / "assets" / "branding"
TECH = ROOT / "assets" / "tech"

FONT = "'Noto Serif', Georgia, 'Times New Roman', serif"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Nunito', 'Quicksand', Roboto, Helvetica, Arial, sans-serif"


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def write_svg(path: Path, text: str) -> None:
    """Write an SVG with trailing whitespace trimmed (keeps diffs clean)."""
    cleaned = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    path.write_text(cleaned, encoding="utf-8")


def wrap_svg(width: int, height: int, defs: str, style: str, body: str, title: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{title}">\n'
        f"<title>{title}</title>\n"
        f"<defs>\n{defs}\n</defs>\n"
        f"<style>\n{style}\n</style>\n"
        f"{body}\n</svg>\n"
    )


# ---------------------------------------------------------------------------
# Hero banners
# ---------------------------------------------------------------------------

HERO_W, HERO_H = 1400, 788


def build_hero(scheme: str) -> str:
    dark = scheme == "dark"
    prefix = "dh_" if dark else "lh_"
    source = "hero-dark.jpg" if dark else "hero-light.jpg"
    image = data_uri(IMAGES / source, "image/jpeg")

    if dark:
        edge = ["#7FC4E8", "#FF9CC8", "#B892FF", "#7FC4E8"]
        aura_a, aura_b = "#FF7AC6", "#6BE5FF"
        shine_opacity = "0.16"
        vignette = "0.16"
    else:
        edge = ["#7FC4E8", "#F6A6C8", "#C8B6FF", "#7FC4E8"]
        aura_a, aura_b = "#F6A6C8", "#7FC4E8"
        shine_opacity = "0.20"
        vignette = "0.05"

    defs = f'''
    <clipPath id="{prefix}clip"><rect x="0" y="0" width="{HERO_W}" height="{HERO_H}" rx="26"/></clipPath>
    <linearGradient id="{prefix}edge" x1="0" y1="0" x2="{HERO_W}" y2="{HERO_H}" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{edge[0]}"/>
      <stop offset="36%" stop-color="{edge[1]}"/>
      <stop offset="70%" stop-color="{edge[2]}"/>
      <stop offset="100%" stop-color="{edge[3]}"/>
    </linearGradient>
    <radialGradient id="{prefix}auraA" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{aura_a}" stop-opacity="0.55"/>
      <stop offset="55%" stop-color="{aura_a}" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="{aura_a}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="{prefix}auraB" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{aura_b}" stop-opacity="0.50"/>
      <stop offset="55%" stop-color="{aura_b}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{aura_b}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="{prefix}shine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="50%" stop-color="#FFFFFF" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="{prefix}vignette" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0B1622" stop-opacity="0"/>
      <stop offset="72%" stop-color="#0B1622" stop-opacity="0"/>
      <stop offset="100%" stop-color="#0B1622" stop-opacity="{vignette}"/>
    </linearGradient>
    <linearGradient id="{prefix}noteA" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="100%" stop-color="{aura_b}"/>
    </linearGradient>
    <linearGradient id="{prefix}noteB" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="100%" stop-color="{aura_a}"/>
    </linearGradient>
    '''

    style = f'''
    .{prefix}aura {{ transform-box: fill-box; transform-origin: center; }}
    .{prefix}note {{ transform-box: fill-box; transform-origin: center; }}
    .{prefix}twinkle {{ transform-box: fill-box; transform-origin: center; }}
    @media (prefers-reduced-motion: no-preference) {{
      @keyframes {prefix}auraPulse {{
        0%, 100% {{ opacity: .55; transform: scale(1); }}
        50% {{ opacity: .95; transform: scale(1.08); }}
      }}
      @keyframes {prefix}floatNote {{
        0%, 100% {{ transform: translate3d(0, 0, 0) rotate(0deg); }}
        50% {{ transform: translate3d(0, -14px, 0) rotate(-5deg); }}
      }}
      @keyframes {prefix}twinkle {{
        0%, 100% {{ opacity: .55; transform: scale(.86); }}
        50% {{ opacity: 1; transform: scale(1.16); }}
      }}
      @keyframes {prefix}sweep {{
        0% {{ transform: translateX(-420px) skewX(-18deg); }}
        62%, 100% {{ transform: translateX({HERO_W + 420}px) skewX(-18deg); }}
      }}
      @keyframes {prefix}edgeRun {{
        0% {{ stroke-dashoffset: 0; }}
        100% {{ stroke-dashoffset: -100; }}
      }}
      @keyframes {prefix}bar {{
        0%, 100% {{ transform: scaleY(.35); }}
        50% {{ transform: scaleY(1); }}
      }}
      .{prefix}aura {{ animation: {prefix}auraPulse 7s ease-in-out infinite; }}
      .{prefix}aura.b {{ animation-delay: -3.2s; }}
      .{prefix}note {{ animation: {prefix}floatNote 4.8s ease-in-out infinite; }}
      .{prefix}note.n2 {{ animation-duration: 5.8s; animation-delay: -1.4s; }}
      .{prefix}note.n3 {{ animation-duration: 6.4s; animation-delay: -2.6s; }}
      .{prefix}note.n4 {{ animation-duration: 5.2s; animation-delay: -3.4s; }}
      .{prefix}note.n5 {{ animation-duration: 6.8s; animation-delay: -0.8s; }}
      .{prefix}twinkle {{ animation: {prefix}twinkle 3.4s ease-in-out infinite; }}
      .{prefix}twinkle.t2 {{ animation-duration: 4.2s; animation-delay: -1.3s; }}
      .{prefix}twinkle.t3 {{ animation-duration: 3.8s; animation-delay: -2.1s; }}
      .{prefix}twinkle.t4 {{ animation-duration: 4.8s; animation-delay: -0.6s; }}
      .{prefix}sweep {{ animation: {prefix}sweep 9s ease-in-out infinite; }}
      .{prefix}edge-run {{ animation: {prefix}edgeRun 7s linear infinite; }}
      .{prefix}bar {{ transform-box: fill-box; transform-origin: bottom; animation: {prefix}bar 1.4s ease-in-out infinite; }}
      .{prefix}bar.b2 {{ animation-delay: -.25s; }}
      .{prefix}bar.b3 {{ animation-delay: -.5s; }}
      .{prefix}bar.b4 {{ animation-delay: -.75s; }}
      .{prefix}bar.b5 {{ animation-delay: -1s; }}
    }}
    '''

    def note(x: float, y: float, scale: float, fill: str, cls: str = "") -> str:
        return (
            f'<g transform="translate({x} {y}) scale({scale})">'
            f'<g class="{prefix}note {cls}">'
            f'<path d="M0 18 L0 0 L22 -6 L22 12" fill="none" stroke="{fill}" stroke-width="2.4" '
            f'stroke-linecap="round" stroke-linejoin="round" opacity=".9"/>'
            f'<ellipse cx="-5" cy="19" rx="6.4" ry="4.6" fill="{fill}" opacity=".92" '
            f'transform="rotate(-18 -5 19)"/>'
            f'<ellipse cx="17" cy="13" rx="6.4" ry="4.6" fill="{fill}" opacity=".92" '
            f'transform="rotate(-18 17 13)"/>'
            f"</g></g>"
        )

    def star(x: float, y: float, r: float, fill: str, cls: str = "") -> str:
        return (
            f'<g transform="translate({x} {y})">'
            f'<g class="{prefix}twinkle {cls}">'
            f'<path d="M0 -{r:.1f} L{r * 0.28:.1f} -{r * 0.28:.1f} L{r:.1f} 0 '
            f'L{r * 0.28:.1f} {r * 0.28:.1f} L0 {r:.1f} L-{r * 0.28:.1f} {r * 0.28:.1f} '
            f'L-{r:.1f} 0 L-{r * 0.28:.1f} -{r * 0.28:.1f} Z" fill="{fill}"/>'
            f"</g></g>"
        )

    # Flowing bars in the bottom-right corner, drawn with a translucent glass pill
    bars = ""
    for i in range(7):
        bx = 1210 + i * 12
        height = 10 + (i % 4) * 7
        bars += (
            f'<rect class="{prefix}bar b{(i % 5) + 1}" x="{bx}" y="{734 - height}" width="5" '
            f'height="{height}" rx="2.5" fill="url(#{prefix}noteA)" opacity=".9"/>'
        )

    body = f'''
  <g clip-path="url(#{prefix}clip)">
    <image href="{image}" x="0" y="0" width="{HERO_W}" height="{HERO_H}" preserveAspectRatio="xMidYMid slice"/>
    <ellipse class="{prefix}aura" cx="1180" cy="120" rx="330" ry="230" fill="url(#{prefix}auraA)"/>
    <ellipse class="{prefix}aura b" cx="180" cy="700" rx="380" ry="250" fill="url(#{prefix}auraB)"/>
    <rect x="0" y="0" width="{HERO_W}" height="{HERO_H}" fill="url(#{prefix}vignette)"/>
    <rect class="{prefix}sweep" x="0" y="-220" width="200" height="1240" fill="url(#{prefix}shine)" opacity="{shine_opacity}" transform="translate(-420 0) skewX(-18)"/>

    {note(300, 620, 1.05, f"url(#{prefix}noteA)", "n1")}
    {note(690, 120, 0.86, f"url(#{prefix}noteB)", "n2")}
    {note(905, 640, 1.18, f"url(#{prefix}noteB)", "n3")}
    {note(1235, 560, 0.78, f"url(#{prefix}noteA)", "n4")}
    {note(470, 300, 0.62, f"url(#{prefix}noteA)", "n5")}

    {star(205, 500, 13, "#FFFFFF", "t1")}
    {star(640, 250, 10, "#FFFFFF", "t2")}
    {star(770, 700, 12, "#FFFFFF", "t3")}
    {star(1260, 205, 11, "#FFFFFF", "t4")}

    <g opacity=".94">
      <rect x="1122" y="704" width="182" height="46" rx="23" fill="#0B1622" opacity=".24"/>
      <rect x="1122.75" y="704.75" width="180.5" height="44.5" rx="22.25" fill="none" stroke="#FFFFFF" stroke-opacity=".38"/>
      <text x="1146" y="733" font-family="{SANS}" font-size="11" font-weight="700" fill="#FFFFFF" letter-spacing="1.5">CODING</text>
      {bars}
    </g>
  </g>

  <rect x="1.5" y="1.5" width="{HERO_W - 3}" height="{HERO_H - 3}" rx="25" fill="none" stroke="url(#{prefix}edge)" stroke-width="3"/>
  <rect x="9" y="9" width="{HERO_W - 18}" height="{HERO_H - 18}" rx="19" fill="none" stroke="url(#{prefix}edge)" stroke-width="10" opacity=".14"/>
  <rect class="{prefix}edge-run" x="10" y="10" width="{HERO_W - 20}" height="{HERO_H - 20}" rx="18" fill="none" stroke="#FFFFFF" stroke-opacity=".65" stroke-width="2.4" pathLength="100" stroke-dasharray="7 93" stroke-linecap="round"/>
    '''

    return wrap_svg(HERO_W, HERO_H, defs, style, body, "Ryoko animated illustration")


# ---------------------------------------------------------------------------
# Wordmark
# ---------------------------------------------------------------------------

def build_wordmark(scheme: str = "light") -> str:
    width, height = 1200, 320
    dark = scheme == "dark"
    ink_stops = (
        ("0%", "#7FC4E8"), ("40%", "#A9D8FF"), ("74%", "#C8B6FF"), ("100%", "#F2A6C6")
    ) if dark else (
        ("0%", "#1E5F82"), ("46%", "#3F93C4"), ("76%", "#8FBFE2"), ("100%", "#F2A6C6")
    )
    ink_markup = "".join(
        f'<stop offset="{offset}" stop-color="{colour}"/>' for offset, colour in ink_stops
    )
    glow_a = "#6BE5FF" if dark else "#7FC4E8"
    glow_b = "#FF9CC8" if dark else "#F2A6C6"
    halo_opacity = ".20" if dark else ".28"
    text_attrs = (
        f'x="600" y="216" text-anchor="middle" font-family="{FONT}" font-size="220" '
        f'font-weight="700" letter-spacing="4"'
    )
    defs = f'''
    <linearGradient id="wm_ink" x1="160" y1="80" x2="1040" y2="250" gradientUnits="userSpaceOnUse">
      {ink_markup}
    </linearGradient>
    <linearGradient id="wm_sweep" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset="45%" stop-color="#FFFFFF" stop-opacity=".72"/>
      <stop offset="55%" stop-color="#FFFFFF" stop-opacity=".72"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="wm_clip"><text {text_attrs} fill="#FFFFFF">Ryoko</text></clipPath>
    <radialGradient id="wm_halo" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#7FC4E8" stop-opacity="{halo_opacity}"/>
      <stop offset="100%" stop-color="#7FC4E8" stop-opacity="0"/>
    </radialGradient>
    '''
    style = '''
    @media (prefers-reduced-motion: no-preference) {
      @keyframes wmBreathe {
        0%, 100% { opacity: .38; }
        50% { opacity: .85; }
      }
      @keyframes wmSweep {
        0% { transform: translateX(-620px) skewX(-16deg); }
        55%, 100% { transform: translateX(700px) skewX(-16deg); }
      }
      @keyframes wmLine {
        0% { transform: scaleX(.2); opacity: .2; }
        100% { transform: scaleX(1); opacity: .65; }
      }
      @keyframes wmTwinkle {
        0%, 100% { opacity: .35; transform: scale(.85); }
        50% { opacity: 1; transform: scale(1.15); }
      }
      .wm-glow { animation: wmBreathe 5.6s ease-in-out infinite; }
      .wm-sweep { animation: wmSweep 8.5s ease-in-out infinite; }
      .wm-line { transform-box: fill-box; transform-origin: center; animation: wmLine 1.4s cubic-bezier(.16,1,.3,1) .2s both; }
      .wm-star { transform-box: fill-box; transform-origin: center; animation: wmTwinkle 3.8s ease-in-out infinite; }
      .wm-star.s2 { animation-duration: 4.6s; animation-delay: -1.2s; }
      .wm-star.s3 { animation-duration: 4.2s; animation-delay: -2.4s; }
    }
    '''
    body = f'''
  <ellipse cx="600" cy="150" rx="430" ry="130" fill="url(#wm_halo)"/>
  <text class="wm-glow" {text_attrs} fill="none" stroke="{glow_a}" stroke-width="42" opacity=".14">Ryoko</text>
  <text class="wm-glow" {text_attrs} fill="none" stroke="{glow_a}" stroke-width="24" opacity=".20">Ryoko</text>
  <text class="wm-glow" {text_attrs} fill="none" stroke="{glow_b}" stroke-width="11" opacity=".18">Ryoko</text>
  <text {text_attrs} fill="url(#wm_ink)" filter="none">Ryoko</text>
  <g clip-path="url(#wm_clip)">
    <rect class="wm-sweep" x="0" y="40" width="170" height="220" fill="url(#wm_sweep)" opacity=".9" transform="translate(-620 0) skewX(-16)"/>
  </g>
  <rect class="wm-line" x="528" y="292" width="144" height="3" rx="1.5" fill="url(#wm_ink)"/>
  <rect x="500" y="292.5" width="200" height="2" rx="1" fill="url(#wm_ink)" opacity=".22"/>
  <g class="wm-star"><path d="M238 84 L242 96 L254 100 L242 104 L238 116 L234 104 L222 100 L234 96 Z" fill="{glow_b}"/></g>
  <g class="wm-star s2"><path d="M948 96 L951 105 L960 108 L951 111 L948 120 L945 111 L936 108 L945 105 Z" fill="{glow_a}"/></g>
  <g class="wm-star s3"><circle cx="968" cy="264" r="4.5" fill="#C8B6FF"/></g>
    '''
    return wrap_svg(width, height, defs, style, body, "Ryoko")


# ---------------------------------------------------------------------------
# Section marker
# ---------------------------------------------------------------------------

def build_section_mark() -> str:
    defs = '''
    <linearGradient id="sm_ink" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#7FC4E8"/>
      <stop offset="52%" stop-color="#4FA6D2"/>
      <stop offset="100%" stop-color="#F2A6C6"/>
    </linearGradient>
    '''
    style = '''
    @media (prefers-reduced-motion: no-preference) {
      @keyframes smPulse {
        0%, 100% { opacity: .32; transform: scaleY(.9); }
        50% { opacity: .88; transform: scaleY(1.04); }
      }
      .sm-glow { transform-box: fill-box; transform-origin: center; animation: smPulse 3.6s ease-in-out infinite; }
    }
    '''
    body = '''
  <rect class="sm-glow" x="0" y="-1" width="12" height="26" rx="6" fill="#7FC4E8" opacity=".32"/>
  <rect x="2.5" y="1" width="7" height="22" rx="3.5" fill="url(#sm_ink)"/>
  <rect x="4" y="3" width="1.4" height="18" rx=".7" fill="#FFFFFF" opacity=".55"/>
    '''
    return wrap_svg(12, 24, defs, style, body, "")


# ---------------------------------------------------------------------------
# Toolchain panel
# ---------------------------------------------------------------------------

TECH_ORDER = [
    ["go", "cpp", "python", "lua", "bash"],
    ["linux", "nixos", "docker", "redis", "mysql"],
    ["neovim", "kitty", "niri", "git", "pytorch"],
]


def inline_svg(path: Path) -> tuple[str, int, int]:
    """Return (inner markup, width, height) for embedding a standalone SVG inline.

    The tech badges have no <defs>/<style>/ids, so inlining them is safe and
    lets every renderer use the page's font stack for the pill labels.
    """
    import re

    raw = path.read_text(encoding="utf-8")
    wm = re.search(r'width="([0-9.]+)"', raw[:400])
    hm = re.search(r'height="([0-9.]+)"', raw[:400])
    vm = re.search(r'viewBox="([^"]+)"', raw[:400])
    inner = re.sub(r"^.*?<svg[^>]*>", "", raw, count=1, flags=re.S)
    inner = re.sub(r"</svg>\s*$", "", inner, flags=re.S)
    inner = re.sub(r"<title>.*?</title>", "", inner, count=1, flags=re.S)
    return inner, int(float(wm.group(1))), int(float(hm.group(1)))


def build_toolchain() -> str:
    width, height = 1200, 212
    pill_h = 42.0
    gap = 30.0
    rows = []
    y_positions = [16.0, 85.0, 154.0]
    for row_index, names in enumerate(TECH_ORDER):
        entries = []
        for name in names:
            path = TECH / f"{name}.svg"
            inner, sw, sh = inline_svg(path)
            entries.append((name, path, sw / sh * pill_h))
        total = sum(w for _, _, w in entries) + gap * (len(entries) - 1)
        x = (width - total) / 2.0
        for name, path, pw in entries:
            rows.append((name, path, x, y_positions[row_index], pw))
            x += pw + gap

    defs = '''
    <radialGradient id="tc_glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#7FC4E8" stop-opacity=".42"/>
      <stop offset="55%" stop-color="#C8B6FF" stop-opacity=".16"/>
      <stop offset="100%" stop-color="#F2A6C6" stop-opacity="0"/>
    </radialGradient>
    '''
    style = '''
    .tc-chip { transform-box: fill-box; transform-origin: center; transition: transform .28s cubic-bezier(.16,1,.3,1), filter .28s ease; }
    .tc-chip:hover { transform: translateY(-4px) scale(1.06); filter: drop-shadow(0 5px 8px rgba(51,136,187,.32)); }
    @media (prefers-reduced-motion: no-preference) {
      @keyframes tcHalo {
        0%, 100% { opacity: .35; }
        50% { opacity: .7; }
      }
      .tc-halo { animation: tcHalo 4.6s ease-in-out infinite; }
      .tc-halo.h2 { animation-delay: -1.5s; }
      .tc-halo.h3 { animation-delay: -3s; }
    }
    '''
    chips = []
    for index, (name, path, x, y, pw) in enumerate(rows):
        inner, sw, sh = inline_svg(path)
        chips.append(
            f'<g transform="translate({x:.1f} {y:.1f})">'
            f'<g class="tc-chip">'
            f'<ellipse class="tc-halo h{(index % 3) + 1}" cx="{pw / 2:.1f}" cy="{pill_h / 2:.1f}" '
            f'rx="{pw / 2 + 16:.1f}" ry="28" fill="url(#tc_glow)"/>'
            f'<svg x="0" y="0" width="{pw:.1f}" height="{pill_h:.1f}" viewBox="0 0 {sw} {sh}" '
            f'preserveAspectRatio="xMidYMid meet">{inner}</svg>'
            f"</g></g>"
        )
    body = "\n  ".join(chips)
    return wrap_svg(width, height, defs, style, body, "Toolchain")


# ---------------------------------------------------------------------------
# Footer sound wave
# ---------------------------------------------------------------------------

def build_footer_wave() -> str:
    width, height = 1200, 104
    defs = '''
    <linearGradient id="fw_line" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#7FC4E8" stop-opacity=".1"/>
      <stop offset="18%" stop-color="#7FC4E8" stop-opacity=".75"/>
      <stop offset="55%" stop-color="#C8B6FF" stop-opacity=".8"/>
      <stop offset="100%" stop-color="#F2A6C6" stop-opacity=".65"/>
    </linearGradient>
    <linearGradient id="fw_note" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#7FC4E8"/>
      <stop offset="100%" stop-color="#F2A6C6"/>
    </linearGradient>
    '''
    # gentle guitar-like waveform
    wave = (
        "M60 58 C110 58 120 40 160 40 C205 40 210 76 255 76 "
        "C300 76 305 34 350 34 C395 34 402 74 448 74 "
        "C494 74 500 44 545 44 C590 44 600 66 646 66 "
        "C692 66 700 36 746 36 C792 36 800 72 846 72 "
        "C892 72 900 46 946 46 C992 46 1000 64 1046 64 "
        "C1082 64 1100 54 1140 54"
    )
    defs += f'<path id="fw_path" d="{wave}" fill="none"/>'
    style = '''
    @media (prefers-reduced-motion: no-preference) {
      @keyframes fwDraw {
        0% { stroke-dashoffset: 1500; }
        100% { stroke-dashoffset: 0; }
      }
      @keyframes fwBob {
        0%, 100% { transform: translateY(0) rotate(-4deg); }
        50% { transform: translateY(-5px) rotate(3deg); }
      }
      @keyframes fwHeart {
        0%, 100% { opacity: .45; transform: scale(.9); }
        50% { opacity: 1; transform: scale(1.1); }
      }
      .fw-wave { stroke-dasharray: 1500; animation: fwDraw 2.4s cubic-bezier(.16,1,.3,1) .15s both; }
      .fw-note { transform-box: fill-box; transform-origin: center; animation: fwBob 4.2s ease-in-out infinite; }
      .fw-note.n2 { animation-duration: 5.1s; animation-delay: -1.6s; }
      .fw-note.n3 { animation-duration: 4.7s; animation-delay: -2.8s; }
      .fw-heart { transform-box: fill-box; transform-origin: center; animation: fwHeart 3.6s ease-in-out infinite; }
    }
    '''
    staff = "\n  ".join(
        f'<line x1="60" y1="{y}" x2="1140" y2="{y}" stroke="#7FC4E8" stroke-opacity=".18" stroke-width="1"/>'
        for y in (42, 50, 58, 66, 74)
    )
    body = f'''
  <g>
    {staff}
    <use href="#fw_path" stroke="#7FC4E8" stroke-opacity=".10" stroke-width="12" stroke-linecap="round"/>
    <use href="#fw_path" stroke="url(#fw_line)" stroke-width="3.2" stroke-linecap="round" opacity=".7"/>
    <use class="fw-wave" href="#fw_path" stroke="url(#fw_line)" stroke-width="3.2" stroke-linecap="round"/>
  </g>
  <g class="fw-note" transform="translate(188 18)">
    <path d="M0 24 L0 0 L20 -5 L20 18" fill="none" stroke="url(#fw_note)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
    <ellipse cx="-4.5" cy="25" rx="5.6" ry="4" fill="url(#fw_note)" transform="rotate(-18 -4.5 25)"/>
    <ellipse cx="15.5" cy="19" rx="5.6" ry="4" fill="url(#fw_note)" transform="rotate(-18 15.5 19)"/>
  </g>
  <g class="fw-note n2" transform="translate(700 22)">
    <path d="M0 22 L0 0 L18 -4 L18 17" fill="none" stroke="url(#fw_note)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
    <ellipse cx="-4" cy="23" rx="5.2" ry="3.7" fill="url(#fw_note)" transform="rotate(-18 -4 23)"/>
    <ellipse cx="14" cy="18" rx="5.2" ry="3.7" fill="url(#fw_note)" transform="rotate(-18 14 18)"/>
  </g>
  <g class="fw-note n3" transform="translate(1010 16)">
    <path d="M0 26 L0 0 L20 -5 L20 20" fill="none" stroke="url(#fw_note)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
    <ellipse cx="-4.5" cy="27" rx="5.8" ry="4.1" fill="url(#fw_note)" transform="rotate(-18 -4.5 27)"/>
    <ellipse cx="15.5" cy="21" rx="5.8" ry="4.1" fill="url(#fw_note)" transform="rotate(-18 15.5 21)"/>
  </g>
  <g class="fw-heart" transform="translate(600 86)">
    <path d="M0 3 C0 -2 -7 -3 -7 3 C-7 8 0 13 0 13 C0 13 7 8 7 3 C7 -3 0 -2 0 3 Z" fill="#F2A6C6"/>
  </g>
    '''
    return wrap_svg(width, height, defs, style, body, "")


# ---------------------------------------------------------------------------
# Chibi sticker
# ---------------------------------------------------------------------------

def build_chibi_sticker() -> str:
    size = 240
    avatar = data_uri(IMAGES / "chibi-avatar.jpg", "image/jpeg")
    defs = '''
    <clipPath id="cs_clip"><circle cx="120" cy="120" r="99"/></clipPath>
    <linearGradient id="cs_ring" x1="20" y1="20" x2="220" y2="220" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#7FC4E8"/>
      <stop offset="50%" stop-color="#C8B6FF"/>
      <stop offset="100%" stop-color="#F2A6C6"/>
    </linearGradient>
    <radialGradient id="cs_halo" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#F2A6C6" stop-opacity=".35"/>
      <stop offset="100%" stop-color="#7FC4E8" stop-opacity="0"/>
    </radialGradient>
    '''
    style = '''
    .cs-float { transform-box: fill-box; transform-origin: center; }
    @media (prefers-reduced-motion: no-preference) {
      @keyframes csBob {
        0%, 100% { transform: translateY(0) rotate(-1.2deg); }
        50% { transform: translateY(-6px) rotate(1.2deg); }
      }
      @keyframes csTwinkle {
        0%, 100% { opacity: .35; transform: scale(.8); }
        50% { opacity: 1; transform: scale(1.15); }
      }
      .cs-float { animation: csBob 4.6s ease-in-out infinite; }
      .cs-star { transform-box: fill-box; transform-origin: center; animation: csTwinkle 3.8s ease-in-out infinite; }
      .cs-star.s2 { animation-duration: 4.4s; animation-delay: -1.4s; }
    }
    '''
    body = f'''
  <circle cx="120" cy="120" r="116" fill="url(#cs_halo)"/>
  <g class="cs-float">
    <circle cx="120" cy="120" r="105" fill="#FFFFFF" opacity=".95"/>
    <g clip-path="url(#cs_clip)">
      <image href="{avatar}" x="6" y="0" width="228" height="228" preserveAspectRatio="xMidYMid slice"/>
    </g>
    <circle cx="120" cy="120" r="99" fill="none" stroke="#FFFFFF" stroke-width="6"/>
    <circle cx="120" cy="120" r="105" fill="none" stroke="url(#cs_ring)" stroke-width="3"/>
  </g>
  <g class="cs-star"><path d="M34 54 L37 63 L46 66 L37 69 L34 78 L31 69 L22 66 L31 63 Z" fill="#7FC4E8"/></g>
  <g class="cs-star s2"><path d="M206 178 L208.5 186 L216 188.5 L208.5 191 L206 199 L203.5 191 L196 188.5 L203.5 186 Z" fill="#F2A6C6"/></g>
    '''
    return wrap_svg(size, size, defs, style, body, "Chibi Anon sticker")


def main() -> None:
    BRANDING.mkdir(parents=True, exist_ok=True)
    write_svg(BRANDING / "hero-light.svg", build_hero("light"))
    write_svg(BRANDING / "hero-dark.svg", build_hero("dark"))
    write_svg(BRANDING / "wordmark.svg", build_wordmark("light"))
    write_svg(BRANDING / "wordmark-dark.svg", build_wordmark("dark"))
    write_svg(BRANDING / "section-mark.svg", build_section_mark())
    write_svg(BRANDING / "toolchain.svg", build_toolchain())
    write_svg(BRANDING / "footer-wave.svg", build_footer_wave())
    write_svg(IMAGES / "chibi-sticker.svg", build_chibi_sticker())
    print("profile assets rebuilt")


if __name__ == "__main__":
    main()
