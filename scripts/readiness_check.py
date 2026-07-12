#!/usr/bin/env python3
"""Public-release readiness gate (governance.yml release_policy).

Automates what can be automated: re-runs the required pre-push checks and
scans the repo for concrete privacy leaks (credentials, keys, real contact
details, unscrubbed vault markers). The deny_publication_patterns in
governance.yml name categories, not literal strings, so this scan looks for
machine-detectable indicators of those categories. The git history privacy
audit and explicit human approval remain manual gates.
"""
import pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".claude", "logs", "site", "__pycache__", ".venv", "node_modules"}
TEXT_SUFFIXES = {".md", ".yml", ".yaml", ".json", ".jsonl", ".py", ".txt", ".toml", ".html", ".css", ".js"}
ALLOWED_EMAILS = re.compile(r"@(example\.(com|org|net)|[\w.-]+\.example\b|github\.com|yourorg\b)", re.IGNORECASE)

# markers split so this file and validate_vault.py do not flag themselves
MARKERS = ["TODO_" + "REAL_NAME", "SEC" + "RET", "PRIVATE_" + "KEY"]
SECRET_PATTERNS = [
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY")),
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub token", re.compile(r"\b(ghp|gho|ghs|ghu)_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}")),
    ("Slack token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("API secret key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("email address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
]

REQUIRED_CHECKS = [
    ["python3", "scripts/validate_index.py"],
    ["python3", "scripts/validate_vault.py", "examples/fake-vault"],
]

errors = []

for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
        continue
    if SKIP_DIRS & set(path.relative_to(ROOT).parts):
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    rel = path.relative_to(ROOT)
    if path.name not in ("readiness_check.py", "validate_vault.py"):
        for marker in MARKERS:
            if marker in text:
                errors.append(f"{rel}: unscrubbed marker {marker}")
    for label, pattern in SECRET_PATTERNS:
        for match in pattern.findall(text) if label == "email address" else pattern.finditer(text):
            if label == "email address":
                if ALLOWED_EMAILS.search(match):
                    continue
                errors.append(f"{rel}: possible personal contact detail ({match})")
            else:
                errors.append(f"{rel}: possible {label}")
                break

for cmd in REQUIRED_CHECKS:
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).strip()
        errors.append(f"required check failed: {' '.join(cmd)}\n{detail}")

if errors:
    print("Readiness check failed:")
    print("\n".join(errors))
    sys.exit(1)

print("OK: privacy scan clean, required pre-push checks pass")
print("Manual gates still required before public release:")
print("- git history privacy audit")
print("- explicit human approval")
