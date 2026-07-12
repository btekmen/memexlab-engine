#!/usr/bin/env python3
"""Ingest a meeting transcript (.vtt/.srt/.txt) as a meeting note in inbox/.

Deterministic, stdlib-only, no network. Dry-run by default; --apply writes.
Speaker turns become timestamped quote blocks; re-ingesting identical
transcript content is a no-op (RFC-013 phase 1).
"""
import argparse
import hashlib
import pathlib
import re
import sys

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


def _quote(seg: dict) -> str:
    head = ""
    if seg["start"]:
        head += f"[{seg['start']}] "
    if seg["speaker"]:
        head += f"**{seg['speaker']}**: "
    return f"> {head}{seg['text']}"


def _render(title, date, attendees, transcript_id, segments) -> str:
    front = ["---", "type: meeting", "source: transcript",
             f"transcript_id: {transcript_id}"]
    if date:
        front.append(f"date: {date}")
    if attendees:
        front.append("attendees:")
        front += [f"  - {a}" for a in attendees]
    front.append("---")
    body = [f"# {title}", "", "## Transcript", ""]
    body += [_quote(s) for s in segments]
    return "\n".join(front + [""] + body) + "\n"


def _already_ingested(inbox: pathlib.Path, transcript_id: str) -> bool:
    needle = f"transcript_id: {transcript_id}"
    return any(needle in note.read_text(encoding="utf-8")
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
    name = f"meeting-{args.date + '-' if args.date else ''}{_slug(title)}.md"
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
