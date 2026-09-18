from pathlib import Path
import re

import pandas as pd
import yaml


# ============================================================
# CANONICAL PHD OBJECTIVE FEATURE ENGINE V1
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "canonical_literature.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "canonical_objective_features_v1.csv"
)

OBJECTIVE_CONFIG_FILE = (
    BASE_DIR
    / "config"
    / "canonical_objective_features_v1.yaml"
)

VOCABULARY_CONFIG_FILE = (
    BASE_DIR
    / "config"
    / "canonical_biological_vocabulary_v1.yaml"
)


# ============================================================
# HELPERS
# ============================================================

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def has_any_term(text, terms):
    text = normalize_text(text).lower()

    for term in terms:
        if str(term).lower() in text:
            return True

    return False


def matching_terms(text, terms):
    text = normalize_text(text).lower()

    matches = []

    for term in terms:
        if str(term).lower() in text:
            matches.append(str(term))

    return matches


def get_list(mapping, *keys):
    for key in keys:
        value = mapping.get(key)

        if value is not None:
            if isinstance(value, list):
                return [str(x) for x in value]
            if isinstance(value, dict):
                return [
                    str(x)
                    for x in value.keys()
                ]

    return []


# ============================================================
# O5 RELATIONAL MECHANISM HELPERS
# ============================================================

def relational_mito_senescence_link(
    sentence,
    mito_terms,
    senescence_terms,
    causal_terms,
):
    """
    Determine whether a sentence contains a plausible
    directional mitochondrial-senescence relationship.

    Important:
    Mere co-occurrence of mitochondrial + senescence terms
    + a generic causal word is NOT sufficient.

    Accepted structures include patterns such as:

        mitochondrial dysfunction induces senescence
        mitochondrial ROS drives senescence
        mitophagy attenuates senescence
        senescence causes mitochondrial dysfunction
        mitochondrial fission mediates senescence

    The detector is intentionally conservative.
    """

    text = normalize_text(sentence).lower()

    mito_positions = []

    for term in mito_terms:
        term = str(term).lower()

        for match in re.finditer(
            re.escape(term),
            text,
        ):
            mito_positions.append(
                (
                    match.start(),
                    match.end(),
                )
            )

    sen_positions = []

    for term in senescence_terms:
        term = str(term).lower()

        for match in re.finditer(
            re.escape(term),
            text,
        ):
            sen_positions.append(
                (
                    match.start(),
                    match.end(),
                )
            )

    if not mito_positions or not sen_positions:
        return False

    # --------------------------------------------------------
    # Strong explicit directional patterns
    # --------------------------------------------------------

    pattern_groups = [

        # Mitochondria -> senescence
        [
            r"(?:mitochondrial|mitophagy|mitochondria)"
            r".{0,100}"
            r"(?:causes?|induces?|drives?|promotes?|"
            r"mediates?|triggers?|contributes? to|"
            r"leads? to|results? in|is required for|"
            r"is necessary for|is sufficient for)"
            r".{0,100}"
            r"senesc\w*"
        ],

        # Senescence -> mitochondria
        [
            r"senesc\w*"
            r".{0,100}"
            r"(?:causes?|induces?|drives?|promotes?|"
            r"mediates?|triggers?|contributes? to|"
            r"leads? to|results? in|is associated with)"
            r".{0,100}"
            r"(?:mitochondrial|mitophagy|mitochondria)"
        ],

        # Mitochondrial intervention -> senescence outcome
        [
            r"(?:knockdown|knockout|silencing|depletion|"
            r"inhibition|inhibitor|overexpression|"
            r"activation|deficiency|loss[- ]of[- ]function|"
            r"gain[- ]of[- ]function)"
            r".{0,120}"
            r"(?:mitochondrial|mitophagy|mitochondria)"
            r".{0,120}"
            r"(?:senesc\w*)"
        ],

        # Mitochondrial phenotype -> senescence outcome
        [
            r"(?:mitochondrial dysfunction|mitochondrial ROS|"
            r"mitochondrial fission|mitochondrial fusion|"
            r"mitochondrial dynamics|mitophagy|"
            r"mitochondrial quality control|"
            r"mitochondrial homeostasis)"
            r".{0,120}"
            r"(?:attenuates?|ameliorates?|reverses?|"
            r"rescues?|worsens?|exacerbates?|"
            r"suppresses?|restores?)"
            r".{0,120}"
            r"senesc\w*",
        ],
    ]

    for pattern_group in pattern_groups:

        for pattern in pattern_group:

            if re.search(
                pattern,
                text,
            ):
                return True

    # --------------------------------------------------------
    # Local causal relation around the two concepts
    # --------------------------------------------------------

    for mito_start, mito_end in mito_positions:

        for sen_start, sen_end in sen_positions:

            if mito_start <= sen_start:
                between = text[
                    mito_end:sen_start
                ]

            else:
                between = text[
                    sen_end:mito_start
                ]

            if len(between) > 180:
                continue

            if has_any_term(
                between,
                causal_terms,
            ):
                return True

    return False


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("CANONICAL PHD OBJECTIVE FEATURE ENGINE V1")
    print("=" * 80)

    # --------------------------------------------------------
    # Load configuration
    # --------------------------------------------------------

    objective_config = load_yaml(
        OBJECTIVE_CONFIG_FILE
    )

    vocabulary = load_yaml(
        VOCABULARY_CONFIG_FILE
    )

    # --------------------------------------------------------
    # Load canonical literature
    # --------------------------------------------------------

    df = pd.read_csv(
        INPUT_FILE
    )

    print(
        f"\nInput papers: {len(df)}"
    )

    # --------------------------------------------------------
    # Vocabulary
    # --------------------------------------------------------

    primary_genes = get_list(
        vocabulary,
        "primary_hub_genes",
        "primary_genes",
        "priority_hubs",
    )

    core_processes = get_list(
        vocabulary,
        "core_mitochondrial_processes",
        "core_mito_processes",
        "mitochondrial_processes",
    )

    preferred_models = get_list(
        vocabulary,
        "preferred_models",
    )

    # --------------------------------------------------------
    # Objective-specific vocabularies
    # --------------------------------------------------------

    objective_vocab = (
        objective_config.get(
            "objective_vocabulary",
            {}
        )
    )

    # O1
    conservation_terms = (
        objective_vocab.get(
            "O1_conservation_terms",
            [
                "conserved",
                "conservation",
                "concordant",
                "concordance",
                "shared signature",
                "shared signatures",
                "common signature",
                "common signatures",
                "cross-model",
                "cross model",
                "cross-trigger",
                "cross trigger",
                "consistent",
            ],
        )
    )

    # O2
    transcriptomics_terms = (
        objective_vocab.get(
            "O2_transcriptomics_terms",
            [
                "transcriptom",
                "rna-seq",
                "rna seq",
                "rnaseq",
                "gene expression",
            ],
        )
    )

    proteomics_terms = (
        objective_vocab.get(
            "O2_proteomics_terms",
            [
                "proteom",
                "mass spectrom",
            ],
        )
    )

    metabolomics_terms = (
        objective_vocab.get(
            "O2_metabolomics_terms",
            [
                "metabolom",
                "metabolic profiling",
                "metabolite profiling",
            ],
        )
    )

    multiomics_terms = (
        objective_vocab.get(
            "O2_multiomics_terms",
            [
                "multi-omics",
                "multiomics",
                "multi omics",
                "integrated omics",
                "integrative omics",
            ],
        )
    )

    # O5
    mito_terms = [
        "mitochondrial dysfunction",
        "mitochondrial fission",
        "mitochondrial fusion",
        "mitochondrial dynamics",
        "mitophagy",
        "mitochondrial quality control",
        "mitochondrial homeostasis",
        "mitochondrial biogenesis",
        "mitochondrial proteostasis",
        "mitochondrial membrane potential",
        "mitochondrial ros",
        "mitochondrial reactive oxygen species",
        "mitochondrial stress",
        "oxidative phosphorylation",
        "mitochondrial metabolism",
        "mitochondrial dna",
        "mtDNA",
    ]

    senescence_terms = [
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

    strong_causal_terms = [
        "caused by",
        "causes",
        "induces",
        "induced by",
        "drives",
        "driven by",
        "mediates",
        "mediated by",
        "triggers",
        "triggered by",
        "promotes",
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
        "inhibitor",
        "overexpression",
        "deficiency",
        "loss-of-function",
        "gain-of-function",
    ]

    mechanistic_terms = [
        "mechanism",
        "mechanistically",
        "via",
        "through",
        "regulates",
        "regulating",
        "promotes",
        "attenuates",
        "ameliorates",
        "modulates",
        "contributes to",
        "leads to",
        "resulting in",
        "associated with",
        "mediates",
        "mediated by",
    ]

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    results = []

    for _, row in df.iterrows():

        title = normalize_text(
            row.get(
                "title",
                "",
            )
        )

        abstract = normalize_text(
            row.get(
                "abstract",
                "",
            )
        )

        full_text = (
            title
            + " "
            + abstract
        )

        # ====================================================
        # O1 — Conserved signature
        # ====================================================

        has_conservation = has_any_term(
            full_text,
            conservation_terms,
        )

        has_mito = has_any_term(
            full_text,
            mito_terms,
        )

        has_senescence = has_any_term(
            full_text,
            senescence_terms,
        )

        has_omics = (
            has_any_term(
                full_text,
                transcriptomics_terms,
            )
            or
            has_any_term(
                full_text,
                proteomics_terms,
            )
            or
            has_any_term(
                full_text,
                metabolomics_terms,
            )
        )

        o1_matches = matching_terms(
            full_text,
            conservation_terms,
        )

        if (
            has_conservation
            and has_mito
            and has_omics
        ):
            o1_level = 3

        elif (
            has_conservation
            and has_mito
        ):
            o1_level = 2

        elif has_conservation:
            o1_level = 1

        else:
            o1_level = 0

        # ====================================================
        # O2 — Multi-omics integration
        # ====================================================

        transcriptomics = has_any_term(
            full_text,
            transcriptomics_terms,
        )

        proteomics = has_any_term(
            full_text,
            proteomics_terms,
        )

        metabolomics = has_any_term(
            full_text,
            metabolomics_terms,
        )

        explicit_multiomics = has_any_term(
            full_text,
            multiomics_terms,
        )

        modality_count = sum(
            [
                transcriptomics,
                proteomics,
                metabolomics,
            ]
        )

        if (
            explicit_multiomics
            and modality_count >= 2
        ):
            o2_level = 3

        elif (
            modality_count >= 2
            or explicit_multiomics
        ):
            o2_level = 2

        elif modality_count == 1:
            o2_level = 1

        else:
            o2_level = 0

        # ====================================================
        # O3 — Hub genes
        # ====================================================

        o3_matches = matching_terms(
            full_text,
            primary_genes,
        )

        o3_unique = sorted(
            set(
                o3_matches
            )
        )

        if len(o3_unique) >= 2:
            o3_level = 2

        elif len(o3_unique) == 1:
            o3_level = 1

        else:
            o3_level = 0

        # ====================================================
        # O4 — Core mitochondrial processes
        # ====================================================

        o4_matches = matching_terms(
            full_text,
            core_processes,
        )

        o4_unique = sorted(
            set(
                o4_matches
            )
        )

        if len(o4_unique) >= 2:
            o4_level = 2

        elif len(o4_unique) == 1:
            o4_level = 1

        else:
            o4_level = 0

        # ====================================================
        # O5 — Mechanistic mitochondrial-senescence link
        # ====================================================

        has_strong_causal = has_any_term(
            full_text,
            strong_causal_terms,
        )

        has_mechanistic_language = has_any_term(
            full_text,
            mechanistic_terms,
        )

        # ----------------------------------------------------
        # Title evidence
        # ----------------------------------------------------

        title_mito = has_any_term(
            title,
            mito_terms,
        )

        title_senescence = has_any_term(
            title,
            senescence_terms,
        )

        title_causal = (
            has_any_term(
                title,
                strong_causal_terms,
            )
            or
            has_any_term(
                title,
                mechanistic_terms,
            )
        )

        title_connected = (
            title_mito
            and title_senescence
        )

        # IMPORTANT:
        # Title alone is no longer sufficient unless it
        # contains an explicitly directional mechanistic
        # relationship between mitochondria and senescence.
        title_relational_mechanism = (
            title_connected
            and relational_mito_senescence_link(
                title,
                mito_terms,
                senescence_terms,
                strong_causal_terms,
            )
        )

        title_strong_mechanistic = (
            title_relational_mechanism
            and title_causal
        )

        # ----------------------------------------------------
        # Sentence-level evidence
        # ----------------------------------------------------

        sentences = [
            s.strip()
            for s in re.split(
                r"[.!?]",
                abstract,
            )
            if s.strip()
        ]

        mechanistic_sentence_count = 0
        strong_causal_sentence_count = 0
        connected_sentence_count = 0
        relational_mechanistic_sentence_count = 0

        for sentence in sentences:

            sentence_mito = has_any_term(
                sentence,
                mito_terms,
            )

            sentence_senescence = has_any_term(
                sentence,
                senescence_terms,
            )

            sentence_mechanistic = has_any_term(
                sentence,
                mechanistic_terms,
            )

            sentence_strong_causal = has_any_term(
                sentence,
                strong_causal_terms,
            )

            if (
                sentence_mito
                and sentence_senescence
            ):
                connected_sentence_count += 1

            if (
                sentence_mito
                and sentence_senescence
                and (
                    sentence_mechanistic
                    or sentence_strong_causal
                )
            ):
                mechanistic_sentence_count += 1

            if (
                sentence_mito
                and sentence_senescence
                and sentence_strong_causal
            ):
                strong_causal_sentence_count += 1

            if relational_mito_senescence_link(
                sentence,
                mito_terms,
                senescence_terms,
                strong_causal_terms,
            ):
                relational_mechanistic_sentence_count += 1

        # ----------------------------------------------------
        # FINAL O5 CLASSIFICATION
        # ----------------------------------------------------
        #
        # Level 3 requires a RELATIONAL mitochondrial-
        # senescence mechanism.
        #
        # We intentionally do NOT use:
        #
        #   mitochondrial + senescence + generic causal word
        #
        # as sufficient evidence.
        # ----------------------------------------------------

        if (
            relational_mechanistic_sentence_count > 0
            or title_strong_mechanistic
        ):
            o5_level = 3

        elif (
            connected_sentence_count > 0
            and (
                mechanistic_sentence_count > 0
                or has_mechanistic_language
            )
        ):
            o5_level = 2

        elif (
            title_connected
            and (
                has_strong_causal
                or has_mechanistic_language
            )
        ):
            o5_level = 2

        elif (
            has_mito
            and has_senescence
            and has_strong_causal
        ):
            o5_level = 2

        elif (
            has_mito
            and has_senescence
            and has_mechanistic_language
        ):
            o5_level = 2

        elif (
            has_mito
            and has_senescence
        ):
            o5_level = 1

        else:
            o5_level = 0

        # ====================================================
        # OUTPUT
        # ====================================================

        results.append(
            {
                "pmid": row["pmid"],
                "title": title,

                "O1_conserved_signature_level":
                    o1_level,

                "O1_conserved_signature_matches":
                    "; ".join(
                        o1_matches
                    ),

                "O2_multiomics_integration_level":
                    o2_level,

                "O2_modalities":
                    "; ".join(
                        [
                            x
                            for x, present in [
                                (
                                    "transcriptomics",
                                    transcriptomics,
                                ),
                                (
                                    "proteomics",
                                    proteomics,
                                ),
                                (
                                    "metabolomics",
                                    metabolomics,
                                ),
                            ]
                            if present
                        ]
                    ),

                "O3_hub_gene_level":
                    o3_level,

                "O3_hub_gene_matches":
                    "; ".join(
                        o3_unique
                    ),

                "O4_core_mito_process_level":
                    o4_level,

                "O4_core_mito_process_matches":
                    "; ".join(
                        o4_unique
                    ),

                "O5_mechanistic_connection_level":
                    o5_level,

                "O5_mechanistic_sentence_count":
                    mechanistic_sentence_count,

                "O5_strong_causal_sentence_count":
                    strong_causal_sentence_count,

                "O5_connected_sentence_count":
                    connected_sentence_count,

                "O5_relational_mechanistic_sentence_count":
                    relational_mechanistic_sentence_count,

                "O5_title_connected":
                    int(
                        title_connected
                    ),

                "O5_title_strong_mechanistic":
                    int(
                        title_strong_mechanistic
                    ),

                "O5_title_relational_mechanism":
                    int(
                        title_relational_mechanism
                    ),
            }
        )

    # ========================================================
    # DATAFRAME
    # ========================================================

    result_df = pd.DataFrame(
        results
    )

    # --------------------------------------------------------
    # Integrity checks
    # --------------------------------------------------------

    if len(result_df) != len(df):
        raise ValueError(
            "Objective feature row count mismatch."
        )

    if result_df["pmid"].duplicated().any():
        raise ValueError(
            "Duplicate PMID detected."
        )

    if result_df["pmid"].nunique() != len(result_df):
        raise ValueError(
            "PMID uniqueness check failed."
        )

    # --------------------------------------------------------
    # Provenance
    # --------------------------------------------------------

    result_df[
        "objective_feature_engine_version"
    ] = objective_config.get(
        "version",
        "1.0",
    )

    result_df[
        "biological_vocabulary_version"
    ] = vocabulary.get(
        "version",
        "1.0",
    )

    result_df[
        "objective_feature_status"
    ] = objective_config.get(
        "status",
        "canonical_candidate",
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8",
    )

    # ========================================================
    # AUDIT OUTPUT
    # ========================================================

    print(
        "\n"
        + "=" * 80
    )

    print(
        "OBJECTIVE FEATURE SUMMARY"
    )

    print(
        "=" * 80
    )

    objective_columns = [
        "O1_conserved_signature_level",
        "O2_multiomics_integration_level",
        "O3_hub_gene_level",
        "O4_core_mito_process_level",
        "O5_mechanistic_connection_level",
    ]

    for column in objective_columns:

        print(
            f"\n{column}"
        )

        print(
            result_df[column]
            .value_counts()
            .sort_index()
            .to_string()
        )

    print(
        "\nO5 diagnostic totals:"
    )

    print(
        "Title-connected papers:",
        int(
            result_df[
                "O5_title_connected"
            ].sum()
        ),
    )

    print(
        "Title-connected relational-mechanistic:",
        int(
            result_df[
                "O5_title_relational_mechanism"
            ].sum()
        ),
    )

    print(
        "Title-connected strong-mechanistic:",
        int(
            result_df[
                "O5_title_strong_mechanistic"
            ].sum()
        ),
    )

    print(
        "Papers with connected abstract sentence:",
        int(
            (
                result_df[
                    "O5_connected_sentence_count"
                ] > 0
            ).sum()
        ),
    )

    print(
        "Papers with relational mechanistic sentence:",
        int(
            (
                result_df[
                    "O5_relational_mechanistic_sentence_count"
                ] > 0
            ).sum()
        ),
    )

    print(
        "Papers with strong causal sentence:",
        int(
            (
                result_df[
                    "O5_strong_causal_sentence_count"
                ] > 0
            ).sum()
        ),
    )

    print(
        "\nRows:",
        len(result_df),
    )

    print(
        "Unique PMIDs:",
        result_df["pmid"].nunique(),
    )

    print(
        "\nSaved:"
    )

    print(
        OUTPUT_FILE
    )


if __name__ == "__main__":
    main()
