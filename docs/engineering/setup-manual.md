
# From-Scratch Setup Manual

## 1. Goal

Build a local-first, agent-operable second brain that a person or team can use for:

- meeting preparation
- relationship intelligence
- company and market memory
- book and research synthesis
- decision logs
- strategic briefs
- recurring operating reviews

The target system keeps human-readable files as the source of truth:

```text
Markdown Vault -> Schema + Index -> Agent Skills -> Query / Brief / Eval
```

Markdown remains the source of truth. Indexes accelerate retrieval. Agent skills make ingest, query, briefing, markdown editing, and evaluation repeatable.

Intellectual lineage matters. Start with Andrej Karpathy's LLM Knowledge Bases / LLM Wiki pattern, then add Garry Tan's GStack/GBrain operational layer. This repo packages those influences into a reusable framework with schemas, skills, evals, governance, and validation. See [Lineage and Credits](lineage.md).

## 2. Required Components

### Core

- macOS or Linux host
- Git
- GitHub account or GitHub Enterprise
- Python 3
- Optional agent runtime, such as OpenClaw or Codex
- Optional retrieval/indexing layer, such as GBrain
- Optional embedding provider key when semantic search is enabled

### Optional Integrations

- Telegram, Slack, Discord, or WhatsApp for chat
- Gmail / Google Workspace for email and calendar ingestion
- Notion, Google Drive, or local folders for document ingestion
- Twilio or WebRTC for voice-to-brain
- Supabase for hosted Postgres when local PGLite is no longer enough

## 3. Recommended Repository Layout

Use this repository as the framework and keep real private vault data separate:

```text
memex/           # framework, docs, skills, schemas, evals, synthetic examples
private-vault/   # real private knowledge vault, access-controlled
```

Keep them separate. This repo can be made public after privacy review. Real vaults should remain private unless explicitly sanitized.

Recommended private vault structure:

```text
private-vault/
├── AGENTS.md
├── RESOLVER.md
├── schema.md
├── log.md
├── people/
├── companies/
├── projects/
├── books/
├── concepts/
├── philosophies/
├── decisions/
├── relationships/
├── sources/
├── raw/
├── inbox/
├── artifacts/
├── briefs/
├── reviews/
└── templates/
```

## 4. Install Runtime

Clone the framework repo:

```bash
git clone https://github.com/YOUR_ORG/memex.git
cd memex
python3 scripts/validate_index.py
python3 scripts/validate_vault.py examples/fake-vault
```

The validation commands should pass before you connect a real vault.

## 5. Optional Retrieval Runtime

Install Bun:

```bash
curl -fsSL https://bun.sh/install | bash
export PATH="$HOME/.bun/bin:$PATH"
```

Add the path permanently:

```bash
echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.zshrc
```

Install GBrain if you want local keyword/vector retrieval:

```bash
git clone https://github.com/garrytan/gbrain.git ~/gbrain
cd ~/gbrain
bun install
bun link
gbrain --version
```

## 6. Create the Private Vault Repo

```bash
mkdir -p ~/private-vault
cd ~/private-vault
git init
mkdir -p people companies projects books concepts philosophies decisions relationships sources raw inbox artifacts briefs reviews templates
touch AGENTS.md RESOLVER.md schema.md log.md
```

First commit:

```bash
git add .
git commit -m "Initialize private memex vault"
```

## 7. Configure Secrets

Set an embedding key only if your retrieval layer needs one:

```bash
export OPENAI_API_KEY="YOUR_EMBEDDING_KEY"
```

Persist it in a secure environment manager, not inside this repo or the private vault.

Do not commit:

- API keys
- OAuth tokens
- private credentials
- raw customer records
- cap tables or board materials unless the repository is private and access-controlled

## 8. Initialize Retrieval

```bash
gbrain init
gbrain doctor --json
```

Import the private vault without embeddings first:

```bash
gbrain import ~/private-vault --no-embed
```

Generate embeddings:

```bash
gbrain embed --stale
```

Verify:

```bash
gbrain health
gbrain query "what are the main themes in this brain?"
```

Expected healthy state:

```text
Embed coverage: 100.0%
Missing embeddings: 0
Stale pages: 0
Dead links: 0
```

## 9. Configure Sync

Point GBrain to the private vault repo:

```bash
gbrain sync --repo ~/private-vault --no-pull --no-embed
```

After normal edits:

```bash
gbrain sync --repo ~/private-vault --no-pull --no-embed
gbrain embed --stale
```

If using a hosted Git remote:

```bash
gbrain sync --repo ~/private-vault
```

## 10. Install and Configure an Agent Runtime

Install or deploy OpenClaw according to your runtime:

- local workstation for personal use
- private cloud VM for executive assistant workflows
- managed OpenClaw deployment for team access

The OpenClaw agent needs:

- workspace access to `private-vault`
- shell access to `gbrain`
- access to `OPENAI_API_KEY` for embeddings
- chat surface connection, such as Telegram or Slack
- cron/scheduler access for maintenance jobs

## 11. Add Agent Operating Instructions

Create `AGENTS.md` in the private vault repo:

```markdown
# AGENTS.md

This vault is a private executive memory system.

Rules:
- Search before answering questions about people, companies, meetings, books, decisions, or strategy.
- Use GBrain for world knowledge and vault facts.
- Use operational memory for user preferences and assistant behavior.
- Every new claim added to the brain needs provenance.
- Raw sources are append-only.
- Never publish or send private vault content externally without explicit approval.
- Log every durable write in log.md.
```

Create `RESOLVER.md`:

```markdown
# RESOLVER.md

Slug rules:
- lowercase ASCII
- spaces become hyphens
- Turkish characters are folded: ı->i, İ->i, ş->s, ğ->g, ü->u, ö->o, ç->c
- people use firstname-lastname
- companies use common company name
- books use title slug, author only when needed

Never create duplicate entities when a canonical page already exists.
```

## 12. Create Core Templates

Use the templates in [templates](templates.md) for:

- person pages
- company pages
- book pages
- concept pages
- meeting notes
- decision records

Templates are not bureaucracy. They make the brain machine-readable.

## 12. First Ingestion Pass

Start with high-value material:

1. top 50 people
2. top 30 companies
3. active projects
4. current strategic theses
5. board and investor materials
6. important books and articles
7. recent meeting notes

For each item:

```bash
gbrain put <slug> --content "$(cat path/to/file.md)"
```

Or bulk import:

```bash
gbrain import ~/private-vault --no-embed
gbrain embed --stale
```

## 13. Set Up Recurring Jobs

Minimum viable cadence:

```text
Every 15 minutes:
  gbrain sync --repo ~/private-vault --no-pull --no-embed

Hourly:
  gbrain embed --stale

Daily:
  gbrain health
  create daily memory note
  process inbox/

Weekly:
  dead-link scan
  orphan-page review
  stale-claim review
  top-project review
```

OpenClaw cron should run these as isolated jobs when possible.

## 14. OpenClaw Workflows

### Pre-Meeting Brief

Input:

```text
Prep me for my meeting with Jane Doe.
```

Procedure:

1. `gbrain search "Jane Doe"`
2. `gbrain get people/jane-doe`
3. query neighboring company/project pages
4. produce concise brief with:
   - role
   - history
   - open threads
   - risks
   - one sharp question

### Book-to-Brain

Input:

```text
Ingest this book summary.
```

Procedure:

1. create or update book entity
2. extract thesis
3. extract mental models
4. connect to concepts and strategic theses
5. add provenance
6. sync and embed

### Decision Log

Input:

```text
Record this decision.
```

Procedure:

1. create decision page
2. capture context, options, decision, rationale, date, owner
3. link people, companies, projects
4. add review date

## 15. Verification Checklist

A system is ready when all checks pass:

- `gbrain health` shows 100% embedding coverage
- `gbrain query` returns relevant pages
- `gbrain get <slug>` returns exact entities
- OpenClaw can call GBrain from chat
- OpenClaw can write a new entity
- sync picks up file changes
- embeddings refresh after updates
- no secrets are committed
- the framework repo has no private vault content
- the private vault repo is access-controlled

## 16. GitHub Pages Publishing

Publish only the framework repo after privacy review. Do not publish an unsanitized private vault.

```bash
cd memex
git init
git add .
git commit -m "Initial Memex framework"
git branch -M main
git remote add origin git@github.com:YOUR_ORG/memex.git
git push -u origin main
```

In GitHub:

1. Settings
2. Pages
3. Deploy from branch
4. Branch: `main`
5. Folder: `/root`
6. Save

## 17. Common Failure Modes

### GBrain Search Works, Query Does Not

Likely missing `OPENAI_API_KEY`.

```bash
echo $OPENAI_API_KEY
gbrain embed --stale
```

### Sync Points to Old Repo

Run:

```bash
gbrain config set sync.repo_path ~/private-vault
gbrain sync --repo ~/private-vault --no-pull --no-embed
```

### Missing Embeddings

Run:

```bash
gbrain embed --stale
gbrain health
```

### Duplicate People or Companies

Do not delete. Merge into a canonical slug and leave a redirect.

### Agent Gives Unsourced Claims

Tighten `AGENTS.md`: require citation to slugs before strategic claims.

## 18. Definition of Done

The setup is complete when an executive can ask:

```text
What do we know about this person, why does it matter, and what should I ask next?
```

And the agent can answer from the brain with cited, current, inspectable evidence.
