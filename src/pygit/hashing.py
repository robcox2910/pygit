"""Hashing -- fingerprints for content.

Every piece of content gets a unique fingerprint (hash). The same
content always gets the same fingerprint. Different content gets
different fingerprints. This is the foundation of everything in Git.

We use SHA-1 (like real Git) to produce 40-character hex strings.

Before taking the fingerprint, Git sticks a little **label** on the
front saying what kind of object it is and how big it is -- for a file
saying ``hello``, the label is ``blob 6`` followed by a zero byte. We do
exactly the same, which means:

- a file and a tree can never get the same fingerprint by accident, even
  if their bytes happen to match (the labels differ), and
- our file (blob) fingerprints are *identical* to real Git's -- try
  ``git hash-object`` on the same file!
"""

import hashlib

HASH_LENGTH = 40


def object_header(object_type: str, data: bytes) -> bytes:
    r"""Make the label Git puts in front of every object: ``<type> <size>`` and a zero byte.

    Args:
        object_type: What kind of object this is ("blob", "tree" or "commit").
        data: The object's content.

    Returns:
        The header bytes, for example ``b"blob 6\x00"``.

    """
    return f"{object_type} {len(data)}\0".encode()


def hash_object(object_type: str, data: bytes) -> str:
    """Take the fingerprint of an object: SHA-1 of its label plus its content.

    Args:
        object_type: What kind of object this is ("blob", "tree" or "commit").
        data: The object's content.

    Returns:
        A 40-character hexadecimal hash string.

    """
    return hashlib.sha1(object_header(object_type, data) + data).hexdigest()  # noqa: S324
