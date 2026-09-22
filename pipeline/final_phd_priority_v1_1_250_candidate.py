import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "canonical_literature_250_candidate.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "pubmed_final_priority_v1_1_250_candidate.csv"
)


def main():

    print("Loading PhD-priority features...")

    df = pd.read_csv(INPUT_FILE)
    objective = pd.read_csv(
        BASE_DIR / "data" / "processed" /
        "canonical_objective_features_v1_250_candidate.csv"
    )

    df = df.merge(
        objective[[
            "pmid",
            "O2_multiomics_integration_level",
            "O3_hub_gene_level",
            "O4_core_mito_process_level",
            "O5_mechanistic_connection_level",
        ]],
        on="pmid",
        how="inner",
        validate="one_to_one",
    )

    print(f"Loaded {len(df)} papers.")

    # ---------------------------------------------------------
    # Scientific Priority V1.1
    # Distinct dimensions only; avoids double-counting the
    # biological evidence already represented inside hybrid_score.
    # O1 is intentionally excluded until its evidence definition
    # is scientifically finalized.
    # ---------------------------------------------------------

    df["hybrid_component"] = df["hybrid_score"]
    df["mechanistic_component"] = df["O5_mechanistic_connection_level"] / 3.0
    df["hub_component"] = df["O3_hub_gene_level"] / 2.0
    df["pathway_component"] = df["O4_core_mito_process_level"] / 2.0
    df["omics_component"] = df["O2_multiomics_integration_level"] / 3.0
    df["model_component"] = df["preferred_model_present"].astype(float)

    df["final_phd_priority_score"] = 100 * (
        0.35 * df["hybrid_component"]
        + 0.25 * df["mechanistic_component"]
        + 0.15 * df["hub_component"]
        + 0.10 * df["pathway_component"]
        + 0.10 * df["omics_component"]
        + 0.05 * df["model_component"]
    )

    df["final_phd_priority_score"] = (
        df["final_phd_priority_score"]
        .clip(lower=0, upper=100)
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
    print("Scientific Priority V1.1 completed successfully.")


if __name__ == "__main__":
    main()
