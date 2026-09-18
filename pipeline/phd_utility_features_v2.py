from pathlib import Path
import pandas as pd
import yaml
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_FILE = PROJECT_ROOT / "data" / "processed" / "references_pubmed_enriched.csv"
EVIDENCE_FILE = PROJECT_ROOT / "data" / "processed" / "references_evidence_142.csv"
MECHANISTIC_FILE = PROJECT_ROOT / "data" / "processed" / "references_mechanistic_evidence_142.csv"
OBJECTIVE_FILE = PROJECT_ROOT / "data" / "processed" / "phd_objective_evidence_v2.csv"
FEEDBACK_FILE = PROJECT_ROOT / "data" / "processed" / "phd_feedback_dataset.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "phd_utility_features_v2.csv"

PRIMARY_GENES = {
    "dnm1l",
    "drp1",
    "opa1",
    "mfn1",
    "mfn2",
    "pink1",
    "prkn",
    "park2",
}

SUPPORTING_GENES = {
    "sirt3",
    "mtfr1l",
}

def normalize(value):
    if pd.isna(value):
        return ""
    return str(value).strip().lower()

def parse_semicolon(value):
    if pd.isna(value):
        return set()
    return {
        normalize(x)
        for x in str(value).split(";")
        if normalize(x)
    }

def contains_any(text, terms):
    text = normalize(text)
    return any(term in text for term in terms)
def main():
    required_files = [
        RAW_FILE,
        EVIDENCE_FILE,
        MECHANISTIC_FILE,
        OBJECTIVE_FILE,
        FEEDBACK_FILE,
    ]
    for path in required_files:
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    raw = pd.read_csv(RAW_FILE).fillna("")
    evidence = pd.read_csv(EVIDENCE_FILE).fillna("")
    mechanistic = pd.read_csv(MECHANISTIC_FILE).fillna("")
    objective = pd.read_csv(OBJECTIVE_FILE).fillna("")
    feedback = pd.read_csv(FEEDBACK_FILE).fillna("")

    # Use the original PubMed title + abstract as the primary
    # biological-text source for feature extraction.
    raw["full_text"] = (
        raw["title"].astype(str)
        + " "
        + raw["abstract"].astype(str)
    ).map(normalize)

    text_by_pmid = dict(zip(raw["pmid"].astype(str), raw["full_text"]))


    objective_cols = [
        "pmid",
        "O1_conserved_signature_level",
        "O2_multiomics_integration_level",
        "O3_hub_gene_level",
        "O4_mito_senescence_conservation_level",
        "O5_mechanistic_connection_level",
    ]

    feedback_cols = [
        "pmid",
        "user_relevance",
        "user_reason",
    ]

    # ---------------------------------------------------------
    # Normalize PMID datatype across all evidence layers
    # ---------------------------------------------------------

    for frame in [raw, evidence, mechanistic, objective, feedback]:
        frame["pmid"] = (
            frame["pmid"]
            .astype("string")
            .str.strip()
        )

    df = raw[
        [
            "pmid",
            "title",
            "abstract",
        ]
    ].copy()

    df = df.merge(
        evidence,
        on="pmid",
        how="left",
        suffixes=("", "_evidence"),
    )

    df = df.merge(
        mechanistic,
        on="pmid",
        how="left",
        suffixes=("", "_mechanistic"),
    )

    df = df.merge(
        objective[objective_cols],
        on="pmid",
        how="left",
        suffixes=("", "_objective"),
    )

    df = df.merge(
        feedback[feedback_cols],
        on="pmid",
        how="left",
    )
    df["pmid"] = df["pmid"].astype(str)

    rows = []

    for _, row in df.iterrows():
        pmid = str(row["pmid"])
        text = text_by_pmid.get(pmid, "")

        genes = set()

        if row.get("has_dnm1l", 0):
            genes.add("dnm1l")

        if row.get("has_opa1", 0):
            genes.add("opa1")

        if row.get("has_mfn1", 0):
            genes.add("mfn1")

        if row.get("has_mfn2", 0):
            genes.add("mfn2")

        if row.get("has_pink1", 0):
            genes.add("pink1")

        if row.get("has_prkn", 0):
            genes.add("prkn")

        if row.get("has_mtfr1l", 0):
            genes.add("mtfr1l")

        if row.get("has_sirt3", 0):
            genes.add("sirt3")

        # ---------------------------------------------------------
        # Gene-level evidence
        # ---------------------------------------------------------
        primary_genes = genes & PRIMARY_GENES
        supporting_genes = genes & SUPPORTING_GENES

        # Also inspect the original PubMed text so that gene
        # detection is not dependent only on the upstream matcher.
        primary_text_hits = {
            gene for gene in PRIMARY_GENES
            if re.search(r"\b" + re.escape(gene) + r"\b", text)
        }

        supporting_text_hits = {
            gene for gene in SUPPORTING_GENES
            if re.search(r"\b" + re.escape(gene) + r"\b", text)
        }

        primary_genes = primary_genes | primary_text_hits
        supporting_genes = supporting_genes | supporting_text_hits

        # ---------------------------------------------------------
        # Senescence evidence
        # ---------------------------------------------------------
        direct_senescence_terms = [
            "cellular senescence",
            "replicative senescence",
            "stress-induced premature senescence",
            "stress-induced senescence",
            "therapy-induced senescence",
            "irradiation-induced senescence",
            "dna damage-induced senescence",
            "senescent cells",
            "senescence phenotype",
        ]

        has_direct_senescence = contains_any(
            text,
            direct_senescence_terms,
        )

        # ---------------------------------------------------------
        # Mitochondrial evidence
        # ---------------------------------------------------------
        mitochondrial_terms = [
            "mitochondrial dysfunction",
            "mitochondrial function",
            "mitochondrial dynamics",
            "mitochondrial fission",
            "mitochondrial fusion",
            "mitophagy",
            "mitochondrial quality control",
            "mitochondrial biogenesis",
            "mitochondrial ros",
            "mitochondrial reactive oxygen species",
            "mitochondrial membrane potential",
            "mitochondrial homeostasis",
            "mitochondrial proteostasis",
        ]

        mitochondrial_process_terms = [
            "mitochondrial dynamics",
            "mitochondrial fission",
            "mitochondrial fusion",
            "mitophagy",
            "mitochondrial quality control",
            "mitochondrial biogenesis",
            "mitochondrial proteostasis",
            "mitochondrial membrane potential",
        ]

        has_mitochondrial_evidence = contains_any(
            text,
            mitochondrial_terms,
        )

        has_mitochondrial_process = contains_any(
            text,
            mitochondrial_process_terms,
        )

        # A broader mitochondrial-senescence link is useful for
        # contextual papers even when no specific hub gene/process
        # is detected by the upstream evidence matcher.
        has_mito_senescence_link = (
            has_mitochondrial_evidence
            and has_direct_senescence
            and (
                has_mitochondrial_process
                or bool(primary_genes)
            )
        )

        # ---------------------------------------------------------
        # Fibroblast / experimental model relevance
        # ---------------------------------------------------------
        fibroblast_terms = [
            "imr-90",
            "imr90",
            "human fibroblast",
            "human fibroblasts",
            "fibroblast",
            "fibroblasts",
        ]

        has_fibroblast_model = contains_any(
            text,
            fibroblast_terms,
        )

        # More specific model hierarchy.
        if contains_any(text, ["imr-90", "imr90"]):
            model_tier = 3
        elif contains_any(
            text,
            ["human fibroblast", "human fibroblasts"],
        ):
            model_tier = 3
        elif contains_any(
            text,
            ["fibroblast", "fibroblasts"],
        ):
            model_tier = 2
        elif contains_any(
            text,
            [
                "rpe",
                "retinal pigment epithelial",
                "ovarian granulosa",
                "bmsc",
                "bone marrow stromal",
                "chondrocyte",
                "chondrocytes",
                "mouse embryonic fibroblast",
                "mouse embryonic fibroblasts",
            ],
        ):
            model_tier = 2
        elif contains_any(
            text,
            [
                "skeletal muscle",
                "myocardial",
                "cardiovascular",
                "kidney",
                "renal",
                "nucleus pulposus",
            ],
        ):
            model_tier = 1
        else:
            model_tier = 0

        # ---------------------------------------------------------
        # Omics detection from the original PubMed text
        # ---------------------------------------------------------
        transcriptomics_terms = [
            "rna-seq",
            "rna seq",
            "rna sequencing",
            "transcriptomics",
            "transcriptome",
            "transcriptomic",
            "transcriptional profiling",
            "transcriptional analysis",
            "gene expression profiling",
        ]

        proteomics_terms = [
            "proteomics",
            "proteome",
            "proteomic",
            "mass spectrometry",
        ]

        metabolomics_terms = [
            "metabolomics",
            "metabolome",
            "metabolomic",
        ]

        multiomics_terms = [
            "multi-omics",
            "multiomics",
            "multi-omic",
            "integrated omics",
            "multi omics",
        ]

        omics_modalities = set()

        if contains_any(text, transcriptomics_terms):
            omics_modalities.add("transcriptomics")

        if contains_any(text, proteomics_terms):
            omics_modalities.add("proteomics")

        if contains_any(text, metabolomics_terms):
            omics_modalities.add("metabolomics")

        explicit_multiomics = contains_any(
            text,
            multiomics_terms,
        )

        has_multiomics = (
            len(omics_modalities) >= 2
            or explicit_multiomics
        )

        # ---------------------------------------------------------
        # Mechanistic signal
        # ---------------------------------------------------------
        mechanistic_terms = [
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
            "pharmacological",
        ]

        has_mechanistic_signal = contains_any(
            text,
            mechanistic_terms,
        )

        # ---------------------------------------------------------
        # Objective evidence levels
        # ---------------------------------------------------------
        def safe_int(value):
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return 0

        o1 = safe_int(row.get("O1_conserved_signature_level", 0))
        o2 = safe_int(row.get("O2_multiomics_integration_level", 0))
        o3 = safe_int(row.get("O3_hub_gene_level", 0))
        o4 = safe_int(row.get("O4_mito_senescence_conservation_level", 0))
        o5 = safe_int(row.get("O5_mechanistic_connection_level", 0))

        rows.append({
            "pmid": pmid,
            "title": row["title"],
            "user_relevance": row.get("user_relevance", ""),
            "user_reason": row.get("user_reason", ""),

            "primary_hub_genes": "; ".join(sorted(primary_genes)),
            "supporting_genes": "; ".join(sorted(supporting_genes)),

            "has_primary_hub_gene": int(bool(primary_genes)),
            "has_supporting_gene": int(bool(supporting_genes)),

            "has_mitochondrial_evidence": int(
                has_mitochondrial_evidence
            ),

            "has_mitochondrial_process": int(
                has_mitochondrial_process
            ),

            "has_direct_senescence_evidence": int(
                has_direct_senescence
            ),

            "has_mito_senescence_link": int(
                has_mito_senescence_link
            ),

            "has_fibroblast_model": int(
                has_fibroblast_model
            ),

            "model_relevance_tier": model_tier,

            "omics_modalities": "; ".join(
                sorted(omics_modalities)
            ),

            "omics_modality_count": len(
                omics_modalities
            ),

            "has_multiomics": int(
                has_multiomics
            ),

            "has_mechanistic_signal": int(
                has_mechanistic_signal
            ),

            "matched_direct_references": safe_int(
                row.get("matched_direct_references", 0)
            ),

            "matched_mechanistic_references": safe_int(
                row.get("matched_mechanistic_references", 0)
            ),

            "objective_O1": o1,
            "objective_O2": o2,
            "objective_O3": o3,
            "objective_O4": o4,
            "objective_O5": o5,
        })

    out = pd.DataFrame(rows)

    out.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("PhD Research Utility Feature Engine V2.1")
    print("=" * 65)

    print(f"Input papers: {len(out)}")
    print(f"Output: {OUTPUT_FILE}")

    print("\nFeature prevalence:")

    feature_columns = [
        "has_primary_hub_gene",
        "has_supporting_gene",
        "has_mitochondrial_evidence",
        "has_mitochondrial_process",
        "has_direct_senescence_evidence",
        "has_mito_senescence_link",
        "has_fibroblast_model",
        "has_multiomics",
        "has_mechanistic_signal",
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
