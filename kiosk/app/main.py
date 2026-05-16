from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from .config import Settings
from .qr import qr_svg
from .session_store import SessionStore
from .trip_factory import generate_session

settings = Settings.from_env()
session_store = SessionStore()

CHAOS_COOLDOWN_SECONDS = 30

app = FastAPI(title="Itinerary in Motion — kiosk")

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
if settings.brand_dir.is_dir():
    app.mount("/brand", StaticFiles(directory=str(settings.brand_dir)), name="brand")
else:
    logger.warning("brand dir missing: {}", settings.brand_dir)

# Serve the prebuilt phone-frame's bundled assets where Vite emits them (/assets/*).
# The dist/index.html (served at /m/{traveler_id}) references /assets/index-XXX.js etc.
if (settings.frontend_dist / "assets").is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=str(settings.frontend_dist / "assets")),
        name="frontend-assets",
    )
else:
    logger.warning("frontend dist/assets missing: {}", settings.frontend_dist)


@app.get("/", response_class=HTMLResponse)
def kiosk_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "kiosk.html",
        {
            "title": "Itinerary in Motion",
            "tagline": "Your itinerary listens to the world and re-plans itself in seconds.",
        },
    )


@app.post("/api/session")
def post_session() -> list[dict[str, Any]]:
    trips = generate_session(settings)
    session_store.replace(trips)
    payload = []
    for trip in trips:
        mobile_url = f"{settings.host_url.rstrip('/')}/m/{trip.traveler_id}"
        payload.append(
            {
                "traveler_id": trip.traveler_id,
                "trip_id": trip.trip_id,
                "summary": trip.summary(),
                "mobile_url": mobile_url,
                "qr_svg": qr_svg(mobile_url),
            }
        )
    return payload


@app.get("/api/travelers/{traveler_id}")
def get_traveler(traveler_id: str) -> dict[str, Any]:
    trip = session_store.find_by_traveler(traveler_id)
    if trip is None:
        raise HTTPException(status_code=404, detail=f"traveler {traveler_id} not in current session")
    out = trip.outbound
    return {
        "traveler": {
            "user_id": trip.traveler_id,
            "name": f"Guest {trip.traveler_id[-4:]}",
        },
        "flight": {
            "flightNo": out.flight_no,
            "carrier": out.carrier_name,
            "origin": out.origin_iata,
            "destination": out.destination_iata,
            "scheduledDeparture": out.scheduled_departure,
            "scheduledArrival": out.scheduled_arrival,
            "status": out.status,
            "gate": out.gate,
        },
        "itinerary": [
            {
                "day": item.day + 1,
                "date": item.date,
                "time": f"{item.hour:02d}:00",
                "title": item.title,
                "location": item.location,
                "activityType": item.activity_type,
            }
            for item in trip.items
        ],
        "trip": {
            "trip_id": trip.trip_id,
            "destination_city": trip.destination_city,
            "destination_iata": trip.destination_iata,
            "start_date": trip.start_date,
            "end_date": trip.end_date,
        },
    }


@app.post("/api/trips/{trip_id}/chaos")
def post_chaos(trip_id: str) -> dict[str, Any]:
    trip = session_store.get(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail=f"trip {trip_id} not in current session")
    now = time.monotonic()
    last = session_store.last_chaos(trip_id)
    if last is not None and now - last < CHAOS_COOLDOWN_SECONDS:
        wait = CHAOS_COOLDOWN_SECONDS - (now - last)
        raise HTTPException(status_code=429, detail=f"cooldown active; retry in {wait:.0f}s")
    session_store.touch_chaos(trip_id, now)
    from .chaos import inject_random_delay  # local import to keep solace dep optional in tests

    payload = inject_random_delay(trip)
    return {"published": True, "topic": payload["topic"], "event_id": payload["event_id"]}


@app.get("/m/{traveler_id}", response_class=HTMLResponse)
def mobile_entry(traveler_id: str) -> HTMLResponse:
    index = settings.frontend_dist / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=503, detail="frontend bundle not built — run `npm run build` in frontend/")
    html = index.read_text(encoding="utf-8")
    bootstrap = (
        f"<script>window.__TRAVELER_ID__ = {traveler_id!r};</script>\n"
        f"<link rel=\"stylesheet\" href=\"/brand/index.css\">\n"
    )
    if "</head>" in html:
        html = html.replace("</head>", bootstrap + "</head>", 1)
    else:
        html = bootstrap + html
    return HTMLResponse(html)


@app.get("/m-assets/{path:path}")
def mobile_assets(path: str) -> Response:
    asset = settings.frontend_dist / path
    if not asset.is_file():
        raise HTTPException(status_code=404)
    return Response(asset.read_bytes(), media_type=_guess_type(asset.suffix))


def _guess_type(suffix: str) -> str:
    return {
        ".js": "application/javascript",
        ".css": "text/css",
        ".svg": "image/svg+xml",
        ".json": "application/json",
        ".png": "image/png",
        ".woff2": "font/woff2",
    }.get(suffix.lower(), "application/octet-stream")
