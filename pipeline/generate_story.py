"""
Mitochondrial Research Intelligence
Research Story Generator

Synthesizes the canonical 250-paper dataset, the 80 V2 deep-evidence
extractions, and the live Supabase discovery log into one flowing,
narrative "story" of the current research landscape - regenerated
whenever a "Check for New Papers" run finds genuinely new papers.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "pipeline"))

CANONICAL_CSV = BASE_DIR / "data" / "production_v1" / "human_preference_layer_v1.csv"
V2_SUMMARY_CSV = BASE_DIR / "data" / "processed" / "v2" / "all_papers_v2_summary.csv"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


def _try_streamlit_secret(key: str) -> str:
    try:
        import streamlit as st
        return st.secrets.get(key, "")
    except Exception:
        return ""


def _get_groq_key() -> str:
    return GROQ_API_KEY or _try_streamlit_secret("GROQ_API_KEY")


def _truncate(text, limit):
    text = str(text) if text is not None else ""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."


def _build_context():
    """Assemble a heavily condensed text representation of the full
    corpus. Groq's request-size limit (HTTP 413 if exceeded) means this
    must stay compact - so titles and evidence notes are truncated and
    long lists are sampled rather than fully enumerated."""

    parts = []

    # --- V2 deep-evidence papers (richest, most compact summaries) ---
    v2_count = 0
    v2_pmids = set()
    MAX_V2_SHOWN = 80

    if V2_SUMMARY_CSV.exists():
        v2_df_full = pd.read_csv(V2_SUMMARY_CSV)
        v2_count = len(v2_df_full)
        v2_pmids = set(v2_df_full["pmid"].astype(str))
        v2_df = v2_df_full.head(MAX_V2_SHOWN)
        parts.append(
            f"=== {v2_count} PAPERS WITH DEEP EVIDENCE EXTRACTION "
            f"(showing {len(v2_df)}) ==="
        )
        for _, row in v2_df.iterrows():
            parts.append(
                f"- {_truncate(row.get('title', ''), 90)} | "
                f"Priority: {row.get('research_priority_category', 'unclear')} | "
                f"Evidence: {row.get('evidence_strength', 'unclear')} | "
                f"Genes: {_truncate(row.get('genes', 'unclear'), 40)} | "
                f"{_truncate(row.get('why_this_paper_matters', ''), 100)}"
            )

    # --- Canonical corpus beyond V2 (title-only, sampled) ---
    remaining_count = 0
    if CANONICAL_CSV.exists():
        canon_df = pd.read_csv(CANONICAL_CSV, usecols=["pmid", "title"])
        remaining = canon_df[~canon_df["pmid"].astype(str).isin(v2_pmids)]
        remaining_count = len(remaining)
        sample = remaining.head(80)
        parts.append(
            f"\n=== {remaining_count} ADDITIONAL CANONICAL PAPERS (titles only; "
            f"showing a sample of {len(sample)}) ==="
        )
        for _, row in sample.iterrows():
            parts.append(f"- {_truncate(row.get('title', ''), 70)}")

    # --- Live discovered papers from Supabase (latest 40) ---
    try:
        from supabase_client import get_client
        client = get_client()
        result = client.table("discovered_papers").select("title,discovered_at").order(
            "discovered_at", desc=True
        ).limit(40).execute()
        discovered = result.data or []
    except Exception:
        discovered = []

    if discovered:
        parts.append(
            f"\n=== RECENTLY AUTO-DISCOVERED PAPERS (newest research, latest {len(discovered)} shown) ==="
        )
        for row in discovered:
            parts.append(f"- {_truncate(row.get('title', ''), 70)}")

    total_count = v2_count + remaining_count + len(discovered)

    MAX_CONTEXT_CHARS = 28000  # keeps the Groq request safely under its payload limit
    full_context = "\n".join(parts)
    if len(full_context) > MAX_CONTEXT_CHARS:
        full_context = full_context[:MAX_CONTEXT_CHARS] + "\n... (truncated for length)"

    return full_context, total_count


STORY_PROMPT_TEMPLATE = """You are a scientific writing assistant helping a PhD researcher \
understand the current literature landscape of their own research area: \
"Multi-Omics Analysis of Mitochondrial Dysfunction in Cellular Senescence".

Below is a condensed inventory of the papers in their tracked corpus - the most \
deeply analyzed papers (with evidence strength, key genes, and why each matters), \
the rest of the canonical corpus (titles only), and the most recently \
auto-discovered new papers from PubMed.

Your task: write a flowing, engaging NARRATIVE (not a bullet list, not a table) \
that tells the "story" of this research field as it currently stands, organized \
into clear thematic sections with headers, such as:
- Mitochondrial dynamics & quality control (fission/fusion, mitophagy)
- Cellular senescence hallmarks and how mitochondria drive them
- Key genes and pathways recurring across the corpus
- Multi-omics and machine learning / AI approaches emerging in this space
- What the most recently discovered papers add to the picture

Write in clear, precise scientific English (not Hinglish), roughly 500-650 words \
TOTAL (this is a hard limit - stay concise and prioritize the most important points \
over completeness), using Markdown headers (##) for each section. Be specific - name \
genes, pathways, and paper themes you see in the data rather than writing generically. \
End with a short "What this means for the PhD research" paragraph connecting the \
literature to the multi-omics mitochondrial dysfunction / senescence research direction. \
Make sure you finish the final sentence - do not trail off mid-sentence.

CORPUS DATA:
{context}
"""


def generate_research_story() -> tuple[str, int]:
    """Returns (story_markdown, total_papers_covered)."""
    import requests

    context, total_count = _build_context()

    api_key = _get_groq_key()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not configured - cannot generate the research story.")

    prompt = STORY_PROMPT_TEMPLATE.format(context=context)

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "max_tokens": 1800,
        },
        timeout=90,
    )
    resp.raise_for_status()

    data = resp.json()
    story_text = data["choices"][0]["message"]["content"].strip()
    return story_text, total_count


def generate_and_save():
    story_text, total_count = generate_research_story()

    from supabase_client import save_research_story

    generated_at = (
        datetime.now(timezone.utc)
        .astimezone(ZoneInfo("Asia/Kolkata"))
        .strftime("%d %b %Y, %I:%M %p IST")
    )
    save_research_story(story_text, generated_at, total_count)
    print(f"Research story generated and saved ({total_count} papers covered).")
    return story_text


if __name__ == "__main__":
    generate_and_save()
