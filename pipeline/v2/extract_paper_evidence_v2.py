import json
import sys
from pathlib import Path

import pandas as pd
from jsonschema import Draft202012Validator


# ============================================================
# Mitochondrial Research Intelligence
# V2 Paper Evidence Extractor
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

SCHEMA_PATH = (
    BASE_DIR
    / "schemas"
    / "v2"
    / "paper_evidence_schema_v2.json"
)

DATASET_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "phd_labeling_dataset_80.csv"
)


# ============================================================
# Schema
# ============================================================

def load_schema():
    """Load the V2 paper evidence JSON schema."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# Source text
# ============================================================

def build_source_text(title, abstract):
    """
    Build source text for future Research Model extraction.

    This remains outside the final evidence object.
    """
    return f"TITLE:\n{title}\n\nABSTRACT:\n{abstract}"


# ============================================================
# Empty V2 evidence record
# ============================================================

def create_empty_evidence_record(pmid, title, abstract):
    """
    Create a schema-aligned V2 evidence record.

    Scientific fields remain empty until the Research Model
    performs evidence extraction.
    """

    return {
        "schema_version": "2.0",

        "paper_identity": {
            "pmid": str(pmid),
            "title": str(title),
            "authors": [],
            "journal": "",
            "publication_date": "",
            "doi": "",
            "pubmed_url": "",
            "source": "PubMed",
            "retrieval_date": "",
        },

        "biological_context": {
            "organism": "",
            "species": "",
            "cell_type": "",
            "tissue": "",
            "organ": "",
            "disease": "",
            "primary_model": "",
            "senescence_model": "",
            "senescence_trigger": "",
        },

        "senescence": {
            "investigated": False,
            "evidence_type": "unclear",
            "trigger": "",
            "markers": [],
            "phenotype": "",
        },

        "mitochondrial": {
            "investigated": False,
            "evidence_type": "unclear",
            "dysfunction": "",
            "processes": [],
            "mitochondrial_dynamics": [],
            "mitophagy": "",
            "ros": "",
            "metabolism": "",
            "bioenergetics": "",
            "morphology": "",
        },

        "molecular_entities": {
            "genes": [],
            "proteins": [],
            "pathways": [],
            "metabolites": [],
            "interventions": [],
        },

        "omics": {
            "modalities": [],
            "integration_level": "unclear",
            "methods": [],
            "targets": [],
        },

        "experimental_design": {
            "study_type": "",
            "groups": [],
            "controls": [],
            "interventions": [],
            "assays": [],
            "time_points": [],
        },

        "mechanism": [],

        "findings": [],

        "evidence_assessment": {
            "overall_strength": "unclear",
            "direct_experimental": False,
            "mechanistic_perturbation": False,
            "orthogonal_validation": False,
            "omics_support": False,
            "functional_validation": False,
            "uncertainties": [],
        },

        "limitations": [],

        "research_gaps": [],

        "phd_objectives": {
            "O1": {
                "level": 0,
                "reason": "",
                "evidence": [],
                "confidence": "low",
            },
            "O2": {
                "level": 0,
                "reason": "",
                "evidence": [],
                "confidence": "low",
            },
            "O3": {
                "level": 0,
                "reason": "",
                "evidence": [],
                "confidence": "low",
            },
            "O4": {
                "level": 0,
                "reason": "",
                "evidence": [],
                "confidence": "low",
            },
            "O5": {
                "level": 0,
                "reason": "",
                "evidence": [],
                "confidence": "low",
            },
        },

        "phd_relevance": {
            "classification": "unclear",
            "reason": "",
            "supporting_evidence": [],
        },

        "research_priority": {
            "category": "",
            "components": {},
            "reason": "",
        },

        "why_this_paper_matters": "",

        "confidence": {
            "overall": "low",
            "scientific_extraction": "low",
            "mechanism": "low",
            "relevance": "low",
        },
    }


# ============================================================
# Schema validation
# ============================================================

def validate_record(record, schema):
    """Validate a V2 evidence record against the JSON schema."""

    validator = Draft202012Validator(schema)

    return sorted(
        validator.iter_errors(record),
        key=lambda error: list(error.path),
    )


# ============================================================
# Main test
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # 1. Load schema
    # --------------------------------------------------------

    schema = load_schema()

    print("V2 schema loaded successfully.")
    print("Schema version:", schema.get("$schema"))

    # --------------------------------------------------------
    # 2. Load dataset
    # --------------------------------------------------------

    if not DATASET_PATH.exists():
        print("ERROR: Dataset not found:")
        print(DATASET_PATH)
        sys.exit(1)

    df = pd.read_csv(DATASET_PATH)

    print("Dataset loaded successfully.")
    print("Dataset rows:", len(df))
    print("Dataset columns:", len(df.columns))

    # --------------------------------------------------------
    # 3. Select real test paper
    # --------------------------------------------------------

    pmid = 42526698

    matches = df[df["pmid"] == pmid]

    if matches.empty:
        print(f"ERROR: PMID {pmid} not found in dataset.")
        sys.exit(1)

    row = matches.iloc[0]

    # --------------------------------------------------------
    # 4. Build V2 record
    # --------------------------------------------------------

    record = create_empty_evidence_record(
        pmid=row["pmid"],
        title=row["title"],
        abstract=row["abstract"],
    )

    source_text = build_source_text(
        row["title"],
        row["abstract"],
    )

    # --------------------------------------------------------
    # 5. Validate record
    # --------------------------------------------------------

    errors = validate_record(record, schema)

    if errors:
        print("SCHEMA VALIDATION: FAIL")

        for error in errors:
            location = ".".join(str(x) for x in error.path)

            if not location:
                location = "root"

            print(f"- {location}: {error.message}")

        sys.exit(1)

    # --------------------------------------------------------
    # 6. Success
    # --------------------------------------------------------

    print("SCHEMA VALIDATION: PASS")
    print("Paper loaded successfully.")
    print("PMID:", record["paper_identity"]["pmid"])
    print("Title:", record["paper_identity"]["title"])
    print("Source text length:", len(source_text))

    # --------------------------------------------------------
    # 7. Save validated V2 evidence record
    # --------------------------------------------------------

    output_dir = BASE_DIR / "data" / "processed" / "v2"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = (
        output_dir
        / f"PMID_{record['paper_identity']['pmid']}_evidence_v2.json"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            record,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("V2 evidence record saved:")
    print(output_path)
