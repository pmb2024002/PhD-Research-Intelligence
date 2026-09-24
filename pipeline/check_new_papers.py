"""
Mitochondrial Research Intelligence
New Paper Checker

Searches PubMed, compares against the canonical 250-paper dataset,
and maintains an ACCUMULATING log of all discovered-but-not-yet-in-
canonical-dataset papers in Supabase (persists reliably across
Streamlit Cloud restarts, unlike local CSV files).
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pubmed_collector import SEARCH_QUERY, search_pubmed, fetch_articles
from supabase_client import get_client


BASE_DIR = Path(__file__).resolve().parents[1]

CANONICAL_FILE = (
    BASE_DIR
    / "data"
    / "production_v1"
    / "human_preference_layer_v1.csv"
)

MAX_RESULTS = 100

DISCOVERED_COLUMNS = [
    "pmid", "title", "abstract", "authors", "journal",
    "publication_date", "journal_issue_date", "doi", "pubmed_url",
]


def get_known_pmids():
    if not CANONICAL_FILE.exists():
        raise FileNotFoundError(f"Canonical file not found: {CANONICAL_FILE}")

    df = pd.read_csv(CANONICAL_FILE)
    return set(df["pmid"].astype(str))


def load_discovered():
    client = get_client()
    result = client.table("discovered_papers").select("*").execute()

    if not result.data:
        return pd.DataFrame(columns=DISCOVERED_COLUMNS)

    return pd.DataFrame(result.data)


def check_for_new_papers():

    print("=" * 70)
    print("Checking PubMed for new papers...")
    print("=" * 70)

    known_pmids = get_known_pmids()
    discovered_df = load_discovered()

    already_discovered_pmids = set()
    if len(discovered_df) > 0 and "pmid" in discovered_df.columns:
        already_discovered_pmids = set(discovered_df["pmid"].astype(str))

    print(f"Known papers in canonical dataset: {len(known_pmids)}")
    print(f"Already in discovery log: {len(already_discovered_pmids)}")

    found_pmids = search_pubmed(SEARCH_QUERY, MAX_RESULTS)
    print(f"PubMed search returned: {len(found_pmids)} papers")

    excluded = known_pmids | already_discovered_pmids

    genuinely_new_pmids = [
        pmid for pmid in found_pmids
        if str(pmid) not in excluded
    ]

    print(f"Genuinely new papers this check: {len(genuinely_new_pmids)}")

    if genuinely_new_pmids:

        print("\nFetching details for new papers...")
        new_articles = fetch_articles(genuinely_new_pmids)

        discovered_at_now = datetime.now(timezone.utc).isoformat()
        for article in new_articles:
            article["pmid"] = str(article["pmid"])
            article["discovered_at"] = discovered_at_now

        client = get_client()
        client.table("discovered_papers").upsert(new_articles).execute()

        print(f"Added {len(new_articles)} papers to discovery log.")

        new_df = pd.DataFrame(new_articles)
        discovered_df = pd.concat(
            [discovered_df, new_df],
            ignore_index=True,
        )

    else:
        print("\nNo genuinely new papers this check.")

    if len(discovered_df) > 0 and "discovered_at" in discovered_df.columns:
        discovered_df = discovered_df.sort_values(
            by="discovered_at", ascending=False, na_position="last"
        ).reset_index(drop=True)

    print(f"\nTotal papers in discovery log: {len(discovered_df)}")

    if len(discovered_df) > 0:
        print("\nAll discovered papers:")
        print(
            discovered_df[["pmid", "publication_date", "title"]]
            .to_string(index=False)
        )

    return discovered_df


if __name__ == "__main__":
    check_for_new_papers()
