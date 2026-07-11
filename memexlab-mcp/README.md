# memexlab-mcp

**Governed, citable, local memory for AI agents.** An MCP server over a plain-markdown
vault: your agent can search it, cite it (`[[slug]]`), and file new notes — but only
into `inbox/`, with provenance, and every write logged. It can have memory without
being able to corrupt it.

## Quickstart (no keys needed)

```bash
uvx memexlab-mcp --vault path/to/your-vault        # any folder of markdown files
```

Try it on the synthetic vault in this repo:

```bash
git clone https://github.com/btekmen/memexlab-engine && cd memexlab-engine
uvx --from ./memexlab-mcp memexlab-mcp-demo --vault examples/fake-vault
```

## Add to your agent

**Claude Code**
```bash
claude mcp add memexlab -- uvx memexlab-mcp --vault ~/vault
```

**Claude Desktop** — `claude_desktop_config.json`:
```json
{ "mcpServers": { "memexlab": { "command": "uvx", "args": ["memexlab-mcp", "--vault", "/absolute/path/to/vault"] } } }
```

**Cursor** — `.cursor/mcp.json`: same `command`/`args` block as above.

## Tools

| Tool | What it does |
| --- | --- |
| `vault_info()` | Notes count, sections, and the governed write dir |
| `search_vault(query)` | Deterministic BM25 — results carry `[[slug]]`s to cite |
| `read_note(slug_or_path)` | Frontmatter + body |
| `capture_note(title, body, sources)` | Files a note into `inbox/` with provenance; logged to `.memexlab/log.jsonl`; canonical is untouchable |

Governance: the write boundary defaults to `inbox/` and can be set with `write_dir:` in
your vault's `governance.yml`. There is no code path that writes anywhere else.

Part of [MemexLab](https://memexlab.xyz) — the governed memory layer for AI agents. MIT.
