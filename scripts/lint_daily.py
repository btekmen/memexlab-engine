#!/usr/bin/env python3
"""
scripts/lint_daily.py — cron-friendly daily vault linter

Walks a vault's markdown notes, produces a dated lint report under _lint/,
and logs structured events to .memex/log.jsonl on failure.

Usage:
  python scripts/lint_daily.py --vault PATH [--date YYYY-MM-DD] [--dry-run]
  VAULT_PATH=/path/to/vault python scripts/lint_daily.py
"""

import argparse
import json
import os
import pathlib
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    yaml = None


class LintFinding:
    """A single lint finding with severity, file path, and description."""

    def __init__(self, severity: str, path: pathlib.Path, description: str):
        self.severity = severity  # "error" or "warning"
        self.path = path
        self.description = description

    def __repr__(self):
        return f"{self.severity.upper()}: {self.path}: {self.description}"


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Daily vault linter - produces _lint/lint-YYYY-MM-DD.md"
    )
    parser.add_argument(
        "--vault",
        type=str,
        default=os.environ.get("VAULT_PATH"),
        help="Path to vault (required, or set VAULT_PATH env var)",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        help="Date for report filename (default: today UTC)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print report path and exit without writing",
    )
    parser.add_argument(
        "--max-findings",
        type=int,
        default=50,
        help="Maximum findings to list in report (default: 50, 0 = unlimited)",
    )
    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="List only errors in report (warnings still counted)",
    )
    parser.add_argument(
        "--scope",
        type=str,
        default="vault",
        choices=["vault", "wiki"],
        help="Scope: 'vault' (all) or 'wiki' (skip people/, companies/, books/)",
    )
    args = parser.parse_args()

    if not args.vault:
        parser.error("--vault is required (or set VAULT_PATH environment variable)")

    return args


def log_event(vault_path: pathlib.Path, event_name: str, details: dict):
    """Append a structured JSON event to .memex/log.jsonl."""
    try:
        log_dir = vault_path / ".memex"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "log.jsonl"

        event = {
            "event": event_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "error",
            **details,
        }

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        # If we can't even log, write to stderr and give up
        print(f"FATAL: Could not write to log.jsonl: {e}", file=sys.stderr)


def extract_frontmatter(content: str) -> tuple[dict, bool]:
    """
    Extract YAML frontmatter from markdown content.

    Returns:
        (frontmatter_dict, is_valid)
    """
    if not content.startswith("---\n"):
        return {}, False

    try:
        parts = content.split("---\n", 2)
        if len(parts) < 3:
            return {}, False

        if yaml is None:
            # Minimal fallback parser if PyYAML not available
            fm = {}
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    fm[key.strip()] = val.strip()
            return fm, True

        fm = yaml.safe_load(parts[1])
        return fm if isinstance(fm, dict) else {}, True

    except Exception:
        return {}, False


def find_wikilinks(content: str) -> list[str]:
    """Extract all [[wikilink]] targets from markdown content."""
    pattern = r"\[\[([^\]]+)\]\]"
    return re.findall(pattern, content)


def resolve_wikilink_target(
    link: str, vault_path: pathlib.Path, all_notes: set[pathlib.Path]
) -> bool:
    """
    Check if a wikilink target resolves to an existing note.

    Wikilinks can be:
    - [[path/name]] → looks for path/name.md
    - [[name]] → looks for name.md anywhere in vault
    """
    # Normalize link (remove any .md extension if present)
    link = link.strip()
    if link.endswith(".md"):
        link = link[:-3]

    # Try direct path resolution
    candidate = vault_path / f"{link}.md"
    if candidate in all_notes:
        return True

    # Try finding by slug (basename) anywhere in vault
    slug = pathlib.Path(link).name
    for note_path in all_notes:
        if note_path.stem == slug:
            return True

    return False


def count_inbound_links(
    note_path: pathlib.Path, vault_path: pathlib.Path, all_notes_content: dict
) -> int:
    """Count how many other notes link to this note."""
    # Get relative path and possible link targets
    rel_path = note_path.relative_to(vault_path)
    slug = note_path.stem

    inbound_count = 0
    for other_path, content in all_notes_content.items():
        if other_path == note_path:
            continue

        links = find_wikilinks(content)
        for link in links:
            link_slug = pathlib.Path(link.strip().replace(".md", "")).name
            if link_slug == slug or link.strip().replace(".md", "") == str(
                rel_path.with_suffix("")
            ):
                inbound_count += 1

    return inbound_count


def lint_vault(vault_path: pathlib.Path, scope: str = "vault") -> list[LintFinding]:
    """
    Perform lint checks on the vault.

    Args:
        vault_path: Path to the vault
        scope: 'vault' (all notes) or 'wiki' (skip people/, companies/, books/)

    Returns list of findings.
    """
    findings = []

    # Collect all markdown notes (excluding .memex and raw/ directories)
    all_notes = set()
    all_notes_content = {}

    # Directories to skip based on scope
    skip_dirs = {"raw"}  # Always skip raw/
    if scope == "wiki":
        skip_dirs.update({"people", "companies", "books"})

    for md_file in vault_path.rglob("*.md"):
        # Skip .memex and configured skip directories
        rel_path = md_file.relative_to(vault_path)
        if any(part.startswith(".") for part in rel_path.parts):
            continue
        if rel_path.parts and rel_path.parts[0] in skip_dirs:
            continue

        all_notes.add(md_file)

        try:
            content = md_file.read_text(encoding="utf-8")
            all_notes_content[md_file] = content
        except Exception as e:
            findings.append(
                LintFinding("error", md_file, f"Could not read file: {e}")
            )

    # Lint each note
    for note_path in all_notes:
        content = all_notes_content.get(note_path, "")

        # Check 1: Frontmatter validation
        frontmatter, fm_valid = extract_frontmatter(content)

        if not content.startswith("---\n"):
            findings.append(LintFinding("error", note_path, "Missing YAML frontmatter"))
            continue

        if not fm_valid:
            findings.append(
                LintFinding("error", note_path, "Malformed YAML frontmatter")
            )
            continue

        # Check 2: Required frontmatter fields
        required_fields = ["type", "title", "status"]
        for field in required_fields:
            if field not in frontmatter:
                findings.append(
                    LintFinding("error", note_path, f"Missing required field: {field}")
                )

        # Check 3: Broken wikilink targets
        wikilinks = find_wikilinks(content)
        for link in wikilinks:
            if not resolve_wikilink_target(link, vault_path, all_notes):
                findings.append(
                    LintFinding("error", note_path, f"Broken wikilink: [[{link}]]")
                )

        # Check 4: Orphan atomic notes under wiki/
        rel_path = note_path.relative_to(vault_path)
        if (
            rel_path.parts[0] == "wiki"
            and frontmatter.get("type") in ["concept", "atomic"]
        ):
            inbound_count = count_inbound_links(
                note_path, vault_path, all_notes_content
            )
            if inbound_count == 0:
                findings.append(
                    LintFinding(
                        "warning",
                        note_path,
                        "Orphan atomic note (zero inbound wikilinks)",
                    )
                )

    return findings


def format_report(
    scan_time: datetime,
    findings: list[LintFinding],
    scanned_count: int,
    max_findings: int = 50,
    errors_only: bool = False,
) -> str:
    """
    Format lint findings into a markdown report.

    Args:
        scan_time: When the scan was performed
        findings: List of all findings
        scanned_count: Total notes scanned
        max_findings: Maximum findings to list (0 = unlimited)
        errors_only: If True, only list errors (warnings still counted)
    """
    error_count = sum(1 for f in findings if f.severity == "error")
    warning_count = sum(1 for f in findings if f.severity == "warning")

    report = f"""---
type: lint-report
title: Daily Lint Report
generated: {scan_time.isoformat()}
---

# Daily Lint Report

**Scan time:** {scan_time.strftime("%Y-%m-%d %H:%M:%S UTC")}

**Summary:**
- Scanned: {scanned_count} notes
- Errors: {error_count}
- Warnings: {warning_count}

"""

    if not findings:
        report += "✓ No issues found.\n"
        return report

    # Group findings by severity
    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]

    # Determine how many to show
    unlimited = max_findings == 0
    remaining_budget = max_findings if not unlimited else float("inf")

    if errors:
        report += "## Errors\n\n"
        report += "| File | Issue |\n"
        report += "|------|-------|\n"

        errors_to_show = errors if unlimited else errors[:remaining_budget]
        for finding in errors_to_show:
            report += f"| `{finding.path.name}` | {finding.description} |\n"

        omitted_errors = len(errors) - len(errors_to_show)
        if omitted_errors > 0:
            report += f"\n*… and {omitted_errors} more errors (omitted)*\n"

        report += "\n"
        remaining_budget -= len(errors_to_show)

    if warnings and not errors_only:
        report += "## Warnings\n\n"
        report += "| File | Issue |\n"
        report += "|------|-------|\n"

        warnings_to_show = (
            warnings if unlimited else warnings[: int(remaining_budget)]
        )
        for finding in warnings_to_show:
            report += f"| `{finding.path.name}` | {finding.description} |\n"

        omitted_warnings = len(warnings) - len(warnings_to_show)
        if omitted_warnings > 0:
            report += f"\n*… and {omitted_warnings} more warnings (omitted)*\n"

        report += "\n"
    elif warnings and errors_only:
        report += f"*{warning_count} warnings omitted (--errors-only)*\n\n"

    return report


def main():
    """Main entry point."""
    try:
        args = parse_args()
        vault_path = pathlib.Path(args.vault).resolve()

        # Validate vault exists
        if not vault_path.exists():
            log_event(
                vault_path,
                "lint_daily_vault_error",
                {"reason": "vault path does not exist", "path": str(vault_path)},
            )
            print(f"ERROR: Vault path does not exist: {vault_path}", file=sys.stderr)
            return 1

        if not vault_path.is_dir():
            log_event(
                vault_path,
                "lint_daily_vault_error",
                {"reason": "vault path is not a directory", "path": str(vault_path)},
            )
            print(
                f"ERROR: Vault path is not a directory: {vault_path}", file=sys.stderr
            )
            return 1

        # Determine report path
        report_dir = vault_path / "_lint"
        report_path = report_dir / f"lint-{args.date}.md"

        if args.dry_run:
            print(f"DRY RUN: Would write report to {report_path}")
            return 0

        # Perform lint
        scan_time = datetime.now(timezone.utc)
        findings = lint_vault(vault_path, scope=args.scope)

        # Count scanned notes (respecting scope)
        skip_dirs = {"raw"}
        if args.scope == "wiki":
            skip_dirs.update({"people", "companies", "books"})

        scanned_count = sum(
            1
            for md_file in vault_path.rglob("*.md")
            if not any(part.startswith(".") for part in md_file.relative_to(vault_path).parts)
            and (
                not md_file.relative_to(vault_path).parts
                or md_file.relative_to(vault_path).parts[0] not in skip_dirs
            )
        )

        # Generate report
        report_content = format_report(
            scan_time,
            findings,
            scanned_count,
            max_findings=args.max_findings,
            errors_only=args.errors_only,
        )

        # Write report
        try:
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report_content, encoding="utf-8")
            print(f"✓ Lint report written to {report_path}")
        except Exception as e:
            log_event(
                vault_path,
                "lint_daily_vault_error",
                {"reason": "could not write report", "error": str(e)},
            )
            print(f"ERROR: Could not write report: {e}", file=sys.stderr)
            return 1

        # Exit 0 even if findings exist (findings are the report, not a failure)
        return 0

    except Exception as e:
        # Unexpected crash
        if "vault_path" in locals():
            log_event(
                vault_path,
                "lint_daily_lint_error",
                {"reason": "unexpected error", "error": str(e)},
            )
        print(f"FATAL: Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
