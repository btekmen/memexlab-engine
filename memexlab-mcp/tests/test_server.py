import asyncio

from memexlab_mcp import server


def test_tool_registry_exact():
    tools = asyncio.run(server.mcp.list_tools())
    assert sorted(t.name for t in tools) == [
        "capture_note", "complete_queue_item", "list_queue",
        "read_note", "search_vault", "vault_info",
    ]


def test_tools_operate_on_configured_vault(fixture_vault):
    server.configure(str(fixture_vault))
    info = server.vault_info()
    assert info["notes"] == 3 and info["write_dir"] == "inbox"
    hits = server.search_vault("governed memory")
    assert hits[0]["slug"] == "governed-memory"
    note = server.read_note("governed-memory")
    assert note["path"] == "concepts/governed-memory.md"
    res = server.capture_note("From Test", "body", sources=["governed-memory"])
    assert res["path"].startswith("inbox/")


def test_main_requires_vault(monkeypatch, capsys):
    monkeypatch.delenv("MEMEXLAB_VAULT", raising=False)
    monkeypatch.setattr("sys.argv", ["memexlab-mcp"])
    try:
        server.main()
        raised = False
    except SystemExit as e:
        raised = e.code != 0
    assert raised
