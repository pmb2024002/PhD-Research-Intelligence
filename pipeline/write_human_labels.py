import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "phd_labeling_dataset_80.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "phd_labeling_dataset_80_labeled.csv"
)


# ============================================================
# Agreed human labels — 80 papers
# ============================================================

LABELS = {
    1:  "Relevant",
    2:  "Relevant",
    3:  "Relevant",
    4:  "Maybe",
    5:  "Relevant",
    6:  "Relevant",
    7:  "Maybe",
    8:  "Maybe",
    9:  "Maybe",
    10: "Maybe",
    11: "Maybe",
    12: "Maybe",
    13: "Maybe",
    14: "Maybe",
    15: "Relevant",
    16: "Relevant",
    17: "Maybe",
    18: "Maybe",
    19: "Maybe",
    20: "Maybe",
    21: "Maybe",
    22: "Maybe",
    23: "Maybe",
    24: "Maybe",
    25: "Maybe",
    26: "Maybe",
    27: "Maybe",
    28: "Maybe",
    29: "Maybe",
    30: "Maybe",
    31: "Maybe",
    32: "Maybe",
    33: "Maybe",
    34: "Maybe",
    35: "Maybe",
    36: "Maybe",
    37: "Maybe",
    38: "Maybe",
    39: "Maybe",
    40: "Maybe",
    41: "Maybe",
    42: "Maybe",
    43: "Maybe",
    44: "Maybe",
    45: "Maybe",
    46: "Maybe",
    47: "Not Relevant",
    48: "Maybe",
    49: "Relevant",
    50: "Relevant",
    51: "Maybe",
    52: "Maybe",
    53: "Maybe",
    54: "Not Relevant",
    55: "Maybe",
    56: "Relevant",
    57: "Relevant",
    58: "Relevant",
    59: "Maybe",
    60: "Maybe",
    61: "Maybe",
    62: "Relevant",
    63: "Maybe",
    64: "Maybe",
    65: "Relevant",
    66: "Maybe",
    67: "Not Relevant",
    68: "Maybe",
    69: "Relevant",
    70: "Relevant",
    71: "Maybe",
    72: "Relevant",
    73: "Maybe",
    74: "Relevant",
    75: "Maybe",
    76: "Not Relevant",
    77: "Maybe",
    78: "Relevant",
    79: "Relevant",
    80: "Relevant",
}


REASONS = {
    "Relevant":
        "Directly supports the PhD focus on mitochondrial dysfunction in cellular senescence.",
    "Maybe":
        "Contains useful mitochondrial/senescence evidence but has a broader or indirect primary focus.",
    "Not Relevant":
        "Mitochondrial dysfunction and/or senescence is secondary to the primary research question.",
}


def main():

    print("Loading 80-paper labeling dataset...")

    df = pd.read_csv(INPUT_FILE)

    if len(df) != 80:
        raise ValueError(
            f"Expected 80 papers, found {len(df)}"
        )

    if "labeling_order" not in df.columns:
        raise ValueError(
            "Missing required column: labeling_order"
        )

    # Ensure every labeling order has a human label
    missing_orders = [
        i for i in range(1, 81)
        if i not in LABELS
    ]

    if missing_orders:
        raise ValueError(
            f"Missing labels for: {missing_orders}"
        )

    # Write labels
    df["user_relevance"] = (
        df["labeling_order"]
        .map(LABELS)
    )

    df["user_reason"] = (
        df["user_relevance"]
        .map(REASONS)
    )

    # ---------------------------------------------------------
    # Integrity checks
    # ---------------------------------------------------------

    if df["user_relevance"].isna().any():
        raise ValueError(
            "Some papers still have missing labels."
        )

    allowed = {
        "Relevant",
        "Maybe",
        "Not Relevant"
    }

    invalid = set(df["user_relevance"].dropna()) - allowed

    if invalid:
        raise ValueError(
            f"Invalid labels found: {invalid}"
        )

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    print()
    print("HUMAN LABELING DATASET")
    print("=" * 60)

    print(f"Total papers: {len(df)}")
    print(
        f"Labeled papers: "
        f"{df['user_relevance'].notna().sum()}"
    )

    print()
    print("Label distribution:")
    print(
        df["user_relevance"]
        .value_counts()
        .to_string()
    )

    print()
    print("Missing labels:",
          df["user_relevance"].isna().sum())

    print("Missing reasons:",
          df["user_reason"].isna().sum())

    print()
    print("Saved labeled dataset to:")
    print(OUTPUT_FILE)

    print()
    print("Human labeling successfully written and validated.")


if __name__ == "__main__":
    main()
