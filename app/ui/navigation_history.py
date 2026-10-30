"""Bounded session-local history of explicitly visited editor positions."""

from dataclasses import dataclass
from weakref import ReferenceType


@dataclass(frozen=True)
class NavigationPoint:
    editor: ReferenceType
    revision: int
    position: int
    anchor: int
    project: object | None
    kind: str | None
    item_id: str | None


class NavigationHistory:
    def __init__(self, limit: int = 100) -> None:
        self.limit = limit
        self.points: list[NavigationPoint] = []
        self.index = -1

    def record(self, point: NavigationPoint) -> None:
        if self.index >= 0 and self.points[self.index] == point:
            return
        del self.points[self.index + 1:]
        self.points.append(point)
        if len(self.points) > self.limit:
            del self.points[:len(self.points) - self.limit]
        self.index = len(self.points) - 1

    def move(self, direction: int, restore) -> bool:
        index = self.index + direction
        while 0 <= index < len(self.points):
            if restore(self.points[index]):
                self.index = index
                return True
            index += direction
        return False
