import requests
from datetime import datetime


POLISEN_URL = "https://polisen.se/api/events"

SEVERITY_MAP = {
    "Trafikolycka": "Måttlig",
    "Trafikolycka, singel": "Måttlig",
    "Trafikolycka, vilt": "Låg",
    "Brand": "Hög",
    "Brand, byggnad": "Hög",
    "Explosion": "Hög",
    "Skottlossning": "Hög",
    "Mord/dråp": "Hög",
    "Rån": "Måttlig",
    "Inbrott": "Låg",
    "Misshandel": "Måttlig",
    "Räddningsinsats": "Måttlig",
    "Naturkatastrof": "Hög",
}


def fetch_events() -> list[dict]:
    """Hämtar aktuella polishändelser från Polisens öppna API."""
    response = requests.get(POLISEN_URL, timeout=10)
    response.raise_for_status()

    data = response.json()
    incidents = []

    for event in data:
        event_type = event.get("type", "")
        location = event.get("location", {})

        incidents.append({
            "source": "Polisen",
            "title": f"{event_type} – {location.get('name', '')}",
            "description": event.get("summary", ""),
            "severity": SEVERITY_MAP.get(event_type, "Låg"),
            "published": _parse_time(event.get("datetime")),
            "county": _extract_county(location.get("name", "")),
            "lat": location.get("gps", "").split(",")[0] or None,
            "lon": location.get("gps", "").split(",")[1] or None,
        })

    return incidents


def _extract_county(location_name: str) -> str:
    """Polisens API returnerar 'Ort, Län' — vi plockar ut länet."""
    if "," in location_name:
        return location_name.split(",")[-1].strip()
    return location_name


def _parse_time(time_string: str) -> str:
    """Omvandlar Polisens tidsformat till en läsbar sträng."""
    if not time_string:
        return ""
    try:
        dt = datetime.fromisoformat(time_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return time_string
