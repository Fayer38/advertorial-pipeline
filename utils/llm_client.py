"""
Client LLM unifié pour tous les agents.
Route via claude-max-api-proxy (OpenAI-compatible endpoint sur localhost:3456)
qui utilise l'abonnement Claude Max/Pro au lieu de crédits API.

Fallback: appel direct via `claude --print` si le proxy est down.
"""

import os
import json
import logging
import asyncio
import subprocess
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4"
PROXY_BASE = os.getenv("LLM_PROXY_URL", "http://localhost:3456")
MAX_RETRIES = 5
RETRY_DELAY = 3
CALL_TIMEOUT = 120  # 2 min max per call


class LLMClient:
    """Client wrapper pour le proxy Claude Max API avec fallback CLI."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.base_url = PROXY_BASE

    async def _check_proxy(self) -> bool:
        """Quick health check on proxy."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def _restart_proxy(self):
        """Try to restart the proxy if it's down."""
        logger.warning("Proxy down — attempting restart...")
        try:
            proc = await asyncio.create_subprocess_exec(
                "bash", "-c",
                "fuser -k 3456/tcp 2>/dev/null; sleep 1; systemctl restart claude-proxy",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=10)
            await asyncio.sleep(3)
            ok = await self._check_proxy()
            logger.info(f"Proxy restart: {'OK' if ok else 'FAILED'}")
            return ok
        except Exception as e:
            logger.error(f"Proxy restart failed: {e}")
            return False

    async def _call_cli_fallback(self, user_prompt: str, system_prompt: str, max_tokens: int) -> str:
        """Fallback: call claude CLI directly."""
        logger.info("Using CLI fallback (claude --print)...")
        cmd = ["claude", "--print", "--model", self.model]
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=user_prompt.encode()),
            timeout=180,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"CLI fallback failed: {stderr.decode()[:200]}")
        return stdout.decode()

    async def ask(
        self,
        user_prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.3,
        response_format: str = "json",
    ) -> dict | str:
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
            # Check proxy health before each attempt
            if attempt > 1 or not await self._check_proxy():
                if not await self._check_proxy():
                    logger.warning(f"Proxy unhealthy (attempt {attempt}/{MAX_RETRIES})")
                    if attempt <= 2:
                        await self._restart_proxy()
                        await asyncio.sleep(2)
                    else:
                        # Fallback to CLI
                        try:
                            raw_text = await self._call_cli_fallback(user_prompt, system_prompt, max_tokens)
                            return self._parse_json(raw_text) if response_format == "json" else raw_text
                        except Exception as e:
                            logger.error(f"CLI fallback failed: {e}")
                            if attempt == MAX_RETRIES:
                                raise
                            await asyncio.sleep(RETRY_DELAY)
                            continue

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/v1/chat/completions",
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=aiohttp.ClientTimeout(total=CALL_TIMEOUT),
                    ) as resp:
                        if resp.status == 429:
                            wait = RETRY_DELAY * attempt
                            logger.warning(f"Rate limit, retry dans {wait}s (attempt {attempt}/{MAX_RETRIES})")
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

                        raw_text = resp_data["choices"][0]["message"]["content"]
                        return self._parse_json(raw_text) if response_format == "json" else raw_text

            except asyncio.TimeoutError:
                logger.warning(f"Timeout ({CALL_TIMEOUT}s) on attempt {attempt}/{MAX_RETRIES}")
                if attempt == MAX_RETRIES:
                    raise RuntimeError(f"LLM timeout after {MAX_RETRIES} attempts")
                await asyncio.sleep(RETRY_DELAY)

            except aiohttp.ClientError as e:
                logger.error(f"Erreur réseau (attempt {attempt}/{MAX_RETRIES}): {e}")
                if attempt == MAX_RETRIES:
                    raise
                await asyncio.sleep(RETRY_DELAY)

        raise RuntimeError("Échec après toutes les tentatives")

    def _parse_json(self, text: str) -> dict:
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


_client: Optional[LLMClient] = None


def get_llm_client(model: str = DEFAULT_MODEL) -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient(model=model)
    return _client
