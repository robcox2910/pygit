"""Object store -- the photo album for blobs, trees, and commits.

Git stores everything as "objects" identified by their hash. This
module handles reading and writing those objects to disk. Objects
are stored in `.pygit/objects/` using the first two characters of
the hash as a subdirectory name (to avoid one huge folder).

Example:
    Hash: 943a702d06f34599aee1f8da8ef9f7296031d699
    Path: .pygit/objects/94/3a702d06f34599aee1f8da8ef9f7296031d699

Each object file holds a small label -- its type and size, like
``blob 13`` and a zero byte -- followed by the content, exactly as real
Git does. (Real Git also squashes the file with zlib compression; we
skip that so you can open the files and look inside.)

"""

from pathlib import Path

from pygit.errors import ObjectNotFoundError, ObjectTypeError
from pygit.hashing import hash_object, object_header

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

    def write_object(self, object_type: str, data: bytes) -> str:
        """Store an object and return its hash.

        Think of it like filing a photo in an album -- once it's
        filed under its label (hash), you can always find it again.
        Works for any object type: blobs, trees, or commits.

        If the object already exists (same type and content), this is a
        no-op (content-addressable means no duplicates).

        Args:
            object_type: What kind of object this is ("blob", "tree" or "commit").
            data: The object's content.

        Returns:
            The SHA-1 hash of the labelled object.

        """
        object_hash = hash_object(object_type, data)
        path = self._object_path(object_hash)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(object_header(object_type, data) + data)
        return object_hash

    def read_object(self, object_hash: str, object_type: str) -> bytes:
        """Retrieve an object's content by its hash, checking its type label.

        Like looking up a photo in the album by its label -- hand over the
        hash and the kind of thing you expect, and get back its content.

        Args:
            object_hash: The SHA-1 hash of the object.
            object_type: The type you expect ("blob", "tree" or "commit").

        Returns:
            The object's content, without its label.

        Raises:
            ObjectNotFoundError: If no object with that hash exists.
            ObjectTypeError: If the object is labelled with a different type
                (or its label is damaged).

        """
        path = self._object_path(object_hash)
        if not path.exists():
            msg = f"Object not found: {object_hash}"
            raise ObjectNotFoundError(msg)
        header, _, data = path.read_bytes().partition(b"\0")
        # Compare the label as bytes: a damaged file's label may not be text.
        stored_type = header.split(b" ", 1)[0]
        if stored_type != object_type.encode():
            label = stored_type.decode(errors="replace")
            msg = f"Object {object_hash} is a {label}, not a {object_type}"
            raise ObjectTypeError(msg)
        return data

    def exists(self, object_hash: str) -> bool:
        """Check whether an object with the given hash exists."""
        return self._object_path(object_hash).exists()
