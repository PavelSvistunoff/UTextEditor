"""Conservative line-based three-way merge for explicit author review."""

from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass(frozen=True)
class MergeResult:
    text: str
    conflicts: int


@dataclass(frozen=True)
class _Edit:
    start: int
    end: int
    lines: tuple[str, ...]


def _changes(base: list[str], other: list[str]) -> list[_Edit]:
    matcher = SequenceMatcher(None, base, other, autojunk=False)
    return [
        _Edit(a, b, tuple(other[c:d]))
        for operation, a, b, c, d in matcher.get_opcodes()
        if operation != "equal"
    ]


def _apply(base: list[str], start: int, end: int, edits: list[_Edit]) -> str:
    result = []
    position = start
    for edit in edits:
        result.extend(base[position:edit.start])
        result.extend(edit.lines)
        position = edit.end
    result.extend(base[position:end])
    return "".join(result)


def _conflict(buffer: str, disk: str) -> str:
    def section(value: str) -> str:
        return value if not value or value.endswith("\n") else value + "\n"

    return "<<<<<<< OPEN BUFFER\n" + section(buffer) + "=======\n" + section(disk) + ">>>>>>> DISK\n"


def merge_text(base: str, buffer: str, disk: str) -> MergeResult:
    """Merge unambiguous changes; flag overlapping changes for manual review.

    Returned text is a proposal only. It must never be written without explicit
    review and a new disk conflict check. Adjacent edits are conservatively
    grouped, including insertions at a changed range's boundaries.
    """
    if buffer == disk:
        return MergeResult(buffer, 0)
    if buffer == base:
        return MergeResult(disk, 0)
    if disk == base:
        return MergeResult(buffer, 0)
    original = base.splitlines(keepends=True)
    mine = buffer.splitlines(keepends=True)
    theirs = disk.splitlines(keepends=True)
    # SequenceMatcher can take quadratic time for repeated lines. For large
    # inputs, present the complete alternatives instead of blocking the UI.
    if (max(len(original), len(mine), len(theirs)) > 2000
            or max(len(base), len(buffer), len(disk)) > 200_000):
        return MergeResult(_conflict(buffer, disk), 1)
    changes = sorted(
        [(edit.start, 0, edit) for edit in _changes(original, mine)]
        + [(edit.start, 1, edit) for edit in _changes(original, theirs)],
        key=lambda item: (item[0], item[1]),
    )
    output = []
    position = 0
    conflicts = 0
    i = 0
    while i < len(changes):
        start = changes[i][2].start
        end = changes[i][2].end
        group = []
        while i < len(changes) and changes[i][2].start <= end:
            _, side, edit = changes[i]
            group.append((side, edit))
            end = max(end, edit.end)
            i += 1
        output.extend(original[position:start])
        left = [edit for side, edit in group if side == 0]
        right = [edit for side, edit in group if side == 1]
        left_text = _apply(original, start, end, left)
        right_text = _apply(original, start, end, right)
        if not left:
            output.append(right_text)
        elif not right or left_text == right_text:
            output.append(left_text)
        else:
            output.append(_conflict(left_text, right_text))
            conflicts += 1
        position = end
    output.extend(original[position:])
    return MergeResult("".join(output), conflicts)
