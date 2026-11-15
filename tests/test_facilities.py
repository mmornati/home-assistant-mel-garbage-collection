"""Tests des déchèteries, points d'apport et données envoyées aux cartes."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from custom_components.mel_collecte.coordinator import MelCollecteCoordinator
from custom_components.mel_collecte.dashboard import entry_payload
from custom_components.mel_collecte.facilities import (
    distance_km,
    facility_status,
    next_mobile_visit,
    normalize_facilities,
)

HOME = (50.628584, 3.05259)
FIXED = "Apr-Oct Mo-Sa 07:30-19:00; Apr-Oct Su 08:00-13:00; Jan-Mar Mo-Sa 07:30-18:00; Jan-Mar Su 08:00-13:00; Nov-Dec Mo-Sa 07:30-18:00; Nov-Dec Su 08:00-13:00"


def _facility(ident, type_id, name, lat, lon, hours="", status="opened"):
    return {
        "id": ident,
        "name": name,
        "address": f"adresse {ident}",
        "facility_type": {"id": type_id},
        "facility_status": status,
        "location": {"lat": lat, "lon": lon},
        "opening_hours": hours,
        "opening_hours_blurb": None,
    }


RAW = [
    _facility(1, 71, "Déchèterie de Wattrelos", 50.696359, 3.220222, FIXED),
    _facility(2, 71, "Déchèterie de Lille Borda", 50.6162465, 3.0382976, FIXED),
    _facility(3, 71, "Déchèterie fermée", 50.62, 3.05, FIXED, status="closed"),
    _facility(
        4,
        91,
        "Déchèterie mobile de Lomme 2",
        50.646808,
        2.9810088,
        "Jan-Feb,Dec off; May 01 off; Nov 11 off; Mar 1-Nov 30 Sa[3] 14:00-17:00",
    ),
    _facility(
        5,
        91,
        "Déchèterie mobile de Lesquin",
        50.5908249,
        3.1047333,
        "Jan-Feb,Dec off; May 01 off; Nov 11 off; Mar 1-Nov 30 Su[2] 09:30-12:30",
    ),
    _facility(6, 559, "Composteur", 50.63, 3.06, "24/7"),
    _facility(7, 86, "Borne à verre", 50.629, 3.053),
    _facility(7, 86, "Borne à verre (doublon)", 50.629, 3.053),
    {"id": 8, "facility_type": {"id": 86}, "location": None},
    _facility(9, 12345, "Autre type", 50.6, 3.0),
]


def test_distance():
    assert distance_km(*HOME, *HOME) == 0
    assert 1.5 < distance_km(*HOME, 50.6162465, 3.0382976) < 2.0


def test_normalize_sorts_by_distance_and_filters():
    places = normalize_facilities(RAW, *HOME)
    assert [p["name"] for p in places["recycling_center"]] == [
        "Déchèterie de Lille Borda",
        "Déchèterie de Wattrelos",
    ]
    assert places["recycling_center"][0]["distance_km"] == pytest.approx(1.71, abs=0.05)
    assert len(places["glass"]) == 1
    assert len(places["composter"]) == 1
    assert len(places["mobile"]) == 2


def test_normalize_without_home_position():
    places = normalize_facilities(RAW, None, None)
    assert places["recycling_center"][0]["distance_km"] is None


def test_facility_status():
    places = normalize_facilities(RAW, *HOME)
    borda = places["recycling_center"][0]
    opened = facility_status(borda, datetime(2026, 11, 14, 10, 0))
    assert opened["open"] is True
    assert opened["closes_at"] == "2026-11-14T18:00:00"
    assert opened["today"] == ["07:30-18:00"]

    closed = facility_status(borda, datetime(2026, 12, 25, 10, 0))
    assert closed["open"] is False
    assert closed["today"] == []
    assert closed["next_open"] == "2026-12-26T07:30:00"

    unknown = facility_status(places["glass"][0], datetime(2026, 11, 14, 10, 0))
    assert unknown["open"] is None


def test_next_mobile_visit():
    places = normalize_facilities(RAW, *HOME)["mobile"]
    place, start, end = next_mobile_visit(places, datetime(2026, 6, 1, 9, 0))
    assert place["name"] == "Déchèterie mobile de Lesquin"
    assert start == datetime(2026, 6, 14, 9, 30)
    assert end == datetime(2026, 6, 14, 12, 30)

    # en cours de passage : c'est celui-ci qui est renvoyé
    place, start, end = next_mobile_visit(places, datetime(2026, 6, 20, 15, 0))
    assert place["name"] == "Déchèterie mobile de Lomme 2"
    assert end == datetime(2026, 6, 20, 17, 0)

    assert next_mobile_visit([], datetime(2026, 6, 1)) is None


COLLECTIONS = [
    {
        "id": 10,
        "name": "Fiche générale emballages",
        "schedules": [],
        "metas": {
            "garbage_types": ["emb"],
            "accepted_waste": ["générale"],
            "rejected_waste": [],
        },
        "contacts": [
            {"type": "Email", "metas": {"value": "contact@example.org"}},
            {"type": "TollFreePhoneNumber", "metas": {"value": "0 800 000 000"}},
        ],
    },
    {
        "id": 11,
        "name": "Secteur emballages",
        "schedules": [{"opening_hours": "Fr 18:30-23:59"}],
        "metas": {
            "garbage_types": ["emb"],
            "collection_mode": "truck",
            "accepted_waste": ["Bouteilles en plastique", ""],
            "rejected_waste": ["Vaisselle cassée"],
            "collection_rules_blurb": '<p class="x">Sortir le bac&nbsp;la veille.</p>',
        },
        "contacts": [
            {"type": "Form", "metas": {"value": "https://example.org/contact"}}
        ],
    },
    {
        "id": 12,
        "name": "Redirection",
        "schedules": [],
        "metas": {"garbage_types": ["pile"]},
    },
    {
        "id": 13,
        "name": "Biflux",
        "schedules": [],
        "metas": {"garbage_types": ["omr", "bio"], "accepted_waste": ["x"]},
    },
]


def _coordinator(api):
    return MelCollecteCoordinator(
        None, api, address="1 rue Test, Lille", instance_id="876", lat=None, lon=None
    )


def _api(facilities=None, error=None):
    api = AsyncMock()
    api.geocode_address.return_value = {
        "geometry": {"coordinates": [HOME[1], HOME[0]]},
        "properties": {"id": "59350_1", "postcode": "59000"},
    }
    api.fetch_waste_collections.return_value = COLLECTIONS
    api.fetch_alerts.return_value = []
    if error:
        api.fetch_facilities.side_effect = error
    else:
        api.fetch_facilities.return_value = facilities or []
    return api


@pytest.mark.asyncio
async def test_coordinator_guide_contacts_and_facilities():
    api = _api(RAW)
    data = await _coordinator(api)._async_update_data()

    assert [item["type"] for item in data["guide"]] == ["emb"]
    emb = data["guide"][0]
    assert emb["accepted"] == [
        "Bouteilles en plastique"
    ]  # la collecte de l'adresse prime
    assert emb["rejected"] == ["Vaisselle cassée"]
    assert emb["rules"] == "Sortir le bac la veille."
    assert emb["color"] == "yellow"

    assert data["contacts"] == {
        "email": "contact@example.org",
        "phone": "0 800 000 000",
        "form": "https://example.org/contact",
    }
    assert data["home"] == {"lat": HOME[0], "lon": HOME[1]}
    assert (
        data["facilities"]["recycling_center"][0]["name"] == "Déchèterie de Lille Borda"
    )
    # déchèteries, déchèteries mobiles, composteurs, puis bornes à verre du code postal
    assert api.fetch_facilities.await_count == 4
    assert api.fetch_facilities.await_args_list[-1].args == ("898", 86, "59000")


@pytest.mark.asyncio
async def test_coordinator_keeps_last_facilities_on_error():
    api = _api(RAW)
    coordinator = _coordinator(api)
    await coordinator._async_update_data()

    api.fetch_facilities.side_effect = RuntimeError("panne")
    data = await coordinator._async_update_data()
    assert (
        data["facilities"]["recycling_center"][0]["name"] == "Déchèterie de Lille Borda"
    )
    assert data["events"]  # les collectes, elles, sont bien à jour


@pytest.mark.asyncio
async def test_coordinator_facilities_error_on_first_refresh():
    data = await _coordinator(_api(error=RuntimeError("panne")))._async_update_data()
    assert data["facilities"] == {}


def test_entry_payload():
    now = datetime(2026, 11, 14, 10, 0, tzinfo=timezone.utc)
    data = {
        "events": [
            {
                "start": datetime(2026, 11, 13, 18, 30, tzinfo=timezone.utc),
                "end": datetime(2026, 11, 13, 23, 59, tzinfo=timezone.utc),
                "garbage_types": ["emb"],
                "collection_mode": "truck",
            },
            {
                "start": datetime(2026, 11, 17, 18, 30, tzinfo=timezone.utc),
                "end": datetime(2026, 11, 17, 23, 59, tzinfo=timezone.utc),
                "garbage_types": ["omr"],
                "collection_mode": "truck",
            },
        ],
        "facilities": normalize_facilities(RAW, *HOME),
        "home": {"lat": HOME[0], "lon": HOME[1]},
        "fetched_at": "2026-11-14T09:00:00+00:00",
    }
    payload = entry_payload(
        "abc", "Maison", "1 rue Test", "en", data, now, {"next": "sensor.x"}
    )

    assert [event["types"] for event in payload["events"]] == [
        ["omr"]
    ]  # passé : retiré
    assert payload["types"] == {
        "omr": {"label": "Residual household waste", "color": "grey"}
    }
    assert payload["facilities"]["recycling_center"][0]["open"] is True
    assert payload["entities"] == {"next": "sensor.x"}
    assert payload["alerts"] == [] and payload["guide"] == []
    assert payload["updated"] == "2026-11-14T09:00:00+00:00"


# ----- entités -----------------------------------------------------------


class _Coordinator:
    def __init__(self, facilities):
        self.data = {"facilities": facilities, "collections": [], "events": []}
        self._visible_types = []


def _entry():
    from types import SimpleNamespace

    return SimpleNamespace(entry_id="abc", options={}, data={})


def _at(module, moment):
    from unittest.mock import patch

    return patch(
        f"custom_components.mel_collecte.{module}.dt_util.now", return_value=moment
    )


def test_recycling_center_sensor():
    from custom_components.mel_collecte.sensor import MelCollecteRecyclingCenterSensor

    sensor = MelCollecteRecyclingCenterSensor(
        _Coordinator(normalize_facilities(RAW, *HOME)), _entry()
    )
    assert sensor.native_value == "Déchèterie de Lille Borda"
    with _at("sensor", datetime(2026, 11, 14, 10, 0)):
        attrs = sensor.extra_state_attributes
    assert attrs["ouverte"] is True
    assert attrs["horaires_du_jour"] == ["07:30-18:00"]
    assert attrs["latitude"] == pytest.approx(50.6162465)
    assert [place["nom"] for place in attrs["decheteries"]] == [
        "Déchèterie de Lille Borda",
        "Déchèterie de Wattrelos",
    ]

    empty = MelCollecteRecyclingCenterSensor(_Coordinator({}), _entry())
    assert empty.native_value is None
    assert empty.extra_state_attributes == {}


def test_mobile_recycling_center_sensor():
    from custom_components.mel_collecte.sensor import (
        MelCollecteMobileRecyclingCenterSensor,
    )

    sensor = MelCollecteMobileRecyclingCenterSensor(
        _Coordinator(normalize_facilities(RAW, *HOME)), _entry()
    )
    with _at("sensor", datetime(2026, 6, 1, 9, 0)):
        assert sensor.native_value == "2026-06-14T09:30:00"
        attrs = sensor.extra_state_attributes
    assert attrs["nom"] == "Déchèterie mobile de Lesquin"
    assert attrs["fin"] == "2026-06-14T12:30:00"

    empty = MelCollecteMobileRecyclingCenterSensor(_Coordinator({}), _entry())
    with _at("sensor", datetime(2026, 6, 1, 9, 0)):
        assert empty.native_value is None
        assert empty.extra_state_attributes == {}


def test_recycling_center_open_binary_sensor():
    from custom_components.mel_collecte.binary_sensor import (
        MelCollecteRecyclingCenterOpenSensor,
    )

    sensor = MelCollecteRecyclingCenterOpenSensor(
        _Coordinator(normalize_facilities(RAW, *HOME)), _entry()
    )
    with _at("binary_sensor", datetime(2026, 11, 14, 10, 0)):
        assert sensor.is_on is True
        assert sensor.icon == "mdi:gate-open"
        assert sensor.extra_state_attributes["fermeture"] == "2026-11-14T18:00:00"
    with _at("binary_sensor", datetime(2026, 11, 14, 20, 0)):
        assert sensor.is_on is False
        assert sensor.icon == "mdi:gate"
        assert (
            sensor.extra_state_attributes["prochaine_ouverture"]
            == "2026-11-15T08:00:00"
        )

    empty = MelCollecteRecyclingCenterOpenSensor(_Coordinator({}), _entry())
    assert empty.is_on is None
    assert empty.extra_state_attributes == {}


@pytest.mark.asyncio
async def test_platforms_create_facility_entities():
    from custom_components.mel_collecte import binary_sensor, sensor
    from custom_components.mel_collecte.const import DATA_COORDINATOR, DOMAIN
    from types import SimpleNamespace

    entry = _entry()
    for facilities, expected in (
        (normalize_facilities(RAW, *HOME), (5, 1)),
        ({}, (3, 0)),
    ):
        hass = SimpleNamespace(
            data={DOMAIN: {"abc": {DATA_COORDINATOR: _Coordinator(facilities)}}}
        )
        added: list = []
        await sensor.async_setup_entry(hass, entry, added.extend)
        assert len(added) == expected[0]
        added = []
        await binary_sensor.async_setup_entry(hass, entry, added.extend)
        assert len(added) == expected[1]


def test_accents_repaired():
    places = normalize_facilities(
        [_facility(1, 559, "Residence AllÃ©es du ThÃ©atre", 50.63, 3.06, "24/7")], *HOME
    )
    assert places["composter"][0]["name"] == "Residence Allées du Théatre"


def test_mobile_visits_lists_every_site():
    from custom_components.mel_collecte.facilities import mobile_visits

    places = normalize_facilities(RAW, *HOME)["mobile"]
    visits = mobile_visits(places, datetime(2026, 6, 1, 9, 0))
    assert [(place["name"], start) for place, start, _ in visits] == [
        ("Déchèterie mobile de Lesquin", datetime(2026, 6, 14, 9, 30)),
        ("Déchèterie mobile de Lomme 2", datetime(2026, 6, 20, 14, 0)),
    ]
    assert mobile_visits([], datetime(2026, 6, 1)) == []


def test_mobile_sensor_exposes_all_visits():
    from custom_components.mel_collecte.sensor import (
        MelCollecteMobileRecyclingCenterSensor,
    )

    sensor = MelCollecteMobileRecyclingCenterSensor(
        _Coordinator(normalize_facilities(RAW, *HOME)), _entry()
    )
    with _at("sensor", datetime(2026, 6, 1, 9, 0)):
        passages = sensor.extra_state_attributes["passages"]
    assert [item["nom"] for item in passages] == [
        "Déchèterie mobile de Lesquin",
        "Déchèterie mobile de Lomme 2",
    ]
    assert passages[1]["debut"] == "2026-06-20T14:00:00"
    assert passages[1]["fin"] == "2026-06-20T17:00:00"
    assert passages[1]["adresse"] == "adresse 4"
