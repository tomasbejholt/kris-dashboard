import streamlit as st
from supabase import create_client, Client


def get_client() -> Client:
    """Skapar en anslutning till Supabase med credentials från Streamlit secrets."""
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    return create_client(url, key)


def save_incidents(incidents: list[dict]) -> int:
    """
    Sparar en lista med incidents till Supabase.
    Hoppar över dubletter baserat på source + title + published.
    Returnerar antal nyligen sparade incidents.
    """
    if not incidents:
        return 0

    client = get_client()
    saved = 0

    for incident in incidents:
        existing = (
            client.table("incidents")
            .select("id")
            .eq("source", incident["source"])
            .eq("title", incident["title"])
            .eq("published", incident["published"])
            .execute()
        )

        if not existing.data:
            client.table("incidents").insert(incident).execute()
            saved += 1

    return saved


def fetch_all_incidents() -> list[dict]:
    """Hämtar alla incidents från Supabase, sorterade med senaste först."""
    client = get_client()
    response = (
        client.table("incidents")
        .select("*")
        .order("published", desc=True)
        .execute()
    )
    return response.data


def fetch_recent_incidents(hours: int = 24) -> list[dict]:
    """Hämtar incidents från de senaste X timmarna."""
    from datetime import datetime, timedelta

    cutoff = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")

    client = get_client()
    response = (
        client.table("incidents")
        .select("*")
        .gte("published", cutoff)
        .order("published", desc=True)
        .execute()
    )
    return response.data
