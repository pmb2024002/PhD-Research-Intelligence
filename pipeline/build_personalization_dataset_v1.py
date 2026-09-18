import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "phd_labeling_dataset_110_labeled.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "personalization_dataset_v1.csv"
)

FEATURES = [
    "semantic_similarity",
    "gene_evidence_level",
    "mitochondrial_process_evidence_level",
    "senescence_evidence_level",
    "model_evidence_level",
    "omics_evidence_level",
    "primary_gene_count",
    "core_mito_process_count",
]

REQUIRED = [
    "pmid",
    "title",
    "user_relevance",
] + FEATURES


def main():

    print("=" * 70)
    print("BUILDING PERSONALIZATION DATASET V1")
    print("=" * 70)

    df = pd.read_csv(INPUT_FILE)

    print(f"\nLoaded rows: {len(df)}")

    missing = [
        col for col in REQUIRED
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    # ---------------------------------------------------------
    # Remove incomplete labels
    # ---------------------------------------------------------

    df = df.dropna(
        subset=["user_relevance"]
    ).copy()

    df["user_relevance"] = (
        df["user_relevance"]
        .astype(str)
        .str.strip()
    )

    allowed = {
        "Relevant",
        "Maybe",
        "Not Relevant",
    }

    invalid = set(df["user_relevance"]) - allowed

    if invalid:
        raise ValueError(
            f"Invalid labels detected: {invalid}"
        )

    # ---------------------------------------------------------
    # Binary personalization target
    #
    # Relevant = positive
    # Maybe / Not Relevant = non-positive
    # ---------------------------------------------------------

    df["personal_relevant"] = (
        df["user_relevance"] == "Relevant"
    ).astype(int)

    # ---------------------------------------------------------
    # Preserve original human label
    # ---------------------------------------------------------

    output_columns = [
        "pmid",
        "title",
        "user_relevance",
        "personal_relevant",
    ] + FEATURES

    out = df[output_columns].copy()

    # ---------------------------------------------------------
    # Ensure numeric features
    # ---------------------------------------------------------

    for feature in FEATURES:
        out[feature] = pd.to_numeric(
            out[feature],
            errors="coerce"
        )

    # ---------------------------------------------------------
    # Final integrity checks
    # ---------------------------------------------------------

    if out["pmid"].duplicated().any():
        raise ValueError(
            "Duplicate PMID detected."
        )

    if out[FEATURES].isna().any().any():
        missing_counts = (
            out[FEATURES]
            .isna()
            .sum()
        )

        raise ValueError(
            "Missing feature values detected:\n"
            f"{missing_counts[missing_counts > 0]}"
        )

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    out.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    # ---------------------------------------------------------
    # Report
    # ---------------------------------------------------------

    print("\nFinal dataset:")
    print(f"Rows: {len(out)}")
    print(f"Features: {len(FEATURES)}")

    print("\nHuman labels:")
    print(
        out["user_relevance"]
        .value_counts()
        .to_string()
    )

    print("\nBinary personalization target:")
    print(
        out["personal_relevant"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nIncluded features:")
    for feature in FEATURES:
        print(f"  - {feature}")

    print("\nExcluded baseline/ranking variables:")
    excluded = [
        "hybrid_score",
        "final_phd_priority_score",
        "final_phd_rank",
        "final_priority_category",
        "biological_score",
        "biological_score_normalized",
        "phd_priority_feature_score",
        "research_priority",
    ]

    for feature in excluded:
        if feature in df.columns:
            print(f"  - {feature}")

    print("\nSaved:")
    print(OUTPUT_FILE)

    print("\nPersonalization dataset V1 created successfully.")


if __name__ == "__main__":
    main()
