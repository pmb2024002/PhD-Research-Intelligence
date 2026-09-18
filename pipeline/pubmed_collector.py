import requests
import pandas as pd
import xml.etree.ElementTree as ET
import time
import os

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

MAX_RESULTS_PER_QUERY = 100

OUTPUT_FILE = "data/raw/pubmed_articles.csv"

# ============================================================
# PhD Research Intelligence System
# PubMed Literature Collector
# ============================================================

SEARCH_QUERY = """
(
    "cellular senescence"[Title/Abstract]
    OR
    "cell senescence"[Title/Abstract]
)
AND
(
    "mitochondrial dysfunction"[Title/Abstract]
    OR
    "mitochondrial dynamics"[Title/Abstract]
    OR
    "mitochondrial quality control"[Title/Abstract]
    OR
    "mitochondrial homeostasis"[Title/Abstract]
    OR
    "mitophagy"[Title/Abstract]
    OR
    "mitochondrial fission"[Title/Abstract]
    OR
    "mitochondrial fusion"[Title/Abstract]
    OR
    "mitochondrial ROS"[Title/Abstract]
    OR
    "mitochondrial biogenesis"[Title/Abstract]
    OR
    DNM1L[Title/Abstract]
    OR
    DRP1[Title/Abstract]
    OR
    OPA1[Title/Abstract]
    OR
    MFN1[Title/Abstract]
    OR
    MFN2[Title/Abstract]
    OR
    PINK1[Title/Abstract]
    OR
    PRKN[Title/Abstract]
)
"""

# ============================================================
# Search PubMed
# ============================================================

def search_pubmed(query, max_results=20):

    url = EUTILS_BASE + "esearch.fcgi"

    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "pub date"
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return data["esearchresult"]["idlist"]


# ============================================================
# Fetch detailed article information
# ============================================================

def fetch_articles(pmids):

    if not pmids:
        return []

    url = EUTILS_BASE + "efetch.fcgi"

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }

    response = requests.get(
        url,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    root = ET.fromstring(response.text)

    articles = []

    for article in root.findall(".//PubmedArticle"):

        # ----------------------------------------------------
        # PMID
        # ----------------------------------------------------

        pmid_element = article.find(".//PMID")

        pmid = (
            pmid_element.text
            if pmid_element is not None
            else ""
        )

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        title_element = article.find(".//ArticleTitle")

        title = (
            "".join(title_element.itertext())
            if title_element is not None
            else ""
        )

        # ----------------------------------------------------
        # Abstract
        # ----------------------------------------------------

        abstract_parts = []

        for abstract_text in article.findall(
            ".//Abstract/AbstractText"
        ):

            text = "".join(
                abstract_text.itertext()
            )

            label = abstract_text.get("Label")

            if label:
                text = f"{label}: {text}"

            abstract_parts.append(text)

        abstract = " ".join(abstract_parts)

        # ----------------------------------------------------
        # Authors
        # ----------------------------------------------------

        authors = []

        for author in article.findall(
            ".//AuthorList/Author"
        ):

            lastname = author.findtext("LastName")
            firstname = author.findtext("ForeName")

            if lastname and firstname:
                authors.append(
                    f"{firstname} {lastname}"
                )

            elif lastname:
                authors.append(lastname)

        authors_string = ", ".join(authors)

        # ----------------------------------------------------
        # Journal
        # ----------------------------------------------------

        journal_element = article.find(
            ".//Journal/Title"
        )

        journal = (
            journal_element.text
            if journal_element is not None
            else ""
        )

        # ----------------------------------------------------
        # ----------------------------------------------------
        # Publication dates
        # ----------------------------------------------------

        publication_date = ""
        journal_issue_date = ""

        # Prefer electronic publication date when available
        electronic_date = article.find(
            ".//ArticleDate[@DateType='Electronic']"
        )

        if electronic_date is not None:

            year = electronic_date.findtext("Year")
            month = electronic_date.findtext("Month")
            day = electronic_date.findtext("Day")

            if year and month and day:
                publication_date = (
                    f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                )

            elif year and month:
                publication_date = (
                    f"{year}-{month.zfill(2)}"
                )

            elif year:
                publication_date = year

        # Keep journal issue date separately
        issue_year = article.findtext(
            ".//JournalIssue/PubDate/Year"
        )

        issue_month = article.findtext(
            ".//JournalIssue/PubDate/Month"
        )

        issue_day = article.findtext(
            ".//JournalIssue/PubDate/Day"
        )

        if issue_year:

            journal_issue_date = issue_year

            if issue_month:
                journal_issue_date += f" {issue_month}"

            if issue_day:
                journal_issue_date += f" {issue_day}"

        # ----------------------------------------------------
        # Publication dates
        # ----------------------------------------------------

        publication_date = ""
        journal_issue_date = ""

        # Prefer electronic publication date when available
        electronic_date = article.find(
            ".//ArticleDate[@DateType='Electronic']"
        )

        if electronic_date is not None:

            year = electronic_date.findtext("Year")
            month = electronic_date.findtext("Month")
            day = electronic_date.findtext("Day")

            if year and month and day:
                publication_date = (
                    f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                )

            elif year and month:
                publication_date = (
                    f"{year}-{month.zfill(2)}"
                )

            elif year:
                publication_date = year

        # Keep journal issue date separately
        issue_year = article.findtext(
            ".//JournalIssue/PubDate/Year"
        )

        issue_month = article.findtext(
            ".//JournalIssue/PubDate/Month"
        )

        issue_day = article.findtext(
            ".//JournalIssue/PubDate/Day"
        )

        if issue_year:

            journal_issue_date = issue_year

            if issue_month:
                journal_issue_date += f" {issue_month}"

            if issue_day:
                journal_issue_date += f" {issue_day}"

        # ----------------------------------------------------
        # DOI
        # ----------------------------------------------------

        doi = ""

        for article_id in article.findall(
            ".//ArticleId"
        ):

            if article_id.get("IdType") == "doi":

                doi = article_id.text or ""

                break

        # ----------------------------------------------------
        # PubMed URL
        # ----------------------------------------------------

        pubmed_url = (
            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        )

        # ----------------------------------------------------
        # Store article
        # ----------------------------------------------------

        articles.append({

            "pmid": pmid,

            "title": title,

            "abstract": abstract,

            "authors": authors_string,

            "journal": journal,

            "publication_date": publication_date,

            "journal_issue_date": journal_issue_date,

            "doi": doi,

            "pubmed_url": pubmed_url
        })

        # Small delay to be polite to NCBI servers
        time.sleep(0.1)

    return articles


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)

    print(
        "PhD Research Intelligence System"
    )

    print(
        "PubMed Literature Collector"
    )

    print("=" * 70)

    print("\nSearching PubMed...")

    pmids = search_pubmed(
        SEARCH_QUERY,
        MAX_RESULTS_PER_QUERY
    )

    print(
        f"Found {len(pmids)} papers."
    )

    print(
        "\nRetrieving detailed article information..."
    )

    articles = fetch_articles(pmids)

    df = pd.DataFrame(articles)

    # Create output directory if needed
    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"\nSaved {len(df)} papers to:"
    )

    print(
        OUTPUT_FILE
    )

    print("\nColumns collected:")

    for column in df.columns:

        print(f"  - {column}")

    print("\nLatest papers:")

    print(
        df[
            [
                "pmid",
                "publication_date",
                "title"
            ]
        ].to_string(index=False)
    )

    print("\nCollector completed successfully.")


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()
