from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    host_url: str
    itinerary_db: Path
    flights_json: Path
    frontend_dist: Path
    brand_dir: Path
    regions_json: Path

    @classmethod
    def from_env(cls) -> "Settings":
        default_db = REPO_ROOT / "profiles" / "fy27-demothon-v1" / "core" / "db" / "itinerary.db"
        default_flights = REPO_ROOT / "profiles" / "fy27-demothon-v1" / "core" / "mock" / "flights.json"
        default_dist = REPO_ROOT / "frontend" / "dist"
        default_brand = REPO_ROOT / "sponsor-specific" / "BrandedCSS"
        default_regions = Path(__file__).resolve().parent.parent / "data" / "regions.json"
        return cls(
            host_url=os.environ.get("KIOSK_HOST_URL", "http://localhost:9000"),
            itinerary_db=Path(os.environ.get("KIOSK_ITINERARY_DB", str(default_db))),
            flights_json=Path(os.environ.get("KIOSK_FLIGHTS_JSON", str(default_flights))),
            frontend_dist=Path(os.environ.get("KIOSK_FRONTEND_DIST", str(default_dist))),
            brand_dir=Path(os.environ.get("KIOSK_BRAND_DIR", str(default_brand))),
            regions_json=Path(os.environ.get("KIOSK_REGIONS_JSON", str(default_regions))),
        )
