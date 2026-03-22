"""Tests for the diff module."""

from pygit.diff import diff_lines, format_diff

ADDED_PREFIX = "+"
REMOVED_PREFIX = "-"
UNCHANGED_PREFIX = " "


class TestDiffLines:
    """Verify that diff_lines detects additions, removals, and unchanged lines."""

    def test_added_lines(self) -> None:
        """Mark new lines with a '+' prefix."""
        old = ""
        new = "hello\nworld"
        result = diff_lines(old, new)
        assert any(line.startswith(ADDED_PREFIX) for line in result)
        assert "hello" in result[0]

    def test_removed_lines(self) -> None:
        """Mark deleted lines with a '-' prefix."""
        old = "hello\nworld"
        new = ""
        result = diff_lines(old, new)
        assert any(line.startswith(REMOVED_PREFIX) for line in result)

    def test_unchanged_lines(self) -> None:
        """Mark common lines with a ' ' prefix."""
        old = "hello\nworld"
        new = "hello\nplanet"
        result = diff_lines(old, new)
        unchanged = [line for line in result if line.startswith(UNCHANGED_PREFIX)]
        assert len(unchanged) >= 1
        assert "hello" in unchanged[0]

    def test_identical_files_empty_diff(self) -> None:
        """Produce only unchanged lines for identical content."""
        content = "line one\nline two"
        result = diff_lines(content, content)
        for line in result:
            assert line.startswith(UNCHANGED_PREFIX)

    def test_completely_different(self) -> None:
        """Show removals and additions when nothing matches."""
        old = "alpha\nbeta"
        new = "gamma\ndelta"
        result = diff_lines(old, new)
        removed = [line for line in result if line.startswith(REMOVED_PREFIX)]
        added = [line for line in result if line.startswith(ADDED_PREFIX)]
        assert len(removed) > 0
        assert len(added) > 0


class TestFormatDiff:
    """Verify that format_diff joins diff lines into a display string."""

    def test_format_joins_lines(self) -> None:
        """Join diff lines with newlines."""
        diff = ["+ added", "- removed", "  same"]
        result = format_diff(diff)
        assert result == "+ added\n- removed\n  same"

    def test_format_empty_diff(self) -> None:
        """Return an empty string for an empty diff."""
        result = format_diff([])
        assert result == ""
