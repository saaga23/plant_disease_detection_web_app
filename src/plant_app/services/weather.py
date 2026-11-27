"""Weather service.

The legacy app scraped weather pages, which broke silently. This service uses
the Open-Meteo public API (no API key required, free for non-commercial use,
https://open-meteo.com/) and degrades gracefully: callers receive
``None``/empty results plus a human-readable reason instead of a traceback.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_S = 10


@dataclass
class WeatherReport:
    location: str
    temperature_c: float | None
    humidity_pct: float | None
    description: str
    daily_forecast: list[dict]


def _geocode(city: str) -> dict | None:
    try:
        resp = requests.get(
            GEOCODE_URL,
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=REQUEST_TIMEOUT_S,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0] if results else None
    except requests.RequestException as exc:
        logger.warning("Geocoding failed for %s: %s", city, exc)
        return None


def get_weather(city: str) -> tuple[WeatherReport | None, str]:
    """Return (report, note). report is None when the service is unavailable."""
    city = (city or "").strip()
    if not city:
        return None, "Enter a city name to check the weather."
    geo = _geocode(city)
    if geo is None:
        return None, "Could not reach the weather service or resolve that location. Check your internet connection and try again."
    try:
        resp = requests.get(
            FORECAST_URL,
            params={
                "latitude": geo["latitude"],
                "longitude": geo["longitude"],
                "current": "temperature_2m,relative_humidity_2m,weather_code",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                "timezone": "auto",
                "forecast_days": 3,
            },
            timeout=REQUEST_TIMEOUT_S,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Forecast failed for %s: %s", city, exc)
        return None, "The weather service is unreachable right now. Please try again later."
    current = data.get("current", {})
    daily = data.get("daily", {})
    forecast = []
    dates = daily.get("time", []) or []
    codes = daily.get("weather_code", []) or []
    for i, d in enumerate(dates):
        forecast.append(
            {
                "date": d,
                "weather_code": codes[i] if i < len(codes) else None,
                "temp_max_c": daily.get("temperature_2m_max", [None] * len(dates))[i],
                "temp_min_c": daily.get("temperature_2m_min", [None] * len(dates))[i],
            }
        )
    report = WeatherReport(
        location=f'{geo.get("name")}, {geo.get("country", "")}'.strip(", "),
        temperature_c=current.get("temperature_2m"),
        humidity_pct=current.get("relative_humidity_2m"),
        description=f"WMO weather code {current.get('weather_code')}",
        daily_forecast=forecast,
    )
    note = (
        "Data: Open-Meteo (CC BY 4.0). General outlook only - "
        "not a substitute for an official agricultural weather advisory."
    )
    return report, note
