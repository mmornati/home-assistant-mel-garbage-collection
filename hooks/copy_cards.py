"""Copie les cartes de l'intégration dans le site, pour les démonstrations en direct.

Le site affiche les vraies cartes : il utilise donc le fichier livré avec
l'intégration plutôt qu'une copie qui finirait par diverger.
"""

import shutil
from pathlib import Path

SOURCE = Path("custom_components/mel_collecte/frontend/mel-collecte-cards.js")


def on_post_build(config, **kwargs):
    target = Path(config["site_dir"]) / "assets" / SOURCE.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, target)
