#!/usr/bin/env python3
"""
generate_projects.py
--------------------
Renders the projects card as an SVG in the pixel-paper theme, and rewrites
the PROJECTS block in README.md.

Folders are declared in shelf/shelf.config.json and filled automatically
from GitHub repo topics, so adding a project to a folder means adding a
topic -- not editing this file.

The chest and folder icons are drawn from pixel maps in code, the way
generate_stats.py draws its icons: nothing is downloaded, and no texture
from the game is redistributed.

Env var: GH_TOKEN (optional locally; raises the rate limit and reveals
private repos when the token owns them).

Re-run manually, or let .github/workflows/shelf.yml do it.
"""

import base64
import json
import os
import re
import urllib.request
from pathlib import Path

from pixel_font import font_face_style

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "shelf" / "shelf.config.json"
OUTPUT_SVG = ROOT / "projects.svg"
README = ROOT / "README.md"

START = "<!-- shelf:start -->"
END = "<!-- shelf:end -->"

PAPER     = "#f7f4ea"
GRID_LINE = "#e6e0cf"
INK       = "#2b2617"
TEXT_MID  = "#7c7460"
CARD_BG   = "#fffdf6"
ICON_COLOR = "#334155"
MC_GREEN  = "#3F7A20"

W = 797
PAD_X = 36
HEADING_H = 58
PAD_TOP = 38 + HEADING_H
PAD_BOTTOM = 28

CARD_H = 44
CARD_GAP = 7
ROW_INDENT = 16
SECTION_GAP = 16
FOLDER_ROW_H = 30

# ---------------------------------------------------------------- pixel art ---

# A chest, 16x16. '.' is transparent; the rest index into PALETTE below.
def data_uri(stem):
    """An SVG shown through a README <img> cannot fetch files, so inline it."""
    path = ROOT / "logos" / f"{stem}.avif"
    return "data:image/avif;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def icon_folder(x, y):
    """The same minimal folder outline generate_stats.py uses for repo counts."""
    return (
        f'<path d="M{x+2:.1f} {y+3.5:.1f} h3.5 l2 2 h6 c0.8 0 1.5 0.7 1.5 1.5 v6.5 '
        f'c0 0.8 -0.7 1.5 -1.5 1.5 h-11.5 c-0.8 0 -1.5 -0.7 -1.5 -1.5 v-8.5 '
        f'c0 -0.8 0.7 -1.5 1.5 -1.5 z" fill="none" stroke="{ICON_COLOR}" '
        f'stroke-width="1.5" stroke-linejoin="round"/>'
    )


# ------------------------------------------------------------------- github ---

def fetch_repos(owner):
    repos, page = [], 1
    while page <= 10:
        url = (
            f"https://api.github.com/users/{owner}/repos"
            f"?per_page=100&page={page}&sort=updated"
        )
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            batch = json.load(resp)
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


# -------------------------------------------------------------------- layout ---

def esc(s):
    return (
        str(s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def clip(s, n):
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def month_year(iso):
    if not iso:
        return ""
    y, m = iso[:4], iso[5:7]
    names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{names[int(m)]} {y}"


def gather(config, repos):
    """Resolve folders and loose entries into (label, [repo]) sections."""
    by_name = {r["name"].lower(): r for r in repos}
    claimed, missing = set(), []

    def take_named(names):
        out = []
        for n in names or []:
            r = by_name.get(n.lower())
            if not r:
                missing.append(n)
            elif r["name"] not in claimed:
                claimed.add(r["name"])
                out.append(r)
        return out

    def take_tagged(tags):
        tags = {t.lower() for t in tags or []}
        if not tags:
            return []
        hit = [
            r for r in repos
            if r["name"] not in claimed and tags & {t.lower() for t in r.get("topics") or []}
        ]
        hit.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
        for r in hit:
            claimed.add(r["name"])
        return hit

    folders = []
    for f in config.get("folders", []):
        items = take_named(f.get("repos")) + take_tagged(f.get("tags"))
        folders.append({"name": f["name"], "blurb": f.get("blurb"), "repos": items})

    loose = take_named(config.get("loose")) + take_tagged(config.get("looseTags"))
    return folders, loose, missing


def repo_card(repo, x, y, w):
    name = esc(repo["name"])
    desc = clip(repo.get("description") or "", 74)

    meta = []
    if repo.get("language"):
        meta.append(repo["language"])
    if repo.get("stargazers_count"):
        meta.append(f"★ {repo['stargazers_count']}")
    when = month_year(repo.get("pushed_at"))
    if when:
        meta.append(when)
    meta_s = esc("  ·  ".join(meta))

    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{CARD_H}" rx="6" '
        f'fill="{CARD_BG}" stroke="{GRID_LINE}" stroke-width="1"/>',
        f'<rect x="{x}" y="{y}" width="3" height="{CARD_H}" rx="1.5" fill="{MC_GREEN}"/>',
        f'<text x="{x + 14}" y="{y + 19}" font-family="monospace" font-size="12.5" '
        f'font-weight="bold" fill="{INK}">{name}</text>',
        f'<text x="{x + w - 14}" y="{y + 19}" text-anchor="end" font-family="monospace" '
        f'font-size="10" fill="{TEXT_MID}">{meta_s}</text>',
    ]
    if desc:
        parts.append(
            f'<text x="{x + 14}" y="{y + 34}" font-family="monospace" font-size="10" '
            f'fill="{TEXT_MID}">{esc(desc)}</text>'
        )
    return "".join(parts)


def render_svg(config, folders, loose, missing):
    parts = []
    card_w = W - 2 * PAD_X - ROW_INDENT

    # Heading: chest + PROJECTS, mirroring the pickaxe + TECH STACK heading.
    parts.append(
        f'<image href="{data_uri("chest")}" x="{PAD_X}" y="13" width="66" height="44" '
        f'image-rendering="pixelated"/>'
    )
    parts.append(
        f'<text x="{PAD_X + 66 + 16}" y="{16 + 20 + 8}" class="pixel" font-size="22" '
        f'letter-spacing="2" fill="{INK}">PROJECTS</text>'
    )
    total = sum(len(f["repos"]) for f in folders) + len(loose)
    parts.append(
        f'<text x="{W - PAD_X}" y="{16 + 20 + 8}" text-anchor="end" font-family="monospace" '
        f'font-size="11" fill="{TEXT_MID}">{total} repositories</text>'
    )

    y = PAD_TOP

    def section(label, blurb, items, with_icon):
        nonlocal y
        if with_icon:
            parts.append(icon_folder(PAD_X, y - 1))
            tx = PAD_X + 26
        else:
            tx = PAD_X
        parts.append(
            f'<text x="{tx}" y="{y + 12}" class="pixel" font-size="13" '
            f'letter-spacing="1.5" fill="{INK}">{esc(label.upper())}</text>'
        )
        if items:
            n = f"{len(items)} repo" + ("" if len(items) == 1 else "s")
            parts.append(
                f'<text x="{W - PAD_X}" y="{y + 12}" text-anchor="end" '
                f'font-family="monospace" font-size="10" fill="{TEXT_MID}">{n}</text>'
            )
        y += FOLDER_ROW_H

        if not items:
            parts.append(
                f'<text x="{PAD_X + ROW_INDENT}" y="{y + 6}" font-family="monospace" '
                f'font-size="10" font-style="italic" fill="{TEXT_MID}">'
                f'{esc(blurb or "Nothing here yet.")}</text>'
            )
            y += 20 + SECTION_GAP
            return

        for r in items:
            parts.append(repo_card(r, PAD_X + ROW_INDENT, y, card_w))
            y += CARD_H + CARD_GAP
        y += SECTION_GAP - CARD_GAP

    for f in folders:
        section(f["name"], f.get("blurb"), f["repos"], with_icon=True)
    if loose:
        section("Other projects", None, loose, with_icon=False)

    if missing:
        parts.append(
            f'<text x="{PAD_X}" y="{y + 8}" font-family="monospace" font-size="9.5" '
            f'fill="{TEXT_MID}">! in shelf.config.json but not on the account: '
            f'{esc(", ".join(missing))}</text>'
        )
        y += 18

    h = y - SECTION_GAP + PAD_BOTTOM
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
        f'viewBox="0 0 {W} {h}">\n{font_face_style()}\n'
        f'<rect width="{W}" height="{h}" rx="10" fill="{PAPER}" '
        f'stroke="{GRID_LINE}" stroke-width="1"/>\n'
        f'{"".join(parts)}\n</svg>'
    )


# -------------------------------------------------------------------- readme ---

def render_block(folders, loose):
    """The README block: the card, plus collapsed links (an <img> isn't clickable)."""
    lines = [
        START,
        "",
        '<!-- PROJECTS - AUTO GENERATED BY GITHUB ACTIONS -->',
        '<img src="./projects.svg" width="797" alt="Projects — grouped by event, generated from repo topics"/>',
        "",
        "<details>",
        "<summary><sub>&nbsp;open a project&nbsp;</sub></summary>",
        "",
    ]
    for f in folders:
        if not f["repos"]:
            continue
        lines.append(f'<sub><b>{f["name"]}</b></sub>')
        lines.append("")
        for r in f["repos"]:
            lines.append(f'<sub>· <a href="{r["html_url"]}">{r["name"]}</a></sub><br/>')
        lines.append("")
    if loose:
        lines.append("<sub><b>Other projects</b></sub>")
        lines.append("")
        for r in loose:
            lines.append(f'<sub>· <a href="{r["html_url"]}">{r["name"]}</a></sub><br/>')
        lines.append("")
    lines += ["</details>", "", END]
    return "\n".join(lines)


def splice(text, block):
    a, b = text.find(START), text.find(END)
    if a != -1 and b != -1 and b > a:
        return text[:a] + block + text[b + len(END):]
    # No markers yet: drop the block just above the tech stack, which is where
    # it belongs, rather than appending it after the socials.
    anchor = "<!-- TECH STACK -->"
    if anchor in text:
        return text.replace(anchor, block + "\n\n" + anchor, 1)
    return text.rstrip() + "\n\n" + block + "\n"


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    repos = fetch_repos(config["owner"])
    folders, loose, missing = gather(config, repos)

    svg = render_svg(config, folders, loose, missing)
    OUTPUT_SVG.write_text(svg, encoding="utf-8")

    readme = README.read_text(encoding="utf-8")
    README.write_text(splice(readme, render_block(folders, loose)), encoding="utf-8")

    filed = sum(len(f["repos"]) for f in folders) + len(loose)
    print(f"projects: {len(repos)} repos on the account, {filed} shown")
    if missing:
        print(f"projects: not found -> {', '.join(missing)}")
    print(f"Saved -> {OUTPUT_SVG.name} ({len(svg) // 1024} KB)")
    print(f"Updated -> {README.name}")


if __name__ == "__main__":
    main()
