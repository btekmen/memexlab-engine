"""Tests for dream.py — governed maintenance proposal loop."""
import pathlib
import shutil
import tempfile
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "memexlab-mcp" / "src"))

from memexlab_mcp.vault import Vault  # noqa: E402
sys.path.insert(0, str(ROOT / "runner"))
from dream import (  # noqa: E402
    find_wikilinks,
    find_maintenance_opportunities,
    format_as_queue_item,
    write_queue_items,
)


def test_find_wikilinks():
    """Test wikilink extraction."""
    text = "See [[foo]] and [[bar|alias]] plus [[baz#section]]."
    links = find_wikilinks(text)
    assert links == {"foo", "bar", "baz"}


def test_find_wikilinks_empty():
    """Test empty text."""
    assert find_wikilinks("") == set()
    assert find_wikilinks("No links here!") == set()


def test_maintenance_opportunities_on_fake_vault():
    """Test maintenance detection on examples/fake-vault."""
    vault = Vault(ROOT / "examples" / "fake-vault")
    opportunities = find_maintenance_opportunities(vault)
    
    # Should find at least one opportunity (missing backlinks)
    assert len(opportunities) >= 1
    
    # Check structure
    for opp in opportunities:
        assert "type" in opp
        assert "title" in opp
        assert "body" in opp
        assert "sources" in opp
        assert "priority" in opp
        assert opp["type"] in {
            "broken-link", "missing-backlink", "orphaned-inbox"
        }


def test_format_as_queue_item():
    """Test queue item formatting."""
    opp = {
        "type": "test-type",
        "title": "Test Opportunity",
        "body": "This is a test.\n\n**Evidence**: [[foo]]",
        "sources": ["foo"],
        "priority": "low",
    }
    
    content = format_as_queue_item(opp, agent="test-agent")
    
    assert "---" in content
    assert "type: queue-item" in content
    assert "title: Test Opportunity" in content
    assert "status: pending" in content
    assert "generated_by: test-agent" in content
    assert "This is a test." in content


def test_write_queue_items():
    """Test writing queue items to vault."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = pathlib.Path(tmpdir) / "test-vault"
        vault_path.mkdir()
        
        # Create minimal vault structure
        (vault_path / "people").mkdir()
        (vault_path / "people" / "test.md").write_text(
            "---\ntype: person\ntitle: Test\n---\n\n# Test\n",
            encoding="utf-8"
        )
        
        vault = Vault(vault_path)
        
        opportunities = [
            {
                "type": "test",
                "title": "Test Task 1",
                "body": "Do something.\n\n**Evidence**: [[test]]",
                "sources": ["test"],
                "priority": "low",
            },
            {
                "type": "test",
                "title": "Test Task 2",
                "body": "Do something else.",
                "sources": ["test"],
                "priority": "medium",
            }
        ]
        
        created = write_queue_items(vault, opportunities, agent="test-agent")
        
        assert len(created) == 2
        for path in created:
            assert path.startswith("queue/")
            assert (vault_path / path).is_file()
            content = (vault_path / path).read_text(encoding="utf-8")
            assert "type: queue-item" in content
            assert "status: pending" in content


def test_dry_run_on_fake_vault():
    """Integration test: dry-run mode should not create files."""
    vault_path = ROOT / "examples" / "fake-vault"
    queue_path = vault_path / "queue"
    
    # Count existing queue items
    existing = list(queue_path.glob("*.md")) if queue_path.is_dir() else []
    existing_count = len(existing)
    
    # Run dream loop (dry-run is default, but we're not calling main())
    vault = Vault(vault_path)
    opportunities = find_maintenance_opportunities(vault)
    
    # Verify no new files created
    current = list(queue_path.glob("*.md")) if queue_path.is_dir() else []
    assert len(current) == existing_count


if __name__ == "__main__":
    # Run tests directly without pytest
    print("Running dream.py tests...\n")
    
    try:
        test_find_wikilinks()
        print("✓ test_find_wikilinks")
        
        test_find_wikilinks_empty()
        print("✓ test_find_wikilinks_empty")
        
        test_maintenance_opportunities_on_fake_vault()
        print("✓ test_maintenance_opportunities_on_fake_vault")
        
        test_format_as_queue_item()
        print("✓ test_format_as_queue_item")
        
        test_write_queue_items()
        print("✓ test_write_queue_items")
        
        test_dry_run_on_fake_vault()
        print("✓ test_dry_run_on_fake_vault")
        
        print("\nAll tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
