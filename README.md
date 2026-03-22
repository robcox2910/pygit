# PyGit

**Build your own version control system from scratch!**

PyGit is a simplified version of Git, written entirely in Python. It teaches
you how version control really works under the hood -- hashing, blobs, trees,
commits, branches, and diffs -- by building each piece yourself.

## What is version control?

Imagine you are writing a story. Every time you finish a chapter, you save a
copy so you can go back to it later. Version control does the same thing for
code -- it remembers every change you make, who made it, and why.

## Quick start

```python
from pygit.repository import Repository

# Create a new repository
repo = Repository.init("my-project")

# Create a file and stage it
with open("my-project/hello.txt", "w") as f:
    f.write("Hello, world!")

repo.add("hello.txt")

# Commit the change
commit_hash = repo.commit("Add greeting")
print(f"Created commit: {commit_hash}")

# Make another change
with open("my-project/hello.txt", "w") as f:
    f.write("Hello, everyone!")

repo.add("hello.txt")
repo.commit("Update greeting")

# See the history
for entry in repo.log():
    print(f"{entry.commit_hash[:8]} {entry.message}")
```

## Features

- **Hashing** -- Every piece of content gets a unique fingerprint using SHA-1,
  just like real Git.
- **Object store** -- Files are stored by their hash, so identical content is
  never duplicated.
- **Trees** -- Snapshots of your directory structure, like a table of contents.
- **Commits** -- Diary entries that record what changed, when, and why. Each
  commit points to its parent, forming a chain of history.
- **Branches** -- Create parallel timelines to work on different ideas without
  affecting the main project.
- **Staging area** -- Choose exactly which changes go into the next commit.
- **Diff** -- Compare two versions of a file to see what was added or removed.
- **Status** -- See what files are staged and ready to commit.

## Installation

```bash
uv sync --all-extras
```

## Running tests

```bash
uv run pytest
```

## Project structure

```
src/pygit/
    __init__.py      -- Package marker
    hashing.py       -- SHA-1 fingerprinting
    objects.py       -- Content-addressed object store
    tree.py          -- Directory snapshots
    commit.py        -- History entries
    diff.py          -- Line-by-line comparison
    repository.py    -- Ties everything together
    errors.py        -- Custom exceptions
```

## Related Projects

PyGit is part of an educational series where every layer of the
computing stack is built from scratch:

| Project | What It Teaches |
|---------|----------------|
| [PyOS](https://github.com/robcox2910/py-os) | Operating systems |
| [Pebble](https://github.com/robcox2910/pebble-lang) | Compilers and programming languages |
| [PyDB](https://github.com/robcox2910/pydb) | Relational databases |
| [PyStack](https://github.com/robcox2910/pystack) | Full-stack integration |
| [PyWeb](https://github.com/robcox2910/pyweb) | HTTP web servers |
| [PyCrypt](https://github.com/robcox2910/pycrypt) | Cryptography |
| [PyNet](https://github.com/robcox2910/pynet) | Networking |
| [PySearch](https://github.com/robcox2910/pysearch) | Full-text search |
| [PyMQ](https://github.com/robcox2910/pymq) | Message queues |

All projects use TDD, comprehensive documentation with real-world
analogies, and are designed for learners aged 12+.

## Documentation

Full docs at [robcox2910.github.io/pygit](https://robcox2910.github.io/pygit/)

## License

MIT
