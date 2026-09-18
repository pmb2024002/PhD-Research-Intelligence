import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

BASE_80 = DATA_DIR / "phd_labeling_dataset_80_labeled.csv"
BATCH_001 = DATA_DIR / "phd_active_labeling_pool_v1_labeled.csv"
OUTPUT = DATA_DIR / "phd_labeling_dataset_110_labeled.csv"


def main():

    print("=" * 70)
    print("BUILDING EXPANDED 110-PAPER CALIBRATION DATASET")
    print("=" * 70)

    # ---------------------------------------------------------
    # Load datasets
    # ---------------------------------------------------------

    df80 = pd.read_csv(BASE_80)
    df30 = pd.read_csv(BATCH_001)

    print(f"\nOriginal dataset: {len(df80)} papers")
    print(f"Batch 001:        {len(df30)} papers")

    # ---------------------------------------------------------
    # Integrity checks
    # ---------------------------------------------------------

    if "pmid" not in df80.columns or "pmid" not in df30.columns:
        raise ValueError("Both datasets must contain PMID.")

    if "user_relevance" not in df80.columns:
        raise ValueError("Original dataset missing user_relevance.")

    if "user_relevance" not in df30.columns:
        raise ValueError("Batch 001 missing user_relevance.")

    if df80["user_relevance"].isna().any():
        raise ValueError("Original 80-paper dataset contains missing labels.")

    if df30["user_relevance"].isna().any():
        raise ValueError("Batch 001 contains missing labels.")

    # ---------------------------------------------------------
    # PMID uniqueness within each dataset
    # ---------------------------------------------------------

    if df80["pmid"].duplicated().any():
        raise ValueError("Duplicate PMID detected in original 80-paper dataset.")

    if df30["pmid"].duplicated().any():
        raise ValueError("Duplicate PMID detected in Batch 001.")

    # ---------------------------------------------------------
    # Check overlap
    # ---------------------------------------------------------

    overlap = set(df80["pmid"]) & set(df30["pmid"])

    print(f"\nCross-dataset PMID overlap: {len(overlap)}")

    if overlap:
        print("Overlapping PMIDs:")
        print(sorted(overlap))
        raise ValueError(
            "PMID overlap detected. Refusing to create dataset."
        )

    # ---------------------------------------------------------
    # Combine
    # ---------------------------------------------------------

    df110 = pd.concat(
        [df80, df30],
        ignore_index=True,
        sort=False
    )

    # ---------------------------------------------------------
    # Final integrity checks
    # ---------------------------------------------------------

    if len(df110) != 110:
        raise ValueError(
            f"Expected 110 papers, found {len(df110)}"
        )

    if df110["pmid"].nunique() != 110:
        raise ValueError(
            "Final dataset does not contain 110 unique PMIDs."
        )

    if df110["user_relevance"].isna().any():
        raise ValueError(
            "Final dataset contains missing labels."
        )

    allowed = {
        "Relevant",
        "Maybe",
        "Not Relevant"
    }

    invalid = set(df110["user_relevance"]) - allowed

    if invalid:
        raise ValueError(
            f"Invalid labels detected: {invalid}"
        )

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    df110.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8"
    )

    # ---------------------------------------------------------
    # Report
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("110-PAPER DATASET INTEGRITY REPORT")
    print("=" * 70)

    print(f"\nTotal papers:        {len(df110)}")
    print(f"Unique PMIDs:        {df110['pmid'].nunique()}")
    print(
        f"Labeled papers:      "
        f"{df110['user_relevance'].notna().sum()}"
    )
    print(
        f"Missing labels:      "
        f"{df110['user_relevance'].isna().sum()}"
    )

    print("\nLabel distribution:")
    print(
        df110["user_relevance"]
        .value_counts()
        .to_string()
    )

    print("\nSaved:")
    print(OUTPUT)

    print("\n110-paper calibration dataset created successfully.")


if __name__ == "__main__":
    main()
