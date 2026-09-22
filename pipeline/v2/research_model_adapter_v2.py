"""
Mitochondrial Research Intelligence
V2 Research Model Adapter

This module connects the provider-independent V2 adapter
to either the OpenAI Responses API or a local Ollama model.

API credentials are loaded from the environment.
They are never stored in source code.
"""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

import requests
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]

SCHEMA_PATH = (
    BASE_DIR
    / "schemas"
    / "v2"
    / "paper_evidence_schema_v2.json"
)


class ResearchModelAdapter(ABC):
    """Abstract interface for scientific paper extraction models."""

    @abstractmethod
    def analyze_paper(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """Analyze one scientific paper."""
        raise NotImplementedError


class OpenAIResearchModel(ResearchModelAdapter):
    """OpenAI-backed scientific research model."""

    def __init__(self, model: str = "gpt-5.6-sol"):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def analyze_paper(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:

        response = self.client.responses.create(
            model=self.model,
            instructions=system_prompt,
            input=user_prompt,
        )

        output_text = response.output_text

        if not output_text:
            raise RuntimeError("OpenAI returned an empty response.")

        try:
            return json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ValueError("OpenAI returned non-JSON output.") from exc


class OllamaResearchModel(ResearchModelAdapter):
    """
    Local Ollama-backed scientific research model.

    Notes:
    - Local calls to 127.0.0.1 must bypass any HTTP(S)_PROXY set
      in the environment, or the institutional proxy will block
      them (confirmed via manual curl testing).
    - "think": False is required so the JSON lands in the
      "response" field instead of the "thinking" field
      (confirmed via manual testing on qwen3:4b).
    - The full JSON schema is passed as the "format" parameter
      (not just the string "json"). This forces Ollama to use
      grammar-constrained decoding so the output structurally
      matches the schema exactly, instead of the model inventing
      its own flat/simplified field names.
    """

    def __init__(
        self,
        model: str = None,
        host: str = None,
        timeout: int = 900,
    ):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3:4b")
        self.host = host or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        self.timeout = timeout
        self.no_proxy = {"http": None, "https": None}

        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            self._schema = json.load(f)

    def analyze_paper(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:

        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "format": self._schema,
            "stream": False,
            "think": False,
        }

        try:
            resp = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                proxies=self.no_proxy,
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

        data = resp.json()
        output_text = data.get("response", "").strip()

        if not output_text:
            output_text = data.get("thinking", "").strip()

        if not output_text:
            raise RuntimeError("Ollama returned an empty response.")

        try:
            return json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Ollama returned non-JSON output: {output_text[:500]}"
            ) from exc


def get_model_adapter() -> ResearchModelAdapter:
    """Return the configured Research Model adapter."""

    provider = os.getenv("RESEARCH_MODEL_PROVIDER", "openai").lower()

    if provider == "openai":
        return OpenAIResearchModel()

    if provider == "ollama":
        return OllamaResearchModel()

    raise RuntimeError(f"Unsupported Research Model provider: {provider}")


if __name__ == "__main__":

    adapter = get_model_adapter()

    print("V2 Research Model adapter loaded.")
    print("Adapter:", adapter.__class__.__name__)
    print("Model:", adapter.model)

    if isinstance(adapter, OpenAIResearchModel):
        print("API key configured:", bool(os.getenv("OPENAI_API_KEY")))
    elif isinstance(adapter, OllamaResearchModel):
        print("Ollama host:", adapter.host)
