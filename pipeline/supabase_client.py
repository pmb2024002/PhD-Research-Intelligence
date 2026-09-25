"""
Mitochondrial Research Intelligence
Supabase client helper.

Provides a shared, lazily-initialized Supabase client for reading
and writing saved_papers and discovered_papers, so data persists
reliably on the deployed Streamlit Cloud site (whose local
filesystem is ephemeral) as well as locally.
"""

import os

try:
    import streamlit as st
except ImportError:
    st = None

from supabase import create_client


def _get_secret(name):
    """Read a secret from Streamlit secrets first, then env vars."""
    if st is not None:
        try:
            if name in st.secrets:
                return st.secrets[name]
        except Exception:
            pass
    return os.getenv(name)


_client = None


def get_client():
    """Return a shared Supabase client, creating it on first use."""

    global _client

    if _client is not None:
        return _client

    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_KEY are not configured "
            "(check .streamlit/secrets.toml or Streamlit Cloud secrets)."
        )

    _client = create_client(url, key)
    return _client


def get_saved_papers():
    """Return all saved papers as a list of dicts."""
    client = get_client()
    result = client.table("saved_papers").select("*").execute()
    return result.data or []


def get_saved_pmids():
    """Return a set of PMIDs (as strings) that are currently saved."""
    return {str(row["pmid"]) for row in get_saved_papers()}


def save_paper(paper_row: dict):
    """Save a paper (upsert by pmid) to saved_papers."""
    import datetime

    client = get_client()

    row = {
        "pmid": str(paper_row.get("pmid", "")),
        "title": paper_row.get("title", ""),
        "abstract": paper_row.get("abstract", ""),
        "authors": paper_row.get("authors", ""),
        "journal": paper_row.get("journal", ""),
        "publication_date": paper_row.get("publication_date", ""),
        "journal_issue_date": paper_row.get("journal_issue_date", ""),
        "doi": paper_row.get("doi", ""),
        "pubmed_url": paper_row.get("pubmed_url", ""),
        "saved_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }

    client.table("saved_papers").upsert(row).execute()


def unsave_paper(pmid: str):
    """Remove a paper from saved_papers by pmid."""
    client = get_client()
    client.table("saved_papers").delete().eq("pmid", str(pmid)).execute()


def get_research_story():
    """Return the latest saved research story as a dict, or None if
    none has been generated yet."""
    client = get_client()
    result = client.table("research_story").select("*").eq("id", 1).execute()
    rows = result.data or []
    return rows[0] if rows else None


def save_research_story(content: str, generated_at: str, papers_covered: int):
    """Upsert the single research-story row (id=1)."""
    client = get_client()
    row = {
        "id": 1,
        "content": content,
        "generated_at": generated_at,
        "papers_covered": papers_covered,
    }
    client.table("research_story").upsert(row).execute()
