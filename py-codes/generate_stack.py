#!/usr/bin/env python3
"""
generate_stack.py
-------------------
One-off (not scheduled): renders the tech-stack card as an SVG, matching
the wordmark/mosaic pixel-paper theme.

Each technology's pixel-art logo lives in logos/ and is embedded as a
base64 data URI -- an SVG shown through a README <img> tag cannot fetch
external files, so inlining is what makes the logos appear on GitHub.

Re-run manually if the stack changes.
"""

import base64
import os

from pixel_font import font_face_style

OUTPUT_SVG = "stack.svg"
LOGO_DIR = "logos"

PAPER     = "#f7f4ea"
GRID_LINE = "#e6e0cf"
INK       = "#2b2617"
TEXT_MID  = "#7c7460"

# (logo filename stem, display name)
CATEGORIES = [
    ("FRONTEND",  [("react", "React"), ("html", "HTML"), ("css", "CSS"), ("js", "JavaScript")]),
    ("BACKEND",   [("django", "Django")]),
    ("DATABASE",  [("postgresql", "PostgreSQL")]),
    ("LANGUAGES", [("c", "C"), ("cpp", "C++"), ("java", "Java"), ("python", "Python")]),
    ("HARDWARE",  [("esp32", "ESP32"), ("arduino", "Arduino")]),
]

W = 797
PAD_TOP, PAD_BOTTOM = 38, 30
LABEL_X = 36
LOGOS_X = 178          # where the logo columns start
LOGO = 72
CELL = 142             # horizontal pitch between logos
NAME_GAP = 15          # logo bottom -> name baseline
ROW_GAP = 24


def data_uri(stem):
    path = os.path.join(LOGO_DIR, f"{stem}.avif")
    with open(path, "rb") as f:
        return "data:image/avif;base64," + base64.b64encode(f.read()).decode("ascii")


def render():
    parts = []
    y = PAD_TOP

    for label, items in CATEGORIES:
        parts.append(
            f'<text x="{LABEL_X}" y="{y + LOGO / 2 + 5:.0f}" class="pixel" font-size="13" '
            f'letter-spacing="1.5" fill="{INK}">{label}</text>'
        )

        for i, (stem, name) in enumerate(items):
            x = LOGOS_X + i * CELL
            parts.append(
                f'<image href="{data_uri(stem)}" x="{x}" y="{y}" '
                f'width="{LOGO}" height="{LOGO}" image-rendering="pixelated"/>'
            )
            parts.append(
                f'<text x="{x + LOGO / 2:.0f}" y="{y + LOGO + NAME_GAP}" text-anchor="middle" '
                f'font-family="monospace" font-size="11" fill="{TEXT_MID}">{name}</text>'
            )

        y += LOGO + NAME_GAP + ROW_GAP

    card_h = y - ROW_GAP + PAD_BOTTOM

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{card_h}" viewBox="0 0 {W} {card_h}">
{font_face_style()}
<rect width="{W}" height="{card_h}" rx="10" fill="{PAPER}" stroke="{GRID_LINE}" stroke-width="1"/>
{"".join(parts)}
</svg>'''


svg = render()
with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"Saved -> {OUTPUT_SVG} ({len(svg) // 1024} KB)")
