import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "pubmed_phd_priority_features_batch_002.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "phd_labeling_pool_batch_002.csv"
)


def main():

    print("Loading PhD-priority features...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded {len(df)} papers.")

    # ---------------------------------------------------------
    # Final PhD-specific priority score
    #
    # Hybrid score already combines:
    #   biological evidence + semantic similarity
    #
    # This layer adds explicit PhD-specific signals.
    # ---------------------------------------------------------

    df["final_phd_priority_score"] = (
        70 * df["hybrid_score"]
        + 8 * df["direct_mito_senescence"]
        + 6 * df["primary_gene_present"]
        + 5 * df["preferred_model_present"]
        + 5 * df["multiomics_present"]
        + 6 * df["strong_biological_evidence"]
    )

    # Maximum theoretical score = 100
    df["final_phd_priority_score"] = (
        df["final_phd_priority_score"]
        .clip(upper=100)
    )

    # ---------------------------------------------------------
    # Final ranking
    # ---------------------------------------------------------

    df["final_phd_rank"] = (
        df["final_phd_priority_score"]
        .rank(
            ascending=False,
            method="min"
        )
        .astype(int)
    )

    df = df.sort_values(
        by="final_phd_priority_score",
        ascending=False
    ).reset_index(drop=True)

    # ---------------------------------------------------------
    # Priority categories
    # ---------------------------------------------------------

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
        df["final_phd_priority_score"]
        .apply(classify)
    )

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    # ---------------------------------------------------------
    # Display top 20
    # ---------------------------------------------------------

    print()
    print("TOP 20 PAPERS — FINAL PhD PRIORITY")
    print()

    for i, row in df.head(20).iterrows():

        print(
            f"{i + 1}. "
            f"{row['final_phd_priority_score']:.2f} "
            f"| {row['final_priority_category']} "
            f"| Hybrid {row['hybrid_score']:.3f} "
            f"| Direct {int(row['direct_mito_senescence'])} "
            f"| Gene {int(row['primary_gene_present'])} "
            f"| Model {int(row['preferred_model_present'])} "
            f"| Omics {int(row['multiomics_present'])} "
            f"| Strong {int(row['strong_biological_evidence'])} "
            f"| {row['title']}"
        )

    print()
    print("Priority distribution:")
    print(
        df["final_priority_category"]
        .value_counts()
        .to_string()
    )

    print()
    print("Saved final PhD priority rankings to:")
    print(OUTPUT_FILE)

    print()
    print("Final PhD priority ranking completed successfully.")


if __name__ == "__main__":
    main()
