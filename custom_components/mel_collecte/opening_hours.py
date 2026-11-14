"""Lecture des horaires d'ouverture publiés par la MEL (format OpenStreetMap).

Seule la partie du format réellement publiée pour les déchèteries est gérée :

    Apr-Oct Mo-Sa 07:30-19:00; Apr-Oct Su 08:00-13:00; 2025 Jan 09 off
    Jan-Feb,Dec off; May 01 off; Mar 1-Nov 30 Su[1] 09:30-12:30; PH off
    24/7

Comme dans le format d'origine, une règle écrite plus loin remplace les
précédentes pour les jours qu'elle couvre.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

MONTHS = {
    name: index
    for index, name in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        + ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        start=1,
    )
}
WEEKDAYS = {"Mo": 0, "Tu": 1, "We": 2, "Th": 3, "Fr": 4, "Sa": 5, "Su": 6}

_TIME_RANGE = re.compile(r"^(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})$")
_DATE_PART = re.compile(r"^([A-Z][a-z]{2})(?: (\d{1,2}))?$")
_WEEKDAY_PART = re.compile(r"^([A-Z][a-z])(?:-([A-Z][a-z]))?(?:\[([\d,]+)\])?$")

Interval = tuple[time, time]


@dataclass
class Rule:
    """Une règle : les jours couverts et les heures d'ouverture ces jours-là."""

    year: int | None = None
    # périodes de l'année, bornes (mois, jour) incluses
    date_ranges: list[tuple[tuple[int, int], tuple[int, int]]] = field(
        default_factory=list
    )
    # jour de la semaine -> rangs dans le mois (vide : toutes les semaines)
    weekdays: dict[int, set[int]] = field(default_factory=dict)
    public_holidays: bool = False
    intervals: list[Interval] = field(default_factory=list)

    def covers(self, day: date) -> bool:
        """Indique si la règle s'applique à ce jour."""
        if self.year is not None and day.year != self.year:
            return False
        if self.date_ranges and not any(
            _in_range((day.month, day.day), start, end)
            for start, end in self.date_ranges
        ):
            return False
        if self.public_holidays and not self.weekdays:
            return is_public_holiday(day)
        if self.weekdays:
            if day.weekday() not in self.weekdays:
                return self.public_holidays and is_public_holiday(day)
            ranks = self.weekdays[day.weekday()]
            if ranks and (day.day - 1) // 7 + 1 not in ranks:
                return False
        return True


def _in_range(value: tuple[int, int], start: tuple[int, int], end: tuple[int, int]):
    if start <= end:
        return start <= value <= end
    return value >= start or value <= end  # période à cheval sur le nouvel an


def _easter(year: int) -> date:
    """Dimanche de Pâques (algorithme de Meeus)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    j, k = divmod(c, 4)
    m = (a + 11 * h) // 319
    r = (2 * e + 2 * j - k - h + m + 32) % 7
    month = (h - m + r + 90) // 25
    day = (h - m + r + month + 19) % 32
    return date(year, month, day)


def is_public_holiday(day: date) -> bool:
    """Jours fériés français (hors spécificités locales)."""
    if (day.month, day.day) in {
        (1, 1),
        (5, 1),
        (5, 8),
        (7, 14),
        (8, 15),
        (11, 1),
        (11, 11),
        (12, 25),
    }:
        return True
    easter = _easter(day.year)
    return day in {
        easter + timedelta(days=1),  # lundi de Pâques
        easter + timedelta(days=39),  # Ascension
        easter + timedelta(days=50),  # lundi de Pentecôte
    }


def _parse_dates(text: str) -> list[tuple[tuple[int, int], tuple[int, int]]] | None:
    """Lit « Apr-Oct », « Jan-Feb,Dec », « Mar 1-Nov 30 » ou « May 01 »."""
    ranges = []
    for chunk in text.split(","):
        bounds = [_DATE_PART.match(part.strip()) for part in chunk.split("-")]
        if not bounds or len(bounds) > 2 or not all(bounds):
            return None
        if any(match.group(1) not in MONTHS for match in bounds if match):
            return None
        first, last = bounds[0], bounds[-1]
        assert first and last
        start = (MONTHS[first.group(1)], int(first.group(2) or 1))
        end = (MONTHS[last.group(1)], int(last.group(2) or 31))
        ranges.append((start, end))
    return ranges


def _parse_weekdays(text: str) -> dict[int, set[int]] | None:
    """Lit « Mo-Sa », « Mo,Fr,Sa », « Su[1] » ou « Sa[2,4] »."""
    weekdays: dict[int, set[int]] = {}
    # les virgules entre crochets séparent des rangs, pas des jours
    for chunk in re.split(r",(?![^\[]*\])", text):
        match = _WEEKDAY_PART.match(chunk.strip())
        if not match or match.group(1) not in WEEKDAYS:
            return None
        first = WEEKDAYS[match.group(1)]
        last = first
        if match.group(2):
            if match.group(2) not in WEEKDAYS:
                return None
            last = WEEKDAYS[match.group(2)]
        ranks = (
            {int(rank) for rank in match.group(3).split(",")}
            if match.group(3)
            else set()
        )
        index = first
        while True:
            weekdays[index] = ranks
            if index == last:
                break
            index = (index + 1) % 7
    return weekdays


def _parse_rule(text: str) -> Rule | None:
    rule = Rule()
    rest = text.strip()
    if not rest:
        return None
    if rest == "24/7":
        rule.intervals = [(time(0, 0), time(23, 59, 59))]
        return rule

    tokens = rest.split()
    if tokens[-1] == "off":
        tokens.pop()
    elif all(_TIME_RANGE.match(part) for part in tokens[-1].split(",")):
        for part in tokens.pop().split(","):
            match = _TIME_RANGE.match(part)
            assert match
            hours = [int(group) for group in match.groups()]
            end = time(23, 59, 59) if hours[2] >= 24 else time(hours[2], hours[3])
            rule.intervals.append((time(hours[0], hours[1]), end))
    else:
        return None

    if tokens and re.fullmatch(r"\d{4}", tokens[0]):
        rule.year = int(tokens.pop(0))
    if tokens and tokens[-1] == "PH":
        rule.public_holidays = True
        tokens.pop()
    elif tokens and (_parse_weekdays(tokens[-1]) is not None):
        rule.weekdays = _parse_weekdays(tokens.pop()) or {}
    if tokens:
        dates = _parse_dates(" ".join(tokens))
        if dates is None:
            return None
        rule.date_ranges = dates
    return rule


def parse_opening_hours(spec: str | None) -> list[Rule]:
    """Convertit la chaîne publiée en règles ; les règles illisibles sont ignorées."""
    rules = []
    for chunk in (spec or "").split(";"):
        try:
            rule = _parse_rule(chunk)
        except ValueError:
            # heure ou date impossible (« 25:00 », « Feb 45 ») : la règle est ignorée
            rule = None
        if rule is not None:
            rules.append(rule)
    return rules


class OpeningHours:
    """Horaires d'un lieu, avec d'éventuels jours de fermeture annuels."""

    def __init__(
        self, spec: str | None, closed_days: set[tuple[int, int]] | None = None
    ) -> None:
        self.rules = parse_opening_hours(spec)
        self._closed_days = closed_days or set()

    def __bool__(self) -> bool:
        return any(rule.intervals for rule in self.rules)

    def intervals(self, day: date) -> list[Interval]:
        """Heures d'ouverture d'un jour donné (liste vide : fermé)."""
        if (day.month, day.day) in self._closed_days:
            return []
        for rule in reversed(self.rules):
            if rule.covers(day):
                return sorted(rule.intervals)
        return []

    def is_open(self, moment: datetime) -> bool:
        """Indique si le lieu est ouvert à cet instant (heure locale)."""
        now = moment.time()
        return any(start <= now < end for start, end in self.intervals(moment.date()))

    def closes_at(self, moment: datetime) -> datetime | None:
        """Heure de fermeture si le lieu est ouvert à cet instant."""
        now = moment.time()
        for start, end in self.intervals(moment.date()):
            if start <= now < end:
                return datetime.combine(moment.date(), end, tzinfo=moment.tzinfo)
        return None

    def next_opening(
        self, moment: datetime, horizon_days: int = 400
    ) -> tuple[datetime, datetime] | None:
        """Prochaine plage d'ouverture qui commence après cet instant."""
        for offset in range(horizon_days + 1):
            day = moment.date() + timedelta(days=offset)
            for start, end in self.intervals(day):
                if offset == 0 and start <= moment.time():
                    continue
                return (
                    datetime.combine(day, start, tzinfo=moment.tzinfo),
                    datetime.combine(day, end, tzinfo=moment.tzinfo),
                )
        return None
