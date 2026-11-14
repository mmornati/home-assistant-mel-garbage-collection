---
title: Les cartes
description: Les quatre cartes de tableau de bord livrées avec MEL Collecte et leurs options.
---

# Les cartes

Quatre cartes sont livrées avec l'intégration. Il n'y a rien d'autre à installer : ni carte tierce, ni ressource à déclarer. Elles trouvent seules l'adresse configurée, suivent le thème clair ou sombre de Home Assistant et parlent la langue choisie dans les options de l'intégration.

Les cartes de cette page sont les vraies, branchées sur une adresse d'exemple : vous pouvez cliquer dedans.

## Prochaine collecte

La carte dit quoi faire, dans vos mots : « Ce soir, sortez le bac marron », « Sortez le bac gris avant 18 h 30 », « Collecte en cours ». Le bac concerné s'avance sur le trottoir, et le camion passe pendant la collecte. En dessous, les jours à venir et les informations publiées par la MEL.

<div class="mel-live" data-mel-card="mel-collecte-card"></div>

```yaml
type: custom:mel-collecte-card
```

| Option | Rôle | Par défaut |
|---|---|---|
| `days` | Nombre de jours affichés sous la scène, de 7 à 21 | `14` |
| `show_alerts` | Afficher les informations de la MEL (travaux, grèves, reports) | `true` |

!!! info "Quand sortir le bac ?"
    La carte applique la règle de la MEL : pour une collecte du matin, le bac se sort la veille au soir après 19 h ; pour une collecte de l'après-midi ou du soir, le jour même.

## Calendrier

Le mois en cours, avec une marque de la couleur du couvercle sous chaque jour de collecte. Touchez un jour pour voir les heures de passage ; les flèches changent de mois.

<div class="mel-live" data-mel-card="mel-collecte-calendar-card"></div>

```yaml
type: custom:mel-collecte-calendar-card
```

| Couleur | Collecte |
|---|---|
| <span class="mel-swatch" style="--c:#7b8794"></span> Gris | Ordures ménagères |
| <span class="mel-swatch" style="--c:#f0b90b"></span> Jaune | Emballages recyclables |
| <span class="mel-swatch" style="--c:#8d5b3a"></span> Marron | Biodéchets |
| <span class="mel-swatch" style="--c:#2e9d5c"></span> Vert | Verre |
| <span class="mel-swatch" style="--c:#8a5cd6"></span> Violet | Encombrants |

## Guide du tri

Les consignes officielles de la MEL pour votre adresse : ce qui va dans chaque bac, et ce qui n'y va pas. Le champ de recherche parcourt toutes les consignes à la fois ; il ignore les accents et les majuscules.

<div class="mel-live" data-mel-card="mel-collecte-guide-card"></div>

```yaml
type: custom:mel-collecte-guide-card
```

## Déchèteries et points d'apport

Les lieux les plus proches de votre adresse, classés par distance à vol d'oiseau, avec un plan schématique centré sur chez vous.

- **Déchèteries** : les 14 déchèteries de la métropole, ouvertes ou fermées à l'instant, heure de fermeture ou de prochaine ouverture.
- **Mobiles** : le prochain passage des déchèteries mobiles (elles ne circulent pas de décembre à février).
- **Verre** : les bornes à verre de votre code postal.
- **Compost** : les composteurs de quartier.

Le lien **Itinéraire** ouvre le trajet dans Google Maps.

<div class="mel-live" data-mel-card="mel-collecte-places-card"></div>

```yaml
type: custom:mel-collecte-places-card
```

| Option | Rôle | Par défaut |
|---|---|---|
| `count` | Nombre de lieux affichés, de 2 à 8 | `4` |
| `show_map` | Afficher le plan | `true` |

## Options communes

Toutes les options se règlent dans l'éditeur visuel de la carte.

| Option | Rôle |
|---|---|
| `title` | Remplace le titre de la carte |
| `entry` | L'adresse à afficher, si plusieurs sont configurées. Sans cette option, la première adresse est utilisée |
| `language` | `fr` ou `en`, pour une carte dans une autre langue que celle de l'intégration |

## Une vue complète

Pour une vue « Déchets » prête à coller dans un tableau de bord (mode YAML de la vue) :

```yaml
title: Déchets
icon: mdi:trash-can-outline
type: sections
sections:
  - cards:
      - type: custom:mel-collecte-card
      - type: custom:mel-collecte-calendar-card
  - cards:
      - type: custom:mel-collecte-guide-card
  - cards:
      - type: custom:mel-collecte-places-card
```

## Et Trash Card ?

Le calendrier créé par l'intégration reste compatible avec la carte communautaire [Trash Card](https://github.com/idaho/hassio-trash-card). Les attributs `couleur` et `couleurs` des capteurs donnent la couleur du bac pour vos propres cartes.
