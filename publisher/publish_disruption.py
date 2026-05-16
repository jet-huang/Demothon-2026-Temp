from __future__ import annotations

import argparse
import random
import time

from loguru import logger

try:
    from .lib import (
        EVENT_TYPES,
        FlightChange,
        broker_publisher,
        build_payload,
        now_iso,
        publish,
        publish_flight_change,
        topic_for,
    )
except ImportError:
    from lib import (  # type: ignore[no-redef]
        EVENT_TYPES,
        FlightChange,
        broker_publisher,
        build_payload,
        now_iso,
        publish,
        publish_flight_change,
        topic_for,
    )


def cmd_disrupt(args: argparse.Namespace) -> None:
    fc = FlightChange(
        traveler_id=args.traveler_id,
        flight_no=args.flight,
        carrier=args.carrier or args.flight[:2],
        origin_iata=args.origin,
        destination_iata=args.destination,
        previous_status=args.previous_status,
        new_status=args.status,
        event_type=args.event_type,
        delay_minutes=args.minutes,
        new_gate=args.gate,
        reason=args.reason,
        reason_code=args.reason_code,
        scheduled_departure=args.scheduled_departure,
        scheduled_arrival=args.scheduled_arrival,
        flight_duration_minutes=args.flight_duration,
        source=args.source,
    )
    publish_flight_change(fc)


def cmd_ambient(args: argparse.Namespace) -> None:
    with broker_publisher() as pub:
        rng = random.Random(args.seed) if args.seed is not None else random.Random()
        i = 0
        try:
            while True:
                i += 1
                topic = f"travel/telemetry/heartbeat/{i}"
                payload = {
                    "seq": i,
                    "ts": now_iso(),
                    "broker_load_hint": rng.randint(1, 100),
                }
                publish(pub, topic, payload)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logger.info("ambient loop interrupted")


def main() -> None:
    parser = argparse.ArgumentParser(description="Travel demo broker publisher (Chaos Maker).")
    sub = parser.add_subparsers(dest="command", required=True)

    p_disrupt = sub.add_parser("disrupt", help="Publish a one-shot flight change event.")
    p_disrupt.add_argument("--traveler-id", required=True, help="Traveler ID owning the flight (e.g. ULID minted by the kiosk).")
    p_disrupt.add_argument("--flight", required=True, help="Flight number, e.g. JL001.")
    p_disrupt.add_argument("--carrier", default=None, help="Carrier code (default: first 2 chars of --flight).")
    p_disrupt.add_argument("--origin", default="SFO", help="Origin IATA code.")
    p_disrupt.add_argument("--destination", default="HND", help="Destination IATA code.")
    p_disrupt.add_argument(
        "--status",
        default="DELAYED",
        choices=["DELAYED", "CANCELLED", "GATE_CHANGE", "ON_TIME"],
    )
    p_disrupt.add_argument("--previous-status", default="ON_TIME")
    p_disrupt.add_argument(
        "--event-type",
        default=None,
        choices=list(EVENT_TYPES),
        help="Override the event_type (default: derived from --status).",
    )
    p_disrupt.add_argument("--minutes", type=int, default=180, help="Delay in minutes (for event_type=delay).")
    p_disrupt.add_argument("--gate", default=None, help="New gate (for event_type=gate-change).")
    p_disrupt.add_argument("--reason", default="weather", help="Free-text reason.")
    p_disrupt.add_argument("--reason-code", default=None, help="Override reason_code (default: mapped from --reason).")
    p_disrupt.add_argument("--scheduled-departure", default=None, help="ISO-8601 with offset; default: now.")
    p_disrupt.add_argument("--scheduled-arrival", default=None, help="ISO-8601 with offset; default: scheduled_departure + flight-duration.")
    p_disrupt.add_argument("--flight-duration", type=int, default=210, help="Scheduled flight duration minutes when arrival not provided.")
    p_disrupt.add_argument("--source", default="chaos-maker")
    p_disrupt.set_defaults(func=cmd_disrupt)

    p_ambient = sub.add_parser("ambient", help="Publish ambient heartbeat events.")
    p_ambient.add_argument("--interval", type=float, default=3.0, help="Seconds between events.")
    p_ambient.add_argument("--seed", type=int, default=None)
    p_ambient.set_defaults(func=cmd_ambient)

    args = parser.parse_args()
    args.func(args)


# `build_payload`/`topic_for` re-exported for any callers still importing from this module.
__all__ = ["build_payload", "topic_for", "cmd_disrupt", "main"]


if __name__ == "__main__":
    main()
