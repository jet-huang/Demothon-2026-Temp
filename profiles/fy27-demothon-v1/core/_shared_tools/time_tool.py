from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def get_current_time(
    tz: str = "Asia/Tokyo",
    tool_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        zone = ZoneInfo(tz)
    except ZoneInfoNotFoundError:
        return {"ok": False, "error": f"unknown tz '{tz}'"}
    now = datetime.now(zone)
    return {
        "ok": True,
        "tz": tz,
        "iso": now.isoformat(timespec="seconds"),
        "date": now.date().isoformat(),
        "weekday": now.strftime("%A"),
        "epoch_ms": int(now.timestamp() * 1000),
    }
