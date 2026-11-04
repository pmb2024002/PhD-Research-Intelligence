"""
Mitochondrial Research Intelligence
Quick Analyze — lightweight, fast paper summary for newly-discovered
papers (NOT the full V2 pipeline).

Supports two providers:
- Groq (cloud, free tier) -- used automatically when GROQ_API_KEY is
  available (via Streamlit secrets or environment variable). This is
  what runs on the deployed Streamlit Cloud site, since Ollama is not
  available there.
- Ollama (local) -- fallback when no Groq key is configured, for
  fully local/offline use.

Uses a tiny 3-field output (key_findings, relevance, conclusion)
instead of the full V2 evidence schema, so it runs in seconds rather
than the ~10-15 minutes the full V2 pipeline takes.
"""

import json
import os
import time

import requests

try:
    import streamlit as st
except ImportError:
    st = None


def _get_secret(name):
    """Read a secret from Streamlit secrets first, then env vars."""
    if st is not None:
        try:
            if name in st.secrets:
                return str(st.secrets[name]).strip()
        except Exception:
            pass
    return os.getenv(name)


GROQ_API_KEY = _get_secret("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")

RESEARCH_FOCUS = (
    "Multi-Omics Analysis of Mitochondrial Dysfunction in "
    "Cellular Senescence. Central question: which senescence "
    "programs in human fibroblasts depend on mitochondria, which "
    "genes are their hubs, and do interventions reverse them?"
)

QUICK_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "key_findings",
        "relevance",
        "conclusion",
        "plain_summary",
        "paper_type",
        "novelty",
        "thesis_relevance",
    ],
    "properties": {
        "key_findings": {"type": "string"},
        "relevance": {"type": "string"},
        "conclusion": {"type": "string"},
        "plain_summary": {"type": "string"},
        "paper_type": {
            "type": "string",
            "enum": [
                "Methodology",
                "Novel Finding",
                "Conceptual Framework",
                "Review",
            ],
        },
        "novelty": {
            "type": "string",
            "enum": ["High", "Moderate", "Established"],
        },
        "thesis_relevance": {
            "type": "string",
            "enum": ["High", "Medium", "Low"],
        },
    },
}


def _build_prompt(title: str, abstract: str) -> str:
    return f"""
Analyze this paper for a PhD research project focused on:
"{RESEARCH_FOCUS}"

TITLE: {title}

ABSTRACT: {abstract}

Using ONLY information in the abstract above, respond with a JSON
object with EXACTLY these seven keys (no other keys, no markdown,
no code fences -- just the raw JSON object):

- "key_findings": 2-3 sentences summarizing the main findings.
- "relevance": 1-2 sentences on how this relates to mitochondrial
  dysfunction and cellular senescence research. Only say the paper
  addresses mitochondria or senescence if the abstract EXPLICITLY
  says so. If it does not, say plainly that it does not, rather
  than forcing a connection.
- "conclusion": 1-2 sentence brief conclusion of what the paper shows.
- "plain_summary": 3-4 sentences explaining what this paper found and
  why it matters, written for someone NEW to the field. Avoid or
  briefly define jargon (e.g. instead of just "mitophagy", say
  "mitophagy (the cell's process for clearing out damaged
  mitochondria)"). Prioritize being easy to understand over being
  technically dense.
- "paper_type": classify as exactly one of "Methodology" (introduces
  or validates a method, assay, model, or analytical technique),
  "Novel Finding" (reports a genuinely new result, mechanism, or
  discovery not previously well-established), "Conceptual Framework"
  (proposes a model, hypothesis, or way of thinking about the field
  rather than new data), or "Review" (summarizes/synthesizes existing
  literature rather than presenting new primary results).
- "novelty": rate as exactly one of "High" (challenges or extends
  established understanding in a significant way), "Moderate" (adds
  incremental evidence to an existing line of work), or "Established"
  (confirms or applies already well-known findings/mechanisms).
  Base this ONLY on what the abstract itself claims -- do not guess
  beyond what is stated.
- "thesis_relevance": usefulness for the PhD focus above, as exactly
  one of "High", "Medium" or "Low". "High": the abstract itself shows
  that a senescence program (for example SASP, mtDNA release,
  mitophagy, mitochondrial calcium, mtDNA repair) depends on
  mitochondria, especially by perturbing mitochondria (removal,
  inhibitors, knockdown) or by multi-omics (RNA-seq, proteomics,
  phosphoproteomics, single-cell) of senescent human cells.
  "Medium": mitochondria or senescence is central and the other is
  only linked; OR a compound or intervention changes senescence;
  OR a computational / multi-omics method that could be applied to
  senescence data. "Low": mitochondria and senescence are only
  mentioned in passing, or the paper is mainly about an unrelated
  disease or process. Judge ONLY from the abstract.

Do not invent details not present in the abstract.
"""


def _analyze_with_groq(title: str, abstract: str, timeout: int = 60):

    prompt = _build_prompt(title, abstract)

    _url = "https://api.groq.com/openai/v1/chat/completions"
    _headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    _body = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
        "reasoning_effort": "low",
        "max_completion_tokens": 4096,
    }

    resp = requests.post(_url, headers=_headers, json=_body, timeout=timeout)

    _tries = 0
    while resp.status_code == 429 and _tries < 2:
        try:
            _wait = float(resp.headers.get("retry-after", "10"))
        except ValueError:
            _wait = 10.0
        time.sleep(min(_wait, 20.0) + 1.0)
        resp = requests.post(
            _url, headers=_headers, json=_body, timeout=timeout
        )
        _tries += 1

    if resp.status_code == 429:
        raise RuntimeError(
            "Groq free-tier rate limit reached. Wait about a minute "
            "and try again."
        )
    if resp.status_code == 401:
        raise RuntimeError(
            "Groq rejected the API key. Check GROQ_API_KEY in Secrets "
            "and reboot the app."
        )
    if resp.status_code == 400:
        resp = requests.post(
            _url, headers=_headers,
            json=dict(_body, temperature=0.3), timeout=timeout
        )
    if resp.status_code == 400:
        raise RuntimeError(f"Groq 400: {resp.text[:300]}")
    resp.raise_for_status()

    data = resp.json()
    content = data["choices"][0]["message"]["content"]

    return json.loads(content)


def _analyze_with_ollama(title: str, abstract: str, timeout: int = 120):

    prompt = _build_prompt(title, abstract)

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


def quick_analyze_paper(title: str, abstract: str, timeout: int = 120):
    """
    Return a quick, lightweight summary of a paper's key findings,
    relevance to the PhD research focus, and a brief conclusion.

    Uses Groq (cloud) when GROQ_API_KEY is configured, otherwise
    falls back to local Ollama.
    """

    if GROQ_API_KEY:
        return _analyze_with_groq(title, abstract, timeout=min(timeout, 60))

    return _analyze_with_ollama(title, abstract, timeout=timeout)
