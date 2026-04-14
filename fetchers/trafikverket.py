import requests
from datetime import datetime


TRAFIKVERKET_URL = "https://api.trafikinfo.trafikverket.se/v2/data.json"

SEVERITY_MAP = {
    "Ingen påverkan": "Låg",
    "Liten påverkan": "Låg",
    "Stor påverkan": "Hög",
    "Mycket stor påverkan": "Hög",
}


def fetch_disruptions() -> list[dict]:
    """Hämtar aktiva trafikstörningar från Trafikverkets öppna API."""
    query = """
    <REQUEST>
        <LOGIN authenticationkey=""/>
        <QUERY objecttype="Situation" schemaversion="1.5" limit="50">
            <FILTER>
                <EQ name="Deviation.ManagedCause" value="true"/>
            </FILTER>
            <INCLUDE>Deviation.Header</INCLUDE>
            <INCLUDE>Deviation.Message</INCLUDE>
            <INCLUDE>Deviation.SeverityText</INCLUDE>
            <INCLUDE>Deviation.StartTime</INCLUDE>
            <INCLUDE>Deviation.Geometry.WGS84</INCLUDE>
            <INCLUDE>Deviation.CountyNo</INCLUDE>
        </QUERY>
    </REQUEST>
    """

    response = requests.post(
        TRAFIKVERKET_URL,
        data=query,
        headers={"Content-Type": "text/xml"},
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    incidents = []

    situations = data.get("RESPONSE", {}).get("RESULT", [{}])[0].get("Situation", [])

    for situation in situations:
        for deviation in situation.get("Deviation", []):
            geometry = deviation.get("Geometry", {}).get("WGS84", "")
            lat, lon = _parse_geometry(geometry)

            incidents.append({
                "source": "Trafikverket",
                "title": deviation.get("Header", "Okänd störning"),
                "description": deviation.get("Message", ""),
                "severity": SEVERITY_MAP.get(deviation.get("SeverityText", ""), "Måttlig"),
                "published": _parse_time(deviation.get("StartTime")),
                "county": _county_name(deviation.get("CountyNo", [])),
                "lat": lat,
                "lon": lon,
            })

    return incidents


def _parse_geometry(wgs84_string: str):
    """Plockar ut lat/lon ur Trafikverkets WGS84-sträng, t.ex. 'POINT (18.07 59.33)'."""
    try:
        coords = wgs84_string.replace("POINT (", "").replace(")", "").split()
        return float(coords[1]), float(coords[0])
    except Exception:
        return None, None


def _parse_time(time_string: str) -> str:
    """Omvandlar Trafikverkets tidsformat till en läsbar sträng."""
    if not time_string:
        return ""
    try:
        dt = datetime.fromisoformat(time_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return time_string


def _county_name(county_numbers: list) -> str:
    """Returnerar ett länsnamn baserat på länsnummer."""
    county_map = {
        1: "Stockholms län", 3: "Uppsala län", 4: "Södermanlands län",
        5: "Östergötlands län", 6: "Jönköpings län", 7: "Kronobergs län",
        8: "Kalmar län", 9: "Gotlands län", 10: "Blekinge län",
        12: "Skåne län", 13: "Hallands län", 14: "Västra Götalands län",
        17: "Värmlands län", 18: "Örebro län", 19: "Västmanlands län",
        20: "Dalarnas län", 21: "Gävleborgs län", 22: "Västernorrlands län",
        23: "Jämtlands län", 24: "Västerbottens län", 25: "Norrbottens län",
    }
    if county_numbers:
        return county_map.get(county_numbers[0], f"Län {county_numbers[0]}")
    return "Okänt län"
