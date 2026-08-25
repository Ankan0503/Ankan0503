#!/usr/bin/env python3
"""
generate_socials.py
---------------------
One-off (not scheduled): draws four independent rounded icon tiles into
socials/ -- one per network, each with its name captioned underneath.

They are separate files, not one card, because an SVG shown through a
README <img> tag cannot carry working links; each tile gets its own <a>
in the README. Separate <img> tags in a row can reflow unevenly on a
narrow screen (three wrap to one line, one to the next) -- README.md
wraps this row in an HTML <table> instead, which GitHub scrolls
horizontally rather than reflowing, so the row never breaks unevenly.

Every glyph is a 16x16 pixel map: a square brand plate with the mark
knocked out in white, sitting on the same cream tile as the other cards
(a bare black X plate would vanish on GitHub's dark theme).

Re-run manually if an icon changes.
"""

import os

OUT_DIR = "socials"

PAPER     = "#f7f4ea"
GRID_LINE = "#e6e0cf"
TEXT_MID  = "#7c7460"

TILE_W, TILE_H = 72, 58
SCALE = 2                 # 16 * 2 = 32px glyph
GLYPH = 16 * SCALE
GLYPH_Y = 8
NAME_BASELINE = 50
R = 10

BLANK = "................"
PLATE = ".{0}{0}{0}{0}{0}{0}{0}{0}{0}{0}{0}{0}{0}{0}."

# X.com -- white mark on black. Both strokes are 2px and mirror each other,
# so the cross reads evenly at 16px.
X_ICON = [
    BLANK,
    PLATE.format("K"),
    PLATE.format("K"),
    ".KKWWKKKKKKKWWK.",
    ".KKKWWKKKKKWWKK.",
    ".KKKKWWKKKWWKKK.",
    ".KKKKKWWKWWKKKK.",
    ".KKKKKKWWWKKKKK.",
    ".KKKKKKWWWKKKKK.",
    ".KKKKKWWKWWKKKK.",
    ".KKKKWWKKKWWKKK.",
    ".KKKWWKKKKKWWKK.",
    ".KKWWKKKKKKKWWK.",
    PLATE.format("K"),
    PLATE.format("K"),
    BLANK,
]

# LinkedIn -- white "in"
LINKEDIN_ICON = [
    BLANK,
    PLATE.format("B"),
    PLATE.format("B"),
    ".BBWWBBBBBBBBBB.",
    ".BBWWBBBBBBBBBB.",
    PLATE.format("B"),
    ".BBWWBWWWWWWBBB.",
    ".BBWWBWWBBWWBBB.",
    ".BBWWBWWBBWWBBB.",
    ".BBWWBWWBBWWBBB.",
    ".BBWWBWWBBWWBBB.",
    ".BBWWBWWBBWWBBB.",
    ".BBWWBWWBBWWBBB.",
    PLATE.format("B"),
    PLATE.format("B"),
    BLANK,
]

# Facebook -- white "f"
FACEBOOK_ICON = [
    BLANK,
    PLATE.format("B"),
    PLATE.format("B"),
    ".BBBBBBBWWWWBBB.",
    ".BBBBBBWWBBBBBB.",
    ".BBBBBBWWBBBBBB.",
    ".BBBBWWWWWWBBBB.",
    ".BBBBWWWWWWBBBB.",
    ".BBBBBBWWBBBBBB.",
    ".BBBBBBWWBBBBBB.",
    ".BBBBBBWWBBBBBB.",
    ".BBBBBBWWBBBBBB.",
    ".BBBBBBWWBBBBBB.",
    PLATE.format("B"),
    PLATE.format("B"),
    BLANK,
]

# Instagram -- white camera outline, lens and flash on the brand gradient,
# matching the current app icon so it sits in the same system as the rest.
INSTAGRAM_ICON = [
    BLANK,
    PLATE.format("G"),
    PLATE.format("G"),
    PLATE.format("G"),
    ".GGGWWWWWWWWGGG.",
    ".GGGWGGGGWGWGGG.",
    ".GGGWGGWWGGWGGG.",
    ".GGGWGWGGWGWGGG.",
    ".GGGWGWGGWGWGGG.",
    ".GGGWGGWWGGWGGG.",
    ".GGGWGGGGGGWGGG.",
    ".GGGWWWWWWWWGGG.",
    PLATE.format("G"),
    PLATE.format("G"),
    PLATE.format("G"),
    BLANK,
]

# Instagram's gradient runs bottom-left (warm) to top-right (violet).
IG_RAMP = ["#F9A03F", "#F77737", "#F35E4B", "#E1306C", "#C13584", "#833AB4"]

ICONS = {
    "x":         ("X",         X_ICON,         {"K": "#000000", "W": "#FFFFFF"}),
    "instagram": ("Instagram", INSTAGRAM_ICON, None),
    "linkedin":  ("LinkedIn",  LINKEDIN_ICON,  {"B": "#0A66C2", "W": "#FFFFFF"}),
    "facebook":  ("Facebook",  FACEBOOK_ICON,  {"B": "#1877F2", "W": "#FFFFFF"}),
}


def ig_colour(x, y):
    """Step through the ramp along the bottom-left -> top-right diagonal."""
    t = (x + (15 - y)) / 30
    return IG_RAMP[min(int(t * len(IG_RAMP)), len(IG_RAMP) - 1)]


def render(label, pixels, palette):
    gx = (TILE_W - GLYPH) // 2
    rects = []
    for y, row in enumerate(pixels):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            if ch == "W":
                colour = "#FFFFFF"
            elif palette is None:
                colour = ig_colour(x, y)
            else:
                colour = palette[ch]
            rects.append(
                f'<rect x="{gx + x * SCALE}" y="{GLYPH_Y + y * SCALE}" '
                f'width="{SCALE}" height="{SCALE}" fill="{colour}"/>'
            )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{TILE_W}" height="{TILE_H}" '
        f'viewBox="0 0 {TILE_W} {TILE_H}" shape-rendering="crispEdges" role="img" '
        f'aria-label="{label}">'
        f'<rect width="{TILE_W}" height="{TILE_H}" rx="{R}" fill="{PAPER}" '
        f'stroke="{GRID_LINE}" stroke-width="1"/>'
        + "".join(rects)
        + f'<text x="{TILE_W / 2:.0f}" y="{NAME_BASELINE}" text-anchor="middle" '
          f'font-family="monospace" font-size="10" fill="{TEXT_MID}">{label}</text>'
        + "</svg>"
    )


os.makedirs(OUT_DIR, exist_ok=True)
for key, (label, pixels, palette) in ICONS.items():
    assert len(pixels) == 16, f"{key}: {len(pixels)} rows, expected 16"
    for r, row in enumerate(pixels):
        assert len(row) == 16, f"{key} row {r}: {len(row)} wide, expected 16"

    svg = render(label, pixels, palette)
    path = os.path.join(OUT_DIR, f"{key}.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Saved -> {path}  {TILE_W}x{TILE_H}")
