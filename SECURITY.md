# Security Policy

## Supported versions

MemexLab Engine is an early preview (`0.2.0-harness-preview`). Only the latest `main` is
supported. There are no backported security fixes for older tags.

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Report vulnerabilities privately using
[GitHub's private vulnerability reporting](https://github.com/btekmen/memexlab-engine/security/advisories/new)
(the **Security → Report a vulnerability** tab on this repository).

When reporting, please include:

- A description of the issue and its potential impact.
- Steps to reproduce, or a proof of concept.
- Affected files, commands, or configuration.
- Any suggested remediation, if you have one.

## What to expect

- **Acknowledgement** within a few days of your report.
- An initial assessment and, where confirmed, a remediation plan.
- Coordinated disclosure — we will agree on timing with you before any public write-up, and
  credit you unless you prefer to remain anonymous.

## Scope

This repository ships documentation, Agent Skills, schemas, a synthetic example vault, and a
self-hosted **reference agent** (`runner/`). Relevant concerns include, but are not limited to:

- Handling of API keys and provider credentials (the engine is provider-agnostic; keys are
  supplied via environment variables such as `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` and must
  never be committed).
- Path traversal, code execution, or injection when the reference agent or validation scripts
  process untrusted vault content.
- Accidental inclusion of private data (real names, emails, tokens, exports) in the repo.

## Handling secrets

The engine reads credentials from environment variables only. Never commit `.env` files,
`*.key`, `*.pem`, or any secret — `.gitignore` excludes the common cases. If you discover a
committed secret, report it privately as above so it can be rotated and purged from history.
