from pathlib import Path
import re
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RANKED_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pubmed_ranked.csv"
)

FEEDBACK_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phd_feedback_dataset.csv"
)

OBJECTIVE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phd_objective_evidence_v1.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phd_utility_features_v1.csv"
)


# ---------------------------------------------------------
# Text utilities
# ---------------------------------------------------------

def normalize(text):
    return str(text).lower()


def contains_any(text, terms):
    text = normalize(text)

    for term in terms:
        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        if re.search(pattern, text):
            return True

    return False


def contains_stem(text, stems):
    """Match biological word stems such as transcriptom -> transcriptome/transcriptomic/transcriptomics."""
    text = normalize(text)

    for stem in stems:
        pattern = r"\b" + re.escape(stem.lower()) + r"\w*\b"
        if re.search(pattern, text):
            return True

    return False


# ---------------------------------------------------------
# Feature definitions
# ---------------------------------------------------------

def get_phd_text(row):
    return normalize(
        str(row.get("title", ""))
        + " "
        + str(row.get("abstract", ""))
    )


def detect_hub_gene(text):
    genes = [
        "DNM1L",
        "DRP1",
        "OPA1",
        "MFN1",
        "MFN2",
        "PINK1",
        "PRKN",
        "PARK2",
        "SIRT3",
        "MTFR1L",
    ]

    return int(contains_any(text, genes))


def detect_fibroblast(text):
    terms = [
        "IMR-90",
        "IMR90",
        "human fibroblast",
        "fibroblast",
        "fibroblasts",
    ]

    return int(contains_any(text, terms))


def detect_mito_senescence(text):
    mitochondrial = [
        "mitochondrial dysfunction",
        "mitochondrial dynamics",
        "mitochondrial quality control",
        "mitochondrial homeostasis",
        "mitophagy",
        "mitochondrial fission",
        "mitochondrial fusion",
        "mitochondrial ros",
    ]

    senescence = [
        "cellular senescence",
        "senescence",
        "senescent",
    ]

    return int(
        contains_any(text, mitochondrial)
        and contains_any(text, senescence)
    )


def detect_omics(text):
    """Detect transcriptomic, proteomic, metabolomic and multi-omics evidence."""
    if contains_stem(text, ['transcriptom', 'proteom', 'metabolom']):
        return 1

    if contains_any(text, [
        'rna-seq',
        'rna seq',
        'transcriptional profiling',
        'transcriptional analysis',
        'mass spectrometry',
        'multi-omics',
        'multiomics',
        'single-cell',
    ]):
        return 1

    return 0

def detect_multiomics(text):
    """Detect whether at least two distinct omics modalities are present."""
    transcriptomic = contains_stem(text, ['transcriptom']) or contains_any(
        text, ['rna-seq', 'rna seq', 'transcriptional profiling', 'transcriptional analysis']
    )

    proteomic = contains_stem(text, ['proteom']) or contains_any(
        text, ['mass spectrometry']
    )

    metabolomic = contains_stem(text, ['metabolom']) or contains_any(
        text, ['metabolite profiling']
    )

    modality_count = sum([
        transcriptomic,
        proteomic,
        metabolomic,
    ])

    explicit_multiomics = contains_any(
        text,
        ['multi-omics', 'multiomics', 'multi-omics integration',
         'integrative analysis', 'cross-omics']
    )

    return int(modality_count >= 2 or explicit_multiomics)

def detect_mechanistic_signal(text):
    terms = [
        "knockdown",
        "knockout",
        "overexpression",
        "inhibition",
        "inhibitor",
        "silencing",
        "depletion",
        "loss-of-function",
        "gain-of-function",
        "mutation",
        "mutant",
        "rescue",
        "rescued",
        "pharmacological inhibition",
        "genetic manipulation",
        "deletion",
    ]

    return int(contains_any(text, terms))


def detect_experimental_model(text):
    terms = [
        "IMR-90",
        "IMR90",
        "human fibroblast",
        "fibroblast",
        "RPE",
        "retinal pigment epithelial",
        "ovarian granulosa",
        "bovine cumulus",
        "BMSC",
        "bone marrow stromal",
        "skeletal muscle",
        "myocardial",
        "cardiovascular",
        "kidney",
        "renal",
        "chondrocyte",
    ]

    return int(contains_any(text, terms))


def detect_model_relevance_tier(text):
    """Assign model relevance using experimental-model context, not simple keyword mentions."""
    text = normalize(text)

    # Direct PhD models: require experimental-use context for generic fibroblast terms.
    direct_specific = [
        'IMR-90',
        'IMR90',
        'IMR-90 fibroblast',
        'IMR90 fibroblast',
    ]

    direct_fibroblast_context = [
        'fibroblasts were used',
        'fibroblasts were cultured',
        'fibroblasts were treated',
        'fibroblasts were exposed',
        'fibroblasts were isolated',
        'fibroblasts were obtained',
        'fibroblast cells were used',
        'human fibroblasts were used',
        'human fibroblasts were cultured',
        'human fibroblasts were treated',
        'human fibroblasts were exposed',
        'human fibroblasts were isolated',
        'human fibroblasts were obtained',
        'lung fibroblast senescence',
        'lung fibroblasts contribute',
        'lung fibroblasts contributes',
        'lung fibroblasts senescence',
    ]

    related_models = [
        'RPE',
        'retinal pigment epithelial',
        'ovarian granulosa',
        'bovine cumulus',
        'BMSC',
        'bone marrow stromal',
        'chondrocyte',
        'chondrocytes',
        'mouse embryonic fibroblast',
        'mouse embryonic fibroblasts',
    ]

    other_models = [
        'skeletal muscle',
        'myocardial',
        'cardiovascular',
        'kidney',
        'renal',
    ]

    other_model_context = [
        'mitochondrial dysfunction in nucleus pulposus (np) cells',
        'degenerated np cells',
        'degenerated nucleus pulposus cells',
        'np cells in vitro',
        'nucleus pulposus cells in vitro',
        'nucleus pulposus cells were used',
        'nucleus pulposus cells were cultured',
        'nucleus pulposus cells were treated',
        'nucleus pulposus cells were exposed',
        'nucleus pulposus cells were isolated',
        'nucleus pulposus cells were obtained',
        'NP cells were used',
        'NP cells were cultured',
        'NP cells were treated',
        'NP cells were exposed',
        'NP cells were isolated',
        'NP cells were obtained',
    ]

    if contains_any(text, direct_specific):
        return 3

    if contains_any(text, direct_fibroblast_context):
        return 3

    if contains_any(text, related_models):
        return 2

    if contains_any(text, other_model_context):
        return 1

    # A generic NP-cell mention is contextual evidence, not an experimental model.
    # Do not assign a model tier from 'nucleus pulposus' alone.

    if contains_any(text, other_models):
        return 1

    return 0

def detect_disease_application(text):
    terms = [
        "pulmonary fibrosis",
        "idiopathic pulmonary fibrosis",
        "IPF",
        "osteoarthritis",
        "rheumatoid arthritis",
        "alzheimer",
        "intervertebral disc",
        "disc degeneration",
        "cardiovascular disease",
        "myocardial",
        "acute kidney injury",
        "kidney disease",
        "skin aging",
        "cancer",
        "tumor",
    ]

    return int(contains_any(text, terms))


def detect_core_phd_model(text):
    """Detect experimental models most directly aligned with the PhD."""
    terms = [
        'IMR-90',
        'IMR90',
        'human fibroblast',
        'human fibroblasts',
        'fibroblast',
        'fibroblasts',
    ]

    return int(contains_any(text, terms))

def detect_transferable_mechanism(text):
    """
    Mechanistic findings that may transfer across models.
    """

    terms = [
        "mitochondrial fission",
        "mitochondrial fusion",
        "mitophagy",
        "mitochondrial quality control",
        "mitochondrial dynamics",
        "mitochondrial dysfunction",
        "mitochondrial ros",
        "mitochondrial membrane potential",
    ]

    return int(contains_any(text, terms))


# ---------------------------------------------------------
# Main feature construction
# ---------------------------------------------------------

def main():

    if not RANKED_FILE.exists():
        raise FileNotFoundError(
            f"Ranked file not found: {RANKED_FILE}"
        )

    if not FEEDBACK_FILE.exists():
        raise FileNotFoundError(
            f"Feedback file not found: {FEEDBACK_FILE}"
        )

    if not OBJECTIVE_FILE.exists():
        raise FileNotFoundError(
            f"Objective evidence file not found: {OBJECTIVE_FILE}"
        )

    ranked = pd.read_csv(RANKED_FILE).fillna("")
    feedback = pd.read_csv(FEEDBACK_FILE).fillna("")
    objective = pd.read_csv(OBJECTIVE_FILE).fillna("")

    feedback_subset = feedback[
        [
            "pmid",
            "user_relevance",
            "user_reason",
        ]
    ]

    df = ranked.merge(
        feedback_subset,
        on="pmid",
        how="left",
    )

    df = df.merge(
        objective,
        on=["pmid", "title"],
        how="left",
        suffixes=("", "_objective"),
    )

    feature_rows = []

    for _, row in df.iterrows():

        text = get_phd_text(row)

        feature_rows.append(
            {
                "pmid": row["pmid"],
                "title": row["title"],
                "user_relevance": row["user_relevance"],
                "user_reason": row["user_reason"],

                "has_mito_senescence_link":
                    detect_mito_senescence(text),

                "has_priority_hub_gene":
                    detect_hub_gene(text),

                "has_fibroblast_relevance":
                    detect_fibroblast(text),

                "has_core_phd_model":
                    detect_core_phd_model(text),

                "has_omics_signal":
                    detect_omics(text),

                "has_multiomics_signal":
                    detect_multiomics(text),

                "has_mechanistic_signal":
                    detect_mechanistic_signal(text),

                "has_experimental_model":
                    detect_experimental_model(text),

                "model_relevance_tier":
                    detect_model_relevance_tier(text),

                "has_disease_application":
                    detect_disease_application(text),

                "has_transferable_mito_mechanism":
                    detect_transferable_mechanism(text),

                "objective_O1":
                    row["O1_conserved_signatures_level"],

                "objective_O2":
                    row["O2_multiomics_integration_level"],

                "objective_O3":
                    row["O3_hub_genes_level"],

                "objective_O4":
                    row["O4_conserved_pathways_level"],

                "objective_O5":
                    row["O5_mechanistic_connection_level"],
            }
        )

    out = pd.DataFrame(feature_rows)

    out.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("PhD Utility Feature Engine v1")
    print("=" * 60)

    print(f"Input papers: {len(out)}")
    print(f"Output: {OUTPUT_FILE}")

    print("\nFeature prevalence:")

    feature_columns = [
        "has_mito_senescence_link",
        "has_priority_hub_gene",
        "has_fibroblast_relevance",
        "has_core_phd_model",
        "has_omics_signal",
        "has_multiomics_signal",
        "has_mechanistic_signal",
        "has_experimental_model",
        "has_disease_application",
        "has_transferable_mito_mechanism",
    ]

    for column in feature_columns:
        print(
            f"{column}: "
            f"{int(out[column].sum())}/{len(out)}"
        )

    print("\nUser-label distribution:")

    print(
        out["user_relevance"]
        .value_counts()
        .to_string()
    )

    print("\nVALID")


if __name__ == "__main__":
    main()
