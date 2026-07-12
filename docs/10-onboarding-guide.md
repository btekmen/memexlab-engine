# Onboarding Guide

This is the minimum path from “I have an empty laptop” to “I am operating the system.” It assumes nothing beyond comfort with a terminal and a text editor. The whole path takes roughly two hours if you work straight through, though splitting it across two sittings is healthier.

The goal of onboarding is not to build a perfect vault. It is to build a vault you trust enough to feed, so that three months from now you have enough raw material for the system’s compounding benefits to appear.

## Prerequisites

You will install the following. Everything is free; everything is cross-platform.

Tool

Why

Install

Obsidian

Editor, renderer, link graph, template runner.

https://obsidian.md

Git

Vault and engine are both version-controlled.

`brew install git` / platform installer

Python 3.12+

The engine runs on it.

`brew install python@3.12` / platform installer

uv

Python environment manager used by the engine.

```
curl -LsSf https://astral.sh/uv/install.sh \| sh
```

An LLM provider API key (Anthropic, OpenAI, …)

The engine’s LLM-driven modes call your configured model.

https://console.anthropic.com (Anthropic) · https://platform.openai.com (OpenAI)

Marp CLI (optional)

For rendering `.md` slides to `.pdf` / `.html`. Only needed if you’ll generate decks.

```
npm i -g @marp-team/marp-cli
```

Verify with:

```
obsidian --version          # graphical app; check Help > About if no CLIgit --versionpython3.12 --versionuv --version
```

## Step 1 — Clone the engine

```
cd ~git clone <your-memex-repo> memexcd memexuv sync
```

This installs the engine’s Python dependencies into a local `.venv/` and makes `memex` invocable via `uv run python -m memex`.

Run `memex doctor` — it will complain that your provider API key (e.g. `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`) is unset and `VAULT_PATH` is unset. That’s expected; we fix it in Step 3.

## Step 2 — Create the vault

Obsidian treats any folder as a vault. The recommended structure is outside the engine repo:

```
~/Documents/Obsidian/<your-vault>/
```

Create it:

```
mkdir -p ~/Documents/Obsidian/<your-vault>
```

Inside that folder, create the core scaffolding:

```
cd ~/Documents/Obsidian/<your-vault>mkdir -p inbox raw wiki people companies philosophies eras \         projects archive templates daily \         _qa _index _essays _slides _charts _lint \         .memex/snapshots .memextouch .memex/log.jsonl
```

Open the folder in Obsidian (`File → Open vault → Open folder as vault`). Obsidian will write its own `.obsidian/` directory and you’ll see the sidebar populate with your empty folders.

### Install required Obsidian plugins

From `Settings → Community plugins`, install and enable:

- Templater — template execution. Configure `Settings → Templater → Template folder location` to `templates/`.

- Dataview — in-vault queries.

- (Optional) Text Generator or similar capture plugins — only if you want in-editor LLM prompts. Not required; the engine handles this externally.

Reload the vault.

## Step 3 — Configure the engine

The engine reads two environment variables plus an optional `.env` in the engine repo.

```
cd ~/memexcat > .env <<EOFVAULT_PATH=$HOME/Documents/Obsidian/<your-vault>EOF
```

Put the API key in your shell profile (not in `.env`), because `.env` is easier to accidentally commit:

```
# ~/.zshrc or ~/.bashrc — set the variable your provider expects
export ANTHROPIC_API_KEY=sk-ant-...   # Anthropic
# export OPENAI_API_KEY=sk-...        # ...or OpenAI
```

Reload the shell, then confirm:

```
cd ~/memexuv run python -m memex doctor --api
```

Expected output: `doctor_ok` with the vault path echoed back and the API ping successful. If either fails, the error message is actionable.

## Step 4 — Add the two core notes

Every vault has two “core” notes — a persona note (about you) and a system note (about how the vault works). They are part of every engine retrieval, which means they permanently ground the model in who you are and what you’re trying to do. Time spent on them pays dividends.

Create `<your-name>.md` in the vault root:

```
<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>title: "<your-name>"type: personacreated: 2026-04-19updated: 2026-04-19status: activetags: []latticework: []<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div># <your-name>## Who I amFounder and operator in fintech. Building [[<your-company>]] and [[<your-product>]]. Interestedin programmable money, AI-native banking, stablecoin settlement, embedded finance,regulatory strategy, and Islamic finance.## How I thinkI use a Latticework of five problems as my primary framing:1. **Seeing reality clearly** — what is actually happening, not what I hope is.2. **Deciding under uncertainty** — choosing when the signal is partial.3. **Allocating time and energy** — committing the scarcest resources well.4. **Avoiding self-deception** — knowing where my own reasoning breaks down.5. **Playing long games** — building things that compound over decades.Every atomic note in this vault is tagged with zero or more of these in its`latticework:` frontmatter.## What this vault is forA governed, citable knowledge system that compounds across years. Ingests everything I read and thinkabout. Outputs first-drafts of essays, decks, memos, and strategic briefs. Ownedin markdown, queryable via its own CLI.
```

Create `memexlab.md` in the vault root:

```
<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>title: "MemexLab"type: manifestcreated: 2026-04-19updated: 2026-04-19status: activetags: []latticework: []<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div># MemexLab## What this system isA markdown-first governed memory layer for agents. Inbox captures, raw sources, atomic wiki notes,curated ontology, project folders, engine-generated outputs. Filesystem is thedatabase; Obsidian is the editor; `memex` is the engine.## How a note enters the wiki1. Captured into `inbox/`.2. Promoted to `raw/` when the source is worth keeping.3. Compiled into atomic notes in `wiki/` via `memex compile`.4. Linked to neighbouring notes.5. Promoted from `seed` → `draft` → `evergreen` as it earns trust.## How an output is made`memex qa`, `memex index`, `memex export essay`, `memex export slides`, or`memex chart`. Every output is a first draft that is edited in Obsidian likeany other markdown file.## Non-negotiables- Dry-run before `--apply`, always.- No auto-promote. All status transitions are manual.- No links into `archive/` from active notes.- Lint passes before end of day.
```

These two notes will be refined over months, but even this first version is enough for the engine to perform sensibly.

## Step 5 — Install templates

Create the following files in `templates/`. The minimum set for first use is `inbox.md`, `source.md`, and `concept.md`.

### templates/inbox.md

```
<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>date: <% tp.date.now("YYYY-MM-DD") %>time: <% tp.date.now("HH:mm") %>tags: []<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div><% tp.file.cursor() %>
```

### templates/source.md

```
<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>title: "<% tp.file.title %>"type: sourcesource_url: publisher: author: publication_date: ingested: <% tp.date.now("YYYY-MM-DD") %>status: seedtags: []latticework: []<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>## Original text<% tp.file.cursor() %>## Reactions- ## Related-
```

### templates/concept.md

```
<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>date: <% tp.date.now("YYYY-MM-DD") %>type: articletitle: "<% tp.file.title %>"status: seedtags: []latticework: []<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div># <% tp.file.title %><1–2 sentence definition>## What it is## Why it matters## Related-
In Settings → Templater → Folder templates, map:
inbox/ → templates/inbox.md
raw/ → templates/source.md
wiki/ → templates/concept.md
```

Now, creating a new file in any of those folders auto-applies the right template.

The remaining templates (`paper.md`, `transcript.md`, `memo.md`, `person.md`, `company.md`, `philosophy.md`, `era.md`, `project.md`, `slides.md`, `daily-note.md`) are documented in `05-templates.md`. Add them when you first need them — don’t pre-build the ones you aren’t sure you’ll use.

## Step 6 — Capture your first inbox item

In Obsidian, create a new file in `inbox/`. The template auto-runs; you get a dated skeleton. Paste a URL you saved recently and one line about why it mattered. Save.

Do this five more times across the day. Don’t think about structure. The goal right now is to build the reflex of capture — if the inbox feels friction-free, the rest of the system follows.

## Step 7 — Promote your first source

Pick one inbox item. Fetch the full text of the source (copy-paste from the reader, or `curl` the page). In Obsidian, create `raw/<YYYY-MM-DD-publisher-slug>.md`. The source template auto-applies. Fill in the frontmatter: `source_url`, `publisher`, `author`, `publication_date`, appropriate `tags` and `latticework` values. Paste the full article text into the `Original text` section.

Delete the inbox item.

Now run, from the engine repo:

```
cd ~/memexuv run python -m memex lint
```

You should see zero errors. If the linter complains about schema fields, revisit the frontmatter.

## Step 8 — Compile your first atomic notes

Once you have one raw source fully ingested, compile it:

```
uv run python -m memex compile \    ~/Documents/Obsidian/<your-vault>/raw/<your-file>.md
```

Read the dry-run output. You’ll see a list of proposed atomic notes with titles, slugs, tags, and bodies. Decide which ones are keepers. If most look good:

```
uv run python -m memex compile \    ~/Documents/Obsidian/<your-vault>/raw/<your-file>.md --apply
```

New files appear in `wiki/`. Open them in Obsidian. Read each one. Edit where needed. Add at least two `[[wiki-links]]` each.

This is the first time the system is visibly useful. You went from a single long article to a handful of clean, linked atomic notes in a few minutes. The quality depends on your raw source and your review — this is not a magic step, but it is a compounding one.

## Step 9 — Ask the vault a question

With even a few atomic notes in place, try:

```
uv run python -m memex qa "What is the tradeoff between gross and net settlement?"
```

If your vault has the relevant notes, the engine retrieves them, writes an answer note into `_qa/`, and cites `[[slug]]` references inline. Open the `_qa/` file in Obsidian. Follow the citations. If the answer is wrong, find the weak note and improve it — that is the feedback loop.

If the vault doesn’t yet have the right notes, the engine will say so honestly. That is also useful — it tells you where to ingest next.

## Step 10 — Schedule the daily linter

```
crontab -e
```

Add:

```
0 6 * * * cd ~/memex && uv run python scripts/lint_daily.py \    2>> ~/Documents/Obsidian/<your-vault>/.memex/log.jsonl
```

From tomorrow morning, the vault lints itself. You wake up to either silence (all good) or a dated report in `_lint/` showing what needs attention.

## Step 11 — Set up a weekly review recurring event

On your calendar, a recurring 60-minute block, same time every week. The review is:

- Inbox sweep. Promote, merge, or delete every item.

- Raw triage. For each new raw file, decide: compile now, compile later, reference only.

- Compile queue. Run `memex compile` on everything in the “now” bucket.

- Link pass. Open every `status: seed` note from the week and add missing links.

- Lint report review. Read the week’s lint reports. Fix anything non-trivial.

This is non-negotiable. The vault compounds in direct proportion to how faithfully you run this review.

## Day-one done

At this point:

- The engine installs cleanly and can run all eight modes.

- The vault has its two core notes and at least one raw source compiled into atomic notes.

- You’ve asked the vault a question and read the answer.

- The daily linter runs overnight.

- A weekly review is on your calendar.

A month of consistent capture and triage will give you a vault that can answer real questions. Three months will produce a vault worth building outputs from. A year will produce a vault that makes you a noticeably better thinker in your domain.

## Read next

- `04-daily-workflow.md` — the daily / weekly rhythms in detail.

- `10-best-practices.md` — how to make the vault better over time.

- `11-common-mistakes.md` — what to watch out for in the first months.

---

[← User Modes](09-user-modes.md) · [Docs index](README.md) · [Best Practices →](11-best-practices.md)
