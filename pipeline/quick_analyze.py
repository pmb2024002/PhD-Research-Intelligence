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
                return st.secrets[name]
        except Exception:
            pass
    return os.getenv(name)


GROQ_API_KEY = _get_secret("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")

RESEARCH_FOCUS = (
    "Multi-Omics Analysis of Mitochondrial Dysfunction in "
    "Cellular Senescence"
)

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


def _build_prompt(title: str, abstract: str) -> str:
    return f"""
Analyze this paper for a PhD research project focused on:
"{RESEARCH_FOCUS}"

TITLE: {title}

ABSTRACT: {abstract}

Using ONLY information in the abstract above, respond with a JSON
object with EXACTLY these three keys (no other keys, no markdown,
no code fences -- just the raw JSON object):

- "key_findings": 2-3 sentences summarizing the main findings.
- "relevance": 1-2 sentences on how this relates to mitochondrial
  dysfunction and cellular senescence research. If it is not clearly
  related, say so plainly rather than forcing a connection.
- "conclusion": 1-2 sentence brief conclusion of what the paper shows.

Do not invent details not present in the abstract.
"""


def _analyze_with_groq(title: str, abstract: str, timeout: int = 60):

    prompt = _build_prompt(title, abstract)

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        },
        timeout=timeout,
    )
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
