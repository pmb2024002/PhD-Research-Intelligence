from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phd_utility_features_v1.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phd_utility_scores_v1.csv"
)


def score_priority_hub_gene(row):
    return 20 if int(row["has_priority_hub_gene"]) else 0


def score_core_model(row):
    return 20 if int(row["has_core_phd_model"]) else 0


def score_mito_senescence(row):
    return 20 if int(row["has_mito_senescence_link"]) else 0


def score_omics(row):
    return 15 if int(row["has_omics_signal"]) else 0


def score_objective_alignment(row):
    levels = [
        int(row["objective_O1"]),
        int(row["objective_O2"]),
        int(row["objective_O3"]),
        int(row["objective_O4"]),
        int(row["objective_O5"]),
    ]

    # Use the strongest objective signal rather than summing
    # correlated objectives.
    strongest = max(levels)

    if strongest >= 3:
        return 10

    if strongest == 2:
        return 7

    if strongest == 1:
        return 4

    return 0


def score_transferable_mechanism(row):
    return 10 if int(row["has_transferable_mito_mechanism"]) else 0


def score_model_tier(row):
    tier = int(row["model_relevance_tier"])

    if tier >= 3:
        return 5

    if tier == 2:
        return 3

    if tier == 1:
        return 1

    return 0


def classify_prus(score):
    if score >= 80:
        return "Very High Utility"

    if score >= 60:
        return "High Utility"

    if score >= 40:
        return "Moderate Utility"

    if score >= 20:
        return "Low Utility"

    return "Minimal Utility"


def build_reason(row):
    reasons = []

    if int(row["has_priority_hub_gene"]):
        reasons.append("priority hub gene")

    if int(row["has_core_phd_model"]):
        reasons.append("core PhD model")

    if int(row["has_mito_senescence_link"]):
        reasons.append("mitochondrial-senescence link")

    if int(row["has_omics_signal"]):
        reasons.append("omics evidence")

    if int(row["has_transferable_mito_mechanism"]):
        reasons.append("transferable mitochondrial mechanism")

    if not reasons:
        return "limited direct PhD utility signals"

    return "; ".join(reasons)


def main():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE).fillna("")

    results = []

    for _, row in df.iterrows():

        hub = score_priority_hub_gene(row)
        model = score_core_model(row)
        mito_sen = score_mito_senescence(row)
        omics = score_omics(row)
        objective = score_objective_alignment(row)
        transfer = score_transferable_mechanism(row)
        model_tier = score_model_tier(row)

        total = (
            hub
            + model
            + mito_sen
            + omics
            + objective
            + transfer
            + model_tier
        )

        results.append(
            {
                "pmid": row["pmid"],
                "title": row["title"],
                "user_relevance": row["user_relevance"],
                "prus_score": total,
                "prus_category": classify_prus(total),
                "score_hub_gene": hub,
                "score_core_model": model,
                "score_mito_senescence": mito_sen,
                "score_omics": omics,
                "score_objective_alignment": objective,
                "score_transferable_mechanism": transfer,
                "score_model_tier": model_tier,
                "prus_reason": build_reason(row),
            }
        )

    out = pd.DataFrame(results)

    out = out.sort_values(
        ["prus_score", "pmid"],
        ascending=[False, True],
    )

    out.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("PhD Research Utility Score Engine v1")
    print("=" * 60)
    print(f"Input papers: {len(out)}")
    print(f"Output: {OUTPUT_FILE}")

    print("\nPRUS distribution:")
    print(
        out["prus_category"]
        .value_counts()
        .to_string()
    )

    print("\nTop papers:")
    print(
        out[
            [
                "pmid",
                "prus_score",
                "prus_category",
                "title",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    print("\nVALID")


if __name__ == "__main__":
    main()
