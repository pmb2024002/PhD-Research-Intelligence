from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

EVIDENCE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phd_evidence_strength_v1.csv"
)

RANKED_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "pubmed_ranked.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "phd_objective_evidence_v1.csv"
)


def load_data():
    evidence = pd.read_csv(EVIDENCE_FILE).fillna("")
    ranked = pd.read_csv(RANKED_FILE).fillna("")

    columns = [
        "pmid",
        "title",
        "mechanistic_evidence",
        "evidence_tier",
    ]

    ranked_subset = ranked[columns]

    df = evidence.merge(
        ranked_subset,
        on=["pmid", "title"],
        how="left"
    )

    return df


def objective_o1(row):
    """
    O1: Conserved mitochondrial dysfunction signatures

    Stronger evidence requires:
    - mitochondrial evidence
    - omics evidence
    - conservation/cross-dataset/meta-analysis signal
    """

    mito = int(row["mitochondrial_process_evidence_level"])
    omics = int(row["omics_evidence_level"])

    text = (
        str(row["title"]) + " "
        + str(row.get("mechanistic_evidence", ""))
    ).lower()

    conservation_terms = [
        "conserved",
        "cross-dataset",
        "cross dataset",
        "meta-analysis",
        "meta analysis",
        "signature",
        "signatures",
    ]

    conservation = any(term in text for term in conservation_terms)

    if mito >= 2 and omics >= 2 and conservation:
        return 3, "Mitochondrial evidence + multi-omics + conservation signal"

    if mito >= 2 and omics >= 1 and conservation:
        return 2, "Mitochondrial evidence + omics + conservation signal"

    if mito >= 2 and omics >= 1:
        return 1, "Mitochondrial and omics evidence detected"

    return 0, "Insufficient evidence for conserved mitochondrial signatures"


def objective_o2(row):
    """
    O2: Transcriptomic-proteomic / multi-omics integration

    0 = no omics
    1 = one modality
    2 = multiple modalities
    3 = multiple modalities with explicit integration evidence
    """

    omics_level = int(row["omics_evidence_level"])
    modalities = str(row["omics_evidence"]).lower()
    text = str(row["title"]).lower()

    integration_terms = [
        "multi-omics",
        "multiomics",
        "integrated multi-omics",
        "integrative multi-omics",
        "integration",
        "integrated analysis",
        "cross-omics",
    ]

    integration = any(
        term in text or term in modalities
        for term in integration_terms
    )

    if omics_level >= 2 and integration:
        return 3, "Multiple omics modalities with integration signal"

    if omics_level >= 2:
        return 2, "Multiple omics modalities detected"

    if omics_level == 1:
        return 1, "Single omics modality detected"

    return 0, "No meaningful omics evidence detected"


def objective_o3(row):
    """
    O3: Mitochondrial hub genes

    Uses the evidence-strength level already calculated
    by the evidence engine.
    """

    level = int(row["gene_evidence_level"])
    genes = str(row["gene_evidence_genes"])

    if level >= 3:
        return 3, f"Strong mechanistic evidence for priority gene(s): {genes}"

    if level == 2:
        return 2, f"Priority gene(s) investigated/associated: {genes}"

    if level == 1:
        return 1, f"Priority gene(s) mentioned: {genes}"

    return 0, "No priority hub gene evidence detected"


def objective_o4(row):
    """
    O4: Conserved mitochondrial pathways

    Requires mitochondrial-process evidence and
    increases strength when linked to senescence.
    """

    mito = int(row["mitochondrial_process_evidence_level"])
    sen = int(row["senescence_evidence_level"])

    processes = str(row["mitochondrial_process_evidence"])

    if mito >= 3 and sen >= 2:
        return 3, f"Strong mitochondrial-process evidence linked to senescence: {processes}"

    if mito >= 2 and sen >= 2:
        return 2, f"Mitochondrial processes investigated in a senescence context: {processes}"

    if mito >= 1:
        return 1, f"Mitochondrial process evidence detected: {processes}"

    return 0, "No meaningful mitochondrial pathway evidence detected"


def objective_o5(row):
    """
    O5: Mechanistic mitochondrial-senescence connection

    Requires:
    - mitochondrial evidence
    - senescence evidence
    - text-based mechanistic evidence

    Mechanistic evidence remains explicitly text-based.
    """

    mito = int(row["mitochondrial_process_evidence_level"])
    sen = int(row["senescence_evidence_level"])
    mech = str(row["mechanistic_evidence"]).strip()

    has_mechanistic_evidence = bool(mech)

    if mito >= 3 and sen >= 3 and has_mechanistic_evidence:
        return 3, "Strong text-based mitochondrial-senescence mechanistic signal"

    if mito >= 2 and sen >= 2 and has_mechanistic_evidence:
        return 2, "Mitochondrial + senescence evidence with text-based mechanistic signal"

    if mito >= 2 and sen >= 1:
        return 1, "Mitochondrial and senescence evidence detected, but mechanistic support is limited"

    return 0, "Insufficient evidence for a mitochondrial-senescence mechanism"


def analyze_paper(row):
    o1, o1_reason = objective_o1(row)
    o2, o2_reason = objective_o2(row)
    o3, o3_reason = objective_o3(row)
    o4, o4_reason = objective_o4(row)
    o5, o5_reason = objective_o5(row)

    return {
        "pmid": row["pmid"],
        "title": row["title"],

        "O1_conserved_signatures_level": o1,
        "O1_conserved_signatures_reason": o1_reason,

        "O2_multiomics_integration_level": o2,
        "O2_multiomics_integration_reason": o2_reason,

        "O3_hub_genes_level": o3,
        "O3_hub_genes_reason": o3_reason,

        "O4_conserved_pathways_level": o4,
        "O4_conserved_pathways_reason": o4_reason,

        "O5_mechanistic_connection_level": o5,
        "O5_mechanistic_connection_reason": o5_reason,
    }


def main():
    if not EVIDENCE_FILE.exists():
        raise FileNotFoundError(
            f"Evidence file not found: {EVIDENCE_FILE}"
        )

    if not RANKED_FILE.exists():
        raise FileNotFoundError(
            f"Ranked file not found: {RANKED_FILE}"
        )

    df = load_data()

    results = [
        analyze_paper(row)
        for _, row in df.iterrows()
    ]

    out = pd.DataFrame(results)

    out.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("Objective Evidence Engine v1")
    print("=" * 60)
    print(f"Input papers: {len(df)}")
    print(f"Output: {OUTPUT_FILE}")

    print("\nObjective level distributions:")

    objective_columns = [
        "O1_conserved_signatures_level",
        "O2_multiomics_integration_level",
        "O3_hub_genes_level",
        "O4_conserved_pathways_level",
        "O5_mechanistic_connection_level",
    ]

    for column in objective_columns:
        print(f"\n{column}")
        print(
            out[column]
            .value_counts()
            .sort_index()
            .to_string()
        )

    print("\nVALID")


if __name__ == "__main__":
    main()
