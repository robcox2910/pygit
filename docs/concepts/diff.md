# Diff

## Spot the Difference

Remember those "spot the difference" puzzles where you compare two
pictures and circle what changed? That's what `diff` does for text
files.

```
Old version:              New version:
  Line 1: Hello             Line 1: Hello
  Line 2: World             Line 2: World!    ← changed
                             Line 3: Bye       ← added
```

The diff shows exactly what was added, removed, or changed:

```diff
  Hello
- World
+ World!
+ Bye
```

Lines starting with `-` were removed. Lines starting with `+` were
added. Unchanged lines have no prefix.

## Why Diffs Matter

Diffs tell you:
- **What changed** between two versions of a file
- **What's staged** -- differences between working directory and index
- **What a commit did** -- differences between a commit and its parent

## Diff in PyGit

```python
from pygit.diff import diff_lines, format_diff

old = "Hello\nWorld"
new = "Hello\nWorld!\nBye"

changes = diff_lines(old, new)
print(format_diff(changes))
#   Hello
# - World
# + World!
# + Bye
```

## What We Test

- Added lines show with `+` prefix.
- Removed lines show with `-` prefix.
- Unchanged lines have no prefix.
- Identical files produce an empty diff.

## Next Up

You've learned all the core concepts. The last piece is **branches**
-- parallel timelines for your project. Head to [Branches](branches.md).
