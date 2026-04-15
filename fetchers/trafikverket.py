import requests
import streamlit as st
from datetime import datetime


TRAFIKVERKET_URL = "https://api.trafikinfo.trafikverket.se/v2/data.json"

SEVERITY_MAP = {
    "Halt": "Hög",
    "Mycket halt": "Hög",
    "Isigt": "Hög",
    "Snöigt": "Hög",
    "Blött": "Måttlig",
    "Fuktigt": "Måttlig",
    "Vattenfilm": "Måttlig",
}


def fetch_disruptions() -> list[dict]:
    """Hämtar problematiska väglagsrapporter från Trafikverkets öppna API."""
    api_key = st.secrets["trafikverket_key"]
    query = f"""<REQUEST>
        <LOGIN authenticationkey="{api_key}"/>
        <QUERY objecttype="RoadCondition" schemaversion="1" limit="100">
            <FILTER>
                <EQ name="Deleted" value="false"/>
            </FILTER>
        </QUERY>
    </REQUEST>"""

    response = requests.post(
        TRAFIKVERKET_URL,
        data=query.encode("utf-8"),
        headers={"Content-Type": "text/xml; charset=utf-8"},
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    incidents = []

    conditions = data.get("RESPONSE", {}).get("RESULT", [{}])[0].get("RoadCondition", [])

    for condition in conditions:
        condition_text = condition.get("ConditionText", "Okänt väglag")
        if condition_text == "Normalt":
            continue
        lat, lon = _parse_linestring(condition.get("Geometry", {}).get("WGS84", ""))
        extra_info = ", ".join(condition.get("ConditionInfo", []))

        incidents.append({
            "source": "Trafikverket",
            "title": f"Väglag: {condition_text} – {condition.get('RoadNumber', '')}",
            "description": f"{condition.get('LocationText', '')}. {extra_info}".strip(". "),
            "severity": SEVERITY_MAP.get(condition_text, "Måttlig"),
            "published": _parse_time(condition.get("StartTime")),
            "county": _county_name(condition.get("CountyNo", [])),
            "lat": lat,
            "lon": lon,
        })

    return incidents


def _parse_linestring(wgs84_string: str):
    """Plockar ut mittpunkten ur en WGS84 LINESTRING."""
    try:
        coords_str = wgs84_string.replace("LINESTRING (", "").replace(")", "")
        pairs = [p.strip().split() for p in coords_str.split(",")]
        mid = pairs[len(pairs) // 2]
        return float(mid[1]), float(mid[0])
    except Exception:
        return None, None


def _parse_time(time_string: str) -> str:
    """Omvandlar ISO-tidsstämpel till en läsbar sträng."""
    if not time_string:
        return ""
    try:
        dt = datetime.fromisoformat(time_string)
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
