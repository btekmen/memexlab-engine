#!/usr/bin/env python3
import pathlib, re, sys

vault = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
errors = []
for path in vault.rglob("*.md"):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"{path}: missing frontmatter")
    if "type:" not in text.split("---", 2)[1]:
        errors.append(f"{path}: missing type")
    for bad in ["TODO_REAL_NAME", "SECRET", "PRIVATE_KEY"]:
        if bad in text:
            errors.append(f"{path}: forbidden marker {bad}")

if errors:
    print("Validation failed:")
    print("\n".join(errors))
    sys.exit(1)
print(f"OK: validated markdown vault at {vault}")
