import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "pubmed_new_hybrid_ranked_batch_002.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "pubmed_phd_priority_features_batch_002.csv"
)


PRIMARY_GENES = {
    "DNM1L",
    "DRP1",
    "OPA1",
    "MFN1",
    "MFN2",
    "PINK1",
    "PRKN",
    "PARK2",
}


CORE_MITOCHONDRIAL_PROCESSES = {
    "mitochondrial fission",
    "mitochondrial fusion",
    "mitochondrial dynamics",
    "mitophagy",
    "mitochondrial quality control",
    "mitochondrial homeostasis",
    "mitochondrial biogenesis",
    "mitochondrial proteostasis",
    "mitochondrial membrane potential",
    "mitochondrial ros",
}


PREFERRED_MODELS = {
    "IMR-90",
    "human fibroblast",
    "fibroblast",
}


def split_terms(value):

    if pd.isna(value):
        return set()

    return {
        x.strip().lower()
        for x in str(value).split(";")
        if x.strip()
    }


def main():

    print("Loading hybrid-ranked literature...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded {len(df)} papers.")

    # ---------------------------------------------------------
    # Priority gene feature
    # ---------------------------------------------------------

    def priority_gene_count(value):

        genes = {
            x.strip().upper()
            for x in str(value).split(";")
            if x.strip()
        }

        return len(genes & PRIMARY_GENES)

    df["primary_gene_count"] = (
        df["gene_evidence_genes"]
        .fillna("")
        .apply(priority_gene_count)
    )

    df["primary_gene_present"] = (
        df["primary_gene_count"] > 0
    ).astype(int)

    # ---------------------------------------------------------
    # Mitochondrial mechanism feature
    # ---------------------------------------------------------

    def core_process_count(value):

        processes = split_terms(value)

        return len(
            processes & {
                x.lower()
                for x in CORE_MITOCHONDRIAL_PROCESSES
            }
        )

    df["core_mito_process_count"] = (
        df["mitochondrial_process_evidence"]
        .fillna("")
        .apply(core_process_count)
    )

    # ---------------------------------------------------------
    # Direct mitochondrial-senescence connection
    # ---------------------------------------------------------

    df["direct_mito_senescence"] = (
        (
            pd.to_numeric(
                df["mitochondrial_process_evidence_level"],
                errors="coerce"
            ).fillna(0) >= 2
        )
        &
        (
            pd.to_numeric(
                df["senescence_evidence_level"],
                errors="coerce"
            ).fillna(0) >= 2
        )
    ).astype(int)

    # ---------------------------------------------------------
    # Preferred experimental model
    # ---------------------------------------------------------

    def preferred_model(value):

        models = {
            x.strip().lower()
            for x in str(value).split(";")
            if x.strip()
        }

        return int(
            bool(
                models
                & {
                    x.lower()
                    for x in PREFERRED_MODELS
                }
            )
        )

    df["preferred_model_present"] = (
        df["model_evidence"]
        .fillna("")
        .apply(preferred_model)
    )

    # ---------------------------------------------------------
    # Multi-omics feature
    # ---------------------------------------------------------

    df["multiomics_present"] = (
        pd.to_numeric(
            df["omics_evidence_level"],
            errors="coerce"
        ).fillna(0) >= 2
    ).astype(int)

    # ---------------------------------------------------------
    # Mechanistic evidence proxy
    # ---------------------------------------------------------

    df["strong_biological_evidence"] = (
        (
            pd.to_numeric(
                df["mitochondrial_process_evidence_level"],
                errors="coerce"
            ).fillna(0) >= 3
        )
        &
        (
            pd.to_numeric(
                df["senescence_evidence_level"],
                errors="coerce"
            ).fillna(0) >= 3
        )
    ).astype(int)

    # ---------------------------------------------------------
    # Transparent feature score
    # ---------------------------------------------------------

    df["phd_priority_feature_score"] = (
        5 * df["direct_mito_senescence"]
        + 4 * df["primary_gene_present"]
        + 3 * df["preferred_model_present"]
        + 3 * df["multiomics_present"]
        + 2 * (
            df["core_mito_process_count"] > 0
        ).astype(int)
        + 2 * df["strong_biological_evidence"]
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,

        encoding="utf-8"
    )

    print()
    print("Feature summary:")
    print()

    print(
        f"Direct mito-senescence: "
        f"{df['direct_mito_senescence'].sum()}"
    )

    print(
        f"Primary-gene papers: "
        f"{df['primary_gene_present'].sum()}"
    )

    print(
        f"Preferred-model papers: "
        f"{df['preferred_model_present'].sum()}"
    )

    print(
        f"Multi-omics papers: "
        f"{df['multiomics_present'].sum()}"
    )

    print(
        f"Strong biological evidence: "
        f"{df['strong_biological_evidence'].sum()}"
    )

    print()
    print("Saved PhD-priority features to:")
    print(OUTPUT_FILE)

    print()
    print("PhD-priority feature extraction completed successfully.")


if __name__ == "__main__":
    main()
