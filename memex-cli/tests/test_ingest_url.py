import json
import pathlib

import pytest

from memex_cli.ingest_url import ingest_url
from memex_cli.state import IngestState
from memex_cli.vault import Vault

FIXTURE_HTML = """<!DOCTYPE html><html><head>
<title>Governed Memory, Explained</title>
<meta name="author" content="Ada Stone">
</head><body><article>
<h1>Governed Memory, Explained</h1>
<p>Agents need memory they can use but cannot corrupt. A governed vault keeps
canonical notes untouchable while new captures land in an inbox with provenance.</p>
<p>Deterministic retrieval makes every answer citable back to real files.</p>
</article></body></html>"""

URL = "https://example.com/governed-memory"


@pytest.fixture
def vault(tmp_path: pathlib.Path) -> Vault:
    (tmp_path / "governance.yml").write_text("write_dir: inbox\n", encoding="utf-8")
    return Vault(tmp_path)


def test_dry_run_writes_nothing(vault):
    res = ingest_url(vault, URL, apply=False, html=FIXTURE_HTML)
    assert res["ok"] and not res["applied"]
    assert res["note"].startswith("inbox/governed-memory-explained-")
    assert not (vault.root / "inbox").exists()
    assert not (vault.root / ".memex").exists()


def test_apply_writes_note_with_provenance(vault):
    res = ingest_url(vault, URL, apply=True, html=FIXTURE_HTML)
    note = (vault.root / res["note"]).read_text(encoding="utf-8")
    assert note.startswith("---\n")
    assert "title: Governed Memory, Explained" in note
    assert f"source_url: {URL}" in note
    assert "captured_via: cli" in note
    assert "cannot corrupt" in note
    state = json.loads((vault.root / ".memex" / "ingest_state.json").read_text())
    assert list(state["url"].values())[0]["note"] == res["note"]


def test_reingest_is_deduplicated_and_force_overrides(vault):
    first = ingest_url(vault, URL, apply=True, html=FIXTURE_HTML)
    second = ingest_url(vault, URL, apply=True, html=FIXTURE_HTML)
    assert second["action"] == "skip-duplicate" and second["note"] == first["note"]
    assert len(list((vault.root / "inbox").glob("*.md"))) == 1
    forced = ingest_url(vault, URL, apply=True, force=True, html=FIXTURE_HTML)
    assert forced["action"] == "ingest-url"
    assert len(list((vault.root / "inbox").glob("*.md"))) == 2


def test_respects_custom_write_dir(vault):
    (vault.root / "governance.yml").write_text("write_dir: capture\n", encoding="utf-8")
    res = ingest_url(vault, URL, apply=True, html=FIXTURE_HTML)
    assert res["note"].startswith("capture/")


def test_extract_failure_reports_not_ok(vault):
    res = ingest_url(vault, URL, apply=True, html="<html><body></body></html>")
    assert not res["ok"] and res["action"] == "extract-failed"
    assert not (vault.root / "inbox").exists()


def test_cli_end_to_end(vault, capsys, monkeypatch):
    from memex_cli import cli

    monkeypatch.setattr("memex_cli.ingest_url.fetch_html", lambda url: FIXTURE_HTML)
    code = cli.main(["ingest", "url", URL, "--vault", str(vault.root)])
    out, err = capsys.readouterr()
    assert code == 0 and "dry-run" in out
    event = json.loads(err.strip().splitlines()[-1])
    assert event["cmd"] == "ingest-url" and event["ok"] and not event["applied"]

    code = cli.main(["ingest", "url", URL, "--vault", str(vault.root), "--apply"])
    out, err = capsys.readouterr()
    assert code == 0 and "captured:" in out
    event = json.loads(err.strip().splitlines()[-1])
    assert event["applied"] is True
