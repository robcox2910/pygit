"""Repository -- the diary that holds everything.

The repository is the `.pygit` folder in your project. It stores all
objects (blobs, trees, commits), tracks branches, and maintains the
staging area. This module ties everything together.
"""

import json
from pathlib import Path

from pygit.commit import Commit, create_commit, parse_commit
from pygit.errors import RepositoryError
from pygit.objects import ObjectStore
from pygit.tree import TreeEntry, build_tree

PYGIT_DIR = ".pygit"
OBJECTS_DIR = "objects"
REFS_DIR = "refs/heads"
HEAD_FILE = "HEAD"
INDEX_FILE = "index"
DEFAULT_BRANCH = "main"


class Repository:
    """A PyGit repository.

    Manage the complete version control lifecycle: init, add, commit,
    log, branch, and status.

    """

    __slots__ = ("_path", "_pygit_dir", "_store")

    def __init__(self, path: str | Path) -> None:
        """Open an existing repository.

        Args:
            path: The project root directory.

        Raises:
            RepositoryError: If no `.pygit` directory exists.

        """
        self._path = Path(path).resolve()
        self._pygit_dir = self._path / PYGIT_DIR
        if not self._pygit_dir.exists():
            msg = f"Not a pygit repository: {self._path}"
            raise RepositoryError(msg)
        self._store = ObjectStore(self._pygit_dir / OBJECTS_DIR)

    @classmethod
    def init(cls, path: str | Path) -> Repository:
        """Create a new repository in the given directory.

        Creates the `.pygit` directory structure with objects, refs,
        HEAD, and an empty index.

        Args:
            path: The project root directory.

        Returns:
            The newly created Repository.

        """
        root = Path(path).resolve()
        pygit_dir = root / PYGIT_DIR

        if pygit_dir.exists():
            msg = f"Repository already exists: {root}"
            raise RepositoryError(msg)

        # Create directory structure.
        (pygit_dir / OBJECTS_DIR).mkdir(parents=True)
        (pygit_dir / REFS_DIR).mkdir(parents=True)

        # Create HEAD pointing to main.
        (pygit_dir / HEAD_FILE).write_text(f"ref: {REFS_DIR}/{DEFAULT_BRANCH}\n", encoding="utf-8")

        # Create empty index.
        (pygit_dir / INDEX_FILE).write_text("{}", encoding="utf-8")

        return cls(root)

    @property
    def path(self) -> Path:
        """Return the project root path."""
        return self._path

    def add(self, file_path: str) -> str:
        """Stage a file for the next commit.

        Read the file's content, store it as a blob, and record it
        in the index (staging area).

        Args:
            file_path: Path to the file (relative to project root).

        Returns:
            The blob hash of the staged file.

        Raises:
            RepositoryError: If the file doesn't exist.

        """
        full_path = self._path / file_path
        if not full_path.is_file():
            msg = f"File not found: {file_path}"
            raise RepositoryError(msg)

        content = full_path.read_text(encoding="utf-8")
        blob_hash = self._store.write_blob(content)

        # Update the index.
        index = self._read_index()
        index[file_path] = blob_hash
        self._write_index(index)

        return blob_hash

    def commit(self, message: str, author: str = "Anonymous") -> str:
        """Create a commit from the current staging area.

        Build a tree from the index, create a commit pointing to it,
        update the current branch, and clear the index.

        Args:
            message: The commit message.
            author: The author's name.

        Returns:
            The commit hash.

        Raises:
            RepositoryError: If the staging area is empty.

        """
        index = self._read_index()
        if not index:
            msg = "Nothing to commit (staging area is empty)"
            raise RepositoryError(msg)

        # Build the tree from the index.
        entries = [
            TreeEntry(name=name, entry_type="blob", hash=blob_hash)
            for name, blob_hash in index.items()
        ]
        tree_hash, tree_content = build_tree(entries)
        self._store.write_blob(tree_content)

        # Get the parent commit (current branch tip).
        parent_hash = self._get_branch_tip()

        # Create the commit.
        commit_hash, commit_content = create_commit(
            tree_hash=tree_hash,
            parent_hash=parent_hash,
            message=message,
            author=author,
        )
        self._store.write_blob(commit_content)

        # Update the current branch to point to the new commit.
        self._set_branch_tip(commit_hash)

        # Clear the index.
        self._write_index({})

        return commit_hash

    def log(self) -> list[Commit]:
        """Return the commit history, newest first.

        Walk the parent chain from the current branch tip back to
        the first commit.

        Returns:
            A list of Commit objects, newest first.

        """
        commits: list[Commit] = []
        current_hash = self._get_branch_tip()

        while current_hash:
            content = self._store.read_blob(current_hash)
            commit = parse_commit(content)
            commits.append(commit)
            current_hash = commit.parent_hash

        return commits

    def status(self) -> dict[str, str]:
        """Return the current staging area contents.

        Returns:
            A dict mapping file paths to blob hashes.

        """
        return self._read_index()

    def create_branch(self, name: str) -> None:
        """Create a new branch pointing to the current commit.

        Args:
            name: The branch name.

        Raises:
            RepositoryError: If the branch already exists.

        """
        branch_path = self._pygit_dir / REFS_DIR / name
        if branch_path.exists():
            msg = f"Branch already exists: {name}"
            raise RepositoryError(msg)
        tip = self._get_branch_tip()
        branch_path.write_text(tip or "", encoding="utf-8")

    def list_branches(self) -> list[str]:
        """Return all branch names."""
        refs_dir = self._pygit_dir / REFS_DIR
        return sorted(p.name for p in refs_dir.iterdir() if p.is_file())

    def current_branch(self) -> str:
        """Return the name of the current branch."""
        head = (self._pygit_dir / HEAD_FILE).read_text(encoding="utf-8").strip()
        if head.startswith("ref: "):
            return head.removeprefix(f"ref: {REFS_DIR}/")
        return head

    def switch_branch(self, name: str) -> None:
        """Switch to a different branch.

        Args:
            name: The branch name to switch to.

        Raises:
            RepositoryError: If the branch doesn't exist.

        """
        branch_path = self._pygit_dir / REFS_DIR / name
        if not branch_path.exists():
            msg = f"Branch not found: {name}"
            raise RepositoryError(msg)
        (self._pygit_dir / HEAD_FILE).write_text(f"ref: {REFS_DIR}/{name}\n", encoding="utf-8")

    # -- Internal helpers --

    def _read_index(self) -> dict[str, str]:
        """Read the staging area from disk."""
        index_path = self._pygit_dir / INDEX_FILE
        if not index_path.exists():
            return {}
        content = index_path.read_text(encoding="utf-8")
        result: dict[str, str] = json.loads(content)
        return result

    def _write_index(self, index: dict[str, str]) -> None:
        """Write the staging area to disk."""
        index_path = self._pygit_dir / INDEX_FILE
        index_path.write_text(json.dumps(index), encoding="utf-8")

    def _get_branch_tip(self) -> str | None:
        """Return the commit hash at the tip of the current branch."""
        branch = self.current_branch()
        branch_path = self._pygit_dir / REFS_DIR / branch
        if not branch_path.exists():
            return None
        tip = branch_path.read_text(encoding="utf-8").strip()
        return tip or None

    def _set_branch_tip(self, commit_hash: str) -> None:
        """Update the current branch to point to a commit."""
        branch = self.current_branch()
        branch_path = self._pygit_dir / REFS_DIR / branch
        branch_path.write_text(commit_hash, encoding="utf-8")
