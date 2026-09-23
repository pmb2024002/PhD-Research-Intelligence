"""
Mitochondrial Research Intelligence
Quick Analyze — lightweight, fast paper summary for newly-discovered
papers (NOT the full V2 pipeline).

Uses a tiny 3-field schema (key_findings, relevance, conclusion)
instead of the full V2 evidence schema, so it runs in ~20-60 seconds
on CPU instead of ~10-15 minutes.
"""

import json
import os

import requests


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")

QUICK_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["key_findings", "relevance", "conclusion"],
    "properties": {
        "key_findings": {"type": "string"},
        "relevance": {"type": "string"},
        "conclusion": {"type": "string"},
    },
}

RESEARCH_FOCUS = (
    "Multi-Omics Analysis of Mitochondrial Dysfunction in "
    "Cellular Senescence"
)


def quick_analyze_paper(title: str, abstract: str, timeout: int = 120):
    """
    Return a quick, lightweight summary of a paper's key findings,
    relevance to the PhD research focus, and a brief conclusion --
    using ONLY the abstract. Not a substitute for the full V2
    pipeline; intended for fast triage of newly-discovered papers.
    """

    prompt = f"""
Analyze this paper for a PhD research project focused on:
"{RESEARCH_FOCUS}"

TITLE: {title}

ABSTRACT: {abstract}

Using ONLY information in the abstract above, provide:
- key_findings: 2-3 sentences summarizing the main findings.
- relevance: 1-2 sentences on how this relates to mitochondrial
  dysfunction and cellular senescence research. If it is not clearly
  related, say so plainly rather than forcing a connection.
- conclusion: 1-2 sentence brief conclusion of what the paper shows.

Do not invent details not present in the abstract.
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "format": QUICK_SCHEMA,
        "stream": False,
        "think": False,
    }

    resp = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json=payload,
        proxies={"http": None, "https": None},
        timeout=timeout,
    )
    resp.raise_for_status()

    data = resp.json()
    output_text = data.get("response", "").strip()

    if not output_text:
        raise RuntimeError("Ollama returned an empty response.")

    return json.loads(output_text)
