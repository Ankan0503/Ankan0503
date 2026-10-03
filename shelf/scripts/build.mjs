#!/usr/bin/env node
// Shelf — turns a folder tree into a public, collapsible repo index.
//
// GitHub has no folders for repositories, and a browser extension would only
// show them to you. Markdown <details> blocks render for every visitor, so the
// folders live in the profile README instead.
//
//   node scripts/build.mjs --config shelf.config.json --out README.md
//
// Repos named in the config but missing from the account are reported rather
// than silently dropped: an index that quietly omits things is worse than one
// that admits a gap.

import { readFile, writeFile } from "node:fs/promises";

const START = "<!-- shelf:start -->";
const END = "<!-- shelf:end -->";

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

async function fetchRepos(owner) {
  const headers = { Accept: "application/vnd.github+json" };
  if (process.env.GITHUB_TOKEN) {
    headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  }
  const out = [];
  for (let page = 1; page <= 10; page++) {
    const url = `https://api.github.com/users/${owner}/repos?per_page=100&page=${page}&sort=updated`;
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error(`GitHub API ${res.status} for ${owner}: ${await res.text()}`);
    const batch = await res.json();
    out.push(...batch);
    if (batch.length < 100) break;
  }
  return out;
}

const esc = (s) => String(s ?? "").replace(/\|/g, "\\|").replace(/</g, "&lt;");

function monthYear(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-GB", { month: "short", year: "numeric" });
}

function repoLine(repo) {
  const bits = [];
  if (repo.language) bits.push(`\`${repo.language}\``);
  if (repo.stargazers_count) bits.push(`★ ${repo.stargazers_count}`);
  const updated = monthYear(repo.pushed_at);
  if (updated) bits.push(updated);
  if (repo.archived) bits.push("archived");

  const desc = repo.description ? ` — ${esc(repo.description)}` : "";
  const meta = bits.length ? `  <sub>${bits.join(" · ")}</sub>` : "";
  return `- **[${esc(repo.name)}](${repo.html_url})**${desc}${meta}`;
}

// Every repo reachable from a folder and its subfolders, so the parent's
// count reflects the whole subtree rather than only its direct children.
//
// A folder gathers repos two ways:
//   tags  — any repo carrying one of these GitHub topics, picked up automatically
//   repos — named explicitly, for repos that carry no suitable topic
//
// Folders are walked in config order and a repo is claimed by the first folder
// that matches it, so a repo tagged for two folders appears once, in the
// earlier one, rather than being silently duplicated.
function collect(folder, ctx) {
  const direct = [];

  for (const name of folder.repos ?? []) {
    const repo = ctx.byName.get(name.toLowerCase());
    if (!repo) {
      ctx.missing.push(name);
    } else if (!ctx.claimed.has(repo.name)) {
      ctx.claimed.add(repo.name);
      direct.push(repo);
    }
  }

  const tags = (folder.tags ?? []).map((t) => t.toLowerCase());
  if (tags.length) {
    const matched = ctx.repos
      .filter(
        (r) =>
          !ctx.claimed.has(r.name) &&
          (r.topics ?? []).some((t) => tags.includes(t.toLowerCase()))
      )
      .sort((a, b) => new Date(b.pushed_at) - new Date(a.pushed_at));
    for (const repo of matched) {
      ctx.claimed.add(repo.name);
      direct.push(repo);
    }
  }

  const children = (folder.folders ?? []).map((f) => collect(f, ctx));
  const total = direct.length + children.reduce((n, c) => n + c.total, 0);
  return { folder, direct, children, total };
}

const plural = (n) => (n === 1 ? "1 repo" : `${n} repos`);

function renderNode(node, depth = 0) {
  const { folder, direct, children, total } = node;
  const label = plural(total);
  const lines = [];

  lines.push(`<details${depth === 0 ? " open" : ""}>`);
  lines.push(`<summary><b>📁 ${esc(folder.name)}</b> · ${label}</summary>`);
  lines.push("");
  if (folder.blurb) {
    lines.push(`<sub>${esc(folder.blurb)}</sub>`);
    lines.push("");
  }
  if (direct.length) {
    lines.push(...direct.map(repoLine));
    lines.push("");
  }
  for (const child of children) {
    lines.push(...renderNode(child, depth + 1));
    lines.push("");
  }
  if (!direct.length && !children.length) {
    lines.push("<sub>Nothing here yet.</sub>");
    lines.push("");
  }
  lines.push("</details>");
  return lines;
}

function render(config, repos) {
  const ctx = {
    repos,
    byName: new Map(repos.map((r) => [r.name.toLowerCase(), r])),
    missing: [],
    claimed: new Set()
  };
  const nodes = (config.folders ?? []).map((f) => collect(f, ctx));
  const missing = ctx.missing;

  const filed = new Set([...ctx.claimed].map((n) => n.toLowerCase()));

  const out = [START, ""];
  if (config.heading) out.push(config.heading, "");

  for (const node of nodes) {
    out.push(...renderNode(node));
    out.push("");
  }

  if (config.showUnsorted) {
    // The profile repo is excluded by default: it holds this index, so listing
    // it inside the index is just noise.
    const skip = new Set(
      [...(config.exclude ?? []), config.owner].map((s) => s.toLowerCase())
    );
    const rest = repos.filter(
      (r) => !filed.has(r.name.toLowerCase()) && !r.fork && !skip.has(r.name.toLowerCase())
    );
    if (rest.length) {
      out.push("<details>");
      out.push(`<summary><b>📂 Unsorted</b> · ${plural(rest.length)}</summary>`);
      out.push("");
      out.push(...rest.map(repoLine));
      out.push("");
      out.push("</details>");
      out.push("");
    }
  }

  if (missing.length) {
    out.push(
      `<sub>⚠️ Listed in \`shelf.config.json\` but not found on the account: ` +
        `${missing.map((m) => `\`${m}\``).join(", ")}. ` +
        `They may be private, renamed, or under a different owner.</sub>`,
      ""
    );
  }

  // Deliberately no "updated on" date: it would differ on every run, so the
  // workflow would commit every week even when nothing actually changed.
  if (config.toolUrl) {
    out.push(`<sub>Folders generated by [Shelf](${config.toolUrl}).</sub>`, "");
  }
  out.push(END);
  return { markdown: out.join("\n"), missing, filed: filed.size };
}

function splice(existing, block) {
  const a = existing.indexOf(START);
  const b = existing.indexOf(END);
  if (a !== -1 && b !== -1 && b > a) {
    return existing.slice(0, a) + block + existing.slice(b + END.length);
  }
  // No markers yet: append rather than overwrite whatever is already there.
  return `${existing.trimEnd()}\n\n${block}\n`;
}

const configPath = arg("config", "shelf.config.json");
const outPath = arg("out", "README.md");

const config = JSON.parse(await readFile(configPath, "utf8"));
if (!config.owner) throw new Error(`"owner" is required in ${configPath}`);

const repos = await fetchRepos(config.owner);
const { markdown, missing, filed } = render(config, repos);

let existing = "";
try {
  existing = await readFile(outPath, "utf8");
} catch {
  existing = `# ${config.owner}\n`;
}

await writeFile(outPath, splice(existing, markdown));

console.log(`shelf: ${repos.length} repos on the account, ${filed} filed into folders`);
if (missing.length) console.log(`shelf: ${missing.length} not found -> ${missing.join(", ")}`);
console.log(`shelf: wrote ${outPath}`);
