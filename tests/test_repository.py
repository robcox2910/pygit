"""Tests for the repository module."""

from pathlib import Path

import pytest

from pygit.errors import RepositoryError
from pygit.repository import DEFAULT_BRANCH, HEAD_FILE, INDEX_FILE, OBJECTS_DIR, PYGIT_DIR, REFS_DIR, Repository

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
