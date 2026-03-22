"""Tests for the tree module."""

from pygit.tree import TreeEntry, build_tree, parse_tree

BLOB_TYPE = "blob"
HASH_A = "a" * 40
HASH_B = "b" * 40
HASH_C = "c" * 40


class TestBuildTree:
    """Verify that build_tree produces sorted, deterministic trees."""

    def test_entries_sorted_by_name(self) -> None:
        """Sort entries alphabetically by name."""
        entries = [
            TreeEntry(name="zebra.txt", entry_type=BLOB_TYPE, hash=HASH_A),
            TreeEntry(name="apple.txt", entry_type=BLOB_TYPE, hash=HASH_B),
        ]
        _tree_hash, content = build_tree(entries)
        parsed = parse_tree(content)
        names = [e.name for e in parsed]
        assert names == ["apple.txt", "zebra.txt"]

    def test_same_entries_same_hash(self) -> None:
        """Produce the same hash regardless of insertion order."""
        entries_forward = [
            TreeEntry(name="a.txt", entry_type=BLOB_TYPE, hash=HASH_A),
            TreeEntry(name="b.txt", entry_type=BLOB_TYPE, hash=HASH_B),
        ]
        entries_reverse = [
            TreeEntry(name="b.txt", entry_type=BLOB_TYPE, hash=HASH_B),
            TreeEntry(name="a.txt", entry_type=BLOB_TYPE, hash=HASH_A),
        ]
        hash_forward, _ = build_tree(entries_forward)
        hash_reverse, _ = build_tree(entries_reverse)
        assert hash_forward == hash_reverse

    def test_parse_tree_round_trips(self) -> None:
        """Serialize and deserialize a tree without data loss."""
        entries = [
            TreeEntry(name="file.txt", entry_type=BLOB_TYPE, hash=HASH_A),
            TreeEntry(name="dir", entry_type="tree", hash=HASH_C),
        ]
        _tree_hash, content = build_tree(entries)
        parsed = parse_tree(content)
        assert len(parsed) == len(entries)
        # After sorting, dir comes before file.txt.
        assert parsed[0].name == "dir"
        assert parsed[0].entry_type == "tree"
        assert parsed[0].hash == HASH_C
        assert parsed[1].name == "file.txt"
        assert parsed[1].entry_type == BLOB_TYPE
        assert parsed[1].hash == HASH_A

    def test_different_entries_different_hash(self) -> None:
        """Produce different hashes for different sets of entries."""
        entries_a = [TreeEntry(name="a.txt", entry_type=BLOB_TYPE, hash=HASH_A)]
        entries_b = [TreeEntry(name="b.txt", entry_type=BLOB_TYPE, hash=HASH_B)]
        hash_a, _ = build_tree(entries_a)
        hash_b, _ = build_tree(entries_b)
        assert hash_a != hash_b

    def test_empty_tree(self) -> None:
        """Build a tree with no entries."""
        tree_hash, content = build_tree([])
        assert isinstance(tree_hash, str)
        assert len(tree_hash) > 0
        parsed = parse_tree(content)
        assert parsed == []
