# Hashing

## Fingerprints for Files

Put your thumb on an ink pad and press it on paper. That thumbprint is
unique to you -- no one else in the world has the same one. And no
matter how many times you press your thumb, you always get the same
print.

A **hash** works the same way for data. Feed any content into a hash
function and you get a unique fingerprint:

```
"Hello, world!" → 943a702d06f34599aee1f8da8ef9f7296031d699
"Hello, world?" → a different fingerprint entirely
```

## Why Hashing Matters for Git

Git uses hashes for everything:

1. **Identity** -- each file version gets a unique ID based on its content
2. **Integrity** -- if the content changes, the hash changes (corruption detected!)
3. **Deduplication** -- same content = same hash = stored only once

If two files are identical (even with different names), they get the
same hash and Git stores the content only once. Efficient!

## SHA-1: Git's Hash Function

Git uses **SHA-1**, which produces a 40-character hexadecimal string.
Our PyGit uses the same algorithm:

```python
from pygit.hashing import hash_object

hash_object("blob", b"Hello, world!")
# "5dd01c177f5d7d1be5346a5bc18a569a7410c2ef"
```

The same input always produces the same output. Different inputs
(almost) always produce different outputs.

## The Label on Every Object

Before taking the fingerprint, Git sticks a little **label** on the front
of every object: what *kind* of object it is, and how many bytes long. For
a file containing `Hello, world!` (13 bytes) the label is `blob 13`,
followed by a special zero byte, and *then* the content.

Why bother? Imagine a file that happens to contain exactly the same text
as one of Git's tree objects. Without labels they'd get the same
fingerprint and Git would mix them up. With labels, a `blob` and a `tree`
can never collide.

PyGit does exactly what real Git does here -- so if you run
`git hash-object` on a file, real Git prints **the same fingerprint**
PyGit gives it. (Our trees and commits are written in a simpler format
than real Git's, so *their* fingerprints differ.)

## How We Store Hashed Content

Git stores objects in a folder structure based on the first two
characters of the hash:

```
.pygit/objects/
├── 94/
│   └── 3a702d06f34599aee1f8da8ef9f7296031d699  (the file)
├── a1/
│   └── b2c3d4e5f6...
```

This keeps any single folder from getting too crowded.

## What We Test

- Same content always produces the same hash.
- Different content produces different hashes.
- The hash is a 40-character hex string.
- Content can be stored and retrieved by hash.

## Next Up

Now that we can fingerprint content, let's store actual files.
Head to [Blobs](blobs.md).
