"""Tests for the command-line interface."""

from pathlib import Path

import pytest

from pygit.cli import main

SAMPLE_FILENAME = "hello.txt"
SAMPLE_CONTENT = "Hello, world!"
COMMIT_MESSAGE = "Initial commit"


def test_init_creates_repository(tmp_path: Path) -> None:
    """Create the .pygit directory via the init command."""
    exit_code = main(["-C", str(tmp_path), "init"])
    assert exit_code == 0
    assert (tmp_path / ".pygit").is_dir()


def test_add_stages_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Stage a file via the add command."""
    main(["-C", str(tmp_path), "init"])
    (tmp_path / SAMPLE_FILENAME).write_text(SAMPLE_CONTENT, encoding="utf-8")
    exit_code = main(["-C", str(tmp_path), "add", SAMPLE_FILENAME])
    assert exit_code == 0
    assert SAMPLE_FILENAME in capsys.readouterr().out


def test_commit_and_log(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Commit staged files and show them in the log."""
    main(["-C", str(tmp_path), "init"])
    (tmp_path / SAMPLE_FILENAME).write_text(SAMPLE_CONTENT, encoding="utf-8")
    main(["-C", str(tmp_path), "add", SAMPLE_FILENAME])
    capsys.readouterr()

    exit_code = main(["-C", str(tmp_path), "commit", "-m", COMMIT_MESSAGE])
    assert exit_code == 0

    assert main(["-C", str(tmp_path), "log"]) == 0
    assert COMMIT_MESSAGE in capsys.readouterr().out


def test_status_reports_staged_files(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Report staged files via the status command."""
    main(["-C", str(tmp_path), "init"])
    (tmp_path / SAMPLE_FILENAME).write_text(SAMPLE_CONTENT, encoding="utf-8")
    main(["-C", str(tmp_path), "add", SAMPLE_FILENAME])
    capsys.readouterr()

    assert main(["-C", str(tmp_path), "status"]) == 0
    assert SAMPLE_FILENAME in capsys.readouterr().out


def test_status_when_nothing_staged(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Report an empty staging area."""
    main(["-C", str(tmp_path), "init"])
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "status"]) == 0
    assert "Nothing staged" in capsys.readouterr().out


def test_no_command_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Return an error and print help when no command is given."""
    exit_code = main([])
    assert exit_code == 1
    assert "usage" in capsys.readouterr().out.lower()


def test_error_returns_exit_code_one(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Return exit code 1 and a message when a PyGit error occurs."""
    # Adding a missing file in an initialized repo raises RepositoryError.
    main(["-C", str(tmp_path), "init"])
    exit_code = main(["-C", str(tmp_path), "add", "does_not_exist.txt"])
    assert exit_code == 1
    assert "error" in capsys.readouterr().err.lower()
