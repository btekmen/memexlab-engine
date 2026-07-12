import json
import pathlib

import pytest

from memex_cli.ingest_rss import ingest_rss, parse_feed
from memex_cli.vault import Vault

RSS2 = b"""<?xml version="1.0"?>
<rss version="2.0"><channel>
<title>Stratechery-ish</title>
<item><title>Platform Banking, Revisited</title>
<link>https://example.com/platform-banking</link>
<guid>ex-1</guid>
<pubDate>Wed, 08 Jul 2026 09:00:00 GMT</pubDate>
<description>&lt;p&gt;Banks as &lt;b&gt;platforms&lt;/b&gt;, not pipes.&lt;/p&gt;&lt;script&gt;evil()&lt;/script&gt;</description>
</item>
<item><title>Older Piece</title>
<link>https://example.com/older</link>
<guid>ex-2</guid>
<pubDate>Mon, 01 Jun 2026 09:00:00 GMT</pubDate>
<description>Old news.</description>
</item>
</channel></rss>"""

ATOM = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<title>Governed Notes</title>
<entry><title>Memory With A Boundary</title>
<id>tag:example.com,2026:a1</id>
<link rel="alternate" href="https://example.com/boundary"/>
<published>2026-07-10T12:00:00Z</published>
<summary>Writes land in inbox only.</summary>
</entry>
</feed>"""


@pytest.fixture
def vault(tmp_path: pathlib.Path) -> Vault:
    (tmp_path / "governance.yml").write_text("write_dir: inbox\n", encoding="utf-8")
    return Vault(tmp_path)


def test_parse_rss2_strips_html_and_scripts():
    feed = parse_feed(RSS2)
    assert feed["title"] == "Stratechery-ish"
    assert feed["items"][0]["date"] == "2026-07-08"
    assert feed["items"][0]["summary"] == "Banks as platforms, not pipes."


def test_parse_atom():
    feed = parse_feed(ATOM)
    assert feed["items"][0]["link"] == "https://example.com/boundary"
    assert feed["items"][0]["date"] == "2026-07-10"


def test_malformed_feed_raises():
    with pytest.raises(ValueError, match="not an RSS/Atom"):
        parse_feed(b"<html><body>nope</body></html>")


def test_dry_run_writes_nothing(vault):
    res = ingest_rss(vault, "https://example.com/feed.xml", data=RSS2)
    assert res["ok"] and res["new_items"] == 2 and not res["applied"]
    assert not (vault.root / "inbox").exists()
    assert not (vault.root / ".memex").exists()


def test_apply_then_rerun_is_zero_delta(vault):
    res = ingest_rss(vault, "https://example.com/feed.xml", apply=True, data=RSS2)
    assert res["new_items"] == 2
    note = next((vault.root / "inbox").glob("platform-banking-revisited-*.md")).read_text()
    assert "captured_via: rss" in note
    assert "source_url: https://example.com/platform-banking" in note
    assert "feed_title: Stratechery-ish" in note
    assert "Banks as platforms, not pipes." in note
    res2 = ingest_rss(vault, "https://example.com/feed.xml", apply=True, data=RSS2)
    assert res2["new_items"] == 0
    assert len(list((vault.root / "inbox").glob("*.md"))) == 2


def test_limit_guards_volume(vault):
    res = ingest_rss(vault, "https://example.com/feed.xml", apply=True, data=RSS2, limit=1)
    assert res["new_items"] == 1 and res["skipped_by_limit"] == 1
    res2 = ingest_rss(vault, "https://example.com/feed.xml", apply=True, data=RSS2, limit=1)
    assert res2["new_items"] == 1  # picks up the held-back item next run


def test_since_filters_old_items(vault):
    res = ingest_rss(vault, "https://example.com/feed.xml", data=RSS2, since="2026-07-01")
    assert [it["title"] for it in res["plan"]] == ["Platform Banking, Revisited"]


def test_cli_end_to_end(vault, capsys, monkeypatch):
    from memex_cli import cli

    monkeypatch.setattr("memex_cli.ingest_rss.fetch_bytes", lambda url: RSS2)
    code = cli.main(["ingest", "rss", "https://example.com/feed.xml",
                     "--vault", str(vault.root)])
    out, err = capsys.readouterr()
    assert code == 0 and "dry-run: would capture 2" in out
    event = json.loads(err.strip().splitlines()[-1])
    assert event["cmd"] == "ingest-rss" and not event["applied"]

    code = cli.main(["ingest", "rss", "https://example.com/feed.xml",
                     "--vault", str(vault.root), "--apply", "--limit", "1"])
    out, _ = capsys.readouterr()
    assert code == 0 and "captured 1 new item(s)" in out and "held back" in out
