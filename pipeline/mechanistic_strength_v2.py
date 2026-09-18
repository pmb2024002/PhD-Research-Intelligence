from pathlib import Path
import pandas as pd
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_FILE = PROJECT_ROOT / "data" / "raw" / "pubmed_articles.csv"
FEATURE_FILE = PROJECT_ROOT / "data" / "processed" / "phd_utility_features_v2.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "phd_mechanistic_strength_v2.csv"


def normalize(value):
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def contains_any(text, terms):
    text = normalize(text)
    return any(term in text for term in terms)


def contains_pattern(text, patterns):
    text = normalize(text)
    return any(re.search(pattern, text) for pattern in patterns)

def detect_perturbation(text):
    patterns = [
        r"\bknockdown\b",
        r"\bknockout\b",
        r"\bknock-out\b",
        r"\boverexpression\b",
        r"\bover-expression\b",
        r"\bsilencing\b",
        r"\bdepletion\b",
        r"\binhibition\b",
        r"\binhibitor\b",
        r"\binhibit(?:ed|s|ing)?\b",
        r"\bdeletion\b",
        r"\bmutation\b",
        r"\bmutant\b",
        r"\bloss[- ]of[- ]function\b",
        r"\bgain[- ]of[- ]function\b",
        r"\bpharmacological\b",
        r"\bsiRNA\b",
        r"\bshRNA\b",
        r"\bCRISPR\b",
    ]
    return contains_pattern(text, patterns)


def detect_rescue(text):
    rescue_terms = [
        "rescue",
        "rescued",
        "rescue experiment",
        "restored",
        "restoration",
        "reversed",
        "reversal",
        "revert",
        "reverted",
        "ameliorated",
        "attenuated",
    ]
    return contains_any(text, rescue_terms)


def detect_senescence_phenotype(text):
    phenotype_terms = [
        "senescence phenotype",
        "senescent phenotype",
        "cellular senescence",
        "senescent cells",
        "senescence-associated",
        "sa-β-gal",
        "sa-beta-gal",
        "p16",
        "cdkn2a",
        "p21",
        "cdkn1a",
        "senescence marker",
        "senescence markers",
        "sasp",
    ]
    return contains_any(text, phenotype_terms)


def detect_mitochondrial_phenotype(text):
    phenotype_terms = [
        "mitochondrial dysfunction",
        "mitochondrial function",
        "mitochondrial morphology",
        "mitochondrial fragmentation",
        "mitochondrial elongation",
        "mitochondrial membrane potential",
        "mitochondrial ros",
        "mitochondrial reactive oxygen species",
        "oxygen consumption",
        "respiration",
        "respiratory capacity",
        "atp production",
        "mitophagy",
        "mitochondrial quality control",
        "mitochondrial fission",
        "mitochondrial fusion",
    ]
    return contains_any(text, phenotype_terms)

def detect_mito_senescence_connection(text):
    mito_terms = [
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
    ]

    senescence_terms = [
        "cellular senescence",
        "replicative senescence",
        "stress-induced senescence",
        "senescent cells",
        "senescence phenotype",
        "senescence-associated",
    ]

    return (
        contains_any(text, mito_terms)
        and contains_any(text, senescence_terms)
    )


def detect_mechanistic_link(text):
    """
    Detect whether the abstract contains language suggesting that
    a mitochondrial factor/process was experimentally manipulated
    in relation to a biological phenotype.
    """

    mitochondrial_terms = [
        "mitochondrial dysfunction",
        "mitochondrial dynamics",
        "mitochondrial fission",
        "mitochondrial fusion",
        "mitophagy",
        "mitochondrial quality control",
        "mitochondrial function",
        "mitochondrial ros",
        "mitochondrial membrane potential",
    ]

    perturbation_terms = [
        "knockdown",
        "knockout",
        "knock-out",
        "overexpression",
        "over-expression",
        "silencing",
        "depletion",
        "inhibition",
        "inhibitor",
        "mutation",
        "mutant",
        "loss-of-function",
        "gain-of-function",
        "pharmacological",
        "sirna",
        "shrna",
        "crispr",
    ]

    senescence_terms = [
        "cellular senescence",
        "replicative senescence",
        "stress-induced senescence",
        "senescent cells",
        "senescence phenotype",
        "senescence-associated",
    ]

    return (
        contains_any(text, mitochondrial_terms)
        and contains_any(text, perturbation_terms)
        and contains_any(text, senescence_terms)
    )


def detect_strong_causal_signal(text):
    """
    Stronger evidence requires a perturbation together with
    mitochondrial and senescence phenotypes, plus rescue/reversal
    or explicit causal language.
    """

    perturbation = detect_perturbation(text)
    mito = detect_mitochondrial_phenotype(text)
    senescence = detect_senescence_phenotype(text)
    rescue = detect_rescue(text)

    causal_terms = [
        "caused",
        "causally",
        "mediated",
        "mediates",
        "required for",
        "necessary for",
        "sufficient for",
        "drives",
        "driven by",
        "depends on",
        "dependent on",
    ]

    causal_language = contains_any(text, causal_terms)

    return (
        perturbation
        and mito
        and senescence
        and (rescue or causal_language)
    )

def detect_core_mitochondrial_mechanism(text):
    """
    Detect whether the abstract contains a mechanism centered on
    mitochondrial processes or priority mitochondrial genes relevant
    to the PhD research question.
    """

    core_genes = [
        "dnm1l",
        "drp1",
        "opa1",
        "mfn1",
        "mfn2",
        "pink1",
        "prkn",
        "park2",
    ]

    core_processes = [
        "mitochondrial fission",
        "mitochondrial fusion",
        "mitochondrial dynamics",
        "mitophagy",
        "mitochondrial quality control",
        "mitochondrial biogenesis",
        "mitochondrial membrane potential",
    ]

    mechanism_terms = [
        "knockdown",
        "knockout",
        "knock-out",
        "overexpression",
        "over-expression",
        "silencing",
        "depletion",
        "inhibition",
        "inhibitor",
        "mutation",
        "mutant",
        "loss-of-function",
        "gain-of-function",
        "pharmacological",
        "sirna",
        "shrna",
        "crispr",
        "rescue",
        "rescued",
        "restored",
        "restoration",
    ]

    has_core_gene = contains_any(text, core_genes)
    has_core_process = contains_any(text, core_processes)
    has_mechanism_term = contains_any(text, mechanism_terms)

    return (
        (has_core_gene or has_core_process)
        and has_mechanism_term
    )

def detect_targeted_core_mechanism(text):
    """
    Detect whether a PhD-relevant mitochondrial gene or process
    is part of an experimentally investigated mechanistic pathway.
    """

    core_genes = [
        "dnm1l",
        "drp1",
        "opa1",
        "mfn1",
        "mfn2",
        "pink1",
        "prkn",
        "park2",
    ]

    core_processes = [
        "mitochondrial fission",
        "mitochondrial fusion",
        "mitochondrial dynamics",
        "mitophagy",
        "mitochondrial quality control",
        "mitochondrial biogenesis",
    ]

    direct_target_patterns = [
        r"\bknockdown of\b",
        r"\bknockout of\b",
        r"\bknock-out of\b",
        r"\boverexpression of\b",
        r"\bover-expression of\b",
        r"\bsilencing of\b",
        r"\bdepletion of\b",
        r"\binhibition of\b",
        r"\btargeting\b",
        r"\btargeted\b",
    ]

    mechanistic_relationship_patterns = [
        r"\bmediated by\b",
        r"\bmediated through\b",
        r"\bdependent on\b",
        r"\bdepends on\b",
        r"\brequired for\b",
        r"\bnecessary for\b",
        r"\bsufficient for\b",
        r"\bdrives\b",
        r"\bdriven by\b",
        r"\bregulates\b",
        r"\bregulated by\b",
        r"\binteracts with\b",
        r"\binteracted with\b",
        r"\bpathway\b",
        r"\baxis\b",
    ]

    has_core_gene = contains_any(text, core_genes)
    has_core_process = contains_any(text, core_processes)

    has_direct_target = contains_pattern(
        text,
        direct_target_patterns
    )

    has_mechanistic_relationship = contains_pattern(
        text,
        mechanistic_relationship_patterns
    )

    return (
        (has_core_gene or has_core_process)
        and (
            has_direct_target
            or has_mechanistic_relationship
        )
    )

def identify_mechanism_label(text):
    """
    Assign a human-readable label to the main mitochondrial
    mechanism detected in the abstract.
    """

    text = normalize(text)

    if (
        contains_any(text, ["pink1", "prkn", "park2", "parkin"])
        and contains_any(
            text,
            [
                "mitophagy",
                "mitochondrial quality control"
            ]
        )
    ):
        return "PINK1/PRKN → mitophagy"

    if contains_any(text, ["dnm1l", "drp1"]):
        if contains_any(
            text,
            [
                "mitochondrial fission",
                "mitochondrial dynamics",
                "fragmentation"
            ]
        ):
            return "DNM1L/DRP1 → mitochondrial fission/dynamics"

    if contains_any(text, ["opa1"]):
        if contains_any(
            text,
            [
                "mitochondrial fusion",
                "mitochondrial dynamics",
                "cristae"
            ]
        ):
            return "OPA1 → mitochondrial fusion/dynamics"

    if contains_any(text, ["mfn1"]):
        if contains_any(
            text,
            [
                "mitochondrial fusion",
                "mitochondrial dynamics"
            ]
        ):
            return "MFN1 → mitochondrial fusion/dynamics"

    if contains_any(text, ["mfn2"]):
        if contains_any(
            text,
            [
                "mitochondrial dysfunction",
                "mitochondrial fusion",
                "mitochondrial dynamics"
            ]
        ):
            return "MFN2 → mitochondrial dysfunction/fusion"

    if contains_any(text, ["sirt3"]):
        if contains_any(
            text,
            [
                "mitophagy",
                "mitochondrial quality control",
                "mitochondrial dysfunction"
            ]
        ):
            return "SIRT3 → mitochondrial quality control"

    if contains_any(text, ["mtfr1l"]):
        if contains_any(
            text,
            [
                "mitochondrial fission",
                "mitochondrial dynamics"
            ]
        ):
            return "MTFR1L → mitochondrial fission/dynamics"

    if contains_any(
        text,
        [
            "mitochondrial fission",
            "mitochondrial fusion",
            "mitochondrial dynamics"
        ]
    ):
        return "Mitochondrial dynamics → senescence"

    if contains_any(
        text,
        [
            "mitophagy",
            "mitochondrial quality control"
        ]
    ):
        return "Mitochondrial quality control → senescence"

    if contains_any(
        text,
        [
            "mitochondrial dysfunction",
            "mitochondrial membrane potential",
            "mitochondrial ros"
        ]
    ):
        return "Mitochondrial dysfunction → senescence"

    return "General mitochondrial-senescence association"

def classify_mechanistic_strength(text):
    mito_senescence = detect_mito_senescence_connection(text)
    perturbation = detect_perturbation(text)
    mito_phenotype = detect_mitochondrial_phenotype(text)
    senescence_phenotype = detect_senescence_phenotype(text)
    rescue = detect_rescue(text)
    mechanistic_link = detect_mechanistic_link(text)
    strong_causal = detect_strong_causal_signal(text)
    core_mechanism = detect_core_mitochondrial_mechanism(text)
    targeted_core_mechanism = detect_targeted_core_mechanism(text)
    if strong_causal and targeted_core_mechanism:
        return (
            4,
            "Strong causal/mechanistic signal involving a "
            "PhD-relevant mitochondrial mechanism"
        )

    if mechanistic_link and targeted_core_mechanism and rescue:
        return (
            4,
            "Strong mitochondrial mechanism with perturbation "
            "and rescue evidence"
        )

    if mechanistic_link and targeted_core_mechanism:
        return (
            3,
            "Mechanistic signal involving a PhD-relevant "
            "mitochondrial factor or process"
        )

    if (
        mito_senescence
        and perturbation
        and mito_phenotype
        and senescence_phenotype
    ):
        return (
            2,
            "Experimental mitochondrial-senescence association "
            "with perturbation evidence"
        )

    if (
        mito_senescence
        and mito_phenotype
        and senescence_phenotype
    ):
        return (
            2,
            "Mitochondrial and senescence phenotypes are both "
            "investigated"
        )

    if mito_senescence:
        return (
            1,
            "Mitochondrial and senescence association detected"
        )

    if mito_phenotype or senescence_phenotype:
        return (
            0,
            "Partial biological evidence without a clear "
            "mitochondrial-senescence connection"
        )

    return (
        0,
        "No clear mitochondrial-senescence mechanistic evidence"
    )

def main():
    for path in [RAW_FILE, FEATURE_FILE]:
        if not path.exists():
            raise FileNotFoundError(
                f"Required file not found: {path}"
            )

    raw = pd.read_csv(RAW_FILE).fillna("")
    features = pd.read_csv(FEATURE_FILE).fillna("")

    raw["pmid"] = raw["pmid"].astype(str)
    features["pmid"] = features["pmid"].astype(str)

    raw["full_text"] = (
        raw["title"].astype(str)
        + " "
        + raw["abstract"].astype(str)
    ).map(normalize)

    text_by_pmid = dict(
        zip(raw["pmid"], raw["full_text"])
    )

    rows = []

    for _, row in features.iterrows():
        pmid = str(row["pmid"])
        text = text_by_pmid.get(pmid, "")

        strength, explanation = classify_mechanistic_strength(
            text
        )

        rows.append({
            "pmid": pmid,
            "title": row["title"],
            "user_relevance": row.get(
                "user_relevance", ""
            ),
            "mechanistic_strength_level": strength,
            "mechanistic_strength_explanation": explanation,
            "mechanism_label": identify_mechanism_label(text),
            "has_mito_senescence_connection": int(
                detect_mito_senescence_connection(text)
            ),
            "has_perturbation": int(
                detect_perturbation(text)
            ),
            "has_mitochondrial_phenotype": int(
                detect_mitochondrial_phenotype(text)
            ),
            "has_senescence_phenotype": int(
                detect_senescence_phenotype(text)
            ),
            "has_rescue_signal": int(
                detect_rescue(text)
            ),
            "has_mechanistic_link": int(
                detect_mechanistic_link(text)
            ),
            "has_strong_causal_signal": int(
                detect_strong_causal_signal(text)
            ),
        })

    output = pd.DataFrame(rows)

    output = output.sort_values(
        by=[
            "mechanistic_strength_level",
            "user_relevance"
        ],
        ascending=[False, True]
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nMechanistic-strength analysis completed.")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Rows: {len(output)}")

    print("\nMechanistic strength distribution:")
    print(
        output[
            "mechanistic_strength_level"
        ].value_counts().sort_index()
    )

    print("\nSummary by user relevance:")
    print(
        output.groupby(
            [
                "user_relevance",
                "mechanistic_strength_level"
            ]
        ).size()
    )

    print("\nTop mechanistic papers:")
    print(
        output[
            [
                "pmid",
                "user_relevance",
                "mechanistic_strength_level",
                "mechanistic_strength_explanation"
            ]
        ].head(10).to_string(index=False)
    )


if __name__ == "__main__":
    main()
