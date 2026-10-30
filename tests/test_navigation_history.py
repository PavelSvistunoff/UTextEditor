from weakref import ref

from app.ui.navigation_history import NavigationHistory, NavigationPoint


class Editor:
    pass


def test_history_is_bounded_skips_stale_points_and_discards_forward_branch():
    editor = Editor()
    history = NavigationHistory(limit=3)
    points = [NavigationPoint(ref(editor), i, i, i, None, None, None) for i in range(5)]
    for point in points[:4]:
        history.record(point)
    assert history.points == points[1:4]
    restored = []

    def restore(point):
        restored.append(point.revision)
        return point.revision != 2

    assert history.move(-1, restore)
    assert restored == [2, 1]
    history.record(points[4])
    assert history.points == [points[1], points[4]]
    assert not history.move(1, restore)
