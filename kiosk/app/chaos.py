from __future__ import annotations

import random
from typing import TYPE_CHECKING

from publisher.lib import FlightChange, build_payload, broker_publisher, publish, topic_for

if TYPE_CHECKING:
    from .trip_factory import Trip


DELAY_REASONS = [
    ("weather", "WX"),
    ("air traffic control flow", "ATC"),
    ("aircraft maintenance hold", "MX"),
    ("crew rest requirement", "CREW"),
    ("upstream operations", "OPS"),
]


def inject_random_delay(trip: "Trip") -> dict:
    rng = random.Random()
    # Demo storyline only covers the outbound leg (kiosk → destination).
    # Picking the return leg confuses the downstream agents because the
    # itinerary is anchored on the outbound arrival.
    leg = trip.outbound
    reason, code = rng.choice(DELAY_REASONS)
    minutes = rng.choice([45, 90, 120, 180, 240])

    fc = FlightChange(
        traveler_id=trip.traveler_id,
        flight_no=leg.flight_no,
        carrier=leg.carrier_code,
        origin_iata=leg.origin_iata,
        destination_iata=leg.destination_iata,
        previous_status="ON_TIME",
        new_status="DELAYED",
        event_type="delay",
        delay_minutes=minutes,
        reason=reason,
        reason_code=code,
        scheduled_departure=leg.scheduled_departure,
        scheduled_arrival=leg.scheduled_arrival,
        source="kiosk-chaos",
    )
    payload = build_payload(fc)
    topic = topic_for(payload)
    with broker_publisher() as pub:
        publish(pub, topic, payload)
    return {"topic": topic, "event_id": payload["event_id"]}
