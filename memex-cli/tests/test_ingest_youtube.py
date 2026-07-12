import json
import pathlib

import pytest

from memex_cli.ingest_youtube import (ingest_youtube, parse_timedtext,
                                      parse_watch_page, pick_track, video_id)
from memex_cli.vault import Vault

VID = "dQw4w9WgXcQ"
WATCH = (
    '<html><head><meta property="og:title" content="Governed Memory — a talk">'
    "</head><body><script>var ytInitialPlayerResponse = {"
    '"captionTracks":[{"baseUrl":"https://www.youtube.com/api/timedtext?v=dQw4w9WgXcQ'
    '\\u0026lang=en\\u0026kind=asr","languageCode":"en","kind":"asr"},'
    '{"baseUrl":"https://www.youtube.com/api/timedtext?v=dQw4w9WgXcQ\\u0026lang=tr",'
    '"languageCode":"tr"}],'
    '"ownerChannelName":"Ada Explains"};</script></body></html>'
)
TIMEDTEXT = """<?xml version="1.0" encoding="utf-8"?>
<transcript>
<text start="0.0" dur="4.2">Agents need memory they can use</text>
<text start="4.4" dur="3.9">but cannot corrupt.</text>
<text start="65.2" dur="4.0">Writes land in inbox only,</text>
<text start="69.4" dur="3.1">with provenance &amp;amp; an audit log.</text>
<text start="131.0" dur="2.5">Deterministic retrieval makes it citable.</text>
</transcript>"""


@pytest.fixture
def vault(tmp_path: pathlib.Path) -> Vault:
    (tmp_path / "governance.yml").write_text("write_dir: inbox\n", encoding="utf-8")
    return Vault(tmp_path)


def test_video_id_variants():
    for u in (f"https://www.youtube.com/watch?v={VID}",
              f"https://youtu.be/{VID}?t=42",
              f"https://www.youtube.com/shorts/{VID}"):
        assert video_id(u) == VID
    with pytest.raises(ValueError):
        video_id("https://example.com/nope")


def test_parse_watch_page_unescapes_track_urls():
    meta = parse_watch_page(WATCH)
    assert meta["title"] == "Governed Memory — a talk"
    assert meta["channel"] == "Ada Explains"
    assert len(meta["tracks"]) == 2
    assert "&lang=en" in meta["tracks"][0]["url"]


def test_pick_track_prefers_uploaded_and_honors_lang():
    tracks = parse_watch_page(WATCH)["tracks"]
    assert pick_track(tracks, None)["lang"] == "tr"      # uploaded beats asr
    assert pick_track(tracks, "en")["kind"] == "asr"
    with pytest.raises(ValueError, match="no caption track for language 'de'"):
        pick_track(tracks, "de")
    with pytest.raises(ValueError, match="no captions available"):
        pick_track([], None)


def test_timedtext_parsing_unescapes_entities():
    segs = parse_timedtext(TIMEDTEXT)
    assert len(segs) == 5
    assert segs[3]["text"] == "with provenance & an audit log."


def test_apply_builds_anchored_note_with_deeplinks(vault):
    res = ingest_youtube(vault, f"https://youtu.be/{VID}", apply=True,
                         page=WATCH, timedtext=TIMEDTEXT)
    assert res["ok"] and res["anchors"] == 3 and res["transcript_kind"] == "uploaded"
    note = (vault.root / res["note"]).read_text()
    assert "captured_via: youtube" in note
    assert f"video_id: {VID}" in note
    assert "transcript_kind: uploaded" in note
    assert "channel: Ada Explains" in note
    assert f"## [0:00](https://youtu.be/{VID}?t=0) {{#000}}" in note
    assert f"## [1:05](https://youtu.be/{VID}?t=65) {{#105}}" in note
    assert f"## [2:11](https://youtu.be/{VID}?t=131) {{#211}}" in note
    assert "Agents need memory they can use but cannot corrupt." in note


def test_dry_run_and_dedup(vault):
    res = ingest_youtube(vault, f"https://youtu.be/{VID}",
                         page=WATCH, timedtext=TIMEDTEXT)
    assert not res["applied"]
    assert not (vault.root / "inbox").exists()
    ingest_youtube(vault, f"https://youtu.be/{VID}", apply=True,
                   page=WATCH, timedtext=TIMEDTEXT)
    dup = ingest_youtube(vault, f"https://www.youtube.com/watch?v={VID}", apply=True,
                         page=WATCH, timedtext=TIMEDTEXT)
    assert dup["action"] == "skip-duplicate"
    assert len(list((vault.root / "inbox").glob("*.md"))) == 1


def test_cli_end_to_end(vault, capsys, monkeypatch):
    from memex_cli import cli

    def fake_fetch(url):
        return TIMEDTEXT if "timedtext" in url else WATCH

    monkeypatch.setattr("memex_cli.ingest_youtube.fetch_text", fake_fetch)
    code = cli.main(["ingest", "youtube", f"https://youtu.be/{VID}",
                     "--vault", str(vault.root)])
    out, err = capsys.readouterr()
    assert code == 0 and "3 timestamp anchors" in out
    event = json.loads(err.strip().splitlines()[-1])
    assert event["cmd"] == "ingest-youtube" and not event["applied"]

    code = cli.main(["ingest", "youtube", f"https://youtu.be/{VID}",
                     "--vault", str(vault.root), "--apply", "--lang", "en"])
    out, _ = capsys.readouterr()
    assert code == 0 and "auto captions" in out


def test_empty_or_invalid_timedtext_fails_cleanly(vault):
    res = ingest_youtube(vault, f"https://youtu.be/{VID}", apply=True,
                         page=WATCH, timedtext="")
    assert not res["ok"] and res["action"] == "no-caption-data" and "hint" in res
    assert not (vault.root / "inbox").exists()
    assert parse_timedtext("not xml at all") == []
