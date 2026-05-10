---
title: 'Add automation trigger events for upcoming collections (Issue 14)'
type: 'feature'
created: '2026-05-10T18:52:14Z'
status: 'done'
baseline_commit: '829e02e9ec02c6f2b6b419092f699c330da35a4c'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Users must currently use complex template-based triggers polling sensor values to trigger automations before a collection. A native event-based approach would be cleaner and more efficient.

**Approach:** Fire a custom Home Assistant event (`mel_collecte.collection_upcoming`) with configurable lead time before a collection occurs, ensuring it only fires once per collection. A new service `mel_collecte.set_collection_offset` will allow users to configure the lead time.

## Boundaries & Constraints

**Always:** 
- The event must contain `entry_id`, `address`, `collection_id`, `collection_name`, `garbage_types`, `garbage_types_friendly`, `start`, `end`, `days_until`, and `hours_until`.
- Fire the event exactly once per collection (prevent automation spam).
- Store `fired_events` state so we do not re-fire. Default offset is 24 hours.

**Ask First:** 
- Adding UI config options for the offset. The service is enough for now.

**Never:** 
- Break existing sensors or the calendar.
- Fire the event repeatedly on every coordinator update for the same collection.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Collection approaching | Coordinator updates, a collection is exactly within the configured hours offset | Event `mel_collecte.collection_upcoming` is fired. | N/A |
| Already fired event | Coordinator updates, collection still within offset but event already fired | Event is NOT fired again for the same collection. | N/A |
| Change offset service | User calls `set_collection_offset` | The internal offset value is updated. New collections will use this offset. | Handled by service schema validation |

</frozen-after-approval>

## Code Map

- `custom_components/mel_collecte/const.py` -- Define event name `EVENT_COLLECTION_UPCOMING` and default offset.
- `custom_components/mel_collecte/coordinator.py` -- Add `fired_events` tracking state, so we know what events have been fired.
- `custom_components/mel_collecte/__init__.py` -- Add listener `_async_fire_events` to the coordinator, implement logic to check collections and fire events, and register the new service.
- `custom_components/mel_collecte/services.yaml` -- Document the new service `set_collection_offset`.
- `tests/test_init.py` or similar -- Unit tests for the new event firing and service.
- `README.md` & `docs/guide_utilisateur.md` -- Update documentation in French.

## Tasks & Acceptance

**Execution:**
- [ ] `custom_components/mel_collecte/const.py` -- Add `EVENT_COLLECTION_UPCOMING = "collection_upcoming"` and `DEFAULT_COLLECTION_OFFSET = 24`.
- [ ] `custom_components/mel_collecte/coordinator.py` -- Add `self.fired_events = set()` and `self.collection_offset_hours = DEFAULT_COLLECTION_OFFSET`.
- [ ] `custom_components/mel_collecte/__init__.py` -- Register service `set_collection_offset`, register listener on coordinator, loop through `coordinator.data` (upcoming collections) and fire event if `hours_until <= collection_offset_hours` and not in `fired_events`. Add to `fired_events`.
- [ ] `custom_components/mel_collecte/services.yaml` -- Document `set_collection_offset`.
- [ ] `tests/test_events.py` -- Create new test file to verify `set_collection_offset` and event firing logic.
- [ ] `README.md` -- Document new events and automation example in French.
- [ ] `docs/guide_utilisateur.md` -- Document new events in French.

**Acceptance Criteria:**
- Given a collection is approaching, when the time to collection becomes less than or equal to the offset, then an event `mel_collecte.collection_upcoming` is fired once.
- Given the `set_collection_offset` service is called, then the internal offset state is updated and future checks respect the new offset.

## Verification

**Commands:**
- `make test` -- expected: All tests pass.
- `make lint` -- expected: Linting passes.
