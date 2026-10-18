"""Tests for the repository module."""

from pathlib import Path

import pytest

from pygit.commit import parse_commit
from pygit.errors import RepositoryError
from pygit.objects import ObjectStore
from pygit.repository import (
    DEFAULT_BRANCH,
    HEAD_FILE,
    INDEX_FILE,
    OBJECTS_DIR,
    PYGIT_DIR,
    REFS_DIR,
    Repository,
)
from pygit.tree import parse_tree

SAMPLE_FILENAME = "hello.txt"
SAMPLE_CONTENT = "Hello, world!"
UPDATED_CONTENT = "Hello, everyone!"
COMMIT_MESSAGE = "Initial commit"
SECOND_COMMIT_MESSAGE = "Update greeting"
BRANCH_NAME = "feature"
AUTHOR_NAME = "Test Author"
EXPECTED_INITIAL_BRANCH_COUNT = 1
EXPECTED_TWO_BRANCHES = 2
EXPECTED_TWO_COMMITS = 2
# Shrunk by the model check in tests/test_model.py: each one used to crash,
# escape .pygit/refs/heads, or make a branch you couldn't switch back to.
INVALID_BRANCH_NAMES = [
    "",
    ".",
    "..",
    "../escaped",
    "feature/login",
    "back\\slash",
    "nul\0byte",
    "\r",
    "trailing ",
    "x" * 300,
]


class TestRepositoryInit:
    """Verify that Repository.init creates the correct directory structure."""

    def test_init_creates_pygit_dir(self, tmp_path: Path) -> None:
        """Create the .pygit directory."""
        Repository.init(tmp_path)
        assert (tmp_path / PYGIT_DIR).is_dir()

    def test_init_creates_objects_dir(self, tmp_path: Path) -> None:
        """Create the objects subdirectory."""
        Repository.init(tmp_path)
        assert (tmp_path / PYGIT_DIR / OBJECTS_DIR).is_dir()

    def test_init_creates_refs_dir(self, tmp_path: Path) -> None:
        """Create the refs/heads subdirectory."""
        Repository.init(tmp_path)
        assert (tmp_path / PYGIT_DIR / REFS_DIR).is_dir()

    def test_init_creates_head_file(self, tmp_path: Path) -> None:
        """Create the HEAD file pointing to main."""
        Repository.init(tmp_path)
        head = (tmp_path / PYGIT_DIR / HEAD_FILE).read_text(encoding="utf-8")
        assert DEFAULT_BRANCH in head

    def test_init_creates_empty_index(self, tmp_path: Path) -> None:
        """Create an empty index file."""
        Repository.init(tmp_path)
        index = (tmp_path / PYGIT_DIR / INDEX_FILE).read_text(encoding="utf-8")
        assert index == "{}"

    def test_init_twice_raises(self, tmp_path: Path) -> None:
        """Raise RepositoryError if repository already exists."""
        Repository.init(tmp_path)
        with pytest.raises(RepositoryError):
            Repository.init(tmp_path)


class TestRepositoryAdd:
    """Verify that add stages files in the index."""

    def test_add_stages_file(self, tmp_path: Path) -> None:
        """Record the file in the staging area."""
        repo = Repository.init(tmp_path)
        (tmp_path / SAMPLE_FILENAME).write_text(SAMPLE_CONTENT, encoding="utf-8")
        blob_hash = repo.add(SAMPLE_FILENAME)
        assert isinstance(blob_hash, str)
        assert len(blob_hash) > 0

    def test_add_nonexistent_raises(self, tmp_path: Path) -> None:
        """Raise RepositoryError for a missing file."""
        repo = Repository.init(tmp_path)
        with pytest.raises(RepositoryError):
            repo.add("does_not_exist.txt")

    def test_status_shows_staged_file(self, tmp_path: Path) -> None:
        """Show staged files in the status output."""
        repo = Repository.init(tmp_path)
        (tmp_path / SAMPLE_FILENAME).write_text(SAMPLE_CONTENT, encoding="utf-8")
        repo.add(SAMPLE_FILENAME)
        status = repo.status()
        assert SAMPLE_FILENAME in status


class TestRepositoryCommit:
    """Verify that commit creates history entries."""

    def test_commit_creates_hash(self, tmp_path: Path) -> None:
        """Return a commit hash string."""
        repo = Repository.init(tmp_path)
        (tmp_path / SAMPLE_FILENAME).write_text(SAMPLE_CONTENT, encoding="utf-8")
        repo.add(SAMPLE_FILENAME)
        commit_hash = repo.commit(COMMIT_MESSAGE, author=AUTHOR_NAME)
        assert isinstance(commit_hash, str)
        assert len(commit_hash) > 0

    def test_empty_commit_raises(self, tmp_path: Path) -> None:
        """Raise RepositoryError when staging area is empty."""
        repo = Repository.init(tmp_path)
        with pytest.raises(RepositoryError):
            repo.commit(COMMIT_MESSAGE)

    def test_commit_clears_index(self, tmp_path: Path) -> None:
        """Clear the staging area after committing."""
        repo = Repository.init(tmp_path)
        (tmp_path / SAMPLE_FILENAME).write_text(SAMPLE_CONTENT, encoding="utf-8")
        repo.add(SAMPLE_FILENAME)
        repo.commit(COMMIT_MESSAGE)
        assert repo.status() == {}

    def test_commit_is_full_snapshot(self, tmp_path: Path) -> None:
        """Keep previously committed files in later commit snapshots."""
        repo = Repository.init(tmp_path)
        (tmp_path / "a.txt").write_text("first a", encoding="utf-8")
        (tmp_path / "b.txt").write_text("first b", encoding="utf-8")
        repo.add("a.txt")
        repo.add("b.txt")
        repo.commit(COMMIT_MESSAGE)

        # Change and re-stage only a.txt, then commit again.
        (tmp_path / "a.txt").write_text("second a", encoding="utf-8")
        repo.add("a.txt")
        second_hash = repo.commit(SECOND_COMMIT_MESSAGE)

        # The second commit's tree must still contain b.txt.
        store = ObjectStore(tmp_path / PYGIT_DIR / OBJECTS_DIR)
        commit = parse_commit(store.read_object(second_hash, "commit").decode())
        tree = parse_tree(store.read_object(commit.tree_hash, "tree").decode())
        tree_names = {entry.name for entry in tree}
        assert tree_names == {"a.txt", "b.txt"}


class TestRepositoryLog:
    """Verify that log walks the commit chain."""

    def test_log_returns_commits(self, tmp_path: Path) -> None:
        """Return a list of commits in reverse chronological order."""
        repo = Repository.init(tmp_path)
        (tmp_path / SAMPLE_FILENAME).write_text(SAMPLE_CONTENT, encoding="utf-8")
        repo.add(SAMPLE_FILENAME)
        repo.commit(COMMIT_MESSAGE)
        history = repo.log()
        assert len(history) == 1
        assert history[0].message == COMMIT_MESSAGE

    def test_log_walks_parent_chain(self, tmp_path: Path) -> None:
        """Walk the parent chain across multiple commits."""
        repo = Repository.init(tmp_path)
        (tmp_path / SAMPLE_FILENAME).write_text(SAMPLE_CONTENT, encoding="utf-8")
        repo.add(SAMPLE_FILENAME)
        repo.commit(COMMIT_MESSAGE)

        (tmp_path / SAMPLE_FILENAME).write_text(UPDATED_CONTENT, encoding="utf-8")
        repo.add(SAMPLE_FILENAME)
        repo.commit(SECOND_COMMIT_MESSAGE)

        history = repo.log()
        assert len(history) == EXPECTED_TWO_COMMITS
        assert history[0].message == SECOND_COMMIT_MESSAGE
        assert history[1].message == COMMIT_MESSAGE

    def test_log_empty_repo(self, tmp_path: Path) -> None:
        """Return an empty list for a fresh repository."""
        repo = Repository.init(tmp_path)
        assert repo.log() == []


class TestRepositoryBranches:
    """Verify branch creation, listing, and switching."""

    def test_current_branch_is_main(self, tmp_path: Path) -> None:
        """Default to the main branch after init."""
        repo = Repository.init(tmp_path)
        assert repo.current_branch() == DEFAULT_BRANCH

    def test_create_branch(self, tmp_path: Path) -> None:
        """Add a new branch to the branch list."""
        repo = Repository.init(tmp_path)
        (tmp_path / SAMPLE_FILENAME).write_text(SAMPLE_CONTENT, encoding="utf-8")
        repo.add(SAMPLE_FILENAME)
        repo.commit(COMMIT_MESSAGE)
        repo.create_branch(BRANCH_NAME)
        branches = repo.list_branches()
        assert BRANCH_NAME in branches
        assert len(branches) == EXPECTED_TWO_BRANCHES

    def test_create_duplicate_branch_raises(self, tmp_path: Path) -> None:
        """Raise RepositoryError when creating a branch that already exists."""
        repo = Repository.init(tmp_path)
        (tmp_path / SAMPLE_FILENAME).write_text(SAMPLE_CONTENT, encoding="utf-8")
        repo.add(SAMPLE_FILENAME)
        repo.commit(COMMIT_MESSAGE)
        repo.create_branch(BRANCH_NAME)
        with pytest.raises(RepositoryError):
            repo.create_branch(BRANCH_NAME)

    def test_switch_branch(self, tmp_path: Path) -> None:
        """Change HEAD to the target branch."""
        repo = Repository.init(tmp_path)
        (tmp_path / SAMPLE_FILENAME).write_text(SAMPLE_CONTENT, encoding="utf-8")
        repo.add(SAMPLE_FILENAME)
        repo.commit(COMMIT_MESSAGE)
        repo.create_branch(BRANCH_NAME)
        repo.switch_branch(BRANCH_NAME)
        assert repo.current_branch() == BRANCH_NAME

    def test_switch_nonexistent_branch_raises(self, tmp_path: Path) -> None:
        """Raise RepositoryError when switching to a branch that does not exist."""
        repo = Repository.init(tmp_path)
        with pytest.raises(RepositoryError):
            repo.switch_branch("nonexistent")

    def test_list_branches_initial(self, tmp_path: Path) -> None:
        """List only the main branch for a fresh repo with one commit."""
        repo = Repository.init(tmp_path)
        (tmp_path / SAMPLE_FILENAME).write_text(SAMPLE_CONTENT, encoding="utf-8")
        repo.add(SAMPLE_FILENAME)
        repo.commit(COMMIT_MESSAGE)
        branches = repo.list_branches()
        assert len(branches) == EXPECTED_INITIAL_BRANCH_COUNT
        assert DEFAULT_BRANCH in branches

    def test_branch_name_cannot_climb_out_of_the_branches_folder(self, tmp_path: Path) -> None:
        """Regression: create_branch("../escaped") wrote .pygit/refs/escaped, outside refs/heads."""
        repo = Repository.init(tmp_path)
        with pytest.raises(RepositoryError, match="Invalid branch name"):
            repo.create_branch("../escaped")
        assert not (tmp_path / PYGIT_DIR / "refs" / "escaped").exists()

    def test_switching_to_an_empty_name_raises(self, tmp_path: Path) -> None:
        """Regression: switch_branch("") found the branches *folder* and moved HEAD onto it."""
        repo = Repository.init(tmp_path)
        with pytest.raises(RepositoryError):
            repo.switch_branch("")
        assert repo.current_branch() == DEFAULT_BRANCH

    @pytest.mark.parametrize("name", INVALID_BRANCH_NAMES)
    def test_invalid_branch_names_are_refused(self, tmp_path: Path, name: str) -> None:
        """Names that aren't one plain file name are refused, by create and by switch."""
        repo = Repository.init(tmp_path)
        with pytest.raises(RepositoryError, match="Invalid branch name"):
            repo.create_branch(name)
        with pytest.raises(RepositoryError):
            repo.switch_branch(name)
        assert repo.list_branches() == []

    def test_names_differing_only_in_capitals_are_refused(self, tmp_path: Path) -> None:
        """On a Mac "Feature" and "feature" are one file, so PyGit refuses the second everywhere."""
        repo = Repository.init(tmp_path)
        repo.create_branch(BRANCH_NAME)
        with pytest.raises(RepositoryError, match="capitals"):
            repo.create_branch(BRANCH_NAME.capitalize())
        assert repo.list_branches() == [BRANCH_NAME]

    def test_a_name_like_main_is_refused_before_the_first_commit(self, tmp_path: Path) -> None:
        """Regression: on a Mac, "Main" was made, then the first commit on main overwrote its file."""
        repo = Repository.init(tmp_path)
        with pytest.raises(RepositoryError, match="capitals"):
            repo.create_branch("Main")

    def test_switching_needs_the_exact_name(self, tmp_path: Path) -> None:
        """Regression: on a Mac switch_branch("MAIN") found main's file and HEAD said MAIN."""
        repo = Repository.init(tmp_path)
        (tmp_path / SAMPLE_FILENAME).write_text(SAMPLE_CONTENT, encoding="utf-8")
        repo.add(SAMPLE_FILENAME)
        repo.commit(COMMIT_MESSAGE)
        with pytest.raises(RepositoryError):
            repo.switch_branch(DEFAULT_BRANCH.upper())
        assert repo.current_branch() == DEFAULT_BRANCH


def _tree_at(repo_path: Path, tree_hash: str) -> dict[str, tuple[str, str]]:
    """Read one tree object as ``{name: (type, hash)}``."""
    store = ObjectStore(repo_path / PYGIT_DIR / OBJECTS_DIR)
    entries = parse_tree(store.read_object(tree_hash, "tree").decode())
    return {e.name: (e.entry_type, e.hash) for e in entries}


def _root_tree(repo_path: Path, commit_hash: str) -> dict[str, tuple[str, str]]:
    """Read the top-level tree of a commit."""
    store = ObjectStore(repo_path / PYGIT_DIR / OBJECTS_DIR)
    commit = parse_commit(store.read_object(commit_hash, "commit").decode())
    return _tree_at(repo_path, commit.tree_hash)


class TestFoldersBecomeNestedTrees:
    """Each folder in the project gets its own tree, just like real Git."""

    def test_files_in_folders_are_stored_in_sub_trees(self, tmp_path: Path) -> None:
        """Regression: everything used to go in one flat tree named like 'src/main.py'."""
        repo = Repository.init(tmp_path)
        (tmp_path / "src" / "lib").mkdir(parents=True)
        (tmp_path / "README.md").write_text("hi\n", encoding="utf-8")
        (tmp_path / "src" / "main.py").write_text("print(1)\n", encoding="utf-8")
        (tmp_path / "src" / "lib" / "util.py").write_text("x = 1\n", encoding="utf-8")
        for path in ("README.md", "src/main.py", "src/lib/util.py"):
            repo.add(path)
        root = _root_tree(tmp_path, repo.commit(COMMIT_MESSAGE))
        assert root["README.md"][0] == "blob"
        assert root["src"][0] == "tree"
        src = _tree_at(tmp_path, root["src"][1])
        assert set(src) == {"main.py", "lib"}
        assert src["lib"][0] == "tree"
        assert set(_tree_at(tmp_path, src["lib"][1])) == {"util.py"}

    def test_next_commit_keeps_files_in_untouched_folders(self, tmp_path: Path) -> None:
        """Changing one file keeps every other file, however deep, in the snapshot."""
        repo = Repository.init(tmp_path)
        (tmp_path / "src" / "lib").mkdir(parents=True)
        (tmp_path / "src" / "lib" / "util.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "src" / "main.py").write_text("v1\n", encoding="utf-8")
        repo.add("src/lib/util.py")
        repo.add("src/main.py")
        repo.commit(COMMIT_MESSAGE)
        (tmp_path / "src" / "main.py").write_text("v2\n", encoding="utf-8")
        repo.add("src/main.py")
        root = _root_tree(tmp_path, repo.commit(SECOND_COMMIT_MESSAGE))
        src = _tree_at(tmp_path, root["src"][1])
        assert set(src) == {"main.py", "lib"}
        assert set(_tree_at(tmp_path, src["lib"][1])) == {"util.py"}


class TestRealGitCompatibility:
    """Blob fingerprints match real Git's, byte for byte."""

    def test_added_file_has_the_same_hash_git_would_give_it(self, tmp_path: Path) -> None:
        """Running git hash-object on a file saying "hello" gives this exact hash."""
        repo = Repository.init(tmp_path)
        (tmp_path / "hello.txt").write_bytes(b"hello\n")
        assert repo.add("hello.txt") == "ce013625030ba8dba906f756967f9e9ca394464a"

    def test_binary_files_can_be_added(self, tmp_path: Path) -> None:
        """Regression: adding a picture used to crash, because files were read as text."""
        repo = Repository.init(tmp_path)
        (tmp_path / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe")
        repo.add("logo.png")
        repo.commit(COMMIT_MESSAGE)
        assert "logo.png" in _root_tree(tmp_path, repo.log()[0].commit_hash)
