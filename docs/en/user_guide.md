# Intégration Home Assistant – MEL Waste Collections

This documentation explains how to install and configure the `mel_collecte` custom component, and how to display collections in the Home Assistant interface (calendar and Trash Card).

---

## 1. Prerequisites

- Home Assistant Core, OS or Supervised (version ≥ 2024.6 recommended).
- Access to the `config/` directory of your instance (Samba, VS Code, SSH…).
- Internet connection to query the Publidata API of the European Metropolis of Lille.

---

## 2. Installing the Component

1. **Download the sources**
   - Clone the repository or retrieve the `mel_collecte.zip` archive generated via `make build`.

2. **Copy to Home Assistant**
   - Extract the `custom_components/mel_collecte` folder to your Home Assistant directory:
     ```
     /config/custom_components/mel_collecte
     ```

3. **Restart Home Assistant**
   - From the interface: `Settings → System → Restart`.
   - Or via CLI: `ha core restart`.

---

## 3. Adding the Integration

1. Open `Settings → Devices & Services → Add Integration`.
2. Search for **"MEL Collecte des déchets"**.
3. Enter your postal address (e.g. `19 rue Example, 59000 Lille`).
   The integration uses the API `https://api.publidata.io/v2/geocoder` to automatically retrieve the address ID, latitude, and longitude.
   The address is validated in real-time: if it cannot be found or if it is not in the service area of the European Metropolis of Lille, an explicit error message is displayed before creating the entry.
4. Validate: the entities are created after the first refresh (a few seconds).

---

## 4. Configuring Options

The integration allows you to customize several parameters after the initial addition:

1. Go to `Settings → Devices & Services → MEL Collecte des déchets`.
2. Click **"Configure"** next to the integration.
3. The available options are:
   - **Update interval**: data refresh frequency in days (1-30, default: 7).
   - **Forecast window**: number of days to look ahead for collection events (7-365, default: 90).
   - **Visible waste types**: selection of waste types to display. If no type is selected, all types are displayed (default behavior).

4. Validate to save. Changes take effect after the next refresh.

---

## 5. Available Entities

- `calendar.collectes_des_dechets`: calendar containing all upcoming collections (90-day rolling window).
- `sensor.prochaine_collecte`: ISO date/time of the next collection, with attributes:
  - `types` (raw codes `omr`, `dv`, `enc`, …),
  - `types_friendly` (French labels: "Ordures ménagères résiduelles", "Déchets verts"…),
  - `mode` (pickup, drop-off, appointment…),
  - `debut` / `fin`.
- `sensor.jours_avant_prochaine_collecte`: indicates the integer number of days remaining until the next collection.
- `sensor.collecte_<type>`: one sensor per detected type (`sensor.collecte_dechets_verts`, etc.).
- `sensor.alertes_collecte`: number of active collection service alerts, with attributes:
  - `alerts`: complete list of alerts with details (id, name, type, message, dates),
  - `last_alert_name`: title of the last alert,
  - `last_alert_type`: type of the last alert (`danger`, `warning`, `info`),
  - `last_alert_message`: HTML content of the last alert.

All sensors are automatically updated according to the configured interval + on startup.

---

## 6. Displaying in Home Assistant

### 6.1 Internal Calendar

1. Go to `Dashboards → Add Card → Calendar`.
2. Select `calendar.collectes_des_dechets`.
3. The calendar displays all generated collections (up to the configured forecast window).

### 6.2 Trash Card

For a more visual presentation, you can use the community **Trash Card** ([idaho/hassio-trash-card](https://github.com/idaho/hassio-trash-card)). This card reads your calendars and displays upcoming collections, with customizable icons and colors.

#### Quick Installation

1. Install Trash Card via HACS (or by copying the provided files in the repository).
2. Restart Home Assistant or reload Lovelace.

#### Configuration with `mel_collecte`

The `calendar.collectes_des_dechets` calendar is used as the source. Events are created with readable French labels: "Ordures ménagères résiduelles", "Déchets verts", "Emballages recyclables", etc.

Example YAML configuration:

```yaml
type: custom:trash-card
entities:
  - calendar.collectes_des_dechets
next_days: 120
pattern:
  - label: Residual waste
    icon: mdi:trash-can
    color: grey
    pattern: Ordures ménagères résiduelles
    type: waste
  - label: Green waste
    icon: mdi:leaf
    color: green
    pattern: Déchets verts
    type: organic
  - label: Packaging
    icon: mdi:recycle
    color: amber
    pattern: Emballages recyclables
    type: recycle
  - label: Bulky items
    icon: mdi:sofa
    color: purple
    pattern: Encombrants
    type: others
```

> **Important**: `pattern` (detection field) must exactly match the calendar event label. Sensors provide the complete list via the `types_friendly` attribute; you can check it in `Developer Tools → States`.

---

### 6.3 Alert Card

To display collection service alerts, use a Markdown card:

```yaml
type: markdown
title: 🚨 Collection Alerts
content: |
  {% set alerts = state_attr('sensor.alertes_collecte', 'alerts') %}
  {% if alerts and alerts | length > 0 %}
    {% for alert in alerts %}
  ### {{ alert.type_friendly }} – {{ alert.name }}
  {{ alert.message | regex_replace('<[^>]+>', '') | truncate(200) }}

  *Published on {{ alert.published_at[:10] }}*

  ---
    {% endfor %}
  {% else %}
  No active alerts.
  {% endif %}
```

This card displays all active alerts with their type (⚠️ Alert, ℹ️ Information), title, and message.

---

## 7. Possible Automations

### 7.1 Native Events (New)

The integration automatically triggers a `mel_collecte.collection_upcoming` event when a collection is approaching. This allows you to create simple automations without using templates.

**Configuring the delay:**
By default, the event is triggered 24 hours before the collection starts. You can modify this delay via the `mel_collecte.set_collection_offset` service:
```yaml
service: mel_collecte.set_collection_offset
data:
  hours_before: 12
```

**Automation example:**
```yaml
automation:
  - trigger:
      - platform: event
        event_type: mel_collecte.collection_upcoming
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.garbage_types | first == 'omr' }}"
    action:
      - service: notify.mobile_app
        data:
          message: "Remember to take out the grey bin in {{ trigger.event.data.hours_until }} hours!"
```

### 7.2 Other Automations
- **Day-before notification**: trigger at 8 PM if `sensor.collecte_dechets_verts_dans` is at 1.
- **Voice reminder**: use `sensor.prochaine_collecte` in a TTS script.
- **Bin management**: combine with an `input_boolean` to know which bin was put out.

---

## 8. Troubleshooting

- **No collections created**: check the address (MEL must serve this street). The log may contain errors if the API returns nothing.
- **Incorrect schedules**: Publidata data is authoritative. Events are generated from `opening_hours` slots. If an unexpected format appears, open an issue on the repository.
- **Trash Card not displaying**: check that the calendar entity is properly configured in the card and that patterns match exact labels.
- **Waste types not displayed**: check in the options that the desired types are selected. An unselected type appears neither in sensors nor in the calendar.
- **Manual refresh**: You can call the `mel_collecte.force_refresh` service via *Developer Tools → Services* to force an immediate update without restarting Home Assistant.

### 8.1 Retry Logic and Error Handling

The integration distinguishes two categories of errors when calling the Publidata API:

| Category | Examples | Behavior |
|----------|----------|----------|
| **Transient error** | Network error, timeout, HTTP 429 (too many requests), HTTP 5xx | Automatic retry up to 3 times with exponential delay (1 s, 2 s, 4 s) |
| **Permanent error** | HTTP 400, 401, 403, 404 (invalid address, incorrect API key) | No retry — error raised immediately |

In case of HTTP **429 (Too Many Requests)**, the `Retry-After` header is respected if present; otherwise exponential backoff applies with a 30-second ceiling.

After exhausting all retries, the coordinator marks the update as failed but does not crash Home Assistant. The next scheduled update will start from the beginning.

**Data freshness tracking**: the `last_update_success` attribute (available in `Developer Tools → States` on each entity) indicates the ISO timestamp of the last successful retrieval. If this value is old while the integration appears active, check the logs for repeated transient errors.

**Consulting logs**: transient errors are logged at the `WARNING` level (not `ERROR`), which allows you to filter them easily in `Settings → System → Logs`.

---

## 9. Updating

- Copy the new `custom_components/mel_collecte` folder over the old one.
- Restart Home Assistant.
- Registered options are preserved during the update.

---

Enjoy! Feel free to contribute or report a malfunction via the repository issues. Improvements (dedicated icons, appointment management, etc.) are being considered. 👍