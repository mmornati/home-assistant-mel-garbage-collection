"""Modèles d'automatisation (blueprints) fournis avec l'intégration.

Home Assistant ne propose pas aux intégrations personnalisées de publier des
blueprints : on copie donc les fichiers dans ``config/blueprints/automation``,
où ils apparaissent dans Paramètres > Automatisations > Blueprints.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from .const import DOMAIN

BLUEPRINTS_DIR = Path(__file__).parent / "blueprints" / "automation" / DOMAIN


def install_blueprints(config_dir: str) -> list[str]:
    """Copie les modèles absents et renvoie le nom des fichiers ajoutés.

    Un fichier déjà présent n'est jamais remplacé : l'utilisateur a pu le
    modifier. Chaque modèle porte une ``source_url``, Home Assistant sait donc
    le réimporter à la demande.
    """
    target = Path(config_dir) / "blueprints" / "automation" / DOMAIN
    added: list[str] = []
    for source in sorted(BLUEPRINTS_DIR.glob("*.yaml")):
        destination = target / source.name
        if destination.exists():
            continue
        target.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        added.append(source.name)
    return added
