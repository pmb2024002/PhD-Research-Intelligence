from pathlib import Path
import re
import pandas as pd

INPUT = Path("data/processed/references_142.txt")
OUTPUT = Path("data/processed/references_master.csv")

text = INPUT.read_text(encoding="utf-8")
references = re.split(r"\n(?=\[\d+\]\s)", text.strip())

rows = []

for ref in references:
    ref = ref.strip()

    number_match = re.match(r"\[(\d+)\]\s*", ref)
    if not number_match:
        continue

    reference_no = int(number_match.group(1))

    year_match = re.search(r"\((\d{4})\)\.", ref)
    year = int(year_match.group(1)) if year_match else None

    doi_match = re.search(r"https://doi\.org/([^\s]+)", ref)
    doi = doi_match.group(1).rstrip(".") if doi_match else None

    rows.append({
        "reference_no": reference_no,
        "year": year,
        "doi": doi,
        "citation_text": ref
    })

df = pd.DataFrame(rows)
df = df.sort_values("reference_no")

df.to_csv(OUTPUT, index=False)

print("References parsed:", len(df))
print("Reference range:", df["reference_no"].min(), "-", df["reference_no"].max())
print("DOIs found:", df["doi"].notna().sum())
print("Saved:", OUTPUT)
