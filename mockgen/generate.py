from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SEED = Path(__file__).resolve().parent / "seeds" / "storyline.yaml"
DEFAULT_DB_DIR = REPO_ROOT / "sam-project" / "db"
DEFAULT_MOCK_DIR = REPO_ROOT / "sam-project" / "mock"


def load_seed(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_weather_db(seed: dict[str, Any], output_db: Path) -> None:
    ensure_dir(output_db)
    if output_db.exists():
        output_db.unlink()
    conn = sqlite3.connect(output_db)
    try:
        conn.executescript(
            """
            CREATE TABLE weather_forecast (
                city TEXT NOT NULL,
                forecast_date TEXT NOT NULL,
                summary TEXT NOT NULL,
                temp_high_c INTEGER NOT NULL,
                temp_low_c INTEGER NOT NULL,
                precip_probability INTEGER NOT NULL,
                notes TEXT,
                PRIMARY KEY (city, forecast_date)
            );
            """
        )
        rows = [
            (
                w["city"],
                w["date"],
                w["summary"],
                w["temp_high_c"],
                w["temp_low_c"],
                w["precip_probability"],
                w.get("notes", ""),
            )
            for w in seed.get("weather", [])
        ]
        conn.executemany(
            "INSERT INTO weather_forecast VALUES (?, ?, ?, ?, ?, ?, ?)", rows
        )
        conn.commit()
    finally:
        conn.close()
    logger.info("weather.db written: {} rows -> {}", len(rows), output_db)


def write_itinerary_db(seed: dict[str, Any], output_db: Path) -> None:
    ensure_dir(output_db)
    if output_db.exists():
        output_db.unlink()
    conn = sqlite3.connect(output_db)
    try:
        conn.executescript(
            """
            CREATE TABLE traveler (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                home_city TEXT
            );
            CREATE TABLE trip (
                user_id TEXT PRIMARY KEY,
                origin_city TEXT NOT NULL,
                origin_iata TEXT NOT NULL,
                destination_city TEXT NOT NULL,
                destination_iata TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL
            );
            CREATE TABLE itinerary_item (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                day INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                city TEXT NOT NULL,
                title TEXT NOT NULL,
                location TEXT NOT NULL,
                activity_type TEXT NOT NULL
            );
            """
        )
        traveler = seed["traveler"]
        trip = seed["trip"]
        user_id = traveler["user_id"]
        conn.execute(
            "INSERT INTO traveler VALUES (?, ?, ?)",
            (user_id, traveler["name"], traveler.get("home_city", "")),
        )
        conn.execute(
            "INSERT INTO trip VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                trip["origin_city"],
                trip["origin_iata"],
                trip["destination_city"],
                trip["destination_iata"],
                trip["start_date"],
                trip["end_date"],
            ),
        )
        items = []
        for day in seed.get("itinerary", []):
            for act in day["activities"]:
                items.append(
                    (
                        user_id,
                        day["day"],
                        day["date"],
                        act["time"],
                        day["city"],
                        act["title"],
                        act["location"],
                        act["type"],
                    )
                )
        conn.executemany(
            "INSERT INTO itinerary_item (user_id, day, date, time, city, title, location, activity_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            items,
        )
        conn.commit()
    finally:
        conn.close()
    logger.info("itinerary.db written: {} items -> {}", len(items), output_db)


def write_flights_json(seed: dict[str, Any], output_json: Path) -> None:
    ensure_dir(output_json)
    payload = {
        f["flight_no"]: {
            "carrier": f["carrier"],
            "origin": f["origin"],
            "destination": f["destination"],
            "scheduled_departure": f["scheduled_departure"],
            "scheduled_arrival": f["scheduled_arrival"],
            "status": f["status"],
            "gate": f["gate"],
            "aircraft": f["aircraft"],
        }
        for f in seed.get("flights", [])
    }
    output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    logger.info("flights.json written: {} flights -> {}", len(payload), output_json)


def main() -> None:
    parser = argparse.ArgumentParser(description="Travel demo mock data generator.")
    parser.add_argument("command", choices=["all", "weather", "itinerary", "flights"])
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--weather-db", type=Path, default=DEFAULT_DB_DIR / "weather.db")
    parser.add_argument("--itinerary-db", type=Path, default=DEFAULT_DB_DIR / "itinerary.db")
    parser.add_argument("--flights-json", type=Path, default=DEFAULT_MOCK_DIR / "flights.json")
    args = parser.parse_args()

    seed = load_seed(args.seed)
    logger.info("loaded seed from {}", args.seed)

    if args.command in ("all", "weather"):
        write_weather_db(seed, args.weather_db)
    if args.command in ("all", "itinerary"):
        write_itinerary_db(seed, args.itinerary_db)
    if args.command in ("all", "flights"):
        write_flights_json(seed, args.flights_json)


if __name__ == "__main__":
    main()
