import pandas as pd
import yaml
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

RANKED_FILE = BASE_DIR / "data" / "processed" / "pubmed_ranked.csv"
PROFILE_FILE = BASE_DIR / "config" / "research_profile.yaml"
EXPLAIN_FILE = BASE_DIR / "config" / "explainability.yaml"

OUTPUT_FILE = BASE_DIR / "data" / "processed" / "pubmed_explained.csv"


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def clean_value(value):
    if pd.isna(value):
        return ""
    value = str(value).strip()
    if value.lower() in {"nan", "none", ""}:
        return ""
    return value

def classify_evidence_type(row):
    omics_evidence = clean_value(row.get("omics_evidence")).lower()
    mechanistic_evidence = clean_value(row.get("mechanistic_evidence")).lower()

    evidence_types = []

    modalities = []

    if "transcriptomics" in omics_evidence:
        modalities.append("Transcriptomic")

    if "proteomics" in omics_evidence:
        modalities.append("Proteomic")

    if "metabolomics" in omics_evidence:
        modalities.append("Metabolomic")

    if len(modalities) >= 2:
        evidence_types.append("Multi-omics")
    else:
        evidence_types.extend(modalities)

    if mechanistic_evidence:
        evidence_types.append("Mechanistic / experimental signal")

    if not evidence_types:
        evidence_types.append("Background / other")

    return ", ".join(dict.fromkeys(evidence_types))


def build_explanation(row, profile, explainability):
    evidence_type = classify_evidence_type(row)
    title = clean_value(row.get("title"))
    relevance_level = clean_value(row.get("relevance_level"))
    relevance_score = clean_value(row.get("relevance_score"))
    evidence_tier = clean_value(row.get("evidence_tier"))

    core_evidence = clean_value(row.get("core_evidence"))
    strong_context = clean_value(row.get("strong_context"))
    supporting_context = clean_value(row.get("supporting_context"))
    peripheral_context = clean_value(row.get("peripheral_context"))

    biological_score = clean_value(row.get("biological_score"))
    context_score = clean_value(row.get("context_score"))
    mechanistic_evidence = clean_value(row.get("mechanistic_evidence"))

    phd_relevance = (
        f"This paper is classified as {relevance_level} relevance "
        f"and {evidence_tier} in relation to the PhD research topic "
        f"'{profile['research_title']}'. "
        f"The current rule-based relevance score is {relevance_score}, "
        f"with a biological score of {biological_score} and a context score "
        f"of {context_score}."
    )

    if core_evidence:
        key_evidence = (
            f"The paper contains the following detected PhD-relevant evidence: "
            f"{core_evidence}."
        )
    else:
        key_evidence = (
            "The current ranking did not record specific core evidence fields "
            "for this paper."
        )
    if mechanistic_evidence:
        mechanistic_connection = (
            f"The ranking system detected the following text-based mechanistic "
            f"relationship(s): {mechanistic_evidence}. "
            f"This indicates a candidate mechanistic connection to the "
            f"mitochondrial-senescence framework; experimental causality should "
            f"be verified from the full paper."
        )
    else:
        mechanistic_connection = (
            "No specific mechanistic gene-process relationship was detected "
            "by the current rule-based ranking."
        )

    biological_parts = []

    if strong_context:
        biological_parts.append(
            f"Strong biological/contextual matches: {strong_context}."
        )

    if supporting_context:
        biological_parts.append(
            f"Supporting context: {supporting_context}."
        )

    if biological_parts:
        biological_connection = " ".join(biological_parts)
    else:
        biological_connection = (
            "No strong or supporting biological/contextual matches were recorded."
        )

    model_evidence = clean_value(row.get("model_matches"))

    if model_evidence:
        model_relevance = (
            f"Experimental-model relevance detected: {model_evidence}."
        )
    else:
        model_relevance = (
            "No specific experimental model was detected by the current "
            "rule-based ranking."
        )

    omics_evidence = clean_value(row.get("omics_evidence"))

    if omics_evidence:
        methodological_relevance = (
            f"Relevant omics or computational methods detected: "
            f"{omics_evidence}."
        )
    else:
        methodological_relevance = (
            "No specific omics or computational method was detected "
            "by the current ranking."
        )

    if peripheral_context:
        peripheral_section = (
            f"Potentially peripheral or distracting context detected: "
            f"{peripheral_context}."
        )
    else:
        peripheral_section = (
            "No major peripheral context was detected."
        )

    potential_use = (
        "Potential use: literature background, mechanistic interpretation, "
        "hypothesis generation, dataset interpretation, or comparison with "
        "the mitochondrial-senescence framework. Manual reading is recommended "
        "before treating the paper as directly applicable to the PhD."
    )

    sections = [
        f"PhD Relevance\n{phd_relevance}",
        f"Key Evidence\n{key_evidence}",
        f"Evidence Type\n{evidence_type}",
        f"Biological Connection\n{biological_connection}",
        f"Mechanistic Connection\n{mechanistic_connection}",
        f"Model Relevance\n{model_relevance}",
        f"Methodological Relevance\n{methodological_relevance}",
        f"Peripheral Context\n{peripheral_section}",
        f"Potential Use\n{potential_use}",
    ]

    return "\n\n".join(sections)


def main():

    print("Loading ranked PubMed results...")

    df = pd.read_csv(RANKED_FILE)

    profile = load_yaml(PROFILE_FILE)
    explainability = load_yaml(EXPLAIN_FILE)

    print(f"Loaded {len(df)} ranked papers.")

    df["explanation"] = df.apply(
        lambda row: build_explanation(
            row,
            profile,
            explainability
        ),
        axis=1
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    print()
    print(f"Saved explanations for {len(df)} papers to:")
    print(OUTPUT_FILE)
    print()
    print("Explanation generator completed successfully.")


if __name__ == "__main__":
    main()
