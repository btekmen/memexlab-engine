# Syncing Your Vault with Git

Your vault is a folder of plain markdown — which means the sync problem is already
solved, by the most battle-tested replication tool in software. Git syncs the
filesystem itself: no sync service, no account with us, full history, and readable
diffs because the substrate is markdown. This page is the recommended path from
one-machine vault to every-device vault.

> The invariants do the work here. Because the filesystem is the database and notes
> are plain markdown, git needs no adapter — the vault is already a repository's
> natural shape.

## 1. Make the vault a repository

```bash
cd <your-vault>
git init
```

Add a `.gitignore` before the first commit:

```gitignore
# engine caches — derived, rebuildable, never truth
.memex/
# agent write log — per-device by default (see note)
.memexlab/log.jsonl
# Obsidian per-device state (keep settings, drop workspace churn)
.obsidian/workspace*.json
.obsidian/cache
# OS noise
.DS_Store
Thumbs.db
```

**The log choice, explicitly:** `.memexlab/log.jsonl` is the agent-write audit log. The
default above keeps it per-device (each machine audits its own agents). If you want one
merged audit trail across devices, remove that line and accept occasional append-append
conflicts — both policies are legitimate; pick one deliberately.

Then:

```bash
git add -A && git commit -m "vault: initial commit"
```

## 2. Choose a private remote — the sovereignty ladder

Pick the rung that matches your threat model. Verify privacy before the first push.

| Rung | Remote | Trade-off |
| --- | --- | --- |
| 1 | GitHub/GitLab **private** repo | Easiest; your notes live on their servers (encrypted at rest, but hosted) |
| 2 | Self-hosted forge (Forgejo/Gitea on your VPS) | Your infra, web UI, mobile-friendly HTTPS |
| 3 | Bare repo on your NAS / home server / USB disk | Nothing leaves hardware you own: `git init --bare /volume/vault.git` |

```bash
git remote add origin <your-private-remote>
git push -u origin main
```

**Verification step (do not skip):** open the remote URL in a logged-out/private browser
window — you must see a 404 or a login wall, never your notes.

## 3. The daily rhythm

Two habits prevent nearly all conflicts:

- **Pull before you write.** Start each session (or each device switch) with `git pull`.
- **Commit at natural boundaries.** End of a capture burst, end of a weekly review,
  after every `--apply`. Small commits make history useful and conflicts trivial.

```bash
# a serviceable end-of-session one-liner
git add -A && git commit -m "vault: $(date +%F) session" && git push
```

Automate only after the habit exists (cron/launchd examples belong in your dotfiles,
not in the engine — there is no daemon here by design).

## 4. Mobile

Recommended paths, honestly ranked:

- **iOS — Obsidian + Working Copy (recommended).** Working Copy clones your private
  remote; Obsidian opens the folder via the Files integration. Pull in Working Copy →
  capture in Obsidian → commit/push in Working Copy. Pairs with the share-sheet
  capture recipe (see [Future Expansion](14-future-expansion.md), mobile capture path).
- **Android — Obsidian + Termux git (free, fiddly) or MGit (simpler UI).** Same
  pull → edit → push loop.
- **Syncthing (both platforms)** — real-time folder replication, no history, no
  conflict semantics beyond file copies. Fine as a *transport* between your own
  devices; you lose git's history and review. If you use it, still keep a git remote
  as the system of record.
- **iCloud/Drive sync** — workable for Obsidian alone, but it fights git (partial
  syncs, file locks). Do not point both at the same folder. Choose git *or* blob sync;
  we recommend git.

## 5. When a conflict happens anyway

Atomic, per-note files make collisions rare — two devices must edit the *same note*
between syncs. When it happens:

1. `git pull` reports the conflicted file(s) — almost always one note.
2. Open the note. It is markdown: read the `<<<<<<<`/`>>>>>>>` blocks, keep the right
   sentences, delete the markers.
3. `git add <note> && git commit`.
4. Run `memex lint` (or `scripts/validate_vault.py`) to confirm frontmatter survived.

Never resolve with `--theirs`/`--ours` blindly — the whole point of markdown storage is
that you can read the two versions.

## 6. Secrets discipline (non-negotiable)

- API keys live in your shell environment only — never in any file under version
  control (this is already an engine non-negotiable; sync makes it existential).
- Respect the deny-patterns in `governance.yml`: credentials, raw private messages,
  customer records and similar material do not belong in a synced vault.
- Before the first push of an existing vault, scan it:
  `git grep -iE 'api[_-]?key|secret|BEGIN (RSA|OPENSSH)' -- '*.md'` should return
  nothing.

## 7. Two-device walkthrough (prove it works)

1. Laptop: init, `.gitignore`, commit, push to a private remote (§1–2).
2. Phone: clone in Working Copy / Termux, open the folder in Obsidian.
3. Phone: capture a note into `inbox/`, commit, push.
4. Laptop: `git pull` — the note is there.
5. Laptop: run your normal flow (`memex lint`, weekly review, `memex qa`).
6. Laptop: commit + push; pull on the phone. Round-trip complete — you have a synced,
   versioned, fully local-first vault.

## 8. Teams — a preview, not a feature

Two or more people on one vault is a different contract: scoped write folders,
PR-based review, contributor provenance. The design is sketched in
[Future Expansion — multi-user](14-future-expansion.md); until that ships, the honest
answer for teams is "one owner, collaborators via pull requests".

## What we will never build

A proprietary sync protocol or a hosted sync service. Mandatory cloud hosting is on the
"paths we will not pursue" list in [Future Expansion](14-future-expansion.md). A thin
`memex sync` convenience wrapper (git status/pull/push with a dry-run diff preview,
refusing to push when lint fails) may come later if real friction reports justify it —
it would be git porcelain, nothing more.

---

[Docs index](README.md) · [Maintenance](13-maintenance.md) · [Future Expansion](14-future-expansion.md)
