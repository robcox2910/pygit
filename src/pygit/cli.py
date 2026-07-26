"""Command line -- the control panel for PyGit.

Like the row of buttons on a machine, this lets you drive PyGit from
your terminal: press a button (type a command) and PyGit does the work.
It wires the ``pygit`` command to the :class:`~pygit.repository.Repository`
so you can init, add, commit, log, and check status without writing any
Python.
"""

import argparse
import sys

from pygit.errors import PyGitError
from pygit.repository import Repository

SHORT_HASH_LENGTH = 8


def _cmd_init(args: argparse.Namespace) -> int:
    """Create a new repository in the given directory."""
    repo = Repository.init(args.path)
    print(f"Initialized empty pygit repository in {repo.path}")
    return 0


def _cmd_add(args: argparse.Namespace) -> int:
    """Stage a file for the next commit."""
    repo = Repository(args.path)
    blob_hash = repo.add(args.file)
    print(f"Staged {args.file} ({blob_hash[:SHORT_HASH_LENGTH]})")
    return 0


def _cmd_commit(args: argparse.Namespace) -> int:
    """Record the staged files as a new commit."""
    repo = Repository(args.path)
    commit_hash = repo.commit(args.message, author=args.author)
    print(f"[{repo.current_branch()} {commit_hash[:SHORT_HASH_LENGTH]}] {args.message}")
    return 0


def _cmd_log(args: argparse.Namespace) -> int:
    """Print the commit history, newest first."""
    repo = Repository(args.path)
    for commit in repo.log():
        print(f"commit {commit.commit_hash}")
        print(f"Author: {commit.author}")
        print(f"Date:   {commit.timestamp}")
        print(f"\n    {commit.message}\n")
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    """Print the files currently staged for commit."""
    repo = Repository(args.path)
    staged = repo.status()
    if not staged:
        print("Nothing staged for commit.")
        return 0
    print("Staged files:")
    for name in sorted(staged):
        print(f"  {name}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="pygit",
        description="A tiny version control system built from scratch.",
    )
    parser.add_argument(
        "-C",
        dest="path",
        default=".",
        help="Run as if pygit was started in this directory.",
    )
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Create a new repository.")
    init_parser.set_defaults(func=_cmd_init)

    add_parser = subparsers.add_parser("add", help="Stage a file for the next commit.")
    add_parser.add_argument("file", help="Path to the file to stage.")
    add_parser.set_defaults(func=_cmd_add)

    commit_parser = subparsers.add_parser("commit", help="Record staged changes.")
    commit_parser.add_argument("-m", "--message", required=True, help="The commit message.")
    commit_parser.add_argument("--author", default="Anonymous", help="The author's name.")
    commit_parser.set_defaults(func=_cmd_commit)

    log_parser = subparsers.add_parser("log", help="Show the commit history.")
    log_parser.set_defaults(func=_cmd_log)

    status_parser = subparsers.add_parser("status", help="Show staged files.")
    status_parser.set_defaults(func=_cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the ``pygit`` command-line tool.

    Args:
        argv: The command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        A process exit code: 0 on success, 1 on error.

    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    try:
        result: int = args.func(args)
    except PyGitError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return result


if __name__ == "__main__":
    raise SystemExit(main())
