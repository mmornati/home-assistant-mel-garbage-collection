"""Tests de la lecture des horaires publiés par la MEL."""

from datetime import date, datetime

from custom_components.mel_collecte.opening_hours import (
    OpeningHours,
    is_public_holiday,
    parse_opening_hours,
)

FIXED = (
    "Apr-Oct Mo-Sa 07:30-19:00; Apr-Oct Su 08:00-13:00; "
    "Jan-Mar Mo-Sa 07:30-18:00; Jan-Mar Su 08:00-13:00; "
    "Nov-Dec Mo-Sa 07:30-18:00; Nov-Dec Su 08:00-13:00; 2025 Jan 09 off"
)
MOBILE = "Jan-Feb,Dec off; May 01 off; Nov 11 off; Mar 1-Nov 30 Su[1] 09:30-12:30"


def _hours(spec, day):
    return [
        (start.strftime("%H:%M"), end.strftime("%H:%M"))
        for start, end in OpeningHours(spec).intervals(day)
    ]


def test_summer_and_winter_hours():
    assert _hours(FIXED, date(2026, 7, 15)) == [("07:30", "19:00")]  # mercredi d'été
    assert _hours(FIXED, date(2026, 11, 14)) == [("07:30", "18:00")]  # samedi d'hiver
    assert _hours(FIXED, date(2026, 11, 15)) == [("08:00", "13:00")]  # dimanche


def test_dated_exception_overrides_regular_hours():
    assert _hours(FIXED, date(2025, 1, 9)) == []
    assert _hours(FIXED, date(2026, 1, 9)) == [("07:30", "18:00")]


def test_leading_off_rule_is_overridden_by_later_rules():
    assert _hours("off; " + FIXED, date(2026, 6, 1)) == [("07:30", "19:00")]


def test_nth_weekday_of_month():
    assert _hours(MOBILE, date(2026, 6, 7)) == [("09:30", "12:30")]  # 1er dimanche
    assert _hours(MOBILE, date(2026, 6, 14)) == []  # 2e dimanche
    assert _hours(MOBILE, date(2026, 12, 6)) == []  # pause hivernale


def test_several_ranks_and_days():
    spec = "Jan-Feb,Dec off; Mar 1-Nov 30 Sa[1] 09:30-12:30; Mar 1-Nov 30 Mo[2,4] 14:00-17:00; PH off"
    assert _hours(spec, date(2026, 6, 6)) == [("09:30", "12:30")]
    assert _hours(spec, date(2026, 6, 8)) == [("14:00", "17:00")]
    assert _hours(spec, date(2026, 6, 15)) == []
    assert _hours(spec, date(2026, 6, 22)) == [("14:00", "17:00")]


def test_public_holiday_closes():
    spec = "Mar-Nov Fr 09:30-12:30,14:00-17:00; Jan-Feb,Dec off; PH off"
    assert _hours(spec, date(2026, 5, 15)) == [("09:30", "12:30"), ("14:00", "17:00")]
    assert _hours(spec, date(2026, 5, 1)) == []  # vendredi 1er mai
    assert is_public_holiday(date(2026, 5, 14))  # Ascension
    assert is_public_holiday(date(2026, 4, 6))  # lundi de Pâques
    assert not is_public_holiday(date(2026, 4, 7))


def test_day_list_and_always_open():
    spec = "Mar-Nov Mo,Fr,Sa 10:00-16:00; Mar-Nov Su 09:30-12:30; Jan-Feb off; Dec off"
    assert _hours(spec, date(2026, 6, 5)) == [("10:00", "16:00")]
    assert _hours(spec, date(2026, 6, 2)) == []
    assert OpeningHours("24/7").is_open(datetime(2026, 1, 1, 3, 0))


def test_unreadable_rules_are_ignored():
    assert parse_opening_hours("n'importe quoi; ; Mo 25h") == []
    assert not OpeningHours("")
    assert not OpeningHours(None)


def test_impossible_times_do_not_raise():
    # une heure invalide dans les données publiées ne doit pas faire planter les capteurs
    assert parse_opening_hours("Mo 25:00-26:00; Tu 08:99-09:00") == []
    assert _hours("Mo 25:00-26:00; Mo-Sa 08:00-12:00", date(2026, 6, 1)) == [
        ("08:00", "12:00")
    ]
    assert _hours("Mo-Su 08:00-24:00", date(2026, 6, 1)) == [("08:00", "23:59")]


def test_open_state_and_next_opening():
    hours = OpeningHours(FIXED, closed_days={(12, 25)})
    saturday_evening = datetime(2026, 11, 14, 19, 30)
    assert not hours.is_open(saturday_evening)
    assert hours.closes_at(saturday_evening) is None
    start, end = hours.next_opening(saturday_evening)
    assert (start, end) == (datetime(2026, 11, 15, 8, 0), datetime(2026, 11, 15, 13, 0))

    saturday_noon = datetime(2026, 11, 14, 12, 0)
    assert hours.is_open(saturday_noon)
    assert hours.closes_at(saturday_noon) == datetime(2026, 11, 14, 18, 0)
    # la plage en cours n'est pas « la prochaine »
    assert hours.next_opening(saturday_noon)[0] == datetime(2026, 11, 15, 8, 0)

    assert hours.intervals(date(2026, 12, 25)) == []
    assert hours.next_opening(datetime(2026, 12, 24, 20, 0))[0] == datetime(
        2026, 12, 26, 7, 30
    )


def test_next_opening_none_when_never_open():
    assert OpeningHours("Jan-Dec off").next_opening(datetime(2026, 1, 1, 0, 0)) is None
