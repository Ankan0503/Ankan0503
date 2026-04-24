#!/usr/bin/env python3
"""
generate_garden.py
------------------
Fetches GitHub contribution data for Ankan0503 and generates:
  - sunflower-garden.svg  (animated sunflower garden + flying bees)

Run by GitHub Actions daily. Commit the output SVG to the repo root.
Requires env var: GH_TOKEN (a GitHub personal access token with read:user scope)
"""

import os
import json
import math
import random
import requests
from datetime import datetime, timedelta

# ── Config ────────────────────────────────────────────────────────────────────
USERNAME   = "Ankan0503"
GH_TOKEN   = os.environ.get("GH_TOKEN", "")
OUTPUT_SVG = "sunflower-garden.svg"

# ── Colours (blues/purples theme) ─────────────────────────────────────────────
BG         = "#0d1117"
SKY_TOP    = "#0d1117"
SKY_BOT    = "#1a1a2e"
SOIL       = "#2d1b00"
SOIL_LIGHT = "#3d2800"
STEM       = "#22543d"
LEAF       = "#276749"
PETAL_0    = "#2d3748"   # no commit  → dark grey
PETAL_1    = "#553c9a"   # 1-2        → soft purple
PETAL_2    = "#6b46c1"   # 3-5        → medium purple
PETAL_3    = "#d97706"   # 6-9        → golden
PETAL_4    = "#f59e0b"   # 10+        → bright gold/yellow
CENTRE_0   = "#1a202c"
CENTRE_1   = "#4a1d96"
CENTRE_2   = "#5b21b6"
CENTRE_3   = "#92400e"
CENTRE_4   = "#b45309"
TEXT_COL   = "#a78bfa"
SUN_COL    = "#fbbf24"

# Garden layout
COLS       = 52          # weeks
ROWS       = 7           # days per week
CELL       = 14          # px per cell
GAP        = 2
FLOWER_R   = 5           # base petal radius
PADDING_X  = 60
PADDING_Y  = 60
WIDTH      = COLS * (CELL + GAP) + PADDING_X * 2 + 40
HEIGHT     = ROWS * (CELL + GAP) + PADDING_Y * 2 + 120

# ── GitHub GraphQL query ───────────────────────────────────────────────────────
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
        # Return dummy data if no token (for testing)
        print("Warning: No GH_TOKEN found. Using random demo data.")
        weeks = []
        base = datetime.now() - timedelta(weeks=52)
        for w in range(52):
            days = []
            for d in range(7):
                dt = base + timedelta(weeks=w, days=d)
                days.append({"date": dt.strftime("%Y-%m-%d"),
                              "contributionCount": random.choices(
                                  [0,1,2,4,7,12],
                                  weights=[30,20,20,15,10,5])[0]})
            weeks.append({"contributionDays": days})
        return weeks

    headers = {"Authorization": f"bearer {GH_TOKEN}"}
    resp = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"login": USERNAME}},
        headers=headers,
        timeout=30
    )
    resp.raise_for_status()
    data = resp.json()
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

def commit_level(count):
    if count == 0: return 0
    if count <= 2:  return 1
    if count <= 5:  return 2
    if count <= 9:  return 3
    return 4

def petal_colour(level):
    return [PETAL_0, PETAL_1, PETAL_2, PETAL_3, PETAL_4][level]

def centre_colour(level):
    return [CENTRE_0, CENTRE_1, CENTRE_2, CENTRE_3, CENTRE_4][level]

def flower_size(level):
    return [0.4, 0.6, 0.8, 1.0, 1.3][level]

def draw_sun(svg):
    cx, cy, r = 40, 40, 18
    rays = ""
    for i in range(12):
        angle = math.radians(i * 30)
        x1 = cx + math.cos(angle) * (r + 4)
        y1 = cy + math.sin(angle) * (r + 4)
        x2 = cx + math.cos(angle) * (r + 11)
        y2 = cy + math.sin(angle) * (r + 11)
        rays += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{SUN_COL}" stroke-width="2" stroke-linecap="round" opacity="0.7"/>'
    svg.append(rays)
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{SUN_COL}" opacity="0.85">'
               f'<animate attributeName="opacity" values="0.85;1;0.85" dur="3s" repeatCount="indefinite"/>'
               f'</circle>')

def draw_flower(svg, cx, cy, level):
    scale = flower_size(level)
    pr = FLOWER_R * scale          # petal radius
    cr = FLOWER_R * scale * 0.55   # centre radius
    pc = petal_colour(level)
    cc = centre_colour(level)

    if level == 0:
        # bare soil dot
        svg.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2.5" fill="{SOIL_LIGHT}" opacity="0.5"/>')
        return

    # Stem (tiny)
    stem_h = 4 * scale
    svg.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx:.1f}" y2="{cy+stem_h:.1f}" '
               f'stroke="{STEM}" stroke-width="1" stroke-linecap="round"/>')

    # Petals (8 petals)
    petals = ""
    n_petals = 8 if level >= 3 else 6
    for i in range(n_petals):
        angle = math.radians(i * (360 / n_petals))
        px = cx + math.cos(angle) * pr * 1.5
        py = cy + math.sin(angle) * pr * 1.5
        petals += (f'<ellipse cx="{px:.1f}" cy="{py:.1f}" rx="{pr:.1f}" ry="{pr*0.55:.1f}" '
                   f'fill="{pc}" opacity="0.9" '
                   f'transform="rotate({math.degrees(angle):.1f},{px:.1f},{py:.1f})"/>')
    svg.append(petals)

    # Centre
    glow = ""
    if level == 4:
        glow = f'<animate attributeName="r" values="{cr:.1f};{cr*1.15:.1f};{cr:.1f}" dur="2s" repeatCount="indefinite"/>'
    svg.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{cr:.1f}" fill="{cc}">{glow}</circle>')

def draw_bee(svg, bee_id, cx, cy, delay=0):
    """Draw an animated bee that flies to position cx,cy and lands."""
    start_x = random.choice([-60, WIDTH + 60])
    start_y = random.uniform(PADDING_Y, PADDING_Y + ROWS * (CELL + GAP))
    dur = random.uniform(4, 8)

    # Bee body
    bid = f"bee{bee_id}"
    svg.append(f'''
  <g id="{bid}" opacity="0">
    <!-- Body -->
    <ellipse cx="0" cy="0" rx="4" ry="2.5" fill="#f59e0b"/>
    <ellipse cx="0" cy="0" rx="4" ry="2.5" fill="none" stroke="#1a1a2e" stroke-width="0.6"
             stroke-dasharray="1.5 1.5"/>
    <!-- Head -->
    <circle cx="4.5" cy="0" r="2" fill="#d97706"/>
    <!-- Eyes -->
    <circle cx="5.5" cy="-0.7" r="0.5" fill="#1a1a2e"/>
    <!-- Wings -->
    <ellipse cx="-1" cy="-3" rx="3.5" ry="1.8" fill="white" opacity="0.6">
      <animateTransform attributeName="transform" type="rotate"
        values="0,-1,-3;15,-1,-3;0,-1,-3;-15,-1,-3;0,-1,-3"
        dur="0.12s" repeatCount="indefinite"/>
    </ellipse>
    <ellipse cx="1" cy="-3" rx="3.5" ry="1.8" fill="white" opacity="0.6">
      <animateTransform attributeName="transform" type="rotate"
        values="0,1,-3;-15,1,-3;0,1,-3;15,1,-3;0,1,-3"
        dur="0.12s" repeatCount="indefinite"/>
    </ellipse>

    <!-- Fly-in animation -->
    <animateMotion
      path="M {start_x - cx:.0f},{start_y - cy:.0f} C {(start_x-cx)//2:.0f},{(start_y-cy)//2:.0f} 0,-20 0,0"
      dur="{dur:.1f}s" begin="{delay:.1f}s" fill="freeze"/>
    <animate attributeName="opacity" values="0;1;1" keyTimes="0;0.05;1"
      dur="{dur:.1f}s" begin="{delay:.1f}s" fill="freeze"/>
  </g>
  <animateTransform xlink:href="#{bid}" attributeName="transform" type="translate"
    values="{cx:.0f},{cy:.0f}" dur="{dur:.1f}s" begin="{delay:.1f}s" fill="freeze"
    additive="sum"/>
''')

def generate_svg(weeks):
    svg = []
    svg.append(f'''<svg width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}"
  xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">

<defs>
  <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{SKY_TOP}"/>
    <stop offset="100%" stop-color="{SKY_BOT}"/>
  </linearGradient>
  <linearGradient id="soilGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{SOIL_LIGHT}"/>
    <stop offset="100%" stop-color="{SOIL}"/>
  </linearGradient>
  <filter id="glow">
    <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
    <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>

<!-- Background -->
<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#skyGrad)" rx="12"/>

<!-- Soil strip -->
<rect x="0" y="{HEIGHT-55}" width="{WIDTH}" height="55"
  fill="url(#soilGrad)" rx="0 0 12 12"/>

<!-- Stars -->''')

    # Stars
    random.seed(42)
    for _ in range(60):
        sx = random.uniform(0, WIDTH)
        sy = random.uniform(0, PADDING_Y + 20)
        sr = random.uniform(0.5, 1.5)
        sd = random.uniform(1.5, 4)
        svg.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{sr:.1f}" fill="white" opacity="0.4">'
                   f'<animate attributeName="opacity" values="0.4;0.9;0.4" dur="{sd:.1f}s" repeatCount="indefinite"/>'
                   f'</circle>')

    draw_sun(svg)

    # Title
    svg.append(f'''
<text x="{WIDTH//2}" y="30" text-anchor="middle" font-family="monospace"
  font-size="14" fill="{TEXT_COL}" font-weight="bold" opacity="0.9">
  🌻 Ankan0503's Contribution Garden 🐝
</text>''')

    # Month labels
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    prev_month = None
    for wi, week in enumerate(weeks):
        if week["contributionDays"]:
            d = week["contributionDays"][0]["date"]
            m = int(d.split("-")[1]) - 1
            if m != prev_month:
                lx = PADDING_X + wi * (CELL + GAP)
                svg.append(f'<text x="{lx}" y="{PADDING_Y - 8}" font-family="monospace" '
                           f'font-size="9" fill="{TEXT_COL}" opacity="0.6">{month_names[m]}</text>')
                prev_month = m

    # Day labels
    days = ["Mon","","Wed","","Fri","","Sun"]
    for di, dl in enumerate(days):
        if dl:
            ly = PADDING_Y + di * (CELL + GAP) + CELL
            svg.append(f'<text x="{PADDING_X - 6}" y="{ly:.1f}" font-family="monospace" '
                       f'font-size="8" fill="{TEXT_COL}" opacity="0.5" text-anchor="end">{dl}</text>')

    # Flowers + collect bee targets
    bee_targets = []   # (cx, cy, count) for days with commits
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            count = day["contributionCount"]
            level = commit_level(count)
            cx = PADDING_X + wi * (CELL + GAP) + CELL // 2
            cy = PADDING_Y + di * (CELL + GAP) + CELL // 2
            draw_flower(svg, cx, cy, level)
            if count > 0:
                bee_targets.append((cx, cy, count))

    # Bees — pick top committed days (max 15 bees to keep SVG manageable)
    bee_targets.sort(key=lambda x: -x[2])
    bee_spots = bee_targets[:15]
    bee_id = 0
    for (bx, by, bcount) in bee_spots:
        n_bees = 1 if bcount <= 3 else 2 if bcount <= 8 else 3
        for b in range(n_bees):
            offset_x = random.uniform(-4, 4)
            offset_y = random.uniform(-4, 4)
            delay = bee_id * 0.6 + random.uniform(0, 1)
            draw_bee(svg, bee_id, bx + offset_x, by + offset_y - 6, delay=delay)
            bee_id += 1

    # Legend
    legend_items = [
        (PETAL_0, "0 commits"),
        (PETAL_1, "1–2"),
        (PETAL_2, "3–5"),
        (PETAL_3, "6–9"),
        (PETAL_4, "10+"),
    ]
    lx_start = PADDING_X
    ly = HEIGHT - 22
    svg.append(f'<text x="{lx_start}" y="{ly}" font-family="monospace" font-size="9" '
               f'fill="{TEXT_COL}" opacity="0.6">Less</text>')
    for i, (col, label) in enumerate(legend_items):
        lx = lx_start + 38 + i * 16
        svg.append(f'<circle cx="{lx}" cy="{ly-4}" r="5" fill="{col}" opacity="0.9"/>')
    svg.append(f'<text x="{lx_start + 38 + 5*16 + 6}" y="{ly}" font-family="monospace" '
               f'font-size="9" fill="{TEXT_COL}" opacity="0.6">More</text>')

    svg.append("</svg>")
    return "\n".join(svg)

if __name__ == "__main__":
    print("🌻 Fetching contributions...")
    weeks = fetch_contributions()
    print(f"   Got {len(weeks)} weeks of data.")
    print("🎨 Generating SVG...")
    svg_content = generate_svg(weeks)
    with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"✅ Saved → {OUTPUT_SVG}")
    print(f"   SVG size: {len(svg_content)//1024} KB")
