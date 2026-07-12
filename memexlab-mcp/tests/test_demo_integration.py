import pathlib
import shutil

from memexlab_mcp.demo import run_demo

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
FAKE_VAULT = REPO_ROOT / "examples" / "fake-vault"


def test_demo_against_fake_vault_copy(tmp_path):
    vault = tmp_path / "fake-vault"
    shutil.copytree(FAKE_VAULT, vault)
    result = run_demo(str(vault))
    assert result["hits"] >= 1
    assert result["captured"].startswith("inbox/")
    assert result["canonical_changed"] is False
    assert (vault / ".memexlab" / "log.jsonl").exists()
