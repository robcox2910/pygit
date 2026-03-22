# What Is Version Control?

## The Time Machine for Your Code

Imagine you're writing a story. You finish Chapter 3 and it's great.
Then you rewrite Chapter 3 and... it's terrible. You wish you could
go back to the old version. But you saved over it. It's gone.

**Version control** is a time machine that prevents this. Every time
you save a snapshot (called a **commit**), it remembers exactly what
every file looked like at that moment. You can always go back.

## Why Git?

Git is the version control system used by almost every programmer in
the world. GitHub, where you probably found this project, is built on
Git. Understanding how Git works inside is like understanding how a
car engine works -- you don't need to know it to drive, but knowing it
makes you a much better driver.

## How Does Git Actually Work?

Here's the secret: Git is surprisingly simple inside. It's built from
just a few building blocks:

### 1. Everything Gets a Fingerprint

When Git stores a file, it doesn't use the filename. Instead, it
calculates a **hash** -- a unique fingerprint based on the content.
Two files with the same content always get the same fingerprint, even
if they have different names.

```
"Hello, world!" → a0b1c2d3e4f5...  (always the same)
"Hello, world?" → 9f8e7d6c5b4a...  (different content = different fingerprint)
```

### 2. Three Types of Objects

Git stores everything as one of three types:

| Object | What It Is | Analogy |
|--------|-----------|---------|
| **Blob** | The content of a single file | A photo of one page |
| **Tree** | A list of files and their fingerprints | A table of contents |
| **Commit** | A snapshot with a message and a date | A diary entry |

### 3. Commits Form a Chain

Each commit points to the one before it, forming a chain:

```
Commit 3 → Commit 2 → Commit 1
"Add Ch.3"  "Fix typo"  "Start story"
```

You can walk backwards along the chain to see every version that
ever existed. That's your timeline.

### 4. Branches Are Just Labels

A **branch** is just a sticky note pointing to a commit. The `main`
branch points to the latest commit. When you create a new branch,
you're just putting a new sticky note on the same commit.

```
main ──→ Commit 3 → Commit 2 → Commit 1
          ↑
feature ──┘  (both point to the same commit... for now)
```

## Our Building Blocks

| Concept | Doc | What It Does |
|---------|-----|--------------|
| **Hashing** | [hashing.md](concepts/hashing.md) | Calculate fingerprints for content |
| **Blobs** | [blobs.md](concepts/blobs.md) | Store file contents by fingerprint |
| **Trees** | [trees.md](concepts/trees.md) | Snapshot a directory structure |
| **Commits** | [commits.md](concepts/commits.md) | Record a moment in history |
| **Repository** | [repository.md](concepts/repository.md) | The `.pygit` folder that holds it all |
| **Staging** | [staging.md](concepts/staging.md) | Choose which changes to include |
| **Diff** | [diff.md](concepts/diff.md) | Spot the differences between versions |
| **Branches** | [branches.md](concepts/branches.md) | Parallel timelines for your project |

## Let's Start!

Head to [Hashing](concepts/hashing.md) to learn how Git creates
fingerprints for your files.
