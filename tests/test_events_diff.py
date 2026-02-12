"""Tests for the event diff engine and types."""

from cocapi.events._diff import diff_dicts, diff_member_tags
from cocapi.events._types import Change, Event, EventType, WarState


# ---------------------------------------------------------------------------
# diff_dicts
# ---------------------------------------------------------------------------


class TestDiffDicts:
    def test_no_changes(self):
        old = {"a": 1, "b": "x"}
        assert diff_dicts(old, old.copy()) == []

    def test_changed_field(self):
        old = {"a": 1, "b": 2}
        new = {"a": 1, "b": 3}
        changes = diff_dicts(old, new)
        assert len(changes) == 1
        assert changes[0] == Change(field="b", old_value=2, new_value=3)

    def test_added_field(self):
        old = {"a": 1}
        new = {"a": 1, "b": 2}
        changes = diff_dicts(old, new)
        assert len(changes) == 1
        assert changes[0] == Change(field="b", old_value=None, new_value=2)

    def test_removed_field(self):
        old = {"a": 1, "b": 2}
        new = {"a": 1}
        changes = diff_dicts(old, new)
        assert len(changes) == 1
        assert changes[0] == Change(field="b", old_value=2, new_value=None)

    def test_include_fields(self):
        old = {"a": 1, "b": 2, "c": 3}
        new = {"a": 10, "b": 20, "c": 30}
        changes = diff_dicts(old, new, include_fields=frozenset({"a", "c"}))
        assert len(changes) == 2
        fields = {c.field for c in changes}
        assert fields == {"a", "c"}

    def test_exclude_fields(self):
        old = {"a": 1, "b": 2, "c": 3}
        new = {"a": 10, "b": 20, "c": 30}
        changes = diff_dicts(old, new, exclude_fields=frozenset({"b"}))
        assert len(changes) == 2
        fields = {c.field for c in changes}
        assert fields == {"a", "c"}

    def test_nested_dict_changed(self):
        old = {"a": {"x": 1}}
        new = {"a": {"x": 2}}
        changes = diff_dicts(old, new)
        assert len(changes) == 1
        assert changes[0].field == "a"

    def test_nested_dict_unchanged(self):
        old = {"a": {"x": 1}}
        new = {"a": {"x": 1}}
        assert diff_dicts(old, new) == []

    def test_list_changed(self):
        old = {"items": [1, 2]}
        new = {"items": [1, 2, 3]}
        changes = diff_dicts(old, new)
        assert len(changes) == 1

    def test_empty_dicts(self):
        assert diff_dicts({}, {}) == []

    def test_multiple_changes_sorted(self):
        old = {"z": 1, "a": 2}
        new = {"z": 10, "a": 20}
        changes = diff_dicts(old, new)
        assert [c.field for c in changes] == ["a", "z"]


# ---------------------------------------------------------------------------
# diff_member_tags
# ---------------------------------------------------------------------------


class TestDiffMemberTags:
    def test_no_changes(self):
        members = [{"tag": "#A", "name": "Alice", "trophies": 100}]
        joined, left, updated = diff_member_tags(members, members.copy())
        assert joined == []
        assert left == []
        assert updated == []

    def test_member_joined(self):
        old = [{"tag": "#A", "name": "Alice"}]
        new = [{"tag": "#A", "name": "Alice"}, {"tag": "#B", "name": "Bob"}]
        joined, left, updated = diff_member_tags(old, new)
        assert len(joined) == 1
        assert joined[0]["tag"] == "#B"
        assert left == []
        assert updated == []

    def test_member_left(self):
        old = [{"tag": "#A", "name": "Alice"}, {"tag": "#B", "name": "Bob"}]
        new = [{"tag": "#A", "name": "Alice"}]
        joined, left, updated = diff_member_tags(old, new)
        assert joined == []
        assert len(left) == 1
        assert left[0]["tag"] == "#B"
        assert updated == []

    def test_member_updated(self):
        old = [{"tag": "#A", "name": "Alice", "trophies": 100}]
        new = [{"tag": "#A", "name": "Alice", "trophies": 200}]
        joined, left, updated = diff_member_tags(old, new)
        assert joined == []
        assert left == []
        assert len(updated) == 1
        assert updated[0][0]["trophies"] == 100
        assert updated[0][1]["trophies"] == 200

    def test_join_leave_update_simultaneous(self):
        old = [
            {"tag": "#A", "name": "Alice", "trophies": 100},
            {"tag": "#B", "name": "Bob"},
        ]
        new = [
            {"tag": "#A", "name": "Alice", "trophies": 200},
            {"tag": "#C", "name": "Charlie"},
        ]
        joined, left, updated = diff_member_tags(old, new)
        assert len(joined) == 1
        assert joined[0]["tag"] == "#C"
        assert len(left) == 1
        assert left[0]["tag"] == "#B"
        assert len(updated) == 1
        assert updated[0][1]["trophies"] == 200

    def test_empty_lists(self):
        joined, left, updated = diff_member_tags([], [])
        assert joined == []
        assert left == []
        assert updated == []

    def test_from_empty_to_members(self):
        new = [{"tag": "#A", "name": "Alice"}]
        joined, left, updated = diff_member_tags([], new)
        assert len(joined) == 1
        assert left == []

    def test_all_leave(self):
        old = [{"tag": "#A", "name": "Alice"}]
        joined, left, updated = diff_member_tags(old, [])
        assert joined == []
        assert len(left) == 1


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------


class TestEventTypes:
    def test_event_type_values(self):
        assert EventType.CLAN_UPDATED.value == "clan_updated"
        assert EventType.MEMBER_JOINED.value == "member_joined"
        assert EventType.POLL_ERROR.value == "poll_error"

    def test_war_state_values(self):
        assert WarState.NOT_IN_WAR.value == "notInWar"
        assert WarState.IN_WAR.value == "inWar"

    def test_change_frozen(self):
        c = Change(field="x", old_value=1, new_value=2)
        assert c.field == "x"

    def test_event_defaults(self):
        e = Event(event_type=EventType.CLAN_UPDATED, tag="#TEST")
        assert e.old_data is None
        assert e.new_data is None
        assert e.changes == ()
        assert e.metadata == {}
        assert e.timestamp > 0

    def test_event_with_changes(self):
        changes = (Change("a", 1, 2),)
        e = Event(
            event_type=EventType.PLAYER_UPDATED,
            tag="#P1",
            changes=changes,
            metadata={"source": "test"},
        )
        assert len(e.changes) == 1
        assert e.metadata["source"] == "test"
