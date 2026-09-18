import pandas as pd
from pathlib import Path
import yaml


# ============================================================
# PhD Priority Feature Extraction V1
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "pubmed_new_hybrid_ranked.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "pubmed_phd_priority_features_v1.csv"
)

VOCABULARY_FILE = (
    BASE_DIR
    / "config"
    / "canonical_biological_vocabulary_v1.yaml"
)


# ============================================================
# Configuration
# ============================================================

def load_vocabulary():

    if not VOCABULARY_FILE.exists():
        raise FileNotFoundError(
            f"Canonical biological vocabulary not found: "
            f"{VOCABULARY_FILE}"
        )

    with open(
        VOCABULARY_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        vocabulary = yaml.safe_load(f)

    if not isinstance(vocabulary, dict):
        raise ValueError(
            "Canonical biological vocabulary is invalid."
        )

    required_keys = [
        "primary_hub_genes",
        "core_mitochondrial_processes",
        "preferred_models",
    ]

    missing = [
        key
        for key in required_keys
        if key not in vocabulary
    ]

    if missing:
        raise ValueError(
            "Canonical biological vocabulary missing: "
            f"{missing}"
        )

    return vocabulary


# ============================================================
# Utilities
# ============================================================

def split_terms(value):

    if pd.isna(value):
        return set()

    return {
        x.strip().lower()
        for x in str(value).split(";")
        if x.strip()
    }


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 80)
    print("PhD PRIORITY FEATURE EXTRACTION V1")
    print("=" * 80)

    # --------------------------------------------------------
    # Load vocabulary
    # --------------------------------------------------------

    print("\nLoading canonical biological vocabulary...")

    vocabulary = load_vocabulary()

    primary_genes = {
        x.strip().upper()
        for x in vocabulary["primary_hub_genes"]
    }

    core_processes = {
        x.strip().lower()
        for x in vocabulary[
            "core_mitochondrial_processes"
        ]
    }

    preferred_models = {
        x.strip().lower()
        for x in vocabulary[
            "preferred_models"
        ]
    }

    print(
        f"Primary hub genes: {len(primary_genes)}"
    )

    print(
        f"Core mitochondrial processes: "
        f"{len(core_processes)}"
    )

    print(
        f"Preferred models: {len(preferred_models)}"
    )

    # --------------------------------------------------------
    # Load hybrid-ranked literature
    # --------------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    print("\nLoading hybrid-ranked literature...")

    df = pd.read_csv(
        INPUT_FILE
    )

    print(
        f"Loaded {len(df)} papers."
    )

    # --------------------------------------------------------
    # Validate required columns
    # --------------------------------------------------------

    required_columns = [
        "pmid",
        "gene_evidence_genes",
        "mitochondrial_process_evidence",
        "mitochondrial_process_evidence_level",
        "senescence_evidence_level",
        "model_evidence",
        "omics_evidence_level",
    ]

    missing = [
        c
        for c in required_columns
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Input dataset missing columns: {missing}"
        )

    # --------------------------------------------------------
    # Priority gene feature
    # --------------------------------------------------------

    def priority_gene_count(value):

        genes = {
            x.strip().upper()
            for x in str(value).split(";")
            if x.strip()
        }

        return len(
            genes & primary_genes
        )

    df["primary_gene_count"] = (
        df["gene_evidence_genes"]
        .fillna("")
        .apply(priority_gene_count)
    )

    df["primary_gene_present"] = (
        df["primary_gene_count"] > 0
    ).astype(int)

    # --------------------------------------------------------
    # Core mitochondrial-process feature
    # --------------------------------------------------------

    def core_process_count(value):

        processes = split_terms(value)

        return len(
            processes & core_processes
        )

    df["core_mito_process_count"] = (
        df["mitochondrial_process_evidence"]
        .fillna("")
        .apply(core_process_count)
    )

    # --------------------------------------------------------
    # Direct mitochondrial-senescence connection
    # --------------------------------------------------------

    mito_level = pd.to_numeric(
        df["mitochondrial_process_evidence_level"],
        errors="coerce"
    ).fillna(0)

    senescence_level = pd.to_numeric(
        df["senescence_evidence_level"],
        errors="coerce"
    ).fillna(0)

    df["direct_mito_senescence"] = (
        (mito_level >= 2)
        &
        (senescence_level >= 2)
    ).astype(int)

    # --------------------------------------------------------
    # Preferred experimental model
    # --------------------------------------------------------

    def preferred_model(value):

        models = {
            x.strip().lower()
            for x in str(value).split(";")
            if x.strip()
        }

        return int(
            bool(
                models & preferred_models
            )
        )

    df["preferred_model_present"] = (
        df["model_evidence"]
        .fillna("")
        .apply(preferred_model)
    )

    # --------------------------------------------------------
    # Multi-omics feature
    # --------------------------------------------------------

    omics_level = pd.to_numeric(
        df["omics_evidence_level"],
        errors="coerce"
    ).fillna(0)

    df["multiomics_present"] = (
        omics_level >= 2
    ).astype(int)

    # --------------------------------------------------------
    # Strong biological evidence proxy
    # --------------------------------------------------------

    df["strong_biological_evidence"] = (
        (mito_level >= 3)
        &
        (senescence_level >= 3)
    ).astype(int)

    # --------------------------------------------------------
    # Transparent feature score
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # This score remains an intermediate feature summary.
    # It is NOT the final canonical scientific-priority score.
    # --------------------------------------------------------

    df["phd_priority_feature_score"] = (
        5 * df["direct_mito_senescence"]
        + 4 * df["primary_gene_present"]
        + 3 * df["preferred_model_present"]
        + 3 * df["multiomics_present"]
        + 2 * (
            df["core_mito_process_count"] > 0
        ).astype(int)
        + 2 * df["strong_biological_evidence"]
    )

    # --------------------------------------------------------
    # Provenance
    # --------------------------------------------------------

    df["biological_vocabulary_version"] = (
        vocabulary.get(
            "version",
            "1.0"
        )
    )

    df["biological_vocabulary_status"] = (
        vocabulary.get(
            "status",
            "canonical_candidate"
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("FEATURE SUMMARY")
    print("=" * 80)

    print(
        f"Direct mito-senescence: "
        f"{df['direct_mito_senescence'].sum()}"
    )

    print(
        f"Primary-gene papers: "
        f"{df['primary_gene_present'].sum()}"
    )

    print(
        f"Preferred-model papers: "
        f"{df['preferred_model_present'].sum()}"
    )

    print(
        f"Multi-omics papers: "
        f"{df['multiomics_present'].sum()}"
    )

    print(
        f"Strong biological evidence: "
        f"{df['strong_biological_evidence'].sum()}"
    )

    print(
        f"Primary-gene count > 0: "
        f"{(df['primary_gene_count'] > 0).sum()}"
    )

    print(
        f"Core mito-process count > 0: "
        f"{(df['core_mito_process_count'] > 0).sum()}"
    )

    print("\nVocabulary version:")
    print(
        df["biological_vocabulary_version"]
        .iloc[0]
    )

    print("\nSaved:")
    print(OUTPUT_FILE)

    print(
        "\nPhD-priority feature extraction "
        "completed successfully."
    )


if __name__ == "__main__":
    main()
