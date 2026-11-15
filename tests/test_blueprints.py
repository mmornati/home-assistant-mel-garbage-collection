"""Modèles d'automatisation : installation, structure et gabarits."""

from __future__ import annotations

import ast
from datetime import datetime, timedelta

import pytest

from custom_components.mel_collecte.blueprints import (
    BLUEPRINTS_DIR,
    install_blueprints,
)

yaml = pytest.importorskip("yaml")
jinja2 = pytest.importorskip("jinja2")

NAMES = ["rappel_bacs.yaml", "rappel_decheterie_mobile.yaml"]
NOW = datetime(2026, 11, 15, 19, 0)


class _Input(str):
    """Référence ``!input`` d'un blueprint."""


class _Loader(yaml.SafeLoader):
    pass


_Loader.add_constructor("!input", lambda loader, node: _Input(node.value))


def _load(name: str) -> dict:
    return yaml.load((BLUEPRINTS_DIR / name).read_text(encoding="utf-8"), _Loader)


def _inputs(node) -> set[str]:
    if isinstance(node, _Input):
        return {str(node)}
    if isinstance(node, dict):
        return set().union(*(_inputs(value) for value in node.values()), set())
    if isinstance(node, list):
        return set().union(*(_inputs(value) for value in node), set())
    return set()


def _native(text: str):
    """Comme Home Assistant : le texte rendu redevient liste, dictionnaire ou None."""
    text = text.strip()
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return text


def _render(name: str, inputs: dict, states: dict) -> dict:
    """Évalue les variables du blueprint comme le ferait Home Assistant."""
    env = jinja2.Environment()
    env.globals.update(
        now=lambda: NOW,
        timedelta=timedelta,
        as_datetime=datetime.fromisoformat,
        as_local=lambda value: value,
        state_attr=lambda entity, attr: states.get(entity, {}).get(attr),
    )
    values: dict = {}
    for key, raw in _load(name)["variables"].items():
        if isinstance(raw, _Input):
            values[key] = inputs[str(raw)]
        else:
            values[key] = _native(env.from_string(raw).render(**values))
    return values


def test_install_blueprints_copies_once(tmp_path):
    assert install_blueprints(str(tmp_path)) == NAMES
    target = tmp_path / "blueprints" / "automation" / "mel_collecte"
    assert sorted(path.name for path in target.iterdir()) == NAMES

    # un modèle modifié par l'utilisateur n'est pas écrasé
    (target / NAMES[0]).write_text("modifié", encoding="utf-8")
    assert install_blueprints(str(tmp_path)) == []
    assert (target / NAMES[0]).read_text(encoding="utf-8") == "modifié"


@pytest.mark.parametrize("name", NAMES)
def test_blueprint_structure(name):
    content = _load(name)
    blueprint = content["blueprint"]
    assert blueprint["domain"] == "automation"
    assert blueprint["source_url"].endswith(f"/automation/mel_collecte/{name}")
    # chaque entrée déclarée est utilisée, et inversement
    used = _inputs({key: value for key, value in content.items() if key != "blueprint"})
    assert used == set(blueprint["input"])


BINS = {
    "sensor.omr": {
        "debut": "2026-11-16T06:00:00",
        "types_friendly": ["Ordures ménagères résiduelles"],
    },
    "sensor.emb": {
        "debut": "2026-11-16T13:00:00",
        "types_friendly": ["Emballages recyclables"],
    },
    "sensor.verre_jours": {
        "prochaine_collecte": "2026-11-20T06:00:00",
        "type_libelle": "Verre",
    },
    "sensor.jours": {
        "next_collection_date": "2026-11-16T06:00:00",
        "next_collection_type": ["Ordures ménagères résiduelles"],
    },
    "sensor.vide": {},
}


def test_bins_reminder_lists_tomorrows_bins():
    values = _render(
        "rappel_bacs.yaml",
        {"collection_sensors": list(BINS), "days_before": 1, "title": "Poubelles"},
        BINS,
    )
    assert values["bacs_liste"] == [
        "Ordures ménagères résiduelles",
        "Emballages recyclables",
    ]
    assert values["bacs"] == "Ordures ménagères résiduelles, Emballages recyclables"
    assert values["quand"] == "demain"


def test_bins_reminder_silent_without_collection():
    values = _render(
        "rappel_bacs.yaml",
        {"collection_sensors": list(BINS), "days_before": 0, "title": "Poubelles"},
        BINS,
    )
    assert values["bacs_liste"] == []
    assert values["quand"] == "aujourd'hui"

    values = _render(
        "rappel_bacs.yaml",
        {"collection_sensors": ["sensor.verre_jours"], "days_before": 5, "title": ""},
        BINS,
    )
    assert values["bacs_liste"] == ["Verre"]
    assert values["quand"] == "dans 5 jours"


LOOS = {
    "nom": "Déchèterie mobile de Loos",
    "adresse": "Place Winston-Churchill, Loos",
    "distance_km": 3.12,
    "debut": "2026-11-16T09:30:00",
    "fin": "2026-11-16T12:30:00",
}
HAUBOURDIN = {
    "nom": "Déchèterie mobile d'Haubourdin",
    "adresse": "Rue de Lisbonne, Haubourdin",
    "distance_km": 5.51,
    "debut": "2026-11-16T14:00:00",
    "fin": "2026-11-16T17:00:00",
}
MOBILE = {"sensor.mobile": {**LOOS, "passages": [LOOS, HAUBOURDIN]}}


def _mobile(states=MOBILE, **inputs):
    defaults = {
        "mobile_sensor": "sensor.mobile",
        "days_before": 1,
        "commune": "",
        "max_distance": 0,
        "title": "Déchèterie mobile",
    }
    return _render("rappel_decheterie_mobile.yaml", {**defaults, **inputs}, states)[
        "passage"
    ]


def test_mobile_reminder_filters_by_town_and_distance():
    assert _mobile() == LOOS
    # la commune voulue est retenue même si un autre site passe plus tôt
    assert _mobile(commune=" haubourdin ") == HAUBOURDIN
    assert _mobile(commune="Lomme") is None
    assert _mobile(max_distance=4) == LOOS
    assert _mobile(commune="Haubourdin", max_distance=4) is None
    assert _mobile(days_before=0) is None


def test_mobile_reminder_works_without_visit_list():
    """Versions jusqu'à 1.6.0 : le capteur ne donne que le prochain passage."""
    states = {"sensor.mobile": LOOS}
    assert _mobile(states)["nom"] == LOOS["nom"]
    assert _mobile(states, commune="Haubourdin") is None
    assert _mobile({"sensor.mobile": {}}) is None
