#!/usr/bin/env python3
"""
generate_stats.py
-------------------
Fetches lifetime GitHub stats for Ankan0503 and renders them matching the reference:
- Left: Single integrated "Ankan's GitHub Stats" card with minimalist icons & vertical list
- Right: Warm Ivory STREAK card with orange border & clipped campfire

Run by GitHub Actions daily. Commit the output SVG to the repo root.
Requires env var: GH_TOKEN (a GitHub personal access token with read:user scope)
"""

import base64
import os
import random
from datetime import datetime, timezone

from pixel_font import font_face_style

USERNAME   = "Ankan0503"
GH_TOKEN   = os.environ.get("GH_TOKEN", "")
OUTPUT_SVG = "stats.svg"
CAMPFIRE   = os.path.join("logos", "campfire-streak.avif")

PAPER      = "#f7f4ea"
GRID_LINE  = "#e6e0cf"
INK        = "#2b2617"
TEXT_MID   = "#7c7460"
MC_GREEN   = "#3F7A20"

W = 797
PAD_X = 36
PAD_TOP = 54
PAD_BOTTOM = 28

STATS_QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    pullRequests { totalCount }
    repositories(first: 100, ownerAffiliations: [OWNER], isFork: false) {
      totalCount
      nodes { stargazerCount }
    }
  }
}
"""


def year_alias_query(login, years):
    """One request, one aliased contributionsCollection per calendar year."""
    parts = []
    for i, year in enumerate(years):
        frm = f"{year}-01-01T00:00:00Z"
        to = f"{year + 1}-01-01T00:00:00Z"
        parts.append(f'''
        y{i}: contributionsCollection(from: "{frm}", to: "{to}") {{
          totalCommitContributions
          contributionCalendar {{
            weeks {{ contributionDays {{ date contributionCount }} }}
          }}
        }}''')
    return f'query($login: String!) {{ user(login: $login) {{ {"".join(parts)} }} }}'


def gql(query, variables):
    import requests
    headers = {"Authorization": f"bearer {GH_TOKEN}"}
    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def longest_and_current_streak(all_days):
    """Returns (current, longest) streak."""
    if not all_days:
        return 0, 0

    longest = run = 0
    for count in all_days:
        run = run + 1 if count > 0 else 0
        longest = max(longest, run)

    current = 0
    i = len(all_days) - 1
    if all_days[i] == 0 and i > 0:
        i -= 1
    while i >= 0 and all_days[i] > 0:
        current += 1
        i -= 1
    return current, longest


def fetch_stats():
    if not GH_TOKEN:
        print("Warning: No GH_TOKEN found. Using demo data.")
        rng = random.Random(3)
        days = [rng.choices([0, 1, 2, 4, 7], weights=[35, 25, 20, 12, 8])[0] for _ in range(900)]
        current, longest = longest_and_current_streak(days)
        return {
            "repos": 18, "commits": 3482, "prs": 41,
            "followers": 27, "stars": 62,
            "current_streak": current, "longest_streak": longest,
        }

    user = gql(STATS_QUERY, {"login": USERNAME})["user"]
    repos = user["repositories"]
    stars = sum(n["stargazerCount"] for n in repos["nodes"])

    created = datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    this_year = datetime.now(timezone.utc).year
    years = list(range(created.year, this_year + 1))

    yearly = gql(year_alias_query(USERNAME, years), {"login": USERNAME})["user"]

    total_commits = 0
    all_days = []
    for i in range(len(years)):
        y = yearly[f"y{i}"]
        total_commits += y["totalCommitContributions"]
        for week in y["contributionCalendar"]["weeks"]:
            for day in week["contributionDays"]:
                all_days.append(day["contributionCount"])

    current, longest = longest_and_current_streak(all_days)

    return {
        "repos": repos["totalCount"],
        "commits": total_commits,
        "prs": user["pullRequests"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "stars": stars,
        "current_streak": current,
        "longest_streak": longest,
    }


## ── Minimalist monochrome icons for stat rows matching reference ──────────
ICON_COLOR  = "#334155"  # dark charcoal / slate
LABEL_COLOR = "#334155"
CARD_BG     = "#fffdf6"  # warm cream interior

def icon_repo(x, y):
    # Minimalist folder: tab on top + rounded folder body
    return (f'<path d="M{x+2:.1f} {y+3.5:.1f} h3.5 l2 2 h6 c0.8 0 1.5 0.7 1.5 1.5 v6.5 c0 0.8 -0.7 1.5 -1.5 1.5 h-11.5 c-0.8 0 -1.5 -0.7 -1.5 -1.5 v-8.5 c0 -0.8 0.7 -1.5 1.5 -1.5 z" '
            f'fill="none" stroke="{ICON_COLOR}" stroke-width="1.5" stroke-linejoin="round"/>')


def icon_commit(x, y):
    # Minimalist circular gauge / commit clock
    cx, cy = x + 8.0, y + 8.0
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="6.5" fill="none" stroke="{ICON_COLOR}" stroke-width="1.5"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="1.5" fill="{ICON_COLOR}"/>'
            f'<line x1="{cx:.1f}" y1="{cy-6.5:.1f}" x2="{cx:.1f}" y2="{cy-4.0:.1f}" stroke="{ICON_COLOR}" stroke-width="1.5" stroke-linecap="round"/>'
            f'<line x1="{cx:.1f}" y1="{cy+4.0:.1f}" x2="{cx:.1f}" y2="{cy+6.5:.1f}" stroke="{ICON_COLOR}" stroke-width="1.5" stroke-linecap="round"/>'
            f'<line x1="{cx-6.5:.1f}" y1="{cy:.1f}" x2="{cx-4.0:.1f}" y2="{cy:.1f}" stroke="{ICON_COLOR}" stroke-width="1.5" stroke-linecap="round"/>'
            f'<line x1="{cx+4.0:.1f}" y1="{cy:.1f}" x2="{cx+6.5:.1f}" y2="{cy:.1f}" stroke="{ICON_COLOR}" stroke-width="1.5" stroke-linecap="round"/>')


def icon_star(x, y):
    # Minimalist 5-point star outline
    pts = [
        (8.0, 1.5), (10.0, 6.0), (14.8, 6.5), (11.2, 9.8), (12.3, 14.5),
        (8.0, 12.0), (3.7, 14.5), (4.8, 9.8), (1.2, 6.5), (6.0, 6.0)
    ]
    pts_str = " ".join(f"{x + px:.1f},{y + py:.1f}" for px, py in pts)
    return f'<polygon points="{pts_str}" fill="none" stroke="{ICON_COLOR}" stroke-width="1.5" stroke-linejoin="round"/>'


def icon_pr(x, y):
    # Minimalist git pull request loop icon
    return (f'<circle cx="{x+4:.1f}" cy="{y+4:.1f}" r="2" fill="none" stroke="{ICON_COLOR}" stroke-width="1.5"/>'
            f'<circle cx="{x+4:.1f}" cy="{y+12:.1f}" r="2" fill="none" stroke="{ICON_COLOR}" stroke-width="1.5"/>'
            f'<circle cx="{x+12:.1f}" cy="{y+7:.1f}" r="2" fill="none" stroke="{ICON_COLOR}" stroke-width="1.5"/>'
            f'<path d="M{x+4:.1f} {y+6:.1f} v4 M{x+12:.1f} {y+9:.1f} v1 c0 1.1 -0.9 2 -2 2 h-4" '
            f'fill="none" stroke="{ICON_COLOR}" stroke-width="1.5" stroke-linecap="round"/>')


def icon_followers(x, y):
    # Minimalist user / followers outline
    return (f'<circle cx="{x+6.5:.1f}" cy="{y+4.5:.1f}" r="2.8" fill="none" stroke="{ICON_COLOR}" stroke-width="1.5"/>'
            f'<path d="M{x+1.5:.1f} {y+13.5:.1f} c0 -2.8 2.2 -4.5 5 -4.5 c2.8 0 5 1.7 5 4.5" fill="none" stroke="{ICON_COLOR}" stroke-width="1.5" stroke-linecap="round"/>'
            f'<path d="M{x+12:.1f} {y+4:.1f} a2 2 0 0 1 0 3 M{x+13:.1f} {y+12.5:.1f} c1.2 -0.4 2 -1.4 2 -2.5" fill="none" stroke="{ICON_COLOR}" stroke-width="1.3" stroke-linecap="round"/>')


def icon_flame(x, y, color):
    return (f'<path d="M{x+7:.1f} {y+1:.1f} c2.5 3.5 -1.5 4.5 -0.8 8 c2.5 -0.8 3.5 -3.5 3.5 -3.5 c1.8 2.5 1 7 -2.5 8 '
            f'c-4.2 0.8 -7 -2.5 -6 -6 c0.8 -2.5 2.5 -2.5 2.5 -5 c0.8 1.8 1.8 1.8 1.8 1.8 c-0.8 -1.8 -0.8 -1.8 1.5 -3.3 z" fill="{color}"/>')


# Typography stack: clean, modern UI font inside cards
STATS_FONT = "Roboto, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"

FLAME_BG     = "#fef8ee"
FLAME_BORDER = "#ea580c"

# Box size controls (Ankan's GitHub Stats vs Streak)
MAIN_W   = 380    # Width of Ankan's GitHub Stats box
MAIN_H   = 196    # Height of Ankan's GitHub Stats box

STREAK_W = 249    # Width of the Streak box
STREAK_H = 196    # Height of the Streak box
GAP      = 16     # Gap between the two boxes

IMG_MARGIN = 18
IMG_MAX_H = 180
CAMPFIRE_BOTTOM_OFFSET = 48


def data_uri(path, mime):
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")


def bar_chart_icon(x, y):
    heights = [10, 15, 8, 18]
    colors = ["#bfe0b4", "#8fd19e", "#f0a93a", "#d97706"]
    parts = []
    for i, (h, c) in enumerate(zip(heights, colors)):
        parts.append(f'<rect x="{x + i*6}" y="{y + 18 - h}" width="4" height="{h}" fill="{c}" rx="1"/>')
    return "".join(parts)


def format_commits(count):
    if count >= 1000:
        return f"{count/1000:.1f}k+"
    return str(count)


def render_main_stats_card(x, y, w, h, stats):
    """Large integrated card displaying Ankan's GitHub Stats as a clean vertical list."""
    parts = [
        f'<rect x="{x:.1f}" y="{y}" width="{w}" height="{h}" rx="14" fill="{CARD_BG}" stroke="{GRID_LINE}" stroke-width="1"/>',
        f'<text x="{x + 24:.1f}" y="{y + 32}" font-family="{STATS_FONT}" font-weight="700" font-size="16" fill="{INK}">Ankan\'s GitHub Stats</text>',
    ]

    rows = [
        ("Total Repos",    str(stats["repos"]),            icon_repo),
        ("Total Commits",  format_commits(stats["commits"]), icon_commit),
        ("Total Stars",    str(stats["stars"]),            icon_star),
        ("Pull Requests",  str(stats["prs"]),              icon_pr),
        ("Followers",      str(stats["followers"]),        icon_followers),
    ]

    start_y = y + 62
    row_step = 26.5
    for i, (label, val, icon_fn) in enumerate(rows):
        ry = start_y + i * row_step
        # Icon
        parts.append(icon_fn(x + 24, ry - 12))
        # Label
        parts.append(
            f'<text x="{x + 50:.1f}" y="{ry:.1f}" font-family="{STATS_FONT}" '
            f'font-weight="500" font-size="13.5" fill="{LABEL_COLOR}">{label}</text>'
        )
        # Value left-aligned in a straight column
        num_x = x + 310
        parts.append(
            f'<text x="{num_x:.1f}" y="{ry:.1f}" text-anchor="start" font-family="{STATS_FONT}" '
            f'font-weight="700" font-size="14.5" fill="{INK}">{val}</text>'
        )

    return parts


def render_streak_card(x, y, w, h, stats):
    """Distinct streak card with warm ivory interior, orange accent border, and clipped campfire."""
    clip_def = f'<clipPath id="streakBoxClip"><rect x="{x:.1f}" y="{y}" width="{w}" height="{h}" rx="14"/></clipPath>'

    parts = [
        f'<rect x="{x:.1f}" y="{y}" width="{w}" height="{h}" rx="14" fill="{FLAME_BG}"/>'
    ]

    # Header: flame icon + STREAK
    parts.append(icon_flame(x + 20, y + 17, FLAME_BORDER))
    parts.append(
        f'<text x="{x + 42:.1f}" y="{y + 30}" font-family="{STATS_FONT}" '
        f'font-weight="700" font-size="13.5" letter-spacing="0.8" fill="{INK}">STREAK</text>'
    )

    # Two stat columns: Current + Longest Streak
    row_y = y + 56
    col_w = (w - 32) / 2
    STREAK_COL_SPREAD = 12  # increase outward separation from the divider
    cx1 = x + 16 + col_w * 0.5 - STREAK_COL_SPREAD
    cx2 = x + 16 + col_w * 1.5 + STREAK_COL_SPREAD

    # Column 1: Current Streak
    parts.append(
        f'<text x="{cx1:.1f}" y="{row_y + 20}" text-anchor="middle" font-family="{STATS_FONT}" '
        f'font-weight="700" font-size="19.5" fill="{INK}">{stats["current_streak"]} days</text>'
    )
    parts.append(
        f'<text x="{cx1:.1f}" y="{row_y + 39}" text-anchor="middle" font-family="{STATS_FONT}" '
        f'font-weight="500" font-size="12" fill="{TEXT_MID}">Current Streak</text>'
    )

    # Subtle column divider
    mid_x = x + w / 2
    parts.append(f'<line x1="{mid_x:.1f}" y1="{row_y}" x2="{mid_x:.1f}" y2="{row_y + 42}" stroke="{FLAME_BORDER}" stroke-width="1" opacity="0.3"/>')

    # Column 2: Longest Streak
    parts.append(
        f'<text x="{cx2:.1f}" y="{row_y + 20}" text-anchor="middle" font-family="{STATS_FONT}" '
        f'font-weight="700" font-size="19.5" fill="{INK}">{stats["longest_streak"]} days</text>'
    )
    parts.append(
        f'<text x="{cx2:.1f}" y="{row_y + 39}" text-anchor="middle" font-family="{STATS_FONT}" '
        f'font-weight="500" font-size="12" fill="{TEXT_MID}">Longest Streak</text>'
    )

    # Campfire image: clipped inside streak box, bottom tucked behind bottom border
    img = _campfire_size()
    if img:
        native_w, native_h = img
        img_w = w - IMG_MARGIN * 2
        img_h = img_w * native_h / native_w
        if img_h > IMG_MAX_H:
            img_h = IMG_MAX_H
            img_w = img_h * native_w / native_h
        img_x = x + w / 2 - img_w / 2
        img_y = y + h - img_h + CAMPFIRE_BOTTOM_OFFSET
        parts.append(
            f'<g clip-path="url(#streakBoxClip)">'
            f'<image href="{data_uri(CAMPFIRE, "image/avif")}" x="{img_x:.1f}" y="{img_y:.1f}" width="{img_w:.1f}" height="{img_h:.1f}"/>'
            f'</g>'
        )

    # Border stroke drawn over the image
    parts.append(
        f'<rect x="{x:.1f}" y="{y}" width="{w}" height="{h}" rx="14" '
        f'fill="none" stroke="{FLAME_BORDER}" stroke-width="1.2"/>'
    )

    return clip_def, parts


def _campfire_size():
    if not os.path.exists(CAMPFIRE):
        return None
    from PIL import Image
    with Image.open(CAMPFIRE) as im:
        return im.size


def render_stats_svg(stats):
    ty = PAD_TOP
    inner_w = W - PAD_X * 2
    streak_w = inner_w - MAIN_W - GAP

    main_parts = render_main_stats_card(PAD_X, ty, MAIN_W, MAIN_H, stats)
    streak_x = PAD_X + MAIN_W + GAP
    clip_def, streak_parts = render_streak_card(streak_x, ty, streak_w, STREAK_H, stats)

    card_h = PAD_TOP + max(MAIN_H, STREAK_H) + PAD_BOTTOM

    svg = f'''<svg width="{W}" height="{card_h}" viewBox="0 0 {W} {card_h}" xmlns="http://www.w3.org/2000/svg">
{font_face_style()}
<defs>{clip_def}</defs>
<rect width="{W}" height="{card_h}" rx="10" fill="{PAPER}" stroke="{GRID_LINE}" stroke-width="1"/>
{bar_chart_icon(PAD_X, 18)}
<text x="{PAD_X + 34}" y="34" class="pixel" font-size="16" letter-spacing="2" fill="{INK}">GITHUB STATS</text>
{"".join(main_parts)}
{"".join(streak_parts)}
</svg>'''
    return svg


if __name__ == "__main__":
    print("Fetching stats...")
    stats = fetch_stats()
    print(stats)

    svg_content = render_stats_svg(stats)
    with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Saved -> {OUTPUT_SVG} ({len(svg_content)//1024} KB)")
