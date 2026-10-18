"""Strategies -- recipes for random file contents, hashes and names, shared by the property tests.

A strategy tells Hypothesis how to invent one kind of input. Each one here
is a named function, named for what it makes, with a one-line docstring.
``tests/test_properties.py`` and ``tests/test_model.py`` both use them.

``git_hash`` is here too: it is Git's fingerprint rule, written out with
nothing but Python's own ``hashlib``, so the tests can check PyGit against
it without borrowing any of PyGit's code.
"""

import hashlib

from hypothesis import strategies as st

# Files are written to a real folder on disk, and small files find the same
# bugs as big ones, so contents stay under this many bytes. A failure shrinks
# to a tiny file anyway.
MOST_BYTES_PER_FILE = 64

HEX_DIGITS = "0123456789abcdef"
HASH_LENGTH = 40


def git_hash(object_type: str, data: bytes) -> str:
    r"""Fingerprint an object by Git's rule: SHA-1 of ``<type> <size>\0`` then the content."""
    return hashlib.sha1(b"%s %d\0" % (object_type.encode(), len(data)) + data).hexdigest()  # noqa: S324


def file_contents() -> st.SearchStrategy[bytes]:
    """Make the bytes of one small file: empty, text, or not text at all."""
    return st.binary(max_size=MOST_BYTES_PER_FILE)


def object_types() -> st.SearchStrategy[str]:
    """Pick one of the three kinds of object: blob, tree or commit."""
    return st.sampled_from(["blob", "tree", "commit"])


def any_hashes() -> st.SearchStrategy[str]:
    """Make a 40-character hash, the kind PyGit writes, that probably names nothing yet."""
    return st.text(alphabet=HEX_DIGITS, min_size=HASH_LENGTH, max_size=HASH_LENGTH)


def awkward_branch_names() -> st.SearchStrategy[str]:
    """Make a branch name a careless (or sneaky) user might type: slashes, dots, spaces, the lot."""
    return st.one_of(
        st.sampled_from(
            [
                "",
                ".",
                "..",
                "../escaped",
                "../../../outside",
                "feature/login",
                "nul\0byte",
                "trailing ",
                "new\nline",
                "Main",
                "MAIN",
                "x" * 300,
            ]
        ),
        st.text(),
    )


def plain_branch_names() -> st.SearchStrategy[str]:
    """Make an ordinary branch name: a few lowercase letters, like ``feature`` or ``fix``."""
    return st.text(alphabet="abcdefghij", min_size=1, max_size=6)


def commit_messages() -> st.SearchStrategy[str]:
    r"""Make a commit message, leaning on the edges a careless clean-up would trim: spaces, tabs, ``\r`` and ``\n``."""
    edge = st.text(alphabet=" \t\r\n", max_size=3)
    return st.one_of(
        st.text(max_size=20),
        st.sampled_from(["\r", "\n", " ", "\t", "", " \r\n "]),
        st.builds(lambda lead, body, tail: lead + body + tail, edge, st.text(max_size=10), edge),
    )
