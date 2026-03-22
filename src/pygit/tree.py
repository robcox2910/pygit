"""Trees -- snapshots of directory structure.

A tree is like a table of contents: it lists which files (blobs) and
subdirectories (other trees) exist, along with their names and hashes.
When you commit, Git builds a tree of the entire project.
"""

import json
from dataclasses import dataclass

from pygit.hashing import hash_content


@dataclass(frozen=True, slots=True)
class TreeEntry:
    """One entry in a tree (a file or subdirectory).

    Args:
        name: The filename or directory name.
        entry_type: "blob" for files, "tree" for directories.
        hash: The SHA-1 hash of the blob or sub-tree.

    """

    name: str
    entry_type: str
    hash: str


def build_tree(entries: list[TreeEntry]) -> tuple[str, str]:
    """Build a tree object from a list of entries.

    Sorts entries by name for consistency (same entries always produce
    the same tree hash, regardless of insertion order).

    Args:
        entries: The tree entries (files and directories).

    Returns:
        A tuple of (tree_hash, serialized_tree_content).

    """
    sorted_entries = sorted(entries, key=lambda e: e.name)
    content = json.dumps(
        [{"name": e.name, "type": e.entry_type, "hash": e.hash} for e in sorted_entries]
    )
    tree_hash = hash_content(content)
    return tree_hash, content


def parse_tree(content: str) -> list[TreeEntry]:
    """Deserialize a tree from its stored content.

    Args:
        content: The JSON-serialized tree content.

    Returns:
        A list of TreeEntry objects.

    """
    raw: list[dict[str, str]] = json.loads(content)
    return [TreeEntry(name=e["name"], entry_type=e["type"], hash=e["hash"]) for e in raw]
