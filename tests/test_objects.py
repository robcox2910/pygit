"""Tests for the object store module."""

import pytest

from pygit.errors import ObjectNotFoundError
from pygit.objects import ObjectStore

SAMPLE_CONTENT = "Hello, world!"
DIFFERENT_CONTENT = "Goodbye, world!"
NONEXISTENT_HASH = "0" * 40


class TestObjectStore:
    """Verify that the object store reads and writes blobs correctly."""

    def test_write_blob_returns_hash(self, tmp_path: object) -> None:
        """Return a hash string when writing a blob."""
        store = ObjectStore(tmp_path)  # type: ignore[arg-type]
        blob_hash = store.write_blob(SAMPLE_CONTENT)
        assert isinstance(blob_hash, str)
        assert len(blob_hash) > 0

    def test_read_blob_returns_content(self, tmp_path: object) -> None:
        """Retrieve the original content by its hash."""
        store = ObjectStore(tmp_path)  # type: ignore[arg-type]
        blob_hash = store.write_blob(SAMPLE_CONTENT)
        content = store.read_blob(blob_hash)
        assert content == SAMPLE_CONTENT

    def test_read_nonexistent_raises(self, tmp_path: object) -> None:
        """Raise ObjectNotFoundError for a hash that does not exist."""
        store = ObjectStore(tmp_path)  # type: ignore[arg-type]
        with pytest.raises(ObjectNotFoundError):
            store.read_blob(NONEXISTENT_HASH)

    def test_exists_returns_true_for_stored_blob(self, tmp_path: object) -> None:
        """Return True when the blob has been written."""
        store = ObjectStore(tmp_path)  # type: ignore[arg-type]
        blob_hash = store.write_blob(SAMPLE_CONTENT)
        assert store.exists(blob_hash) is True

    def test_exists_returns_false_for_missing_blob(self, tmp_path: object) -> None:
        """Return False when the blob does not exist."""
        store = ObjectStore(tmp_path)  # type: ignore[arg-type]
        assert store.exists(NONEXISTENT_HASH) is False

    def test_same_content_same_hash(self, tmp_path: object) -> None:
        """Return the same hash when writing identical content twice."""
        store = ObjectStore(tmp_path)  # type: ignore[arg-type]
        first = store.write_blob(SAMPLE_CONTENT)
        second = store.write_blob(SAMPLE_CONTENT)
        assert first == second

    def test_different_content_different_hash(self, tmp_path: object) -> None:
        """Return different hashes for different content."""
        store = ObjectStore(tmp_path)  # type: ignore[arg-type]
        first = store.write_blob(SAMPLE_CONTENT)
        second = store.write_blob(DIFFERENT_CONTENT)
        assert first != second
