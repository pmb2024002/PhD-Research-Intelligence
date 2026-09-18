from pathlib import Path
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]

KB_FILE = PROJECT_ROOT / "data" / "knowledge_base" / "curated_phd_literature_kb_v1.csv"
GENE_ALIAS_FILE = PROJECT_ROOT / "config" / "gene_aliases.yaml"


def load_knowledge_base():
    if not KB_FILE.exists():
        raise FileNotFoundError(f"Knowledge base not found: {KB_FILE}")

    return pd.read_csv(KB_FILE).fillna("")


def load_gene_aliases():
    if not GENE_ALIAS_FILE.exists():
        raise FileNotFoundError(f"Gene alias file not found: {GENE_ALIAS_FILE}")

    with open(GENE_ALIAS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["canonical_genes"]


def get_kb_summary():
    df = load_knowledge_base()

    return {
        "references": len(df),
        "directly_relevant": int(
            (df["knowledge_role"] == "Directly relevant").sum()
        ),
        "mechanistically_relevant": int(
            (df["knowledge_role"] == "Mechanistically relevant").sum()
        ),
        "methodologically_relevant": int(
            (df["knowledge_role"] == "Methodologically relevant").sum()
        ),
        "background": int(
            (df["knowledge_role"] == "Background").sum()
        ),
        "peripheral": int(
            (df["knowledge_role"] == "Peripheral").sum()
        ),
        "canonical_genes": len(load_gene_aliases()),
    }


if __name__ == "__main__":
    print("Knowledge Base Loader Test")
    print("-" * 30)

    summary = get_kb_summary()

    for key, value in summary.items():
        print(f"{key}: {value}")
