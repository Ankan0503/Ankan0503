#!/usr/bin/env python3
"""
generate_wordmark.py
----------------------
One-off (not scheduled): renders the name/role card as a pixel-font SVG,
with the creeper face set beside the name.

The creeper is embedded as a base64 data URI because an SVG shown through
a README <img> tag cannot fetch external files.

Needs Pillow, only to measure the rendered width of the name so the
name + creeper group stays centred if the name ever changes.

Re-run manually if the name, role, or location change.
"""

import base64
import io
import os

from PIL import ImageFont

from pixel_font import SILKSCREEN_BOLD_B64, font_face_style

OUTPUT_SVG = "wordmark.svg"
CREEPER = os.path.join("logos", "creeper.avif")

PAPER     = "#f7f4ea"
GRID_LINE = "#e6e0cf"
INK       = "#2b2617"
TEXT_MID  = "#7c7460"
# Minecraft grass green. The creeper's own brighter greens (#61AD20, #88C835)
# only reach 2.5:1 and 1.8:1 on this cream card, so they are not legible as
# text; this shade still reads as Minecraft green at 4.75:1.
MC_GREEN  = "#3F7A20"

NAME      = "ANKAN GIRI"
ROLE      = "FULL STACK DEVELOPER"
ADD_ROLE  = "OPEN SOURCE ENTHUSIAST"

W, H = 797, 170  # matches generate_mosaic.py's CARD_W so the cards line up
NAME_SIZE = 46
NAME_TRACK = 3           # letter-spacing
NAME_BASELINE = 92
CREEPER_SIZE = 54
CREEPER_GAP = 20
ROLE_BASELINE = 128


def data_uri(path, mime):
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")


def name_width():
    """Advance width of NAME as the browser will lay it out, tracking included."""
    font = ImageFont.truetype(io.BytesIO(base64.b64decode(SILKSCREEN_BOLD_B64)), NAME_SIZE)
    return font.getlength(NAME) + NAME_TRACK * len(NAME)   # Chrome tracks every glyph


name_w = name_width()
group_w = name_w + CREEPER_GAP + CREEPER_SIZE
start_x = (W - group_w) / 2

# centre the creeper on the name's cap height rather than its baseline.
# 0.62 is Silkscreen's measured cap ratio, taken off a render -- not a guess.
cap_top = NAME_BASELINE - NAME_SIZE * 0.62
creeper_y = (cap_top + NAME_BASELINE) / 2 - CREEPER_SIZE / 2
creeper_x = start_x + name_w + CREEPER_GAP

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
{font_face_style()}
<rect width="{W}" height="{H}" rx="10" fill="{PAPER}" stroke="{GRID_LINE}" stroke-width="1"/>
<text x="{start_x:.0f}" y="{NAME_BASELINE}" class="pixel" font-size="{NAME_SIZE}" letter-spacing="{NAME_TRACK}" fill="{INK}">{NAME}</text>
<image href="{data_uri(CREEPER, "image/avif")}" x="{creeper_x:.0f}" y="{creeper_y:.0f}" width="{CREEPER_SIZE}" height="{CREEPER_SIZE}" image-rendering="pixelated"/>
<text x="{start_x + group_w / 2:.0f}" y="{ROLE_BASELINE}" text-anchor="middle" font-family="monospace" font-size="13" letter-spacing="1"><tspan fill="{MC_GREEN}" stroke-width="0.6" font-weight="bold">{ROLE}</tspan><tspan fill="{TEXT_MID}">  ·  {ADD_ROLE}</tspan></text>
</svg>'''

with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
    f.write(svg)

print(f"name width={name_w:.1f}  group={group_w:.1f}  start_x={start_x:.1f}")
print(f"Saved -> {OUTPUT_SVG} ({len(svg) // 1024} KB)")
