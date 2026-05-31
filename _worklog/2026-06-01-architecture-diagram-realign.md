# Architecture Diagram Realign + Team Name

Date: 2026-06-01

## Summary

Reworked the runtime architecture diagram in `docs/index.html` to reflect a corrected event flow, added the team name, and reconciled cross-document inconsistencies before commit.

## Changes

### Diagram flow (docs/index.html)

- Flight Change Signal now publishes straight into the source Solace Event Broker (removed the old NATS to MI to Broker ingress bridge).
- Added an egress recording lane as a vertical column on the left edge: Broker to Solace Queue to Micro-Integration to NATS to Itinerary Recorder.
- NATS relocated from top-center to the left lane, positioned after the Micro-Integration.
- Final sink renamed from generic NATS Subscriber to Itinerary Recorder (NATS subscriber that records customer itinerary changes).
- Egress lane edges given a distinct ink dashed style (`.edge.egress`) and ink arrowheads so they no longer share the green outbound styling used for per-traveler replies.
- Legend gains an entry for the egress recording lane (`.swatch.egress`).
- End-to-end flow steps 2 and 3 updated to match the new flow.

### Team name (docs/index.html)

- Topbar badge `Team H` added next to FY27 Demothon.
- Footer build credit `Built by Team H`.

### CSS (docs/assets/css/page.css)

- Added `.edge.egress` and `.legend .swatch.egress` styles.

### Cross-document reconciliation

- transcript.md: softened "fans the event out on two paths in parallel" to neutral "One path / Another path" wording so the spoken script does not contradict the diagram's additional recording lane.
- Confirmed runbook.html, demo-runbook.md, and event-schemas/README.md already describe publisher direct-to-broker publishing; the diagram change aligns with them.

## Notes

- The signal-direct-to-broker change resolved a prior mismatch between the diagram and the runbook/schema docs.
