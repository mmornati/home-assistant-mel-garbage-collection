---
title: Automatisations
description: Modèles d'automatisation prêts à l'emploi et exemples, rappel des bacs, déchèterie mobile, annonce vocale.
---

# Automatisations

## Les modèles prêts à l'emploi

L'intégration fournit deux modèles d'automatisation (blueprints). Ils s'appuient sur les capteurs, sans YAML à écrire : on choisit le capteur, l'heure et le téléphone.

| Modèle | Ce qu'il fait |
|---|---|
| **Rappel pour sortir les bacs** | À l'heure choisie, la veille ou le jour même d'une collecte, envoie la liste des bacs à sortir. Rien les jours sans collecte |
| **Passage de la déchèterie mobile** | Prévient la veille ou le jour même d'un passage, avec un filtre sur la commune et sur la distance |

### Les installer

Avec les versions postérieures à la 1.6.0, les deux modèles sont copiés dans `config/blueprints/automation/mel_collecte/` au démarrage de Home Assistant. Ils apparaissent dans **Paramètres > Automatisations et scènes > Blueprints**.

Avec la 1.6.0, ou pour récupérer la dernière version d'un modèle, importez-les :

[![Importer le blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fmmornati%2Fhome-assistant-mel-garbage-collection%2Fblob%2Fmain%2Fcustom_components%2Fmel_collecte%2Fblueprints%2Fautomation%2Fmel_collecte%2Frappel_bacs.yaml)
Rappel pour sortir les bacs

[![Importer le blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fmmornati%2Fhome-assistant-mel-garbage-collection%2Fblob%2Fmain%2Fcustom_components%2Fmel_collecte%2Fblueprints%2Fautomation%2Fmel_collecte%2Frappel_decheterie_mobile.yaml)
Passage de la déchèterie mobile

Un modèle déjà présent n'est jamais remplacé par une mise à jour de l'intégration : vos modifications sont conservées. Le menu du blueprint propose **Réimporter** pour reprendre la version publiée.

### Rappel pour sortir les bacs

1. Dans **Blueprints**, ouvrez **MEL Collecte : rappel pour sortir les bacs** et choisissez **Créer une automatisation**.
2. **Capteurs de collecte** : sélectionnez les capteurs **Collecte *type*** des bacs à suivre. Un capteur par bac permet d'annoncer deux collectes le même jour ; **Prochaine collecte** seul suffit si vous n'en avez jamais qu'une.
3. Réglez l'heure (19 h par défaut) et le nombre de jours avant la collecte : `1` pour la veille, `0` pour le jour même.
4. Choisissez les téléphones à prévenir.

Le message est modifiable. Il dispose des variables `bacs` (« Ordures ménagères résiduelles, Emballages recyclables »), `bacs_liste` et `quand` (« demain »).

### Passage de la déchèterie mobile

1. Créez une automatisation à partir de **MEL Collecte : passage de la déchèterie mobile**.
2. Sélectionnez le capteur **Prochaine déchèterie mobile**.
3. **Commune** : saisissez le nom de votre commune, par exemple `Lomme`, pour ignorer les passages des communes voisines. Le texte est cherché dans le nom et l'adresse du site.
4. Réglez l'heure, le nombre de jours avant le passage et les téléphones.

!!! note "Filtre par commune et version"
    Jusqu'à la version 1.6.0, le capteur ne connaît que le tout prochain passage parmi les trois sites les plus proches : un passage dans votre commune peut être masqué par celui d'une commune voisine prévu plus tôt le même jour. Les versions suivantes ajoutent l'attribut `passages` (le prochain passage de chaque site) et le filtre devient exact.

### Autre chose qu'une notification

Les deux modèles ont un champ **Actions supplémentaires** : annonce vocale, lampe, groupe de notification. Les variables du message y sont disponibles.

```yaml
- service: tts.speak
  target:
    entity_id: tts.home_assistant_cloud
  data:
    media_player_entity_id: media_player.cuisine
    message: "Pensez aux poubelles : {{ bacs }}."
```

Pour deux rappels (la veille au soir et le matin même), créez deux automatisations à partir du même modèle.

## L'événement de rappel

Avant chaque collecte, l'intégration déclenche l'événement `mel_collecte.collection_upcoming`. Par défaut 24 heures avant ; le service `mel_collecte.set_collection_offset` change ce délai.

!!! warning "Versions jusqu'à la 1.6.0"
    L'événement n'y était émis qu'au moment où l'intégration relisait les données de la MEL, une fois par semaine par défaut : un rappel pouvait donc ne jamais partir. Les versions suivantes le vérifient chaque minute. Les modèles ci-dessus ne dépendent pas de cet événement.

| Donnée | Contenu |
|---|---|
| `garbage_types` | Codes des déchets collectés, par exemple `["omr", "emb"]` |
| `garbage_types_friendly` | Les mêmes en clair : `["Ordures ménagères résiduelles", "Emballages recyclables"]` |
| `start`, `end` | Début et fin du passage |
| `hours_until`, `days_until` | Temps restant |
| `address`, `entry_id` | L'adresse concernée, utile si vous en suivez plusieurs |

## Une notification la veille

```yaml
alias: Rappel poubelles
trigger:
  - platform: event
    event_type: mel_collecte.collection_upcoming
action:
  - service: notify.mobile_app_telephone
    data:
      title: Poubelles
      message: >
        À sortir : {{ trigger.event.data.garbage_types_friendly | join(', ') }}.
```

## Une lampe à la couleur du bac

La lampe de l'entrée prend la couleur du couvercle jusqu'à ce que le bac soit sorti.

```yaml
alias: Lampe couleur du bac
trigger:
  - platform: event
    event_type: mel_collecte.collection_upcoming
action:
  - service: light.turn_on
    target:
      entity_id: light.entree
    data:
      color_name: >
        {% set bac = trigger.event.data.garbage_types[0] %}
        {{ {'omr': 'white', 'emb': 'yellow', 'dv': 'orange', 'bio': 'orange'}.get(bac, 'purple') }}
      brightness_pct: 60
```

## Une annonce vocale à 19 h

Le rappel arrive au bon moment pour les collectes du matin : la veille au soir.

```yaml
alias: Annonce poubelles
trigger:
  - platform: time
    at: "19:00:00"
condition:
  - condition: numeric_state
    entity_id: sensor.collectes_mel_jours_avant_prochaine_collecte
    below: 2
action:
  - service: tts.speak
    target:
      entity_id: tts.home_assistant_cloud
    data:
      media_player_entity_id: media_player.cuisine
      message: >
        Pensez aux poubelles :
        {{ state_attr('sensor.collectes_mel_jours_avant_prochaine_collecte', 'next_collection_type') | join(' et ') }}.
```

!!! note "Identifiants d'entités"
    Les identifiants de ces exemples sont ceux d'une installation en français. Vérifiez les vôtres sur la page de l'appareil **Collectes MEL**.

## Prévenir quand la déchèterie ferme bientôt

```yaml
alias: Déchèterie, dernière heure
trigger:
  - platform: template
    value_template: >
      {% set fin = state_attr('binary_sensor.collectes_mel_decheterie_ouverte', 'fermeture') %}
      {{ fin is not none and (as_datetime(fin) - now()).total_seconds() < 3600 }}
condition:
  - condition: state
    entity_id: binary_sensor.collectes_mel_decheterie_ouverte
    state: "on"
action:
  - service: notify.mobile_app_telephone
    data:
      message: >
        La {{ state_attr('binary_sensor.collectes_mel_decheterie_ouverte', 'nom') }}
        ferme dans une heure.
```

## Ne garder que certains déchets

Une condition sur `garbage_types` limite un rappel au bac qui vous intéresse :

```yaml
condition:
  - condition: template
    value_template: "{{ 'emb' in trigger.event.data.garbage_types }}"
```
