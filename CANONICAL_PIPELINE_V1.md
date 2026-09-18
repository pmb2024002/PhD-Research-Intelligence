# PhD Research Intelligence System
# Canonical Pipeline Specification V1

## 1. Purpose

This document defines the single canonical production pipeline
for the PhD Research Intelligence System.

Historical experiments, backups, checkpoints, and obsolete branches
must not be used by the production application.

---

## 2. Research Scope

Research Title:

Multi-Omics Analysis of Mitochondrial Dysfunction in Cellular Senescence

Primary purpose:

Automatically retrieve, evaluate, prioritize, explain, and present
literature relevant to the PhD research program.

---

## 3. Canonical Production Architecture

Literature Retrieval
        ↓
Canonical Paper Table
        ↓
Evidence Extraction
        ↓
Semantic Relevance
        ↓
Mechanistic Evidence
        ↓
Scientific Priority
        ↓
Human Preference / Personalization
        ↓
Explanation
        ↓
Streamlit Application

---

## 4. Canonical Data Layers

### Layer 1 — Raw Literature

Location:

data/raw/

Purpose:

Store source PubMed records exactly as retrieved.

Canonical fields:

- PMID
- title
- abstract
- authors
- journal
- publication_date
- journal_issue_date
- DOI
- PubMed URL

Raw data must never be manually altered.

---

## 5. Canonical Evidence Layer

Purpose:

Convert paper text into structured biological evidence.

Required evidence dimensions:

- priority gene evidence
- mitochondrial process evidence
- senescence evidence
- experimental model evidence
- omics evidence

Evidence levels:

0 = absent
1 = mentioned
2 = investigated/associated
3 = strong/direct/mechanistic evidence

Keyword presence must not automatically be interpreted as
mechanistic evidence.

---

## 6. Canonical Semantic Layer

Model:

sentence-transformers/all-MiniLM-L6-v2

Input:

Paper title + abstract

Reference:

Canonical PhD research profile

Output:

semantic_similarity

Semantic similarity is a prioritization signal and not a biological
mechanistic proof.

---

## 7. Canonical Mechanistic Layer

Purpose:

Identify stronger causal/mechanistic relationships.

Important evidence:

- perturbation
- rescue
- mitochondrial phenotype
- senescence phenotype
- causal link
- mechanistic evidence level

Mechanistic evidence must be kept separate from simple keyword evidence.

---

## 8. Canonical Scientific Priority Layer

Scientific priority must combine:

- direct mitochondrial-senescence relevance
- mitochondrial mechanism
- priority hub genes
- experimental model relevance
- omics relevance
- PhD objective alignment
- transferable biology
- peripheral/disease context

No single keyword or gene mention may determine priority by itself.

---

## 9. Human Preference Layer

Human labels currently available:

- Relevant
- Maybe
- Not Relevant

Current annotation dataset:

110 papers

Class distribution:

Relevant = 31
Maybe = 67
Not Relevant = 12

The current 110-paper dataset is informatively sampled and therefore
must not be treated as an independent representative benchmark of
the entire literature.

Human labels are used for personalization/calibration, not as a
replacement for the scientific evidence engine.

---

## 10. ML Status

Historical ML versions V5–V18 are exploratory analyses.

They are NOT production models.

The following must not be presented as final validated model
performance:

- V7 balanced accuracy
- V8 threshold results
- V14 repeated validation
- V15 holdout
- V17 diagnostics
- V18 diagnostics

A production personalization model may only be activated after
a separate validation decision.

---

## 11. Excluded ML Predictors

The following baseline/composite variables must not be used as
independent predictors when their component variables are already
present:

- biological_score
- biological_score_normalized
- hybrid_score
- final_phd_priority_score
- final_phd_rank
- final_priority_category
- phd_priority_feature_score
- research_priority

Reason:

Composite scores duplicate information already represented by
component evidence features.

---

## 12. Human Reason Field

user_reason is retained for provenance.

Current reasons contain only three repeated templates and therefore
must not be treated as rich paper-specific rationale.

Do not use user_reason as an ML predictor.

---

## 13. Knowledge Base

Canonical knowledge resources:

- curated_phd_literature_kb_v1.csv
- gene_aliases.yaml
- phd_evidence_ontology.yaml
- phd_relevance_ontology.yaml
- phd_objectives.yaml
- mechanistic_rules.yaml

These resources define the biological vocabulary and evidence framework.

---

## 14. Configuration Principle

One authoritative version of each concept must eventually exist.

Avoid parallel active definitions of:

- relevance
- priority
- evidence
- mechanistic strength
- utility

Historical versions may be archived but must not silently feed production.

---

## 15. Website Principle

The Streamlit website must consume only the canonical production
dataset.

The current legacy application dependency on:

- pubmed_explained.csv
- phd_feedback_dataset.csv

must be replaced during the production integration phase.

The 20-paper legacy dataset must not be treated as the production
literature database.

---

## 16. Historical Files

Historical scripts, backups, checkpoints, and experimental outputs
must be preserved until their role has been documented.

Do not delete them during cleanup.

Move them to an archive structure only after the canonical pipeline
has been verified.

---

## 17. Reproducibility Requirements

Every canonical production stage must have:

- one input
- one documented output
- versioned configuration
- deterministic/random seed where applicable
- clear execution order
- provenance record

The final production pipeline must be runnable from a clean
environment.

---

## 18. Current Status

Literature retrieval:
PARTIALLY COMPLETE

Evidence engine:
COMPLETE / NEEDS CONSOLIDATION

Semantic ranking:
COMPLETE / NEEDS CONSOLIDATION

Mechanistic layer:
PARTIALLY INTEGRATED

Scientific priority:
PARTIALLY COMPLETE

Human annotation:
COMPLETE FOR CURRENT 110 PAPERS

Personalization:
NOT FINAL

ML validation:
NOT FINAL

Website:
NOT INTEGRATED WITH CANONICAL PIPELINE

Project organization:
NEEDS CLEANUP

Reproducibility:
NEEDS COMPLETION

---

## 19. Production Rule

Only components explicitly designated as canonical may be used
by the final Streamlit application.

Historical experiments must remain separate from production.

---

## 20. Freeze Rule

No new ML model version should be created unless:

1. data provenance is documented,
2. feature provenance is documented,
3. validation design is approved,
4. the previous experiment is formally assessed,
5. the new experiment answers a clearly defined scientific question.
