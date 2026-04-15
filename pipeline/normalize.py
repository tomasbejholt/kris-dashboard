from fetchers.smhi import fetch_warnings
from fetchers.trafikverket import fetch_disruptions
from fetchers.krisinformation import fetch_incidents
from fetchers.polisen import fetch_events
from pipeline.database import delete_old_incidents


COUNTY_COORDINATES = {
    "Stockholms län": (59.33, 18.07),
    "Uppsala län": (59.86, 17.64),
    "Södermanlands län": (59.37, 16.51),
    "Östergötlands län": (58.41, 15.62),
    "Jönköpings län": (57.78, 14.16),
    "Kronobergs län": (56.88, 14.81),
    "Kalmar län": (56.66, 16.36),
    "Gotlands län": (57.63, 18.29),
    "Blekinge län": (56.16, 15.00),
    "Skåne län": (55.99, 13.59),
    "Hallands län": (56.67, 12.86),
    "Västra Götalands län": (57.70, 11.97),
    "Värmlands län": (59.38, 13.50),
    "Örebro län": (59.27, 15.21),
    "Västmanlands län": (59.61, 16.55),
    "Dalarnas län": (60.60, 15.63),
    "Gävleborgs län": (60.67, 17.14),
    "Västernorrlands län": (62.45, 17.32),
    "Jämtlands län": (63.18, 14.64),
    "Västerbottens län": (63.82, 20.26),
    "Norrbottens län": (65.58, 22.15),
}

VALID_LAT = (55.0, 70.0)
VALID_LON = (10.0, 25.0)


def run_pipeline() -> list[dict]:
    """
    Kör alla fetchers, normaliserar datan och returnerar
    en ren lista med incidents redo att sparas i Supabase.
    """
    delete_old_incidents(days=30)
    raw = []

    for fetch_fn in [fetch_warnings, fetch_disruptions, fetch_incidents, fetch_events]:
        try:
            raw.extend(fetch_fn())
        except Exception as e:
            print(f"Fel vid hämtning från {fetch_fn.__name__}: {e}")

    return [_normalize(incident) for incident in raw]


def _normalize(incident: dict) -> dict:
    """Städar och kompletterar ett enskilt incident-objekt."""
    incident["title"] = _clean_text(incident.get("title", "Okänd händelse"))
    incident["description"] = _clean_text(incident.get("description", ""))
    incident["source"] = incident.get("source", "Okänd")
    incident["severity"] = incident.get("severity", "Låg")
    incident["published"] = incident.get("published", "")
    incident["county"] = incident.get("county", "Okänt område")

    lat = _to_float(incident.get("lat"))
    lon = _to_float(incident.get("lon"))

    if _valid_coordinates(lat, lon):
        incident["lat"] = lat
        incident["lon"] = lon
    else:
        incident["lat"], incident["lon"] = _county_fallback(incident["county"])

    return incident


def _clean_text(text) -> str:
    """Tar bort onödiga mellanslag och säkerställer att värdet är en sträng."""
    return str(text).strip() if text else ""


def _to_float(value) -> float | None:
    """Försöker omvandla ett värde till ett flyttal."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _valid_coordinates(lat, lon) -> bool:
    """Kontrollerar att koordinaterna ligger inom Sverige."""
    if lat is None or lon is None:
        return False
    return VALID_LAT[0] <= lat <= VALID_LAT[1] and VALID_LON[0] <= lon <= VALID_LON[1]


def _county_fallback(county: str):
    """Returnerar länets centralkoordinater om exakta koordinater saknas."""
    return COUNTY_COORDINATES.get(county, (None, None))
