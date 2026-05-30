# Quickstart

Ten minutes from zero to a working vault with one source ingested and one concept note created. The full onboarding is in `09-onboarding.md`; this page is the compressed version.

## Prerequisites (2 min)

Install:

```
brew install git python@3.12 obsidiancurl -LsSf https://astral.sh/uv/install.sh | sh
```

Get an API key from your LLM provider — e.g. Anthropic (https://console.anthropic.com) or OpenAI (https://platform.openai.com) — and export the variable it expects:

```
export ANTHROPIC_API_KEY=sk-ant-...   # Anthropic
# export OPENAI_API_KEY=sk-...        # ...or OpenAI
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.zshrc
source ~/.zshrc
```

## Clone the engine (1 min)

```
git clone <your-memex-repo> ~/memexcd ~/memexuv sync
```

## Create the vault (1 min)

```
mkdir -p ~/Documents/Obsidian/<your-vault>/{inbox,raw,wiki,people,companies,philosophies,eras,projects,archive,templates,_qa,_index,_essays,_slides,_charts,_lint,.memex/snapshots}touch ~/Documents/Obsidian/<your-vault>/.memex/log.jsonlecho "VAULT_PATH=$HOME/Documents/Obsidian/<your-vault>" > ~/memex/.env
```

Open the vault in Obsidian: `File → Open vault → Open folder as vault`, pick `~/Documents/Obsidian/<your-vault>`.

Install the Templater plugin from `Settings → Community plugins`. Point Templater’s template folder at `templates/`.

## Confirm the engine sees the vault (1 min)

```
cd ~/memexuv run python -m memex doctor --api
```

Expect `doctor_ok`. If not, read the error — it’ll tell you exactly what to fix.

## Add the two core notes (2 min)

```
Create ~/Documents/Obsidian/<your-vault>/<your-name>.md:
<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>title: "<your-name>"type: personacreated: 2026-04-19updated: 2026-04-19status: activetags: []latticework: []<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div># <your-name>Founder / operator in fintech. Building <your-company> and <your-product>. Thinks in termsof five Latticework problems: seeing reality clearly, deciding under uncertainty,allocating time and energy, avoiding self-deception, playing long games.
Create ~/Documents/Obsidian/<your-vault>/memexlab.md:
<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>title: "MemexLab"type: manifestcreated: 2026-04-19updated: 2026-04-19status: activetags: []latticework: []<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div># MemexLabA markdown-first second brain. Inbox → raw → wiki → outputs. Filesystem is thedatabase. Engine is additive. LLM compiles; human decides.
```

## Ingest one source (2 min)

Find a web article you want to keep. Create `~/Documents/Obsidian/<your-vault>/raw/2026-04-19-example-source.md`:

```
<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>title: "<article title>"type: sourcesource_url: <url>publisher: <publisher>publication_date: 2026-04-17ingested: 2026-04-19status: seedtags: [topic/<your-topic>]latticework: [problem-1]<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>## Original text<paste the article text here>## Reactions- <one sentence>## Related-
```

## Compile it (1 min)

```
uv run python -m memex compile \    ~/Documents/Obsidian/<your-vault>/raw/2026-04-19-example-source.md
```

Read the dry-run output. If it looks right:

```
uv run python -m memex compile \    ~/Documents/Obsidian/<your-vault>/raw/2026-04-19-example-source.md --apply
```

New files appear in `wiki/`. Open one in Obsidian; read it; add two `[[links]]` to related concepts.

## Ask the vault a question

```
uv run python -m memex qa "What did I just learn from the source?"
```

An answer note lands in `_qa/` with slug citations. Open it in Obsidian; follow the links back to the atomic notes.

## Schedule the daily linter

```
crontab -e
```

Add:

```
0 6 * * * cd ~/memex && uv run python scripts/lint_daily.py \    2>> ~/Documents/Obsidian/<your-vault>/.memex/log.jsonl
```

From tomorrow morning, the vault lints itself.

## You’re done

The loop is live. Capture aggressively; compile weekly; ask questions whenever you want; produce when you have a reason.

Read `04-daily-workflow.md` for the day-to-day rhythm, `10-best-practices.md` for how to keep the vault compounding, and `11-common-mistakes.md` for what to watch out for.

---

[← FAQ](15-faq.md) · [Docs index](README.md) · [Maintenance Checklist →](maintenance-checklist.md)
