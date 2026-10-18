"""Property-based tests -- rules that must hold for *every* input.

An ordinary test checks one example someone thought of: "store the bytes
``Hello, world!`` and you can read them back". A property test states a rule
instead, such as "whatever bytes you store, reading them back gives exactly
those bytes", and lets Hypothesis invent hundreds of files to try to break
it. If one breaks the rule, Hypothesis *shrinks* it down to the smallest
input that still fails, and shows you that.

Each test below says its rule in plain English in its docstring. The
strategies at the top are recipes for making random inputs; each one is
named for what it makes.

The step-by-step checks of the object store and the repository's branches
against plain dicts live in ``tests/test_model.py``. See
``docs/property-testing.md`` for the walk-through.
"""

import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from pygit.diff import diff_lines
from pygit.errors import PyGitError
from pygit.hashing import hash_object
from pygit.objects import ObjectStore
from pygit.tree import TreeEntry, build_tree, parse_tree
from tests.strategies import any_hashes, file_contents, git_hash, object_types

# --- Strategies: recipes for random inputs -----------------------------------
# file_contents(), object_types(), any_hashes() and git_hash() live in
# tests/strategies.py, shared with the model check.

# A handful of lines, so two random texts often share some (otherwise the
# diff would almost always be "remove everything, add everything").
SHARED_LINES = ["apple", "banana", "cherry", ""]


def entries_from(by_name: dict[str, tuple[str, str]]) -> list[TreeEntry]:
    """Turn ``{name: (kind, hash)}`` into a list of tree entries."""
    return [
        TreeEntry(name=name, entry_type=kind, hash=object_hash)
        for name, (kind, object_hash) in by_name.items()
    ]


def tree_entries() -> st.SearchStrategy[list[TreeEntry]]:
    """Make the entries of one folder: any names, each a file or a sub-folder, with a hash."""
    # A folder can't hold two things with the same name, so the names are
    # the keys of a dict (TreeEntry: "the filename or directory name").
    by_name = st.dictionaries(st.text(), st.tuples(st.sampled_from(["blob", "tree"]), any_hashes()))
    return by_name.map(entries_from)


def any_text() -> st.SearchStrategy[str]:
    """Make a whole file of text: any characters at all, or lines picked from a small shared set."""
    return st.one_of(st.text(), st.lists(st.sampled_from(SHARED_LINES)).map("\n".join))


# --- Helpers -----------------------------------------------------------------


def read_or_refuse(store: ObjectStore, object_hash: str) -> None:
    """Read a blob from the store, accepting only a PyGitError refusal.

    A PyGitError (ObjectNotFoundError or ObjectTypeError) is caught and
    ignored: refusing a damaged object is fine. Any *other* exception escapes
    and fails the test, and that is the whole check.
    """
    try:
        store.read_object(object_hash, "blob")
    except PyGitError:
        return


# --- Hashing: PyGit fingerprints files exactly like Git ----------------------


@given(data=file_contents())
def test_blob_hash_follows_gits_rule(data: bytes) -> None:
    """A file's fingerprint is SHA-1 of ``blob <size>``, a zero byte, then the file -- Git's rule."""
    assert hash_object("blob", data) == git_hash("blob", data)


# --- The object store: whatever you file away comes back --------------------


@given(object_type=object_types(), data=file_contents())
def test_write_then_read_gives_back_the_same_bytes(object_type: str, data: bytes) -> None:
    """Reading an object by the hash that writing returned gives back exactly the bytes written."""
    with tempfile.TemporaryDirectory() as folder:
        store = ObjectStore(Path(folder))
        object_hash = store.write_object(object_type, data)
        assert object_hash == git_hash(object_type, data)
        assert store.exists(object_hash)
        assert store.read_object(object_hash, object_type) == data


@given(junk=file_contents(), object_hash=any_hashes())
def test_damaged_object_reads_or_raises_pygit_error(junk: bytes, object_hash: str) -> None:
    """Whatever bytes are in an object file, reading gives bytes or a PyGitError, never another error."""
    with tempfile.TemporaryDirectory() as folder:
        store = ObjectStore(Path(folder))
        # Objects live at objects/<first two characters>/<the other 38>.
        path = Path(folder) / object_hash[:2] / object_hash[2:]
        path.parent.mkdir()
        path.write_bytes(junk)
        read_or_refuse(store, object_hash)


# --- Trees: a folder's table of contents --------------------------------------


@given(entries=tree_entries())
def test_build_then_parse_gives_back_the_entries_sorted_by_name(entries: list[TreeEntry]) -> None:
    """Parsing a built tree gives back every entry, unchanged, in order of name."""
    _tree_hash, content = build_tree(entries)
    assert parse_tree(content) == sorted(entries, key=lambda entry: entry.name)


@given(entries=tree_entries(), data=st.data())
def test_tree_hash_ignores_the_order_of_entries(
    entries: list[TreeEntry], data: st.DataObject
) -> None:
    """The same entries in any order give the same tree hash."""
    shuffled = data.draw(st.permutations(entries), label="shuffled")
    assert build_tree(shuffled) == build_tree(entries)


# --- Diff: both versions can be read back out of it ---------------------------


@given(old=any_text(), new=any_text())
def test_diff_contains_both_versions(old: str, new: str) -> None:
    """Unchanged plus removed lines spell out the old text; unchanged plus added lines spell out the new."""
    diff = diff_lines(old, new)
    assert [line[2:] for line in diff if line[:2] in {"  ", "- "}] == old.splitlines()
    assert [line[2:] for line in diff if line[:2] in {"  ", "+ "}] == new.splitlines()
