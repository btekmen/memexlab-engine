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

## NVIDIA NemoClaw / OpenShell (sandboxed agents)

NemoClaw runs agents — OpenClaw by default — inside hardened OpenShell sandboxes
with egress control and routed inference. It composes cleanly with MemexLab:
**OpenShell governs the runtime (network, credentials, model calls); the vault
governs the memory (inbox-only writes, provenance, citations).** Two boundaries,
no overlap.

Two lanes, depending on how the agent consumes the vault:

**Lane A — Agent Skills (OpenClaw's native surface).** Skills are plain files, and
NemoClaw's snapshot/rebuild flows explicitly preserve skills paths and app state.

1. Allow egress to your private git host once (`nemo-deepagents <sandbox> policy-add
   … --dry-run`, then `--yes` — NemoClaw policies are dry-run-first too), and clone
   the vault inside the sandbox: `git clone <private-remote> /sandbox/vault`
   (see the [vault sync guide](vault-sync.md) for the private-remote setup).
2. Install this repo's `skills/` into the sandboxed OpenClaw's skills path.
3. The agent now operates the vault through the memex skills; at runtime nothing
   needs egress except your git pushes.

**Lane B — memexlab-mcp inside the sandbox.** Note the constraint we verified in
NVIDIA's docs: NemoClaw's *managed* MCP registration (`nemoclaw <sandbox> mcp add`)
canonicalizes **HTTPS-only** server definitions — a stdio server like memexlab-mcp
doesn't ride that flow. Instead, run it agent-native, entirely in-sandbox:

1. Create a project venv under the sandbox (per NemoClaw's own guidance):
   `python3 -m venv /sandbox/venvs/memex && /sandbox/venvs/memex/bin/pip install
   memexlab-mcp` (needs PyPI egress once — or copy the wheel into the sandbox and
   install from the file: zero egress).
2. Register it in the agent's own MCP config as a stdio server: command
   `/sandbox/venvs/memex/bin/memexlab-mcp`, args `--vault /sandbox/vault`.
3. Runtime needs **no network at all** — retrieval is local BM25, writes land in
   `/sandbox/vault/inbox/` with provenance, and the vault never leaves the sandbox.

> Status: this recipe is verified against NVIDIA's published NemoClaw docs
> (2026-07-13) but not yet exercised on OpenShell hardware. If you run it, tell us
> what breaks — the steps will be tightened from real runs.

## Verifying the connection

Ask the agent for `vault_info`. You should see your note count, sections, and
`"write_dir": "inbox"`. Then try a capture: the file must land in `inbox/` with
provenance frontmatter, and `.memexlab/log.jsonl` must gain a line. If an agent
ever claims it edited a canonical note, it didn't — there is no tool for that.
