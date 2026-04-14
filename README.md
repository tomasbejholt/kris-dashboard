# National Crisis & Incident Dashboard

A real-time dashboard for monitoring crisis events, weather warnings, and traffic disruptions across Sweden. Built as a data engineering and machine learning project with direct relevance to civil defense and emergency management.

## What it does

The dashboard aggregates live data from four official Swedish sources, normalizes it into a unified format, stores it in a cloud database, and presents it through an interactive interface with a map, tables, and an AI-generated situation summary.

**Data sources**
- Swedish Police API — real-time incident reports by county
- SMHI — active weather warnings with severity levels
- Krisinformation.se (MSB) — official crisis communications
- Trafikverket — road and rail disruptions

**Features**
- Interactive map with color-coded severity markers
- Auto-generated situation summary ("lägesbild") — e.g. *"12 incidents recorded in the last 24 hours. 3 classified as severe. Most active area: Stockholms län."*
- Anomaly detection model that flags unusual patterns in incident data
- Filter by source, severity, and time window
- Cloud-backed storage with duplicate prevention

## Tech stack

| Layer | Technology |
|---|---|
| Dashboard | Streamlit |
| Data pipeline | Python (requests, feedparser) |
| Data storage | Supabase (PostgreSQL) |
| Machine learning | scikit-learn — Isolation Forest |
| Mapping | Folium |
| Data processing | pandas |

## Architecture

```
fetchers/        # Four independent data fetchers (SMHI, Police, etc.)
pipeline/        # Normalization, coordinate resolution, database layer
models/          # Anomaly detection model
dashboard/       # Streamlit app
```

The pipeline fetches, normalizes, and stores incidents on demand. Each source returns data in a different format — the normalization layer converts everything into a unified schema before storage. Incidents without coordinates are resolved to county-level positions using a coordinate lookup table.

## Machine learning

The anomaly detection component uses an **Isolation Forest** model (scikit-learn) trained in real-time on the current dataset. Each incident receives an anomaly score between 0 and 1 based on its severity, source, and time of day. Incidents scoring above 0.7 are flagged as anomalies in the dashboard.

## Relevance

This project mirrors real tools used in Swedish civil defense and emergency management. The combination of a data pipeline, cloud database, machine learning component, and operational dashboard represents a common architecture in government data systems.
