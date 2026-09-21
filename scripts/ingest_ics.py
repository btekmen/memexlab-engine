#!/usr/bin/env python3
"""Ingest a calendar invite (.ics) as a meeting note draft in the vault's inbox/.

Deterministic, no network (PyYAML is the only import outside the stdlib).
Dry-run by default; --apply writes. One note per VEVENT; re-ingesting the same
UID never duplicates (RFC-012 shim).

An .ics file is attacker-controlled input — anyone who can email a calendar
invite chooses these values, and _unescape turns `\\n` into a real newline. So
frontmatter is built as a dict and serialized with yaml.safe_dump (never
f-string interpolation), and the filename components are slugified: an invite
cannot add frontmatter keys, forge type:/tags:, close the block with a second
`---`, or steer the write out of inbox/.
"""
import argparse
import pathlib
import re
import sys

import yaml


def _unfold(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def _unescape(value: str) -> str:
    return (
        value.replace("\\n", "\n").replace("\\N", "\n")
        .replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")
    )


def _parse_property(line: str):
    head, _, value = line.partition(":")
    parts = head.split(";")
    name = parts[0].upper()
    params = {}
    for p in parts[1:]:
        k, _, v = p.partition("=")
        params[k.upper()] = v
    return name, params, value


def _person(params: dict, value: str) -> dict:
    email = value[len("mailto:"):] if value.lower().startswith("mailto:") else value
    return {"name": params.get("CN", email), "email": email}


def _fmt_dt(value: str) -> str:
    value = value.rstrip("Z")
    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2})(\d{2}))?", value)
    if not m:
        return value
    y, mo, d, hh, mm, ss = m.groups()
    if hh is None:
        return f"{y}-{mo}-{d}"
    return f"{y}-{mo}-{d}T{hh}:{mm}:{ss}"


def parse_ics(path: pathlib.Path) -> list[dict]:
    text = pathlib.Path(path).read_text(encoding="utf-8")
    events, event = [], None
    for line in _unfold(text):
        if not line.strip():
            continue
        name, params, value = _parse_property(line)
        if name == "BEGIN" and value.upper() == "VEVENT":
            event = {"uid": "", "summary": "", "dtstart": "", "location": "",
                     "description": "", "organizer": None, "attendees": []}
        elif name == "END" and value.upper() == "VEVENT" and event is not None:
            events.append(event)
            event = None
        elif event is None:
            continue
        elif name == "UID":
            event["uid"] = value
        elif name == "SUMMARY":
            event["summary"] = _unescape(value)
        elif name == "DTSTART":
            event["dtstart"] = _fmt_dt(value)
        elif name == "LOCATION":
            event["location"] = _unescape(value)
        elif name == "DESCRIPTION":
            event["description"] = _unescape(value)
        elif name == "ORGANIZER":
            event["organizer"] = _person(params, value)
        elif name == "ATTENDEE":
            event["attendees"].append(_person(params, value))
    return events


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "meeting"


def _date_slug(value: str) -> str:
    """Filename-safe date component — never a path separator or a `..`."""
    return re.sub(r"[^0-9A-Za-z-]+", "-", value).strip("-")[:20]


_FRONTMATTER = re.compile(r"\A---\n(.*?)^---\s*$", re.S | re.M)


def frontmatter_of(note: pathlib.Path) -> dict:
    """Parse a note's frontmatter block; {} if it has none or it is malformed.

    The closing fence must be a line of its own — a `---` sitting inside an
    (indented) quoted scalar does not end the block.
    """
    m = _FRONTMATTER.search(note.read_text(encoding="utf-8"))
    if not m:
        return {}
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _existing_uids(inbox: pathlib.Path) -> set[str]:
    uids = set()
    for note in inbox.glob("*.md"):
        uid = frontmatter_of(note).get("uid")
        if isinstance(uid, str) and uid:
            uids.add(uid)
    return uids


def _render(event: dict) -> str:
    front = {"type": "meeting", "source": "ics", "uid": event["uid"],
             "date": event["dtstart"]}
    if event["location"]:
        front["location"] = event["location"]
    if event["organizer"]:
        front["organizer"] = event["organizer"]["email"]
    if event["attendees"]:
        front["attendees"] = [a["email"] for a in event["attendees"]]
    block = ["---", yaml.safe_dump(front, sort_keys=False,
                                   allow_unicode=True).rstrip(), "---"]
    body = [f"# {event['summary']}", ""]
    if event["attendees"]:
        body.append("## Attendees")
        body += [f"- {a['name']} <{a['email']}>" for a in event["attendees"]]
        body.append("")
    if event["description"]:
        body += ["## Description", event["description"], ""]
    return "\n".join(block + [""] + body)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ics", help="path to the .ics file")
    parser.add_argument("--vault", required=True, help="vault root")
    parser.add_argument("--apply", action="store_true",
                        help="write notes (default: dry-run preview)")
    args = parser.parse_args(argv)

    ics = pathlib.Path(args.ics)
    if not ics.is_file():
        sys.exit(f"error: no such file: {ics}")
    inbox = pathlib.Path(args.vault) / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)

    events = parse_ics(ics)
    seen = _existing_uids(inbox)
    for event in events:
        date = _date_slug(event["dtstart"].split("T")[0])
        stem = f"meeting-{date}-{_slug(event['summary'])}" if date \
            else f"meeting-{_slug(event['summary'])}"
        target = inbox / f"{stem}.md"
        if event["uid"] in seen:
            print(f"skip (already ingested): {event['summary']} [{event['uid']}]")
        elif args.apply:
            target.write_text(_render(event), encoding="utf-8")
            print(f"wrote {target}")
        else:
            print(f"dry-run: would write {target}  ({event['summary']})")
    if not args.apply:
        print("dry-run: nothing written; pass --apply to write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
