"""Custom exceptions for PyGit.

Clear error messages help you understand what went wrong. Each
exception type tells you the category of the problem.
"""


class PyGitError(Exception):
    """Base exception for all PyGit errors."""


class ObjectNotFoundError(PyGitError):
    """Raise when a requested object hash doesn't exist."""


class RepositoryError(PyGitError):
    """Raise when a repository operation fails."""
