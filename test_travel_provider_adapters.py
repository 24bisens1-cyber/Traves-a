from __future__ import annotations

import pytest

from services.travel_provider_adapters import flight_search_alternatives, normalise_metno_forecast, validate_weather_contact, provider_cache_until_epoch


def test_external_flight_handoffs_are_current_search_links_not_fare_results():
    links = flight_search_alternatives("NAG", "GOI", "2026-11-10", "2026-11-15", 2)
    assert [item["provider"] for item in links] == ["Google Flights", "KAYAK", "ixigo Flights"]
    assert all(item["mode"] == "external_live_search" for item in links)
    assert "google.com/travel/flights?q=" in links[0]["url"]
    assert "2026-11-10" in links[1]["url"] and "2026-11-15" in links[1]["url"]
    assert links[2]["url"] == "https://www.ixigo.com/flights"
    assert all("price" not in item for item in links)


def test_metno_normalizer_aggregates_real_provider_shape_without_inventing_precip_probability():
    fixture = {
        "properties": {
            "timeseries": [
                {
                    "time": "2026-10-25T00:00:00Z",
                    "data": {
                        "instant": {"details": {"air_temperature": 23.5, "relative_humidity": 63, "wind_speed": 2.4}},
                        "next_1_hours": {"summary": {"symbol_code": "partly_cloudy_day"}, "details": {"precipitation_amount": 0.1}},
                    },
                },
                {
                    "time": "2026-10-25T12:00:00Z",
                    "data": {
                        "instant": {"details": {"air_temperature": 29, "relative_humidity": 40, "wind_speed": 3.2}},
                        "next_1_hours": {"summary": {"symbol_code": "clearsky_day"}, "details": {"precipitation_amount": 0.2}},
                    },
                },
                {
                    "time": "2026-10-26T00:00:00Z",
                    "data": {
                        "instant": {"details": {"air_temperature": 20, "relative_humidity": 70, "wind_speed": 1.5}},
                        "next_1_hours": {"summary": {"symbol_code": "rain"}, "details": {"precipitation_amount": 1.2}},
                    },
                },
            ]
        }
    }
    body = normalise_metno_forecast(fixture, latitude=21.14, longitude=79.08, forecast_days=2, retrieved_at="2026-10-25T00:00:00Z")
    assert body["source"] == "MET Norway Locationforecast/2.0"
    assert body["current"]["temperature_2m"] == 23.5
    assert body["current"]["apparent_temperature"] is None
    assert body["daily"]["temperature_2m_max"] == [29.0, 20.0]
    assert body["daily"]["temperature_2m_min"] == [23.5, 20.0]
    assert body["daily"]["precipitation_probability_max"] == [None, None]
    assert body["daily"]["precipitation_sum"] == [0.3, 1.2]
    assert "CC BY 4.0" in body["attribution"]


def test_metno_normalizer_rejects_empty_or_malformed_forecast():
    with pytest.raises(ValueError):
        normalise_metno_forecast({}, latitude=0, longitude=0, forecast_days=3, retrieved_at="now")
    with pytest.raises(ValueError):
        normalise_metno_forecast({"properties": {"timeseries": []}}, latitude=0, longitude=0, forecast_days=3, retrieved_at="now")


def test_release_contract_has_no_key_satellite_and_transparent_provider_policy():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    app = (root / "app.py").read_text(encoding="utf-8")
    docs = (root / "docs" / "PROVIDER_SETUP.md").read_text(encoding="utf-8")
    shell = (root / "frontend" / "index.html").read_text(encoding="utf-8")
    pulse = (root / "frontend" / "pulseboard.js").read_text(encoding="utf-8")
    assert "gibs.earthdata.nasa.gov/wmts/epsg3857/best/" in app
    assert '"nasa_fallback_available":True' in app
    assert "CITYPULSEX_CONTACT_EMAIL" in app and "normalise_metno_forecast" in app
    assert "Open-Meteo's free API is non-commercial" in docs
    assert 'data-view="pulse"' in shell and "Trip Pulseboard" in pulse
    assert "no hidden scores" in pulse


def test_weather_contact_validation_requires_real_contact_shape_and_https_public_url():
    assert validate_weather_contact("ops@example.org", "") == "ops@example.org"
    assert validate_weather_contact("bad email", "https://example.org/contact") == "https://example.org/contact"
    assert validate_weather_contact("", "http://example.org/contact") == ""
    assert validate_weather_contact("", "https://user:pass@example.org/contact") == ""
    assert validate_weather_contact("", "https://example.org/contact\r\nFake-Agent: x") == ""
    assert validate_weather_contact("", "") == ""


def test_weather_cache_respects_provider_expires_header():
    from datetime import datetime, timezone, timedelta
    now = datetime(2026, 10, 25, 0, 0, tzinfo=timezone.utc).timestamp()
    future = (datetime(2026, 10, 25, 1, 30, tzinfo=timezone.utc)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    assert provider_cache_until_epoch(future, now) == datetime(2026, 10, 25, 1, 30, tzinfo=timezone.utc).timestamp()
    assert provider_cache_until_epoch("bad expires", now, 300) == now + 300
    assert provider_cache_until_epoch("", now, 10) == now + 60
