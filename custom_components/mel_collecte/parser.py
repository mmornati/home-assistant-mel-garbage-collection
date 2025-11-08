"""Utilitaires de parsing des créneaux de collecte."""

from __future__ import annotations

import re
from datetime import datetime, time, timedelta
from typing import Dict, List

DAY_MAP = {
    "Mo": 0,
    "Tu": 1,
    "We": 2,
    "Th": 3,
    "Fr": 4,
    "Sa": 5,
    "Su": 6,
}

WEEK_PATTERN = re.compile(r"week\s+(\d+)-(\d+)(?:/(\d+))?", re.IGNORECASE)
TIME_RANGE_PATTERN = re.compile(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})")


def parse_schedule(schedule: str, start: datetime, end: datetime) -> List[Dict[str, datetime]]:
    """Convertit une chaîne d'horaire Publidata en occurrences."""
    schedule = schedule.strip()
    if not schedule:
        return []

    week_info = WEEK_PATTERN.search(schedule)
    weeks = None
    interval = 1
    if week_info:
        week_start = int(week_info.group(1))
        week_end = int(week_info.group(2))
        interval = int(week_info.group(3) or 1)
        weeks = (week_start, week_end, interval)

    day_token = next((token[:2] for token in schedule.split() if token[:2] in DAY_MAP), None)
    if not day_token:
        return []
    weekday = DAY_MAP[day_token]

    time_match = TIME_RANGE_PATTERN.search(schedule)
    if not time_match:
        return []

    start_time = _parse_time(time_match.group(1))
    end_time = _parse_time(time_match.group(2))

    occurrences: List[Dict[str, datetime]] = []
    current = start
    while current <= end:
        if current.weekday() == weekday and _week_matches(current.isocalendar()[1], weeks):
            occ_start = datetime.combine(current.date(), start_time, tzinfo=start.tzinfo)
            occ_end = datetime.combine(current.date(), end_time, tzinfo=end.tzinfo)
            if occ_end <= occ_start:
                occ_end += timedelta(days=1)
            if occ_end >= start:
                occurrences.append({"start": occ_start, "end": occ_end})
        current += timedelta(days=1)
    return occurrences


def _parse_time(value: str) -> time:
    hour, minute = map(int, value.split(":"))
    return time(hour, minute)


def _week_matches(week_number: int, weeks: tuple[int, int, int] | None) -> bool:
    if not weeks:
        return True
    week_start, week_end, interval = weeks
    if week_number < week_start or week_number > week_end:
        return False
    return (week_number - week_start) % interval == 0

