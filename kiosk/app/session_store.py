from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .trip_factory import Trip


class SessionStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._trips: dict[str, "Trip"] = {}
        self._last_chaos: dict[str, float] = {}

    def replace(self, trips: list["Trip"]) -> None:
        with self._lock:
            self._trips = {trip.trip_id: trip for trip in trips}
            self._last_chaos = {}

    def get(self, trip_id: str) -> "Trip | None":
        with self._lock:
            return self._trips.get(trip_id)

    def find_by_traveler(self, traveler_id: str) -> "Trip | None":
        with self._lock:
            for trip in self._trips.values():
                if trip.traveler_id == traveler_id:
                    return trip
            return None

    def last_chaos(self, trip_id: str) -> float | None:
        with self._lock:
            return self._last_chaos.get(trip_id)

    def touch_chaos(self, trip_id: str, ts: float) -> None:
        with self._lock:
            self._last_chaos[trip_id] = ts
