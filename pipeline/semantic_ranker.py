import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "raw" / "pubmed_articles.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "pubmed_new_semantic_ranked.csv"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


RESEARCH_PROFILE = """
Multi-Omics Analysis of Mitochondrial Dysfunction in Cellular Senescence.

Core research areas:
cellular senescence, mitochondrial dysfunction, mitochondrial dynamics,
mitochondrial quality control, mitochondrial homeostasis, MiDAS,
transcriptomics, proteomics, multi-omics integration.

Priority genes:
DNM1L, DRP1, OPA1, MFN1, MFN2, PINK1, PRKN, PARK2.

Mitochondrial processes:
mitochondrial fission, mitochondrial fusion, mitophagy,
mitochondrial biogenesis, mitochondrial proteostasis,
mitochondrial quality control, mitochondrial membrane potential,
mitochondrial ROS.

Senescence processes:
SASP, p16, CDKN2A, p21, CDKN1A,
DNA damage response, DDR, replicative senescence,
stress-induced premature senescence, therapy-induced senescence.

Relevant signaling:
cGAS-STING, AMPK, mTOR, p53, p38 MAPK, NF-kB, NAD metabolism.

Relevant methods:
RNA-seq, transcriptomics, differential expression, DESeq2,
limma, edgeR, proteomics, multi-omics integration,
GSVA, ssGSEA, pathway enrichment, network analysis.

Relevant experimental models:
IMR-90, fibroblast, human fibroblast,
replicative senescence, irradiation-induced senescence,
DNA damage-induced senescence.

Research goal:
identify conserved mitochondrial dysfunction signatures in cellular
senescence, integrate transcriptomic and proteomic evidence,
identify mitochondrial hub genes and conserved pathways,
and investigate mechanisms connecting mitochondrial dysfunction with senescence.
"""


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def create_document_text(row):
    title = clean_text(row.get("title"))
    abstract = clean_text(row.get("abstract"))

    return f"Title: {title}\nAbstract: {abstract}"


def main():

    print("Loading explained PubMed results...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded {len(df)} papers.")

    print()
    print(f"Loading embedding model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    print("Creating research-profile embedding...")

    profile_embedding = model.encode(
        RESEARCH_PROFILE,
        normalize_embeddings=True
    )

    print("Creating paper embeddings...")

    documents = df.apply(create_document_text, axis=1).tolist()

    paper_embeddings = model.encode(
        documents,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    print("Calculating semantic similarity...")

    similarities = cosine_similarity(
        paper_embeddings,
        profile_embedding.reshape(1, -1)
    ).flatten()

    df["semantic_similarity"] = similarities

    df["semantic_rank"] = (
        df["semantic_similarity"]
        .rank(
            ascending=False,
            method="min"
        )
        .astype(int)
    )

    df = df.sort_values(
        by="semantic_similarity",
        ascending=False
    ).reset_index(drop=True)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8"
    )

    print()
    print("Top 5 papers by semantic similarity:")
    print()

    for i, row in df.head(5).iterrows():
        print(
            f"{i + 1}. "
            f"{row['semantic_similarity']:.4f} - "
            f"{row['title']}"
        )

    print()
    print(f"Saved semantic rankings to:")
    print(OUTPUT_FILE)

    print()
    print("Semantic ranking completed successfully.")


if __name__ == "__main__":
    main()
