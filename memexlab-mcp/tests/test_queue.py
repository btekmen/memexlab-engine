import json

import pytest

from memexlab_mcp import queue as queue_mod
from memexlab_mcp.vault import Vault, parse_frontmatter


@pytest.fixture
def queue_vault(fixture_vault):
    (fixture_vault / "queue").mkdir()
    (fixture_vault / "queue" / "summarize-memory.md").write_text(
        "---\ntype: queue-item\ntitle: Summarize governed memory\nstatus: pending\n"
        "destination: research-agent\ncreated: 2026-07-01\n---\n"
        "Summarize the governed-memory note in three bullets.\n",
        encoding="utf-8",
    )
    (fixture_vault / "queue" / "old-task.md").write_text(
        "---\ntype: queue-item\ntitle: Old Task\nstatus: done\ncreated: 2026-06-01\n---\ndone already\n",
        encoding="utf-8",
    )
    (fixture_vault / "queue" / "stray.md").write_text(
        "---\ntitle: Not a queue item\n---\nstray\n", encoding="utf-8"
    )
    return fixture_vault


def test_list_queue_default_pending_only(queue_vault):
    got = queue_mod.list_queue(Vault(queue_vault))
    assert [r["item"] for r in got] == ["summarize-memory"]
    assert got[0]["destination"] == "research-agent"
    assert "three bullets" in got[0]["task"]


def test_list_queue_status_filters(queue_vault):
    v = Vault(queue_vault)
    assert [r["item"] for r in queue_mod.list_queue(v, "done")] == ["old-task"]
    assert [r["item"] for r in queue_mod.list_queue(v, "all")] == ["old-task", "summarize-memory"]
    with pytest.raises(ValueError, match="status must be one of"):
        queue_mod.list_queue(v, "bogus")


def test_complete_files_result_then_flips_status_and_logs(queue_vault):
    v = Vault(queue_vault)
    res = queue_mod.complete_queue_item(
        v, "summarize-memory", "Summary: governed memory", "- durable\n- citable\n- auditable"
    )
    assert res["status"] == "done" and res["result"].startswith("inbox/")
    meta, _ = parse_frontmatter((queue_vault / "queue" / "summarize-memory.md").read_text())
    assert meta["status"] == "done"
    assert meta["result"] == res["result"]
    assert meta["completed_by"] == "memexlab-mcp"
    result_meta, result_body = parse_frontmatter((queue_vault / res["result"]).read_text())
    assert "summarize-memory" in result_meta["sources"]
    assert "citable" in result_body
    lines = [json.loads(l) for l in (queue_vault / ".memexlab" / "log.jsonl").read_text().splitlines()]
    assert [e["action"] for e in lines] == ["capture_note", "complete_queue_item"]


def test_complete_refuses_empty_result(queue_vault):
    with pytest.raises(ValueError, match="non-empty result note"):
        queue_mod.complete_queue_item(Vault(queue_vault), "summarize-memory", "x", "   ")
    meta, _ = parse_frontmatter((queue_vault / "queue" / "summarize-memory.md").read_text())
    assert meta["status"] == "pending"  # untouched


def test_complete_refuses_done_cancelled_and_non_items(queue_vault):
    v = Vault(queue_vault)
    with pytest.raises(ValueError, match="only pending / claimed"):
        queue_mod.complete_queue_item(v, "old-task", "t", "b")
    with pytest.raises(ValueError, match="not a queue item"):
        queue_mod.complete_queue_item(v, "stray", "t", "b")
    with pytest.raises(ValueError, match="no queue item"):
        queue_mod.complete_queue_item(v, "missing", "t", "b")


def test_item_name_cannot_escape_queue_dir(queue_vault):
    with pytest.raises(ValueError, match="no queue item"):
        queue_mod.complete_queue_item(Vault(queue_vault), "../concepts/governed-memory", "t", "b")


def test_canonical_untouched_by_completion(queue_vault):
    before = (queue_vault / "concepts" / "governed-memory.md").read_text()
    queue_mod.complete_queue_item(Vault(queue_vault), "summarize-memory", "t", "b")
    assert (queue_vault / "concepts" / "governed-memory.md").read_text() == before


def test_server_tools(queue_vault):
    from memexlab_mcp import server

    server.configure(str(queue_vault))
    assert [r["item"] for r in server.list_queue()] == ["summarize-memory"]
    res = server.complete_queue_item("summarize-memory", "Summary", "result body")
    assert res["status"] == "done"
    assert server.list_queue() == []
