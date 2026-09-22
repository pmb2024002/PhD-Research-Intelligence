"""
Mitochondrial Research Intelligence
V2 Batch Runner

Runs the V2 extraction pipeline (run_research_model_v2.run_paper)
across multiple papers from the labeling dataset, saving each
paper's validated record as its own JSON file.

A failure on one paper (timeout, invalid JSON, schema mismatch)
does not stop the batch -- it is logged and the batch continues.

Usage:
    RESEARCH_MODEL_PROVIDER=ollama python pipeline/v2/run_batch_v2.py 5
    (runs the first 5 papers in the dataset; defaults to 5 if no
    argument given)
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from run_research_model_v2 import run_paper, DATASET_PATH, BASE_DIR


OUTPUT_DIR = BASE_DIR / "data" / "processed" / "v2"


def run_batch(n):

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATASET_PATH)
    pmids = df["pmid"].head(n).tolist()

    print("============================================")
    print(f"V2 BATCH RUNNER -- {len(pmids)} papers")
    print("============================================")

    results = []

    for i, pmid in enumerate(pmids, start=1):

        print()
        print(f"[{i}/{len(pmids)}] PMID {pmid}")
        print("--------------------------------------------")

        try:
            record = run_paper(pmid)

        except Exception as exc:

            print(f"FAILED: {exc}")

            results.append({
                "pmid": int(pmid),
                "status": "failed",
                "error": str(exc),
            })

            continue

        if record is None:

            results.append({
                "pmid": int(pmid),
                "status": "failed",
                "error": "model execution stopped (see log above)",
            })

            continue

        out_path = OUTPUT_DIR / f"PMID_{pmid}_evidence_v2.json"

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        results.append({
            "pmid": int(pmid),
            "status": "success",
            "path": str(out_path),
        })

        print(f"Saved: {out_path}")

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------

    succeeded = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "failed"]

    print()
    print("============================================")
    print("BATCH SUMMARY")
    print("============================================")
    print(f"Succeeded: {len(succeeded)}/{len(results)}")
    print(f"Failed:    {len(failed)}/{len(results)}")

    if failed:
        print()
        print("Failed PMIDs:")
        for r in failed:
            print(f"- {r['pmid']}: {r['error']}")

    summary_path = OUTPUT_DIR / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print()
    print(f"Summary saved: {summary_path}")

    return results


if __name__ == "__main__":

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    run_batch(n)
