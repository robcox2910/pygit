# Blobs

## Photos of Pages

Imagine you're making a scrapbook. For every page of your story, you
take a photo and label it with a number (the hash). The original page
might change, but the photo never does -- it's a permanent snapshot.

A **blob** (Binary Large Object) is Git's version of that photo. It
stores the content of a single file, identified by its hash. The blob
doesn't know the filename or where the file lives -- it just knows
the content.

## Why Separate Content from Names?

This is a clever trick. If you have two files with identical content
but different names (say `readme.txt` and `readme-backup.txt`), Git
stores the content only once as a single blob. Both filenames point
to the same blob hash.

```
readme.txt        → blob abc123  ──→ "Hello, world!"
readme-backup.txt → blob abc123  ──→ (same blob!)
```

## Blobs in PyGit

```python
from pygit.objects import ObjectStore

store = ObjectStore(".pygit/objects")

# Store an object (returns the hash).
blob_hash = store.write_object("Hello, world!")
# "943a702d06f34599aee1f8da8ef9f7296031d699"

# Read it back.
content = store.read_object(blob_hash)
# "Hello, world!"
```

## What We Test

- Writing a blob stores it and returns a hash.
- Reading a blob by hash returns the original content.
- The same content always produces the same blob hash.
- Reading a non-existent hash raises an error.

## Next Up

A blob is one file. But a project has many files in many folders.
Head to [Trees](trees.md) to learn how Git snapshots an entire
directory.
