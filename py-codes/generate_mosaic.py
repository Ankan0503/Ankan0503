#!/usr/bin/env python3
"""
generate_mosaic.py
-------------------
Fetches GitHub contribution data for Ankan0503 and renders a flat,
fixed-size pixel-grid mosaic (light theme). Colour carries the commit
count instead of size, so long streaks can never make cells overlap.

Run by GitHub Actions daily. Commit the output SVG to the repo root.
Requires env var: GH_TOKEN (a GitHub personal access token with read:user scope)
"""

import os
import random
from datetime import datetime, timedelta

from pixel_font import font_face_style

USERNAME   = "Ankan0503"
GH_TOKEN   = os.environ.get("GH_TOKEN", "")
OUTPUT_SVG = "pixel-mosaic.svg"

# ── Palette (light / paper) ────────────────────────────────────────────────
PAPER      = "#f7f4ea"
GRID_LINE  = "#e6e0cf"
INK        = "#2b2617"
TEXT_MID   = "#7c7460"
TEXT_DIM   = "#a29a84"
SCALE      = ["#eae6da", "#bfe0b4", "#8fd19e", "#f0a93a", "#d97706"]  # level 0-4

# ── Layout ───────────────────────────────────────────────────────────────
CW = CH = 11
CGAP = 3
STEP = CW + CGAP
COLS, ROWS = 52, 7

PAD_X, PAD_TOP, PAD_BOTTOM = 36, 54, 46
GRID_W = COLS * STEP - CGAP
GRID_H = ROWS * STEP - CGAP
CARD_W = GRID_W + PAD_X * 2
CARD_H = PAD_TOP + GRID_H + PAD_BOTTOM

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def fetch_contributions():
    if not GH_TOKEN:
        print("Warning: No GH_TOKEN found. Using random demo data.")
        weeks = []
        base = datetime.now() - timedelta(weeks=52)
        for w in range(52):
            days = []
            for d in range(7):
                dt = base + timedelta(weeks=w, days=d)
                days.append({"date": dt.strftime("%Y-%m-%d"),
                             "contributionCount": random.choices(
                                 [0, 1, 2, 4, 7, 12],
                                 weights=[30, 20, 20, 15, 10, 5])[0]})
            weeks.append({"contributionDays": days})
        return weeks

    import requests
    headers = {"Authorization": f"bearer {GH_TOKEN}"}
    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"login": USERNAME}},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


def commit_level(count):
    if count == 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 9:
        return 3
    return 4


def weeks_to_levels(weeks):
    """52x7 grid of levels (0-4), padded/truncated to exactly 52 weeks."""
    grid = []
    for week in weeks[-52:]:
        days = week["contributionDays"]
        grid.append([commit_level(d["contributionCount"]) for d in days] + [0] * (7 - len(days)))
    while len(grid) < 52:
        grid.insert(0, [0] * 7)
    return grid


def current_streak(weeks):
    """
    Consecutive active days counting back from today.
    If today has 0 commits so far, streak from yesterday is counted.
    """
    all_days = []
    for week in weeks:
        for day in week.get("contributionDays", []):
            all_days.append(day.get("contributionCount", 0))

    if not all_days:
        return 0

    streak = 0
    start_idx = len(all_days) - 1

    # If today (last recorded day) has no commits yet, don't break the streak from yesterday
    if all_days[start_idx] == 0 and start_idx > 0:
        start_idx -= 1

    for i in range(start_idx, -1, -1):
        if all_days[i] > 0:
            streak += 1
        else:
            break
    return streak


def render_mosaic_svg(levels, streak):
    rects = []
    for wi, week in enumerate(levels):
        for di, lvl in enumerate(week):
            x = PAD_X + wi * STEP
            y = PAD_TOP + di * STEP
            rects.append(f'<rect x="{x}" y="{y}" width="{CW}" height="{CH}" rx="2" fill="{SCALE[lvl]}"/>')

    legend_x = CARD_W - 196
    legend_y = CARD_H - 22
    legend = [f'<text x="{legend_x - 30}" y="{legend_y + 8}" font-family="monospace" font-size="10" '
              f'letter-spacing="1" fill="{TEXT_DIM}">LESS</text>']
    for i, col in enumerate(SCALE):
        lx = legend_x + i * 15
        legend.append(f'<rect x="{lx}" y="{legend_y}" width="10" height="10" rx="2" fill="{col}"/>')
    legend.append(f'<text x="{legend_x + len(SCALE) * 15 + 8}" y="{legend_y + 8}" font-family="monospace" '
                   f'font-size="10" letter-spacing="1" fill="{TEXT_DIM}">MORE</text>')

    svg = f'''<svg width="{CARD_W}" height="{CARD_H}" viewBox="0 0 {CARD_W} {CARD_H}"
  xmlns="http://www.w3.org/2000/svg">
{font_face_style()}
<rect width="{CARD_W}" height="{CARD_H}" rx="10" fill="{PAPER}" stroke="{GRID_LINE}" stroke-width="1"/>
<text x="{PAD_X}" y="32" class="pixel" font-size="16" letter-spacing="2" fill="{INK}">CONTRIBUTIONS</text>
{"".join(rects)}
<text x="{PAD_X}" y="{CARD_H - 15}" font-family="monospace" font-size="11" fill="{TEXT_MID}">{streak}-day streak</text>
{"".join(legend)}
</svg>'''
    return svg


if __name__ == "__main__":
    print("Fetching contributions...")
    weeks = fetch_contributions()
    levels = weeks_to_levels(weeks)
    streak = current_streak(weeks)
    print(f"Streak: {streak} days")

    svg_content = render_mosaic_svg(levels, streak)
    with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Saved -> {OUTPUT_SVG} ({len(svg_content)//1024} KB)")
