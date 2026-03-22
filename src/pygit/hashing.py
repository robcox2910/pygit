"""Hashing -- fingerprints for content.

Every piece of content gets a unique fingerprint (hash). The same
content always gets the same fingerprint. Different content gets
different fingerprints. This is the foundation of everything in Git.

We use SHA-1 (like real Git) to produce 40-character hex strings.
"""

import hashlib

HASH_LENGTH = 40


def hash_content(content: str) -> str:
    """Calculate the SHA-1 hash of a string.

    Think of this as taking a fingerprint of the content. The same
    content always produces the same fingerprint.

    Args:
        content: The text to hash.

    Returns:
        A 40-character hexadecimal hash string.

    """
    return hashlib.sha1(content.encode("utf-8")).hexdigest()  # noqa: S324


def hash_bytes(data: bytes) -> str:
    """Calculate the SHA-1 hash of raw bytes.

    Args:
        data: The bytes to hash.

    Returns:
        A 40-character hexadecimal hash string.

    """
    return hashlib.sha1(data).hexdigest()  # noqa: S324
