## Intégration Home Assistant – Collecte des déchets MEL

Ce dépôt contient un composant personnalisé Home Assistant permettant de récupérer les jours de collecte de la Métropole Européenne de Lille (MEL) via les APIs Publidata, et de les exposer sous forme :

- d’un calendrier (`calendar.mel_collectes`) ;
- de capteurs (`sensor.mel_collecte_*`) indiquant la prochaine collecte globale et par type de poubelle.

L’objectif est de pouvoir déclencher des automatisations (notifications, Trash Card, etc.) sans dépendre du widget MEL.

---

### API utilisées

1. **Géocodage** – obtenir l’identifiant d’adresse Publidata (clé `id`).
   ```bash
   curl 'https://api.publidata.io/v2/geocoder?q=EXAMPLE%20ADRESSE&limit=1&lookup=publidata'
   ```

2. **Collectes** – récupérer les services de collecte associés à l’adresse et leurs horaires.
   ```bash
   curl 'https://api.publidata.io/v2/search?size=999&types[]=Platform::Services::WasteCollection&instances[]=876&address_id=<ID_ADRESSE>'
   ```
   La réponse contient notamment :
   - `metas.garbage_types`: codes des poubelles (`omr`, `dv`, `cs`, `enc`, …) ;
   - `schedules[].opening_hours`: fréquence et horaire (ex. `week 1-52/2 Th 05:50-12:50`) ;
   - `metas.accepted_waste` / `rejected_waste` ;
   - `collection_mode` : ramassage devant la maison, dépôt, prise de RDV, etc.

3. **Alertes** – récupérer les alertes et messages du service de collecte.
   ```bash
   curl 'https://api.publidata.io/v2/search?types[]=Alert&states[]=visible&include[]=*model_name&instances[]=876&order[desc]=published_at&address_id=<ID_ADRESSE>&size=5'
   ```
   La réponse contient :
   - `name`: titre de l'alerte ;
   - `alert_type`: type (`danger`, `warning`, `info`) ;
   - `blurb`: contenu HTML du message ;
   - `start_at` / `end_at`: période de validité.

---

### Installation du composant

1. Copier le dossier `custom_components/mel_collecte` dans votre dossier `config/custom_components` de Home Assistant (et redémarrer).

2. Depuis l’interface HA, ajouter l’intégration **“MEL Collecte des déchets”** puis saisir l’adresse complète.

3. L’intégration interroge l’API Publidata :
   - Géocodage de l’adresse (une fois) ;
   - récupération des collectes et des alertes (au démarrage puis chaque semaine) ;
   - génération d’évènements jusqu’à 90 jours à partir des horaires fournis.

---

### Entités créées

- `calendar.mel_collectes` : calendrier contenant l’ensemble des collectes ;
- `sensor.prochaine_collecte` : date/heure ISO de la prochaine collecte ;
- `sensor.collecte_<type>` : une entité par type (`omr`, `dv`, …) avec date de la prochaine collecte correspondante ;
- `sensor.alertes_collecte` : nombre d'alertes actives du service, avec détails dans les attributs.

Chaque entité expose des attributs (`mode`, `types`, `collection_id`, etc.) pour faciliter les automatisations/notifications.

---

### Documentation utilisateur

Une notice complète (installation, configuration, intégration avec la carte [Trash Card](https://github.com/idaho/hassio-trash-card) et patterns des libellés) est disponible dans `docs/guide_utilisateur.md`.

---

### Personnalisation / pistes d’évolution

- Mapper les codes `garbage_types` vers des libellés en clair ou des icônes personnalisées.
- Afficher les listes `accepted_waste` / `rejected_waste` dans des cartes Lovelace.
- Prendre en charge les collectes `booking` (lien vers formulaire).
- Ajouter un service Home Assistant pour forcer un rafraîchissement immédiatement.

---

### Tests unitaires

Des tests basiques sont fournis (`pytest` requis) :

```bash
pip install pytest
pytest
```

---

### Structure du projet

```
custom_components/mel_collecte/
├── __init__.py
├── api.py
├── calendar.py
├── config_flow.py
├── const.py
├── coordinator.py
├── manifest.json
├── parser.py
├── sensor.py
└── strings.json
```

---

Bon tests ! N’hésitez pas à adapter la stratégie de parsing des horaires si d’autres formats apparaissent. Les contributions sont bienvenues.