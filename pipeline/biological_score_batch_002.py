import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "phd_evidence_strength_batch_002.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "phd_biological_score_batch_002.csv"
)


def main():

    print("Loading evidence-strength results...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded {len(df)} papers.")

    # ---------------------------------------------------------
    # Biological evidence weights
    #
    # The weights reflect the PhD research priority:
    # mitochondrial-senescence biology > gene presence >
    # model specificity > omics evidence.
    #
    # Evidence levels remain unchanged:
    # 0 = absent
    # 1 = weak/basic evidence
    # 2 = experimental evidence
    # 3 = strong/mechanistic evidence
    # ---------------------------------------------------------

    weights = {
        "gene_evidence_level": 4,
        "mitochondrial_process_evidence_level": 6,
        "senescence_evidence_level": 6,
        "model_evidence_level": 3,
        "omics_evidence_level": 3,
    }

    # Composite biological evidence score
    df["biological_score"] = 0.0

    for column, weight in weights.items():
        df["biological_score"] += (
            pd.to_numeric(df[column], errors="coerce")
            .fillna(0)
            * weight
        )

    # Maximum possible score:
    # 3 * (4 + 6 + 6 + 3 + 3) = 66
    max_score = 3 * sum(weights.values())

    df["biological_score_normalized"] = (
        df["biological_score"] / max_score
    )

    # Rank
    df["biological_rank"] = (
        df["biological_score"]
        .rank(
            ascending=False,
            method="min"
        )
        .astype(int)
    )

    df = df.sort_values(
        by="biological_score",
        ascending=False
    ).reset_index(drop=True)

    # Save
    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    print()
    print("Top 10 papers by biological evidence:")
    print()

    for i, row in df.head(10).iterrows():

        print(
            f"{i + 1}. "
            f"{row['biological_score']:.1f}/66 "
            f"| {row['biological_score_normalized']:.3f} "
            f"| Gene {int(row['gene_evidence_level'])} "
            f"| Mito {int(row['mitochondrial_process_evidence_level'])} "
            f"| Sen {int(row['senescence_evidence_level'])} "
            f"| Model {int(row['model_evidence_level'])} "
            f"| Omics {int(row['omics_evidence_level'])} "
            f"| {row['title']}"
        )

    print()
    print("Saved biological scores to:")
    print(OUTPUT_FILE)

    print()
    print("Biological scoring completed successfully.")


if __name__ == "__main__":
    main()
