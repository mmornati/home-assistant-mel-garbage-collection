"""Déchèteries et points d'apport autour de l'adresse.

La MEL publie ces lieux sur la même plateforme que les collectes (Publidata).
Ce module les met en forme, les trie par distance et calcule leur état
(ouvert, prochaine ouverture) à un instant donné.
"""

from __future__ import annotations

from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from typing import Any

from .opening_hours import OpeningHours

# Types de lieux Publidata
FACILITY_RECYCLING_CENTER = 71
FACILITY_MOBILE = 91
FACILITY_COMPOSTER = 559
FACILITY_GLASS = 86

# Le règlement d'accès de la MEL ferme les déchèteries ces trois jours-là
RECYCLING_CENTER_CLOSED_DAYS = {(1, 1), (5, 1), (12, 25)}

KIND_BY_TYPE = {
    FACILITY_RECYCLING_CENTER: "recycling_center",
    FACILITY_MOBILE: "mobile",
    FACILITY_COMPOSTER: "composter",
    FACILITY_GLASS: "glass",
}

# Nombre de lieux conservés par catégorie (les plus proches)
MAX_PER_KIND = {"recycling_center": 14, "mobile": 6, "composter": 5, "glass": 5}


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance à vol d'oiseau entre deux points, en kilomètres."""
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    )
    return 6371.0 * 2 * asin(sqrt(a))


def _clean(text: str | None) -> str:
    """Normalise les espaces et répare les accents mal encodés à la source."""
    text = " ".join((text or "").split())
    if "Ã" in text:
        try:
            text = text.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return text


def normalize_facilities(
    raw: list[dict[str, Any]], home_lat: float | None, home_lon: float | None
) -> dict[str, list[dict[str, Any]]]:
    """Trie les lieux par catégorie et par distance à l'adresse."""
    by_kind: dict[str, list[dict[str, Any]]] = {kind: [] for kind in MAX_PER_KIND}
    seen: set[Any] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        kind = KIND_BY_TYPE.get((item.get("facility_type") or {}).get("id") or 0)
        location = item.get("location") or {}
        lat, lon = location.get("lat"), location.get("lon")
        if not kind or lat is None or lon is None or item.get("id") in seen:
            continue
        if item.get("facility_status") not in (None, "opened"):
            continue
        seen.add(item.get("id"))
        distance = (
            round(distance_km(home_lat, home_lon, lat, lon), 2)
            if home_lat is not None and home_lon is not None
            else None
        )
        by_kind[kind].append(
            {
                "id": item.get("id"),
                "kind": kind,
                "name": _clean(item.get("name")),
                "address": _clean(item.get("address")),
                "lat": lat,
                "lon": lon,
                "distance_km": distance,
                "opening_hours": item.get("opening_hours") or "",
                "opening_hours_text": item.get("opening_hours_blurb"),
            }
        )
    for kind, items in by_kind.items():
        items.sort(
            key=lambda place: (
                place["distance_km"] is None,
                place["distance_km"] or 0,
                place["name"],
            )
        )
        del items[MAX_PER_KIND[kind] :]
    return by_kind


def facility_hours(place: dict[str, Any]) -> OpeningHours:
    """Horaires d'un lieu, jours de fermeture réglementaires compris."""
    closed = (
        RECYCLING_CENTER_CLOSED_DAYS if place["kind"] == "recycling_center" else None
    )
    return OpeningHours(place.get("opening_hours"), closed)


def facility_status(place: dict[str, Any], now: datetime) -> dict[str, Any]:
    """État d'un lieu à l'instant donné (heure locale)."""
    hours = facility_hours(place)
    if not hours:
        return {
            "open": None,
            "closes_at": None,
            "next_open": None,
            "next_close": None,
            "today": [],
        }
    closes_at = hours.closes_at(now)
    upcoming = hours.next_opening(now)
    return {
        "open": closes_at is not None,
        "closes_at": closes_at.isoformat() if closes_at else None,
        "next_open": upcoming[0].isoformat() if upcoming else None,
        "next_close": upcoming[1].isoformat() if upcoming else None,
        "today": [
            f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}"
            for start, end in hours.intervals(now.date())
        ],
    }


def with_status(place: dict[str, Any], now: datetime) -> dict[str, Any]:
    """Le lieu et son état, prêt à être envoyé aux cartes."""
    return {**place, **facility_status(place, now)}


def next_mobile_visit(
    places: list[dict[str, Any]], now: datetime
) -> tuple[dict[str, Any], datetime, datetime] | None:
    """Prochain passage d'une déchèterie mobile parmi les plus proches."""
    best: tuple[dict[str, Any], datetime, datetime] | None = None
    for place in places:
        hours = facility_hours(place)
        current_end = hours.closes_at(now)
        if current_end is not None:
            return place, now, current_end
        upcoming = hours.next_opening(now)
        if upcoming and (best is None or upcoming[0] < best[1]):
            best = (place, upcoming[0], upcoming[1])
    return best
