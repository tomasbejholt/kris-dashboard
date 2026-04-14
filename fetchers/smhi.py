import requests
from datetime import datetime


SMHI_WARNINGS_URL = "https://opendata-download-warnings.smhi.se/api/version/2/warnings.json"

SEVERITY_MAP = {
    0: "Ingen",
    1: "Låg",
    2: "Måttlig",
    3: "Hög",
}


def fetch_warnings() -> list[dict]:
    """Hämtar aktiva vädervarningar från SMHIs öppna API."""
    response = requests.get(SMHI_WARNINGS_URL, timeout=10)
    response.raise_for_status()

    data = response.json()
    incidents = []

    for warning in data.get("warnings", []):
        for area in warning.get("warningAreas", []):
            incidents.append({
                "source": "SMHI",
                "title": warning.get("event", {}).get("sv", "Okänd händelse"),
                "description": area.get("description", {}).get("sv", ""),
                "severity": SEVERITY_MAP.get(warning.get("warningLevel", 0), "Okänd"),
                "published": _parse_time(warning.get("published")),
                "county": area.get("areaName", {}).get("sv", "Okänt område"),
                "lat": area.get("approximatedWgs84", {}).get("y"),
                "lon": area.get("approximatedWgs84", {}).get("x"),
            })

    return incidents


def _parse_time(timestamp_ms) -> str:
    """Omvandlar en Unix-tidsstämpel i millisekunder till en läsbar sträng."""
    if timestamp_ms is None:
        return ""
    return datetime.utcfromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d %H:%M")
