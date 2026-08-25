#!/usr/bin/env python3
"""
generate_mosaic.py
-------------------
Fetches GitHub contribution data for Ankan0503 and renders a flat,
fixed-size pixel-grid mosaic (light theme). Colour carries the commit
count instead of size, so long streaks can never make cells overlap.

Month labels above the grid are derived from the real "date" fields in
each fetched week, not hardcoded -- so as months pass, the next Action
run just naturally prints whatever the live data says. No manual edits
needed here when a new month starts.

Run by GitHub Actions daily. Commit the output SVG to the repo root.
Requires env var: GH_TOKEN (a GitHub personal access token with read:user scope)
"""

import base64
import io
import os
import random
from datetime import datetime, timedelta

from PIL import Image

from pixel_font import font_face_style

USERNAME   = "Ankan0503"
GH_TOKEN   = os.environ.get("GH_TOKEN", "")
OUTPUT_SVG = "pixel-mosaic.svg"
TREE_HONEY = os.path.join("logos", "tree-honey-contrib.avif")

# Decorative corner image -- right-aligned, drawn *behind* the grid/text.
# Sized bigger than the freed-up column on purpose: it's meant to spill
# over the grid on the left and past the card's bottom edge, both fine
# since it's behind everything and the card simply clips what overflows.
TREE_DISPLAY_W = 260
TREE_Y_SHIFT = 45  # how far past the card's own bottom edge it hangs
TREE_X_SHIFT = 25  # 👈 Horizontal shift (positive = right, negative = left)
                    # note: unlike TREE_Y_SHIFT, this can't grow the canvas --
                    # CARD_W has to stay 797 to line up with every other card,
                    # so a large positive shift just clips against that edge

# ── Palette (light / paper) ────────────────────────────────────────────────
PAPER      = "#f7f4ea"
GRID_LINE  = "#e6e0cf"
INK        = "#2b2617"
TEXT_MID   = "#7c7460"
TEXT_DIM   = "#a29a84"
SCALE      = ["#eae6da", "#bfe0b4", "#8fd19e", "#f0a93a", "#d97706"]  # level 0-4

# ── Layout ───────────────────────────────────────────────────────────────
# Cells shrunk from 11/3 so the grid no longer spans the full card width,
# freeing a right-hand column for the tree-honey image without growing
# the card at all.
CW = CH = 9
CGAP = 2
STEP = CW + CGAP
COLS, ROWS = 52, 7

PAD_X, PAD_TOP, PAD_BOTTOM = 36, 54, 46
GRID_W = COLS * STEP - CGAP
GRID_H = ROWS * STEP - CGAP
CARD_W = 797  # fixed, matching every other card -- grid no longer defines it
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


def embed_tree_honey():
    """Scale the corner image to its display size and embed as AVIF --
    much smaller than PNG at this size (photo-like gradients, not flat
    pixel-art colour, so AVIF's real compression actually pays off here)."""
    if not os.path.exists(TREE_HONEY):
        return None, 0
    img = Image.open(TREE_HONEY).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    disp_h = round(TREE_DISPLAY_W * img.height / img.width)
    img = img.resize((TREE_DISPLAY_W, disp_h), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="AVIF", quality=45, speed=6)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/avif;base64,{b64}", disp_h


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


def week_months(weeks):
    """First-day month abbreviation for each of the (up to 52) week columns,
    padded the same way weeks_to_levels pads -- so index i here lines up
    with column i in the grid. Comes straight from the fetched dates, so
    it's always this run's actual calendar, not a fixed set of months."""
    months = []
    for week in weeks[-52:]:
        days = week["contributionDays"]
        if days:
            months.append(datetime.strptime(days[0]["date"], "%Y-%m-%d").strftime("%b"))
        else:
            months.append("")
    while len(months) < 52:
        months.insert(0, "")
    return months


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


def render_mosaic_svg(levels, months, streak):
    # tree-honey drawn first so it sits behind the grid and the text
    tree_img = ""
    tree_uri, tree_h = embed_tree_honey()
    if tree_uri:
        tree_x = CARD_W - PAD_X - TREE_DISPLAY_W + TREE_X_SHIFT
        tree_y = CARD_H - tree_h + TREE_Y_SHIFT
        tree_img = f'<image href="{tree_uri}" x="{tree_x}" y="{tree_y}" width="{TREE_DISPLAY_W}" height="{tree_h}"/>'

    month_labels = []
    prev_month, last_label_x = None, -999
    min_gap = STEP * 3  # skip a label that would crowd the previous one,
                         # same trade-off GitHub's own graph makes
    for wi, m in enumerate(months):
        if m and m != prev_month:
            x = PAD_X + wi * STEP
            if x - last_label_x >= min_gap:
                month_labels.append(
                    f'<text x="{x}" y="{PAD_TOP - 8}" font-family="monospace" font-size="10" '
                    f'letter-spacing="0.5" fill="{TEXT_DIM}">{m}</text>'
                )
                last_label_x = x
        prev_month = m or prev_month

    rects = []
    for wi, week in enumerate(levels):
        for di, lvl in enumerate(week):
            x = PAD_X + wi * STEP
            y = PAD_TOP + di * STEP
            rects.append(f'<rect x="{x}" y="{y}" width="{CW}" height="{CH}" rx="2" fill="{SCALE[lvl]}"/>')

    legend_x = PAD_X + 180
    legend_y = CARD_H - 22
    legend = [f'<text x="{legend_x - 30}" y="{legend_y + 8}" font-family="monospace" font-size="10" '
              f'letter-spacing="1" fill="{TEXT_DIM}">LESS</text>']
    for i, col in enumerate(SCALE):
        lx = legend_x + i * 15
        legend.append(f'<rect x="{lx}" y="{legend_y}" width="10" height="10" rx="2" fill="{col}"/>')
    legend.append(f'<text x="{legend_x + len(SCALE) * 15 + 8}" y="{legend_y + 8}" font-family="monospace" '
                   f'font-size="10" letter-spacing="1" fill="{TEXT_DIM}">MORE</text>')

    # canvas taller than the card itself, purely so the tree can visibly
    # hang past the card's bottom edge instead of being invisibly clipped
    # -- <img> clips to the SVG's own canvas no matter what "overflow"
    # says, so the only way to show a spill-over is to make room for it
    total_h = CARD_H + TREE_Y_SHIFT

    svg = f'''<svg width="{CARD_W}" height="{total_h}" viewBox="0 0 {CARD_W} {total_h}"
  xmlns="http://www.w3.org/2000/svg">
{font_face_style()}
<rect width="{CARD_W}" height="{CARD_H}" rx="10" fill="{PAPER}" stroke="{GRID_LINE}" stroke-width="1"/>
<text x="{PAD_X}" y="32" class="pixel" font-size="16" letter-spacing="2" fill="{INK}">CONTRIBUTIONS</text>
{tree_img}
{"".join(month_labels)}
{"".join(rects)}
<text x="{PAD_X}" y="{CARD_H - 15}" font-family="monospace" font-size="11" fill="{TEXT_MID}">{streak}-day streak</text>
{"".join(legend)}
</svg>'''
    return svg


if __name__ == "__main__":
    print("Fetching contributions...")
    weeks = fetch_contributions()
    levels = weeks_to_levels(weeks)
    months = week_months(weeks)
    streak = current_streak(weeks)
    print(f"Streak: {streak} days")

    svg_content = render_mosaic_svg(levels, months, streak)
    with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Saved -> {OUTPUT_SVG} ({len(svg_content)//1024} KB)")
