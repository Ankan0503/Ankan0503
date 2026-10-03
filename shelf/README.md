# Shelf

**Folders for your GitHub repositories — visible to everyone, not just you.**

GitHub has no way to group repositories into folders. It is one of the
oldest open feature requests. The usual workarounds each fall short:

| Approach | Problem |
|---|---|
| Browser extension | Only *you* see the folders. Every visitor still sees a flat list. |
| Topics | Public and filterable, but flat — no nesting, no hierarchy. |
| Organizations | Real separation, but changes repo URLs and splits your profile. |
| Pinned repos | Six, no grouping. |

Shelf takes a different route. Markdown `<details>` blocks render as
collapsible sections **for every visitor to your profile**, so the folders live
in your profile README. You declare the tree once; a GitHub Action keeps the
index current.

## What it produces

<details open>
<summary><b>📁 SIH 2026</b> · 1 repo</summary>

- **[ORCA](https://github.com/Ankan0503/ORCA)** — marine safety console  <sub>`Python` · Sept 2026</sub>

</details>

<details>
<summary><b>📁 HackNex</b> · 2 repos</summary>

Nested folders work too — a parent's count covers its whole subtree.

</details>

Real collapsible folders, with per-repo language, stars, and last-push date
pulled live from the API.

## Setup

Shelf runs inside your **profile repository** — the one named after your
account (`Ankan0503/Ankan0503`), which GitHub renders at the top of your
profile.

1. Copy `scripts/build.mjs`, `shelf.config.json` and
   `.github/workflows/shelf.yml` into that repo.
2. Edit `shelf.config.json` — see below.
3. Push. The Action regenerates the index and commits it.

Run it locally any time:

```bash
node scripts/build.mjs --config shelf.config.json --out README.md
```

No dependencies. Node 18+ for built-in `fetch`.

## Configuration

```json
{
  "owner": "Ankan0503",
  "heading": "## Projects",
  "showUnsorted": true,
  "exclude": ["some-scratch-repo"],
  "folders": [
    {
      "name": "SIH 2026",
      "blurb": "Smart India Hackathon.",
      "repos": ["ORCA"],
      "folders": [
        { "name": "Prototypes", "repos": ["older-attempt"] }
      ]
    }
  ]
}
```

| Key | Meaning |
|---|---|
| `owner` | GitHub account to read repos from. Required. |
| `heading` | Markdown heading above the folders. Optional. |
| `showUnsorted` | Add an "Unsorted" folder for anything unfiled. Forks and the profile repo are left out. |
| `exclude` | Repo names to omit from Unsorted entirely. |
| `folders[].name` | Folder label. |
| `folders[].blurb` | One line under the folder heading. Optional. |
| `folders[].repos` | Repo names in this folder. |
| `folders[].folders` | Subfolders, nested as deep as you like. |

The generated block sits between `<!-- shelf:start -->` and
`<!-- shelf:end -->`. Everything outside those markers is left alone, so the
rest of your README is yours.

## Two deliberate choices

**Repos named in the config but missing from the account are reported, not
dropped.** A private, renamed, or moved repo produces a visible warning in the
output. An index that quietly omits things is worse than one that admits a gap.

**Nothing is stored outside GitHub.** No server, no database, no account. The
tree is a JSON file in your repo; the output is your README.

## Limitations

- Private repos only appear when the Action runs under an account that can see
  them. Locally, export a `GITHUB_TOKEN` with `repo` scope.
- `<details>` renders on github.com, but not in every third-party Markdown
  viewer.
- Folders are presentational. GitHub still stores your repos flat — nothing
  here moves or renames anything.

## License

MIT
