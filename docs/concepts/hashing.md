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
from pygit.hashing import hash_content

hash_content("Hello, world!")
# "943a702d06f34599aee1f8da8ef9f7296031d699"
```

The same input always produces the same output. Different inputs
(almost) always produce different outputs.

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
