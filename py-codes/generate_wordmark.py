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
LABEL     = "PLAYER PROFILE"

W = 797  # matches generate_mosaic.py's CARD_W so the cards line up

# Everything below (name, creeper, role) keeps the exact relative spacing
# it always had -- OFFSET just slides that whole block down to make room
# for the label above it, rather than changing any of their own numbers.
LABEL_W, LABEL_H = 230, 48
LABEL_TOP = 14
LABEL_X = 150           # align to left margin (36px, matching other cards)
LABEL_NAME_GAP = 20    # label bottom -> name's cap-top, per the 15-25px spec
LABEL_NOTCH = 5        # corner cut, keeps it pixel-art rather than rounded-rect
TAIL_DEPTH = 9

NAME_SIZE = 46
NAME_TRACK = 3           # letter-spacing
_NAME_BASELINE0 = 92     # original (pre-label) values, used only to derive OFFSET
_CAP_TOP0 = _NAME_BASELINE0 - NAME_SIZE * 0.62
OFFSET = round(LABEL_TOP + LABEL_H + LABEL_NAME_GAP - _CAP_TOP0)

NAME_BASELINE = _NAME_BASELINE0 + OFFSET
CREEPER_SIZE = 54
CREEPER_GAP = 20
ROLE_BASELINE = 128 + OFFSET

# --- terminal panel -----------------------------------------------------
# Plain monospace, not the pixel font -- this is supporting detail text,
# same hierarchy the role line already uses (pixel font is for headline
# moments only: the label, the name, category headings elsewhere).
TERM_BG     = "#1c1712"
TERM_INNER  = "#3a3128"
TERM_PROMPT = "#7CC443"
TERM_CMD    = "#F0EAD9"
TERM_OUT    = "#A89F8C"
# grey bezel around the dark body -- a Minecraft GUI panel is never one flat
# plane, it's a light top/left edge and a dark bottom/right edge simulating
# a fixed light source, drawn as flat bands rather than a gradient
FRAME_PAD   = 5
FRAME_BASE  = "#847E70"
FRAME_LIGHT = "#B4AD9C"
FRAME_DARK  = "#4A453C"

TERMINAL = [
    ("whoami",     "ankan_giri"),
    ("location",   "Kolkata, India"),
    ("education",  "HITK • CSE"),
    ("skills",     "Django • Java • C"),
    ("achievement", "3× Hackathon Finalist • 1× Winner"),
    ("interests",  "Backend Development • Hardware • IoT"),
]

TERM_W = 460
TERM_PAD_X, TERM_PAD_Y = 22, 18
TERM_NOTCH = 5
CMD_SIZE, OUT_SIZE = 12.5, 12
LINE_H = 17
BLOCK_GAP = 11
TERM_TOP_GAP = 26   # role baseline -> top of terminal

TERM_TOP = ROLE_BASELINE + TERM_TOP_GAP
TERM_H = TERM_PAD_Y * 2 + len(TERMINAL) * (LINE_H * 2) + (len(TERMINAL) - 1) * BLOCK_GAP
TERM_X = (W - TERM_W) / 2

H = TERM_TOP + TERM_H + FRAME_PAD + 26


def data_uri(path, mime):
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode("ascii")


def label_path():
    x, y, w, h, n = LABEL_X, LABEL_TOP, LABEL_W, LABEL_H, LABEL_NOTCH
    tail_l, tail_r, tail_tip = x + 34, x + 58, x + 40
    return (
        f"M{x+n},{y} L{x+w-n},{y} L{x+w},{y+n} L{x+w},{y+h-n} L{x+w-n},{y+h} "
        f"L{tail_r},{y+h} L{tail_tip},{y+h+TAIL_DEPTH} L{tail_l},{y+h} "
        f"L{x+n},{y+h} L{x},{y+h-n} L{x},{y+n} Z"
    )


def notched_rect(x, y, w, h, n):
    return (
        f"M{x+n},{y} L{x+w-n},{y} L{x+w},{y+n} L{x+w},{y+h-n} L{x+w-n},{y+h} "
        f"L{x+n},{y+h} L{x},{y+h-n} L{x},{y+n} Z"
    )


def terminal_svg():
    fx, fy = TERM_X - FRAME_PAD, TERM_TOP - FRAME_PAD
    fw, fh = TERM_W + FRAME_PAD * 2, TERM_H + FRAME_PAD * 2
    fn = TERM_NOTCH + 2

    parts = [
        # grey bezel: base fill, then a light strip along the top+left edge
        # and a dark strip along the bottom+right edge, so it reads as a
        # raised frame rather than a flat grey outline
        f'<path d="{notched_rect(fx, fy, fw, fh, fn)}" fill="{FRAME_BASE}" stroke="{INK}" stroke-width="2"/>',
        f'<path d="M{fx+fn},{fy+2} L{fx+fw-fn},{fy+2} M{fx+2},{fy+fn} L{fx+2},{fy+fh-fn}" '
        f'stroke="{FRAME_LIGHT}" stroke-width="2.5" stroke-linecap="square"/>',
        f'<path d="M{fx+fn},{fy+fh-2} L{fx+fw-fn},{fy+fh-2} M{fx+fw-2},{fy+fn} L{fx+fw-2},{fy+fh-fn}" '
        f'stroke="{FRAME_DARK}" stroke-width="2.5" stroke-linecap="square"/>',
        # dark terminal body, unchanged size/position, sits inside the bezel
        f'<path d="{notched_rect(TERM_X, TERM_TOP, TERM_W, TERM_H, TERM_NOTCH)}" '
        f'fill="{TERM_BG}" stroke="{INK}" stroke-width="2"/>',
        # inner highlight, inset by 3px, same stepped shape -- reads as a
        # bevel without any gradient or glow
        f'<path d="{notched_rect(TERM_X+3, TERM_TOP+3, TERM_W-6, TERM_H-6, TERM_NOTCH-2)}" '
        f'fill="none" stroke="{TERM_INNER}" stroke-width="1"/>',
    ]

    ty = TERM_TOP + TERM_PAD_Y + CMD_SIZE
    tx = TERM_X + TERM_PAD_X
    for cmd, out in TERMINAL:
        parts.append(
            f'<text x="{tx:.0f}" y="{ty:.0f}" font-family="monospace" font-size="{CMD_SIZE}">'
            f'<tspan fill="{TERM_PROMPT}" font-weight="bold">$ </tspan>'
            f'<tspan fill="{TERM_CMD}" font-weight="bold">{cmd}</tspan></text>'
        )
        ty += LINE_H
        parts.append(
            f'<text x="{tx:.0f}" y="{ty:.0f}" font-family="monospace" '
            f'font-size="{OUT_SIZE}" fill="{TERM_OUT}">{out}</text>'
        )
        ty += LINE_H + BLOCK_GAP

    return "".join(parts)


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
<path d="{label_path()}" fill="#fffdf5" stroke="{INK}" stroke-width="1.5" stroke-linejoin="round"/>
<text x="{LABEL_X + LABEL_W / 2:.0f}" y="{LABEL_TOP + LABEL_H / 2 + 5:.0f}" text-anchor="middle" class="pixel" font-size="15" letter-spacing="1.5" fill="{MC_GREEN}">{LABEL}</text>
<text x="{start_x:.0f}" y="{NAME_BASELINE}" class="pixel" font-size="{NAME_SIZE}" letter-spacing="{NAME_TRACK}" fill="{INK}">{NAME}</text>
<image href="{data_uri(CREEPER, "image/avif")}" x="{creeper_x:.0f}" y="{creeper_y:.0f}" width="{CREEPER_SIZE}" height="{CREEPER_SIZE}" image-rendering="pixelated"/>
<text x="{start_x + group_w / 2:.0f}" y="{ROLE_BASELINE}" text-anchor="middle" font-family="monospace" font-size="13" letter-spacing="1"><tspan fill="{MC_GREEN}" stroke-width="0.6" font-weight="bold">{ROLE}</tspan><tspan fill="{TEXT_MID}">  ·  {ADD_ROLE}</tspan></text>
{terminal_svg()}
</svg>'''

with open(OUTPUT_SVG, "w", encoding="utf-8") as f:
    f.write(svg)

print(f"name width={name_w:.1f}  group={group_w:.1f}  start_x={start_x:.1f}")
print(f"Saved -> {OUTPUT_SVG} ({len(svg) // 1024} KB)")
