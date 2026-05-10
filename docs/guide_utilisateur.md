# Intégration Home Assistant – Collectes MEL

Cette documentation explique comment installer et configurer le composant personnalisé `mel_collecte`, puis comment afficher les collectes dans l'interface Home Assistant (calendrier et carte Trash Card).

---

## 1. Pré-requis

- Home Assistant Core, OS ou Supervised (version ≥ 2024.6 recommandée).
- Accès au répertoire `config/` de votre instance (Samba, VS Code, SSH…).
- Connexion Internet pour interroger l'API Publidata de la Métropole Européenne de Lille.

---

## 2. Installation du composant

1. **Télécharger les sources**
   - Cloner le dépôt ou récupérer l'archive `mel_collecte.zip` générée via `make build`.

2. **Copier dans Home Assistant**
   - Extraire le dossier `custom_components/mel_collecte` dans votre répertoire Home Assistant :
     ```
     /config/custom_components/mel_collecte
     ```

3. **Redémarrer Home Assistant**
   - Depuis l'interface : `Paramètres → Système → Redémarrer`.
   - Ou via la CLI : `ha core restart`.

---

## 3. Ajout de l'intégration

1. Ouvrir `Paramètres → Appareils & services → Ajouter une intégration`.
2. Rechercher **"MEL Collecte des déchets"**.
3. Saisir l'adresse postale (ex. `19 rue Exemple, 59000 Lille`).
   L'intégration utilise l'API `https://api.publidata.io/v2/geocoder` pour récupérer automatiquement l'ID adresse, la latitude et la longitude.
4. Valider : les entités sont créées après le premier rafraîchissement (quelques secondes).

---

## 4. Configuration des options

L'intégration permet de personnaliser plusieurs paramètres après l'ajout initial :

1. Accéder à `Paramètres → Appareils & services → MEL Collecte des déchets`.
2. Cliquer sur **"Configurer"** à côté de l'intégration.
3. Les options disponibles sont :
   - **Intervalle de mise à jour** : fréquence de rafraîchissement des données en jours (1-30, défaut : 7).
   - **Fenêtre de prévision** : nombre de jours à avancer pour les événements de collecte (7-365, défaut : 90).
   - **Types de déchets visibles** : sélection des types de déchets à afficher. Si aucun type n'est sélectionné, tous les types sont affichés (comportement par défaut).

4. Valider pour enregistrer. Les modifications prennent effet après le prochain rafraîchissement.

---

## 5. Entités disponibles

- `calendar.collectes_des_dechets` : calendrier contenant toutes les collectes à venir (90 jours glissants).
- `sensor.prochaine_collecte` : date/heure ISO de la prochaine collecte, avec attributs :
  - `types` (codes bruts `omr`, `dv`, `enc`, …),
  - `types_friendly` (libellés français : "Ordures ménagères résiduelles", "Déchets verts"…),
  - `mode` (ramassage, dépôt, RDV…),
  - `debut` / `fin`.
- `sensor.collecte_<type>` : un capteur par type détecté (`sensor.collecte_dechets_verts`, etc.).
- `sensor.alertes_collecte` : nombre d'alertes actives du service de collecte, avec attributs :
  - `alerts` : liste complète des alertes avec détails (id, nom, type, message, dates),
  - `last_alert_name` : titre de la dernière alerte,
  - `last_alert_type` : type de la dernière alerte (`danger`, `warning`, `info`),
  - `last_alert_message` : contenu HTML de la dernière alerte.

Tous les capteurs sont mis à jour automatiquement selon l'intervalle configuré + au démarrage.

---

## 6. Affichage dans Home Assistant

### 6.1 Agenda interne

1. Aller dans `Tableaux de bord → Ajouter une carte → Agenda`.
2. Sélectionner `calendar.collectes_des_dechets`.
3. Le calendrier affiche toutes les collectes générées (jusqu'à la fenêtre de prévision configurée).

### 6.2 Carte Trash Card

Pour une présentation plus visuelle, vous pouvez utiliser la carte communautaire **Trash Card** ([idaho/hassio-trash-card](https://github.com/idaho/hassio-trash-card)). Cette carte lit vos calendriers et affiche les prochains passages, avec icônes et couleurs personnalisables.

#### Installation (rapide)

1. Installer Trash Card via HACS (ou en copiant les fichiers fournis dans le dépôt).
2. Redémarrer Home Assistant ou recharger Lovelace.

#### Configuration avec `mel_collecte`

Le calendrier `calendar.collectes_des_dechets` est utilisé comme source. Les'événements sont créés avec des libellés français lisibles : "Ordures ménagères résiduelles", "Déchets verts", "Emballages recyclables", etc.

Exemple de configuration YAML :

```yaml
type: custom:trash-card
entities:
  - calendar.collectes_des_dechets
next_days: 120
pattern:
  - label: Ordures ménagères
    icon: mdi:trash-can
    color: grey
    pattern: Ordures ménagères résiduelles
    type: waste
  - label: Déchets verts
    icon: mdi:leaf
    color: green
    pattern: Déchets verts
    type: organic
  - label: Emballages
    icon: mdi:recycle
    color: amber
    pattern: Emballages recyclables
    type: recycle
  - label: Encombrants
    icon: mdi:sofa
    color: purple
    pattern: Encombrants
    type: others
```

> **Important** : `pattern` (champ de détection) doit correspondre exactement au libellé d'événement du calendrier. Les capteurs fournissent la liste complète via l'attribut `types_friendly`; vous pouvez la consulter dans `Outils de développement → États`.

---

### 6.3 Carte des alertes

Pour afficher les alertes du service de collecte, utilisez une carte Markdown :

```yaml
type: markdown
title: 🚨 Alertes collecte
content: |
  {% set alerts = state_attr('sensor.alertes_collecte', 'alerts') %}
  {% if alerts and alerts | length > 0 %}
    {% for alert in alerts %}
  ### {{ alert.type_friendly }} – {{ alert.name }}
  {{ alert.message | regex_replace('<[^>]+>', '') | truncate(200) }}

  *Publié le {{ alert.published_at[:10] }}*

  ---
    {% endfor %}
  {% else %}
  Aucune alerte en cours.
  {% endif %}
```

Cette carte affiche toutes les alertes actives avec leur type (⚠️ Alerte, ℹ️ Information), titre, et message.

---

## 7. Automatisations possibles

- **Notification la veille** : déclencher à 20h si `sensor.collecte_dechets_verts` est à moins de 24h.
- **Rappel vocal** : utiliser `sensor.prochaine_collecte` dans un script TTS.
- **Gestion des bacs** : combiner avec `input_boolean` pour savoir quel bac est sorti.

---

## 8. Dépannage

- **Aucune collecte créée** : vérifier l'adresse (la MEL doit desservir cette rue). Le journal peut contenir des erreurs si l'API ne retourne rien.
- **Horaires incorrects** : les données Publidata font foi. Les événements sont générés à partir des créneaux `opening_hours`. Si un format inattendu apparaît, ouvrir une issue sur le dépôt.
- **Trash Card sans affichage** : vérifier que l'entité calendrier est bien configurée dans la carte et que les patterns correspondent aux libellés exacts.
- **Types de déchets non affichés** : vérifier dans les options que les types souhaités sont bien sélectionnés. Un type non sélectionné n'apparaît ni dans les capteurs ni dans le calendrier.

---

## 9. Mise à jour

- Copier le nouveau dossier `custom_components/mel_collecte` par-dessus l'ancien.
- Redémarrer Home Assistant.
- Les options enregistrées sont conservées lors de la mise à jour.

---

Bon usage ! N'hésitez pas à contribuer ou à signaler un dysfonctionnement via les issues du dépôt. Des améliorations (icônes dédiées, gestion des RDV, etc.) sont envisagées. 👍