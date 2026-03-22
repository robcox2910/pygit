"""Object store -- the photo album for blobs, trees, and commits.

Git stores everything as "objects" identified by their hash. This
module handles reading and writing those objects to disk. Objects
are stored in `.pygit/objects/` using the first two characters of
the hash as a subdirectory name (to avoid one huge folder).

Example:
    Hash: 943a702d06f34599aee1f8da8ef9f7296031d699
    Path: .pygit/objects/94/3a702d06f34599aee1f8da8ef9f7296031d699

"""

from pathlib import Path

from pygit.errors import ObjectNotFoundError
from pygit.hashing import hash_content

PREFIX_LENGTH = 2


class ObjectStore:
    """Read and write content-addressed objects.

    Each object is stored as a file named by its hash, inside a
    subdirectory named by the first two characters of the hash.

    Args:
        objects_dir: Path to the `.pygit/objects` directory.

    """

    __slots__ = ("_objects_dir",)

    def __init__(self, objects_dir: str | Path) -> None:
        """Create an object store at the given path."""
        self._objects_dir = Path(objects_dir)
        self._objects_dir.mkdir(parents=True, exist_ok=True)

    def _object_path(self, object_hash: str) -> Path:
        """Return the filesystem path for an object hash."""
        prefix = object_hash[:PREFIX_LENGTH]
        rest = object_hash[PREFIX_LENGTH:]
        return self._objects_dir / prefix / rest

    def write_blob(self, content: str) -> str:
        """Store content as a blob and return its hash.

        If the blob already exists (same content), this is a no-op
        (content-addressable means no duplicates).

        Args:
            content: The file content to store.

        Returns:
            The SHA-1 hash of the content.

        """
        blob_hash = hash_content(content)
        path = self._object_path(blob_hash)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return blob_hash

    def read_blob(self, blob_hash: str) -> str:
        """Retrieve a blob's content by its hash.

        Args:
            blob_hash: The SHA-1 hash of the blob.

        Returns:
            The blob's content as a string.

        Raises:
            ObjectNotFoundError: If no blob with that hash exists.

        """
        path = self._object_path(blob_hash)
        if not path.exists():
            msg = f"Object not found: {blob_hash}"
            raise ObjectNotFoundError(msg)
        return path.read_text(encoding="utf-8")

    def exists(self, object_hash: str) -> bool:
        """Check whether an object with the given hash exists."""
        return self._object_path(object_hash).exists()
