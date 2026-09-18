# PhD Research Intelligence System
# Canonical Component Map V1

## Purpose

This file defines which existing project components are:

KEEP       = current basis for production
REVIEW     = useful but requires technical/scientific verification
ARCHIVE    = historical experiment/backup/checkpoint
REPLACE    = obsolete production implementation
MISSING    = required production component not yet established

No file is deleted during this stage.

---

# 1. LITERATURE RETRIEVAL

Current scripts:

pipeline/pubmed_collector.py
pipeline/pubmed_collector_batch_003.py

Status:
REVIEW

Reason:
The PubMed retrieval system exists, but batch lineage is inconsistent.
pubmed_articles.csv and pubmed_articles_batch_002.csv are exact duplicates.

Required final state:
One canonical collector with explicit retrieval timestamp and batch ID.

---

# 2. CANONICAL LITERATURE TABLE

Status:
MISSING

Required production file:

data/processed/canonical_literature.csv

Minimum fields:

pmid
title
abstract
authors
journal
publication_date
journal_issue_date
doi
pubmed_url
source_batch
retrieval_date

Requirement:
One authoritative downstream paper table.

---

# 3. CURATED LITERATURE CORPUS AUDIT

Scripts:

pipeline/audit_literature_records_v4.py
pipeline/audit_literature_metadata_v5.py

Status:
KEEP

Reason:
These provide the strongest current audit of the 226-paper curated
literature collection.

Role:
Quality-control/audit only, not the live ranking pipeline.

---

# 4. EVIDENCE EXTRACTION

Canonical basis:

pipeline/evidence_strength.py

Status:
KEEP / REVIEW

Reason:
The evidence ontology distinguishes:

0 = absent
1 = mentioned
2 = investigated/associated
3 = strong/direct/mechanistic evidence

This is appropriate for the scientific problem.

Requirement:
Batch-specific copies should eventually be consolidated into one
canonical implementation.

---

# 5. BIOLOGICAL SCORE

Canonical basis:

pipeline/biological_score_v1.py

Status:
KEEP

Current formulation:

B = 4G + 6M + 6S + 3Mo + 3O

Bmax = 66

B_norm = B / 66

Important:
This composite score is derived from component evidence variables.
It must not be treated as independent information when the same
components are supplied separately to a small ML model.

Batch copies:

pipeline/biological_score_batch_002.py
pipeline/biological_score_batch_003.py

Status:
ARCHIVE after consolidation.

---

# 6. SEMANTIC RANKING

Canonical basis:

pipeline/semantic_ranker.py

Status:
KEEP / REVIEW

Model:

sentence-transformers/all-MiniLM-L6-v2

Input:

title + abstract

Reference:

research_profile.yaml

Output:

semantic_similarity

Requirement:
One canonical semantic implementation with reproducible model
identifier and profile version.

---

# 7. HYBRID RANKING

Canonical implementation:

pipeline/new_hybrid_ranker.py

Status:
KEEP / CANONICAL CANDIDATE

Verified formulation:

hybrid_score =
0.60 * biological_normalized
+
0.40 * semantic_normalized

Configuration:

config/canonical_hybrid_v1.yaml

Verification:
The regenerated canonical implementation was compared with
the previously verified priority-feature output for all 100 papers.

Rows compared: 100
Maximum hybrid-score difference: 0.0
Hybrid-rank mismatches: 0
Priority-category mismatches: 0

Therefore the implementation and configuration reproduce the
existing 100-paper hybrid results exactly.

Historical implementation:

pipeline/hybrid_ranker.py

Status:
ARCHIVE

Batch copies:

pipeline/new_hybrid_ranker_batch_002.py
pipeline/new_hybrid_ranker_batch_003.py

Status:
ARCHIVE after consolidation

Requirement:
Exactly one canonical hybrid implementation should remain active.

# 9A. HISTORICAL ALTERNATE RELEVANCE RANKER

Implementation:

pipeline/relevance_ranker.py

Status:
ARCHIVE

Reason:
This is an older keyword/profile/context-based scoring framework
with a different scoring architecture from the canonical hybrid engine.

It should not be combined with the canonical hybrid score.

Related configuration:

config/research_priority_weights.yaml

Status:
REVIEW

Reason:
The configuration contains useful PhD-specific concepts, but its
weights were designed for the historical relevance_ranker framework
and are not currently designated as the production scientific-priority
formula.
