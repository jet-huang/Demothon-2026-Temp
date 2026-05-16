from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from ulid import ULID

from .config import Settings
from .dao import write_session

ORIGIN_CITY = "San Francisco"
ORIGIN_IATA = "SFO"
TRIPS_PER_SESSION = 3


@dataclass
class Flight:
    flight_no: str
    carrier_code: str
    carrier_name: str
    origin_iata: str
    destination_iata: str
    scheduled_departure: str
    scheduled_arrival: str
    status: str = "ON_TIME"
    gate: str = "A8"
    aircraft: str = "Boeing 787-9"


@dataclass
class ItineraryItem:
    day: int
    hour: int
    date: str
    title: str
    location: str
    activity_type: str


@dataclass
class Trip:
    traveler_id: str
    trip_id: str
    destination_city: str
    destination_iata: str
    carrier_code: str
    carrier_name: str
    start_date: str
    end_date: str
    outbound: Flight
    inbound: Flight
    items: list[ItineraryItem] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        return {
            "destination_city": self.destination_city,
            "destination_iata": self.destination_iata,
            "origin_iata": ORIGIN_IATA,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "outbound_flight": self.outbound.flight_no,
            "return_flight": self.inbound.flight_no,
        }


def _load_regions(path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)["regions"]


def _iso(dt: datetime) -> str:
    return dt.astimezone().isoformat(timespec="seconds")


def _flight_no(carrier_code: str, rng: random.Random) -> str:
    return f"{carrier_code}{rng.randint(100, 999)}"


def _build_trip(region: dict[str, Any], rng: random.Random, today: date) -> Trip:
    duration = rng.randint(3, 7)
    depart_offset = rng.randint(7, 30)
    start = today + timedelta(days=depart_offset)
    end = start + timedelta(days=duration - 1)

    out_dep = datetime.combine(start, time(11, 0), tzinfo=timezone.utc) - timedelta(hours=7)
    out_arr = out_dep + timedelta(hours=11)
    ret_dep = datetime.combine(end, time(18, 0), tzinfo=timezone.utc) + timedelta(hours=9)
    ret_arr = ret_dep + timedelta(hours=10)

    outbound = Flight(
        flight_no=_flight_no(region["carrier_code"], rng),
        carrier_code=region["carrier_code"],
        carrier_name=region["carrier_name"],
        origin_iata=ORIGIN_IATA,
        destination_iata=region["iata"],
        scheduled_departure=_iso(out_dep),
        scheduled_arrival=_iso(out_arr),
        gate=f"A{rng.randint(1, 30)}",
    )
    inbound = Flight(
        flight_no=_flight_no(region["carrier_code"], rng),
        carrier_code=region["carrier_code"],
        carrier_name=region["carrier_name"],
        origin_iata=region["iata"],
        destination_iata=ORIGIN_IATA,
        scheduled_departure=_iso(ret_dep),
        scheduled_arrival=_iso(ret_arr),
        gate=f"B{rng.randint(1, 30)}",
    )

    items: list[ItineraryItem] = []
    for day_idx in range(duration):
        slots = sorted(rng.sample([9, 12, 15, 18, 21], k=rng.randint(2, 4)))
        day_date = (start + timedelta(days=day_idx)).isoformat()
        chosen = rng.sample(region["activities"], k=min(len(slots), len(region["activities"])))
        for hour, activity in zip(slots, chosen, strict=False):
            items.append(
                ItineraryItem(
                    day=day_idx,
                    hour=hour,
                    date=day_date,
                    title=activity,
                    location=region["city"],
                    activity_type="sightseeing",
                )
            )

    return Trip(
        traveler_id=str(ULID()),
        trip_id=str(ULID()),
        destination_city=region["city"],
        destination_iata=region["iata"],
        carrier_code=region["carrier_code"],
        carrier_name=region["carrier_name"],
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        outbound=outbound,
        inbound=inbound,
        items=items,
    )


def generate_session(settings: Settings) -> list[Trip]:
    rng = random.Random()
    regions = _load_regions(settings.regions_json)
    chosen = rng.sample(regions, k=min(TRIPS_PER_SESSION, len(regions)))
    today = date.today()
    trips = [_build_trip(region, rng, today) for region in chosen]
    write_session(settings, trips)
    return trips
