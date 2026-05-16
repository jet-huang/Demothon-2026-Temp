from __future__ import annotations

import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterator

from loguru import logger
from solace.messaging.config.solace_properties.authentication_properties import (
    SCHEME_BASIC_PASSWORD,
    SCHEME_BASIC_USER_NAME,
)
from solace.messaging.config.solace_properties.service_properties import VPN_NAME
from solace.messaging.config.solace_properties.transport_layer_properties import (
    HOST,
    RECONNECTION_ATTEMPTS,
    RECONNECTION_ATTEMPTS_WAIT_INTERVAL,
)
from solace.messaging.messaging_service import MessagingService
from solace.messaging.publisher.direct_message_publisher import DirectMessagePublisher
from solace.messaging.resources.topic import Topic
from ulid import ULID

TOPIC_ROOT = "D/changes/flight"
EVENT_TYPES = ("delay", "cancel", "gate-change", "status")
REASON_CODE_MAP = {
    "weather": "WX",
    "atc": "ATC",
    "maintenance": "MX",
    "crew": "CREW",
    "operations": "OPS",
    "ops": "OPS",
}
STATUS_TO_EVENT_TYPE = {
    "DELAYED": "delay",
    "CANCELLED": "cancel",
    "GATE_CHANGE": "gate-change",
    "ON_TIME": "status",
}


@dataclass
class FlightChange:
    traveler_id: str
    flight_no: str
    carrier: str
    origin_iata: str
    destination_iata: str
    previous_status: str = "ON_TIME"
    new_status: str = "DELAYED"
    event_type: str | None = None
    delay_minutes: int = 180
    new_gate: str | None = None
    reason: str = "weather"
    reason_code: str | None = None
    scheduled_departure: str | None = None
    scheduled_arrival: str | None = None
    flight_duration_minutes: int = 210
    source: str = "chaos-maker"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def shift_iso(base_iso: str, minutes: int) -> str:
    return (datetime.fromisoformat(base_iso) + timedelta(minutes=minutes)).isoformat(timespec="seconds")


def resolve_event_type(fc: FlightChange) -> str:
    et = fc.event_type or STATUS_TO_EVENT_TYPE.get(fc.new_status.upper(), "status")
    if et not in EVENT_TYPES:
        raise ValueError(f"event_type '{et}' not in {EVENT_TYPES}")
    return et


def build_payload(fc: FlightChange) -> dict:
    event_type = resolve_event_type(fc)
    flight_no = fc.flight_no.upper()
    carrier = (fc.carrier or flight_no[:2]).upper()
    new_status = fc.new_status.upper()
    scheduled_departure = fc.scheduled_departure or now_iso()
    scheduled_arrival = fc.scheduled_arrival or shift_iso(scheduled_departure, fc.flight_duration_minutes)

    change: dict[str, object] = {
        "previous_status": fc.previous_status.upper(),
        "new_status": new_status,
        "reason": fc.reason,
        "reason_code": REASON_CODE_MAP.get(fc.reason.lower(), fc.reason_code or "OPS"),
        "delay_minutes": None,
        "new_estimated_departure": None,
        "new_estimated_arrival": None,
        "new_gate": None,
    }

    if event_type == "delay":
        change["delay_minutes"] = fc.delay_minutes
        change["new_estimated_departure"] = shift_iso(scheduled_departure, fc.delay_minutes)
        change["new_estimated_arrival"] = shift_iso(scheduled_arrival, fc.delay_minutes)
    elif event_type == "gate-change":
        change["new_gate"] = fc.new_gate or "B12"

    return {
        "event_id": f"evt_{ULID()}",
        "event_type": event_type,
        "issued_at": now_iso(),
        "source": fc.source,
        "traveler_id": fc.traveler_id,
        "flight": {
            "flight_no": flight_no,
            "carrier": carrier,
            "origin_iata": fc.origin_iata.upper(),
            "destination_iata": fc.destination_iata.upper(),
            "scheduled_departure": scheduled_departure,
            "scheduled_arrival": scheduled_arrival,
        },
        "change": change,
    }


def topic_for(payload: dict) -> str:
    flight = payload["flight"]
    return f"{TOPIC_ROOT}/{flight['carrier']}/{flight['flight_no']}/{payload['event_type']}"


def broker_props() -> dict[str, str]:
    return {
        HOST: os.environ.get("BROKER_URL", "tcp://192.168.88.188:55555"),
        VPN_NAME: os.environ.get("BROKER_VPN", "ai168"),
        SCHEME_BASIC_USER_NAME: os.environ.get("BROKER_USERNAME", "user01"),
        SCHEME_BASIC_PASSWORD: os.environ.get("BROKER_PASSWORD", "password"),
        RECONNECTION_ATTEMPTS: "3",
        RECONNECTION_ATTEMPTS_WAIT_INTERVAL: "3000",
    }


@contextmanager
def broker_publisher() -> Iterator[DirectMessagePublisher]:
    service = MessagingService.builder().from_properties(broker_props()).build()
    service.connect()
    publisher = service.create_direct_message_publisher_builder().build()
    publisher.start()
    logger.info("connected to broker; ready to publish")
    try:
        yield publisher
    finally:
        publisher.terminate()
        service.disconnect()


def publish(publisher: DirectMessagePublisher, topic: str, payload: dict) -> None:
    body = json.dumps(payload, separators=(",", ":"))
    # Send raw bytes (not str). When `message` is str the Python SDK wraps it
    # in an SDT String, which adds a type-marker byte at the head of the
    # binary attachment. Browser consumers reading getBinaryAttachment() then
    # see the framing byte and JSON.parse fails on the leading non-JSON char.
    publisher.publish(destination=Topic.of(topic), message=bytearray(body, "utf-8"))
    logger.info("PUB {} -> {}", topic, body)


def publish_flight_change(fc: FlightChange) -> dict:
    payload = build_payload(fc)
    topic = topic_for(payload)
    with broker_publisher() as pub:
        publish(pub, topic, payload)
    return payload
