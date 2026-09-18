from pathlib import Path
import pandas as pd
import numpy as np
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RANKED_FILE = PROJECT_ROOT / "data" / "processed" / "pubmed_semantic_ranked.csv"
SEMANTIC_FILE = PROJECT_ROOT / "data" / "processed" / "pubmed_semantic_ranked.csv"
MECHANISTIC_FILE = PROJECT_ROOT / "data" / "processed" / "references_mechanistic_evidence_142.csv"
UTILITY_FILE = PROJECT_ROOT / "data" / "processed" / "phd_utility_features_v2.csv"
OBJECTIVE_FILE = PROJECT_ROOT / "data" / "processed" / "phd_objective_evidence_v2.csv"
FEEDBACK_FILE = PROJECT_ROOT / "data" / "processed" / "phd_feedback_dataset.csv"

OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "phd_prus_v2.csv"
ONTOLOGY_FILE = PROJECT_ROOT / "config" / "phd_relevance_ontology.yaml"
RSA_RULES_FILE = PROJECT_ROOT / "config" / "phd_rsa_rules.yaml"


def load_ontology():
    with open(ONTOLOGY_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_rsa_rules():
    with open(RSA_RULES_FILE, "r", encoding="utf-8") as f:
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
    # Validated 142-paper evidence
    has_mito_evidence = str(row.get("has_mitochondrial_evidence", 0)).lower() in {"1", "1.0", "true"}
    has_mito_process = str(row.get("has_mitochondrial_process", 0)).lower() in {"1", "1.0", "true"}
    has_direct_senescence = str(row.get("has_direct_senescence_evidence", 0)).lower() in {"1", "1.0", "true"}
    has_mito_senescence_link = str(row.get("has_mito_senescence_link", 0)).lower() in {"1", "1.0", "true"}
    has_primary_hub = str(row.get("has_primary_hub_gene", 0)).lower() in {"1", "1.0", "true"}
    has_multiomics = str(row.get("has_multiomics", 0)).lower() in {"1", "1.0", "true"}
    has_fibroblast = str(row.get("has_fibroblast_model", 0)).lower() in {"1", "1.0", "true"}
    has_mechanistic_signal = str(row.get("has_mechanistic_signal", 0)).lower() in {"1", "1.0", "true"}

    mech_score = float(pd.to_numeric(
        pd.Series([row.get("mechanistic_score", 0)]),
        errors="coerce"
    ).fillna(0).iloc[0])

    mech_score = max(0.0, min(mech_score, 20.0))

    # Validated 142-paper evidence
    has_mito_evidence = str(row.get("has_mitochondrial_evidence", 0)).lower() in {"1", "1.0", "true"}
    has_mito_process = str(row.get("has_mitochondrial_process", 0)).lower() in {"1", "1.0", "true"}
    has_direct_senescence = str(row.get("has_direct_senescence_evidence", 0)).lower() in {"1", "1.0", "true"}
    has_mito_senescence_link = str(row.get("has_mito_senescence_link", 0)).lower() in {"1", "1.0", "true"}
    has_primary_hub = str(row.get("has_primary_hub_gene", 0)).lower() in {"1", "1.0", "true"}
    has_multiomics = str(row.get("has_multiomics", 0)).lower() in {"1", "1.0", "true"}
    has_mechanistic_signal = str(row.get("has_mechanistic_signal", 0)).lower() in {"1", "1.0", "true"}

    # Model relevance
    has_fibroblast = str(
        row.get("has_fibroblast_model", 0)
    ).lower() in {"1", "1.0", "true"}

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


    # ---------------------------------------------------------
    # 5. Mechanistic evidence
    # ---------------------------------------------------------

    mechanism_weight = float(
        weights.get("systems_mechanism", 4)
    )

    if mech_score > 0:
        mechanism_bonus = (
            mechanism_weight
            * (mech_score / 20.0)
        )

        score += mechanism_bonus

        reasons.append(
            f"Mechanistic evidence: {mech_score:.0f}/20"
        )

    elif has_mechanistic_signal:
        score += mechanism_weight * 0.25

        reasons.append(
            "Mechanistic evidence signal detected"
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

def calculate_centrality_signals(row, ontology):
    """
    Estimate research-question centrality from title and abstract.

    Centrality is based on connected mitochondrial-senescence evidence,
    rather than isolated keyword presence.
    """
    title = clean_text(row.get("title", "")).lower()
    abstract = clean_text(row.get("abstract", "")).lower()

    scope = ontology.get("research_scope", {})

    mito_terms = [
        str(x).lower()
        for x in scope.get("core_mitochondrial_processes", [])
    ]

    sen_terms = [
        str(x).lower()
        for x in scope.get("senescence_processes", [])
    ]

    hub_terms = [
        str(x).lower()
        for x in scope.get("priority_hubs", [])
    ]

    # Mitochondrial concepts that are especially informative
    # for the PhD research question.
    mito_core_terms = [
        "mitochondrial dysfunction",
        "mitochondrial dynamics",
        "mitochondrial fission",
        "mitochondrial fusion",
        "mitophagy",
        "mitochondrial quality control",
        "mitochondrial homeostasis",
        "mitochondrial biogenesis",
        "mitochondrial proteostasis",
        "mitochondrial membrane potential",
        "mitochondrial ros",
    ]

    # Direct senescence concepts.
    sen_core_terms = [
        "cellular senescence",
        "cellular senescence",
        "replicative senescence",
        "stress-induced senescence",
        "irradiation-induced senescence",
        "dna damage-induced senescence",
        "therapy-induced senescence",
    ]

    # Causal/mechanistic language.
    mechanistic_patterns = [
        "mechanistically",
        "mechanism",
        "via",
        "mediates",
        "mediation",
        "regulates",
        "regulating",
        "drives",
        "driving",
        "promotes",
        "causes",
        "contributes to",
        "leads to",
        "leading to",
        "results in",
        "resulting in",
        "through",
        "dependent on",
        "required for",
        "rescues",
        "attenuates",
    ]

    def matches(text, terms):
        return [term for term in terms if term and term in text]

    def sentences(text):
        return [
            s.strip()
            for s in text.replace("?", ".")
            .replace("!", ".")
            .split(".")
            if s.strip()
        ]

    abstract_sentences = sentences(abstract)

    title_mito = matches(title, mito_core_terms + hub_terms)
    title_sen = matches(title, sen_core_terms)

    # ---------------------------------------------------------
    # 1. TITLE CENTRALITY
    # ---------------------------------------------------------
    # A title signal requires BOTH mitochondrial and senescence
    # concepts. A mitochondrial-only or senescence-only title
    # is not sufficient.
    title_core = bool(title_mito and title_sen)

    # ---------------------------------------------------------
    # 2. OBJECTIVE CENTRALITY
    # ---------------------------------------------------------
    # Look mainly at the first three abstract sentences, where
    # the study rationale/objective is usually introduced.
    objective_sentences = abstract_sentences[:3]
    objective_text = " ".join(objective_sentences)

    objective_mito = matches(
        objective_text,
        mito_core_terms + hub_terms
    )

    objective_sen = matches(
        objective_text,
        sen_core_terms
    )

    objective_core = bool(objective_mito and objective_sen)

    # ---------------------------------------------------------
    # 3. MECHANISTIC CENTRALITY
    # ---------------------------------------------------------
    # Require mitochondrial + senescence evidence in the same
    # sentence, together with causal/mechanistic language.
    mechanistic_sentences = []

    for sentence in abstract_sentences:
        mito_hit = matches(
            sentence,
            mito_core_terms + hub_terms
        )
        sen_hit = matches(
            sentence,
            sen_core_terms
        )
        mech_hit = matches(
            sentence,
            mechanistic_patterns
        )

        if mito_hit and sen_hit and mech_hit:
            mechanistic_sentences.append(sentence)

    mechanistic_core = bool(mechanistic_sentences)

    signals = {
        "title_core": title_core,
        "objective_core": objective_core,
        "mechanistic_core": mechanistic_core,
    }

    evidence = {
        "title_mito_matches": title_mito[:8],
        "title_senescence_matches": title_sen[:8],
        "objective_mito_matches": objective_mito[:8],
        "objective_senescence_matches": objective_sen[:8],
        "mechanistic_sentence_count": len(mechanistic_sentences),
    }

    return signals, evidence


def calculate_rsa_v2(row, ontology, rsa_rules):
    """
    RSA V2 — PhD-specific Research Scope Alignment.

    Evidence is classified into biologically meaningful dimensions
    rather than being treated as a simple keyword-counting system.
    """
    hub_genes = clean_text(row.get("primary_hub_genes", "")).lower()


    score = 0.0
    reasons = []

    components = rsa_rules.get("components", {})
    weights = rsa_rules.get("evidence_weights", {})
    scope = ontology.get("research_scope", {})

    mito_classes = rsa_rules.get("mitochondrial_evidence_classes", {})
    sen_classes = rsa_rules.get("senescence_evidence_classes", {})

    def matched_terms(terms):
        return [
            str(term).lower()
            for term in terms
            if str(term).lower() in text
        ]


    # Mechanistic evidence: 0–20 scale
    mech_score = float(
        pd.to_numeric(
            pd.Series([
                row.get("mechanistic_score", 0)
            ]),
            errors="coerce"
        ).fillna(0).iloc[0]
    )

    mech_score = max(0.0, min(mech_score, 20.0))
    # Validated 142-paper evidence
    has_mito_evidence = str(row.get("has_mitochondrial_evidence", 0)).lower() in {"1", "1.0", "true"}
    has_mito_process = str(row.get("has_mitochondrial_process", 0)).lower() in {"1", "1.0", "true"}
    has_direct_senescence = str(row.get("has_direct_senescence_evidence", 0)).lower() in {"1", "1.0", "true"}
    has_mito_senescence_link = str(row.get("has_mito_senescence_link", 0)).lower() in {"1", "1.0", "true"}
    has_primary_hub = str(row.get("has_primary_hub_gene", 0)).lower() in {"1", "1.0", "true"}
    has_multiomics = str(row.get("has_multiomics", 0)).lower() in {"1", "1.0", "true"}
    has_mechanistic_signal = str(row.get("has_mechanistic_signal", 0)).lower() in {"1", "1.0", "true"}

    # Model relevance
    has_fibroblast = str(
        row.get("has_fibroblast_model", 0)
    ).lower() in {"1", "1.0", "true"}

    # Omics relevance

    # ---------------------------------------------------------
    # 1. Direct mitochondrial–senescence relationship
    direct_mito = has_mito_senescence_link
    direct_senescence = has_direct_senescence

    # Determine whether mitochondrial and senescence evidence
    # are connected rather than merely co-occurring.
    centrality_signals, _ = calculate_centrality_signals(
        row, ontology
    )

    connected_mito_senescence = (
        direct_mito
        and direct_senescence
        and (
            centrality_signals.get("title_core", False)
            or centrality_signals.get("objective_core", False)
            or centrality_signals.get("mechanistic_core", False)
        )
    )

    if connected_mito_senescence:
        score += float(
            components.get("direct_mito_senescence", 0)
        )
        reasons.append(
            "Direct mitochondrial–senescence relationship"
        )


    # ---------------------------------------------------------
    # 2. Mitochondrial evidence hierarchy
    # ---------------------------------------------------------

    if has_mito_process:
        score += float(
            weights.get(
                "mitochondrial_evidence", {}
            ).get(
                "core_mechanistic", 6
            )
        )
        reasons.append(
            "Specific mitochondrial process/mechanism"
        )

    elif has_mito_evidence:
        score += float(
            weights.get(
                "mitochondrial_evidence", {}
            ).get(
                "functional", 3
            )
        )
        reasons.append(
            "Mitochondrial biological evidence"
        )


    # ---------------------------------------------------------
    # 3. Senescence evidence hierarchy
    # ---------------------------------------------------------

    if has_direct_senescence:
        score += float(
            weights.get(
                "senescence_evidence", {}
            ).get(
                "direct", 5
            )
        )

        reasons.append(
            "Direct cellular-senescence evidence"
        )


    # ---------------------------------------------------------
    # 4. Priority hub-gene evidence
    # ---------------------------------------------------------

    if has_primary_hub:
        score += float(
            weights.get("priority_hub", 3)
        )

        reasons.append(
            "Priority mitochondrial hub-gene involvement"
        )

    # ---------------------------------------------------------
    # 5. Mechanistic evidence
    # ---------------------------------------------------------

    mechanism_weight = float(
        weights.get("systems_mechanism", 0)
    )

    mechanism_bonus = mechanism_weight * (
        mech_score / 20.0
    )

    if mechanism_bonus > 0:
        score += mechanism_bonus
        reasons.append(
            f"Mechanistic evidence: {mech_score:.0f}/20"
        )


    # ---------------------------------------------------------
    # 6. Model relevance
    # ---------------------------------------------------------

    if has_fibroblast:
        score += float(
            weights.get("model_relevance", 4)
        )

        reasons.append(
            "PhD-relevant fibroblast model"
        )


    # ---------------------------------------------------------
    # 7. Omics relevance
    # ---------------------------------------------------------

    if has_multiomics:
        score += float(
            weights.get("omics_relevance", 3)
        )

        reasons.append(
            "Multi-omics evidence"
        )

    elif (
        pd.to_numeric(row.get("objective_O2", 0), errors="coerce") > 0
        or pd.to_numeric(row.get("objective_O3", 0), errors="coerce") > 0
    ):
        score += float(
            weights.get("omics_relevance", 3)
        )

        reasons.append(
            "Relevant computational/omics evidence"
        )


    objective_levels = [
        pd.to_numeric(row.get(f"objective_O{i}", 0), errors="coerce")
        for i in range(1, 6)
    ]
    objective_max = max([float(x) if pd.notna(x) else 0.0 for x in objective_levels])

    # ---------------------------------------------------------
    # 8. Scope gating
    # ---------------------------------------------------------

    specific_features = sum([
        has_mito_process,
        has_primary_hub,
        mech_score >= 10,
        has_fibroblast,
        has_multiomics,
        objective_max >= 1,
    ])

    gating = rsa_rules.get(
        "scope_gating",
        {}
    )

    if (
        has_mito_senescence_link
        and gating.get(
            "direct_mito_senescence_requires_specificity",
            False
        )
        and specific_features == 0
    ):
        direct_bonus = float(
            components.get(
                "direct_mito_senescence",
                8
            )
        )

        score -= direct_bonus

        reasons.append(
            "Direct mitochondrial-senescence evidence gated: "
            "insufficient PhD-specific supporting evidence"
        )


    # ---------------------------------------------------------
    # 9. Peripheral context
    # ---------------------------------------------------------
    #
    # No validated peripheral-context field is currently
    # available in the 142-paper evidence layer.
    #
    # Therefore, no unsupported peripheral penalty is applied.
    # Disease context will be handled later by the broader
    # relevance model rather than assumed to be irrelevant.
    # ---------------------------------------------------------


    # ---------------------------------------------------------
    # 10. Research-question centrality
    # ---------------------------------------------------------
    #
    # Centrality is primarily determined from the validated
    # 142-paper evidence layer. Text-level signals are retained
    # as secondary evidence, not as a hard gate.
    #
    # This prevents highly relevant mitochondrial-senescence
    # papers from being classified as C0 simply because the
    # mitochondrial and senescence terms occur in different
    # abstract sentences.
    # ---------------------------------------------------------

    has_mito_evidence = str(
        row.get("has_mitochondrial_evidence", 0)
    ).lower() in {"1", "1.0", "true"}

    has_mito_process = str(
        row.get("has_mitochondrial_process", 0)
    ).lower() in {"1", "1.0", "true"}

    has_direct_senescence = str(
        row.get("has_direct_senescence_evidence", 0)
    ).lower() in {"1", "1.0", "true"}

    has_mito_senescence_link = str(
        row.get("has_mito_senescence_link", 0)
    ).lower() in {"1", "1.0", "true"}

    has_primary_hub = str(
        row.get("has_primary_hub_gene", 0)
    ).lower() in {"1", "1.0", "true"}

    has_multiomics = str(
        row.get("has_multiomics", 0)
    ).lower() in {"1", "1.0", "true"}

    objective_levels = []

    for objective_col in [
        "objective_O1",
        "objective_O2",
        "objective_O3",
        "objective_O4",
        "objective_O5",
    ]:
        value = pd.to_numeric(
            pd.Series([row.get(objective_col, 0)]),
            errors="coerce"
        ).fillna(0).iloc[0]

        objective_levels.append(float(value))

    objective_max = max(objective_levels) if objective_levels else 0.0

    title_core = centrality_signals.get(
        "title_core", False
    )

    objective_core = centrality_signals.get(
        "objective_core", False
    )

    mechanistic_core = centrality_signals.get(
        "mechanistic_core", False
    )

    # ---------------------------------------------------------
    # Establish connected mitochondrial-senescence biology
    # ---------------------------------------------------------
    #
    # The validated evidence extractor is authoritative here.
    # Text-level mechanistic evidence can independently support
    # the connection.
    # ---------------------------------------------------------

    connected_mito_senescence = (
        has_mito_senescence_link
        or (
            direct_mito
            and direct_senescence
            and (
                title_core
                or objective_core
                or mechanistic_core
            )
        )
    )

    # ---------------------------------------------------------
    # Centrality classification
    # ---------------------------------------------------------

    if connected_mito_senescence:

        # C3 = direct/core mitochondrial-senescence biology.
        #
        # Strong evidence includes a validated mito-senescence
        # link plus at least one additional research-specific
        # signal.
        strong_core_signal = (
            title_core
            or objective_core
            or mechanistic_core
            or has_mito_process
            or has_primary_hub
            or mech_score >= 10
            or has_multiomics
            or objective_max >= 2
        )

        if strong_core_signal:
            centrality_class = "C3"

        else:
            centrality_class = "C2"

    elif (
        has_mito_evidence
        or has_direct_senescence
        or direct_mito
        or direct_senescence
    ):

        # C1 = relevant mitochondrial or senescence biology,
        # but no validated connected relationship.
        centrality_class = "C1"

    else:

        # C0 = no meaningful evidence for the PhD biological scope.
        centrality_class = "C0"

    centrality_weights = rsa_rules.get(
        "centrality_weights", {}
    )

    centrality_bonus = float(
        centrality_weights.get(
            centrality_class, 0
        )
    )

    score += centrality_bonus

    reasons.append(
        f"Research-question centrality: "
        f"{centrality_class} (+{centrality_bonus:.1f})"
    )

    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # 11. RSA tier
    # ---------------------------------------------------------

    thresholds = rsa_rules.get("thresholds", {})

    if (
        score >= float(thresholds.get("R1_direct_core", 20))
        and has_mito_senescence_link
        and specific_features >= 1
    ):
        tier = "R1 — Direct Core Relevance"

    elif score >= float(
        thresholds.get("R2_direct_mechanistic", 14)
    ):
        tier = "R2 — Direct Mechanistic Relevance"

    elif score >= float(
        thresholds.get("R3_computational_multiomics", 9)
    ):
        tier = "R3 — Computational / Multi-Omics Relevance"

    elif score >= float(
        thresholds.get("R4_transferable", 6)
    ):
        tier = "R4 — Transferable Biological Relevance"

    elif score >= float(
        thresholds.get("R5_supporting", 3)
    ):
        tier = "R5 — Supporting Background Relevance"

    else:
        tier = "R6 — Peripheral / Low Relevance"

    return score, tier, reasons

def test_rsa():
    ontology = load_ontology()
    rsa_rules = load_rsa_rules()

    df = pd.read_csv(RANKED_FILE)
    mechanistic = pd.read_csv(MECHANISTIC_FILE)
    utility = pd.read_csv(UTILITY_FILE)

    df["pmid"] = df["pmid"].astype(str).str.strip()
    mechanistic["pmid"] = mechanistic["pmid"].astype(str).str.strip()
    utility["pmid"] = utility["pmid"].astype(str).str.strip()

    # ---------------------------------------------------------
    # Merge validated mechanistic evidence
    # ---------------------------------------------------------
    df = df.merge(
        mechanistic[
            [
                "pmid",
                "mechanistic_evidence_level",
                "mechanistic_score",
            ]
        ],
        on="pmid",
        how="left",
    )

    # ---------------------------------------------------------
    # Merge validated 142-paper biological / objective evidence
    # ---------------------------------------------------------
    utility_columns = [
        "pmid",
        "primary_hub_genes",
        "model_relevance_tier",
        "has_fibroblast_model",
        "has_mitochondrial_evidence",
        "has_mitochondrial_process",
        "has_direct_senescence_evidence",
        "has_mito_senescence_link",
        "has_multiomics",
        "has_mechanistic_signal",
        "objective_O1",
        "objective_O2",
        "objective_O3",
        "objective_O4",
        "objective_O5",
    ]

    df = df.merge(
        utility[utility_columns],
        on="pmid",
        how="left",
    )

    results = []

    for _, row in df.iterrows():
        score, tier, reasons = calculate_rsa_v2(
            row,
            ontology,
            rsa_rules,
        )

        results.append(
            {
                "pmid": row["pmid"],
                "title": row["title"],
                "RSA_V2": score,
                "RSA_V2_tier": tier,
                "RSA_V2_reasons": "; ".join(reasons),
            }
        )

    result_df = pd.DataFrame(results)

    output_file = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "phd_rsa_v2.csv"
    )

    result_df.to_csv(output_file, index=False)

    print("\nRSA V2 results saved to: data/processed/phd_rsa_v2.csv")
    print(f"Rows scored: {len(result_df)}")
if __name__ == "__main__":
    test_rsa()
