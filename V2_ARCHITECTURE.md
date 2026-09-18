# V2 ARCHITECTURE
# Mitochondrial Research Intelligence

Version: 2.0
Status: Architecture Specification
Purpose: Automatic scientific literature understanding and PhD research intelligence

---

## 1. SYSTEM OBJECTIVE

The V2 system will automatically collect scientific literature and transform each paper into a structured research-intelligence record.

The system is designed for:

- automatic literature collection
- paper-level scientific understanding
- structured evidence extraction
- mitochondrial biology interpretation
- cellular senescence interpretation
- mechanism extraction
- multi-omics interpretation
- PhD objective mapping
- research-gap identification
- relevance and priority assessment
- human verification
- benchmark creation
- future model evaluation and improvement

V2 must not depend primarily on manually written keyword rules for scientific interpretation.

The existing V1 deterministic pipeline will be retained as a baseline and supporting evidence layer.

---

## 2. CORE ARCHITECTURE

Literature Sources
        |
        v
Collector
        |
        v
Deduplication + Metadata QC
        |
        v
Research Model
        |
        v
Structured Scientific Evidence
        |
        v
Evidence Validation
        |
        v
PhD Objective Mapping
        |
        v
Mechanism / Findings / Gap Analysis
        |
        v
Relevance + Research Priority
        |
        v
Streamlit Dashboard
        |
        v
Human Verification
        |
        v
Verified Benchmark Dataset
        |
        +--------------------+
        |                    |
        v                    v
    Evaluation        Future Model Improvement

---

## 3. V1 AND V2 RELATIONSHIP

V1 is the existing deterministic baseline.

V1 components include:

- lexical evidence matching
- gene alias matching
- mitochondrial process matching
- senescence terminology matching
- model detection
- omics terminology detection
- biological scoring
- semantic scoring
- hybrid scoring
- PhD priority scoring
- O1-O5 rule-based mapping

V1 will NOT be deleted.

V1 outputs will be retained for:

- baseline comparison
- feature comparison
- quality control
- regression testing
- explainability
- benchmark analysis

V2 will provide a separate research-understanding layer.

V2 must not blindly reproduce V1 scores.

---

## 4. PAPER INPUT

Minimum input:

- PMID
- title
- abstract
- authors
- journal
- publication date
- DOI
- PubMed URL

Optional future inputs:

- full text
- supplementary information
- figures
- tables
- references
- citation information

V2 must clearly distinguish abstract-only analysis from full-text analysis.

---

## 5. PAPER IDENTITY OBJECT

Each paper must retain:

- pmid
- doi
- title
- authors
- journal
- publication_date
- journal_issue_date
- pubmed_url
- source
- retrieval_date

PMID should be the primary stable identifier where available.

---

## 6. BIOLOGICAL CONTEXT

The Research Model should extract:

- organism
- species
- cell type
- tissue
- organ
- disease
- disease context
- primary experimental model
- secondary models
- normal vs pathological context

For senescence studies:

- senescence model
- senescence trigger
- replicative senescence
- stress-induced senescence
- irradiation-induced senescence
- therapy-induced senescence
- other trigger

The model must distinguish the primary experimental context from incidental mentions.

---

## 7. SENESCENCE EVIDENCE

Extract:

- whether cellular senescence is experimentally investigated
- senescence trigger
- senescence markers
- phenotypic evidence
- growth arrest
- SA-beta-gal
- CDKN2A / p16
- CDKN1A / p21
- SASP
- DNA damage response
- other relevant markers

Evidence categories:

- direct experimental evidence
- indirect evidence
- background/contextual mention
- no meaningful evidence

---

## 8. MITOCHONDRIAL EVIDENCE

Extract mitochondrial involvement including:

- mitochondrial dysfunction
- mitochondrial dynamics
- mitochondrial fission
- mitochondrial fusion
- mitophagy
- mitochondrial quality control
- mitochondrial homeostasis
- mitochondrial biogenesis
- mitochondrial proteostasis
- mitochondrial membrane potential
- mitochondrial ROS
- oxidative stress
- mitochondrial metabolism
- mitochondrial morphology
- mitochondrial mass
- mitochondrial respiration
- ATP / bioenergetics

The system must distinguish:

- direct experimental evidence
- indirect evidence
- background mention
- absent evidence

---

## 9. MOLECULAR ENTITIES

Extract:

### Genes

- canonical gene symbol
- aliases
- direction/change if reported
- experimental role

### Proteins

- protein name
- gene association
- modification if relevant

### Pathways

- pathway name
- pathway database identifier where available

### Other entities

- metabolites
- drugs
- inhibitors
- activators
- mutations
- transcription factors

---

## 10. OMICS EVIDENCE

Identify:

- transcriptomics
- RNA-seq
- microarray
- single-cell transcriptomics
- proteomics
- metabolomics
- epigenomics
- phosphoproteomics
- other omics

The system must distinguish:

1. single modality
2. multiple modalities analyzed separately
3. multiple modalities statistically integrated
4. mechanistically integrated multi-omics

Merely mentioning the word "integration" must not be treated as proof of multi-omics integration.

---

## 11. EXPERIMENTAL DESIGN

Extract when available:

- experimental groups
- control groups
- treatment/intervention
- perturbation
- knockdown
- knockout
- overexpression
- inhibition
- rescue
- mutation
- time points
- biological system
- assays
- sequencing methods
- proteomic methods
- imaging methods
- functional assays

The model must distinguish an intervention from a descriptive observation.

---

## 12. MECHANISTIC REPRESENTATION

V2 must attempt to represent experimentally supported relationships as structured relationships.

Preferred representation:

CAUSE
  ->
INTERMEDIATE
  ->
EFFECT

Example:

DRP1 perturbation
  ->
mitochondrial dynamics alteration
  ->
ROS change
  ->
senescence phenotype

Mechanistic relationships must be classified as:

- experimentally supported
- author-proposed
- observational association
- inferred by model

Model inference must never be presented as experimentally demonstrated fact.

---

## 13. FINDINGS

Extract the major findings of the paper.

Each finding should ideally contain:

- finding statement
- entities involved
- direction
- experimental support
- evidence source
- confidence

The system must distinguish:

- positive finding
- negative finding
- null finding
- association
- causal/mechanistic finding

Negation must be explicitly handled.

---

## 14. EVIDENCE STRENGTH

Evidence should not be determined solely by keyword presence.

Suggested evidence dimensions:

- direct experimental evidence
- mechanistic perturbation
- replication
- orthogonal validation
- omics support
- functional validation
- consistency across experiments
- author conclusion
- limitation/uncertainty

Evidence strength should be represented separately from relevance.

---

## 15. PHD OBJECTIVES

The system will preserve the existing O1-O5 framework.

### O1
Conserved mitochondrial dysfunction signatures

### O2
Transcriptomic-proteomic / multi-omics integration

### O3
Mitochondrial hub genes

### O4
Conserved mitochondrial pathways

### O5
Mechanistic mitochondrial-senescence connection

For every objective, V2 should produce:

- objective relevance
- supporting evidence
- evidence strength
- explanation
- confidence

A paper may map to multiple objectives.

---

## 16. PHD RELEVANCE

PhD relevance must be separated from general biological importance.

Assess:

- direct relevance
- supporting relevance
- methodological relevance
- model relevance
- disease-context relevance
- peripheral relevance

Human IMR-90 fibroblast evidence should be distinguished from evidence obtained in other models.

Different models should reduce contextual relevance where appropriate, but should not automatically make a biologically informative paper irrelevant.

---

## 17. RESEARCH PRIORITY

V2 may produce a research-priority assessment after structured evidence extraction.

Priority must be derived from transparent components such as:

- biological relevance
- PhD objective alignment
- mechanistic evidence
- model relevance
- omics relevance
- methodological usefulness

The system must preserve the underlying evidence and components.

A single opaque score must not replace the evidence record.

---

## 18. RESEARCH GAP DETECTION

For each sufficiently informative paper, attempt to identify:

- unresolved question
- limitation
- missing experiment
- missing model
- missing omics modality
- missing mechanistic validation
- contradictory evidence
- unexplored biological connection
- potential future research direction

Research gaps must be labeled as:

- explicitly stated by authors
- inferred from stated limitations
- model-generated inference

Model-generated gaps must never be presented as author-stated gaps.

---

## 19. LIMITATIONS

Extract limitations when explicitly reported.

Examples:

- small sample size
- limited model
- lack of validation
- lack of mechanistic experiment
- single omics modality
- absence of human validation
- disease-specific context
- observational design

Do not invent limitations.

---

## 20. WHY THIS PAPER MATTERS

Generate a concise explanation based on extracted evidence.

The explanation should answer:

Why is this paper useful for the PhD research question?

It should reference concrete evidence rather than generic statements.

---

## 21. STRUCTURED OUTPUT

The Research Model should produce a structured JSON object.

Core structure:

{
  "paper_identity": {},
  "biological_context": {},
  "senescence": {},
  "mitochondrial": {},
  "molecular_entities": {},
  "omics": {},
  "experimental_design": {},
  "mechanism": [],
  "findings": [],
  "evidence_assessment": {},
  "limitations": [],
  "research_gap": [],
  "phd_objectives": {},
  "phd_relevance": {},
  "research_priority": {},
  "why_this_paper_matters": "",
  "confidence": {}
}

The JSON schema must be validated before database/dashboard insertion.

---

## 22. PROVENANCE

Every important model-derived claim should retain provenance whenever possible.

Preferred provenance levels:

- title
- abstract
- full text
- figure/table
- supplementary information
- reference/background
- model inference

The system must distinguish source evidence from model interpretation.

---

## 23. V1 BASELINE COMPARISON

For each paper where V1 and V2 are both available, retain:

- V1 evidence
- V2 evidence
- agreement
- disagreement
- human-verified resolution where available

Disagreement should be treated as an evaluation signal, not automatically as a V2 failure.

---

## 24. HUMAN FEEDBACK

Human feedback must be genuine and must not be generated from the model's own predictions.

Human review should allow:

- relevance correction
- evidence correction
- mechanism correction
- objective correction
- missing information
- reason/comment
- reviewer confidence

Human labels should retain provenance:

- reviewer
- date
- version
- reviewed fields

The existing hard-coded `write_human_labels.py` is NOT considered ground truth unless the labels have been independently reviewed and approved.

---

## 25. BENCHMARK DATASET

The current 250-paper corpus will be retained as the V1 benchmark/reference corpus.

The existing 80-paper pool will be treated as a candidate human-validation pool.

The 80 papers must not be called a supervised training dataset until genuine human labels have been collected and verified.

No model should be trained solely on its own previous predictions.

---

## 26. TRAINING STRATEGY

Initial V2 operation should prioritize inference and evaluation.

Future model improvement should use:

- verified human labels
- corrected evidence extraction
- corrected mechanism annotations
- corrected objective mappings
- high-confidence benchmark examples

Avoid:

- training directly on unverified model predictions
- treating V1 scores as scientific ground truth
- using hard-coded labels as human labels
- uncontrolled self-training

---

## 27. QUALITY CONTROL

Every paper should pass:

1. metadata validation
2. JSON schema validation
3. required-field validation
4. entity normalization
5. evidence/provenance validation
6. contradiction/negation checks
7. confidence checks

Invalid model output should be rejected or sent for review.

---

## 28. MODEL SAFETY AGAINST HALLUCINATION

The Research Model must not invent:

- experiments
- genes
- pathways
- findings
- mechanisms
- sample sizes
- model systems
- research gaps
- author conclusions

When information is unavailable:

Use:

"Not reported in available source"

rather than generating an assumption.

---

## 29. DASHBOARD DESIGN

Streamlit should expose:

### Paper overview
- title
- PMID
- journal
- date

### Biological context
- model
- trigger
- disease

### Mitochondrial evidence
- processes
- genes
- pathways

### Senescence evidence
- trigger
- markers
- phenotype

### Omics
- modalities
- integration level

### Mechanism
- causal chain

### Findings
- major findings

### Evidence
- evidence strength
- provenance
- confidence

### PhD mapping
- O1-O5

### Research intelligence
- relevance
- priority
- limitations
- research gaps
- why the paper matters

### Human review
- correction
- feedback
- confidence

---

## 30. DATA STORAGE

V2 should separate:

data/raw/
data/intermediate/
data/processed/
data/v2/
data/benchmark/
data/feedback/

Model-generated structured evidence should not overwrite raw source data.

Human-verified records should be versioned.

---

## 31. IMPLEMENTATION PRINCIPLE

Do not create many overlapping scripts with names such as:

- v2
- v2_pre
- v2_recovered
- batch_002
- batch_003
- final_v1
- final_v1_1

Each production component should have one canonical implementation.

Experimental scripts should be clearly separated from production code.

---

## 32. DEVELOPMENT ORDER

Implementation will proceed in this order:

Phase 1
- freeze V1
- create V2 directory structure
- define JSON schema

Phase 2
- build paper input/normalization layer
- build Research Model interface

Phase 3
- implement structured scientific extraction

Phase 4
- implement evidence validation

Phase 5
- implement O1-O5 mapping

Phase 6
- implement mechanism and research-gap extraction

Phase 7
- implement relevance and priority layer

Phase 8
- create human-review interface

Phase 9
- construct verified benchmark

Phase 10
- evaluate V2 against human annotations and V1 baseline

Phase 11
- integrate V2 into Streamlit

Phase 12
- expand automated literature collection

---

## 33. CURRENT PROJECT STATUS

V1:
- operational
- 250-paper canonical dataset
- deterministic evidence/scoring pipeline
- Streamlit dashboard deployed

Human labeling:
- 80-paper candidate pool exists
- current user labels are blank in the source pool
- hard-coded label writer exists
- hard-coded labels are not automatically considered ground truth

V2:
- architecture specification
- implementation not yet started

---

## 34. NON-NEGOTIABLE SCIENTIFIC PRINCIPLES

1. Evidence must be separated from inference.
2. Model predictions must not automatically become ground truth.
3. Human labels must be genuinely human-verified.
4. V1 scores are baseline outputs, not scientific truth.
5. Keyword detection is supporting evidence, not scientific interpretation.
6. Mechanistic claims require explicit evidence.
7. Model-generated inference must be labeled as inference.
8. Missing information must remain missing.
9. Raw data must never be overwritten by derived data.
10. Every important output should be traceable to its evidence source.
11. V2 must improve scientific understanding, not merely reproduce V1 scores.
12. Production code must remain reproducible and version controlled.

---

## 35. SUCCESS CRITERION

V2 will be considered successful when, for a newly collected scientific paper, it can automatically produce a validated and traceable research-intelligence record containing:

- what was studied
- in which biological model
- how senescence was induced or evaluated
- what happened to mitochondria
- which genes/proteins/pathways were involved
- what omics were performed
- what experiments were performed
- what the major findings were
- what mechanism is supported
- how strong the evidence is
- which PhD objectives it supports
- what limitations exist
- what research gaps remain
- why the paper matters to the PhD
- and how confident the system is

without presenting unsupported model inference as experimental fact.

---

# END OF V2 ARCHITECTURE SPECIFICATION
