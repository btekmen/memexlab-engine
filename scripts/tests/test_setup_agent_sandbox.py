import json
import pathlib
import subprocess

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO / "scripts" / "setup_agent_sandbox.sh"


def run(*args):
    return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True)


def test_requires_a_vault_source(tmp_path):
    proc = run("--sandbox-root", str(tmp_path / "sb"))
    assert proc.returncode == 1 and "vault-remote" in proc.stderr


def test_dry_run_writes_nothing_and_emits_event(tmp_path):
    sb = tmp_path / "sb"
    proc = run("--sandbox-root", str(sb),
               "--vault-path", str(REPO / "examples" / "fake-vault"), "--with-mcp")
    assert proc.returncode == 0, proc.stderr
    assert "dry-run" in proc.stdout and "HTTPS-only" in proc.stdout
    assert not sb.exists()
    event = json.loads(proc.stderr.strip().splitlines()[-1])
    assert event["cmd"] == "setup_agent_sandbox" and event["mode"] == "dry-run"


def test_apply_places_vault_and_skills(tmp_path):
    sb = tmp_path / "sb"
    proc = run("--sandbox-root", str(sb),
               "--vault-path", str(REPO / "examples" / "fake-vault"), "--apply")
    assert proc.returncode == 0, proc.stderr
    assert (sb / "vault" / "governance.yml").exists() or (sb / "vault").is_dir()
    assert (sb / "vault" / "concepts" / "platform-banking.md").exists()
    assert (sb / "skills" / "memex-query" / "SKILL.md").exists()
    event = json.loads(proc.stderr.strip().splitlines()[-1])
    assert event["mode"] == "apply" and event["mcp"] is False


def test_apply_is_idempotent_for_existing_vault(tmp_path):
    sb = tmp_path / "sb"
    run("--sandbox-root", str(sb),
        "--vault-path", str(REPO / "examples" / "fake-vault"), "--apply")
    marker = sb / "vault" / "inbox"
    marker.mkdir(parents=True, exist_ok=True)
    (marker / "my-note.md").write_text("mine\n", encoding="utf-8")
    proc = run("--sandbox-root", str(sb),
               "--vault-path", str(REPO / "examples" / "fake-vault"), "--apply")
    assert proc.returncode == 0
    assert (marker / "my-note.md").exists()  # existing vault untouched


def test_rejects_both_sources(tmp_path):
    proc = run("--sandbox-root", str(tmp_path / "sb"),
               "--vault-remote", "git@example:v.git",
               "--vault-path", str(REPO / "examples" / "fake-vault"))
    assert proc.returncode == 1 and "not both" in proc.stderr
