from pathlib import Path
import re
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "raw" / "pubmed_articles_batch_002.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "phd_evidence_strength_batch_002.csv"

GENE_ALIAS_FILE = PROJECT_ROOT / "config" / "gene_aliases.yaml"


def load_gene_aliases():
    with open(GENE_ALIAS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["canonical_genes"]


def normalize(text):
    return str(text).lower()


def contains_any(text, terms):
    text = normalize(text)
    return any(re.search(r"\b" + re.escape(term.lower()) + r"\b", text)
               for term in terms)


def get_gene_evidence(text, genes):
    """
    Evidence levels:
    0 = no priority gene
    1 = priority gene mentioned
    2 = priority gene appears in an investigated/associated context
    3 = priority gene has a strong local mechanistic connection
        to a mitochondrial process and/or senescence
    """

    text = normalize(text)

    sentences = re.split(r"(?<=[.!?])\s+", text)

    found = []
    level = 0

    mechanistic_terms = [
        "knockdown",
        "knockout",
        "overexpression",
        "inhibition",
        "inhibitor",
        "inhibited",
        "silencing",
        "depletion",
        "depleted",
        "loss-of-function",
        "gain-of-function",
        "mutation",
        "mutant",
        "rescue",
        "rescued",
        "pharmacological inhibition",
        "genetic manipulation",
        "genetic deletion",
        "gene deletion",
    ]

    mitochondrial_terms = [
        "mitochondrial fission",
        "mitochondrial fusion",
        "mitophagy",
        "mitochondrial quality control",
        "mitochondrial dynamics",
        "mitochondrial dysfunction",
        "mitochondrial ros",
        "mitochondrial function",
    ]

    senescence_terms = [
        "cellular senescence",
        "senescence",
        "senescent",
        "senescence phenotype",
    ]

    experimental_gene_terms = [
        "knockdown",
        "knockout",
        "overexpression",
        "silencing",
        "inhibition",
        "inhibitor",
        "rescue",
        "depletion",
        "deficiency",
        "mutant",
        "mutation",
        "expression",
    ]

    for canonical, info in genes.items():
        aliases = info.get("aliases", [])

        gene_sentences = []

        for sentence in sentences:
            if any(
                re.search(
                    r"\b" + re.escape(alias.lower()) + r"\b",
                    sentence
                )
                for alias in aliases
            ):
                found.append(canonical)
                gene_sentences.append(sentence)

        if not gene_sentences:
            continue

        # Level 3:
        # Require the priority gene, a mitochondrial concept,
        # and a senescence concept in the SAME sentence,
        # together with mechanistic language.
        for sentence in gene_sentences:
            has_mito = contains_any(sentence, mitochondrial_terms)
            has_sen = contains_any(sentence, senescence_terms)
            has_mech = contains_any(sentence, mechanistic_terms)

            if has_mito and has_sen and has_mech:
                level = max(level, 3)

        # Level 2:
        # Gene appears in an experimentally investigated context,
        # even if a complete mitochondrial-senescence connection
        # is not established.
        if level < 3:
            for sentence in gene_sentences:
                if contains_any(sentence, experimental_gene_terms):
                    level = max(level, 2)

        # Level 1:
        # Gene is present but no stronger evidence was detected.
        if level == 0:
            level = 1

    return level, sorted(set(found))

def get_mitochondrial_process_evidence(text):
    text = normalize(text)

    processes = [
        "mitochondrial fission",
        "mitochondrial fusion",
        "mitochondrial dynamics",
        "mitophagy",
        "mitochondrial quality control",
        "mitochondrial homeostasis",
        "mitochondrial biogenesis",
        "mitochondrial proteostasis",
        "mitochondrial dysfunction",
        "mitochondrial membrane potential",
        "mitochondrial ros",
    ]

    sentences = re.split(r"(?<=[.!?])\s+", text)

    found = []

    for process in processes:
        if any(
            re.search(r"\b" + re.escape(process) + r"\b", sentence)
            for sentence in sentences
        ):
            found.append(process)

    if not found:
        return 0, []

    senescence_terms = [
        "cellular senescence",
        "senescence",
        "senescent",
        "senescence phenotype",
    ]

    mechanistic_terms = [
        "knockdown",
        "knockout",
        "overexpression",
        "inhibition",
        "inhibitor",
        "inhibited",
        "silencing",
        "depletion",
        "depleted",
        "loss-of-function",
        "gain-of-function",
        "mutation",
        "mutant",
        "rescue",
        "rescued",
        "pharmacological inhibition",
        "genetic manipulation",
        "genetic deletion",
        "gene deletion",
    ]

    # Level 3 requires a local mechanistic connection:
    # mitochondrial process + senescence + mechanistic language
    # must occur within the same sentence.
    strong_local_evidence = False

    for sentence in sentences:
        has_mito = any(
            re.search(r"\b" + re.escape(process) + r"\b", sentence)
            for process in processes
        )
        has_sen = contains_any(sentence, senescence_terms)
        has_mech = contains_any(sentence, mechanistic_terms)

        if has_mito and has_sen and has_mech:
            strong_local_evidence = True
            break

    if strong_local_evidence:
        level = 3
    else:
        # Level 2 means mitochondrial evidence and senescence
        # are both present, but a strong local mechanistic
        # connection was not detected.
        has_senescence = contains_any(text, senescence_terms)

        if has_senescence:
            level = 2
        else:
            level = 1

    return level, found

def get_senescence_evidence(text):
    text = normalize(text)

    terms = [
        "cellular senescence",
        "replicative senescence",
        "irradiation-induced senescence",
        "dna damage-induced senescence",
        "stress-induced premature senescence",
        "therapy-induced senescence",
        "senescence phenotype",
        "senescent cells",
        "senescent fibroblast",
    ]

    found = [t for t in terms if re.search(r"\b" + re.escape(t) + r"\b", text)]

    if not found:
        return 0, []

    experimental_terms = [
        "induced",
        "induction",
        "phenotype",
        "senescence-associated",
        "sa-beta-gal",
        "sa-β-gal",
        "cdkn2a",
        "p16",
        "cdkn1a",
        "p21",
        "growth arrest",
    ]

    mechanistic_terms = [
        "knockdown",
        "knockout",
        "overexpression",
        "inhibition",
        "inhibitor",
        "rescue",
        "mediated",
        "regulates",
        "regulating",
        "drives",
        "promotes",
        "attenuates",
    ]

    has_experimental = contains_any(text, experimental_terms)
    has_mechanistic = contains_any(text, mechanistic_terms)

    if has_mechanistic and has_experimental:
        level = 3
    elif has_experimental:
        level = 2
    else:
        level = 1

    return level, found


def get_model_evidence(text):
    text = normalize(text)

    if re.search(r"\bimr-90\b", text):
        return 3, ["IMR-90"]

    if contains_any(text, ["human fibroblast"]):
        return 2, ["human fibroblast"]

    if re.search(r"\bfibroblast\b", text):
        return 2, ["fibroblast"]

    relevant_other_models = [
        "rpe",
        "ovarian granulosa",
        "bovine cumulus",
        "bmsc",
        "chondrocyte",
        "skeletal muscle",
        "myocardial",
        "kidney",
        "cardiovascular",
    ]

    found = [m for m in relevant_other_models if re.search(r"\b" + re.escape(m) + r"\b", text)]

    if found:
        return 1, found

    return 0, []


def get_omics_evidence(text):
    text = normalize(text)

    # Prefix matching is intentional:
    # transcriptom -> transcriptome, transcriptomic, transcriptomics
    # proteom      -> proteome, proteomic, proteomics
    # metabolom    -> metabolome, metabolomic, metabolomics

    transcriptomics = (
        re.search(r"\btranscriptom\w*", text) is not None
        or re.search(r"\brna[- ]seq\b", text) is not None
        or "transcriptional profiling" in text
        or "transcriptional analysis" in text
    )

    proteomics = (
        re.search(r"\bproteom\w*", text) is not None
        or "mass spectrometry" in text
    )

    metabolomics = (
        re.search(r"\bmetabolom\w*", text) is not None
        or "metabolite profiling" in text
    )

    modalities = []

    if transcriptomics:
        modalities.append("transcriptomics")

    if proteomics:
        modalities.append("proteomics")

    if metabolomics:
        modalities.append("metabolomics")

    # Evidence level:
    # 0 = no omics evidence
    # 1 = one omics modality
    # 2 = multiple modalities detected
    # 3 = multiple modalities with explicit integration language

    if len(modalities) >= 2:
        integration_terms = [
            "multi-omics",
            "multiomics",
            "integrated multi-omics",
            "integrative multi-omics",
            "integration",
            "integrated analysis",
            "integrated analysis of",
        ]

        if any(term in text for term in integration_terms):
            level = 3
        else:
            level = 2

    elif len(modalities) == 1:
        level = 1

    else:
        level = 0

    return level, modalities


def analyze_paper(row, genes):
    title = str(row.get("title", ""))
    abstract = str(row.get("abstract", ""))

    text = f"{title} {abstract}"

    gene_level, found_genes = get_gene_evidence(text, genes)
    mito_level, found_processes = get_mitochondrial_process_evidence(text)
    sen_level, found_senescence = get_senescence_evidence(text)
    model_level, found_models = get_model_evidence(text)
    omics_level, found_omics = get_omics_evidence(text)

    return {
        "pmid": row.get("pmid", ""),
        "title": title,
        "gene_evidence_level": gene_level,
        "gene_evidence_genes": ";".join(found_genes),
        "mitochondrial_process_evidence_level": mito_level,
        "mitochondrial_process_evidence": ";".join(found_processes),
        "senescence_evidence_level": sen_level,
        "senescence_evidence": ";".join(found_senescence),
        "model_evidence_level": model_level,
        "model_evidence": ";".join(found_models),
        "omics_evidence_level": omics_level,
        "omics_evidence": ";".join(found_omics),
    }


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE).fillna("")
    genes = load_gene_aliases()

    results = [analyze_paper(row, genes) for _, row in df.iterrows()]

    out = pd.DataFrame(results)
    out.to_csv(OUTPUT_FILE, index=False)

    print("Evidence Strength Engine")
    print("=" * 50)
    print(f"Input papers: {len(df)}")
    print(f"Output: {OUTPUT_FILE}")
    print()
    print("Evidence level distributions:")

    for col in [
        "gene_evidence_level",
        "mitochondrial_process_evidence_level",
        "senescence_evidence_level",
        "model_evidence_level",
        "omics_evidence_level",
    ]:
        print(f"\n{col}")
        print(out[col].value_counts().sort_index().to_string())

    print("\nVALID")


if __name__ == "__main__":
    main()
