"""Tests pour le parser des horaires de collecte."""

from datetime import datetime, timezone

from custom_components.mel_collecte.parser import (
    parse_schedule,
    _parse_time,
    _week_matches,
)


class TestParseSchedule:
    """Tests de parse_schedule()."""

    def test_basic_thursday_schedule(self):
        """Parse un horaire simple le jeudi."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 31, tzinfo=timezone.utc)
        schedule = "Th 13:15-20:15"
        result = parse_schedule(schedule, start, end)
        assert len(result) >= 1
        assert all(evt["start"].weekday() == 3 for evt in result)

    def test_empty_string_returns_empty_list(self):
        """Une chaîne vide retourne une liste vide."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 31, tzinfo=timezone.utc)
        assert parse_schedule("", start, end) == []

    def test_whitespace_only_returns_empty_list(self):
        """Une chaîne avec seulement des espaces retourne une liste vide."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 31, tzinfo=timezone.utc)
        assert parse_schedule("   ", start, end) == []

    def test_invalid_day_returns_empty_list(self):
        """Un jour invalide retourne une liste vide."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 31, tzinfo=timezone.utc)
        assert parse_schedule("week 1-52/2 XX 09:00-12:00", start, end) == []

    def test_no_time_range_returns_empty_list(self):
        """Sans plage horaire, retourne une liste vide."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 31, tzinfo=timezone.utc)
        assert parse_schedule("Th", start, end) == []

    def test_week_pattern_simple(self):
        """Parse un horaire avec semaine simple."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 12, 31, tzinfo=timezone.utc)
        schedule = "week 1-52/2 Th 05:50-12:50"
        result = parse_schedule(schedule, start, end)
        for evt in result:
            week_num = evt["start"].isocalendar()[1]
            assert (week_num - 1) % 2 == 0

    def test_week_pattern_boundary_week_53(self):
        """Parse un horaire avec semaine 53."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 12, 31, tzinfo=timezone.utc)
        schedule = "week 1-53 Th 05:50-12:50"
        result = parse_schedule(schedule, start, end)
        assert len(result) >= 1

    def test_overnight_collection(self):
        """Parse une collecte de nuit (fin < début)."""
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end = datetime(2025, 1, 31, tzinfo=timezone.utc)
        schedule = "Th 22:00-05:00"
        result = parse_schedule(schedule, start, end)
        for evt in result:
            assert evt["end"] > evt["start"]

    def test_occurrence_filter_before_start(self):
        """Les occurrences qui finissent avant le début sont filtrées."""
        start = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
        end = datetime(2025, 1, 31, tzinfo=timezone.utc)
        schedule = "We 05:00-12:00"
        result = parse_schedule(schedule, start, end)
        for evt in result:
            assert evt["end"] >= start


class TestParseTime:
    """Tests de _parse_time()."""

    def test_midnight(self):
        """Parse 00:00."""
        result = _parse_time("00:00")
        assert result.hour == 0
        assert result.minute == 0

    def test_end_of_day(self):
        """Parse 23:59."""
        result = _parse_time("23:59")
        assert result.hour == 23
        assert result.minute == 59

    def test_single_digit_hour(self):
        """Parse 9:00."""
        result = _parse_time("9:00")
        assert result.hour == 9
        assert result.minute == 0


class TestWeekMatches:
    """Tests de _week_matches()."""

    def test_none_weeks_returns_true(self):
        """Si weeks est None, retourne toujours True."""
        assert _week_matches(1, None) is True
        assert _week_matches(25, None) is True
        assert _week_matches(52, None) is True

    def test_week_outside_range_returns_false(self):
        """Une semaine en dehors de l'intervalle retourne False."""
        weeks = (10, 20, 1)
        assert _week_matches(5, weeks) is False
        assert _week_matches(25, weeks) is False

    def test_week_inside_interval_matches(self):
        """Une semaine dans l'intervalle avec interval correct."""
        weeks = (1, 52, 2)
        assert _week_matches(1, weeks) is True
        assert _week_matches(3, weeks) is True
        assert _week_matches(5, weeks) is True

    def test_week_inside_interval_no_match(self):
        """Une semaine dans l'intervalle mais interval ne match pas."""
        weeks = (1, 52, 3)
        assert _week_matches(2, weeks) is False
        assert _week_matches(5, weeks) is False

    def test_week_at_start_boundary(self):
        """Semaine exactement au début de l'intervalle."""
        weeks = (10, 20, 2)
        assert _week_matches(10, weeks) is True
        assert _week_matches(12, weeks) is True

    def test_week_at_end_boundary(self):
        """Semaine exactement à la fin de l'intervalle."""
        weeks = (10, 20, 2)
        assert _week_matches(20, weeks) is True
