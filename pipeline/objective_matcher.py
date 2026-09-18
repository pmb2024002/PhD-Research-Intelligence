from pathlib import Path
import re
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OBJECTIVE_FILE = PROJECT_ROOT / "config" / "phd_objectives.yaml"
PUBMED_FILE = PROJECT_ROOT / "data" / "raw" / "pubmed_articles.csv"
FEEDBACK_FILE = PROJECT_ROOT / "data" / "processed" / "phd_feedback_dataset.csv"


def normalize(text):
    return str(text).lower()


def contains_any(text, terms):
    text = normalize(text)

    for term in terms:
        pattern = r"\b" + re.escape(term.lower()) + r"\b"
        if re.search(pattern, text):
            return True

    return False


def load_objectives():
    with open(OBJECTIVE_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["phd_objectives"]


def load_data():
    papers = pd.read_csv(PUBMED_FILE).fillna("")
    feedback = pd.read_csv(FEEDBACK_FILE).fillna("")

    df = papers.merge(
        feedback[["pmid", "user_relevance"]],
        on="pmid",
        how="left"
    )

    df["text"] = (
        df["title"].astype(str)
        + " "
        + df["abstract"].astype(str)
    )

    return df


def detect_objectives(df, objectives):

    for objective_id, objective in objectives.items():

        keywords = objective.get("keywords", [])
        genes = objective.get("genes", [])
        processes = objective.get("processes", [])

        df[objective_id] = False

        for idx, text in df["text"].items():

            keyword_match = contains_any(text, keywords)
            gene_match = contains_any(text, genes)
            process_match = contains_any(text, processes)

            if keyword_match or gene_match or process_match:
                df.loc[idx, objective_id] = True

    return df


def main():

    objectives = load_objectives()
    df = load_data()
    df = detect_objectives(df, objectives)

    objective_columns = list(objectives.keys())

    print("\nObjective Detection Summary")
    print("=" * 70)

    rates = df.groupby("user_relevance")[objective_columns].mean() * 100
    print(rates.round(1).to_string())

    print("\n\nObjective Feature Separation")
    print("=" * 70)

    for objective in objective_columns:

        relevant = df.loc[
            df["user_relevance"] == "Relevant",
            objective
        ].mean() * 100

        maybe = df.loc[
            df["user_relevance"] == "Maybe",
            objective
        ].mean() * 100

        not_relevant = df.loc[
            df["user_relevance"] == "Not Relevant",
            objective
        ].mean() * 100

        print(
            f"{objective}: "
            f"Relevant={relevant:.1f}% | "
            f"Maybe={maybe:.1f}% | "
            f"Not Relevant={not_relevant:.1f}%"
        )

    print("\n\nPaper-level Objective Detection")
    print("=" * 70)

    cols = [
        "pmid",
        "user_relevance",
        "title"
    ] + objective_columns

    print(
        df[cols]
        .sort_values(
            ["user_relevance"] + objective_columns,
            ascending=[True] + [False] * len(objective_columns)
        )
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
