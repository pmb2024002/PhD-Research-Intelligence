"""
Mitochondrial Research Intelligence
New Paper Checker

Searches PubMed using the same query as the original collector,
compares results against the canonical 250-paper dataset, and
saves any NEW papers (not already in the dataset) to a separate
file for review.

This does NOT touch the canonical 250-paper dataset or the V1/V2
pipelines -- it's a read-only discovery step.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pubmed_collector import SEARCH_QUERY, search_pubmed, fetch_articles


BASE_DIR = Path(__file__).resolve().parents[1]

CANONICAL_FILE = (
    BASE_DIR
    / "data"
    / "production_v1"
    / "human_preference_layer_v1.csv"
)

NEW_PAPERS_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "new_papers_found.csv"
)

MAX_RESULTS = 100


def get_known_pmids():
    if not CANONICAL_FILE.exists():
        raise FileNotFoundError(f"Canonical file not found: {CANONICAL_FILE}")

    df = pd.read_csv(CANONICAL_FILE)
    return set(df["pmid"].astype(str))


def check_for_new_papers():

    print("=" * 70)
    print("Checking PubMed for new papers...")
    print("=" * 70)

    known_pmids = get_known_pmids()
    print(f"Known papers in canonical dataset: {len(known_pmids)}")

    found_pmids = search_pubmed(SEARCH_QUERY, MAX_RESULTS)
    print(f"PubMed search returned: {len(found_pmids)} papers")

    new_pmids = [
        pmid for pmid in found_pmids
        if str(pmid) not in known_pmids
    ]

    print(f"New papers (not in canonical dataset): {len(new_pmids)}")

    if not new_pmids:
        print("\nNo new papers found.")
        # Still write an empty file so the website has something to read
        pd.DataFrame(
            columns=["pmid", "title", "abstract", "authors", "journal",
                     "publication_date", "journal_issue_date", "doi", "pubmed_url"]
        ).to_csv(NEW_PAPERS_FILE, index=False)
        return pd.DataFrame()

    print("\nFetching details for new papers...")
    articles = fetch_articles(new_pmids)
    df = pd.DataFrame(articles)

    NEW_PAPERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(NEW_PAPERS_FILE, index=False)

    print(f"\nSaved {len(df)} new papers to: {NEW_PAPERS_FILE}")
    print("\nNew papers found:")
    print(df[["pmid", "publication_date", "title"]].to_string(index=False))

    return df


if __name__ == "__main__":
    check_for_new_papers()
