import pathlib

import pytest

from memex_cli.feeds import (ingest_feeds, ingest_youtube_feed,
                             parse_feeds_file, resolve_channel)
from memex_cli.vault import Vault

YT_ATOM = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>Ada Explains</title>
<entry><title>Governed memory in 12 minutes</title>
<id>yt:video:abc123</id>
<link rel="alternate" href="https://www.youtube.com/watch?v=abc123"/>
<published>2026-07-09T12:00:00Z</published>
</entry>
</feed>"""

CID = "UC" + "a" * 22


@pytest.fixture
def vault(tmp_path: pathlib.Path) -> Vault:
    (tmp_path / "governance.yml").write_text("write_dir: inbox\n", encoding="utf-8")
    return Vault(tmp_path)


def test_resolve_channel_variants():
    direct = resolve_channel(CID)
    assert direct.endswith(f"channel_id={CID}")
    assert resolve_channel(f"https://www.youtube.com/channel/{CID}/videos") == direct
    resolved = resolve_channel(
        "@ada", fetch=lambda url: f'{{"channelId":"{CID}"}}'.encode())
    assert resolved == direct
    with pytest.raises(ValueError, match="unrecognized channel"):
        resolve_channel("not-a-channel")
    with pytest.raises(ValueError, match="could not resolve"):
        resolve_channel("@ghost", fetch=lambda url: b"<html>no id here</html>")


def test_youtube_feed_notes_carry_via_and_link(vault):
    res = ingest_youtube_feed(vault, CID, apply=True, data=YT_ATOM)
    assert res["ok"] and res["new_items"] == 1 and res["channel"] == CID
    note = next((vault.root / "inbox").glob("governed-memory-in-12-minutes-*.md")).read_text()
    assert "captured_via: youtube-feed" in note
    assert "source_url: https://www.youtube.com/watch?v=abc123" in note


def test_parse_feeds_file():
    subs = parse_feeds_file(
        "# My feeds\n\n"
        "- https://example.com/feed.xml #ai #research\n"
        "some prose to ignore\n"
        f"- {CID}\n"
        "- @handle #video\n"
    )
    assert [s["kind"] for s in subs] == ["rss", "youtube-feed", "youtube-feed"]
    assert subs[0]["tags"] == ["ai", "research"]
    assert subs[2]["tags"] == ["video"]


def test_ingest_feeds_isolates_failures_and_applies_tags(vault, monkeypatch):
    RSS = (b'<?xml version="1.0"?><rss version="2.0"><channel><title>Blog</title>'
           b'<item><title>Post One</title><link>https://e.com/1</link>'
           b'<guid>g1</guid><description>Body.</description></item></channel></rss>')
    (vault.root / "feeds.md").write_text(
        "- https://good.example/feed.xml #ai\n"
        "- https://bad.example/feed.xml\n", encoding="utf-8")

    def fake_fetch(url):
        if "bad.example" in url:
            raise OSError("connection refused")
        return RSS

    monkeypatch.setattr("memex_cli.ingest_rss.fetch_bytes", fake_fetch)
    res = ingest_feeds(vault, apply=True)
    assert res["subscriptions"] == 2 and res["failures"] == 1
    assert res["new_items"] == 1
    ok = next(r for r in res["results"] if r["ok"])
    bad = next(r for r in res["results"] if not r["ok"])
    assert ok["new_items"] == 1 and "connection refused" in bad["error"]
    note = next((vault.root / "inbox").glob("post-one-*.md")).read_text()
    assert "tags:\n- ai" in note or "tags: [ai]" in note


def test_ingest_feeds_requires_file(vault):
    with pytest.raises(ValueError, match="no feeds.md"):
        ingest_feeds(vault)


def test_cli_end_to_end(vault, capsys, monkeypatch):
    from memex_cli import cli

    (vault.root / "feeds.md").write_text(f"- {CID} #video\n", encoding="utf-8")
    monkeypatch.setattr("memex_cli.ingest_rss.fetch_bytes", lambda url: YT_ATOM)
    code = cli.main(["ingest", "feeds", "--vault", str(vault.root)])
    out, err = capsys.readouterr()
    assert code == 0 and "dry-run: would capture 1" in out and "youtube-feed" in out

    code = cli.main(["ingest", "youtube-feed", CID, "--vault", str(vault.root), "--apply"])
    out, _ = capsys.readouterr()
    assert code == 0 and "captured 1 new video note(s)" in out
