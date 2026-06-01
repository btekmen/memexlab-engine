#!/usr/bin/env python3
"""Regenerate library/README.md from the frontmatter of every asset in library/.

Drop a new knowledge asset into library/papers/ or library/books/, run this, and the
index updates. No third-party dependencies.
"""
import pathlib, re, sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "library")

def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    d = {}
    if not m:
        return d
    for line in m.group(1).splitlines():
        mm = re.match(r"^(\w+):\s*(.*)$", line)
        if mm:
            d[mm.group(1)] = mm.group(2).strip().strip('"')
    return d

groups = {}
for p in sorted(root.rglob("*.md")):
    if p.name == "README.md":
        continue
    d = frontmatter(p.read_text(encoding="utf-8"))
    kind = p.parent.name
    rel = p.relative_to(root).as_posix()
    authors = d.get("authors") or d.get("author", "")
    authors = re.sub(r"^\[|\]$", "", authors)
    groups.setdefault(kind, []).append((d.get("title", rel), authors, d.get("year", ""), rel))

names = {"papers": "Papers", "reports": "Reports", "books": "Books"}
order = ["papers", "reports", "books"]
lines = [
    "# Library",
    "",
    "A growing collection of MemexLab **knowledge assets** — synthesized notes from papers,",
    "reports, and books, each with provenance, key ideas, and atomic-note candidates.",
    "",
    "Add one by dropping a markdown file (with frontmatter: `title`, `author`/`authors`, `year`,",
    "`tags`) into `library/papers/`, `library/reports/`, or `library/books/`, then regenerate",
    "this index:",
    "",
    "```bash",
    "python3 scripts/build_library_index.py",
    "```",
    "",
]
total = 0
for k in order + [g for g in groups if g not in order]:
    if k not in groups:
        continue
    items = sorted(groups[k])
    total += len(items)
    lines += [f"## {names.get(k, k.title())} ({len(items)})", "", "| Title | Author(s) | Year |", "| --- | --- | --- |"]
    for title, authors, year, rel in items:
        lines.append(f"| [{title}]({rel}) | {authors} | {year} |")
    lines.append("")
(root / "README.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
print(f"indexed {total} assets into {root}/README.md")
