# Trees

## The Table of Contents

A blob is a photo of one page. But a book has many pages, organized
into chapters. The **table of contents** lists which pages are in
which chapters.

A Git **tree** is that table of contents. It's a list of entries,
each with:

- A **name** (the filename)
- A **type** (blob for files, tree for subdirectories)
- A **hash** (pointing to the blob or sub-tree)

```
Tree (root):
  readme.txt    → blob abc123
  src/          → tree def456
    main.py     → blob 789ghi
    utils.py    → blob jkl012
```

## Trees Can Contain Trees

Just like folders can contain subfolders, trees can contain other
trees. This lets Git represent any directory structure:

```
root tree
├── readme.txt  (blob)
├── src/        (tree)
│   ├── main.py   (blob)
│   └── utils.py  (blob)
└── tests/      (tree)
    └── test_main.py (blob)
```

## Trees in PyGit

```python
from pygit.tree import TreeEntry, build_tree, parse_tree

# Build a tree from file entries.
entries = [
    TreeEntry(name="readme.txt", entry_type="blob", hash="abc123"),
    TreeEntry(name="main.py", entry_type="blob", hash="def456"),
]
tree_hash, tree_content = build_tree(entries)

# Parse the tree back from its serialized form.
restored = parse_tree(tree_content)
print(restored[0].name)  # "main.py" (sorted by name)
```

## What We Test

- A tree stores a list of named entries.
- Each entry has a name, type, and hash.
- Trees can reference blobs and other trees.
- The same set of entries always produces the same tree hash.

## Next Up

We can snapshot a single file (blob) and a whole directory (tree).
Now we need to record *when* and *why* that snapshot was taken.
Head to [Commits](commits.md).
