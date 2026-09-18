from pathlib import Path
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

EVIDENCE_FILE = (
    BASE_DIR / "data" / "processed" / "references_evidence_142.csv"
)

MECHANISTIC_FILE = (
    BASE_DIR / "data" / "processed" / "references_mechanistic_evidence_142.csv"
)

PUBMED_FILE = (
    BASE_DIR / "data" / "processed" / "references_pubmed_enriched.csv"
)

OUTPUT_FILE = (
    BASE_DIR / "data" / "processed" / "phd_objective_evidence_v2.csv"
)

# ============================================================
# GENE PRIORITY
# ============================================================

PRIMARY_HUB_GENES = [
    "dnm1l",
    "opa1",
    "mfn1",
    "mfn2",
    "pink1",
    "prkn",
]

# DRP1 and PARK2 are aliases already represented in the
# ontology, but retained here as primary conceptual hubs.
PRIMARY_ALIAS_COLUMNS = [
    "has_dnm1l",
    "has_opa1",
    "has_mfn1",
    "has_mfn2",
    "has_pink1",
    "has_prkn",
]

SUPPORTING_GENES = [
    "has_mtfr1l",
    "has_sirt3",
]


# ============================================================
# HELPERS
# ============================================================

def safe_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def flag(row, column):
    return safe_int(row.get(column, 0)) > 0


def join_names(names):
    return "; ".join(names)


# ============================================================
# O1 — CONSERVED MITOCHONDRIAL SIGNATURE
# ============================================================
#
# O1 is intentionally conservative.
#
# A single paper cannot establish cross-dataset conservation
# simply because it contains the word "conserved".
#
# Current corpus-level evidence can support O1 only when the
# paper explicitly reports cross-dataset / multiple-model /
# reproducible mitochondrial signatures.
#
# This implementation therefore uses explicit terminology in
# the paper title/abstract where available.
# ============================================================

def score_o1(row):

    text = (
        str(row.get("title", ""))
        + " "
        + str(row.get("abstract", ""))
    ).lower()

    explicit_conservation_terms = [
        "conserved",
        "conservation",
        "consistent across",
        "consistently across",
        "reproducible across",
        "shared signature",
        "common signature",
        "cross-dataset",
        "cross dataset",
        "independent datasets",
        "multiple datasets",
        "multiple models",
        "across models",
    ]

    has_conservation = any(
        term in text
        for term in explicit_conservation_terms
    )

    has_mito = flag(row, "has_mitochondrial")
    has_omics = (
        flag(row, "has_transcriptomics")
        or flag(row, "has_single_cell")
        or flag(row, "has_proteomics")
        or flag(row, "has_metabolomics")
        or flag(row, "has_multiomics")
    )

    has_multiomics = (
        flag(row, "has_multiomics")
        or (
            flag(row, "has_transcriptomics")
            and (
                flag(row, "has_proteomics")
                or flag(row, "has_metabolomics")
            )
        )
    )

    if has_mito and has_multiomics and has_conservation:
        return (
            3,
            "Explicit conservation signal with mitochondrial and multi-omics evidence"
        )

    if has_mito and has_omics and has_conservation:
        return (
            2,
            "Explicit conservation signal with mitochondrial and omics evidence"
        )

    if has_mito and has_conservation:
        return (
            1,
            "Explicit mitochondrial conservation-related signal"
        )

    return (
        0,
        "No sufficient explicit cross-dataset conservation evidence"
    )


# ============================================================
# O2 — MULTI-OMICS INTEGRATION
# ============================================================

def score_o2(row):

    transcriptomics = flag(row, "has_transcriptomics") or flag(
        row, "has_single_cell"
    )

    proteomics = flag(row, "has_proteomics")
    metabolomics = flag(row, "has_metabolomics")
    explicit_multiomics = flag(row, "has_multiomics")

    modality_count = sum([
        transcriptomics,
        proteomics,
        metabolomics,
    ])

    if explicit_multiomics and modality_count >= 2:
        return (
            3,
            "Explicit multi-omics evidence with multiple modalities"
        )

    if modality_count >= 2:
        return (
            2,
            "Multiple omics modalities detected"
        )

    if explicit_multiomics:
        return (
            2,
            "Explicit multi-omics terminology detected"
        )

    if modality_count == 1:
        modality = (
            "transcriptomics"
            if transcriptomics
            else "proteomics"
            if proteomics
            else "metabolomics"
        )

        return (
            1,
            f"Single omics modality detected: {modality}"
        )

    return (
        0,
        "No strong omics integration evidence detected"
    )


# ============================================================
# O3 — HUB-GENE PRIORITY
# ============================================================

def score_o3(row):

    primary = []

    if flag(row, "has_dnm1l"):
        primary.append("DNM1L/DRP1")

    if flag(row, "has_opa1"):
        primary.append("OPA1")

    if flag(row, "has_mfn1"):
        primary.append("MFN1")

    if flag(row, "has_mfn2"):
        primary.append("MFN2")

    if flag(row, "has_pink1"):
        primary.append("PINK1")

    if flag(row, "has_prkn"):
        primary.append("PRKN/PARK2")

    supporting = []

    if flag(row, "has_mtfr1l"):
        supporting.append("MTFR1L")

    if flag(row, "has_sirt3"):
        supporting.append("SIRT3")

    mech = safe_int(
        row.get("mechanistic_evidence_level", 0)
    )

    if primary:
        if mech >= 3:
            return (
                3,
                f"Primary PhD hub gene(s) with strong mechanistic evidence: {join_names(primary)}"
            )

        if mech >= 2:
            return (
                2,
                f"Primary PhD hub gene(s) with moderate mechanistic evidence: {join_names(primary)}"
            )

        return (
            1,
            f"Primary PhD hub gene(s) detected: {join_names(primary)}"
        )

    if supporting:
        if mech >= 2:
            return (
                2,
                f"Supporting mitochondrial regulator with mechanistic evidence: {join_names(supporting)}"
            )

        return (
            1,
            f"Supporting mitochondrial regulator detected: {join_names(supporting)}"
        )

    return (
        0,
        "No prioritized PhD hub gene detected"
    )


# ============================================================
# O4 — MITOCHONDRIAL-SENESCENCE CONSERVATION
# ============================================================

def score_o4(row):

    mito = flag(row, "has_mitochondrial")
    sen = flag(row, "has_senescence")

    mito_process = (
        flag(row, "has_mitochondrial_dynamics")
        or flag(row, "has_mitophagy")
        or flag(row, "has_mitochondrial_quality_control")
        or flag(row, "has_mitochondrial_biogenesis")
        or flag(row, "has_mitochondrial_stress")
    )

    direct_link = (
        mito
        and sen
        and (
            flag(row, "has_mitochondrial_dynamics")
            or flag(row, "has_mitophagy")
            or flag(row, "has_mitochondrial_quality_control")
            or flag(row, "has_mitochondrial_stress")
        )
    )

    if direct_link and mito_process:
        return (
            2,
            "Direct mitochondrial-process and senescence evidence detected"
        )

    if mito and sen:
        return (
            1,
            "Mitochondrial and senescence evidence detected"
        )

    return (
        0,
        "Insufficient mitochondrial-senescence evidence"
    )


# ============================================================
# O5 — MECHANISTIC MITOCHONDRIAL → SENESCENCE CONNECTION
# ============================================================

def score_o5(row):

    mech_level = safe_int(
        row.get("mechanistic_evidence_level", 0)
    )

    perturbation = flag(row, "perturbation")
    rescue = flag(row, "rescue")
    mito_pheno = flag(row, "mito_phenotype")
    sen_pheno = flag(row, "senescence_phenotype")
    causal = flag(row, "causal_link")

    hub_present = (
        flag(row, "has_dnm1l")
        or flag(row, "has_opa1")
        or flag(row, "has_mfn1")
        or flag(row, "has_mfn2")
        or flag(row, "has_pink1")
        or flag(row, "has_prkn")
        or flag(row, "has_mtfr1l")
        or flag(row, "has_sirt3")
    )

    # Strongest: perturbation + mitochondrial phenotype +
    # senescence phenotype + rescue.
    if (
        perturbation
        and mito_pheno
        and sen_pheno
        and rescue
    ):
        return (
            3,
            "Perturbation, mitochondrial phenotype, senescence phenotype and rescue detected"
        )

    # Strong direct mechanism.
    if (
        perturbation
        and mito_pheno
        and sen_pheno
        and (causal or mech_level >= 3)
    ):
        return (
            3,
            "Direct perturbational mitochondrial-senescence mechanism detected"
        )

    # Mechanistic evidence with a prioritized hub.
    if (
        mech_level >= 3
        and mito_pheno
        and sen_pheno
        and hub_present
    ):
        return (
            2,
            "Strong mechanistic evidence involving a prioritized mitochondrial regulator"
        )

    # General mechanistic evidence connecting both phenotypes.
    if (
        mech_level >= 2
        and mito_pheno
        and sen_pheno
    ):
        return (
            2,
            "Mechanistic mitochondrial and senescence phenotypes detected"
        )

    # Association only.
    if (
        mito_pheno
        and sen_pheno
    ):
        return (
            1,
            "Mitochondrial and senescence phenotypes detected without strong causal evidence"
        )

    return (
        0,
        "Insufficient mechanistic mitochondrial-senescence evidence"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    for path in [EVIDENCE_FILE, MECHANISTIC_FILE]:
        if not path.exists():
            raise FileNotFoundError(
                f"Required file not found: {path}"
            )

    evidence = pd.read_csv(
        EVIDENCE_FILE
    ).fillna("")

    mechanistic = pd.read_csv(
        MECHANISTIC_FILE
    ).fillna("")

    # --------------------------------------------------------
    # Normalize PMID
    # --------------------------------------------------------

    evidence["pmid"] = (
        evidence["pmid"]
        .astype(str)
        .str.strip()
    )

    mechanistic["pmid"] = (
        mechanistic["pmid"]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Merge the two 142-paper evidence layers.
    # Evidence layer is the authoritative corpus universe.
    # --------------------------------------------------------

    mech_columns = [
        "pmid",
        "perturbation",
        "rescue",
        "mito_phenotype",
        "senescence_phenotype",
        "causal_link",
        "mechanistic_evidence_level",
        "mechanistic_score",
    ]

    df = evidence.merge(
        mechanistic[mech_columns],
        on="pmid",
        how="left",
        suffixes=("", "_mech"),
    )

    df = df.fillna("")

    # --------------------------------------------------------
    # Analyze
    # --------------------------------------------------------

    results = []

    for _, row in df.iterrows():

        o1, o1_reason = score_o1(row)
        o2, o2_reason = score_o2(row)
        o3, o3_reason = score_o3(row)
        o4, o4_reason = score_o4(row)
        o5, o5_reason = score_o5(row)

        primary_names = []

        if flag(row, "has_dnm1l"):
            primary_names.append("DNM1L/DRP1")
        if flag(row, "has_opa1"):
            primary_names.append("OPA1")
        if flag(row, "has_mfn1"):
            primary_names.append("MFN1")
        if flag(row, "has_mfn2"):
            primary_names.append("MFN2")
        if flag(row, "has_pink1"):
            primary_names.append("PINK1")
        if flag(row, "has_prkn"):
            primary_names.append("PRKN/PARK2")

        supporting_names = []

        if flag(row, "has_mtfr1l"):
            supporting_names.append("MTFR1L")
        if flag(row, "has_sirt3"):
            supporting_names.append("SIRT3")

        if primary_names:
            hub_priority = "Primary"
            hub_names = join_names(primary_names)
        elif supporting_names:
            hub_priority = "Supporting"
            hub_names = join_names(supporting_names)
        else:
            hub_priority = "None"
            hub_names = ""

        results.append({
            "pmid": row.get("pmid", ""),
            "title": row.get("title", ""),
            "hub_gene_priority": hub_priority,
            "hub_gene_names": hub_names,

            "O1_conserved_signature_level": o1,
            "O1_conserved_signature_reason": o1_reason,

            "O2_multiomics_integration_level": o2,
            "O2_multiomics_integration_reason": o2_reason,

            "O3_hub_gene_level": o3,
            "O3_hub_gene_reason": o3_reason,

            "O4_mito_senescence_conservation_level": o4,
            "O4_mito_senescence_conservation_reason": o4_reason,

            "O5_mechanistic_connection_level": o5,
            "O5_mechanistic_connection_reason": o5_reason,
        })

    result_df = pd.DataFrame(results)

    result_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # --------------------------------------------------------
    # Audit
    # --------------------------------------------------------

    print("=" * 70)
    print("Objective Evidence Engine V2 — 142-Paper Corpus")
    print("=" * 70)

    print(f"Input evidence rows: {len(evidence)}")
    print(f"Mechanistic rows: {len(mechanistic)}")
    print(f"Output rows: {len(result_df)}")
    print(f"Unique PMIDs: {result_df['pmid'].nunique()}")
    print(f"Saved: {OUTPUT_FILE}")

    print("\nObjective level distributions:")

    objective_columns = [
        "O1_conserved_signature_level",
        "O2_multiomics_integration_level",
        "O3_hub_gene_level",
        "O4_mito_senescence_conservation_level",
        "O5_mechanistic_connection_level",
    ]

    for column in objective_columns:
        print(f"\n{column}")
        print(
            result_df[column]
            .value_counts()
            .sort_index()
            .to_string()
        )

    print("\nHub-priority distribution:")
    print(
        result_df["hub_gene_priority"]
        .value_counts()
        .to_string()
    )

    print("\nIntegrity:")
    valid_pmid_count = (
        result_df["pmid"]
        .replace("", pd.NA)
        .dropna()
        .nunique()
    )

    blank_pmid_count = (
        result_df["pmid"]
        .isna()
        .sum()
        + (result_df["pmid"].astype(str).str.strip() == "").sum()
    )

    print(
        "PASS"
        if len(result_df) == 142
        and valid_pmid_count == 141
        and blank_pmid_count == 1
        else "CHECK REQUIRED"
    )

if __name__ == "__main__":
    main()
