"""
Helpers for recurring Clash of Clans event windows (all times UTC).

Assumptions (these follow the game's long-standing schedule and may change):

- Clan Games: 22nd 08:00 UTC to 28th 08:00 UTC each month.
- Raid Weekend: Friday 07:00 UTC to Monday 07:00 UTC.
- Legend League day: resets daily at 05:00 UTC.

League *season* boundaries have changed over time, so they are deliberately not
computed here; use ``api.league_season()`` / ``league_season_id()`` instead.
"""

from datetime import datetime, timedelta, timezone

UTC = timezone.utc


def _now(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(UTC)
    return now.astimezone(UTC) if now.tzinfo else now.replace(tzinfo=UTC)


def clan_games_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    """Start/end of the running Clan Games, or the next ones if none running."""
    t = _now(now)
    end_this = datetime(t.year, t.month, 28, 8, tzinfo=UTC)
    year, month = t.year, t.month
    if t >= end_this:
        year, month = (t.year + 1, 1) if t.month == 12 else (t.year, t.month + 1)
    return (
        datetime(year, month, 22, 8, tzinfo=UTC),
        datetime(year, month, 28, 8, tzinfo=UTC),
    )


def raid_weekend_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    """Start/end of the running raid weekend, or the next one if none running."""
    t = _now(now)
    # Shift so the weekend ends at midnight Monday; weekday(): Mon=0
    shifted = t - timedelta(hours=7)
    end = (shifted + timedelta(days=7 - shifted.weekday())).replace(
        hour=7, minute=0, second=0, microsecond=0
    )
    start = end - timedelta(days=3)
    return start, end


def is_raid_weekend(now: datetime | None = None) -> bool:
    t = _now(now)
    start, end = raid_weekend_window(t)
    return start <= t < end


def is_clan_games(now: datetime | None = None) -> bool:
    t = _now(now)
    start, end = clan_games_window(t)
    return start <= t < end


def legend_day_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    """Start/end of the current Legend League day (05:00 UTC reset)."""
    t = _now(now)
    start = t.replace(hour=5, minute=0, second=0, microsecond=0)
    if t < start:
        start -= timedelta(days=1)
    return start, start + timedelta(days=1)
