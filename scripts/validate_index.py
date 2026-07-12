#!/usr/bin/env python3
import json, pathlib, sys

REQUIRED = ["id", "title", "path", "source_files", "tags", "ingested_at"]
LIST_FIELDS = ["source_files", "tags"]

index = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "content/index.jsonl")
if not index.exists():
    print(f"OK: no index at {index} (nothing to validate yet)")
    sys.exit(0)

# entries reference paths relative to the vault root (the parent of content/)
root = index.parent.parent
errors, seen_ids = [], {}
for lineno, line in enumerate(index.read_text(encoding="utf-8").splitlines(), 1):
    if not line.strip():
        continue
    try:
        entry = json.loads(line)
    except json.JSONDecodeError as exc:
        errors.append(f"line {lineno}: invalid JSON ({exc.msg})")
        continue
    if not isinstance(entry, dict):
        errors.append(f"line {lineno}: entry is not a JSON object")
        continue
    for field in REQUIRED:
        if field not in entry:
            errors.append(f"line {lineno}: missing field {field}")
        elif field in LIST_FIELDS and not isinstance(entry[field], list):
            errors.append(f"line {lineno}: {field} must be a list")
        elif field not in LIST_FIELDS and not isinstance(entry[field], str):
            errors.append(f"line {lineno}: {field} must be a string")
    entry_id = entry.get("id")
    if isinstance(entry_id, str):
        if entry_id in seen_ids:
            errors.append(f"line {lineno}: duplicate id {entry_id} (first seen on line {seen_ids[entry_id]})")
        else:
            seen_ids[entry_id] = lineno
    source_files = entry.get("source_files")
    for ref in [entry.get("path")] + (source_files if isinstance(source_files, list) else []):
        if isinstance(ref, str) and not (root / ref).exists():
            errors.append(f"line {lineno}: referenced file not found: {ref}")

if errors:
    print("Validation failed:")
    print("\n".join(errors))
    sys.exit(1)
print(f"OK: validated {len(seen_ids)} index entries in {index}")
