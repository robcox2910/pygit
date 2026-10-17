"""Tests for the hashing module."""

from pygit.hashing import HASH_LENGTH, hash_object, object_header

EXPECTED_HASH_LENGTH = 40
SAMPLE = b"Hello, world!"
DIFFERENT = b"Goodbye, world!"
# What real Git prints for `printf 'hello\n' | git hash-object --stdin`.
GIT_HASH_OF_HELLO_NEWLINE = "ce013625030ba8dba906f756967f9e9ca394464a"


class TestObjectHeader:
    """Every object is labelled with its type and size before hashing."""

    def test_header_is_type_space_size_then_a_zero_byte(self) -> None:
        """The label looks exactly like real Git's: ``blob 13`` then a zero byte."""
        assert object_header("blob", SAMPLE) == b"blob 13\x00"


class TestHashObject:
    """Fingerprints are stable, sensitive to content, and sensitive to type."""

    def test_same_object_same_hash(self) -> None:
        """Hashing the same object twice gives the same fingerprint."""
        assert hash_object("blob", SAMPLE) == hash_object("blob", SAMPLE)

    def test_different_content_different_hash(self) -> None:
        """Different content gives a different fingerprint."""
        assert hash_object("blob", SAMPLE) != hash_object("blob", DIFFERENT)

    def test_same_bytes_different_type_different_hash(self) -> None:
        """A blob and a tree with identical bytes still get different fingerprints."""
        assert hash_object("blob", SAMPLE) != hash_object("tree", SAMPLE)

    def test_hash_is_40_char_hex(self) -> None:
        """SHA-1 fingerprints are 40 hexadecimal characters."""
        result = hash_object("blob", SAMPLE)
        assert len(result) == EXPECTED_HASH_LENGTH == HASH_LENGTH
        assert all(c in "0123456789abcdef" for c in result)

    def test_blob_hash_matches_real_git(self) -> None:
        """Regression: our blob fingerprints now match ``git hash-object`` exactly."""
        assert hash_object("blob", b"hello\n") == GIT_HASH_OF_HELLO_NEWLINE
