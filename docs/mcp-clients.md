# Connecting Agents (MCP Clients)

memexlab-mcp gives any MCP-speaking agent a governed, citable memory over your
vault. It runs locally over **stdio** — no account, no cloud, no API keys. The
agent gets six tools:

| Tool | What it does |
|---|---|
| `search_vault` | Deterministic BM25 search; results carry `slug`, `path`, `score`, `snippet` |
| `read_note` | Read a note by slug or relative path |
| `capture_note` | File a **new** note — only into `inbox/`, with provenance frontmatter; every write is appended to `.memexlab/log.jsonl` |
| `vault_info` | Vault stats, sections, `write_dir`, and available views |
| `list_queue` | List task-queue items (pending by default) |
| `complete_queue_item` | Complete a queue item — requires a result note; canonical files stay untouched |

The governance boundary holds for every client below: agents can read everything
and cite it, but there is no code path that modifies your canonical notes.

## The command

```bash
uvx memexlab-mcp --vault ~/vault
```

> **Until the PyPI release lands**, use the git form anywhere you see
> `uvx memexlab-mcp`:
>
> ```bash
> uvx --from "git+https://github.com/btekmen/memexlab-engine#subdirectory=memexlab-mcp" memexlab-mcp --vault ~/vault
> ```

No vault yet? Point `--vault` at `examples/fake-vault` from this repo — a
synthetic vault that works with zero setup.

## Claude Code

```bash
claude mcp add memexlab -- uvx memexlab-mcp --vault ~/vault
```

Then ask: *"Search my vault for platform banking and cite the slugs."*

## Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json`:

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

Restart Claude Desktop; the tools appear in the connectors menu.

## Cursor

`~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (per-project) — same
`mcpServers` shape as Claude Desktop above.

## VS Code (Copilot agent mode)

`.vscode/mcp.json`:

```json
{
  "servers": {
    "memexlab": {
      "type": "stdio",
      "command": "uvx",
      "args": ["memexlab-mcp", "--vault", "/absolute/path/to/vault"]
    }
  }
}
```

## Windsurf

`~/.codeium/windsurf/mcp_config.json` — same `mcpServers` shape as Claude Desktop.

## Raycast

Settings → AI → Manage MCP Servers → Add: command `uvx`, args
`memexlab-mcp --vault /absolute/path/to/vault`. Invoke with `@memexlab` in AI chat.

## Zed, Cline, Continue, LM Studio

Any host that supports stdio MCP servers works with the same command. LM Studio is
worth a special note: a local model plus memexlab-mcp is a fully offline stack —
not a single token leaves your machine.

## Verifying the connection

Ask the agent for `vault_info`. You should see your note count, sections, and
`"write_dir": "inbox"`. Then try a capture: the file must land in `inbox/` with
provenance frontmatter, and `.memexlab/log.jsonl` must gain a line. If an agent
ever claims it edited a canonical note, it didn't — there is no tool for that.
