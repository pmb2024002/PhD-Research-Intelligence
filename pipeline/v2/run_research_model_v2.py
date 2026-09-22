"""
Mitochondrial Research Intelligence
V2 Research Model Runner

Pipeline:

Paper
  ↓
Prompt specification
  ↓
Research Model adapter
  ↓
Structured JSON
  ↓
paper_identity overwritten with verified dataset metadata
  ↓
Schema validation
  ↓
Evidence record

No model provider is hard-coded here.
"""

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd
from jsonschema import Draft202012Validator

from research_model_adapter_v2 import get_model_adapter
from research_model_prompt_v2 import SYSTEM_PROMPT, build_extraction_prompt


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


def load_schema():
    """Load the V2 JSON schema."""

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_paper(pmid):
    """Load one paper from the existing dataset."""

    df = pd.read_csv(DATASET_PATH)

    matches = df[df["pmid"] == pmid]

    if matches.empty:
        raise ValueError(
            f"PMID {pmid} was not found in {DATASET_PATH}"
        )

    return matches.iloc[0]


def build_paper_identity(row):
    """
    Build paper_identity directly from verified dataset metadata.

    This is intentionally NOT left to the model: the model was only
    given title + abstract, so any PMID/authors/journal/DOI/date it
    produced would be fabricated (confirmed via manual testing, where
    the model invented a different PMID, journal, and authors).
    """

    authors_raw = row.get("authors", "")

    if pd.isna(authors_raw) or not str(authors_raw).strip():
        authors = []
    else:
        authors = [a.strip() for a in str(authors_raw).split(",") if a.strip()]

    def clean(value):
        if pd.isna(value):
            return ""
        return str(value)

    return {
        "pmid": clean(row.get("pmid", "")),
        "title": clean(row.get("title", "")),
        "authors": authors,
        "journal": clean(row.get("journal", "")),
        "publication_date": clean(row.get("publication_date", "")),
        "doi": clean(row.get("doi", "")),
        "pubmed_url": clean(row.get("pubmed_url", "")),
        "source": "PubMed",
        "retrieval_date": date.today().isoformat(),
    }

INTERVENTION_KEYWORDS = [
    "extract", "compound", "blend", "formulation", "therapeutic candidate",
    "drug", "inhibitor", "agonist", "administration of", "treatment with",
    "supplementation", "restored", "restores", "rescued", "rescues",
]


def flag_direction_review(row, model_output):
    """
    Heuristic safeguard: qwen3:4b has been observed to misreport a
    gene's "direction" as a baseline disease-state finding when the
    paper actually only describes an intervention's mechanism of
    action (confirmed on PMID 42682802, where a herbal extract blend's
    pathway-activation language was wrongly reported as baseline
    upregulation in senescent cells).

    This is a known model limitation that a clarified prompt did NOT
    fix (tested and confirmed still wrong after the prompt fix). Since
    it cannot currently be reliably prevented at generation time, this
    flags likely-affected papers for manual review instead of trusting
    the model's "direction" field blindly.

    This is a coarse keyword heuristic, not a guarantee: it may flag
    papers that are actually fine, and may miss some that are not. It
    exists to make review, not certainty, tractable.
    """

    abstract = str(row.get("abstract", "")).lower()

    hit_keywords = [kw for kw in INTERVENTION_KEYWORDS if kw in abstract]

    return {
        "direction_may_reflect_intervention_not_baseline": bool(hit_keywords),
        "matched_keywords": hit_keywords,
        "reason": (
            "Abstract contains intervention/treatment language; gene "
            "'direction' fields should be manually verified against the "
            "abstract before trusting them as baseline disease-state "
            "findings."
            if hit_keywords
            else "No intervention/treatment keywords detected; direction "
            "fields are more likely to reflect baseline state, but manual "
            "spot-checking is still recommended."
        ),
    }

def validate_model_output(record, schema):
    """
    Validate model output against the V2 schema.

    Returns validation errors.
    """

    validator = Draft202012Validator(schema)

    return sorted(
        validator.iter_errors(record),
        key=lambda error: list(error.path),
    )


def run_paper(pmid):
    """
    Run the complete V2 model pipeline for one paper.
    """

    print("============================================")
    print("V2 RESEARCH MODEL RUNNER")
    print("============================================")

    schema = load_schema()

    print("Schema loaded.")

    row = load_paper(pmid)

    print("Paper loaded.")
    print("PMID:", row["pmid"])
    print("Title:", row["title"])

    user_prompt = build_extraction_prompt(
        title=row["title"],
        abstract=row["abstract"],
    )

    print("Extraction prompt built.")
    print("Prompt length:", len(user_prompt))

    adapter = get_model_adapter()

    print(
        "Model adapter:",
        adapter.__class__.__name__,
    )

    try:

        model_output = adapter.analyze_paper(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

    except Exception as exc:

        print()
        print("MODEL EXECUTION STOPPED")
        print("----------------------")
        print(str(exc))

        return None

    if not isinstance(model_output, dict):

        raise TypeError(
            "Research Model output must be a JSON object."
        )

    # ----------------------------------------------------------------
    # Overwrite paper_identity with verified dataset metadata.
    # The model only sees title + abstract, so its own paper_identity
    # output is discarded here rather than trusted.
    # ----------------------------------------------------------------

    model_output["paper_identity"] = build_paper_identity(row)

    print("paper_identity overwritten with verified dataset metadata.")

    errors = validate_model_output(
        model_output,
        schema,
    )

    if errors:

        print("MODEL OUTPUT VALIDATION: FAIL")

        for error in errors:

            location = ".".join(
                str(x) for x in error.path
            )

            if not location:
                location = "root"

            print(
                f"- {location}: {error.message}"
            )

        raise ValueError(
            "Research Model returned schema-invalid output."
        )

    print("MODEL OUTPUT VALIDATION: PASS")

    review_flags = flag_direction_review(row, model_output)
    model_output["_review_flags"] = review_flags

    if review_flags["direction_may_reflect_intervention_not_baseline"]:
        print("FLAGGED: gene/protein 'direction' fields may need manual review")
        print("  Matched keywords:", review_flags["matched_keywords"])

    return model_output


if __name__ == "__main__":

    pmid = 42682802

    record = run_paper(pmid)

    if record is not None:

        print()
        print("V2 research model run completed.")
        print(
            json.dumps(
                record,
                indent=2,
                ensure_ascii=False,
            )
        )
