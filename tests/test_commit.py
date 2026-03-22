"""Tests for the commit module."""

from pygit.commit import create_commit, parse_commit

TREE_HASH_A = "a" * 40
TREE_HASH_B = "b" * 40
PARENT_HASH = "c" * 40
COMMIT_MESSAGE = "Initial commit"
SECOND_MESSAGE = "Add feature"
AUTHOR_NAME = "Test Author"


class TestCreateCommit:
    """Verify that create_commit produces valid commit objects."""

    def test_returns_hash_and_content(self) -> None:
        """Return a tuple of (hash, serialized content)."""
        commit_hash, content = create_commit(
            tree_hash=TREE_HASH_A,
            parent_hash=None,
            message=COMMIT_MESSAGE,
            author=AUTHOR_NAME,
        )
        assert isinstance(commit_hash, str)
        assert len(commit_hash) > 0
        assert isinstance(content, str)
        assert len(content) > 0

    def test_content_contains_tree_hash(self) -> None:
        """Include the tree hash in the serialized content."""
        _commit_hash, content = create_commit(
            tree_hash=TREE_HASH_A,
            parent_hash=None,
            message=COMMIT_MESSAGE,
        )
        assert TREE_HASH_A in content

    def test_content_contains_message(self) -> None:
        """Include the commit message in the serialized content."""
        _commit_hash, content = create_commit(
            tree_hash=TREE_HASH_A,
            parent_hash=None,
            message=COMMIT_MESSAGE,
        )
        assert COMMIT_MESSAGE in content


class TestParseCommit:
    """Verify that parse_commit round-trips with create_commit."""

    def test_round_trip(self) -> None:
        """Deserialize a commit and recover all fields."""
        _commit_hash, content = create_commit(
            tree_hash=TREE_HASH_A,
            parent_hash=None,
            message=COMMIT_MESSAGE,
            author=AUTHOR_NAME,
        )
        commit = parse_commit(content)
        assert commit.tree_hash == TREE_HASH_A
        assert commit.parent_hash is None
        assert commit.message == COMMIT_MESSAGE
        assert commit.author == AUTHOR_NAME

    def test_round_trip_with_parent(self) -> None:
        """Preserve the parent hash through serialization."""
        _commit_hash, content = create_commit(
            tree_hash=TREE_HASH_A,
            parent_hash=PARENT_HASH,
            message=COMMIT_MESSAGE,
            author=AUTHOR_NAME,
        )
        commit = parse_commit(content)
        assert commit.parent_hash == PARENT_HASH

    def test_parent_chain(self) -> None:
        """Create a chain of commits with parent pointers."""
        first_hash, first_content = create_commit(
            tree_hash=TREE_HASH_A,
            parent_hash=None,
            message=COMMIT_MESSAGE,
        )
        second_hash, second_content = create_commit(
            tree_hash=TREE_HASH_B,
            parent_hash=first_hash,
            message=SECOND_MESSAGE,
        )
        first = parse_commit(first_content)
        second = parse_commit(second_content)

        assert first.parent_hash is None
        assert second.parent_hash == first_hash
        assert first.commit_hash == first_hash
        assert second.commit_hash == second_hash
