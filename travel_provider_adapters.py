"""Small pure functions for provider-neutral TRAVESÍA weather and travel hand-offs.

This module deliberately has no Flask dependency so its contracts can be tested offline.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote, urlparse
import re
from typing import Any


def flight_search_alternatives(origin: str, destination: str, departure: str, return_date: str, adults: int) -> list[dict[str, str]]:
    """Build current external search hand-offs, not synthetic fares or booking results."""
    route = f"Flights from {origin} to {destination} on {departure}"
    if return_date:
        route += f" returning {return_date}"
    route += f" for {adults} adult traveller(s)"
    google = "https://www.google.com/travel/flights?q=" + quote(route, safe="")
    kayak_url = f"https://www.kayak.co.in/flights/{origin}-{destination}/{departure}"
    if return_date:
        kayak_url += f"/{return_date}"
    kayak_url += "?sort=bestflight_a"
    return [
        {"provider": "Google Flights", "url": google, "mode": "external_live_search", "note": "Route/date search page; prices, seat inventory and terms are provider-controlled."},
        {"provider": "KAYAK", "url": kayak_url, "mode": "external_live_search", "note": "Live metasearch hand-off; confirm final availability and price on the provider page."},
        {"provider": "ixigo Flights", "url": "https://www.ixigo.com/flights", "mode": "external_live_search", "note": "Live flight search and seller checkout; enter the same route and dates on ixigo."},
    ]


def _symbol(data: dict[str, Any]) -> str | None:
    for span in ("next_1_hours", "next_6_hours", "next_12_hours"):
        block = data.get(span)
        if isinstance(block, dict):
            summary = block.get("summary")
            if isinstance(summary, dict) and summary.get("symbol_code"):
                return str(summary["symbol_code"])
    return None


def normalise_metno_forecast(
    payload: dict[str, Any], *, latitude: float, longitude: float, forecast_days: int, retrieved_at: str
) -> dict[str, Any]:
    """Map MET Norway Locationforecast compact GeoJSON into City's provider-neutral contract.

    MET Norway does not return a precipitation probability or apparent temperature in this
    endpoint. Those values intentionally remain unavailable rather than being guessed.
    """
    properties = payload.get("properties") if isinstance(payload, dict) else None
    series = properties.get("timeseries") if isinstance(properties, dict) else None
    if not isinstance(series, list) or not series:
        raise ValueError("MET Norway response contains no forecast time series")

    current = None
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in series:
        if not isinstance(row, dict) or not isinstance(row.get("time"), str):
            continue
        data = row.get("data") if isinstance(row.get("data"), dict) else {}
        instant = data.get("instant") if isinstance(data.get("instant"), dict) else {}
        details = instant.get("details") if isinstance(instant.get("details"), dict) else {}
        stamp = str(row["time"])
        # ISO timestamp normally ends in Z or includes an offset; parse robustly.
        try:
            parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError:
            continue
        day = parsed.date().isoformat()
        next_symbol = _symbol(data)
        next_one = data.get("next_1_hours") if isinstance(data.get("next_1_hours"), dict) else {}
        next_one_details = next_one.get("details") if isinstance(next_one.get("details"), dict) else {}
        record = {
            "time": stamp,
            "temperature": details.get("air_temperature"),
            "relative_humidity": details.get("relative_humidity"),
            "wind_speed": details.get("wind_speed"),
            "symbol": next_symbol,
            "precipitation": next_one_details.get("precipitation_amount"),
        }
        groups[day].append(record)
        if current is None:
            current = record

    if current is None:
        raise ValueError("MET Norway response contains no usable forecast rows")

    daily_rows: list[tuple[str, list[dict[str, Any]]]] = sorted(groups.items())[:forecast_days]
    dates: list[str] = []
    highs: list[float | None] = []
    lows: list[float | None] = []
    precip_amounts: list[float | None] = []
    symbols: list[str | None] = []
    for day, rows in daily_rows:
        dates.append(day)
        temps = [float(row["temperature"]) for row in rows if isinstance(row.get("temperature"), (int, float))]
        precip = [float(row["precipitation"]) for row in rows if isinstance(row.get("precipitation"), (int, float))]
        highs.append(round(max(temps), 1) if temps else None)
        lows.append(round(min(temps), 1) if temps else None)
        precip_amounts.append(round(sum(precip), 1) if precip else None)
        symbols.append(next((row.get("symbol") for row in rows if row.get("symbol")), None))

    temp = current.get("temperature")
    humidity = current.get("relative_humidity")
    wind = current.get("wind_speed")
    return {
        "source": "MET Norway Locationforecast/2.0",
        "source_url": "https://api.met.no/weatherapi/locationforecast/2.0/documentation",
        "data_mode": "live_provider_response",
        "retrieved_at": retrieved_at,
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "timezone": "UTC timestamps from MET Norway forecast response",
        "current": {
            "time": current["time"], "temperature_2m": temp,
            "apparent_temperature": None, "relative_humidity_2m": humidity,
            "wind_speed_10m": wind, "precipitation": current.get("precipitation"),
            "weather_code": None, "weather_description": (current.get("symbol") or "Forecast symbol unavailable").replace("_", " "),
        },
        "units": {"temperature_2m": "°C", "apparent_temperature": "°C", "relative_humidity_2m": "%", "wind_speed_10m": "m/s", "precipitation": "mm"},
        "daily": {"time": dates, "temperature_2m_max": highs, "temperature_2m_min": lows,
                  "precipitation_probability_max": [None for _ in dates], "precipitation_sum": precip_amounts,
                  "weather_code": [None for _ in dates], "weather_description": [s.replace("_", " ") if s else "Symbol unavailable" for s in symbols]},
        "daily_units": {"temperature_2m_max": "°C", "temperature_2m_min": "°C", "precipitation_sum": "mm"},
        "forecast_days": forecast_days, "stale": False,
        "attribution": "Weather forecasts by MET Norway, licensed under CC BY 4.0. Source and time are shown; this is not an official emergency alert.",
        "disclaimer": "Forecast model output, not a local instrument reading, official emergency warning or safety assessment. MET Norway data are made available under CC BY 4.0; provider service terms and a truthful identifying User-Agent with contact information apply.",
    }


def validate_weather_contact(email: str = "", contact_url: str = "") -> str:
    """Return a safe, truthful MET Norway contact identifier or an empty string.

    A syntactically valid email is preferred. Otherwise accept a public HTTPS URL, without
    credentials or control characters, suitable for the provider's identifying User-Agent.
    """
    email = str(email or "").strip()
    if len(email) <= 254 and re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return email
    contact_url = str(contact_url or "").strip()
    if not contact_url or len(contact_url) > 2048 or any(ch.isspace() for ch in contact_url):
        return ""
    try:
        parsed = urlparse(contact_url)
        if (parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password
                and not any(ch.isspace() for ch in parsed.netloc)):
            return contact_url
    except ValueError:
        pass
    return ""


def provider_cache_until_epoch(expires_header: str | None, now_epoch: float, fallback_seconds: int = 900) -> float:
    """Respect an HTTP Expires header when valid; otherwise use a conservative local backoff."""
    header = str(expires_header or "").strip()
    if header:
        try:
            expires = parsedate_to_datetime(header)
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            expires_epoch = expires.timestamp()
            if expires_epoch > now_epoch:
                return expires_epoch
            return now_epoch
        except (TypeError, ValueError, OverflowError):
            pass
    return now_epoch + max(60, min(6 * 60 * 60, int(fallback_seconds)))
