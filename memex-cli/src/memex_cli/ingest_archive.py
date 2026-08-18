"""`memex ingest archive` — local-first import from official data exports.

Connect-in path for official data-export archives: no OAuth, no network scrape,
no personal vault paths. Drop an export file/folder and land notes in inbox/
with provenance. Supports:

1. LinkedIn official data archive (connections CSV from zip or extracted folder)
2. Matter official export (JSON as shipped)
3. Books bundle (simple CSV: title, author, shelf/status)

Invariants:
- Dry-run default; `--apply` to write.
- Writes ONLY to inbox/ with provenance frontmatter.
- Never writes wiki/, people/, companies/, or other canonical paths.
- One export row/item → one inbox note or clearly batched inbox note.
- Tests on synthetic fixtures only.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import json
import pathlib
import re
import zipfile

import yaml

from .state import IngestState
from .vault import Vault


def _slugify(text: str) -> str:
    """Convert text to a safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")
    return slug[:80].rstrip("-") or "item"


def _item_hash(kind: str, *parts: str) -> str:
    """Generate a stable hash for deduplication."""
    joined_parts = "\x00".join(parts)
    return hashlib.sha256(f"{kind}\x00{joined_parts}".encode("utf-8")).hexdigest()[:16]


def _parse_linkedin_connections_csv(data: str) -> list[dict]:
    """Parse LinkedIn Connections.csv → [{first_name, last_name, company, position, email, connected_on}]."""
    lines = [line for line in data.split("\n") if line.strip()]
    if not lines:
        return []
    
    reader = csv.DictReader(lines)
    connections = []
    for row in reader:
        # LinkedIn connections CSV format (actual structure from real exports)
        # May have: "First Name", "Last Name", "Email Address", "Company", "Position", "Connected On"
        # Handle variations gracefully
        first_name = row.get("First Name", "").strip()
        last_name = row.get("Last Name", "").strip()
        email = row.get("Email Address", "").strip()
        company = row.get("Company", "").strip()
        position = row.get("Position", "").strip()
        connected_on = row.get("Connected On", "").strip()
        
        # Skip rows with no meaningful data
        if not first_name and not last_name and not email:
            continue
            
        connections.append({
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "company": company,
            "position": position,
            "connected_on": connected_on,
        })
    return connections


def _parse_matter_export(data: str) -> list[dict]:
    """Parse Matter export JSON → [{title, url, author, content, saved_at}]."""
    try:
        obj = json.loads(data)
    except json.JSONDecodeError:
        return []
    
    # Matter exports are typically a JSON array of saved articles
    if isinstance(obj, list):
        items = obj
    elif isinstance(obj, dict) and "items" in obj:
        items = obj["items"]
    else:
        return []
    
    articles = []
    for item in items:
        if not isinstance(item, dict):
            continue
        
        title = item.get("title", "").strip()
        url = item.get("url", "").strip()
        author = item.get("author", "").strip()
        content = item.get("content", "").strip()
        saved_at = item.get("saved_at", "").strip()
        
        # Skip items with no meaningful data
        if not title and not url:
            continue
        
        articles.append({
            "title": title or url,
            "url": url,
            "author": author,
            "content": content,
            "saved_at": saved_at,
        })
    return articles


def _parse_books_csv(data: str) -> list[dict]:
    """Parse books CSV → [{title, author, shelf}]."""
    lines = [line for line in data.split("\n") if line.strip()]
    if not lines:
        return []
    
    reader = csv.DictReader(lines)
    books = []
    for row in reader:
        # Flexible format: title, author, shelf/status/tags
        # Handle common column name variations
        title = (row.get("title") or row.get("Title") or "").strip()
        author = (row.get("author") or row.get("Author") or "").strip()
        shelf = (row.get("shelf") or row.get("Shelf") or 
                row.get("status") or row.get("Status") or "").strip()
        
        # Skip rows with no title
        if not title:
            continue
        
        books.append({
            "title": title,
            "author": author,
            "shelf": shelf,
        })
    return books


def _render_linkedin_note(connection: dict, now: datetime.datetime) -> str:
    """Generate a markdown note for a LinkedIn connection."""
    full_name = " ".join(p for p in [connection["first_name"], connection["last_name"]] if p)
    title = full_name or "Connection"
    
    frontmatter = {
        "title": title,
        "status": "inbox",
        "captured_via": "linkedin-archive",
        "captured_at": now.isoformat(),
    }
    if connection["email"]:
        frontmatter["contact_email"] = connection["email"]
    if connection["company"]:
        frontmatter["source_company"] = connection["company"]
    if connection["connected_on"]:
        frontmatter["connected_on"] = connection["connected_on"]
    
    body = f"# {title}\n\n"
    if connection["position"]:
        body += f"**Position:** {connection['position']}\n\n"
    if connection["company"]:
        body += f"**Company:** {connection['company']}\n\n"
    if connection["email"]:
        body += f"**Email:** {connection['email']}\n\n"
    if connection["connected_on"]:
        body += f"**Connected:** {connection['connected_on']}\n\n"
    
    body += "## Notes\n\n"
    
    return "---\n" + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True) + "---\n\n" + body


def _render_matter_note(article: dict, now: datetime.datetime) -> str:
    """Generate a markdown note for a Matter article."""
    frontmatter = {
        "title": article["title"],
        "status": "inbox",
        "captured_via": "matter-export",
        "captured_at": now.isoformat(),
    }
    if article["url"]:
        frontmatter["source_url"] = article["url"]
    if article["author"]:
        frontmatter["source_author"] = article["author"]
    if article["saved_at"]:
        frontmatter["saved_at"] = article["saved_at"]
    
    body = f"# {article['title']}\n\n"
    if article["author"]:
        body += f"**Author:** {article['author']}\n\n"
    if article["url"]:
        body += f"**URL:** {article['url']}\n\n"
    if article["content"]:
        body += f"## Content\n\n{article['content']}\n\n"
    else:
        body += "## Notes\n\n"
    
    return "---\n" + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True) + "---\n\n" + body


def _render_book_note(book: dict, now: datetime.datetime) -> str:
    """Generate a markdown note for a book."""
    frontmatter = {
        "title": book["title"],
        "status": "inbox",
        "captured_via": "books-archive",
        "captured_at": now.isoformat(),
    }
    if book["author"]:
        frontmatter["source_author"] = book["author"]
    if book["shelf"]:
        frontmatter["shelf"] = book["shelf"]
    
    body = f"# {book['title']}\n\n"
    if book["author"]:
        body += f"**Author:** {book['author']}\n\n"
    if book["shelf"]:
        body += f"**Shelf:** {book['shelf']}\n\n"
    body += "## Notes\n\n"
    
    return "---\n" + yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True) + "---\n\n" + body


def _read_from_path(path: pathlib.Path, kind: str) -> str:
    """Read data from file or zip archive. Returns content as string."""
    # Check if it's a zip file
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as zf:
            # Look for expected file based on kind
            if kind == "linkedin":
                # LinkedIn exports typically have Connections.csv
                for name in zf.namelist():
                    if "connection" in name.lower() and name.endswith(".csv"):
                        return zf.read(name).decode("utf-8", errors="replace")
                raise ValueError(f"No Connections.csv found in LinkedIn archive: {path}")
            elif kind == "matter":
                # Matter exports might be articles.json or similar
                for name in zf.namelist():
                    if name.endswith(".json"):
                        return zf.read(name).decode("utf-8", errors="replace")
                raise ValueError(f"No JSON file found in Matter archive: {path}")
            else:
                raise ValueError(f"Archive format not supported for kind: {kind}")
    
    # Check if it's a directory (extracted archive)
    if path.is_dir():
        if kind == "linkedin":
            # Look for Connections.csv in the directory
            for csv_file in path.rglob("*.csv"):
                if "connection" in csv_file.name.lower():
                    return csv_file.read_text(encoding="utf-8", errors="replace")
            raise ValueError(f"No Connections.csv found in directory: {path}")
        elif kind == "matter":
            # Look for JSON files
            for json_file in path.rglob("*.json"):
                return json_file.read_text(encoding="utf-8", errors="replace")
            raise ValueError(f"No JSON file found in directory: {path}")
        else:
            raise ValueError(f"Directory format not supported for kind: {kind}")
    
    # Regular file
    return path.read_text(encoding="utf-8", errors="replace")


def ingest_archive(
    vault: Vault,
    archive_path: str,
    kind: str,
    apply: bool = False,
) -> dict:
    """Import from official data export archives.
    
    Args:
        vault: Vault instance
        archive_path: Path to archive file, directory, or CSV
        kind: "linkedin", "matter", or "books"
        apply: Write notes if True, otherwise dry-run
    
    Returns:
        Result dict with action, plan, applied, ok
    """
    path = pathlib.Path(archive_path)
    if not path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    
    # Read and parse based on kind
    if kind == "linkedin":
        data = _read_from_path(path, kind)
        items = _parse_linkedin_connections_csv(data)
        renderer = _render_linkedin_note
        item_type = "connection"
    elif kind == "matter":
        data = _read_from_path(path, kind)
        items = _parse_matter_export(data)
        renderer = _render_matter_note
        item_type = "article"
    elif kind == "books":
        data = path.read_text(encoding="utf-8", errors="replace")
        items = _parse_books_csv(data)
        renderer = _render_book_note
        item_type = "book"
    else:
        raise ValueError(f"Unknown archive kind: {kind} (must be linkedin, matter, or books)")
    
    # Track what we've already imported
    state = IngestState(vault.root)
    archive_key = f"archive_{kind}"
    state.data.setdefault(archive_key, {"items": []})
    known_hashes = set(state.data[archive_key]["items"])
    
    now = datetime.datetime.now(datetime.timezone.utc)
    target_dir = vault.write_target()
    plan = []
    new_count = 0
    known_count = 0
    
    for item in items:
        # Generate hash for deduplication
        if kind == "linkedin":
            item_hash = _item_hash("linkedin", item["first_name"], item["last_name"], item["email"])
        elif kind == "matter":
            item_hash = _item_hash("matter", item["url"] or item["title"])
        else:  # books
            item_hash = _item_hash("books", item["title"], item["author"])
        
        if item_hash in known_hashes:
            known_count += 1
            continue
        
        # Generate note filename
        if kind == "linkedin":
            slug = _slugify(" ".join(p for p in [item["first_name"], item["last_name"]] if p) or "connection")
        elif kind == "matter":
            slug = _slugify(item["title"])
        else:  # books
            slug = _slugify(item["title"])
        
        note_rel = str(pathlib.Path(vault.write_dir()) / f"{slug}-{now.strftime('%Y%m%dT%H%M%SZ')}.md")
        
        # Generate display name for plan
        if kind == "linkedin":
            display = " ".join(p for p in [item["first_name"], item["last_name"]] if p) or "Connection"
        elif kind == "matter":
            display = item["title"]
        else:  # books
            display = item["title"]
        
        plan.append({"item": display, "note": note_rel, "type": item_type})
        new_count += 1
        
        if not apply:
            continue
        
        # Write the note
        full = vault.root / note_rel
        if full.resolve().parent != target_dir:
            raise PermissionError(f"write escapes boundary: {note_rel}")
        
        target_dir.mkdir(parents=True, exist_ok=True)
        content = renderer(item, now)
        full.write_text(content, encoding="utf-8")
        
        # Track this item as imported
        known_hashes.add(item_hash)
        state.data[archive_key]["items"].append(item_hash)
    
    # Update log if it exists
    if apply and new_count > 0:
        log_path = vault.root / ".memexlab" / "log.jsonl"
        if log_path.parent.exists():
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as f:
                log_entry = {
                    "timestamp": now.isoformat(),
                    "action": f"ingest-archive-{kind}",
                    "items": new_count,
                    "source": str(archive_path),
                }
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        state.save()
    
    return {
        "action": f"ingest-archive-{kind}",
        "source": str(archive_path),
        "items_parsed": len(items),
        "new_items": new_count,
        "known_skipped": known_count,
        "plan": plan,
        "applied": apply,
        "ok": True,
    }
