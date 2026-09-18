import pandas as pd
from pathlib import Path


# ============================================================
# PhD Research Intelligence System
# Active Learning / Informative Labeling Pool V1
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "phd_labeling_pool_batch_003.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "phd_active_labeling_pool_v1.csv"
)


def main():

    print("=" * 70)
    print("PhD Research Intelligence System")
    print("Active / Informative Labeling Pool V1")
    print("=" * 70)

    df = pd.read_csv(INPUT_FILE)

    print(f"\nLoaded {len(df)} papers.")

    required = [
        "pmid",
        "title",
        "final_phd_priority_score",
        "hybrid_score",
        "semantic_similarity",
        "biological_score_normalized",
        "direct_mito_senescence",
        "primary_gene_present",
        "preferred_model_present",
        "multiomics_present",
        "strong_biological_evidence",
        "phd_priority_feature_score",
    ]

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    # ---------------------------------------------------------
    # 1. Semantic-biological disagreement
    # ---------------------------------------------------------

    df["semantic_biological_gap"] = (
        df["semantic_similarity"]
        - df["biological_score_normalized"]
    )

    df["absolute_semantic_biological_gap"] = (
        df["semantic_biological_gap"].abs()
    )

    selected = []

    # ---------------------------------------------------------
    # 2. HIGH PRIORITY
    #
    # Six highest-scoring papers.
    # ---------------------------------------------------------

    high = (
        df.sort_values(
            "final_phd_priority_score",
            ascending=False
        )
        .head(6)
    )

    selected.append(high)

    # ---------------------------------------------------------
    # 3. DECISION BOUNDARY
    #
    # Six papers around the median priority region.
    # These help learn the Maybe/Relevant boundary.
    # ---------------------------------------------------------

    median_score = df["final_phd_priority_score"].median()

    boundary = (
        df.assign(
            distance_from_median=(
                df["final_phd_priority_score"]
                - median_score
            ).abs()
        )
        .sort_values("distance_from_median")
        .head(6)
    )

    selected.append(boundary)

    # ---------------------------------------------------------
    # 4. SEMANTIC >> BIOLOGICAL
    #
    # Detect papers whose semantic relevance is not captured
    # by the biological feature engine.
    # ---------------------------------------------------------

    semantic_high = (
        df.sort_values(
            "semantic_biological_gap",
            ascending=False
        )
        .head(6)
    )

    selected.append(semantic_high)

    # ---------------------------------------------------------
    # 5. LOW PRIORITY
    #
    # Important for detecting false negatives.
    # ---------------------------------------------------------

    low = (
        df.sort_values(
            "final_phd_priority_score",
            ascending=True
        )
        .head(6)
    )

    selected.append(low)

    # ---------------------------------------------------------
    # 6. FEATURE-DIVERSITY SAMPLE
    #
    # Select papers with unusual combinations of features.
    # ---------------------------------------------------------

    feature_cols = [
        "direct_mito_senescence",
        "primary_gene_present",
        "preferred_model_present",
        "multiomics_present",
        "strong_biological_evidence",
    ]

    feature_pattern = (
        df[feature_cols]
        .astype(int)
        .astype(str)
        .agg("".join, axis=1)
    )

    df["feature_pattern"] = feature_pattern

    diversity = (
        df.groupby("feature_pattern", group_keys=False)
        .apply(
            lambda x: x.sample(
                n=1,
                random_state=42
            )
        )
        .reset_index(drop=True)
    )

    diversity = (
        diversity
        .sort_values(
            "final_phd_priority_score",
            ascending=False
        )
        .head(6)
    )

    selected.append(diversity)

    # ---------------------------------------------------------
    # Combine selections
    # ---------------------------------------------------------

    pool = pd.concat(
        selected,
        ignore_index=True
    )

    # Remove duplicates by PMID
    pool = (
        pool
        .drop_duplicates(
            subset=["pmid"]
        )
        .reset_index(drop=True)
    )

    # If overlapping strata reduced the pool below 30,
    # fill from remaining papers using score diversity.
    if len(pool) < 30:

        remaining = df[
            ~df["pmid"].isin(pool["pmid"])
        ].copy()

        remaining["distance_from_median"] = (
            remaining["final_phd_priority_score"]
            - median_score
        ).abs()

        fill = (
            remaining
            .sort_values(
                "distance_from_median",
                ascending=True
            )
            .head(30 - len(pool))
        )

        pool = pd.concat(
            [pool, fill],
            ignore_index=True
        )

    # Final ordering
    pool = pool.sort_values(
        "final_phd_priority_score",
        ascending=False
    ).reset_index(drop=True)

    # Labeling order
    pool["labeling_order"] = (
        range(1, len(pool) + 1)
    )

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    pool.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    # ---------------------------------------------------------
    # Report
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("ACTIVE LABELING POOL")
    print("=" * 70)

    print(
        f"\nSelected papers: {len(pool)}"
    )

    print("\nSelected papers:")

    for _, row in pool.iterrows():

        print(
            f"{int(row['labeling_order']):2d}. "
            f"PMID {row['pmid']} | "
            f"Score {row['final_phd_priority_score']:.2f} | "
            f"Semantic {row['semantic_similarity']:.3f} | "
            f"Bio {row['biological_score_normalized']:.3f} | "
            f"Gap {row['semantic_biological_gap']:.3f} | "
            f"{row['title']}"
        )

    print("\nSaved active labeling pool to:")
    print(OUTPUT_FILE)

    print("\nActive labeling pool generation completed successfully.")


if __name__ == "__main__":
    main()
