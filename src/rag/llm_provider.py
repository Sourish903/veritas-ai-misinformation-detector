"""
Swappable LLM provider abstraction.

Implement the BaseLLMProvider interface to plug in any LLM.
Currently ships with:
  - GeminiProvider      (google-generativeai, free tier)
  - HuggingFaceProvider (HuggingFace Inference API, free tier)
  - OllamaProvider      (local Ollama server, completely free, no API key)
  - GroqProvider        (Groq cloud API, free tier, very fast)

Usage:
    provider = get_llm_provider("gemini", api_key="YOUR_KEY")
    provider = get_llm_provider("ollama", model="llama3.2")   # local, no key needed
    provider = get_llm_provider("groq", api_key="YOUR_KEY")
    response = provider.generate("What is misinformation?")
"""

import os
from abc import ABC, abstractmethod
from typing import Optional


# ---------------------------------------------------------------------------
# Base interface
# ---------------------------------------------------------------------------

class BaseLLMProvider(ABC):
    """All LLM providers must implement this single method."""

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.2) -> str:
        """Generate a text response for the given prompt."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"


# ---------------------------------------------------------------------------
# Gemini provider  (google-generativeai)
# ---------------------------------------------------------------------------

class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini via the google-generativeai SDK.

    Free tier supports Gemini 2.5 Flash and others.
    Get a key at: https://aistudio.google.com/app/apikey

    Args:
        api_key: Your Gemini API key. Falls back to GEMINI_API_KEY env var.
        model: Gemini model name. Default: gemini-2.5-flash-preview-04-17
    """

    DEFAULT_MODEL = "gemini-2.5-flash-preview-04-17"

    def __init__(self, api_key: str = None, model: str = None):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai is not installed. "
                "Run: pip install google-generativeai"
            )

        self.model_name = model or self.DEFAULT_MODEL
        resolved_key = api_key or os.getenv("GEMINI_API_KEY")
        if not resolved_key:
            raise ValueError(
                "Gemini API key required. Pass api_key= or set GEMINI_API_KEY env var."
            )

        genai.configure(api_key=resolved_key)
        self._client = genai.GenerativeModel(self.model_name)
        print(f"[LLM] GeminiProvider ready (model={self.model_name})")

    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.2) -> str:
        import google.generativeai as genai

        config = genai.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        response = self._client.generate_content(prompt, generation_config=config)
        return response.text.strip()


# ---------------------------------------------------------------------------
# HuggingFace Inference API provider  (free, no local GPU needed)
# ---------------------------------------------------------------------------

class HuggingFaceProvider(BaseLLMProvider):
    """
    HuggingFace Inference API (free tier).

    Args:
        api_key: HF token. Falls back to HF_API_KEY env var.
        model: HF model repo ID. Default: mistralai/Mistral-7B-Instruct-v0.3
    """

    DEFAULT_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

    def __init__(self, api_key: str = None, model: str = None):
        try:
            from huggingface_hub import InferenceClient
        except ImportError:
            raise ImportError(
                "huggingface_hub is not installed. "
                "Run: pip install huggingface_hub"
            )
        from huggingface_hub import InferenceClient

        self.model_name = model or self.DEFAULT_MODEL
        resolved_key = api_key or os.getenv("HF_API_KEY")
        self._client = InferenceClient(model=self.model_name, token=resolved_key)
        print(f"[LLM] HuggingFaceProvider ready (model={self.model_name})")

    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.2) -> str:
        result = self._client.text_generation(
            prompt,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
        )
        return result.strip()


# ---------------------------------------------------------------------------
# Ollama provider  (local, free, no API key needed)
# ---------------------------------------------------------------------------

class OllamaProvider(BaseLLMProvider):
    """
    Local Ollama server — completely free, runs on your own machine.

    Install Ollama: https://ollama.com/download
    Pull a model:   ollama pull llama3.2   (or mistral, phi3, gemma2, etc.)
    Start server:   ollama serve           (auto-starts on most installs)

    Args:
        model: Ollama model tag. Default: llama3.2
        host:  Ollama server URL. Default: http://localhost:11434
    """

    DEFAULT_MODEL = "llama3.2"
    DEFAULT_HOST  = "http://localhost:11434"

    def __init__(self, model: str = None, host: str = None, api_key: str = None):
        import urllib.request, json as _json
        self.model   = model or os.getenv("OLLAMA_MODEL", self.DEFAULT_MODEL)
        self.host    = (host or os.getenv("OLLAMA_HOST", self.DEFAULT_HOST)).rstrip("/")
        self._json   = _json
        self._urllib = urllib.request

        # Verify server is reachable
        try:
            req = urllib.request.urlopen(f"{self.host}/api/tags", timeout=5)
            tags = _json.loads(req.read())
            available = [m["name"].split(":")[0] for m in tags.get("models", [])]
            if self.model.split(":")[0] not in available:
                print(
                    f"[LLM][WARN] Model '{self.model}' not found locally. "
                    f"Available: {available or 'none pulled yet'}. "
                    f"Run: ollama pull {self.model}"
                )
            else:
                print(f"[LLM] OllamaProvider ready (model={self.model}, host={self.host})")
        except Exception as e:
            raise RuntimeError(
                f"Cannot reach Ollama at {self.host}. "
                f"Is it running? Start with: ollama serve\nError: {e}"
            )

    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.2) -> str:
        import urllib.request, json as _json
        payload = _json.dumps({
            "model":  self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }).encode()

        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = _json.loads(resp.read())
        return data.get("response", "").strip()


# ---------------------------------------------------------------------------
# Groq provider  (cloud API, free tier, very fast inference)
# ---------------------------------------------------------------------------

class GroqProvider(BaseLLMProvider):
    """
    Groq cloud API — free tier with generous rate limits.
    Get a free key at: https://console.groq.com

    Args:
        api_key: Groq API key. Falls back to GROQ_API_KEY env var.
        model:   Groq model. Default: llama-3.3-70b-versatile
    """

    DEFAULT_MODEL = "llama-3.3-70b-versatile"

    def __init__(self, api_key: str = None, model: str = None):
        try:
            from groq import Groq
        except ImportError:
            raise ImportError(
                "groq package not installed. Run: pip install groq"
            )
        from groq import Groq

        resolved_key = api_key or os.getenv("GROQ_API_KEY")
        if not resolved_key:
            raise ValueError(
                "Groq API key required. Pass api_key= or set GROQ_API_KEY env var. "
                "Get a free key at: https://console.groq.com"
            )
        self.model_name = model or self.DEFAULT_MODEL
        self._client    = Groq(api_key=resolved_key)
        print(f"[LLM] GroqProvider ready (model={self.model_name})")

    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.2) -> str:
        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_PROVIDER_MAP = {
    "gemini":       GeminiProvider,
    "huggingface":  HuggingFaceProvider,
    "hf":           HuggingFaceProvider,
    "ollama":       OllamaProvider,
    "groq":         GroqProvider,
}


def get_llm_provider(
    provider: str = "gemini",
    api_key: str = None,
    model: str = None,
    **kwargs,
) -> BaseLLMProvider:
    """
    Instantiate an LLM provider by name.

    Args:
        provider: "gemini" | "huggingface" | "hf" | "ollama" | "groq"
        api_key:  Provider-specific API key (not needed for ollama).
        model:    Override the default model name.

    Returns:
        An instance of BaseLLMProvider.
    """
    key = provider.lower()
    if key not in _PROVIDER_MAP:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Available: {list(_PROVIDER_MAP.keys())}"
        )
    cls = _PROVIDER_MAP[key]
    init_kwargs = {}
    if api_key:
        init_kwargs["api_key"] = api_key
    if model:
        init_kwargs["model"] = model
    init_kwargs.update(kwargs)
    return cls(**init_kwargs)
