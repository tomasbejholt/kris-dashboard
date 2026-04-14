import feedparser
from datetime import datetime


KRISINFORMATION_RSS_URL = "https://www.krisinformation.se/api/feed/rss"

COUNTY_NAMES = [
    "Stockholms län", "Uppsala län", "Södermanlands län", "Östergötlands län",
    "Jönköpings län", "Kronobergs län", "Kalmar län", "Gotlands län",
    "Blekinge län", "Skåne län", "Hallands län", "Västra Götalands län",
    "Värmlands län", "Örebro län", "Västmanlands län", "Dalarnas län",
    "Gävleborgs län", "Västernorrlands län", "Jämtlands län",
    "Västerbottens län", "Norrbottens län",
]


def fetch_incidents() -> list[dict]:
    """Hämtar aktuella händelser från Krisinformation.se via RSS."""
    feed = feedparser.parse(KRISINFORMATION_RSS_URL)
    incidents = []

    for entry in feed.entries:
        text = f"{entry.get('title', '')} {entry.get('summary', '')}"

        incidents.append({
            "source": "Krisinformation",
            "title": entry.get("title", "Okänd händelse"),
            "description": entry.get("summary", ""),
            "severity": "Måttlig",
            "published": _parse_time(entry.get("published_parsed")),
            "county": _extract_county(text),
            "lat": None,
            "lon": None,
        })

    return incidents


def _extract_county(text: str) -> str:
    """Söker igenom texten efter ett känt länsnamn."""
    for county in COUNTY_NAMES:
        if county.lower() in text.lower():
            return county
    return "Okänt område"


def _parse_time(time_struct) -> str:
    """Omvandlar feedparsers tidsformat till en läsbar sträng."""
    if time_struct is None:
        return ""
    try:
        return datetime(*time_struct[:6]).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""
