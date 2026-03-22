# Branches

## Choose Your Own Adventure

Remember those "Choose Your Own Adventure" books? At certain points,
you pick a path: "Turn to page 42 for the cave, or page 67 for the
forest." Each path is a different story branching off from the same
point.

Git **branches** work the same way. You can create a new branch to
try something out, and if you don't like it, you go back to where
you were. If you do like it, you **merge** it back into the main
story.

```
main:    C1 ← C2 ← C3 ← C4
                      ↑
feature:              └── C5 ← C6
```

Commits C5 and C6 only exist on the `feature` branch. The `main`
branch doesn't see them until you merge.

## What IS a Branch?

Here's the beautiful secret: a branch is just a **text file** that
contains a commit hash. That's it!

```
.pygit/refs/heads/main      → "abc123..."
.pygit/refs/heads/feature   → "def456..."
```

Creating a branch = writing a new file with the current commit hash.
Switching branches = updating HEAD to point to a different branch.
Deleting a branch = deleting the file. The commits themselves are
untouched.

## HEAD: "You Are Here"

The `HEAD` file tells Git which branch you're currently on:

```
.pygit/HEAD → "ref: refs/heads/main"
```

When you commit, Git updates the current branch's pointer to the
new commit. HEAD doesn't change -- it still points to the branch.
But the branch now points to a different commit.

## Branches in PyGit

```python
from pygit.repository import Repository

repo = Repository.init("/path/to/project")
# ... add files and commit ...

# Create a new branch.
repo.create_branch("feature")

# List all branches.
print(repo.list_branches())  # ["feature", "main"]

# Switch to the new branch.
repo.switch_branch("feature")
print(repo.current_branch())  # "feature"
```

## What We Test

- Creating a branch stores a commit hash in a file.
- Listing branches shows all branch names.
- HEAD tracks the current branch.
- Switching branches updates HEAD.

## What's Next?

You've learned every concept behind Git! Blobs, trees, commits,
the repository, staging, diffs, and branches. You've built a
version control system from scratch -- the same tool that powers
GitHub and every professional software team in the world.
