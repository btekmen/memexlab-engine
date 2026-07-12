import json
import pathlib

import pytest

from memex_cli import llm
from memex_cli.qa import citation_lint, load_lens, qa
from memex_cli.vault import Vault

FAKE_PROVIDER = {"kind": "openai", "url": "http://local", "key": "",
                 "model": "test-model", "route": "local"}


def fake_complete_factory(answer: str):
    calls = []

    def fake_complete(provider, system, user, max_tokens=1000):
        calls.append({"system": system, "user": user, "max_tokens": max_tokens})
        return {"text": answer, "model": provider["model"],
                "usage": {"input": 10, "output": 20}}

    fake_complete.calls = calls
    return fake_complete


@pytest.fixture
def vault(tmp_path: pathlib.Path) -> Vault:
    (tmp_path / "governance.yml").write_text("write_dir: inbox\n", encoding="utf-8")
    (tmp_path / "concepts").mkdir()
    (tmp_path / "concepts" / "governed-memory.md").write_text(
        "---\ntitle: Governed Memory\ntags: [memory]\n---\n"
        "Governed memory keeps agent knowledge durable, citable and auditable.\n",
        encoding="utf-8",
    )
    (tmp_path / "concepts" / "platform-banking.md").write_text(
        "---\ntitle: Platform Banking\n---\nBanks as platforms, not pipes.\n",
        encoding="utf-8",
    )
    return Vault(tmp_path)


def test_provider_resolution_order_and_refusal():
    p = llm.resolve_provider({"MEMEX_MODEL_URL": "http://localhost:8080/v1",
                              "GLM_API_KEY": "g", "ANTHROPIC_API_KEY": "a"})
    assert p["route"] == "local" and p["key"] == ""
    p = llm.resolve_provider({"GLM_API_KEY": "g", "ANTHROPIC_API_KEY": "a"})
    assert p["route"] == "glm" and p["model"] == "glm-5.2"
    p = llm.resolve_provider({"ANTHROPIC_API_KEY": "a"})
    assert p["route"] == "anthropic" and p["model"] == "claude-sonnet-5"
    p = llm.resolve_provider({"GLM_API_KEY": "g", "MEMEX_MODEL": "glm-5.2-air"})
    assert p["model"] == "glm-5.2-air"
    with pytest.raises(RuntimeError, match="deterministic commands"):
        llm.resolve_provider({})


def test_qa_builds_context_and_lints_citations(vault):
    fake = fake_complete_factory(
        "Governed memory is durable and auditable [[governed-memory]].\n\n"
        "It also cites [[nonexistent]] wrongly.")
    res = qa(vault, "what is governed memory", provider=FAKE_PROVIDER, complete=fake)
    assert res["ok"] and res["route"] == "local"
    assert "governed-memory" in res["context_slugs"]
    system = fake.calls[0]["system"]
    assert "[[governed-memory]]" in system and "ONLY the notes" in system
    assert res["citations_total"] == 2 and res["citations_valid"] == 1
    assert res["citations_invalid"] == ["nonexistent"]


def test_strict_fails_on_invalid_or_missing_citations(vault):
    bad = fake_complete_factory("An answer citing [[nowhere]].")
    res = qa(vault, "governed memory", provider=FAKE_PROVIDER, complete=bad, strict=True)
    assert not res["ok"]
    none = fake_complete_factory("An answer with no citations at all.")
    res = qa(vault, "governed memory", provider=FAKE_PROVIDER, complete=none, strict=True)
    assert not res["ok"]


def test_apply_files_answer_with_frontmatter(vault):
    fake = fake_complete_factory("Durable, citable [[governed-memory]].")
    res = qa(vault, "What is governed memory?", provider=FAKE_PROVIDER,
             complete=fake, apply=True)
    assert res["applied"] and res["note"].startswith("_qa/")
    text = (vault.root / res["note"]).read_text()
    assert "type: qa" in text and "model: test-model" in text
    assert "cited_slugs:\n- governed-memory" in text
    assert "# What is governed memory?" in text


def test_lens_loading_builtin_override_and_translate(vault):
    assert "seven key points" in load_lens(vault, "keypoints", None)
    (vault.root / "lenses").mkdir()
    (vault.root / "lenses" / "keypoints.md").write_text("CUSTOM LENS\n", encoding="utf-8")
    assert "CUSTOM LENS" in load_lens(vault, "keypoints", None)
    assert "Turkish" in load_lens(vault, "translate", "Turkish")
    with pytest.raises(ValueError, match="needs --lang"):
        load_lens(vault, "translate", None)
    with pytest.raises(ValueError, match="unknown lens"):
        load_lens(vault, "haiku", None)


def test_view_scoping_and_no_context(vault):
    (vault.root / "views").mkdir()
    (vault.root / "views" / "banking.md").write_text(
        "---\ntype: view\nquery:\n  tags: [banking]\n---\n", encoding="utf-8")
    fake = fake_complete_factory("x")
    res = qa(vault, "governed memory", view="banking",
             provider=FAKE_PROVIDER, complete=fake)
    assert res["action"] == "no-context" and not res["ok"]


def test_citation_lint_paragraphs():
    lint = citation_lint(
        "A long paragraph over eighty characters that discusses governed memory in "
        "detail but cites nothing at all here.\n\nShort.\n\nCited paragraph that is "
        "also over eighty characters long for the lint check [[a]].", {"a"})
    assert lint["uncited_paragraphs"] == 1 and lint["citations_valid"] == 1


def test_cli_end_to_end(vault, capsys, monkeypatch):
    from memex_cli import cli

    monkeypatch.delenv("MEMEX_MODEL_URL", raising=False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    code = cli.main(["qa", "governed memory", "--vault", str(vault.root)])
    _, err = capsys.readouterr()
    assert code == 1 and "deterministic commands" in err

    monkeypatch.setenv("GLM_API_KEY", "test")
    monkeypatch.setattr("memex_cli.qa.llm.complete",
                        fake_complete_factory("Durable [[governed-memory]]."))
    # qa() default arg bound at import; pass through by patching resolve+complete used in cli path
    monkeypatch.setattr("memex_cli.llm.complete",
                        fake_complete_factory("Durable [[governed-memory]]."))
    code = cli.main(["qa", "what is governed memory", "--vault", str(vault.root)])
    out, err = capsys.readouterr()
    assert code == 0 and "Durable [[governed-memory]]." in out
    event = json.loads(err.strip().splitlines()[0])
    assert event["cmd"] == "qa" and event["route"] == "glm" and "answer" not in event
