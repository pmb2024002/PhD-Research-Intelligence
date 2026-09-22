from pathlib import Path
import pandas as pd
import numpy as np
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RANKED_FILE = PROJECT_ROOT / "data" / "processed" / "pubmed_ranked.csv"
SEMANTIC_FILE = PROJECT_ROOT / "data" / "processed" / "pubmed_semantic_ranked.csv"
MECHANISTIC_FILE = PROJECT_ROOT / "data" / "processed" / "phd_mechanistic_strength_v2.csv"
UTILITY_FILE = PROJECT_ROOT / "data" / "processed" / "phd_utility_features_v2.csv"
OBJECTIVE_FILE = PROJECT_ROOT / "data" / "processed" / "phd_objective_evidence_v2.csv"
FEEDBACK_FILE = PROJECT_ROOT / "data" / "processed" / "phd_feedback_dataset.csv"

OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "phd_prus_v2.csv"
ONTOLOGY_FILE = PROJECT_ROOT / "config" / "phd_relevance_ontology.yaml"


def load_ontology():
    with open(ONTOLOGY_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def safe_numeric(series):
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def contains_term(text, term):
    text = clean_text(text).lower()
    term = clean_text(term).lower()

    if not text or not term:
        return False

    return term in text


def count_items(value):
    text = clean_text(value)

    if not text:
        return 0

    return len([
        item for item in text.split(";")
        if item.strip()
    ])

def calculate_rsa(row, ontology=None):
    """
    Research Scope Alignment (RSA)

    Maximum: 25 points

    RSA evaluates how directly a paper contributes to the
    user's PhD research question.

    Tier 1: Direct core alignment
    Tier 2: Strong transferable alignment
    Tier 3: Supporting/peripheral alignment
    """

    core = clean_text(row.get("core_evidence", "")).lower()
    strong = clean_text(row.get("strong_context", "")).lower()
    peripheral = clean_text(row.get("peripheral_context", "")).lower()
    mechanism = clean_text(row.get("mechanism_label", "")).lower()

    primary_gene = clean_text(
        row.get("primary_hub_genes", "")
    ).lower()

    mitochondrial = clean_text(
        row.get("core_evidence", "")
    ).lower()

    senescence = clean_text(
        row.get("core_evidence", "")
    ).lower()
    score = 0.0
    reasons = []

    # --------------------------------------------------------
    # 1. Direct mitochondrial–senescence relationship
    # --------------------------------------------------------

    direct_mito = (
        "mitochondrial dysfunction" in core
        or "mitochondrial dysfunction" in mechanism
    )

    direct_senescence = (
        "cellular senescence" in core
        or "cellular senescence" in senescence
    )

    if direct_mito and direct_senescence:
        score += 4.0
        reasons.append(
            "Direct mitochondrial dysfunction–senescence alignment"
        )

    # --------------------------------------------------------
    # 2. Relevant mitochondrial mechanism
    # --------------------------------------------------------

    if ontology is not None:
        mechanism_terms = [
            str(x).lower()
            for x in ontology["research_scope"]["core_mitochondrial_processes"]
        ]
    else:
        mechanism_terms = [
            "mitophagy",
            "mitochondrial quality control",
            "mitochondrial dynamics",
            "mitochondrial fission",
            "mitochondrial fusion",
            "mitochondrial biogenesis",
            "mitochondrial ros",
            "mitochondrial membrane potential",
        ]

    if any(term in mitochondrial for term in mechanism_terms):
        score += 5.0
        reasons.append(
            "Relevant mitochondrial mechanism"
        )

    # --------------------------------------------------------
    # 3. Primary PhD hub gene
    # --------------------------------------------------------

    if primary_gene and primary_gene not in {"nan", "none"}:
        score += 4.0
        reasons.append(
            "Primary mitochondrial hub-gene involvement"
        )

    # --------------------------------------------------------
    # 4. Relevant experimental model
    # --------------------------------------------------------

    model_relevance = clean_text(
        row.get("model_relevance_tier", "")
    ).lower()

    has_fibroblast = str(
        row.get("has_fibroblast_model", 0)
    ).lower() in {"1", "1.0", "true"}

    if has_fibroblast:
        score += 3.0
        reasons.append(
            "PhD-relevant fibroblast model"
        )

    elif model_relevance in {"1", "tier 1"}:
        score += 1.0
        reasons.append(
            "Transferable experimental model"
        )

    elif model_relevance in {"2", "tier 2"}:
        score += 1.0
        reasons.append(
            "Secondary model relevance"
        )

    # --------------------------------------------------------
    # 5. Mechanistic evidence
    # --------------------------------------------------------

    mechanistic_level = safe_numeric(
        pd.Series([row.get("mechanistic_strength_level", 0)])
    ).iloc[0]

    if mechanistic_level >= 4:
        score += 3.0
        reasons.append(
            "Strong mechanistic evidence"
        )

    elif mechanistic_level >= 3:
        score += 2.0
        reasons.append(
            "Moderate mechanistic evidence"
        )

    # --------------------------------------------------------
    # 6. Peripheral context penalty
    # --------------------------------------------------------

    peripheral_count = count_items(peripheral)

    if peripheral_count >= 2:
        score -= 4.0
        reasons.append(
            "Multiple peripheral research contexts"
        )

    elif peripheral_count == 1:
        score -= 2.0
        reasons.append(
            "Peripheral research context"
        )

    score = max(0.0, min(score, 25.0))

    # --------------------------------------------------------
    # RSA tier
    # --------------------------------------------------------

    if score >= 18:
        tier = "Tier 1 — Direct Core Alignment"

    elif score >= 12:
        tier = "Tier 2 — Strong Transferable Alignment"

    elif score >= 6:
        tier = "Tier 3 — Supporting Alignment"

    else:
        tier = "Tier 4 — Peripheral / Low Alignment"

    return score, tier, reasons

def calculate_rsa_v2(row, ontology, rsa_rules):
    """
    RSA V2 — PhD-specific Research Scope Alignment.

    This is intentionally separate from RSA V1 so both systems
    can be compared before V2 is adopted.
    """
    core = clean_text(row.get("core_evidence", "")).lower()
    strong = clean_text(row.get("strong_context", "")).lower()
    supporting = clean_text(row.get("supporting_context", "")).lower()
    peripheral = clean_text(row.get("peripheral_context", "")).lower()
    mechanism_label = clean_text(row.get("mechanism_label", "")).lower()
    hub_genes = clean_text(row.get("primary_hub_genes", "")).lower()

    score = 0.0
    reasons = []

    components = rsa_rules.get("components", {})
    scope = ontology.get("research_scope", {})

    mito_terms = [str(x).lower() for x in scope.get("core_mitochondrial_processes", [])]
    sen_terms = [str(x).lower() for x in scope.get("senescence_processes", [])]
    hub_terms = [str(x).lower() for x in scope.get("priority_hubs", [])]
    omics_terms = [str(x).lower() for x in scope.get("omics", [])]
    text = " ".join([core, strong, supporting, mechanism_label])

    direct_mito = "mitochondrial dysfunction" in text
    direct_sen = any(term in text for term in sen_terms if term)

    mito_matches = [term for term in mito_terms if term and term in text]
    matched_hubs = [gene for gene in hub_terms if gene and gene in hub_genes]

    mech_level = float(pd.to_numeric(pd.Series([row.get("mechanistic_strength_level", 0)]), errors="coerce").fillna(0).iloc[0])
    has_fibroblast = str(row.get("has_fibroblast_model", 0)).lower() in {"1", "1.0", "true"}
    omics_matches = [term for term in omics_terms if term and term in text]

    specific_features = 0
    if mito_matches:
        specific_features += 1
    if matched_hubs:
        specific_features += 1
    if mech_level >= 3:
        specific_features += 1
    if has_fibroblast:
        specific_features += 1
    if omics_matches:
        specific_features += 1

    if direct_mito and direct_sen:
        score += float(components.get("direct_mito_senescence", 0))
        reasons.append("Direct mitochondrial dysfunction–senescence relationship")

        gating = rsa_rules.get("scope_gating", {})
        if gating.get("direct_mito_senescence_requires_specificity", False) and specific_features == 0:
            score -= float(components.get("direct_mito_senescence", 0))
            reasons.append("Generic mitochondrial-senescence association gated: no PhD-specific evidence")

    mito_matches = [term for term in mito_terms if term and term in text]
    if mito_matches:
        score += float(components.get("mitochondrial_mechanism", 0))
        reasons.append("Mitochondrial mechanism: " + ", ".join(mito_matches[:4]))

    matched_hubs = [gene for gene in hub_terms if gene and gene in hub_genes]
    if matched_hubs:
        score += float(components.get("primary_hub_gene", 0))
        reasons.append("Priority hub-gene involvement: " + ", ".join(matched_hubs))

    mech_level = float(pd.to_numeric(pd.Series([row.get("mechanistic_strength_level", 0)]), errors="coerce").fillna(0).iloc[0])
    if mech_level >= 3:
        score += float(components.get("mechanistic_evidence", 0))
        reasons.append("Strong mechanistic evidence")

    has_fibroblast = str(row.get("has_fibroblast_model", 0)).lower() in {"1", "1.0", "true"}
    if has_fibroblast:
        score += float(components.get("fibroblast_model", 0))
        reasons.append("PhD-relevant fibroblast model")

    omics_matches = [term for term in omics_terms if term and term in text]
    if omics_matches:
        score += float(components.get("multiomics_or_omics", 0))
        reasons.append("Relevant omics evidence")

    peripheral_count = count_items(peripheral)
    if peripheral_count:
        score -= float(components.get("peripheral_context_penalty", 0))
        reasons.append("Peripheral research context")

    score = max(0.0, score)

    thresholds = rsa_rules.get("thresholds", {})
    if score >= float(thresholds.get("R1_direct_core", 20)):
        tier = "R1 — Direct Core Relevance"
    elif score >= float(thresholds.get("R2_direct_mechanistic", 14)):
        tier = "R2 — Direct Mechanistic Relevance"
    elif score >= float(thresholds.get("R3_computational_multiomics", 9)):
        tier = "R3 — Computational / Multi-Omics Relevance"
    elif score >= float(thresholds.get("R4_transferable", 6)):
        tier = "R4 — Transferable Biological Relevance"
    elif score >= float(thresholds.get("R5_supporting", 3)):
        tier = "R5 — Supporting Background Relevance"
    else:
        tier = "R6 — Peripheral / Low Relevance"

    return score, tier, reasons

def test_rsa():
    ontology = load_ontology()
    df = pd.read_csv(RANKED_FILE)

    mechanistic = pd.read_csv(MECHANISTIC_FILE)
    utility = pd.read_csv(UTILITY_FILE)
    objective = pd.read_csv(OBJECTIVE_FILE)

    df["pmid"] = df["pmid"].astype(str).str.strip()
    mechanistic["pmid"] = mechanistic["pmid"].astype(str).str.strip()
    utility["pmid"] = utility["pmid"].astype(str).str.strip()

    df = df.merge(
        mechanistic[
            [
                "pmid",
                "mechanistic_strength_level",
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
                "primary_hub_genes",
                "model_relevance_tier",
                "has_fibroblast_model",
            ]
        ],
        on="pmid",
        how="left",
    )

    results = []

    objective["pmid"] = objective["pmid"].astype(str).str.strip()

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

    for _, row in df.iterrows():
        score, tier, reasons = calculate_rsa(row, ontology)

        results.append(
            {
                "pmid": row["pmid"],
                "title": row["title"],
                "RSA": score,
                "RSA_tier": tier,
                "RSA_reasons": "; ".join(reasons),
            }
        )

    result_df = pd.DataFrame(results)

    print("=" * 70)
    print("RSA V1 TEST")
    print("=" * 70)
    print(
        result_df[
            [
                "pmid",
                "RSA",
                "RSA_tier",
                "RSA_reasons",
            ]
        ]
        .sort_values("RSA", ascending=False)
        .to_string(index=False)
    )


if __name__ == "__main__":
    test_rsa()
