import requests
from datetime import datetime


SMHI_WARNINGS_URL = "https://opendata-download-warnings.smhi.se/ibww/api/version/1/warning.json"

SEVERITY_MAP = {
    "MESSAGE": "Låg",
    "YELLOW": "Låg",
    "ORANGE": "Måttlig",
    "RED": "Hög",
}


def fetch_warnings() -> list[dict]:
    """Hämtar aktiva vädervarningar från SMHIs öppna API."""
    response = requests.get(SMHI_WARNINGS_URL, timeout=10)
    response.raise_for_status()

    data = response.json()
    incidents = []

    for warning in data:
        title = warning.get("event", {}).get("sv") or warning.get("event", {}).get("en", "Okänd händelse")
        for area in warning.get("warningAreas", []):
            lat, lon = _parse_polygon(area.get("area", {}).get("geometry", {}).get("coordinates", []))
            incidents.append({
                "source": "SMHI",
                "title": title,
                "description": area.get("eventDescription", {}).get("sv") or area.get("eventDescription", {}).get("en", ""),
                "severity": SEVERITY_MAP.get(area.get("warningLevel", {}).get("code", ""), "Måttlig"),
                "published": _parse_time(area.get("published")),
                "county": area.get("areaName", {}).get("sv") or area.get("areaName", {}).get("en", "Okänt område"),
                "lat": lat,
                "lon": lon,
            })

    return incidents


def _parse_polygon(coordinates: list):
    """Beräknar centroid av en polygon för att få en representativ lat/lon."""
    try:
        ring = coordinates[0]
        lons = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        return sum(lats) / len(lats), sum(lons) / len(lons)
    except Exception:
        return None, None


def _parse_time(time_string: str) -> str:
    """Omvandlar ISO-tidsstämpel till en läsbar sträng."""
    if not time_string:
        return ""
    try:
        dt = datetime.fromisoformat(time_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return time_string
