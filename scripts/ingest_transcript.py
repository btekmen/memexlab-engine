#!/usr/bin/env python3
"""Ingest a meeting transcript (.vtt/.srt/.txt) as a meeting note in inbox/.

Deterministic, no network (PyYAML is the only import outside the stdlib).
Dry-run by default; --apply writes. Speaker turns become timestamped quote
blocks; re-ingesting identical transcript content is a no-op (RFC-013 phase 1).

Frontmatter is built as a dict and serialized with yaml.safe_dump rather than
interpolated, and the filename components are slugified, so a title, date or
attendee list carrying newlines, a second `---` or YAML metacharacters cannot
inject frontmatter keys or steer the write out of inbox/.
"""
import argparse
import hashlib
import pathlib
import re
import sys

import yaml

_VTT_TIMING = re.compile(r"^(\d{2}:\d{2}:\d{2})\.\d{3}\s+-->\s+")
_SRT_TIMING = re.compile(r"^(\d{2}:\d{2}:\d{2}),\d{3}\s+-->\s+")
_VOICE_TAG = re.compile(r"^<v\s+([^>]+)>(.*?)(?:</v>)?$")
_SPEAKER_LINE = re.compile(r"^([^:]{1,40}):\s+(.+)$")


def _cue_text(lines: list[str]):
    speaker, parts = "", []
    for line in lines:
        m = _VOICE_TAG.match(line)
        if m:
            speaker = m.group(1).strip()
            line = m.group(2)
        parts.append(re.sub(r"<[^>]+>", "", line).strip())
    return speaker, " ".join(p for p in parts if p)


def _parse_cues(lines: list[str], timing: re.Pattern) -> list[dict]:
    segments, i = [], 0
    while i < len(lines):
        m = timing.match(lines[i])
        if not m:
            i += 1
            continue
        start = m.group(1)
        i += 1
        block = []
        while i < len(lines) and lines[i].strip():
            block.append(lines[i])
            i += 1
        speaker, text = _cue_text(block)
        m2 = _SPEAKER_LINE.match(text)
        if not speaker and m2:
            speaker, text = m2.group(1).strip(), m2.group(2).strip()
        segments.append({"start": start, "speaker": speaker, "text": text})
    return segments


def _parse_txt(lines: list[str]) -> list[dict]:
    segments = []
    for line in lines:
        if not line.strip():
            continue
        m = _SPEAKER_LINE.match(line)
        if m:
            segments.append({"start": "", "speaker": m.group(1).strip(),
                             "text": m.group(2).strip()})
        else:
            segments.append({"start": "", "speaker": "", "text": line.strip()})
    return segments


def parse_transcript(path: pathlib.Path) -> list[dict]:
    path = pathlib.Path(path)
    lines = path.read_text(encoding="utf-8").splitlines()
    suffix = path.suffix.lower()
    if suffix == ".vtt":
        return _parse_cues(lines, _VTT_TIMING)
    if suffix == ".srt":
        return _parse_cues(lines, _SRT_TIMING)
    if suffix == ".txt":
        return _parse_txt(lines)
    sys.exit(f"error: unsupported transcript format: {path.name} "
             "(expected .vtt, .srt, or .txt)")


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "meeting"


def _date_slug(value: str) -> str:
    """Filename-safe date component — never a path separator or a `..`."""
    return re.sub(r"[^0-9A-Za-z-]+", "-", value).strip("-")[:20]


def _quote(seg: dict) -> str:
    head = ""
    if seg["start"]:
        head += f"[{seg['start']}] "
    if seg["speaker"]:
        head += f"**{seg['speaker']}**: "
    return f"> {head}{seg['text']}"


def _render(title, date, attendees, transcript_id, segments) -> str:
    front = {"type": "meeting", "source": "transcript",
             "transcript_id": transcript_id}
    if date:
        front["date"] = date
    if attendees:
        front["attendees"] = list(attendees)
    block = ["---", yaml.safe_dump(front, sort_keys=False,
                                   allow_unicode=True).rstrip(), "---"]
    body = [f"# {title}", "", "## Transcript", ""]
    body += [_quote(s) for s in segments]
    return "\n".join(block + [""] + body) + "\n"


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


def _already_ingested(inbox: pathlib.Path, transcript_id: str) -> bool:
    return any(frontmatter_of(note).get("transcript_id") == transcript_id
               for note in inbox.glob("*.md"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("transcript", help="path to .vtt/.srt/.txt transcript")
    parser.add_argument("--vault", required=True, help="vault root")
    parser.add_argument("--title", default="", help="meeting title")
    parser.add_argument("--date", default="", help="meeting date (YYYY-MM-DD)")
    parser.add_argument("--attendees", default="",
                        help="comma-separated attendee emails")
    parser.add_argument("--apply", action="store_true",
                        help="write the note (default: dry-run preview)")
    args = parser.parse_args(argv)

    path = pathlib.Path(args.transcript)
    if not path.is_file():
        sys.exit(f"error: no such file: {path}")
    segments = parse_transcript(path)
    transcript_id = hashlib.sha256(path.read_bytes()).hexdigest()[:16]

    title = args.title or path.stem
    attendees = [a.strip() for a in args.attendees.split(",") if a.strip()]
    inbox = pathlib.Path(args.vault) / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    date_part = _date_slug(args.date)
    name = f"meeting-{date_part + '-' if date_part else ''}{_slug(title)}.md"
    target = inbox / name

    if _already_ingested(inbox, transcript_id):
        print(f"skip (already ingested): {title} [{transcript_id}]")
    elif args.apply:
        target.write_text(
            _render(title, args.date, attendees, transcript_id, segments),
            encoding="utf-8")
        print(f"wrote {target}  ({len(segments)} segments)")
    else:
        print(f"dry-run: would write {target}  ({len(segments)} segments); "
              "pass --apply to write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
