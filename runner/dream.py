#!/usr/bin/env python3
"""Dream loop — governed maintenance proposal without touching canonical notes.

Reads inbox + a sample of canonical notes, proposes maintenance tasks as queue items
or inbox notes with provenance and [[slug]] citations. Never writes wiki/people/companies.

Human applies proposals via complete_queue_item() or --apply flag.

Usage:
    python3 runner/dream.py --vault examples/fake-vault --dry-run
    python3 runner/dream.py --vault examples/fake-vault --apply  # write queue items
"""
import argparse
import datetime
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "memexlab-mcp" / "src"))

from memexlab_mcp.vault import Vault  # noqa: E402
from memexlab_mcp.governance import write_dir  # noqa: E402
import yaml  # noqa: E402

WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
CANONICAL_DIRS = {"people", "companies", "wiki", "concepts"}
INBOX_SAMPLE_LIMIT = 10
CANONICAL_SAMPLE_LIMIT = 15


def find_wikilinks(text: str) -> set[str]:
    """Extract [[slug]] references from text."""
    return {m.group(1).split("|")[0].split("#")[0].strip() for m in WIKILINK.finditer(text)}


def load_note(vault: Vault, rel_path: pathlib.Path) -> dict | None:
    """Load a note with frontmatter and body."""
    try:
        return vault.read(str(rel_path))
    except Exception:
        return None


def find_maintenance_opportunities(vault: Vault) -> list[dict]:
    """Scan vault and propose maintenance tasks.
    
    Returns list of {type, title, body, sources} dicts suitable for queue items.
    """
    opportunities = []
    all_notes = vault.notes()
    slug_to_path = {p.stem: p for p in all_notes}
    # Also map full paths (without .md) for path-based links
    path_to_note = {str(p.with_suffix('')): p for p in all_notes}
    
    # Sample inbox notes
    inbox_dir = write_dir(vault.root)
    inbox_notes = [p for p in all_notes if p.parts[0] == inbox_dir][:INBOX_SAMPLE_LIMIT]
    
    # Sample canonical notes (avoid queue, views, sources)
    canonical = [p for p in all_notes 
                 if p.parts[0] in CANONICAL_DIRS][:CANONICAL_SAMPLE_LIMIT]
    
    # Check for broken wikilinks
    for rel_path in inbox_notes + canonical:
        note = load_note(vault, rel_path)
        if not note:
            continue
        
        links = find_wikilinks(note.get("body", ""))
        for link in links:
            # Check both slug-only and path-based links
            if link not in slug_to_path and link not in path_to_note:
                opportunities.append({
                    "type": "broken-link",
                    "title": f"Broken link [[{link}]] in {rel_path.stem}",
                    "body": f"Note [[{rel_path.stem}]] references [[{link}]], which does not exist.\n\n"
                            f"**Evidence**: [[{rel_path.stem}]]\n\n"
                            f"**Proposed action**: Create the missing note, update the link, or remove it.",
                    "sources": [rel_path.stem],
                    "priority": "low",
                })
    
    # Check for missing backlinks in canonical notes
    for rel_path in canonical:
        slug = rel_path.stem
        # Find notes that reference this one
        referrers = []
        for other in all_notes:
            if other == rel_path:
                continue
            other_note = load_note(vault, other)
            if other_note and slug in find_wikilinks(other_note.get("body", "")):
                referrers.append(other.stem)
        
        if referrers:
            note = load_note(vault, rel_path)
            if note:
                body_text = note.get("body", "")
                backlinks_present = sum(1 for ref in referrers if f"[[{ref}]]" in body_text)
                if backlinks_present < len(referrers):
                    missing = [r for r in referrers if f"[[{r}]]" not in body_text]
                    opportunities.append({
                        "type": "missing-backlink",
                        "title": f"Missing backlinks in [[{slug}]]",
                        "body": f"Note [[{slug}]] is referenced by {len(referrers)} note(s) "
                                f"but only cites {backlinks_present} of them.\n\n"
                                f"**Missing backlinks**: {', '.join(f'[[{m}]]' for m in missing[:5])}\n\n"
                                f"**Evidence**: [[{slug}]]\n\n"
                                f"**Proposed action**: Add backlink citations to maintain bidirectional references.",
                        "sources": [slug] + missing[:3],
                        "priority": "medium",
                    })
    
    # Check for orphaned inbox notes (old items with no references)
    for rel_path in inbox_notes:
        slug = rel_path.stem
        note = load_note(vault, rel_path)
        if not note:
            continue
        
        # Check if any canonical note references this inbox item
        referenced = False
        for canon in canonical:
            canon_note = load_note(vault, canon)
            if canon_note and slug in find_wikilinks(canon_note.get("body", "")):
                referenced = True
                break
        
        if not referenced:
            opportunities.append({
                "type": "orphaned-inbox",
                "title": f"Orphaned inbox note [[{slug}]]",
                "body": f"Inbox note [[{slug}]] is not referenced by any canonical notes.\n\n"
                        f"**Evidence**: [[{slug}]]\n\n"
                        f"**Proposed action**: Integrate into canonical notes or archive.",
                "sources": [slug],
                "priority": "low",
            })
    
    return opportunities


def format_as_queue_item(opp: dict, agent: str = "dream-loop") -> str:
    """Format a maintenance opportunity as a queue item."""
    now = datetime.datetime.now(datetime.timezone.utc)
    frontmatter = {
        "type": "queue-item",
        "title": opp["title"],
        "status": "pending",
        "destination": "any-agent",
        "created": now.date().isoformat(),
        "tags": ["maintenance", opp["type"], "dream-generated"],
        "priority": opp.get("priority", "low"),
        "generated_by": agent,
    }
    return "---\n" + yaml.safe_dump(frontmatter, sort_keys=False) + "---\n\n" + opp["body"] + "\n"


def write_queue_items(vault: Vault, opportunities: list[dict], agent: str = "dream-loop") -> list[str]:
    """Write maintenance opportunities as queue items. Returns list of created paths."""
    queue_path = vault.root / "queue"
    queue_path.mkdir(parents=True, exist_ok=True)
    
    created = []
    for opp in opportunities:
        slug = re.sub(r"[^a-z0-9]+", "-", opp["title"].casefold()).strip("-")[:60]
        now = datetime.datetime.now(datetime.timezone.utc)
        stamp = now.strftime("%Y%m%d-%H%M%S")
        filename = f"{slug}-{stamp}.md"
        
        target = queue_path / filename
        if target.exists():
            continue  # Skip duplicates
        
        content = format_as_queue_item(opp, agent)
        target.write_text(content, encoding="utf-8")
        created.append(f"queue/{filename}")
    
    return created


def dry_run(vault: Vault, opportunities: list[dict]) -> None:
    """Display what would be written without making changes."""
    print(f"Dream loop — dry run (vault: {vault.root})\n")
    print(f"Found {len(opportunities)} maintenance opportunities:\n")
    
    if not opportunities:
        print("✓ No maintenance needed — vault looks healthy!\n")
        return
    
    for i, opp in enumerate(opportunities, 1):
        print(f"{i}. [{opp['type']}] {opp['title']}")
        print(f"   Priority: {opp.get('priority', 'low')}")
        sources_str = ', '.join(f"[[{s}]]" for s in opp['sources'][:3])
        print(f"   Sources: {sources_str}")
        if i < len(opportunities):
            print()
    
    print(f"\nTo write these as queue items: drop --dry-run or add --apply")


def main():
    ap = argparse.ArgumentParser(description="Dream loop — governed vault maintenance")
    ap.add_argument("--vault", default="examples/fake-vault", 
                    help="path to the markdown vault")
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="preview maintenance opportunities without writing (default)")
    ap.add_argument("--apply", action="store_true",
                    help="write maintenance proposals as queue items")
    ap.add_argument("--agent", default="dream-loop",
                    help="agent name for provenance (default: dream-loop)")
    args = ap.parse_args()
    
    vault_path = args.vault if os.path.isabs(args.vault) else ROOT / args.vault
    try:
        vault = Vault(vault_path)
    except ValueError as e:
        sys.exit(f"error: {e}")
    
    opportunities = find_maintenance_opportunities(vault)
    
    if args.apply:
        args.dry_run = False
    
    if args.dry_run:
        dry_run(vault, opportunities)
    else:
        created = write_queue_items(vault, opportunities, args.agent)
        print(f"Dream loop — applied {len(created)} maintenance proposals")
        for path in created:
            print(f"  ✓ {path}")
        print(f"\nApply with: complete_queue_item(<item>, <result_title>, <result_body>)")


if __name__ == "__main__":
    main()
