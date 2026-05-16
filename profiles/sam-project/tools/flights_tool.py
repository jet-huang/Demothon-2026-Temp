from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger

DEFAULT_FLIGHTS_PATH = Path(__file__).resolve().parent.parent / "mock" / "flights.json"


def _load_flights(path: Path) -> dict[str, Any]:
    if not path.exists():
        logger.warning("flights mock file missing: {}", path)
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def lookup_flight(flight_no: str, tool_config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = tool_config or {}
    path = Path(cfg.get("flights_path", DEFAULT_FLIGHTS_PATH))
    flights = _load_flights(path)
    record = flights.get(flight_no.upper())
    if record is None:
        return {
            "found": False,
            "flight_no": flight_no,
            "message": f"No flight record for {flight_no}.",
        }
    return {"found": True, "flight_no": flight_no.upper(), **record}
