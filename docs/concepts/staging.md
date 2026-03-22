# Staging

## The Shopping Cart

When you're shopping online, you don't buy everything the moment you
click on it. You add things to your **cart** first, then check out
when you're ready.

Git's **staging area** (also called the **index**) works the same way.
You `add` files to the staging area, picking exactly which changes
you want in your next commit. Then you `commit` to make it permanent.

```
Working directory          Staging area          Repository
(your files)               (the cart)            (the diary)

readme.txt  ──add──→  readme.txt  ──commit──→  Commit 1
main.py     ──add──→  main.py                  tree: ...
notes.txt   (not added -- stays out)            message: "Init"
```

## Why Not Just Commit Everything?

Sometimes you've changed 10 files but only 3 of those changes are
related. The staging area lets you commit the 3 related changes as
one commit and save the rest for later. This keeps your history
clean and meaningful.

## What We Test

- Adding a file puts it in the staging area.
- Only staged files are included in a commit.
- The staging area is cleared after a commit.
- Adding the same file twice updates the entry.

## Next Up

Once you've committed, you might want to see what changed between
two versions. Head to [Diff](diff.md).
