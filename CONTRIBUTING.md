# Contributing to MemexLab Engine

Thanks for your interest in improving **MemexLab Engine** — the documentation, skills,
schemas, and reference agent for `memex`, a local-first, markdown-native knowledge vault.

This repo is an early preview (`0.2.0-harness-preview`). Contributions are welcome, and small
focused changes are the easiest to review and merge.

## Ways to contribute

- **Documentation** — fix errors, clarify explanations, improve the `docs/` pages.
- **Skills & schemas** — refine the Agent Skills in `skills/`, the entity schema in
  `schemas/`, or the eval material in `evals/`.
- **Examples** — improve the synthetic `examples/fake-vault/` or the `worked-example/` pass.
- **Reference agent** — improve `runner/` (the self-hosted reference loop).
- **Bug reports & ideas** — open an issue describing the problem or proposal.

## Ground rules

This is a public repository. Before you open a PR:

- **No private data.** Never add real names, company names, emails, phone numbers, API
  tokens, internal project names, or any personal/confidential content. All examples must use
  synthetic data (see `examples/fake-vault/`).
- **No secrets or local artifacts.** Do not commit `.env` files, keys, local databases,
  exports, PDFs, screenshots, or raw messages. `.gitignore` already excludes the common cases —
  double-check your diff.
- **Provider-agnostic.** Keep LLM integration isolated behind the single client. Deterministic
  modes (lint, chart, retrieval, migrate) must not require a model.

## Development workflow

1. **Fork** the repo and create a branch from `main`:
   ```bash
   git checkout -b my-change
   ```
2. **Make your change.** Keep it focused; one logical change per PR.
3. **Validate** any vault content you touched:
   ```bash
   python3 scripts/validate_vault.py examples/fake-vault
   ```
4. **Try the reference agent** (no API key required) if you changed `runner/` or `skills/`:
   ```bash
   python3 runner/agent.py --dry-run --vault examples/fake-vault
   ```
5. **Preview the docs** if you edited `docs/`:
   ```bash
   mkdocs serve
   ```
6. **Open a pull request** against `main` with a clear description of what and why.

## Commit and PR style

- Write clear, imperative commit messages (`docs: clarify retrieval flow`,
  `skills: fix memex-extract frontmatter`).
- Reference any related issue.
- Keep PRs reviewable — split unrelated changes.

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE) that covers this project.

## Attribution

MemexLab Engine builds on prior work — see [Lineage and Credits](docs/engineering/lineage.md),
crediting Andrej Karpathy's LLM Knowledge Bases / LLM Wiki and Garry Tan's GStack/GBrain.
