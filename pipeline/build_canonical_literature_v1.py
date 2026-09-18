import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

RAW_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "pubmed_articles.csv"
)

PRIORITY_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "pubmed_phd_priority_features_v1.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "canonical_literature.csv"
)


def check_unique_pmid(df, name):
    if "pmid" not in df.columns:
        raise ValueError(f"{name}: PMID column missing.")

    if df["pmid"].isna().any():
        raise ValueError(f"{name}: missing PMID detected.")

    duplicates = df["pmid"].duplicated().sum()

    if duplicates:
        raise ValueError(
            f"{name}: {duplicates} duplicate PMID rows detected."
        )


def main():

    print("=" * 80)
    print("BUILDING CANONICAL LITERATURE TABLE V1")
    print("=" * 80)

    # ------------------------------------------------------------------
    # Load authoritative source tables
    # ------------------------------------------------------------------

    raw = pd.read_csv(RAW_FILE)
    priority = pd.read_csv(PRIORITY_FILE)

    print("\nInput sizes:")
    print(f"Raw PubMed:       {len(raw)}")
    print(f"Priority features: {len(priority)}")

    # ------------------------------------------------------------------
    # Identity checks
    # ------------------------------------------------------------------

    check_unique_pmid(raw, "Raw PubMed")
    check_unique_pmid(priority, "Priority features")

    raw_pmids = set(raw["pmid"].astype(str))
    priority_pmids = set(priority["pmid"].astype(str))

    missing_from_priority = raw_pmids - priority_pmids
    extra_in_priority = priority_pmids - raw_pmids

    if missing_from_priority:
        raise ValueError(
            "PMIDs missing from priority table: "
            f"{sorted(missing_from_priority)[:10]}"
        )

    if extra_in_priority:
        raise ValueError(
            "Priority table contains PMIDs absent from raw PubMed: "
            f"{sorted(extra_in_priority)[:10]}"
        )

    # ------------------------------------------------------------------
    # Raw metadata
    # ------------------------------------------------------------------

    raw_required = [
        "pmid",
        "title",
        "abstract",
        "authors",
        "journal",
        "publication_date",
        "journal_issue_date",
        "doi",
        "pubmed_url",
    ]

    missing = [
        c for c in raw_required
        if c not in raw.columns
    ]

    if missing:
        raise ValueError(
            f"Raw PubMed missing columns: {missing}"
        )

    canonical = raw[raw_required].copy()

    # ------------------------------------------------------------------
    # Priority-feature columns to retain
    # ------------------------------------------------------------------

    priority_columns = [
        "pmid",

        # Evidence
        "gene_evidence_level",
        "gene_evidence_genes",
        "mitochondrial_process_evidence_level",
        "mitochondrial_process_evidence",
        "senescence_evidence_level",
        "senescence_evidence",
        "model_evidence_level",
        "model_evidence",
        "omics_evidence_level",
        "omics_evidence",

        # Biological
        "biological_score",
        "biological_score_normalized",
        "biological_rank",

        # Semantic
        "semantic_similarity",
        "semantic_rank",
        "semantic_normalized",

        # Hybrid
        "biological_normalized",
        "hybrid_score",
        "hybrid_rank",

        # Feature layer
        "primary_gene_count",
        "primary_gene_present",
        "core_mito_process_count",
        "direct_mito_senescence",
        "preferred_model_present",
        "multiomics_present",
        "strong_biological_evidence",
        "phd_priority_feature_score",

        # Existing categorical research-priority field
        "research_priority",
    ]

    missing = [
        c for c in priority_columns
        if c not in priority.columns
    ]

    if missing:
        raise ValueError(
            f"Priority table missing columns: {missing}"
        )

    feature_table = priority[priority_columns].copy()

    # ------------------------------------------------------------------
    # Merge
    # ------------------------------------------------------------------

    canonical = canonical.merge(
        feature_table,
        on="pmid",
        how="left",
        validate="one_to_one",
    )

    # ------------------------------------------------------------------
    # Final identity checks
    # ------------------------------------------------------------------

    if len(canonical) != len(raw):
        raise ValueError(
            "Canonical row count changed unexpectedly."
        )

    if canonical["pmid"].duplicated().any():
        raise ValueError(
            "Duplicate PMID detected after merge."
        )

    # ------------------------------------------------------------------
    # Provenance
    # ------------------------------------------------------------------

    canonical["source_file"] = "pubmed_articles.csv"
    canonical["source_batch"] = "batch_001"
    canonical["pipeline_version"] = "canonical_literature_v1"

    canonical["evidence_source"] = (
        "phd_evidence_strength_v1"
    )

    canonical["biological_score_source"] = (
        "phd_biological_score_v1"
    )

    canonical["semantic_model"] = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    canonical["priority_feature_source"] = (
        "pubmed_phd_priority_features_v1"
    )

    # ------------------------------------------------------------------
    # Missingness audit
    # ------------------------------------------------------------------

    core_columns = [
        "pmid",
        "title",
        "abstract",
        "semantic_similarity",
        "gene_evidence_level",
        "mitochondrial_process_evidence_level",
        "senescence_evidence_level",
        "model_evidence_level",
        "omics_evidence_level",
        "biological_score",
        "biological_score_normalized",
        "hybrid_score",
        "phd_priority_feature_score",
    ]

    print("\nMissing values:")
    print(
        canonical[core_columns]
        .isna()
        .sum()
        .to_string()
    )

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    canonical.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    # ------------------------------------------------------------------
    # Final report
    # ------------------------------------------------------------------

    print("\nCanonical table:")
    print(f"Rows:    {len(canonical)}")
    print(f"Columns: {len(canonical.columns)}")

    print("\nPMID uniqueness:")
    print(
        "Unique PMIDs:",
        canonical["pmid"].nunique()
    )

    print("\nSaved:")
    print(OUTPUT_FILE)

    print("\nCANONICAL LITERATURE TABLE CREATED SUCCESSFULLY.")


if __name__ == "__main__":
    main()
