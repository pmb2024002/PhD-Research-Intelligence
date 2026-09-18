import pandas as pd
import re


# ============================================================
# O5 LEVEL-3 AUDIT
# Inspect exact abstract sentences that triggered O5 = 3
# ============================================================

OBJECTIVE_FILE = (
    "data/processed/canonical_objective_features_v1.csv"
)

LITERATURE_FILE = (
    "data/processed/canonical_literature.csv"
)


MITO_TERMS = [
    "mitochondrial dysfunction",
    "mitochondrial fission",
    "mitochondrial fusion",
    "mitochondrial dynamics",
    "mitophagy",
    "mitochondrial quality control",
    "mitochondrial homeostasis",
    "mitochondrial ros",
    "mitochondrial reactive oxygen species",
    "mitochondrial membrane potential",
    "mitochondrial stress",
]


SENESCENCE_TERMS = [
    "cellular senescence",
    "cell senescence",
    "replicative senescence",
    "stress-induced senescence",
    "irradiation-induced senescence",
    "dna damage-induced senescence",
    "therapy-induced senescence",
    "premature senescence",
    "senescent cell",
    "senescent cells",
    "senescence",
]


CAUSAL_TERMS = [
    "caused by",
    "causes",
    "induces",
    "induced by",
    "drives",
    "driven by",
    "mediates",
    "mediated by",
    "required for",
    "necessary for",
    "sufficient for",
    "dependent on",
    "rescues",
    "rescued",
    "reverses",
    "reversed",
    "abolishes",
    "abolished",
    "knockdown",
    "knockout",
    "silencing",
    "depletion",
    "inhibition",
    "overexpression",
    "loss-of-function",
    "gain-of-function",
]


def contains_any(text, terms):
    """
    Return True when at least one term occurs in text.
    """
    text = str(text).lower()

    return any(
        term.lower() in text
        for term in terms
    )


def main():

    print("=" * 120)
    print("O5 LEVEL-3 AUDIT")
    print("=" * 120)

    # --------------------------------------------------------
    # Load files
    # --------------------------------------------------------

    objective_df = pd.read_csv(
        OBJECTIVE_FILE
    )

    literature_df = pd.read_csv(
        LITERATURE_FILE
    )

    # --------------------------------------------------------
    # Integrity checks
    # --------------------------------------------------------

    if objective_df["pmid"].duplicated().any():
        raise ValueError(
            "Duplicate PMID detected in objective features."
        )

    if literature_df["pmid"].duplicated().any():
        raise ValueError(
            "Duplicate PMID detected in literature table."
        )

    # --------------------------------------------------------
    # Merge abstract information
    # --------------------------------------------------------

    df = objective_df.merge(
        literature_df[
            [
                "pmid",
                "abstract",
            ]
        ],
        on="pmid",
        how="left",
        validate="one_to_one",
    )

    # --------------------------------------------------------
    # Select O5 level-3 papers
    # --------------------------------------------------------

    level3 = df[
        df[
            "O5_mechanistic_connection_level"
        ] == 3
    ].copy()

    print(
        f"\nO5 level-3 papers found: {len(level3)}"
    )

    print(
        "\n"
        + "=" * 120
    )
    print(
        "EXACT ABSTRACT SENTENCES TRIGGERING O5 = 3"
    )
    print(
        "=" * 120
    )

    # --------------------------------------------------------
    # Inspect each level-3 paper
    # --------------------------------------------------------

    for _, row in level3.iterrows():

        pmid = row["pmid"]
        title = row["title"]
        abstract = str(
            row.get(
                "abstract",
                ""
            )
        )

        print(
            f"\nPMID: {pmid}"
        )

        print(
            f"Title: {title}"
        )

        print(
            "Title-connected:",
            int(
                row[
                    "O5_title_connected"
                ]
            ),
        )

        print(
            "Title-strong-mechanistic:",
            int(
                row[
                    "O5_title_strong_mechanistic"
                ]
            ),
        )

        print(
            "Mechanistic sentences:",
            int(
                row[
                    "O5_mechanistic_sentence_count"
                ]
            ),
        )

        print(
            "Connected sentences:",
            int(
                row[
                    "O5_connected_sentence_count"
                ]
            ),
        )

        print(
            "Strong causal sentences:",
            int(
                row[
                    "O5_strong_causal_sentence_count"
                ]
            ),
        )

        # ----------------------------------------------------
        # Sentence-level inspection
        # ----------------------------------------------------

        sentences = [
            s.strip()
            for s in re.split(
                r"[.!?]",
                abstract,
            )
            if s.strip()
        ]

        trigger_count = 0

        for sentence in sentences:

            sentence_mito = contains_any(
                sentence,
                MITO_TERMS,
            )

            sentence_senescence = contains_any(
                sentence,
                SENESCENCE_TERMS,
            )

            sentence_causal = contains_any(
                sentence,
                CAUSAL_TERMS,
            )

            if (
                sentence_mito
                and sentence_senescence
                and sentence_causal
            ):

                trigger_count += 1

                print(
                    f"\n  Trigger sentence {trigger_count}:"
                )

                print(
                    "  "
                    + sentence
                )

        if trigger_count == 0:

            print(
                "\n  No qualifying abstract trigger sentence."
            )

            if int(
                row[
                    "O5_title_strong_mechanistic"
                ]
            ) == 1:

                print(
                    "  O5 = 3 is therefore title-driven."
                )

    # --------------------------------------------------------
    # Final audit summary
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 120
    )

    print(
        "AUDIT COMPLETE"
    )

    print(
        "Total O5 level-3 papers:",
        len(level3),
    )

    print(
        "=" * 120
    )


if __name__ == "__main__":
    main()
