from pathlib import Path
import re
import pandas as pd

INPUT = Path("data/processed/references_pubmed_enriched.csv")
OUTPUT = Path("data/processed/references_mechanistic_evidence_142.csv")

df = pd.read_csv(INPUT)


def normalize(text):
    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def has_pattern(text, pattern):
    return bool(re.search(pattern, text, flags=re.IGNORECASE))
text = (
    df["title"].fillna("") + " " +
    df["abstract"].fillna("")
).map(normalize)

patterns = {
    "perturbation": r"knockdown|knockout|depletion|silencing|inhibition|inhibitor|deficiency|deletion|overexpression|activation|treatment|suppression",
    "rescue": r"rescue|rescues|reverses|reversal|restores|restoration|attenuates|ameliorates",
    "mito_phenotype": r"mitochondrial dysfunction|mitochondrial fragmentation|mitochondrial elongation|mitochondrial morphology|membrane potential|mitochondrial ros|mitochondrial oxidative stress|mitophagy",
    "senescence_phenotype": r"senesc\w* phenotype|senescent cells|cellular senescence|senescence",
    "causal_link": r"induces|drives|mediates|promotes|causes|contributes to|required for|dependent on|regulates"
}

for name, pattern in patterns.items():
    df[name] = text.map(lambda x: has_pattern(x, pattern))

def evidence_level(row):
    if (
        row["perturbation"]
        and row["mito_phenotype"]
        and row["senescence_phenotype"]
        and row["rescue"]
    ):
        return "E4"
    elif (
        row["perturbation"]
        and row["mito_phenotype"]
        and row["senescence_phenotype"]
    ):
        return "E3"
    elif (
        row["causal_link"]
        and row["mito_phenotype"]
        and row["senescence_phenotype"]
    ):
        return "E2"
    elif row["mito_phenotype"] and row["senescence_phenotype"]:
        return "E1"
    else:
        return "E0"

df["mechanistic_evidence_level"] = df.apply(evidence_level, axis=1)

df.to_csv(OUTPUT, index=False)

print(f"Input records: {len(df)}")
print(f"Output: {OUTPUT}")
print()
print(df["mechanistic_evidence_level"].value_counts().sort_index())

level_scores = {
    "E0": 0,
    "E1": 5,
    "E2": 10,
    "E3": 15,
    "E4": 20
}

df["mechanistic_score"] = df["mechanistic_evidence_level"].map(level_scores)

df.to_csv(OUTPUT, index=False)

print()
print("Mechanistic score distribution:")
print(df["mechanistic_score"].value_counts().sort_index())
