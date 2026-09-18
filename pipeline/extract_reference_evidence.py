from pathlib import Path
import re
import pandas as pd
import yaml

INPUT = Path("data/processed/references_pubmed_enriched.csv")
ONTOLOGY = Path("config/phd_evidence_ontology.yaml")
OUTPUT = Path("data/processed/references_evidence_142.csv")

df = pd.read_csv(INPUT)

with open(ONTOLOGY, "r", encoding="utf-8") as f:
    ontology = yaml.safe_load(f)

def normalize(text):
    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def contains_any(text, terms):
    return any(normalize(term) in text for term in terms)

def extract_evidence(row):
    text = normalize(
        str(row.get("title", "")) + " " +
        str(row.get("abstract", ""))
    )

    evidence = {}

    evidence["has_senescence"] = contains_any(
        text, ontology["senescence"]
    )

    evidence["has_mitochondrial"] = contains_any(
        text, ontology["mitochondrial"]
    )

    for process, terms in ontology["biological_processes"].items():
        evidence[f"has_{process}"] = contains_any(text, terms)

    for pathway, terms in ontology["signaling"].items():
       evidence[f"has_{pathway}"] = contains_any(text, terms)

    for gene, aliases in ontology["priority_hubs"].items():
        evidence[f"has_{gene.lower()}"] = contains_any(text, aliases)

    for omics_type, terms in ontology["omics"].items():
        evidence[f"has_{omics_type}"] = contains_any(text, terms)

    return evidence

evidence_rows = []

for _, row in df.iterrows():
    evidence_rows.append(extract_evidence(row))

evidence_df = pd.DataFrame(evidence_rows)

result = pd.concat(
    [df[["reference_no", "pmid", "title", "pubmed_year"]], evidence_df],
    axis=1
)

result.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8"
)

print("========================================")
print("REFERENCE EVIDENCE EXTRACTION COMPLETE")
print("========================================")
print("Input references:", len(df))
print("Output records:", len(result))
print("Evidence columns:", len(evidence_df.columns))
print("Saved:", OUTPUT)
