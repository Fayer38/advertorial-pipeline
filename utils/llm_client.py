"""
Client LLM unifié pour tous les agents.
Route via claude-max-api-proxy (OpenAI-compatible endpoint sur localhost:3456)
qui utilise l'abonnement Claude Max/Pro au lieu de crédits API.
"""

import os
import json
import logging
import asyncio
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

# Modèle par défaut (via proxy, mapped to Claude Sonnet 4)
DEFAULT_MODEL = "claude-sonnet-4"
PROXY_BASE = os.getenv("LLM_PROXY_URL", "http://localhost:3456")
MAX_RETRIES = 3
RETRY_DELAY = 2  # secondes


class LLMClient:
    """Client wrapper pour le proxy Claude Max API (OpenAI-compatible)."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.base_url = PROXY_BASE

    async def ask(
        self,
        user_prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.3,
        response_format: str = "json",
    ) -> dict | str:
        """
        Envoie un prompt via le proxy Claude et retourne la réponse.

        Args:
            user_prompt: Le message utilisateur
            system_prompt: Le prompt système (instructions de l'agent)
            max_tokens: Nombre max de tokens en réponse
            temperature: Créativité (0.0 = déterministe, 1.0 = créatif)
            response_format: "json" pour parser auto, "text" pour du texte brut

        Returns:
            dict si response_format="json", str sinon
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/v1/chat/completions",
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=aiohttp.ClientTimeout(total=300),
                    ) as resp:
                        if resp.status == 429:
                            wait = RETRY_DELAY * attempt
                            logger.warning(f"Rate limit, retry dans {wait}s (tentative {attempt}/{MAX_RETRIES})")
                            await asyncio.sleep(wait)
                            continue

                        resp_data = await resp.json()

                        if resp.status != 200:
                            error_msg = resp_data.get("error", {}).get("message", str(resp_data))
                            logger.error(f"Erreur proxy LLM ({resp.status}): {error_msg}")
                            if attempt == MAX_RETRIES:
                                raise RuntimeError(f"Erreur LLM: {error_msg}")
                            await asyncio.sleep(RETRY_DELAY)
                            continue

                        # Extract text from OpenAI-compatible response
                        raw_text = resp_data["choices"][0]["message"]["content"]

                        if response_format == "json":
                            return self._parse_json(raw_text)
                        return raw_text

            except aiohttp.ClientError as e:
                logger.error(f"Erreur réseau (tentative {attempt}/{MAX_RETRIES}): {e}")
                if attempt == MAX_RETRIES:
                    raise
                await asyncio.sleep(RETRY_DELAY)

        raise RuntimeError("Échec après toutes les tentatives")

    def _parse_json(self, text: str) -> dict:
        """Parse la réponse JSON, en nettoyant les balises markdown."""
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Impossible de parser le JSON:\n{cleaned[:500]}...")
            raise ValueError(f"Réponse non-JSON: {e}") from e


# Singleton réutilisable
_client: Optional[LLMClient] = None


def get_llm_client(model: str = DEFAULT_MODEL) -> LLMClient:
    """Retourne un client LLM singleton."""
    global _client
    if _client is None:
        _client = LLMClient(model=model)
    return _client
