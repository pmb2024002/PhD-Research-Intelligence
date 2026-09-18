import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "pubmed_phd_priority_features_batch_002.csv"
)

RAW_PUBMED_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "pubmed_articles_batch_002.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "phd_labeling_dataset_80.csv"
)

LABELING_N = 80


def main():

    print("Loading PhD-priority features...")

    df = pd.read_csv(INPUT_FILE)
    raw = pd.read_csv(RAW_PUBMED_FILE)

    metadata_columns = [
        "pmid",
        "abstract",
        "authors",
        "journal",
        "publication_date",
        "journal_issue_date",
        "doi",
        "pubmed_url",
    ]

    metadata_columns = [
        col for col in metadata_columns
        if col in raw.columns
    ]

    df = df.merge(
        raw[metadata_columns],
        on="pmid",
        how="left",
        suffixes=("", "_raw")
    )

    for col in metadata_columns:
        if col == "pmid":
            continue

        raw_col = f"{col}_raw"

        if raw_col in df.columns:
            if col in df.columns:
                df[col] = df[col].fillna(df[raw_col])
                df.drop(columns=[raw_col], inplace=True)
            else:
                df.rename(columns={raw_col: col}, inplace=True)

    print(f"Loaded {len(df)} papers.")

    # ---------------------------------------------------------
    # Calculate the existing baseline PhD priority score
    # ---------------------------------------------------------

    df["final_phd_priority_score"] = (
        70 * df["hybrid_score"]
        + 8 * df["direct_mito_senescence"]
        + 6 * df["primary_gene_present"]
        + 5 * df["preferred_model_present"]
        + 5 * df["multiomics_present"]
        + 6 * df["strong_biological_evidence"]
    ).clip(upper=100)

    # ---------------------------------------------------------
    # Rank papers
    # ---------------------------------------------------------

    df["final_phd_rank"] = (
        df["final_phd_priority_score"]
        .rank(ascending=False, method="min")
        .astype(int)
    )

    def classify(score):
        if score >= 75:
            return "Critical"
        elif score >= 60:
            return "High"
        elif score >= 45:
            return "Moderate"
        elif score >= 30:
            return "Low"
        else:
            return "Peripheral"

    df["final_priority_category"] = (
        df["final_phd_priority_score"].apply(classify)
    )

    # ---------------------------------------------------------
    # Select 80 papers across the complete priority distribution
    #
    # We deliberately avoid selecting only the top 80.
    # The ML model needs positive, borderline and negative
    # examples to learn the user's actual relevance boundary.
    # ---------------------------------------------------------

    df = df.sort_values(
        "final_phd_priority_score",
        ascending=False
    ).reset_index(drop=True)

    # Five approximately equal score bands.
    # Select 16 papers from each band = 80 papers.
    df["selection_band"] = pd.qcut(
        df["final_phd_priority_score"].rank(method="first"),
        q=5,
        labels=["Very High", "High", "Middle", "Low", "Very Low"]
    )

    selected_parts = []

    for band in ["Very High", "High", "Middle", "Low", "Very Low"]:

        band_df = df[df["selection_band"] == band].copy()

        n = min(16, len(band_df))

        selected = band_df.sample(
            n=n,
            random_state=42
        )

        selected_parts.append(selected)

    labeling_df = pd.concat(
        selected_parts,
        ignore_index=True
    )

    # ---------------------------------------------------------
    # If rounding/edge cases produce fewer than 80 papers,
    # fill from the remaining papers deterministically.
    # ---------------------------------------------------------

    if len(labeling_df) < LABELING_N:

        remaining = df[
            ~df["pmid"].isin(labeling_df["pmid"])
        ].copy()

        needed = LABELING_N - len(labeling_df)

        labeling_df = pd.concat(
            [
                labeling_df,
                remaining.head(needed)
            ],
            ignore_index=True
        )

    # ---------------------------------------------------------
    # Final ordering: highest baseline priority first
    # ---------------------------------------------------------

    labeling_df = labeling_df.sort_values(
        "final_phd_priority_score",
        ascending=False
    ).reset_index(drop=True)

    labeling_df["labeling_order"] = (
        range(1, len(labeling_df) + 1)
    )

    # ---------------------------------------------------------
    # Human-label columns
    # ---------------------------------------------------------

    labeling_df["user_relevance"] = ""
    labeling_df["user_reason"] = ""

    # ---------------------------------------------------------
    # Keep important fields first
    # ---------------------------------------------------------

    preferred_columns = [
        "labeling_order",
        "pmid",
        "title",
        "abstract",
        "publication_date",
        "journal",
        "doi",
        "hybrid_score",
        "final_phd_priority_score",
        "final_phd_rank",
        "final_priority_category",
        "direct_mito_senescence",
        "primary_gene_present",
        "preferred_model_present",
        "multiomics_present",
        "strong_biological_evidence",
        "user_relevance",
        "user_reason",
    ]

    existing_columns = [
        col for col in preferred_columns
        if col in labeling_df.columns
    ]

    remaining_columns = [
        col for col in labeling_df.columns
        if col not in existing_columns
        and col != "selection_band"
    ]

    labeling_df = labeling_df[
        existing_columns + remaining_columns
    ]

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    labeling_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print()
    print("80-PAPER HUMAN LABELING DATASET")
    print("=" * 50)
    print(f"Selected papers: {len(labeling_df)}")

    print()
    print("Priority distribution:")
    print(
        labeling_df["final_priority_category"]
        .value_counts()
        .to_string()
    )

    print()
    print("Score range:")
    print(
        f"{labeling_df['final_phd_priority_score'].min():.2f}"
        f" - "
        f"{labeling_df['final_phd_priority_score'].max():.2f}"
    )

    print()
    print("Saved labeling dataset to:")
    print(OUTPUT_FILE)

    print()
    print("Label columns created:")
    print("  - user_relevance")
    print("  - user_reason")

    print()
    print("Label values should be:")
    print("  Relevant")
    print("  Maybe")
    print("  Not Relevant")


if __name__ == "__main__":
    main()
