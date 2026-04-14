import pandas as pd
from sklearn.ensemble import IsolationForest


SEVERITY_MAP = {"Ingen": 0, "Låg": 1, "Måttlig": 2, "Hög": 3}
SOURCE_MAP = {"SMHI": 1, "Trafikverket": 2, "Krisinformation": 3, "Polisen": 4}


def score_incidents(incidents: list[dict]) -> list[dict]:
    """
    Kör Isolation Forest på listan med incidents.
    Lägger till anomaly_score (0–1) och is_anomaly (True/False) på varje incident.
    Returnerar samma lista med de nya fälten tillagda.
    """
    if len(incidents) < 10:
        for incident in incidents:
            incident["anomaly_score"] = 0.0
            incident["is_anomaly"] = False
        return incidents

    df = pd.DataFrame(incidents)
    features = _extract_features(df)

    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(features)

    raw_scores = model.decision_function(features)
    normalized = _normalize_scores(raw_scores)

    for i, incident in enumerate(incidents):
        incident["anomaly_score"] = round(float(normalized[i]), 3)
        incident["is_anomaly"] = bool(normalized[i] > 0.7)

    return incidents


def _extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Omvandlar textfält till siffror som modellen kan jobba med."""
    features = pd.DataFrame()

    features["severity"] = df["severity"].map(SEVERITY_MAP).fillna(1)
    features["source"] = df["source"].map(SOURCE_MAP).fillna(0)
    features["hour"] = pd.to_datetime(df["published"], errors="coerce").dt.hour.fillna(12)

    return features


def _normalize_scores(scores) -> list[float]:
    """
    Isolation Forest returnerar negativa tal för anomalier.
    Vi vänder på skalan och normaliserar till 0–1
    så att högt värde = mer ovanligt.
    """
    inverted = [-s for s in scores]
    min_s = min(inverted)
    max_s = max(inverted)

    if max_s == min_s:
        return [0.0] * len(inverted)

    return [(s - min_s) / (max_s - min_s) for s in inverted]
