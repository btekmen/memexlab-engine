# memexlab-mcp

**Governed, citable, local memory for AI agents.** An MCP server over a plain-markdown
vault: your agent can search it, cite it (`[[slug]]`), and file new notes — but only
into `inbox/`, with provenance, and every write logged. It can have memory without
being able to corrupt it.

## Quickstart (no keys needed)

```bash
uvx memexlab-mcp --vault path/to/your-vault        # any folder of markdown files
```

> **Not on PyPI yet.** Until `memexlab-mcp` is published, run the same command straight
> from source with `uv`'s git-subdirectory form — no clone, no install step:
> ```bash
> uvx --from "git+https://github.com/btekmen/memexlab-engine@feat/memexlab-mcp#subdirectory=memexlab-mcp" \
>   memexlab-mcp --vault path/to/your-vault
> ```
> (this pin points at the feature branch; once merged to main you can drop the
> `@feat/memexlab-mcp` ref, and once on PyPI this note goes away)

Try the scripted demo on the synthetic vault in this repo:

```bash
git clone -b feat/memexlab-mcp https://github.com/btekmen/memexlab-engine && cd memexlab-engine
uvx --from ./memexlab-mcp memexlab-mcp-demo --vault examples/fake-vault
```

## Add to your agent

**Claude Code**
```bash
claude mcp add memexlab -- uvx memexlab-mcp --vault ~/vault
```
Pre-publish, use the git-subdirectory form instead of `uvx memexlab-mcp` (this pin points
at the feature branch; once merged to main you can drop the `@feat/memexlab-mcp` ref, and
once on PyPI this note goes away):
```bash
claude mcp add memexlab -- uvx --from "git+https://github.com/btekmen/memexlab-engine@feat/memexlab-mcp#subdirectory=memexlab-mcp" memexlab-mcp --vault ~/vault
```

**Claude Desktop** — `claude_desktop_config.json`:
```json
{ "mcpServers": { "memexlab": { "command": "uvx", "args": ["memexlab-mcp", "--vault", "/absolute/path/to/vault"] } } }
```

**Cursor** — `.cursor/mcp.json`: same `command`/`args` block as above.

## Tools

| Tool | What it does |
| --- | --- |
| `vault_info()` | Notes count, sections, available views, and the governed write dir |
| `search_vault(query, view=)` | Deterministic BM25 — results carry `[[slug]]`s to cite; `view=` scopes to a saved query |
| `read_note(note)` | Frontmatter + body |
| `capture_note(title, body, sources)` | Files a note into `inbox/` with provenance; logged to `.memexlab/log.jsonl`; canonical is untouchable |

Governance: the write boundary defaults to `inbox/` and can be set with `write_dir:` in
your vault's `governance.yml`. There is no code path that writes anywhere else.

## Views — saved queries as files

A view is a plain note in `views/` that names a reusable slice of the vault:

```markdown
---
type: view
title: Banking Notes
query:
  any_tags: [banking]      # also: tags, not_tags, types, statuses, folders, since, until, text
---
```

`search_vault(view="banking")` searches only that slice (with an empty query it lists
the members, or uses the view's own `text:` field). Evaluation is deterministic and
read-only; sharing a view = sharing the file. Unknown query fields are errors.
Try it on the synthetic vault: `examples/fake-vault/views/banking.md`.

Part of [MemexLab](https://memexlab.xyz) — the governed memory layer for AI agents. MIT.
