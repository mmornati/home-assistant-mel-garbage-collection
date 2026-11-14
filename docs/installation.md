---
title: Installation
description: Installer MEL Collecte dans Home Assistant avec HACS et configurer son adresse.
---

# Installation

Il faut Home Assistant 2024.6 ou plus récent, et une adresse dans l'une des 95 communes de la Métropole Européenne de Lille.

## 1. Installer avec HACS

[Ouvrir le dépôt dans HACS](https://my.home-assistant.io/redirect/hacs_repository/?owner=mmornati&repository=home-assistant-mel-garbage-collection&category=integration){ .md-button .md-button--primary }

Le bouton ouvre HACS sur le bon dépôt. Sinon, à la main :

1. Dans HACS, ouvrez le menu en haut à droite puis **Dépôts personnalisés**.
2. Ajoutez `https://github.com/mmornati/home-assistant-mel-garbage-collection`, catégorie **Intégration**.
3. Cherchez **MEL Collecte**, installez, puis redémarrez Home Assistant.

??? note "Installation sans HACS"
    Téléchargez `mel_collecte.zip` depuis la [dernière version](https://github.com/mmornati/home-assistant-mel-garbage-collection/releases/latest), décompressez-le dans `config/custom_components/mel_collecte/`, puis redémarrez Home Assistant.

## 2. Ajouter votre adresse

[Ajouter l'intégration](https://my.home-assistant.io/redirect/config_flow_start/?domain=mel_collecte){ .md-button }

Ou bien : **Paramètres → Appareils et services → Ajouter une intégration**, puis cherchez **MEL Collecte**.

| Champ | À saisir |
|---|---|
| Adresse complète | Le numéro, la rue et la commune, par exemple `19 rue Gambetta, Lille` |
| Langue des libellés | Français (par défaut) ou anglais |

L'intégration retrouve votre secteur de collecte, puis crée un appareil **Collectes MEL** avec un calendrier et des capteurs. Vous pouvez ajouter plusieurs adresses : recommencez l'étape pour chacune.

!!! tip "Adresse introuvable ?"
    Écrivez l'adresse comme sur le site de la MEL, avec le nom de la commune. Les lieux-dits et les résidences sans numéro passent mieux avec le nom de la rue seule.

## 3. Poser une carte

Ouvrez un tableau de bord, passez en mode édition, **Ajouter une carte**, puis tapez « MEL ». Quatre cartes sont proposées ; aucune n'a besoin de réglage. Elles sont décrites sur la page [Les cartes](cartes.md).

<div class="mel-live" data-mel-card="mel-collecte-card" data-config='{"show_alerts": false}'></div>

!!! note "Les cartes n'apparaissent pas ?"
    Rechargez la page du navigateur en vidant le cache (++ctrl+shift+r++, ou « Vider le cache de l'interface » dans l'application mobile). Home Assistant charge les cartes au démarrage : un redémarrage après l'installation est nécessaire.

## Options

**Paramètres → Appareils et services → MEL Collecte → Configurer** :

| Option | Rôle | Par défaut |
|---|---|---|
| Intervalle de mise à jour | Nombre de jours entre deux lectures des données de la MEL | 7 |
| Horizon de prévision | Nombre de jours de collectes calculés à l'avance | 90 |
| Types visibles | Codes des types à garder (`omr`, `emb`, `dv`…), séparés par des virgules. Vide : tous | vide |
| Langue des libellés | Langue des noms de capteurs, des types de déchets et des cartes | Français |

Le calendrier change rarement : une lecture par semaine suffit. Pour forcer une lecture tout de suite, appelez le service `mel_collecte.force_refresh`.
