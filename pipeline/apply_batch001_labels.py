import pandas as pd

INPUT = "data/processed/phd_active_labeling_pool_v1_labeled.csv"
OUTPUT = "data/processed/phd_active_labeling_pool_v1_labeled.csv"

LABELS = {
    42212306: "Relevant",
    42218500: "Relevant",
    41990575: "Relevant",
    42422171: "Relevant",
    42394134: "Relevant",
    42518074: "Maybe",
    42066913: "Maybe",
    42346293: "Maybe",
    42363074: "Relevant",
    42477782: "Maybe",
    42459658: "Relevant",
    42510561: "Maybe",
    42375085: "Maybe",
    42104610: "Not Relevant",
    42359697: "Maybe",
    42343000: "Maybe",
    42329074: "Maybe",
    42257494: "Relevant",
    42176571: "Not Relevant",
    42421742: "Maybe",
    42134737: "Maybe",
    42402137: "Maybe",
    42242294: "Relevant",
    42343432: "Not Relevant",
    42212533: "Not Relevant",
    42572354: "Relevant",
    42370305: "Not Relevant",
    42405213: "Not Relevant",
    42450045: "Not Relevant",
    42193955: "Not Relevant",
}

df = pd.read_csv(INPUT)

if len(df) != 30:
    raise ValueError(f"Expected 30 papers, found {len(df)}")

df["pmid"] = df["pmid"].astype(str)

label_map = {str(k): v for k, v in LABELS.items()}

missing = set(df["pmid"]) - set(label_map)

if missing:
    raise ValueError(f"Missing labels for PMIDs: {sorted(missing)}")

df["user_relevance"] = df["pmid"].map(label_map)

allowed = {"Relevant", "Maybe", "Not Relevant"}

invalid = set(df["user_relevance"].dropna()) - allowed

if invalid:
    raise ValueError(f"Invalid labels: {invalid}")

df.to_csv(OUTPUT, index=False, encoding="utf-8")

print("=" * 70)
print("BATCH 001 LABELS APPLIED")
print("=" * 70)

print("\nLabel distribution:")
print(df["user_relevance"].value_counts().to_string())

print("\nUnlabeled:", df["user_relevance"].isna().sum())

print("\nLabel verification:")
print(
    df[
        ["labeling_order", "pmid", "user_relevance"]
    ].sort_values("labeling_order").to_string(index=False)
)

print("\nSaved:")
print(OUTPUT)
