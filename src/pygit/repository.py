"""Repository -- the diary that holds everything.

The repository is the `.pygit` folder in your project. It stores all
objects (blobs, trees, commits), tracks branches, and maintains the
staging area. This module ties everything together.
"""

import json
import unicodedata
from pathlib import Path

from pygit.commit import Commit, create_commit, parse_commit
from pygit.errors import RepositoryError
from pygit.objects import ObjectStore
from pygit.tree import TreeEntry, build_tree, parse_tree

PYGIT_DIR = ".pygit"
OBJECTS_DIR = "objects"
REFS_DIR = "refs/heads"
HEAD_FILE = "HEAD"
INDEX_FILE = "index"
DEFAULT_BRANCH = "main"
# Most file systems refuse a file name longer than 255 bytes.
MAX_BRANCH_NAME_BYTES = 255


def _check_branch_name(name: str) -> None:
    r"""Refuse a branch name that isn't one plain, visible file name.

    A branch is a file in ``.pygit/refs/heads``, named after the branch, so
    the name must be safe to use as a file name there: not empty, not ``.``
    or ``..``, no ``/`` or ``\`` (they would reach into other folders), no
    spaces or invisible characters (HEAD is a line of text, and they get
    lost), and short enough for the file system.

    Raises:
        RepositoryError: If the name isn't allowed.

    """
    if (
        name in {"", ".", ".."}
        or "/" in name
        or "\\" in name
        or not name.isprintable()
        or any(char.isspace() for char in name)
        or len(name.encode()) > MAX_BRANCH_NAME_BYTES
    ):
        msg = f"Invalid branch name: {name!r}"
        raise RepositoryError(msg)


def _same_name_key(name: str) -> str:
    """Return a name as Mac and Windows compare file names: ignoring case and accent spelling."""
    return unicodedata.normalize("NFD", unicodedata.normalize("NFD", name).casefold())


class Repository:
    """A PyGit repository -- your project's diary.

    Like a diary that keeps every version of your story, the repository
    remembers all your project's snapshots, tracks its branches, and
    holds the staging area where you gather changes. It ties everything
    together and manages the complete version control lifecycle: init,
    add, commit, log, branch, and status.

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

        # Files are stored as raw bytes, so pictures and other non-text
        # files work too.
        blob_hash = self._store.write_object("blob", full_path.read_bytes())

        # Update the index.
        index = self._read_index()
        index[Path(file_path).as_posix()] = blob_hash  # "./src/a.py" -> "src/a.py"
        self._write_index(index)

        return blob_hash

    def commit(self, message: str, author: str = "Anonymous") -> str:
        """Create a commit from the current staging area.

        A commit is a *full snapshot*, like a photo of every room in
        the house -- not just the room you tidied. So we start from the
        parent commit's snapshot and lay the staged changes on top,
        which means files committed earlier stay in the picture. Then
        we create a commit pointing to the new tree, update the current
        branch, and clear the index.

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

        # Get the parent commit (current branch tip).
        parent_hash = self._get_branch_tip()

        # Start from the parent's snapshot, then overlay the staged
        # changes so previously committed files are not lost.
        snapshot = self._parent_tree_entries(parent_hash)
        snapshot.update(index)

        # Build a tree for every folder, from the full snapshot.
        tree_hash = self._write_tree(snapshot)

        # Create the commit.
        commit_hash, commit_content = create_commit(
            tree_hash=tree_hash,
            parent_hash=parent_hash,
            message=message,
            author=author,
        )
        self._store.write_object("commit", commit_content.encode())

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
            content = self._store.read_object(current_hash, "commit").decode()
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
            RepositoryError: If the name isn't allowed, or the branch already
                exists, or another branch has the same name in different
                capitals (on a Mac or Windows they would share one file).

        """
        _check_branch_name(name)
        existing = self.list_branches()
        if name in existing:
            msg = f"Branch already exists: {name}"
            raise RepositoryError(msg)
        for other in sorted({*existing, self.current_branch()}):
            if other != name and _same_name_key(other) == _same_name_key(name):
                msg = f"Branch {name!r} differs from {other!r} only in capitals or accents"
                raise RepositoryError(msg)
        tip = self._get_branch_tip()
        try:
            (self._pygit_dir / REFS_DIR / name).write_text(tip or "", encoding="utf-8")
        except OSError as exc:  # e.g. a Mac refuses letters newer than it knows
            msg = f"Invalid branch name: {name!r} ({exc.strerror})"
            raise RepositoryError(msg) from exc

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

        Note: this only moves HEAD to point at the branch -- it does
        not yet update the files in your working directory to match that
        branch's snapshot (a real ``checkout``). Restoring files on
        switch is a great exercise to try yourself!

        Args:
            name: The branch name to switch to.

        Raises:
            RepositoryError: If the name isn't allowed, or the branch doesn't exist.

        """
        _check_branch_name(name)
        # Look for the exact name in the list: asking the file system would
        # let "MAIN" find "main" on a Mac.
        if name not in self.list_branches():
            msg = f"Branch not found: {name}"
            raise RepositoryError(msg)
        (self._pygit_dir / HEAD_FILE).write_text(f"ref: {REFS_DIR}/{name}\n", encoding="utf-8")

    # -- Internal helpers --

    def _parent_tree_entries(self, parent_hash: str | None) -> dict[str, str]:
        """Return a commit's snapshot as a mapping of file path to blob hash."""
        if parent_hash is None:
            return {}
        parent = parse_commit(self._store.read_object(parent_hash, "commit").decode())
        return self._read_tree(parent.tree_hash)

    def _write_tree(self, files: dict[str, str]) -> str:
        """Store a tree for a folder (and, inside it, one for every sub-folder).

        ``files`` maps paths like ``"src/lib/util.py"`` to blob hashes. Files
        directly in this folder become blob entries; everything under a
        sub-folder is gathered up and turned into that sub-folder's own tree
        first -- like a table of contents with a mini table of contents for
        each chapter.

        Returns:
            The hash of this folder's tree.

        """
        entries: list[TreeEntry] = []
        sub_folders: dict[str, dict[str, str]] = {}
        for path, blob_hash in files.items():
            first, slash, rest = path.partition("/")
            if slash:
                sub_folders.setdefault(first, {})[rest] = blob_hash
            else:
                entries.append(TreeEntry(name=first, entry_type="blob", hash=blob_hash))
        for name, contents in sub_folders.items():
            entries.append(TreeEntry(name=name, entry_type="tree", hash=self._write_tree(contents)))
        _tree_hash, tree_content = build_tree(entries)
        return self._store.write_object("tree", tree_content.encode())

    def _read_tree(self, tree_hash: str, prefix: str = "") -> dict[str, str]:
        """Flatten a tree (and its sub-trees) back into ``{path: blob hash}``."""
        files: dict[str, str] = {}
        for entry in parse_tree(self._store.read_object(tree_hash, "tree").decode()):
            path = f"{prefix}{entry.name}"
            if entry.entry_type == "tree":
                files.update(self._read_tree(entry.hash, prefix=f"{path}/"))
            else:
                files[path] = entry.hash
        return files

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
