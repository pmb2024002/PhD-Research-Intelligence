from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RANKED_FILE = PROJECT_ROOT / "data" / "processed" / "pubmed_ranked.csv"
SEMANTIC_FILE = PROJECT_ROOT / "data" / "processed" / "pubmed_semantic_ranked.csv"
MECHANISTIC_FILE = PROJECT_ROOT / "data" / "processed" / "phd_mechanistic_strength_v2.csv"
UTILITY_FILE = PROJECT_ROOT / "data" / "processed" / "phd_utility_features_v2.csv"
OBJECTIVE_FILE = PROJECT_ROOT / "data" / "processed" / "phd_objective_evidence_v2.csv"
FEEDBACK_FILE = PROJECT_ROOT / "data" / "processed" / "phd_feedback_dataset.csv"
RSA_FILE = PROJECT_ROOT / "data" / "processed" / "phd_rsa_v2.csv"

OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "phd_prus_v2.csv"

RSA_MAX = 25.0
MECHANISTIC_MAX = 20.0
SEMANTIC_MAX = 15.0
BIOLOGICAL_MAX = 15.0
MODEL_MAX = 10.0
OMICS_MAX = 5.0
OBJECTIVE_MAX = 10.0
FEEDBACK_MAX = 5.0
PERIPHERAL_MAX_PENALTY = 5.0

def safe_numeric(series):
    return pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0.0)

SEMANTIC_FLOOR = 0.30
SEMANTIC_CEILING = 0.75


def calculate_semantic_component(df):
    similarity = safe_numeric(
        df["semantic_similarity"]
    )

    normalized = (
        (similarity - SEMANTIC_FLOOR)
        / (SEMANTIC_CEILING - SEMANTIC_FLOOR)
    ).clip(0.0, 1.0)

    return normalized * SEMANTIC_MAX

def calculate_mechanistic_component(df):
    level = safe_numeric(
        df["mechanistic_strength_level"]
    ).clip(0, 4)

    return (
        level / 4.0
    ) * MECHANISTIC_MAX

BIOLOGICAL_REFERENCE_MAX = 100.0


def calculate_biological_component(df):
    biological = safe_numeric(
        df["biological_score"]
    ).clip(0, BIOLOGICAL_REFERENCE_MAX)

    normalized = (
        biological
        / BIOLOGICAL_REFERENCE_MAX
    )

    return normalized * BIOLOGICAL_MAX

MODEL_REFERENCE_MAX = 10.0


def calculate_model_component(df):
    model_score = safe_numeric(
        df["model_relevance_score"]
    ).clip(0, MODEL_REFERENCE_MAX)

    return (
        model_score
        / MODEL_REFERENCE_MAX
    ) * MODEL_MAX

def calculate_omics_component(df):
    score = pd.Series(
        0.0,
        index=df.index
    )

    modalities = (
        df["omics_modalities"]
        .fillna("")
        .astype(str)
        .str.lower()
    )

    score += modalities.str.contains(
        "transcriptomics",
        regex=False
    ).astype(float) * 2.0

    score += modalities.str.contains(
        "proteomics",
        regex=False
    ).astype(float) * 2.0

    score += modalities.str.contains(
        "metabolomics",
        regex=False
    ).astype(float) * 2.0

    score += modalities.str.contains(
        "single-cell",
        regex=False
    ).astype(float) * 2.0

    score += df["has_multiomics"].map(
        lambda x: 1.0
        if str(x).strip().lower() in ["1", "true"]
        else 0.0
    )

    return score.clip(
        upper=OMICS_MAX
    )

def calculate_objective_component(df):
    score = pd.Series(
        0.0,
        index=df.index
    )

    objective_columns = [
        "O1_conserved_signature_level",
        "O2_multiomics_integration_level",
        "O3_hub_gene_level",
        "O4_mito_senescence_conservation_level",
        "O5_mechanistic_connection_level",
    ]

    for column in objective_columns:
        if column in df.columns:
            level = safe_numeric(
                df[column]
            ).clip(0, 3)

            score += (
                level / 3.0
            ) * 2.0

    return score.clip(
        upper=OBJECTIVE_MAX
    )

def calculate_feedback_component(df):
    feedback = (
        df["user_relevance"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    score = pd.Series(
        0.0,
        index=df.index
    )

    score += (
        feedback == "relevant"
    ).astype(float) * FEEDBACK_MAX

    score -= (
        feedback == "not relevant"
    ).astype(float) * FEEDBACK_MAX

    return score

def calculate_peripheral_penalty(df):
    peripheral = (
        df["peripheral_context"]
        .fillna("")
        .astype(str)
    )

    counts = peripheral.apply(
        lambda x: len(
            [
                item
                for item in x.split(";")
                if item.strip()
            ]
        )
        if x.strip()
        else 0
    )

    penalty = pd.Series(
        0.0,
        index=df.index
    )

    penalty -= (
        counts >= 1
    ).astype(float) * 2.0

    penalty -= (
        counts >= 2
    ).astype(float) * 1.5

    penalty -= (
        counts >= 3
    ).astype(float) * 1.5

    return penalty.clip(
        lower=-PERIPHERAL_MAX_PENALTY,
        upper=0.0
    )

def build_prus_dataset():
    ranked = pd.read_csv(RANKED_FILE)
    semantic = pd.read_csv(SEMANTIC_FILE)
    mechanistic = pd.read_csv(MECHANISTIC_FILE)
    utility = pd.read_csv(UTILITY_FILE)
    objective = pd.read_csv(OBJECTIVE_FILE)
    feedback = pd.read_csv(FEEDBACK_FILE)
    rsa = pd.read_csv(RSA_FILE)

    datasets = [
        ranked,
        semantic,
        mechanistic,
        utility,
        objective,
        feedback,
        rsa,
    ]

    for dataset in datasets:
        dataset["pmid"] = (
            dataset["pmid"]
            .astype(str)
            .str.strip()
        )

    df = ranked.copy()

    df = df.merge(
        semantic[
            [
                "pmid",
                "semantic_similarity",
            ]
        ],
        on="pmid",
        how="left",
    )

    df = df.merge(
        mechanistic[
            [
                "pmid",
                "mechanistic_strength_level",
                "mechanistic_strength_explanation",
                "mechanism_label",
            ]
        ],
        on="pmid",
        how="left",
    )

    df = df.merge(
        utility[
            [
                "pmid",
                "omics_modalities",
                "has_multiomics",
            ]
        ],
        on="pmid",
        how="left",
    )

    df = df.merge(
        objective[
            [
                "pmid",
                "O1_conserved_signature_level",
                "O2_multiomics_integration_level",
                "O3_hub_gene_level",
                "O4_mito_senescence_conservation_level",
                "O5_mechanistic_connection_level",
            ]
        ],
        on="pmid",
        how="left",
    )

    df = df.merge(
        feedback[
            [
                "pmid",
                "user_relevance",
                "user_reason",
            ]
        ],
        on="pmid",
        how="left",
    )

    df = df.merge(
        rsa[
            [
                "pmid",
                "RSA_V2",
                "RSA_V2_tier",
                "RSA_V2_reasons",
            ]
        ],
        on="pmid",
        how="left",
    )

    return df

def calculate_prus(df):
    df["rsa_component"] = (
        safe_numeric(df["RSA_V2"]).clip(0, 33)
        / 33.0
    ) * RSA_MAX

    df["semantic_component"] = calculate_semantic_component(df)
    df["mechanistic_component"] = calculate_mechanistic_component(df)
    df["biological_component"] = calculate_biological_component(df)
    df["model_component"] = calculate_model_component(df)
    df["omics_component"] = calculate_omics_component(df)
    df["objective_component"] = calculate_objective_component(df)
    df["feedback_component"] = calculate_feedback_component(df)
    df["peripheral_penalty"] = calculate_peripheral_penalty(df)

    df["PRUS_V2"] = (
        df["rsa_component"]
        + df["semantic_component"]
        + df["mechanistic_component"]
        + df["biological_component"]
        + df["model_component"]
        + df["omics_component"]
        + df["objective_component"]
        + df["feedback_component"]
        + df["peripheral_penalty"]
    ).clip(lower=0)

    df = df.sort_values(
        "PRUS_V2",
        ascending=False
    ).reset_index(drop=True)

    df["PRUS_rank"] = df.index + 1

    return df

def main():
    print("=" * 80)
    print("PhD Research Utility Score (PRUS) V2")
    print("=" * 80)

    df = build_prus_dataset()

    required_columns = [
        "semantic_similarity",
        "mechanistic_strength_level",
        "omics_modalities",
        "has_multiomics",
        "user_relevance",
        "RSA_V2",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns after merge: {missing}"
        )

    df = calculate_prus(df)

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print(f"Saved: {OUTPUT_FILE}")
    print(f"Articles: {len(df)}")
    print()

    print(
        df[
            [
                "PRUS_rank",
                "pmid",
                "RSA_V2",
                "RSA_V2_tier",
                "rsa_component",
                "mechanistic_component",
                "semantic_component",
                "biological_component",
                "model_component",
                "omics_component",
                "objective_component",
                "feedback_component",
                "peripheral_penalty",
                "PRUS_V2",
                "user_relevance",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()

