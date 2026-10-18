# Property Testing (Every Photo Filed by Its Fingerprint)

## The Album Inspector

Picture a giant photo album with a strange filing rule. You never choose
where a photo goes. Instead, the album takes the photo's
[fingerprint](concepts/hashing.md) and files it under that. Hand over
the same photo twice and it lands in the same slot. Ask for a
fingerprint and you get exactly that photo back. That album is PyGit's
object store, and every file, folder and commit you save goes into it.

How would you check the album works? The usual way: file one photo, look
it up, and smile. That's an **example test**. It's useful, but it only
tells you about the one photo you thought of.

Now imagine an inspector. All day long they file thousands of things --
holiday snaps, a blank page, a photo of a photo, a page of scribbles in
a language they can't read, a file that isn't a photo at all -- and for
each one they check a single rule:

> Whatever you file, looking up the fingerprint you were given gets
> exactly that thing back.

That rule is a **property**. It doesn't say what any one photo looks
like. It says something that must be true for *every* photo.

When the inspector finds something that breaks the rule, they don't just
report "something went wrong this afternoon, with a big pile of stuff".
They try again with less and less -- fewer photos, smaller photos,
simpler names -- checking it still goes wrong each time, until it's as
simple as it can be. That boiling-down is called **shrinking**, and it's
the best part: the smallest failing input usually points straight at
the bug.

In Python, the inspector is a library called
[Hypothesis](https://hypothesis.readthedocs.io/). PyGit's property tests
live in `tests/test_properties.py`, next to the ordinary example tests,
and the model checks (more on those below) are in `tests/test_model.py`.

## A Property from PyGit

PyGit promises something bold: a file's fingerprint is *exactly* the one
real Git gives it. Git's rule is short. Write `blob`, a space, the
file's size in bytes and a zero byte, stick the file on the end, and
take the SHA-1 of the lot. Here's the property that checks PyGit follows
it, with the two recipes it uses from `tests/strategies.py`:

```python
def git_hash(object_type: str, data: bytes) -> str:
    r"""Fingerprint an object by Git's rule: SHA-1 of ``<type> <size>\0`` then the content."""
    return hashlib.sha1(b"%s %d\0" % (object_type.encode(), len(data)) + data).hexdigest()  # noqa: S324


def file_contents() -> st.SearchStrategy[bytes]:
    """Make the bytes of one small file: empty, text, or not text at all."""
    return st.binary(max_size=MOST_BYTES_PER_FILE)


@given(data=file_contents())
def test_blob_hash_follows_gits_rule(data: bytes) -> None:
    """A file's fingerprint is SHA-1 of ``blob <size>``, a zero byte, then the file -- Git's rule."""
    assert hash_object("blob", data) == git_hash("blob", data)
```

Line by line:

- **`git_hash`** is Git's rule, written out again with nothing but
  Python's own `hashlib`. `b"%s %d\0"` builds the label (`blob 6` and a
  zero byte for a six-byte file). It borrows *nothing* from PyGit, so if
  PyGit gets the rule wrong, the two disagree.
- **`file_contents()`** is a **strategy**: a recipe for making random
  inputs. `st.binary()` makes any run of bytes at all: empty, plain
  text, emoji, or bytes that aren't text at all, like a picture.
  `max_size` keeps each file small, since small files find the same bugs.
- **`@given(data=file_contents())`** tells Hypothesis to run the test
  many times (100 in a normal run), each time with a fresh `data`.
- **The docstring** says the rule in plain English. If you can't say the
  rule in one sentence, it probably isn't a good property yet.
- **The `assert`** is the rule itself: PyGit's fingerprint must equal
  Git's, character for character.

Notice what the test *doesn't* say. It never says "the file `hello`
has the fingerprint `ce0136...`". It doesn't need to know any answers.
It only needs a second, independent way of working them out.

PyGit has five more properties:

| Rule | Test |
|---|---|
| Reading an object by the hash that writing returned gives back exactly the bytes written | `test_write_then_read_gives_back_the_same_bytes` |
| Whatever bytes are in an object file, reading gives bytes or a `PyGitError`, never another error | `test_damaged_object_reads_or_raises_pygit_error` |
| Parsing a built tree gives back every entry, unchanged, in order of name | `test_build_then_parse_gives_back_the_entries_sorted_by_name` |
| The same entries in any order give the same tree hash | `test_tree_hash_ignores_the_order_of_entries` |
| Unchanged plus removed lines spell out the old text; unchanged plus added lines spell out the new | `test_diff_contains_both_versions` |

There's a catch with the "damaged file" rule. An object store that
refuses to read **anything** passes it, because refusing is always
allowed. **A do-nothing object store passes the damaged-file property**,
so the round-trip sits beside it: it fails straight away if reading
never gives anything back.

## Checking Against a Model

A property checks one action. But the album is something you change step
by step: file this, look up that, file the same thing again. Bugs often
hide in the *order* of steps -- looking up a fingerprint nobody filed, or
filing the same photo twice.

So the inspector has a second trick. They carry a little notebook and
write down every fingerprint and photo by hand. After every single step,
they compare the album with the notebook. If the album ever disagrees
with the notebook, something's wrong with the album.

That notebook is a **model**: something simple that we already trust.
For the object store, the model is a plain Python `dict` from hash to
type and bytes. Here's the start of the check in `tests/test_model.py`:

```python
class ObjectStoreMachine(RuleBasedStateMachine):
    """Play random writes and reads on an ObjectStore and a dict side by side."""

    hashes = Bundle("hashes")

    def __init__(self) -> None:
        """Start with an empty store in a new folder, and an empty dict."""
        super().__init__()
        self.folder = tempfile.TemporaryDirectory()
        self.store = ObjectStore(Path(self.folder.name))
        self.model: dict[str, tuple[str, bytes]] = {}

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

    @invariant()
    def every_object_reads_back(self) -> None:
        """After every step, every object in the dict is in the store, with the same bytes."""
        for object_hash, (object_type, data) in self.model.items():
            assert self.store.exists(object_hash)
            assert self.store.read_object(object_hash, object_type) == data


TestObjectStoreModel = cast("type[unittest.TestCase]", ObjectStoreMachine.TestCase)
```

Piece by piece:

- **`RuleBasedStateMachine`** is Hypothesis's tool for testing things
  that change step by step. Hypothesis makes up a random **story** of
  steps and plays it.
- **`self.store` and `self.model`** are the album and the notebook.
  Every story starts with both empty, in a brand-new folder.
- **Each `@rule`** is one kind of step. It does the same thing to the
  store and to the dict. The real file has rules to write an object,
  write one again, and read one back, with the right type, the wrong
  type, or a hash that names nothing. `write` also checks what the store
  *answers*: the hash must be Git's.
- **`hashes = Bundle("hashes")`** is a bag of hashes the store has handed
  out. Two random hashes almost never match, so without it the story
  would hardly ever look up something that's really there. `write` puts
  its hash in the bag (`target=hashes`), and `write_again` pulls one out.
  The `read` rule picks a hash from the bag, a random one, or one *next
  door* to a stored one, so it tries hashes that exist *and* hashes that
  don't.
- **The `@invariant()`** runs after every single step and checks every
  object in the notebook is still in the album, byte for byte.
- **`TestObjectStoreModel = ...TestCase`** turns the machine into a test
  that pytest can find and run. One run plays 100 random stories, each
  up to 20 steps long (a `settings` line in the file sets that;
  Hypothesis's default is 50, which finds the same bugs but takes most
  of the run time).

The `dict` is a good model because it's obviously right and it's *not*
`ObjectStore`'s code. If we built the model by copying `ObjectStore`, any
bug would be in both, and they'd agree perfectly about the wrong answer.

The same file has a second machine, `RepositoryMachine`, for the whole
[repository](concepts/repository.md). Its story adds files, commits, makes
[branches](concepts/branches.md) and switches between them. Its notebook
is a dict of each branch's commits, the name of the current branch, and a
dict of what's staged. After every step `list_branches()`,
`current_branch()`, `status()` and `log()` must all match the notebook.
That machine found a real bug, coming up below.

## Try It Yourself

Let's break the fingerprint on purpose and watch the inspector find it.

Open `src/pygit/hashing.py`, find `object_header`, and change its last
line, as if you'd counted *letters* instead of *bytes*:

```python
    return f"{object_type} {len(data.decode(errors="replace"))}\0".encode()  # was: len(data)
```

Run the property tests:

```bash
uv run pytest tests/test_properties.py tests/test_model.py --no-cov
```

Hypothesis reports this (trimmed to the interesting part):

```
data = b'\xc2\x80'

    @given(data=file_contents())
    def test_blob_hash_follows_gits_rule(data: bytes) -> None:
        """A file's fingerprint is SHA-1 of ``blob <size>``, a zero byte, then the file -- Git's rule."""
>       assert hash_object("blob", data) == git_hash("blob", data)
E       AssertionError: assert '800070894a4b...40f1580f85d2f' == '71d530b41fcb...79cdcffc69769'
E
E         - 71d530b41fcbe7a1f62eca1e64f79cdcffc69769
E         + 800070894a4bf7f5027a604749440f1580f85d2f
E       Failing test case: test_blob_hash_follows_gits_rule(
E           data=b'\xc2\x80',
E       )
```

Look at how small that is. Hypothesis tried hundreds of messy files,
then shrank the failure all the way down to **two bytes**, `c2 80`.
Together, those two bytes spell *one* character in UTF-8 (an invisible
control character). So the broken label said `blob 1`, but the file is
2 bytes long, and Git would have written `blob 2`. Any file of plain
English letters has one byte per letter, so the bug hides until a file
holds something else: an accent, an emoji, or a picture.

`test_blob_hash_follows_gits_rule` catches it, and so do
`test_write_then_read_gives_back_the_same_bytes` and both model checks,
because they all compare hashes with `git_hash`. The tree, diff and
damaged-file properties stay green: they never ask what the hash should
be.

The example tests all still pass. Only the property notices. The
example that checks real Git's fingerprint uses a file saying `hello`,
which is one byte per letter.

Put the line back to `len(data)` and run the tests again. They pass.

!!! tip "Older Hypothesis versions"
    Older versions of Hypothesis print `Falsifying example:` instead of
    `Failing test case:`. It means the same thing.

## A Bug We Found

When we first ran `RepositoryMachine`, it failed on PyGit's real code --
no deliberate bug needed:

```
    | AssertionError: assert {'outer/proje...refs/escaped'} == {'outer/proje...s/../escaped'}
    |
    |   Extra items in the left set:
    |   'outer/project/.pygit/refs/escaped'
    |   Extra items in the right set:
    |   'outer/project/.pygit/refs/heads/../escaped'
    | Failing test case: <state machine>
    | state = RepositoryMachine()
    | state.repository_matches_the_dicts()
    | state.create_awkward_branch(name='../escaped')
    | state.teardown()
```

A branch is just a file in `.pygit/refs/heads`, named after the branch.
`create_branch("../escaped")` glued the name onto that folder, and `..`
means "go up one folder". So the "branch" landed in `.pygit/refs`,
outside the branches folder. A name with more `..` in it could climb
right out of the project.

The same story found more. `feature/login`, a 300-letter name or a zero
byte crashed with Python errors instead of a `RepositoryError`;
`switch_branch("")` found the branches *folder* and moved HEAD onto it;
`"trailing "` made a branch whose space HEAD lost; and, on a Mac, `Main`
and `main` turned out to be one file.

The example tests only ever used names like `feature`. The awkward
names are in the strategy because we guessed at them, but plain
`st.text()` found the invisible `\r` on its own.

The fix is a new check that runs before `create_branch` and
`switch_branch` touch a file: a name must be one plain, visible file
name (no `/`, `\`, `..`, spaces or invisible characters, and not too
long), and must not differ from another branch only in capitals or in
how an accent is spelled. (Real Git allows `feature/login`; PyGit keeps
it simpler.) `switch_branch` now looks for the exact name in `list_branches()`
instead of asking whether a file exists. Every shrunk name is pinned in
`tests/test_repository.py`, like this one:

```python
    def test_branch_name_cannot_climb_out_of_the_branches_folder(self, tmp_path: Path) -> None:
        """Regression: create_branch("../escaped") wrote .pygit/refs/escaped, outside refs/heads."""
        repo = Repository.init(tmp_path)
        with pytest.raises(RepositoryError, match="Invalid branch name"):
            repo.create_branch("../escaped")
        assert not (tmp_path / PYGIT_DIR / "refs" / "escaped").exists()
```

The damaged-file property found one more: an object file starting with
the byte `0x80` crashed `read_object` with a `UnicodeDecodeError`. The
label is now compared as bytes, without turning it into text first, so
it's refused with `ObjectTypeError`:

```python
        stored_type = header.split(b" ", 1)[0]  # was: header.split(b" ", 1)[0].decode()
        if stored_type != object_type.encode():  # was: if stored_type != object_type:
```

## Run It Yourself

Run just the property tests and the model check (100 examples each, the
same every time):

```bash
uv run pytest tests/test_properties.py tests/test_model.py --no-cov
```

The `--no-cov` turns off the coverage check, which expects the *whole*
test suite to run and would fail on two files.

Run them the long way (2,000 random examples each, different every run)
to hunt for rarer bugs. It takes a few minutes:

```bash
uv run pytest tests/test_properties.py tests/test_model.py --no-cov --hypothesis-profile=thorough
```

The normal run uses a fixed seed, so it tries the same inputs every time
and a passing build means the same thing on every computer. The thorough
run is random, so each time you run it the inspector brings a brand-new
box of photos. Both settings live in `conftest.py` at the top of the
project.

## Your Turn

Write one new property for PyGit. Think about [diffs](concepts/diff.md):
what should `diff_lines(text, text)` look like, whatever the text is?
What's the strategy that makes the text? What's the `assert`? Run it and
watch it pass. Then break `diff_lines` on purpose and watch the
inspector find it.
