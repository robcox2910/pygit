"""Tests for the hashing module."""

from pygit.hashing import HASH_LENGTH, hash_bytes, hash_content

EXPECTED_HASH_LENGTH = 40
SAMPLE_CONTENT = "Hello, world!"
DIFFERENT_CONTENT = "Goodbye, world!"
SAMPLE_BYTES = b"Hello, world!"


class TestHashContent:
    """Verify that hash_content produces consistent SHA-1 fingerprints."""

    def test_same_input_same_hash(self) -> None:
        """Return the same hash for identical content."""
        first = hash_content(SAMPLE_CONTENT)
        second = hash_content(SAMPLE_CONTENT)
        assert first == second

    def test_different_input_different_hash(self) -> None:
        """Return different hashes for different content."""
        first = hash_content(SAMPLE_CONTENT)
        second = hash_content(DIFFERENT_CONTENT)
        assert first != second

    def test_hash_is_40_char_hex(self) -> None:
        """Produce a 40-character hexadecimal string."""
        result = hash_content(SAMPLE_CONTENT)
        assert len(result) == EXPECTED_HASH_LENGTH
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_length_constant_matches(self) -> None:
        """Ensure the HASH_LENGTH constant equals 40."""
        assert HASH_LENGTH == EXPECTED_HASH_LENGTH

    def test_empty_string_hashes(self) -> None:
        """Hash an empty string without error."""
        result = hash_content("")
        assert len(result) == EXPECTED_HASH_LENGTH


class TestHashBytes:
    """Verify that hash_bytes produces consistent SHA-1 fingerprints for raw bytes."""

    def test_same_bytes_same_hash(self) -> None:
        """Return the same hash for identical bytes."""
        first = hash_bytes(SAMPLE_BYTES)
        second = hash_bytes(SAMPLE_BYTES)
        assert first == second

    def test_hash_bytes_is_40_char_hex(self) -> None:
        """Produce a 40-character hexadecimal string."""
        result = hash_bytes(SAMPLE_BYTES)
        assert len(result) == EXPECTED_HASH_LENGTH
        assert all(c in "0123456789abcdef" for c in result)
