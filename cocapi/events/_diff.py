"""Change detection utilities for the event polling system."""

from __future__ import annotations

from typing import Any

from ._types import Change


def diff_dicts(
    old: dict[str, Any],
    new: dict[str, Any],
    *,
    include_fields: frozenset[str] | None = None,
    exclude_fields: frozenset[str] | None = None,
) -> list[Change]:
    """Shallow diff of two dicts, returning a list of Change objects.

    Compares top-level keys only. Nested dicts/lists are compared by equality.

    Args:
        old: Previous snapshot.
        new: Current snapshot.
        include_fields: If set, only diff these fields.
        exclude_fields: If set, skip these fields.

    Returns:
        List of Change objects for fields that differ.
    """
    changes: list[Change] = []
    all_keys = set(old.keys()) | set(new.keys())

    for key in sorted(all_keys):
        if include_fields is not None and key not in include_fields:
            continue
        if exclude_fields is not None and key in exclude_fields:
            continue

        old_val = old.get(key)
        new_val = new.get(key)

        if old_val != new_val:
            changes.append(Change(field=key, old_value=old_val, new_value=new_val))

    return changes


def diff_member_tags(
    old_members: list[dict[str, Any]],
    new_members: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[tuple[dict[str, Any], dict[str, Any]]],
]:
    """Compare member lists by tag to detect joins, leaves, and updates.

    Args:
        old_members: Previous member list.
        new_members: Current member list.

    Returns:
        Tuple of (joined, left, updated) where:
        - joined: list of new member dicts
        - left: list of old member dicts no longer present
        - updated: list of (old_member, new_member) tuples where data changed
    """
    old_by_tag: dict[str, dict[str, Any]] = {m["tag"]: m for m in old_members}
    new_by_tag: dict[str, dict[str, Any]] = {m["tag"]: m for m in new_members}

    old_tags = set(old_by_tag.keys())
    new_tags = set(new_by_tag.keys())

    joined = [new_by_tag[t] for t in sorted(new_tags - old_tags)]
    left = [old_by_tag[t] for t in sorted(old_tags - new_tags)]

    updated: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for tag in sorted(old_tags & new_tags):
        if old_by_tag[tag] != new_by_tag[tag]:
            updated.append((old_by_tag[tag], new_by_tag[tag]))

    return joined, left, updated


def diff_named_list(
    old_items: list[dict[str, Any]],
    new_items: list[dict[str, Any]],
    key: str = "name",
    compare_field: str = "level",
) -> list[tuple[str, Any, Any]]:
    """Diff two lists of dicts keyed by *key*, comparing *compare_field*.

    Used for troops, spells, heroes, and equipment which all share a
    ``{"name": str, "level": int}`` structure.

    Args:
        old_items: Previous list snapshot.
        new_items: Current list snapshot.
        key: Dict key used to identify items (default ``"name"``).
        compare_field: Dict key whose value is compared (default ``"level"``).

    Returns:
        List of ``(name, old_value, new_value)`` for items where
        *compare_field* changed.  New items appear as ``(name, None, value)``.
    """
    old_by_key: dict[str, dict[str, Any]] = {item[key]: item for item in old_items}
    new_by_key: dict[str, dict[str, Any]] = {item[key]: item for item in new_items}

    changes: list[tuple[str, Any, Any]] = []
    for name in sorted(new_by_key):
        new_val = new_by_key[name].get(compare_field)
        if name in old_by_key:
            old_val = old_by_key[name].get(compare_field)
            if old_val != new_val:
                changes.append((name, old_val, new_val))
        else:
            # Newly unlocked
            changes.append((name, None, new_val))

    return changes
