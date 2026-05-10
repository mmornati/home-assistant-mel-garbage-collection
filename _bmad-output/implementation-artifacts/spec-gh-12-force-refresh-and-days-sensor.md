---
title: 'Implement Force Refresh Service and Next Collection Days Sensor'
type: 'feature'
created: '2026-05-10T18:34:00'
status: 'ready-for-dev'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Users must currently wait for the scheduled coordinator refresh (up to 7 days) or restart Home Assistant to get updated collection data. There is no manual refresh method and no simple integer sensor for days until the next collection, making dashboard logic complex.

**Approach:** We will register a Home Assistant service `mel_collecte.force_refresh` in the integration's setup that loops through instances and calls `async_request_refresh()` on their coordinators. We will also add a `MelCollecteNextCollectionDaysSensor` returning the integer days until the next collection. Finally, we will update `README.md` and `docs/guide_utilisateur.md` in French.

## Boundaries & Constraints

**Always:** 
- Sensor state must return an integer or `None` if no upcoming collection exists.
- Service must support optional `entry_id` filtering.
- Documentation updates must be in French.

**Ask First:** 
- Any architectural changes to the coordinator.
- Changing the unique ID of existing sensors.

**Never:** 
- Do not introduce blocking code in async contexts.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Valid refresh | Service `mel_collecte.force_refresh` called | Coordinator triggers `async_request_refresh()` | N/A |
| Future event exists | Upcoming event in 2 days | Sensor `native_value` is `2` | N/A |
| No future events | No events in data | Sensor `native_value` is `None` | N/A |

</frozen-after-approval>

## Code Map

- `custom_components/mel_collecte/__init__.py` -- Add service registration and logic.
- `custom_components/mel_collecte/sensor.py` -- Add `MelCollecteNextCollectionDaysSensor`.
- `README.md` -- Document new service and sensor.
- `docs/guide_utilisateur.md` -- Document new service and sensor.

## Tasks & Acceptance

**Execution:**
- [ ] `custom_components/mel_collecte/__init__.py` -- Add `force_refresh` service to `async_setup_entry` using `hass.services.async_register`. -- Enables manual update triggers.
- [ ] `custom_components/mel_collecte/__init__.py` -- Unregister `force_refresh` service in `async_unload_entry`. -- Clean up on integration removal.
- [ ] `custom_components/mel_collecte/sensor.py` -- Add `MelCollecteNextCollectionDaysSensor` class inheriting from `MelCollecteBaseSensor`. -- Provides integer days until next event.
- [ ] `custom_components/mel_collecte/sensor.py` -- Update `async_setup_entry` to append `MelCollecteNextCollectionDaysSensor` to `entities`. -- Registers the new sensor.
- [ ] `README.md` -- Add `sensor.jours_avant_prochaine_collecte` and the `force_refresh` service to the documentation in French. -- Keep docs up-to-date.
- [ ] `docs/guide_utilisateur.md` -- Add `sensor.jours_avant_prochaine_collecte` and the `force_refresh` service to the user guide in French. -- Keep user guide up-to-date.
- [ ] `tests/test_api.py` or similar -- Ensure tests are passing or updated if needed, run `make lint` and `make test`. -- Verify code quality.

**Acceptance Criteria:**
- Given Home Assistant running, when calling `mel_collecte.force_refresh`, then the coordinator updates immediately.
- Given an upcoming event, when reading `sensor.jours_avant_prochaine_collecte`, then the state is an integer of days.
- Given no upcoming events, when reading `sensor.jours_avant_prochaine_collecte`, then the state is `None`.

## Verification

**Commands:**
- `make lint` -- expected: Pass without errors.
- `make test` -- expected: Tests run successfully.
