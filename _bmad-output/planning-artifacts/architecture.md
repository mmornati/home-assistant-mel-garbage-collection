# Architecture - MEL Waste Collection

## 1. Overview

The **MEL Waste Collection** integration is a custom Home Assistant component that communicates with the Publidata API to retrieve waste collection information for the European Metropolis of Lille (MEL).

The architecture follows the standard Home Assistant integration model with:
- A **Config Flow** for user configuration
- A **DataUpdateCoordinator** for data management
- **Entities** (sensors, calendar) for exposure in HA

---

## 2. Functional Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              HOME ASSISTANT                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    DOMAIN: mel_collecte                              │   │
│  │                                                                     │   │
│  │  ┌──────────────┐     ┌─────────────────────────────────────────┐   │   │
│  │  │ __init__.py  │     │           COORDINATOR                  │   │   │
│  │  │              │     │  ┌───────────────────────────────────┐  │   │   │
│  │  │ • async_set- │────▶│  │MelCollecteCoordinator            │  │   │   │
│  │  │   up_entry   │     │  │                                   │  │   │   │
│  │  │ • async_un-  │     │  │ • _async_update_data()           │  │   │   │
│  │  │   load_entry │     │  │ • geocode_address()               │  │   │   │
│  │  └──────────────┘     │  │ • fetch_waste_collections()      │  │   │   │
│  │                       │  │ • fetch_alerts()                 │  │   │   │
│  │                       │  │ • parse_schedule()                │  │   │   │
│  │                       │  └───────────────────────────────────┘  │   │   │
│  │                       └─────────────────────────────────────────┘   │   │
│  │                                    │                                    │   │
│  │                                    ▼                                    │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │                         ENTITÉS                                 │  │   │
│  │  │                                                                  │  │   │
│  │  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐   │  │   │
│  │  │  │    Calendar      │  │    Sensors       │  │  Config     │   │  │   │
│  │  │  │                  │  │                  │  │  Flow       │   │  │   │
│  │  │  │ • mel_collecte   │  │ • prochaine_     │  │              │   │  │   │
│  │  │  │   _calendar      │  │   _collecte     │  │ • user      │   │  │   │
│  │  │  │                  │  │ • collecte_<type>│  │ • options   │   │  │   │
│  │  │  │ • event          │  │ • alertes       │  │              │   │  │   │
│  │  │  │ • async_get_     │  │                  │  │              │   │  │   │
│  │  │  │   _events()      │  │                  │  │              │   │  │   │
│  │  │  └──────────────────┘  └──────────────────┘  └──────────────┘   │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API PUBLIDATA (External)                           │
│                                                                             │
│   ┌─────────────────────┐      ┌─────────────────────┐                      │
│   │   /v2/geocoder     │      │   /v2/search        │                      │
│   │                    │      │                     │                      │
│   │ • q: address       │      │ • types[]           │                      │
│   │ • lookup          │      │ • instances[]      │                      │
│   │ • citycode        │      │ • address_id        │                      │
│   │                    │      │ • lat/lon           │                      │
│   │ ◄── Address ID    │      │ ◄── Collections    │                      │
│   │ ◄── Lat/Lon       │      │ ◄── Alerts          │                      │
│   └─────────────────────┘      └─────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
User enters address
          │
          ▼
┌────────────────────────┐
│   Config Flow         │
│  (config_flow.py)     │
└──────────┬───────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    MelCollecteCoordinator                        │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ Geocoding   │───▶│ Fetch       │───▶│ Parse               │  │
│  │ (api.py)    │    │ Collections │    │ (parser.py)         │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│        │                   │                    │                │
│        ▼                   ▼                    ▼                │
│  address_id         collections          occurrences             │
│  lat/lon            + alerts             (dates/times)         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────────────┐
│                      HA ENTITIES                                  │
│                                                                  │
│  • calendar.collectes_des_dechets (90-day events)                    │
│  • sensor.prochaine_collecte (next collection)                    │
│  • sensor.collecte_omr, sensor.collecte_dv, etc.                 │
│  • sensor.alertes_collecte (active alerts)                     │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Module Structure

### 3.1 Component Files

```
custom_components/mel_collecte/
├── __init__.py          # Entry point, async_setup_entry
├── manifest.json        # HACS/HA metadata
├── config_flow.py       # UI configuration
├── const.py             # Constants (URLs, labels, codes)
├── api.py               # HTTP client for Publidata
├── coordinator.py       # Main DataUpdateCoordinator
├── parser.py            # Schedule parsing
├── sensor.py            # Sensor entities
├── calendar.py         # Calendar entity
└── strings.json         # UI translations
```

### 3.2 Module Details

#### 3.2.1 `__init__.py` - Entry Point

**Responsibilities:**
- Domain registration
- Platform setup (sensor, calendar)
- Lifecycle management (setup/unload)

```python
# Pseudocode flow
async def async_setup_entry(hass, entry):
    # Create API client
    session = aiohttp_client.async_get_clientsession(hass)
    api = MelCollecteAPI(session)

    # Create coordinator
    coordinator = MelCollecteCoordinator(hass, api, address=..., instance_id=...)

    # First refresh
    await coordinator.async_config_entry_first_refresh()

    # Store data
    hass.data[DOMAIN][entry.entry_id] = {DATA_COORDINATOR: coordinator}

    # Forward to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
```

#### 3.2.2 `api.py` - HTTP Client

**Responsibilities:**
- HTTP calls to Publidata API
- Geocoding cache management
- Timeout handling

**Public Methods:**
| Method | Description |
|---------|-------------|
| `geocode_address()` | Returns address_id, lat, lon for an address |
| `fetch_waste_collections()` | Returns collections for an address |
| `fetch_alerts()` | Returns service alerts |

**Configuration:**
- Timeout: 20 seconds
- Geocoding cache: in-memory (per instance)

```python
# Typical call
response = await self._session.get(GEO_URL, params={
    "q": address,
    "limit": 1,
    "lookup": "publidata",
})
```

#### 3.2.3 `coordinator.py` - Data Coordinator

**Responsibilities:**
- API calls orchestration
- Schedule parsing into occurrences
- Calendar event generation
- Periodic refresh (weekly)

**Pattern Used:** Home Assistant `DataUpdateCoordinator`

**Exposed Data:**
```python
{
    "address": {...},           # Geocoding result
    "collections": [...],       # Parsed collections
    "events": [...],            # Sorted calendar events
    "alerts": [...],            # Active alerts
    "fetched_at": "ISO..."      # Update timestamp
}
```

**Schedule Parsing Logic:**

```
Schedule example: "week 1-52/2 Th 05:50-12:50"
                    │       │    │   │
                    │       │    │   └── End time
                    │       │    └────── Start time
                    │       └────────── Day (Thursday)
                    └────────────────── Weeks (even weeks)
```

The parser (`parser.py`) converts this format into concrete occurrences over 90 days.

#### 3.2.4 `parser.py` - Schedule Parsing

**Responsibilities:**
- Week pattern extraction (week 1-52/2 = even weeks)
- Day extraction (Mo, Tu, We, Th, Fr, Sa, Su)
- Time slot extraction (05:50-12:50)
- Occurrence list generation

**Functions:**
```python
def parse_schedule(schedule: str, start: datetime, end: datetime) -> List[Dict]:
    # Returns [{"start": datetime, "end": datetime}, ...]
```

#### 3.2.5 `config_flow.py` - User Configuration

**Responsibilities:**
- Address input form
- Address validation via geocoding
- Configuration entry creation

**Flow:**
```
user_step → validate address → create entry
                 │
                 └─> Error: "Address not found"
```

#### 3.2.6 `sensor.py` - Sensor Entities

**Sensors Created:**

| Sensor | Description | Attributes |
|---------|-------------|-----------|
| `prochaine_collecte` | Next collection (all types) | types, types_friendly, mode, debut, fin |
| `collecte_<type>` | Next collection by type | collection_id, mode, types, debut, fin |
| `alertes_collecte` | Active alerts count | alerts[], last_alert_*, etc. |

#### 3.2.7 `calendar.py` - Calendar Entity

**Responsibilities:**
- Current event (`event` property)
- Events list over period (`async_get_events`)
- Coordinator synchronization

**Event Format:**
```python
CalendarEvent(
    summary="Ordures ménagères résiduelles, Déchets verts",
    start=datetime,
    end=datetime,
    description="Collecte OM • Ordures ménagères résiduelles, Déchets verts"
)
```

---

## 4. Home Assistant Patterns Used

### 4.1 Config Flow

Standard interface for integration configuration:
- Input form
- Validation
- Entry creation

### 4.2 DataUpdateCoordinator

Central pattern for data management:
- Automatic refresh (configurable interval)
- Cache management
- Error propagation

### 4.3 Entity Mixins

Using Home Assistant base classes:
- `SensorEntity` for sensors
- `CalendarEntity` for calendar
- `DeviceInfo` for device information

---

## 5. Configuration and Constants

### 5.1 API URLs

```python
GEO_URL = "https://api.publidata.io/v2/geocoder"
SEARCH_URL = "https://api.publidata.io/v2/search"
```

### 5.2 Parameters

| Parameter | Value | Description |
|-----------|--------|-------------|
| `DEFAULT_INSTANCE_ID` | "876" | MEL ID in Publidata |
| `UPDATE_INTERVAL_DAYS` | 7 | Auto refresh |
| `LOOKAHEAD_DAYS` | 90 | Event generation |

### 5.3 Waste Types

```python
GARBAGE_TYPES_LABELS = {
    "omr": "Ordures ménagère résiduelles",
    "dv": "Déchets verts",
    "cs": "Cartons / sacs",
    "enc": "Encombrants",
    "bio": "Biodéchets",
    "verre": "Verre",
    "text": "Textiles",
    "deee": "Déchets électroniques",
    "pile": "Piles et batteries",
    "emb": "Emballages recyclables",
}
```

---

## 6. Execution Flow - Scenarios

### 6.1 First Start (Configuration)

```
1. User adds integration via UI
2. Enters address: "19 rue example, 59000 Lille"
3. Config flow calls geocode_address()
4. API returns: {id: "...", geometry: {coordinates: [lat, lon]}}
5. Entry created with: address, instance_id, lat, lon
6. __init__.py creates coordinator
7. async_config_entry_first_refresh() → fetch collections + alerts
8. Entities created → calendar and sensors available
```

### 6.2 Automatic Refresh

```
1. Timer triggers (every 7 days)
2. Coordinator._async_update_data() called
3. If no geocoding cache: geocode_address()
4. fetch_waste_collections() → new data
5. fetch_alerts() → new alerts
6. parse_schedule() → new occurrences
7. Entities updated automatically
```

### 6.3 User Consultation

```
1. User displays dashboard
2. Calendar.get_events() called by HA
3. Returns event list (90 days)
4. Trash Card reads calendar → displays collections
```

---

## 7. Architecture Decisions

### 7.1 Key Decisions

| Decision | Justification |
|----------|----------------|
| External API (Publidata) | Official MEL data, no mirroring |
| aiohttp async | Compatible with HA async model |
| Geocoding cache in memory | Avoids redundant requests for same address |
| Weekly refresh | Trade-off between freshness and API load |
| 90-day events | Sufficient for most use cases |

### 7.2 Current Limitations

- Single address per integration instance
- No multi-instance support (multiple addresses)
- No fallback if Publidata API unavailable
- Schedule parsing limited to detected format

### 7.3 Future Improvements

- HA service to force refresh
- Support multiple addresses
- Persistent cache for crash recovery
- More elaborate error handling

---

## 8. Tests

### 8.1 Test Structure

```
pytest
├── test_parser.py         # Schedule parser tests
├── test_api.py           # API client tests (mock)
├── test_coordinator.py    # Coordinator tests
└── test_integration.py   # Integration tests
```

### 8.2 Approach

- **Mocks**: Simulated API responses
- **Fixtures**: Test data for schedules
- **Coverage**: Core modules (api, parser, coordinator)

---

## 9. Dependencies

### 9.1 Python Dependencies

| Package | Usage |
|---------|-------|
| aiohttp | Async HTTP calls |
| async-timeout | Timeout handling |
| homeassistant | Framework |

### 9.2 External Dependencies

| Service | Description |
|---------|-------------|
| Publidata API | Collection data source |

---

## 10. Security

### 10.1 Data Handled

- **Address**: User input, sent to Publidata
- **No personal data**: Only the address
- **HTTPS**: All communications

### 10.2 Best Practices

- 20-second timeout to prevent blocking
- Error handling with logging
- No sensitive data in logs

---

## 11. Technical Glossary

| Term | Definition |
|-------|------------|
| Config Flow | Configuration interface in HA |
| DataUpdateCoordinator | HA pattern for centralized data management |
| Entity | Object exposed in Home Assistant (sensor, calendar, etc.) |
| Platform | Entity type (sensor, calendar, light, etc.) |
| Entry | Integration configuration instance |
| Coordinator | Object that manages data retrieval and updates |