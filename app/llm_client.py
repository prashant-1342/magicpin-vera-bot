"""
Unified LLM client supporting Gemini, OpenAI, Groq, Anthropic, DeepSeek, and Ollama.
Allows Vera to generate fluent, natural, contextual AI responses with deterministic fallback.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Optional, List, Dict, Any

TIMEOUT_SECONDS = 15


class LLMService:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "").lower()
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

    @property
    def is_configured(self) -> bool:
        if self.provider == "ollama":
            return True
        return bool(self.provider and self.api_key)

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> Optional[str]:
        """Generate a completion using the configured provider. Returns None on failure or if unconfigured."""
        if not self.is_configured:
            return None

        try:
            if self.provider in ("openai", "openrouter", "deepseek", "groq"):
                return self._call_openai_compatible(system_prompt, user_prompt, temperature)
            elif self.provider == "gemini":
                return self._call_gemini(system_prompt, user_prompt, temperature)
            elif self.provider == "anthropic":
                return self._call_anthropic(system_prompt, user_prompt, temperature)
            elif self.provider == "ollama":
                return self._call_ollama(system_prompt, user_prompt, temperature)
        except Exception as e:
            # Silently catch so fallback handles the request
            return None
        return None

    def _call_openai_compatible(self, system: str, user: str, temp: float) -> str:
        endpoints = {
            "openai": ("https://api.openai.com/v1/chat/completions", self.model or "gpt-4o-mini"),
            "groq": ("https://api.groq.com/openai/v1/chat/completions", self.model or "llama-3.1-70b-versatile"),
            "deepseek": ("https://api.deepseek.com/v1/chat/completions", self.model or "deepseek-chat"),
            "openrouter": ("https://openrouter.ai/api/v1/chat/completions", self.model or "anthropic/claude-3-haiku"),
        }
        url, default_model = endpoints.get(self.provider, ("https://api.openai.com/v1/chat/completions", "gpt-4o-mini"))
        model_to_use = self.model or default_model

        body = json.dumps({
            "model": model_to_use,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": temp,
            "max_tokens": 300
        }).encode("utf-8")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://magicpin.com"

        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()

    def _call_gemini(self, system: str, user: str, temp: float) -> str:
        model_name = self.model or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        full_prompt = f"{system}\n\nUser Question:\n{user}"

        body = json.dumps({
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": temp, "maxOutputTokens": 300}
        }).encode("utf-8")

        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()

    def _call_anthropic(self, system: str, user: str, temp: float) -> str:
        model_name = self.model or "claude-3-5-sonnet-20241022"
        url = "https://api.anthropic.com/v1/messages"
        body = json.dumps({
            "model": model_name,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "temperature": temp,
            "max_tokens": 300
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["content"][0]["text"].strip()

    def _call_ollama(self, system: str, user: str, temp: float) -> str:
        model_name = self.model or "llama3"
        url = f"{self.ollama_url}/api/generate"
        full_prompt = f"{system}\n\nUser Query:\n{user}"
        body = json.dumps({
            "model": model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {"temperature": temp}
        }).encode("utf-8")

        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()


llm_service = LLMService()
