---
title: Automatisations
description: Exemples d'automatisations avec MEL Collecte, rappel la veille, annonce vocale, déchèterie ouverte.
---

# Automatisations

## L'événement de rappel

Avant chaque collecte, l'intégration déclenche l'événement `mel_collecte.collection_upcoming`. Par défaut 24 heures avant ; le service `mel_collecte.set_collection_offset` change ce délai.

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
