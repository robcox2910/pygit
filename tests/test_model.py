"""Model check -- the object store and the repository must behave like plain Python dicts.

A property test checks one rule for many inputs. A *model check* goes
further: Hypothesis invents a random *story* -- store this, read that, make
a branch, switch to it, commit -- and plays it on two things at once:

- the real ``ObjectStore`` or ``Repository``, writing real files to disk;
- a **model**: plain dicts and lists, which we already trust to be right.

After every step the two must agree. If they ever disagree, Hypothesis
shrinks the story to the shortest list of steps that still goes wrong.

The models are deliberately *not* copies of PyGit's code. They are the
simplest things that are obviously correct, so when the two disagree, PyGit
is the one to suspect.

See ``docs/property-testing.md`` for the walk-through.
"""

import tempfile
import unicodedata
import unittest
from pathlib import Path
from typing import cast

import pytest
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, invariant, rule

from pygit.errors import ObjectNotFoundError, ObjectTypeError, RepositoryError
from pygit.objects import ObjectStore
from pygit.repository import Repository
from tests.strategies import (
    any_hashes,
    awkward_branch_names,
    commit_messages,
    file_contents,
    git_hash,
    object_types,
    plain_branch_names,
)

# --- The object store: one story, played on the store and on a dict ----------


def next_door(object_hash: str) -> str:
    """Change a hash's last character, so it's filed in the same folder but names something else."""
    return object_hash[:-1] + ("1" if object_hash.endswith("0") else "0")


class ObjectStoreMachine(RuleBasedStateMachine):
    """Play random writes and reads on an ObjectStore and a dict side by side."""

    # Hashes the store has handed back. A random hash almost never names a
    # stored object, so reads also pick from here to find ones that do.
    hashes = Bundle("hashes")

    def __init__(self) -> None:
        """Start with an empty store in a new folder, and an empty dict."""
        super().__init__()
        self.folder = tempfile.TemporaryDirectory()
        self.store = ObjectStore(Path(self.folder.name))
        self.model: dict[str, tuple[str, bytes]] = {}

    def teardown(self) -> None:
        """Delete the folder at the end of the story."""
        self.folder.cleanup()

    @rule(target=hashes, object_type=object_types(), data=file_contents())
    def write(self, object_type: str, data: bytes) -> str:
        """Write an object; the store answers with Git's hash, and the dict files it under that."""
        object_hash = self.store.write_object(object_type, data)
        assert object_hash == git_hash(object_type, data)
        self.model[object_hash] = (object_type, data)
        return object_hash

    @rule(object_hash=hashes)
    def write_again(self, object_hash: str) -> None:
        """Write an object that's already stored; the store gives the same hash again."""
        object_type, data = self.model[object_hash]
        assert self.store.write_object(object_type, data) == object_hash

    # A read can ask for a stored hash, a random one, or one filed next door to
    # a stored one (same folder, nothing there).
    @rule(
        object_hash=st.one_of(hashes, any_hashes(), hashes.map(next_door)),
        object_type=object_types(),
    )
    def read(self, object_hash: str, object_type: str) -> None:
        """Read an object: its bytes, ObjectTypeError for the wrong type, or ObjectNotFoundError."""
        assert self.store.exists(object_hash) == (object_hash in self.model)
        if object_hash not in self.model:
            with pytest.raises(ObjectNotFoundError):
                self.store.read_object(object_hash, object_type)
        elif self.model[object_hash][0] != object_type:
            with pytest.raises(ObjectTypeError):
                self.store.read_object(object_hash, object_type)
        else:
            assert self.store.read_object(object_hash, object_type) == self.model[object_hash][1]

    @invariant()
    def every_object_reads_back(self) -> None:
        """After every step, every object in the dict is in the store, with the same bytes."""
        for object_hash, (object_type, data) in self.model.items():
            assert self.store.exists(object_hash)
            assert self.store.read_object(object_hash, object_type) == data


# why: 20 steps find the same bugs; 50 (the default) is most of the run time
ObjectStoreMachine.TestCase.settings = settings(stateful_step_count=20)
# pytest runs this like any other test class: one run plays 100 random stories.
# (Hypothesis doesn't say what type ``TestCase`` is, so ``cast`` tells pyright.)
TestObjectStoreModel = cast("type[unittest.TestCase]", ObjectStoreMachine.TestCase)


# --- The repository: staging, commits and branches, played against dicts -----

# The files the story can add. A few names, one inside a folder, so the same
# file is often changed and added again.
FILE_PATHS = ["hello.txt", "notes.md", "src/app.py"]


def file_paths() -> st.SearchStrategy[str]:
    """Pick one of the project's files."""
    return st.sampled_from(FILE_PATHS)


# Pairs the rule must treat as the same name, and pairs it must not. Written
# out by hand so the check below does not lean on any code of PyGit's.
TWIN_PAIRS = [
    ("feature", "Feature"),
    ("main", "MAIN"),
    ("cafe\u0301", "caf\u00e9"),  # e + combining accent, against one letter e-acute
    ("CAFE\u0301", "caf\u00e9"),
    ("\ufb00", "ff"),  # a ligature is two letters
    ("\u00df", "ss"),
    ("\u00df", "SS"),  # German sharp s is ss
    ("\u017f", "s"),  # long s
    ("\u03c2", "\u03a3"),  # Greek final sigma, against capital sigma
]
NOT_TWINS = [
    ("feature", "features"),
    ("cafe", "caf\u00e9"),  # an accent is a different letter, not a spelling
    ("a", "b"),
    ("\u0131", "i"),  # Turkish dotless i is its own letter
    ("s", "z"),
]


def twin_key(name: str) -> str:
    """Spell a name for comparing: lower case, each accent as one joined letter."""
    # The rule, from docs/concepts/branches.md: two branch names that differ
    # only in capitals or in how an accent is spelled would share one file on
    # a Mac, so the second one is refused everywhere. Built differently from
    # PyGit (which uses casefold and NFD): lower, then upper, then lower again
    # turns every capital, sharp s, long s, final sigma and ligature into its
    # plain letters, and NFC joins accents. The dotless i is the one letter
    # that trick would merge with i but a Mac keeps apart, so it is left alone.
    parts = [
        unicodedata.normalize("NFC", part.lower().upper().lower()) for part in name.split("\u0131")
    ]
    return "\u0131".join(parts)


def test_twin_key_agrees_with_the_hand_written_pairs() -> None:
    """The model's rule calls the listed twins twins and the listed non-twins different."""
    assert all(twin_key(one) == twin_key(two) for one, two in TWIN_PAIRS)
    assert all(twin_key(one) != twin_key(two) for one, two in NOT_TWINS)


@pytest.mark.parametrize(("one", "two"), TWIN_PAIRS)
def test_repository_refuses_a_twin_of_an_existing_branch(
    one: str, two: str, tmp_path: Path
) -> None:
    """A branch whose twin exists is refused."""
    repo = Repository.init(tmp_path)
    repo.create_branch(one)
    with pytest.raises(RepositoryError):
        repo.create_branch(two)


@pytest.mark.parametrize(("one", "two"), NOT_TWINS)
def test_repository_allows_names_that_are_not_twins(one: str, two: str, tmp_path: Path) -> None:
    """Two names that are not twins can both be branches."""
    repo = Repository.init(tmp_path)
    repo.create_branch(one)
    repo.create_branch(two)


class RepositoryMachine(RuleBasedStateMachine):
    """Play random adds, commits, new branches and switches on a Repository and on dicts."""

    branches = Bundle("branches")

    def __init__(self) -> None:
        """Start with a new repository, no branches yet, on main, with nothing staged."""
        super().__init__()
        self.folder = tempfile.TemporaryDirectory()
        # The project sits two folders down, so a branch name that climbs out
        # of the repository with ".." still lands inside the temporary folder.
        self.project = Path(self.folder.name) / "outer" / "project"
        (self.project / "src").mkdir(parents=True)
        self.repo = Repository.init(self.project)
        # Each branch's commits as (hash, message), oldest first. A branch
        # only appears here once it really exists: main does after the first
        # commit.
        self.history: dict[str, list[tuple[str, str]]] = {}
        # Every commit's full snapshot: {file path: blob hash}.
        self.snapshots: dict[str, dict[str, str]] = {}
        self.current = "main"
        self.staged: dict[str, str] = {}
        self.written: set[str] = set()

    def teardown(self) -> None:
        """Delete the folder at the end of the story."""
        self.folder.cleanup()

    @rule(path=file_paths(), data=file_contents())
    def add(self, path: str, data: bytes) -> None:
        """Change a file and stage it; the repository answers with the file's Git hash."""
        (self.project / path).write_bytes(data)
        self.written.add(path)
        blob_hash = git_hash("blob", data)
        assert self.repo.add(path) == blob_hash
        self.staged[path] = blob_hash

    @rule(message=commit_messages())
    def commit(self, message: str) -> None:
        """Commit what's staged: a new commit on the current branch, or RepositoryError if nothing is."""
        if not self.staged:
            with pytest.raises(RepositoryError):
                self.repo.commit(message)
            return
        commits = self.history.get(self.current, [])
        parent_snapshot = self.snapshots[commits[-1][0]] if commits else {}
        commit_hash = self.repo.commit(message)
        # A commit is a full snapshot: the parent's files, with the staged ones on top.
        self.snapshots[commit_hash] = {**parent_snapshot, **self.staged}
        self.history[self.current] = [*commits, (commit_hash, message)]
        self.staged.clear()
        tree_hash = self.repo.log()[0].tree_hash
        assert self.repo._read_tree(tree_hash) == self.snapshots[commit_hash]

    def has_twin(self, name: str) -> bool:
        """Say whether another branch (or the current one) differs from ``name`` only in capitals or accents."""
        others = {*self.history, self.current} - {name}
        return any(twin_key(other) == twin_key(name) for other in others)

    @rule(target=branches, name=plain_branch_names())
    def create_branch(self, name: str) -> str:
        """Make a branch with an ordinary name; it starts with the current branch's commits."""
        if name in self.history or self.has_twin(name):
            with pytest.raises(RepositoryError):
                self.repo.create_branch(name)
        else:
            self.repo.create_branch(name)
            self.history[name] = list(self.history.get(self.current, []))
        return name

    @rule(target=branches, name=awkward_branch_names())
    def create_awkward_branch(self, name: str) -> str:
        """Make a branch with a strange name: made properly or refused, and no file lands elsewhere."""
        # create_branch above checks that ordinary names succeed; here the
        # name may be one PyGit should refuse, so either answer is allowed
        # unless the model knows it must be refused.
        if name in self.history or self.has_twin(name):
            with pytest.raises(RepositoryError):
                self.repo.create_branch(name)
        else:
            try:
                self.repo.create_branch(name)
            except RepositoryError:
                pass  # refusing a strange name is fine; switching to it must fail too
            else:
                self.history[name] = list(self.history.get(self.current, []))
        # Only a branch name can send a file to the wrong place, so this
        # (slow) look at every file runs here rather than after every step.
        assert self.files_outside_the_object_store() == self.expected_files()
        return name

    @rule(name=st.one_of(branches, plain_branch_names(), awkward_branch_names()))
    def switch_branch(self, name: str) -> None:
        """Switch to a branch: fine if it exists, RepositoryError if it doesn't."""
        if name in self.history:
            self.repo.switch_branch(name)
            self.current = name
        else:
            with pytest.raises(RepositoryError):
                self.repo.switch_branch(name)

    @invariant()
    def repository_matches_the_dicts(self) -> None:
        """After every step, the branches, HEAD, the staging area and the log all match the model."""
        assert self.repo.list_branches() == sorted(self.history)
        assert self.repo.current_branch() == self.current
        assert self.repo.status() == self.staged
        logged = [(commit.commit_hash, commit.message) for commit in self.repo.log()]
        assert logged == self.history.get(self.current, [])[::-1]

    def files_outside_the_object_store(self) -> set[str]:
        """List every file in the temporary folder, except the objects, as a path from its top."""
        root = Path(self.folder.name)
        found: set[str] = set()
        for folder, sub_folders, files in root.walk():
            if folder.name == ".pygit":
                sub_folders.remove("objects")  # the object store has its own model check
            found |= {(folder / name).relative_to(root).as_posix() for name in files}
        return found

    def expected_files(self) -> set[str]:
        """List the files that should be there: the project's, HEAD, the index and one per branch."""
        expected = {".pygit/HEAD", ".pygit/index"} | self.written
        expected |= {f".pygit/refs/heads/{name}" for name in self.history}
        return {f"outer/project/{path}" for path in expected}


# why: every step reads and writes real files, so stories are a little shorter
# here; 15 steps find the same bugs (each one shrank to 5 steps or fewer)
RepositoryMachine.TestCase.settings = settings(stateful_step_count=15)
# pytest runs this like any other test class: one run plays 100 random stories.
TestRepositoryModel = cast("type[unittest.TestCase]", RepositoryMachine.TestCase)
