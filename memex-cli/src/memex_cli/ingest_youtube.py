"""`memex ingest youtube <video-url>` — captions → a transcript note with
timestamp heading anchors, so answers can cite the exact minute of a talk the
same way they cite a slug (`[[note#0510]]`), and every anchor deep-links back
to the moment (`?t=`).

Uses the video's PUBLISHED caption tracks via the public timedtext endpoint the
player itself uses — no account, no API key, nothing scraped behind auth. If a
video has no captions we say so and stop; we never guess. (Local ASR as an
explicit opt-in is future work.) `transcript_kind` records whether captions
were uploaded or auto-generated so downstream consumers can weigh them.
"""
from __future__ import annotations

import datetime
import html
import itertools
import json
import pathlib
import re
import urllib.request
import xml.etree.ElementTree as ET

import yaml

from .state import IngestState
from .vault import Vault

BUCKET_SECONDS = 60
_VIDEO_ID = re.compile(
    r"(?:v=|youtu\.be/|shorts/|embed/)([0-9A-Za-z_-]{11})")
_TRACKS = re.compile(r'"captionTracks":(\[.*?\])')
_TITLE = re.compile(r'<meta (?:property="og:title"|name="title") content="([^"]*)"')
_CHANNEL = re.compile(r'"ownerChannelName":"((?:[^"\\]|\\.)*)"')


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")
    return slug[:80].rstrip("-") or "video"


def video_id(url: str) -> str:
    m = _VIDEO_ID.search(url)
    if not m:
        raise ValueError(f"could not find a video id in: {url}")
    return m.group(1)


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "memex-cli",
                                               "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_watch_page(page: str) -> dict:
    """Watch-page HTML → {title, channel, tracks:[{url, lang, kind, name}]}."""
    m = _TRACKS.search(page)
    tracks = []
    if m:
        try:
            for t in json.loads(m.group(1)):
                tracks.append({
                    "url": t.get("baseUrl", "").replace("\\u0026", "&"),
                    "lang": t.get("languageCode", ""),
                    "kind": t.get("kind", ""),  # "asr" = auto-generated
                })
        except json.JSONDecodeError:
            pass
    tm = _TITLE.search(page)
    cm = _CHANNEL.search(page)
    return {
        "title": html.unescape(tm.group(1)) if tm else "",
        "channel": json.loads(f'"{cm.group(1)}"') if cm else "",
        "tracks": [t for t in tracks if t["url"]],
    }


def pick_track(tracks: list[dict], lang: str | None) -> dict:
    if not tracks:
        raise ValueError("no captions available on this video — nothing to ingest "
                         "(we never guess; local ASR may come later as an opt-in)")
    if lang:
        for t in tracks:
            if t["lang"] == lang or t["lang"].startswith(lang + "-"):
                return t
        raise ValueError(f"no caption track for language '{lang}' "
                         f"(available: {', '.join(sorted({t['lang'] for t in tracks}))})")
    uploaded = [t for t in tracks if t["kind"] != "asr"]
    return (uploaded or tracks)[0]


def parse_timedtext(xml_text: str) -> list[dict]:
    """timedtext XML → [{start: float, text: str}]; empty/invalid → []."""
    if not xml_text.strip():
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    out = []
    for el in root.iter("text"):
        raw = "".join(el.itertext())
        text = html.unescape(html.unescape(raw)).replace("\n", " ").strip()
        if text:
            out.append({"start": float(el.get("start", "0")), "text": text})
    return out


def _stamp(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{sec:02d}" if h else f"{m:d}:{sec:02d}"


def _anchor(seconds: float) -> str:
    return _stamp(seconds).replace(":", "")


def build_note(url: str, vid: str, meta: dict, kind: str, segments: list[dict],
               now: datetime.datetime) -> str:
    frontmatter = {
        "title": meta["title"] or f"YouTube video {vid}",
        "status": "inbox",
        "captured_via": "youtube",
        "captured_at": now.isoformat(),
        "source_url": f"https://www.youtube.com/watch?v={vid}",
        "video_id": vid,
        "transcript_kind": "auto" if kind == "asr" else "uploaded",
    }
    if meta["channel"]:
        frontmatter["channel"] = meta["channel"]
    lines = ["---", yaml.safe_dump(frontmatter, sort_keys=False,
                                   allow_unicode=True).rstrip(), "---", "",
             f"# {frontmatter['title']}", ""]
    bucket_start: float | None = None
    bucket_text: list[str] = []

    def flush() -> None:
        if bucket_start is None:
            return
        ts = _stamp(bucket_start)
        link = f"https://youtu.be/{vid}?t={int(bucket_start)}"
        lines.append(f"## [{ts}]({link}) {{#{_anchor(bucket_start)}}}")
        lines.append("")
        lines.append(" ".join(bucket_text))
        lines.append("")

    for seg in segments:
        if bucket_start is None or seg["start"] - bucket_start >= BUCKET_SECONDS:
            flush()
            bucket_start, bucket_text = seg["start"], []
        bucket_text.append(seg["text"])
    flush()
    return "\n".join(lines) + "\n"


def ingest_youtube(
    vault: Vault, url: str, apply: bool = False, force: bool = False,
    lang: str | None = None,
    page: str | None = None, timedtext: str | None = None,
) -> dict:
    """`page`/`timedtext` override network fetches (tests/offline)."""
    vid = video_id(url)
    canonical = f"https://www.youtube.com/watch?v={vid}"

    state = IngestState(vault.root)
    prior = state.seen_url(canonical)
    if prior and not force and (vault.root / prior["note"]).exists():
        return {"action": "skip-duplicate", "url": canonical, "note": prior["note"],
                "applied": False, "ok": True}

    meta = parse_watch_page(page if page is not None else fetch_text(canonical))
    track = pick_track(meta["tracks"], lang)
    segments = parse_timedtext(timedtext if timedtext is not None
                               else fetch_text(track["url"]))
    if not segments:
        return {"action": "no-caption-data", "url": canonical, "applied": False,
                "ok": False,
                "hint": "YouTube returned no usable timedtext for this video/region "
                        "— captions exist in the player but the public endpoint "
                        "withheld them; an opt-in local-ASR path is future work"}

    now = datetime.datetime.now(datetime.timezone.utc)
    note_text = build_note(url, vid, meta, track["kind"], segments, now)
    target_dir = vault.write_target()
    slug = _slugify(meta["title"] or vid)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    rel: pathlib.Path | None = None
    for i in itertools.count():
        name = f"{slug}-{stamp}.md" if i == 0 else f"{slug}-{stamp}-{i}.md"
        cand = target_dir / name
        if cand.resolve().parent != target_dir:
            raise PermissionError(f"write escapes boundary: {name}")
        if not cand.exists():
            rel = cand.relative_to(vault.root)
            break

    result = {"action": "ingest-youtube", "url": canonical, "title": meta["title"],
              "note": str(rel), "segments": len(segments),
              "anchors": note_text.count("\n## ["),
              "transcript_kind": "auto" if track["kind"] == "asr" else "uploaded",
              "applied": apply, "ok": True}
    if not apply:
        return result
    target_dir.mkdir(parents=True, exist_ok=True)
    (vault.root / rel).write_text(note_text, encoding="utf-8")
    state.record_url(canonical, str(rel), now.isoformat())
    state.save()
    return result
