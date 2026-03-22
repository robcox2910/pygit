"""Commits -- diary entries for your project.

A commit records a moment in time: what the project looked like (the
tree), who made the change (the author), when it happened (the
timestamp), and why (the message). Each commit points back to its
parent, forming a chain of history.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from pygit.hashing import hash_content


@dataclass(frozen=True, slots=True)
class Commit:
    """A snapshot of the project at a moment in time.

    Args:
        tree_hash: The hash of the tree representing the project state.
        parent_hash: The hash of the previous commit (None for first commit).
        author: Who made this commit.
        timestamp: When this commit was made.
        message: Why this commit was made.
        commit_hash: The hash of this commit itself.

    """

    tree_hash: str
    parent_hash: str | None
    author: str
    timestamp: str
    message: str
    commit_hash: str


def create_commit(
    tree_hash: str,
    parent_hash: str | None,
    message: str,
    author: str = "Anonymous",
) -> tuple[str, str]:
    """Create a new commit object.

    Args:
        tree_hash: The hash of the root tree.
        parent_hash: The hash of the parent commit (None for first).
        message: The commit message.
        author: The author's name.

    Returns:
        A tuple of (commit_hash, serialized_commit_content).

    """
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    data = {
        "tree": tree_hash,
        "parent": parent_hash,
        "author": author,
        "timestamp": timestamp,
        "message": message,
    }
    content = json.dumps(data)
    commit_hash = hash_content(content)
    return commit_hash, content


def parse_commit(content: str) -> Commit:
    """Deserialize a commit from its stored content.

    Args:
        content: The JSON-serialized commit content.

    Returns:
        A Commit object.

    """
    data: dict[str, str | None] = json.loads(content)
    return Commit(
        tree_hash=str(data["tree"]),
        parent_hash=str(data["parent"]) if data.get("parent") else None,
        author=str(data.get("author", "Unknown")),
        timestamp=str(data.get("timestamp", "")),
        message=str(data.get("message", "")),
        commit_hash=hash_content(content),
    )
