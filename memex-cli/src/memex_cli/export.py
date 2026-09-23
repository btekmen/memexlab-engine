"""Export notes from the vault with mandatory grade classification.

Export creates a graded copy of a note outside canonical directories.
Human approval (via --grade) is required for every export operation.
"""
from __future__ import annotations

import datetime
import pathlib

import yaml

from .vault import Vault, parse_frontmatter

VALID_GRADES = {"private", "internal", "public"}
EXPORT_DIR = "exports"
CANONICAL_DIRS = {"wiki", "people", "companies", "concepts", "sources", "views"}


def export_note(
    vault: Vault,
    slug_or_path: str,
    grade: str | None = None,
    apply: bool = False,
    exported_by: str | None = None,
) -> dict:
    """Export a note with mandatory grade classification.
    
    Args:
        vault: The vault to export from
        slug_or_path: Note identifier (slug or relative path)
        grade: Required classification (private|internal|public)
        apply: Write the export (default: dry-run)
        exported_by: Optional identifier for who/what exported this
        
    Returns:
        Result dict with action, ok, applied, export_path, and grade
    """
    # Validate grade requirement
    if grade is None:
        return {
            "action": "missing-grade",
            "ok": False,
            "applied": False,
            "error": "export requires explicit --grade (private|internal|public)",
        }
    
    if grade not in VALID_GRADES:
        return {
            "action": "invalid-grade",
            "ok": False,
            "applied": False,
            "error": f"grade must be one of: {', '.join(sorted(VALID_GRADES))}",
            "provided": grade,
        }
    
    # Find the note
    try:
        # Try as relative path first
        note_data = vault.read(slug_or_path)
        note_path = pathlib.Path(note_data["path"])
    except FileNotFoundError:
        # Try to find by slug
        try:
            note_path = _find_by_slug(vault, slug_or_path)
            note_data = vault.read(note_path)
        except (FileNotFoundError, ValueError) as e:
            return {
                "action": "note-not-found",
                "ok": False,
                "applied": False,
                "error": str(e),
                "slug_or_path": slug_or_path,
            }
    
    # Generate export path
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d-%H%M%S")
    stem = note_path.stem
    export_rel = f"{EXPORT_DIR}/{stem}-{grade}-{timestamp}.md"
    export_full = vault.root / export_rel
    
    # Check canonical directory protection
    if note_path.parts[0] in CANONICAL_DIRS:
        canonical_warning = True
    else:
        canonical_warning = False
    
    # Build export content with metadata
    original_meta = note_data["frontmatter"]
    export_meta = {
        **original_meta,
        "export_grade": grade,
        "export_timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "export_source": str(note_path),
    }
    if exported_by:
        export_meta["exported_by"] = exported_by
    
    export_content = "---\n"
    export_content += yaml.dump(export_meta, allow_unicode=True, sort_keys=False)
    export_content += "---\n"
    export_content += note_data["body"]
    
    result = {
        "action": "export",
        "ok": True,
        "applied": apply,
        "grade": grade,
        "source_note": str(note_path),
        "export_path": export_rel,
        "canonical_source": canonical_warning,
        "chars": len(export_content),
    }
    
    if apply:
        # Write the export
        export_full.parent.mkdir(parents=True, exist_ok=True)
        export_full.write_text(export_content, encoding="utf-8")
    
    return result


def _find_by_slug(vault: Vault, slug: str) -> pathlib.Path:
    """Find a note by slug in the vault."""
    notes = vault.notes()
    candidates = []
    
    for note_path in notes:
        if note_path.stem == slug:
            candidates.append(note_path)
    
    if not candidates:
        raise FileNotFoundError(f"no note with slug: {slug}")
    
    if len(candidates) > 1:
        paths_str = ", ".join(str(p) for p in candidates)
        raise ValueError(f"ambiguous slug '{slug}' matches: {paths_str}")
    
    return candidates[0]
