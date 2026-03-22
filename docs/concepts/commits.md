# Commits

## Diary Entries

Imagine keeping a diary about your project:

> **March 22, 2026** -- Added Chapter 3 to the story. The book now
> has 3 chapters and 45 pages.

Each diary entry records *when* something happened, *who* did it,
*what* changed (the snapshot), and *what came before* (the previous
entry).

A Git **commit** is exactly this:

```
Commit abc123:
  tree:    def456          ← "this is what the project looked like"
  parent:  789ghi          ← "this is the previous snapshot"
  author:  Alice           ← "who did it"
  date:    2026-03-22      ← "when"
  message: "Add Chapter 3" ← "why"
```

## Commits Form a Chain

Each commit points to its parent (the commit before it). This creates
a chain -- your project's timeline:

```
Commit 3          Commit 2         Commit 1
"Add Ch.3"   ←──  "Fix typo"  ←── "Start story"
tree: ...         tree: ...        tree: ...
parent: C2        parent: C1       parent: None
```

The first commit has no parent (it's the beginning of time). Every
other commit points back to what came before.

## Walking the Chain

To see the full history, you start at the latest commit and follow
the parent links backwards. That's what `pygit log` does.

## What We Test

- A commit stores tree hash, parent, author, date, and message.
- Commits form a linked chain via parent pointers.
- The first commit has no parent.
- Each commit gets a unique hash.

## Next Up

We have all the building blocks: blobs, trees, and commits. Now we
need a place to keep them. Head to [Repository](repository.md).
