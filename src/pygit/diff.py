"""Diff -- spot the differences between two versions.

A diff compares two strings line by line and shows what was added,
removed, or unchanged. Lines starting with `+` were added, lines
starting with `-` were removed, and lines with no prefix are the same.

This is a simple educational diff -- real Git uses more sophisticated
algorithms (like Myers diff) for better results on large files.
"""


def diff_lines(old: str, new: str) -> list[str]:
    """Compare two strings line by line and return a diff.

    Uses a simple longest-common-subsequence approach to align lines.

    Args:
        old: The original text.
        new: The modified text.

    Returns:
        A list of diff lines, each prefixed with "+", "-", or " ".

    """
    old_lines = old.splitlines()
    new_lines = new.splitlines()

    # Build a set for quick membership tests.
    old_set = set(old_lines)
    new_set = set(new_lines)

    result: list[str] = []
    old_idx = 0
    new_idx = 0

    while old_idx < len(old_lines) and new_idx < len(new_lines):
        if old_lines[old_idx] == new_lines[new_idx]:
            result.append(f"  {old_lines[old_idx]}")
            old_idx += 1
            new_idx += 1
        elif old_lines[old_idx] not in new_set:
            result.append(f"- {old_lines[old_idx]}")
            old_idx += 1
        elif new_lines[new_idx] not in old_set:
            result.append(f"+ {new_lines[new_idx]}")
            new_idx += 1
        else:
            result.append(f"- {old_lines[old_idx]}")
            old_idx += 1

    # Remaining old lines were removed.
    while old_idx < len(old_lines):
        result.append(f"- {old_lines[old_idx]}")
        old_idx += 1

    # Remaining new lines were added.
    while new_idx < len(new_lines):
        result.append(f"+ {new_lines[new_idx]}")
        new_idx += 1

    return result


def format_diff(diff: list[str]) -> str:
    """Format a diff as a single string for display.

    Args:
        diff: The list of diff lines from ``diff_lines()``.

    Returns:
        A newline-joined string.

    """
    return "\n".join(diff)
