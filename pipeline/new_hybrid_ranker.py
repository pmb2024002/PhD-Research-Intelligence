import pandas as pd
from pathlib import Path
import yaml


# ============================================================
# Canonical Hybrid Relevance Engine V1
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

BIOLOGICAL_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "phd_biological_score_v1.csv"
)

SEMANTIC_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "pubmed_new_semantic_ranked.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "pubmed_new_hybrid_ranked.csv"
)

HYBRID_CONFIG_FILE = (
    BASE_DIR
    / "config"
    / "canonical_hybrid_v1.yaml"
)


# ============================================================
# Utility functions
# ============================================================

def load_hybrid_config():
    """Load the canonical hybrid configuration."""

    if not HYBRID_CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Hybrid configuration not found: "
            f"{HYBRID_CONFIG_FILE}"
        )

    with open(
        HYBRID_CONFIG_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError(
            "Hybrid configuration is empty or invalid."
        )

    return config


def min_max_normalize(series):
    """
    Min-max normalization to [0, 1].

    If all values are identical, assign 1.0 to every
    observation to avoid division by zero.
    """

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:
        return pd.Series(
            [1.0] * len(series),
            index=series.index
        )

    return (series - minimum) / (maximum - minimum)


# ============================================================
# Main pipeline
# ============================================================

def main():

    print("=" * 80)
    print("CANONICAL HYBRID RELEVANCE ENGINE V1")
    print("=" * 80)

    # --------------------------------------------------------
    # Load configuration
    # --------------------------------------------------------

    print("\nLoading canonical hybrid configuration...")

    config = load_hybrid_config()

    biological_weight = (
        config["components"]["biological"]["weight"]
    )

    semantic_weight = (
        config["components"]["semantic"]["weight"]
    )

    print(
        f"Biological weight: {biological_weight:.2f}"
    )

    print(
        f"Semantic weight:   {semantic_weight:.2f}"
    )

    # --------------------------------------------------------
    # Validate configuration
    # --------------------------------------------------------

    if biological_weight < 0:
        raise ValueError(
            "Biological weight cannot be negative."
        )

    if semantic_weight < 0:
        raise ValueError(
            "Semantic weight cannot be negative."
        )

    total_weight = (
        biological_weight
        + semantic_weight
    )

    if abs(total_weight - 1.0) > 1e-9:
        raise ValueError(
            "Hybrid weights must sum to 1.0. "
            f"Current sum = {total_weight}"
        )

    # --------------------------------------------------------
    # Load biological evidence
    # --------------------------------------------------------

    print("\nLoading biological evidence...")

    if not BIOLOGICAL_FILE.exists():
        raise FileNotFoundError(
            f"Biological file not found: "
            f"{BIOLOGICAL_FILE}"
        )

    biological = pd.read_csv(
        BIOLOGICAL_FILE
    )

    print(
        f"Biological papers: {len(biological)}"
    )

    # --------------------------------------------------------
    # Load semantic rankings
    # --------------------------------------------------------

    print("Loading semantic rankings...")

    if not SEMANTIC_FILE.exists():
        raise FileNotFoundError(
            f"Semantic file not found: "
            f"{SEMANTIC_FILE}"
        )

    semantic = pd.read_csv(
        SEMANTIC_FILE
    )

    print(
        f"Semantic papers: {len(semantic)}"
    )

    # --------------------------------------------------------
    # Validate required columns
    # --------------------------------------------------------

    biological_required = [
        "pmid",
        "biological_score",
    ]

    semantic_required = [
        "pmid",
        "semantic_similarity",
        "semantic_rank",
    ]

    missing_biological = [
        c
        for c in biological_required
        if c not in biological.columns
    ]

    missing_semantic = [
        c
        for c in semantic_required
        if c not in semantic.columns
    ]

    if missing_biological:
        raise ValueError(
            "Biological file missing columns: "
            f"{missing_biological}"
        )

    if missing_semantic:
        raise ValueError(
            "Semantic file missing columns: "
            f"{missing_semantic}"
        )

    # --------------------------------------------------------
    # PMID integrity checks
    # --------------------------------------------------------

    if biological["pmid"].isna().any():
        raise ValueError(
            "Missing PMID values found in biological file."
        )

    if semantic["pmid"].isna().any():
        raise ValueError(
            "Missing PMID values found in semantic file."
        )

    if biological["pmid"].duplicated().any():
        raise ValueError(
            "Duplicate PMID values found in biological file."
        )

    if semantic["pmid"].duplicated().any():
        raise ValueError(
            "Duplicate PMID values found in semantic file."
        )

    # --------------------------------------------------------
    # Merge using PMID
    # --------------------------------------------------------

    print("\nMerging biological and semantic data by PMID...")

    df = biological.merge(
        semantic[
            [
                "pmid",
                "semantic_similarity",
                "semantic_rank",
            ]
        ],
        on="pmid",
        how="inner",
        validate="one_to_one",
    )

    print(
        f"Merged papers: {len(df)}"
    )

    if len(df) == 0:
        raise ValueError(
            "No papers matched between biological and semantic files."
        )

    # --------------------------------------------------------
    # Normalize independent scores
    # --------------------------------------------------------

    print("\nNormalizing biological and semantic scores...")

    df["biological_normalized"] = (
        min_max_normalize(
            df["biological_score"]
        )
    )

    df["semantic_normalized"] = (
        min_max_normalize(
            df["semantic_similarity"]
        )
    )

    # --------------------------------------------------------
    # Canonical hybrid score
    # --------------------------------------------------------

    print("\nCalculating canonical hybrid score...")

    df["hybrid_score"] = (
        biological_weight
        * df["biological_normalized"]
        +
        semantic_weight
        * df["semantic_normalized"]
    )

    # --------------------------------------------------------
    # Ranking
    # --------------------------------------------------------

    df["hybrid_rank"] = (
        df["hybrid_score"]
        .rank(
            ascending=False,
            method="min"
        )
        .astype(int)
    )

    df = (
        df
        .sort_values(
            by="hybrid_score",
            ascending=False
        )
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # Priority categories
    # --------------------------------------------------------

    categories = config.get(
        "categories",
        {}
    )

    very_high_min = categories.get(
        "very_high",
        {}
    ).get(
        "min_score",
        0.75
    )

    high_min = categories.get(
        "high",
        {}
    ).get(
        "min_score",
        0.50
    )

    moderate_min = categories.get(
        "moderate",
        {}
    ).get(
        "min_score",
        0.25
    )

    low_min = categories.get(
        "low",
        {}
    ).get(
        "min_score",
        0.00
    )

    def classify(score):

        if score >= very_high_min:
            return categories.get(
                "very_high",
                {}
            ).get(
                "label",
                "Very High"
            )

        elif score >= high_min:
            return categories.get(
                "high",
                {}
            ).get(
                "label",
                "High"
            )

        elif score >= moderate_min:
            return categories.get(
                "moderate",
                {}
            ).get(
                "label",
                "Moderate"
            )

        elif score >= low_min:
            return categories.get(
                "low",
                {}
            ).get(
                "label",
                "Low"
            )

        return "Low"

    df["research_priority"] = (
        df["hybrid_score"]
        .apply(classify)
    )

    # --------------------------------------------------------
    # Configuration/provenance fields
    # --------------------------------------------------------

    df["hybrid_engine_version"] = (
        config.get(
            "version",
            "1.0"
        )
    )

    df["hybrid_engine_status"] = (
        config.get(
            "status",
            "canonical_candidate"
        )
    )

    df["hybrid_biological_weight"] = (
        biological_weight
    )

    df["hybrid_semantic_weight"] = (
        semantic_weight
    )

    df["semantic_model"] = (
        config.get(
            "canonical_model",
            "sentence-transformers/all-MiniLM-L6-v2"
        )
    )

    # --------------------------------------------------------
    # Final integrity checks
    # --------------------------------------------------------

    if df["pmid"].duplicated().any():
        raise ValueError(
            "Duplicate PMID detected after merge."
        )

    if df["hybrid_score"].isna().any():
        raise ValueError(
            "Missing hybrid scores detected."
        )

    if df["hybrid_rank"].isna().any():
        raise ValueError(
            "Missing hybrid ranks detected."
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("TOP 15 PAPERS — CANONICAL HYBRID RELEVANCE")
    print("=" * 80)

    for i, row in df.head(15).iterrows():

        print(
            f"{i + 1}. "
            f"{row['hybrid_score']:.4f} | "
            f"{row['research_priority']} | "
            f"PMID {row['pmid']} | "
            f"{row['title']}"
        )

    print("\n" + "=" * 80)
    print("PRIORITY DISTRIBUTION")
    print("=" * 80)

    print(
        df["research_priority"]
        .value_counts()
        .to_string()
    )

    print("\n" + "=" * 80)
    print("CANONICAL HYBRID ENGINE SUMMARY")
    print("=" * 80)

    print(
        f"Biological weight: {biological_weight:.2f}"
    )

    print(
        f"Semantic weight:   {semantic_weight:.2f}"
    )

    print(
        f"Total weight:      {total_weight:.2f}"
    )

    print(
        "Semantic model:    "
        f"{df['semantic_model'].iloc[0]}"
    )

    print(
        f"Input papers:      {len(biological)}"
    )

    print(
        f"Merged papers:     {len(df)}"
    )

    print(
        "\nSaved canonical hybrid rankings to:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nCanonical hybrid ranking completed successfully."
    )


if __name__ == "__main__":
    main()
