from pathlib import Path
import re
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PUBMED_FILE = PROJECT_ROOT / "data" / "raw" / "pubmed_articles.csv"
KB_FILE = PROJECT_ROOT / "data" / "knowledge_base" / "curated_phd_literature_kb_v1.csv"
GENE_ALIAS_FILE = PROJECT_ROOT / "config" / "gene_aliases.yaml"


def load_data():
    papers = pd.read_csv(PUBMED_FILE).fillna("")
    kb = pd.read_csv(KB_FILE).fillna("")

    with open(GENE_ALIAS_FILE, "r", encoding="utf-8") as f:
        genes = yaml.safe_load(f)["canonical_genes"]

    return papers, kb, genes


def contains_term(text, term):
    pattern = r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])"
    return bool(re.search(pattern, text, flags=re.IGNORECASE))


def find_genes(text, genes):
    found = []

    for canonical, data in genes.items():
        for alias in data["aliases"]:
            if contains_term(text, alias):
                found.append(canonical)
                break

    return sorted(set(found))


def find_processes(text, genes, found_genes):
    processes = set()

    for gene in found_genes:
        for process in genes[gene].get("processes", []):
            if contains_term(text, process):
                processes.add(process)

    return sorted(processes)


def find_senescence_terms(text):
    terms = [
        "cellular senescence",
        "replicative senescence",
        "stress-induced premature senescence",
        "therapy-induced senescence",
        "senescence",
        "senescent",
        "SASP",
        "p16",
        "CDKN2A",
        "p21",
        "CDKN1A",
        "DNA damage response",
        "DDR",
    ]

    return sorted(
        {term for term in terms if contains_term(text, term)}
    )


def find_omics_methods(text):
    terms = [
        "RNA-seq",
        "transcriptomics",
        "transcriptomic",
        "transcriptional analysis",
        "proteomics",
        "proteomic",
        "metabolomics",
        "metabolomic",
        "multi-omics",
        "single-cell",
        "DESeq2",
        "limma",
        "edgeR",
        "GSVA",
        "ssGSEA",
        "WGCNA",
        "MOFA",
    ]

    return sorted(
        {term for term in terms if contains_term(text, term)}
    )


def find_kb_matches(found_genes, found_processes, kb):
    matches = []

    for _, row in kb.iterrows():
        kb_genes = {
            x.strip().upper()
            for x in __import__("re").split(r"[;,/|]+", str(row["primary_genes"]))
            if x.strip()
        }

        kb_processes = {
            x.strip().lower()
            for x in str(row["mitochondrial_processes"]).split(";")
            if x.strip()
        }

        gene_match = bool(set(found_genes) & kb_genes)
        process_match = bool(
            {x.lower() for x in found_processes} & kb_processes
        )

        if gene_match or process_match:
            matches.append({
                "ref_id": row["ref_id"],
                "knowledge_role": row["knowledge_role"],
                "gene_match": gene_match,
                "process_match": process_match,
            })

    return matches


def analyze_paper(row, kb, genes):
    text = f"{row['title']} {row['abstract']}"

    found_genes = find_genes(text, genes)
    found_processes = find_processes(text, genes, found_genes)
    senescence_terms = find_senescence_terms(text)
    omics_methods = find_omics_methods(text)

    kb_matches = find_kb_matches(
        found_genes,
        found_processes,
        kb,
    )

    return {
        "pmid": row["pmid"],
        "title": row["title"],
        "canonical_genes": "; ".join(found_genes),
        "mitochondrial_processes": "; ".join(found_processes),
        "senescence_terms": "; ".join(senescence_terms),
        "omics_methods": "; ".join(omics_methods),
        "matched_kb_references": len(kb_matches),
        "matched_direct_references": sum(
            x["knowledge_role"] == "Directly relevant"
            for x in kb_matches
        ),
        "matched_mechanistic_references": sum(
            x["knowledge_role"] == "Mechanistically relevant"
            for x in kb_matches
        ),
    }


def run():
    papers, kb, genes = load_data()

    results = [
        analyze_paper(row, kb, genes)
        for _, row in papers.iterrows()
    ]

    return pd.DataFrame(results)


if __name__ == "__main__":
    df = run()

    print("Evidence Matcher Test")
    print("-" * 30)
    print("Papers analyzed:", len(df))
    print()

    print(
        df[
            [
                "pmid",
                "canonical_genes",
                "mitochondrial_processes",
                "senescence_terms",
                "omics_methods",
                "matched_kb_references",
            ]
        ].head(10).to_string(index=False)
    )
