#!/usr/bin/env bash
# Lane A bootstrap: prepare any sandbox (NemoClaw/OpenShell, a plain container,
# or a bare directory) so an OpenClaw-class agent can operate a MemexLab vault.
#
# What it sets up under SANDBOX_ROOT (default /sandbox; override for testing):
#   vault/    — your vault (git clone from --vault-remote, or copy of --vault-path)
#   skills/   — this repo's Agent Skills (point your agent's skills path here)
#   venvs/memex + memexlab-mcp  — optional, with --with-mcp (Lane B add-on)
#
# Universal contract: DRY-RUN by default (prints the exact plan); --apply
# executes; one JSON event on stderr; exit 0/1. No network is touched except
# the git clone / pip install you explicitly asked for.
set -euo pipefail

SANDBOX_ROOT="/sandbox"
VAULT_REMOTE=""
VAULT_PATH=""
WITH_MCP=0
MCP_SOURCE="memexlab-mcp"   # PyPI name; or a local path/wheel for zero-egress installs
APPLY=0
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

usage() { grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0; }

while [ $# -gt 0 ]; do
  case "$1" in
    --sandbox-root) SANDBOX_ROOT="$2"; shift 2 ;;
    --vault-remote) VAULT_REMOTE="$2"; shift 2 ;;
    --vault-path)   VAULT_PATH="$2"; shift 2 ;;
    --with-mcp)     WITH_MCP=1; shift ;;
    --mcp-source)   MCP_SOURCE="$2"; shift 2 ;;
    --apply)        APPLY=1; shift ;;
    -h|--help)      usage ;;
    *) echo "error: unknown flag $1" >&2; exit 1 ;;
  esac
done

if [ -n "$VAULT_REMOTE" ] && [ -n "$VAULT_PATH" ]; then
  echo "error: use --vault-remote OR --vault-path, not both" >&2; exit 1
fi
if [ -z "$VAULT_REMOTE" ] && [ -z "$VAULT_PATH" ]; then
  echo "error: one of --vault-remote <git-url> or --vault-path <dir> is required" >&2; exit 1
fi
if [ -n "$VAULT_PATH" ] && [ ! -d "$VAULT_PATH" ]; then
  echo "error: --vault-path is not a directory: $VAULT_PATH" >&2; exit 1
fi

VAULT_DEST="$SANDBOX_ROOT/vault"
SKILLS_DEST="$SANDBOX_ROOT/skills"
VENV="$SANDBOX_ROOT/venvs/memex"

PLAN=()
if [ -d "$VAULT_DEST" ]; then
  PLAN+=("vault: keep existing $VAULT_DEST (not touched — pull/push it yourself)")
elif [ -n "$VAULT_REMOTE" ]; then
  PLAN+=("vault: git clone $VAULT_REMOTE -> $VAULT_DEST  (needs one-time egress to the git host; on NemoClaw: policy-add first, dry-run then --yes)")
else
  PLAN+=("vault: copy $VAULT_PATH -> $VAULT_DEST")
fi
PLAN+=("skills: copy $REPO_DIR/skills/ -> $SKILLS_DEST  (point your agent's skills path here)")
if [ "$WITH_MCP" = "1" ]; then
  PLAN+=("mcp: python3 -m venv $VENV && $VENV/bin/pip install $MCP_SOURCE  (use a local path/wheel for zero egress)")
  PLAN+=("mcp: register stdio server in the AGENT'S OWN config: command=$VENV/bin/memexlab-mcp args=--vault $VAULT_DEST  (NemoClaw's managed 'mcp add' is HTTPS-only — don't use it for stdio)")
fi
PLAN+=("verify: ask the agent for vault_info / run the first skill; writes must land only in $VAULT_DEST/inbox/")

if [ "$APPLY" = "0" ]; then
  echo "dry-run: would do the following (use --apply to execute):"
  for step in "${PLAN[@]}"; do echo "  - $step"; done
  printf '{"cmd":"setup_agent_sandbox","mode":"dry-run","steps":%d,"ok":true}\n' "${#PLAN[@]}" >&2
  exit 0
fi

mkdir -p "$SANDBOX_ROOT"
if [ ! -d "$VAULT_DEST" ]; then
  if [ -n "$VAULT_REMOTE" ]; then
    git clone --quiet "$VAULT_REMOTE" "$VAULT_DEST"
  else
    cp -R "$VAULT_PATH" "$VAULT_DEST"
  fi
fi
mkdir -p "$SKILLS_DEST"
cp -R "$REPO_DIR/skills/." "$SKILLS_DEST/"
if [ "$WITH_MCP" = "1" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --disable-pip-version-check "$MCP_SOURCE"
fi

echo "done:"
echo "  vault:  $VAULT_DEST"
echo "  skills: $SKILLS_DEST  (agent skills installed: $(ls "$SKILLS_DEST" | wc -l | tr -d ' ') entries)"
if [ "$WITH_MCP" = "1" ]; then
  echo "  mcp:    $VENV/bin/memexlab-mcp --vault $VAULT_DEST  (add to the agent's MCP config)"
fi
echo "next: point the agent's skills path at $SKILLS_DEST and verify with vault_info."
printf '{"cmd":"setup_agent_sandbox","mode":"apply","vault":"%s","skills":"%s","mcp":%s,"ok":true}\n' \
  "$VAULT_DEST" "$SKILLS_DEST" "$([ "$WITH_MCP" = 1 ] && echo true || echo false)" >&2
