---
name: memex-resolve
description: Record a conflict with an existing vault note as a new contested inbox note, and file a resolution proposal a human approves. Never edit or overwrite the note the conflict is about.
---

# Memex Resolve

When new information conflicts with a note already in the vault, keep the old note. File the disagreement beside it.

## Capture a conflict

Call `capture_note` (or `scripts/resolve_contest.py capture`):

- `contests`: the slug or slugs the new evidence disagrees with
- `body`: the evidence
- `origin_ref`: optional; the same value returns the existing contested note

The new file lands in the inbox with `status: contested` and a `contests` list. The named notes are not opened for writing.

`status` on a new note may also be `active`, `stale`, or `archived`. Omit `status` and `contests` and capture behaves as before. Notes that have no `status` stay valid.

## Propose a resolution

Call `propose_resolution` (or `scripts/resolve_contest.py propose`). Pass the contested note's slug and the proposed outcome.

The tool files a second inbox note:

- `resolution: proposed`
- `resolves`: the contested slug
- `status: active` on the proposal itself

It does not change the contested note, and it does not change the notes that note contests. A human applies the proposal by editing the vault. There is no migration that stamps `status` onto existing notes.

The script is dry-run until `--apply`. The MCP tools write the new note immediately and still never edit an existing one. The same `origin_ref` returns the proposal already filed.

## What to read back

`get_index` lists contested notes first. The line includes `contested` and `contests [[slug]]`. Search hits include `status`, and contested hits include `contests`.
