# MCP client setup recipes

`memexlab-mcp` gives any MCP-capable agent governed, citable memory over a plain-markdown
vault: deterministic BM25 search with `[[slug]]` citations, reads, and writes that can
only land in `inbox/` — with provenance frontmatter and a JSONL audit log. No account,
no cloud, no keys.

> **Package status.** The commands below use the published package name. Until the first
> PyPI release lands, use the pinned install form in the `memexlab-mcp` README instead —
> same flags, different source.

The vault can be any folder of markdown files. To try it with zero setup, point it at
this repo's synthetic vault: `--vault examples/fake-vault`.

## Claude Code

```bash
claude mcp add memexlab -- uvx memexlab-mcp --vault ~/vault
```

## Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "memexlab": {
      "command": "uvx",
      "args": ["memexlab-mcp", "--vault", "/absolute/path/to/vault"]
    }
  }
}
```

## Cursor

Add the same block to `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global):

```json
{
  "mcpServers": {
    "memexlab": {
      "command": "uvx",
      "args": ["memexlab-mcp", "--vault", "/absolute/path/to/vault"]
    }
  }
}
```

## Any other MCP client

The server is standard stdio MCP — configure the command `uvx` with args
`["memexlab-mcp", "--vault", "<path>"]` wherever your client accepts an MCP server
definition. Tools exposed:

| Tool | What it does |
| --- | --- |
| `vault_info()` | Notes count, sections, and the governed write directory |
| `search_vault(query)` | Deterministic BM25 — results carry `[[slug]]`s to cite |
| `read_note(note)` | Frontmatter + body of one note |
| `capture_note(title, body, sources)` | Files a note into `inbox/` with provenance; logged to `.memexlab/log.jsonl` |

## The governance boundary (why this is safe to wire into any agent)

- Writes land **only** in the vault's write directory (default `inbox/`; configurable
  via `write_dir:` in the vault's `governance.yml`). There is no code path that
  modifies canonical notes.
- Every write appends one JSON event to `.memexlab/log.jsonl` — audit before trust.
- Retrieval is deterministic: same vault, same query, same results. Citations point at
  your actual files, so every answer is checkable.

## Agent-readable docs

Agents (and you) can consume this documentation without the rendered site:
[`llms.txt`](../llms.txt) indexes every page's raw markdown, and
[`llms-full.txt`](../llms-full.txt) is the whole manual in one file. Both are generated —
`python3 scripts/build_llms_txt.py --apply` regenerates them, `--check` verifies they
are current.

---

[← Engineering index](README.md)
