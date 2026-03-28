"""
Client LLM unifié pour tous les agents.
Wraps l'API Claude d'Anthropic avec retry, logging, et gestion d'erreurs.
"""

import os
import json
import logging
import asyncio
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)

# Modèle par défaut
DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_RETRIES = 3
RETRY_DELAY = 2  # secondes


class LLMClient:
    """Client wrapper pour l'API Claude."""

    def __init__(self, model: str = DEFAULT_MODEL):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY manquante dans l'environnement")
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def ask(
        self,
        user_prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.3,
        response_format: str = "json",
    ) -> dict | str:
        """
        Envoie un prompt à Claude et retourne la réponse.

        Args:
            user_prompt: Le message utilisateur
            system_prompt: Le prompt système (instructions de l'agent)
            max_tokens: Nombre max de tokens en réponse
            temperature: Créativité (0.0 = déterministe, 1.0 = créatif)
            response_format: "json" pour parser auto, "text" pour du texte brut

        Returns:
            dict si response_format="json", str sinon
        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                message = await self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt if system_prompt else anthropic.NOT_GIVEN,
                    messages=[{"role": "user", "content": user_prompt}],
                )

                # Extraire le texte de la réponse
                raw_text = ""
                for block in message.content:
                    if block.type == "text":
                        raw_text += block.text

                if response_format == "json":
                    return self._parse_json(raw_text)
                return raw_text

            except anthropic.RateLimitError:
                wait = RETRY_DELAY * attempt
                logger.warning(f"Rate limit atteint, retry dans {wait}s (tentative {attempt}/{MAX_RETRIES})")
                await asyncio.sleep(wait)

            except anthropic.APIError as e:
                logger.error(f"Erreur API Claude (tentative {attempt}/{MAX_RETRIES}): {e}")
                if attempt == MAX_RETRIES:
                    raise
                await asyncio.sleep(RETRY_DELAY)

        raise RuntimeError("Échec après toutes les tentatives")

    def _parse_json(self, text: str) -> dict:
        """Parse la réponse JSON de Claude, en nettoyant les balises markdown."""
        # Nettoyer les balises ```json ... ```
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
            raise ValueError(f"Réponse non-JSON de Claude: {e}") from e


# Singleton réutilisable
_client: Optional[LLMClient] = None


def get_llm_client(model: str = DEFAULT_MODEL) -> LLMClient:
    """Retourne un client LLM singleton."""
    global _client
    if _client is None:
        _client = LLMClient(model=model)
    return _client
