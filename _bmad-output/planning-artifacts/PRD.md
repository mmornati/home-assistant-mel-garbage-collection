# PRD - MEL Waste Collection - Home Assistant Integration

## 1. Product Overview

### 1.1 Executive Summary

**MEL Waste Collection** is a custom component for Home Assistant that retrieves collection days for the European Metropolis of Lille (MEL) via the Publidata APIs, and exposes them as entities usable for automations.

**Project Type**: Home Assistant Extension (custom integration)

** Target Market**: French Home Assistant users residing in the Lille metropolitan area who want to integrate waste collection information into their home automation.

**Main Value Add**: Enables automations (notifications, Trash Card, reminders) without depending on the official MEL widget, with full control over the data.

---

## 2. Project Context

### 2.1 Problem Identified

Residents of the European Metropolis of Lille do not have easy access to waste collection dates via an open API. The official MEL widget is limited and does not allow deep integration with Home Assistant.

### 2.2 Proposed Solution

A Home Assistant integration that:
- Queries the Publidata API to geocode the user's address
- Retrieves collection schedules by waste type
- Generates calendar events up to 90 days
- Displays service collection alerts

### 2.3 Competition and Alternatives

| Alternative | Description | Limitations |
|-------------|-------------|---------|
| Official MEL widget | Integrated web page | No HA integration, limited data |
| MEL mobile apps | Collection tracking | Not integrable in HA |
| Other integrations | Solutions for other metros | Not MEL compatible |

---

## 3. Personas

### 3.1 Main Persona: "The Home Automator"

- **Profile**: Technical Home Assistant user, develops their own automations
- **Age**: 30-55 years
- **Skills**: Able to modify YAML, install custom components
- **Goals**: Automate bin put-out reminders, optimize waste management
- **Pain Points**: Dependency on external widget, lack of control over data

### 3.2 Secondary Persona: "The Casual User"

- **Profile**: Beginner to intermediate Home Assistant user
- **Age**: 25-70 years
- **Skills**: Knows how to install via HACS, add integrations
- **Goals**: See upcoming collections on dashboard
- **Pain Points**: Technical complexity, wants a ready-to-use solution

---

## 4. Functional Requirements

### 4.1 Core Features (MVP)

| ID | Feature | Priority | Description |
|----|----------------|----------|-------------|
| F01 | Address geocoding | Critical | Transform entered address into Publidata ID |
| F02 | Collection retrieval | Critical | Query API to get collection schedules |
| F03 | Event generation | Critical | Create calendar events for 90 days |
| F04 | "Next collection" sensor | Critical | Sensor giving date/time of next collection |
| F05 | Per-type sensors | High | One sensor per waste type (OMR, DV, etc.) |
| F06 | Calendar integration | High | Calendar entity compatible with HA |
| F07 | UI configuration | High | Config flow for address input |
| F08 | Automatic refresh | Medium | Weekly data update |

### 4.2 Extended Features (v2+)

| ID | Feature | Priority | Description |
|----|----------------|----------|-------------|
| F09 | Alert sensor | High | Sensor displaying service alerts |
| F10 | Built-in notifications | Medium | Push notifications during collections |
| F11 | Refresh service | Medium | API for manual update |
| F12 | Appointment handling | Low | Account for scheduled collections |
| F13 | Custom icons | Low | Images for different waste types |

### 4.3 Use Cases

**UC1: Collection Notification**
> The user receives a notification the evening before if the next day is a green waste collection day.

**UC2: Trash Card Display**
> The user configures a Trash Card on their dashboard showing upcoming collections with custom icons and colors.

**UC3: Seasonal Automation**
> The user disables green waste reminders in winter (November-February) via conditional automation.

---

## 5. Non-Functional Requirements

### 5.1 Performance

- API response time < 5 seconds
- Entity update < 10 seconds after API retrieval
- Server load: 1 request/instance pooling

### 5.2 Reliability

- Geocoding error handling (address not found)
- Network error handling (20s timeout)
- Geocoding cache to avoid redundant requests
- No stale data: auto refresh every week

### 5.3 Compatibility

- Home Assistant Core >= 2024.6
- Python 3.10+
- Protocol: aiohttp for async API calls

### 5.4 Security

- No sensitive data stored
- Address only: no personal data transmitted
- HTTPS only for API calls

---

## 6. Functional Architecture

### 6.1 Main Components

```
┌─────────────────────────────────────────────────────────────┐
│                    HOME ASSISTANT                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              MEL_COLLECTE INTEGRATION                │   │
│  │  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌────────┐  │   │
│  │  │ Config  │  │API Client│  │Coordina-│  │ Parser │  │   │
│  │  │ Flow    │  │          │  │tor      │  │        │  │   │
│  │  └────┬────┘  └────┬─────┘  └────┬────┘  └────┬─────┘  │   │
│  │       │            │            │            │        │   │
│  │       ▼            ▼            ▼            ▼        │   │
│  │  ┌─────────────────────────────────────────────┐     │   │
│  │  │              HA ENTITIES                      │     │   │
│  │  │  • Calendar: collectes_des_dechets           │     │   │
│  │  │  • Sensor: prochaine_collecte                │     │   │
│  │  │  • Sensor: collecte_<type> (per waste)     │     │   │
│  │  │  • Sensor: alertes_collecte                  │     │   │
│  │  └─────────────────────────────────────────────┘     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API PUBLIDATA                            │
│  • /v2/geocoder (geocoding)                                 │
│  • /v2/search (collections + alerts)                        │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Data Flow

1. **Configuration**: User enters address → Config Flow
2. **Geocoding**: Publidata API → returns address_id, lat, lon
3. **Retrieval**: Publidata API → returns WasteCollection + Alert
4. **Parsing**: parser.py → converts schedules to occurrences
5. **Exposure**: Coordinator → updates HA entities

---

## 7. Technical Stack

| Component | Technology |
|-----------|-------------|
| Framework | Home Assistant |
| Language | Python 3.10+ |
| HTTP calls | aiohttp |
| Schedule parsing | regex |
| Configuration | voluptuous + config_entries |
| Tests | pytest |

---

## 8. Supported Waste Types

| Code | French Label |
|------|-----------------|
| omr | Ordures ménagères résiduelles |
| dv | Déchets verts |
| cs | Cartons / sacs |
| enc | Encombrants |
| bio | Biodéchets |
| verre | Verre |
| text | Textiles |
| deee | Déchets électroniques |
| pile | Piles et batteries |
| emb | Emballages recyclables |

---

## 9. Success Metrics

### 9.1 User KPIs

- Number of installations (via HACS or direct)
- Number of active configurations
- GitHub issues handled

### 9.2 Technical KPIs

- Average API response time
- Geocoding error rate
- Test coverage

---

## 10. Roadmap

### Phase 1: MVP (v1.0) - ✓ Complete
- [x] Address geocoding
- [x] Collection retrieval
- [x] Per-type sensors
- [x] Calendar
- [x] Config flow

### Phase 2: Improvements (v1.1) - ✓ Complete
- [x] Alert sensor
- [x] Enriched attributes (types_friendly)

### Phase 3: Advanced Features (v2.0) - Upcoming
- [ ] Refresh service
- [ ] Built-in notifications
- [ ] Scheduled collection handling

---

## 11. Risks and Dependencies

### 11.1 Risks

| Risk | Impact | Probability | Mitigation |
|--------|--------|-------------|------------|
| Publidata API change | High | Medium | Error monitoring, fast adaptation |
| API unavailability | High | Low | Cache, fallbacks |
| HA obsolescence | Medium | Low | Long-term compatibility |

### 11.2 External Dependencies

- **Publidata API**: Third-party service, no control over availability
- **Home Assistant**: Depends on entity structure

---

## 12. Glossary

| Term | Definition |
|-------|------------|
| MEL | Métropole Européenne de Lille |
| Publidata | Geolocated API publisher |
| WasteCollection | API entity type for collections |
| Config Flow | HA configuration interface |
| Coordinator | HA pattern for data management |
| Trash Card | Community Lovelace card for waste |