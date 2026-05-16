from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from .config import Settings
    from .trip_factory import Trip


SCHEMA = """
CREATE TABLE IF NOT EXISTS traveler (
    user_id VARCHAR NOT NULL,
    name VARCHAR,
    home_city VARCHAR,
    PRIMARY KEY (user_id)
);
CREATE TABLE IF NOT EXISTS trip (
    user_id VARCHAR NOT NULL,
    start_offset INTEGER,
    end_offset INTEGER,
    origin_city VARCHAR,
    origin_iata VARCHAR,
    destination_city VARCHAR,
    destination_iata VARCHAR,
    start_date DATE,
    end_date DATE,
    PRIMARY KEY (user_id)
);
CREATE TABLE IF NOT EXISTS itinerary_item (
    user_id VARCHAR NOT NULL,
    day INTEGER NOT NULL,
    hour INTEGER NOT NULL,
    date DATE,
    city VARCHAR,
    title VARCHAR,
    location VARCHAR,
    activity_type VARCHAR,
    PRIMARY KEY (user_id, day, hour)
);
"""


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def write_session(settings: "Settings", trips: list["Trip"]) -> None:
    _write_itinerary_db(settings.itinerary_db, trips)
    _write_flights_json(settings.flights_json, trips)


def _write_itinerary_db(path: Path, trips: list["Trip"]) -> None:
    today = date.today()
    with _connect(path) as conn:
        conn.execute("DELETE FROM itinerary_item")
        conn.execute("DELETE FROM trip")
        conn.execute("DELETE FROM traveler")
        for trip in trips:
            start = date.fromisoformat(trip.start_date)
            end = date.fromisoformat(trip.end_date)
            conn.execute(
                "INSERT INTO traveler (user_id, name, home_city) VALUES (?, ?, ?)",
                (trip.traveler_id, f"Guest {trip.traveler_id[-4:]}", "San Francisco"),
            )
            conn.execute(
                """
                INSERT INTO trip
                (user_id, start_offset, end_offset, origin_city, origin_iata,
                 destination_city, destination_iata, start_date, end_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trip.traveler_id,
                    (start - today).days,
                    (end - today).days,
                    "San Francisco",
                    "SFO",
                    trip.destination_city,
                    trip.destination_iata,
                    trip.start_date,
                    trip.end_date,
                ),
            )
            for item in trip.items:
                conn.execute(
                    """
                    INSERT INTO itinerary_item
                    (user_id, day, hour, date, city, title, location, activity_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        trip.traveler_id,
                        item.day,
                        item.hour,
                        item.date,
                        trip.destination_city,
                        item.title,
                        item.location,
                        item.activity_type,
                    ),
                )
        conn.commit()
    logger.info("itinerary.db rewritten with {} trips", len(trips))


def _write_flights_json(path: Path, trips: list["Trip"]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flights: dict[str, dict] = {}
    for trip in trips:
        for leg in (trip.outbound, trip.inbound):
            flights[leg.flight_no] = {
                "carrier": leg.carrier_name,
                "origin": leg.origin_iata,
                "destination": leg.destination_iata,
                "scheduled_departure": leg.scheduled_departure,
                "scheduled_arrival": leg.scheduled_arrival,
                "status": leg.status,
                "gate": leg.gate,
                "aircraft": leg.aircraft,
            }
    path.write_text(json.dumps(flights, indent=2), encoding="utf-8")
    logger.info("flights.json rewritten with {} legs", len(flights))
