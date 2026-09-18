from pathlib import Path
import pandas as pd
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RANKED_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pubmed_ranked.csv"
)

SEMANTIC_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pubmed_semantic_ranked.csv"
)

MECHANISTIC_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phd_mechanistic_strength_v2.csv"
)

UTILITY_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phd_utility_features_v2.csv"
)

OBJECTIVE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phd_objective_evidence_v2.csv"
)

FEEDBACK_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phd_feedback_dataset.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phd_prus_v1.csv"
)


def safe_numeric(series):
    return pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0.0)

def normalize_score(series):
    """
    Convert a numeric feature to a 0–1 range.

    Min-max normalization is used only for feature scaling;
    it is not used to learn or optimize PRUS weights.
    """

    values = safe_numeric(series)

    minimum = values.min()
    maximum = values.max()

    if maximum == minimum:
        return pd.Series(
            0.0,
            index=series.index
        )

    return (values - minimum) / (
        maximum - minimum
    )


def calculate_semantic_component(df):
    """
    Convert MiniLM semantic similarity into a
    0–20 PRUS component.
    """

    normalized = normalize_score(
        df["semantic_similarity"]
    )

    return normalized * 20.0


def calculate_mechanistic_component(df):
    """
    Convert mechanistic-strength levels into a
    0–20 PRUS component.

    Level 0 = 0
    Level 1 = 5
    Level 2 = 10
    Level 3 = 15
    Level 4 = 20
    """

    level = safe_numeric(
        df["mechanistic_strength_level"]
    ).clip(0, 4)

    return (level / 4.0) * 20.0

def calculate_biological_component(df):
    """
    Convert the existing rule-based biological relevance
    into a 0–20 PRUS component.
    """

    biological = safe_numeric(
        df["biological_score"]
    )

    normalized = normalize_score(
        biological
    )

    return normalized * 20.0


def calculate_model_component(df):
    """
    Convert model relevance into a 0–10 PRUS component.
    """

    model_score = safe_numeric(
        df["model_relevance_score"]
    )

    normalized = normalize_score(
        model_score
    )

    return normalized * 10.0


def calculate_omics_component(df):
    """
    Assign up to 10 points for omics relevance.

    Multi-omics receives the highest score because it directly
    supports the multi-omics architecture of the PhD.
    """

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
    ).astype(float) * 4.0

    score += modalities.str.contains(
        "proteomics",
        regex=False
    ).astype(float) * 4.0

    score += modalities.str.contains(
        "metabolomics",
        regex=False
    ).astype(float) * 4.0

    score += df["has_multiomics"].map(
        lambda x: 2.0 if str(x).lower() in ["1", "true"] else 0.0
    )

    return score.clip(upper=10.0)

def calculate_objective_component(df):
    """
    Calculate alignment with the five predefined PhD objectives.

    O1 = conserved mitochondrial signature
    O2 = multi-omics integration
    O3 = mitochondrial hub genes
    O4 = mitochondrial-senescence conservation
    O5 = mechanistic connection

    Maximum = 15 points.
    """

    objective_weights = {
        "objective_O1": 3.0,
        "objective_O2": 3.0,
        "objective_O3": 3.0,
        "objective_O4": 3.0,
        "objective_O5": 3.0,
    }

    score = pd.Series(
        0.0,
        index=df.index
    )

    for column, weight in objective_weights.items():
        if column in df.columns:
            values = safe_numeric(df[column]).clip(0, 3)
            score += (values / 3.0) * weight

    return score.clip(upper=15.0)


def calculate_feedback_component(df):
    """
    Apply a conservative adjustment based on explicit user feedback.

    Relevant      = +5
    Maybe         =  0
    Not Relevant  = -5
    Unlabeled     =  0

    Feedback is intentionally kept small so that one human
    judgment cannot overwhelm the biological evidence.
    """

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
    ).astype(float) * 5.0

    score -= (
        feedback == "not relevant"
    ).astype(float) * 5.0

    return score


def calculate_peripheral_penalty(df):
    """
    Penalize papers dominated by peripheral research contexts.

    The penalty is deliberately conservative because a peripheral
    disease/model paper can still contain useful mitochondrial
    biology.
    """

    peripheral = (
        df["peripheral_context"]
        .fillna("")
        .astype(str)
    )

    count = peripheral.apply(
        lambda x: (
            0
            if not x.strip()
            else len(
                [
                    item for item in x.split(";")
                    if item.strip()
                ]
            )
        )
    )

    penalty = pd.Series(
        0.0,
        index=df.index
    )

    penalty -= (count >= 1).astype(float) * 2.0
    penalty -= (count >= 2).astype(float) * 2.0

    return penalty

def build_prus_dataset():
    """
    Build the PhD Research Utility Score (PRUS) dataset
    by joining all evidence layers using PMID.
    """

    ranked = pd.read_csv(RANKED_FILE)
    semantic = pd.read_csv(SEMANTIC_FILE)
    mechanistic = pd.read_csv(MECHANISTIC_FILE)
    utility = pd.read_csv(UTILITY_FILE)
    objective = pd.read_csv(OBJECTIVE_FILE)
    feedback = pd.read_csv(FEEDBACK_FILE)

    datasets = [
        ranked,
        semantic,
        mechanistic,
        utility,
        objective,
        feedback,
    ]

    for dataset in datasets:
        dataset["pmid"] = (
            dataset["pmid"]
            .astype(str)
            .str.strip()
        )

    df = ranked.copy()

    semantic_cols = [
        "pmid",
        "semantic_similarity",
    ]

    df = df.merge(
        semantic[semantic_cols],
        on="pmid",
        how="left",
    )

    mechanistic_cols = [
        "pmid",
        "mechanistic_strength_level",
        "mechanistic_strength_explanation",
        "mechanism_label",
    ]

    df = df.merge(
        mechanistic[mechanistic_cols],
        on="pmid",
        how="left",
    )

    utility_cols = [
        "pmid",
        "omics_modalities",
        "has_multiomics",
    ]

    df = df.merge(
        utility[utility_cols],
        on="pmid",
        how="left",
    )

    objective_cols = [
        "pmid",
        "objective_O1",
        "objective_O2",
        "objective_O3",
        "objective_O4",
        "objective_O5",
    ]

    df = df.merge(
         utility[objective_cols],
         on="pmid",
         how="left",
    )
    feedback_cols = [
        "pmid",
        "user_relevance",
        "user_reason",
    ]

    df = df.merge(
        feedback[feedback_cols],
        on="pmid",
        how="left",
    )

    df["biological_component"] = (
        calculate_biological_component(df)
    )

    df["semantic_component"] = (
        calculate_semantic_component(df)
    )

    df["mechanistic_component"] = (
        calculate_mechanistic_component(df)
    )

    df["model_component"] = (
        calculate_model_component(df)
    )

    df["omics_component"] = (
        calculate_omics_component(df)
    )

    df["objective_component"] = (
        calculate_objective_component(df)
    )

    df["feedback_component"] = (
        calculate_feedback_component(df)
    )

    df["peripheral_penalty"] = (
        calculate_peripheral_penalty(df)
    )

    df["PRUS"] = (
        df["biological_component"]
        + df["semantic_component"]
        + df["mechanistic_component"]
        + df["model_component"]
        + df["omics_component"]
        + df["objective_component"]
        + df["feedback_component"]
        + df["peripheral_penalty"]
    )

    df["PRUS"] = df["PRUS"].clip(lower=0)

    df = df.sort_values(
        "PRUS",
        ascending=False
    ).reset_index(drop=True)

    df["PRUS_rank"] = (
        df.index + 1
    )

    return df


def main():
    print("=" * 70)
    print("PhD Research Utility Score (PRUS) V1")
    print("=" * 70)

    df = build_prus_dataset()

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
                "title",
                "PRUS",
                "user_relevance",
            ]
        ].head(10).to_string(index=False)
    )


if __name__ == "__main__":
    main()
