# Repository

## The Diary Itself

Blobs are photos. Trees are tables of contents. Commits are diary
entries. The **repository** is the diary itself -- the folder that
holds everything.

When you run `pygit init`, it creates a `.pygit` folder:

```
my-project/
├── .pygit/
│   ├── objects/       ← all blobs, trees, and commits
│   ├── refs/
│   │   └── heads/     ← branch pointers
│   ├── HEAD           ← which branch you're on
│   └── index          ← the staging area
├── readme.txt
└── src/
    └── main.py
```

## The Key Parts

| File/Folder | What It Does | Analogy |
|-------------|-------------|---------|
| `objects/` | Stores all blobs, trees, and commits | The photo album |
| `refs/heads/` | Branch pointers (name → commit hash) | Bookmarks |
| `HEAD` | Points to the current branch | "You are here" |
| `index` | The staging area | Shopping cart |

## Using PyGit

```python
from pygit.repository import Repository

# Create a new repository.
repo = Repository.init("/path/to/project")

# Add files to the staging area.
repo.add("readme.txt")
repo.add("src/main.py")

# Create a commit.
repo.commit("Initial commit", author="Alice")

# View the log.
for entry in repo.log():
    print(f"{entry.hash[:8]} {entry.message}")
```

## What We Test

- `init` creates the `.pygit` directory structure.
- The HEAD file starts pointing to `main`.
- Objects are stored and retrieved correctly.
- The repository tracks the current branch.

## Next Up

Before committing, you need to choose *which* changes to include.
Head to [Staging](staging.md).
