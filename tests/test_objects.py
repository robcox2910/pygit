"""Tests for the object store module."""

from pathlib import Path

import pytest

from pygit.errors import ObjectNotFoundError, ObjectTypeError
from pygit.hashing import hash_object
from pygit.objects import ObjectStore

SAMPLE = b"Hello, world!"
DIFFERENT = b"Goodbye, world!"
NONEXISTENT_HASH = "0" * 40


class TestObjectStore:
    """Objects go in labelled with their type, and come out checked."""

    def test_write_returns_the_objects_hash(self, tmp_path: Path) -> None:
        """Writing an object returns the fingerprint of its labelled bytes."""
        store = ObjectStore(tmp_path)
        assert store.write_object("blob", SAMPLE) == hash_object("blob", SAMPLE)

    def test_read_returns_the_original_bytes(self, tmp_path: Path) -> None:
        """Reading hands back exactly what was stored, label removed."""
        store = ObjectStore(tmp_path)
        object_hash = store.write_object("blob", SAMPLE)
        assert store.read_object(object_hash, "blob") == SAMPLE

    def test_binary_content_round_trips(self, tmp_path: Path) -> None:
        """Bytes that aren't text (like a picture) are stored safely."""
        store = ObjectStore(tmp_path)
        picture = bytes(range(256))
        assert store.read_object(store.write_object("blob", picture), "blob") == picture

    def test_reading_with_the_wrong_type_raises(self, tmp_path: Path) -> None:
        """Asking for a tree when the label says blob is an error, not a muddle."""
        store = ObjectStore(tmp_path)
        object_hash = store.write_object("blob", SAMPLE)
        with pytest.raises(ObjectTypeError, match="blob"):
            store.read_object(object_hash, "tree")

    def test_read_nonexistent_raises(self, tmp_path: Path) -> None:
        """Reading a hash that was never stored raises ObjectNotFoundError."""
        store = ObjectStore(tmp_path)
        with pytest.raises(ObjectNotFoundError):
            store.read_object(NONEXISTENT_HASH, "blob")

    def test_exists(self, tmp_path: Path) -> None:
        """exists() is True only for stored objects."""
        store = ObjectStore(tmp_path)
        object_hash = store.write_object("blob", SAMPLE)
        assert store.exists(object_hash)
        assert not store.exists(NONEXISTENT_HASH)

    def test_storing_twice_is_a_no_op(self, tmp_path: Path) -> None:
        """Identical objects share one file (content-addressable)."""
        store = ObjectStore(tmp_path)
        assert store.write_object("blob", SAMPLE) == store.write_object("blob", SAMPLE)

    def test_different_content_different_objects(self, tmp_path: Path) -> None:
        """Different content is stored under different fingerprints."""
        store = ObjectStore(tmp_path)
        assert store.write_object("blob", SAMPLE) != store.write_object("blob", DIFFERENT)

    def test_objects_are_filed_under_their_first_two_hash_characters(self, tmp_path: Path) -> None:
        """Objects live in a folder named after the first two characters of their hash."""
        store = ObjectStore(tmp_path)
        object_hash = store.write_object("blob", SAMPLE)
        assert (tmp_path / object_hash[:2] / object_hash[2:]).is_file()
