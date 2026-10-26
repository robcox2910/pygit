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
  with Git's `blob <size>` label in front -- so file (blob) hashes match
  `git hash-object` exactly. (Trees and commits use a simpler JSON layout than
  real Git, so their hashes differ.)
- **Nested trees** -- Every folder gets its own tree, just like real Git.
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

## Releasing

Other projects in the series ([PyStack](https://github.com/robcox2910/pystack)) use a released version of this one from PyPI,
not whatever is on `main`. To publish a change for them:

1. Merge the change to `main`.
2. Release it: `gh release create vX.Y.Z --target main --generate-notes`
   (or push a `vX.Y.Z` tag); the release workflow publishes it to PyPI.
   A change to the public API bumps the minor version (`v0.1.0` → `v0.2.0`);
   anything else bumps the patch (`v0.1.0` → `v0.1.1`).
3. In each project that uses it, raise the `fromscratch-pygit>=X.Y.Z` floor in
   `pyproject.toml`, run `uv lock --upgrade-package fromscratch-pygit`, and open
   a pull request so CI checks the pair together.

<!-- series:start -->
## Related Projects

This project is one of a series that builds real systems "from scratch in Python" to teach how they work. See the [series home](https://robcox2910.github.io/) for the full story.

| Project | What it teaches | Repository | Docs | PyPI |
| --- | --- | --- | --- | --- |
| PyOS | Operating systems | [py-os](https://github.com/robcox2910/py-os) | [Docs](https://robcox2910.github.io/py-os/) | [fromscratch-pyos](https://pypi.org/project/fromscratch-pyos/) |
| Pebble | Compilers and programming languages | [pebble-lang](https://github.com/robcox2910/pebble-lang) | [Docs](https://robcox2910.github.io/pebble-lang/) | [fromscratch-pebble](https://pypi.org/project/fromscratch-pebble/) |
| PyDB | Relational databases | [pydb](https://github.com/robcox2910/pydb) | [Docs](https://robcox2910.github.io/pydb/) | [fromscratch-pydb](https://pypi.org/project/fromscratch-pydb/) |
| PyKV | Key-value stores | [pykv](https://github.com/robcox2910/pykv) | [Docs](https://robcox2910.github.io/pykv/) | [fromscratch-pykv](https://pypi.org/project/fromscratch-pykv/) |
| PyDocDB | Document databases | [pydoc-db](https://github.com/robcox2910/pydoc-db) | [Docs](https://robcox2910.github.io/pydoc-db/) | [fromscratch-pydocdb](https://pypi.org/project/fromscratch-pydocdb/) |
| PyGraphDB | Graph databases | [pygraphdb](https://github.com/robcox2910/pygraphdb) | [Docs](https://robcox2910.github.io/pygraphdb/) | [fromscratch-pygraphdb](https://pypi.org/project/fromscratch-pygraphdb/) |
| PyTSDB | Time-series databases | [pytsdb](https://github.com/robcox2910/pytsdb) | [Docs](https://robcox2910.github.io/pytsdb/) | [fromscratch-pytsdb](https://pypi.org/project/fromscratch-pytsdb/) |
| PyVecDB | Vector databases | [pyvecdb](https://github.com/robcox2910/pyvecdb) | [Docs](https://robcox2910.github.io/pyvecdb/) | [fromscratch-pyvecdb](https://pypi.org/project/fromscratch-pyvecdb/) |
| PyColDB | Column-family databases | [pycoldb](https://github.com/robcox2910/pycoldb) | [Docs](https://robcox2910.github.io/pycoldb/) | [fromscratch-pycoldb](https://pypi.org/project/fromscratch-pycoldb/) |
| PyCrypt | Cryptography | [pycrypt](https://github.com/robcox2910/pycrypt) | [Docs](https://robcox2910.github.io/pycrypt/) | [fromscratch-pycrypt](https://pypi.org/project/fromscratch-pycrypt/) |
| PyNet | Computer networking | [pynet](https://github.com/robcox2910/pynet) | [Docs](https://robcox2910.github.io/pynet/) | [fromscratch-pynet](https://pypi.org/project/fromscratch-pynet/) |
| PyWeb | HTTP web servers | [pyweb](https://github.com/robcox2910/pyweb) | [Docs](https://robcox2910.github.io/pyweb/) | [fromscratch-pyweb](https://pypi.org/project/fromscratch-pyweb/) |
| **PyGit** | **Version control** | [pygit](https://github.com/robcox2910/pygit) | [Docs](https://robcox2910.github.io/pygit/) | [fromscratch-pygit](https://pypi.org/project/fromscratch-pygit/) |
| PySearch | Search engines | [pysearch](https://github.com/robcox2910/pysearch) | [Docs](https://robcox2910.github.io/pysearch/) | [fromscratch-pysearch](https://pypi.org/project/fromscratch-pysearch/) |
| PyMQ | Message queues | [pymq](https://github.com/robcox2910/pymq) | [Docs](https://robcox2910.github.io/pymq/) | [fromscratch-pymq](https://pypi.org/project/fromscratch-pymq/) |
| PyLLM | Language models (the brain) | [pyllm](https://github.com/robcox2910/pyllm) | [Docs](https://robcox2910.github.io/pyllm/) | [fromscratch-pyllm](https://pypi.org/project/fromscratch-pyllm/) |
| PyScheduler | Job scheduling | [pyscheduler](https://github.com/robcox2910/pyscheduler) | [Docs](https://robcox2910.github.io/pyscheduler/) | [fromscratch-pyscheduler](https://pypi.org/project/fromscratch-pyscheduler/) |
| PyStack | Full-stack integration | [pystack](https://github.com/robcox2910/pystack) | [Docs](https://robcox2910.github.io/pystack/) | [fromscratch-pystack](https://pypi.org/project/fromscratch-pystack/) |
<!-- series:end -->

<!-- docs:start -->
## Documentation

Full docs (with kid-friendly explanations of every idea): https://robcox2910.github.io/pygit/

## Install

[![PyPI](https://img.shields.io/pypi/v/fromscratch-pygit)](https://pypi.org/project/fromscratch-pygit/)

```bash
pip install fromscratch-pygit
```

Or get the whole series at once: `pip install fromscratch-pystack`.
<!-- docs:end -->

## License

MIT
