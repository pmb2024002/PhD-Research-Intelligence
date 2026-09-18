from pathlib import Path
import time
import requests
import pandas as pd
import xml.etree.ElementTree as ET

INPUT = Path("data/processed/references_master.csv")
OUTPUT = Path("data/processed/references_pubmed_enriched.csv")

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

session = requests.Session()
session.headers.update({
    "User-Agent": "PhD-Research-Intelligence/1.0"
})

def doi_to_pmid(doi):
    if not doi:
        return None

    params = {
        "db": "pubmed",
        "term": f"{doi}[doi]",
        "retmode": "json"
    }

    try:
        r = session.get(
            f"{BASE}/esearch.fcgi",
            params=params,
            timeout=30
        )
        r.raise_for_status()

        ids = r.json()["esearchresult"]["idlist"]
        return ids[0] if ids else None

    except Exception as e:
        print(f"DOI lookup failed: {doi} | {e}")
        return None

def get_pubmed_record(pmid):
    if not pmid:
        return {}

    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml"
    }

    try:
        r = session.get(
            f"{BASE}/efetch.fcgi",
            params=params,
            timeout=30
        )
        r.raise_for_status()

        root = ET.fromstring(r.text)
        article = root.find(".//PubmedArticle")

        if article is None:
            return {}

        title_node = article.find(".//ArticleTitle")
        title = "".join(title_node.itertext()).strip() if title_node is not None else ""

        abstract_parts = []

        for node in article.findall(".//Abstract/AbstractText"):
            text = "".join(node.itertext()).strip()
            label = node.attrib.get("Label", "")

            if label:
                text = f"{label}: {text}"

            abstract_parts.append(text)

        abstract = " ".join(abstract_parts)

        journal_node = article.find(".//Journal/Title")
        journal = "".join(journal_node.itertext()).strip() if journal_node is not None else ""

        year_node = article.find(".//PubDate/Year")
        year = year_node.text if year_node is not None else ""

        pub_types = []

        for node in article.findall(".//PublicationType"):
            text = "".join(node.itertext()).strip()
            if text:
                pub_types.append(text)

        return {
            "title": title,
            "abstract": abstract,
            "journal": journal,
            "pubmed_year": year,
            "publication_types": "; ".join(pub_types)
        }

    except Exception as e:
        print(f"PMID retrieval failed: {pmid} | {e}")
        return {}
df = pd.read_csv(INPUT)
results = []

print(f"Starting enrichment of {len(df)} references...")

for i, row in df.iterrows():
    doi = str(row["doi"]).strip() if pd.notna(row["doi"]) else ""

    print(f"[{i + 1}/{len(df)}] Reference {int(row['reference_no'])}")

    pmid = doi_to_pmid(doi)
    record = get_pubmed_record(pmid)

    results.append({
        "reference_no": row["reference_no"],
        "doi": doi if doi else None,
        "pmid": pmid,
        "title": record.get("title", ""),
        "abstract": record.get("abstract", ""),
        "journal": record.get("journal", ""),
        "pubmed_year": record.get("pubmed_year", ""),
        "publication_types": record.get("publication_types", "")
    })

    time.sleep(0.35)

out = pd.DataFrame(results)

out.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)

print()
print("========================================")
print("PUBMED ENRICHMENT COMPLETE")
print("========================================")
print("Input references:", len(df))
print("Output records:", len(out))
print("PMIDs found:", out["pmid"].notna().sum())
print(
    "Abstracts found:",
    (out["abstract"].fillna("").str.strip() != "").sum()
)
print("Saved:", OUTPUT)
