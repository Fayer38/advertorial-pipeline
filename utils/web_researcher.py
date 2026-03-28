"""
Utilitaires de recherche web pour l'Agent 2 (Chercheur Avatar).
Fournit des méthodes pour chercher sur Reddit, forums, et le web
des informations sur l'avatar client et les pain points.

Deux stratégies de recherche :
1. API SerpAPI (recommandé en production — résultats structurés)
2. Recherche via Claude web search tool (fallback)
"""

import os
import json
import logging
import asyncio
from typing import Optional
from urllib.parse import quote_plus

import aiohttp

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


class WebResearcher:
    """
    Effectue des recherches web ciblées pour la construction d'avatar.
    Cherche sur Reddit, forums spécialisés, et le web général.
    """

    def __init__(self):
        self.serp_api_key = os.getenv("SERPAPI_KEY", "")
        self.has_serp = bool(self.serp_api_key)
        if not self.has_serp:
            logger.info(
                "SERPAPI_KEY non configurée. "
                "La recherche web passera par le LLM avec web search tool."
            )

    async def research_product_category(
        self,
        product_name: str,
        product_category: str,
        problem_solved: str,
        max_queries: int = 6,
    ) -> dict:
        """
        Lance une série de recherches ciblées pour comprendre
        l'avatar client et les pain points.

        Args:
            product_name: Nom du produit
            product_category: Catégorie (ex: "sérum anti-âge", "complément alimentaire")
            problem_solved: Le problème que le produit résout
            max_queries: Nombre max de requêtes de recherche

        Returns:
            dict avec les résultats de recherche bruts, prêts pour le LLM
        """
        # Construire les requêtes de recherche intelligentes
        queries = self._build_search_queries(
            product_name, product_category, problem_solved
        )

        # Limiter le nombre de requêtes
        queries = queries[:max_queries]

        logger.info(f"Lancement de {len(queries)} recherches web...")

        # Exécuter les recherches
        if self.has_serp:
            results = await self._search_with_serpapi(queries)
        else:
            # Sans SerpAPI, on retourne les requêtes pour que le LLM
            # les utilise avec son propre outil de recherche web
            results = {
                "method": "llm_web_search",
                "queries": queries,
                "results": [],
            }

        return results

    def _build_search_queries(
        self,
        product_name: str,
        product_category: str,
        problem_solved: str,
    ) -> list[dict]:
        """
        Construit des requêtes de recherche stratégiques.
        Chaque requête cible un aspect différent de l'avatar.
        """
        queries = []

        # ── 1. Reddit — Pain points et frustrations ──
        queries.append({
            "query": f"site:reddit.com {problem_solved} frustrated tried everything",
            "purpose": "pain_points_reddit",
            "description": "Frustrations réelles sur Reddit",
        })

        queries.append({
            "query": f"site:reddit.com best {product_category} recommendation",
            "purpose": "recommendations_reddit",
            "description": "Recommandations et avis Reddit",
        })

        # ── 2. Reddit — Langage et objections ──
        queries.append({
            "query": f"site:reddit.com {product_category} worth it scam",
            "purpose": "objections_reddit",
            "description": "Objections et scepticisme sur Reddit",
        })

        # ── 3. Avis et forums ──
        queries.append({
            "query": f"{product_category} reviews complaints {problem_solved}",
            "purpose": "reviews_general",
            "description": "Avis et plaintes générales",
        })

        # ── 4. Questions fréquentes ──
        queries.append({
            "query": f"{problem_solved} how to fix natural remedy",
            "purpose": "solutions_searched",
            "description": "Solutions recherchées par la cible",
        })

        # ── 5. Concurrence ──
        queries.append({
            "query": f"best {product_category} 2025 2026 comparison",
            "purpose": "competitors",
            "description": "Produits concurrents et comparatifs",
        })

        # ── 6. Produit spécifique ──
        queries.append({
            "query": f"{product_name} reviews",
            "purpose": "product_reviews",
            "description": "Avis spécifiques au produit",
        })

        # ── 7. TikTok / tendances ──
        queries.append({
            "query": f"{product_category} viral tiktok trend",
            "purpose": "trends",
            "description": "Tendances et viralité",
        })

        return queries

    async def _search_with_serpapi(self, queries: list[dict]) -> dict:
        """
        Effectue les recherches via SerpAPI (Google Search API).
        Retourne les résultats structurés.
        """
        all_results = []

        async with aiohttp.ClientSession() as session:
            tasks = [
                self._single_serp_search(session, q)
                for q in queries
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for query, result in zip(queries, results):
                if isinstance(result, Exception):
                    logger.warning(f"Recherche échouée pour '{query['query']}': {result}")
                    continue
                all_results.append({
                    "query": query["query"],
                    "purpose": query["purpose"],
                    "description": query["description"],
                    "results": result,
                })

        return {
            "method": "serpapi",
            "total_queries": len(queries),
            "successful_queries": len(all_results),
            "results": all_results,
        }

    async def _single_serp_search(
        self, session: aiohttp.ClientSession, query: dict
    ) -> list[dict]:
        """Effectue une seule recherche SerpAPI."""
        url = "https://serpapi.com/search.json"
        params = {
            "q": query["query"],
            "api_key": self.serp_api_key,
            "engine": "google",
            "num": 5,  # 5 résultats par requête
            "hl": "en",
        }

        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                raise RuntimeError(f"SerpAPI erreur {resp.status}")
            data = await resp.json()

        # Extraire les résultats organiques
        organic = data.get("organic_results", [])
        return [
            {
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "link": r.get("link", ""),
                "source": r.get("source", ""),
            }
            for r in organic
        ]

    def format_results_for_llm(self, research_results: dict) -> str:
        """
        Formate les résultats de recherche en texte lisible
        pour les envoyer au LLM avec le prompt d'analyse.
        """
        if research_results.get("method") == "llm_web_search":
            # Pas de résultats SerpAPI — on formate les requêtes suggérées
            lines = ["## REQUÊTES DE RECHERCHE SUGGÉRÉES\n"]
            lines.append("(Aucune API de recherche configurée. Utilise tes connaissances ")
            lines.append("et les données produit fournies pour construire l'avatar.)\n")
            for q in research_results.get("queries", []):
                lines.append(f"- **{q['description']}** : `{q['query']}`")
            return "\n".join(lines)

        # Résultats SerpAPI disponibles
        lines = ["## RÉSULTATS DE RECHERCHE WEB\n"]

        for group in research_results.get("results", []):
            lines.append(f"### {group['description']}")
            lines.append(f"Requête : `{group['query']}`\n")

            for r in group.get("results", []):
                lines.append(f"**{r['title']}**")
                if r.get("snippet"):
                    lines.append(f"> {r['snippet']}")
                if r.get("link"):
                    lines.append(f"Source : {r['link']}")
                lines.append("")

            lines.append("---\n")

        return "\n".join(lines)


async def scrape_reddit_thread(url: str) -> str:
    """
    Scrape le contenu d'un thread Reddit spécifique.
    Utilise l'endpoint .json de Reddit (comme Shopify !).
    """
    # Reddit expose aussi un .json natif
    json_url = url.rstrip("/") + ".json"

    async with aiohttp.ClientSession(headers={
        **HEADERS,
        "Accept": "application/json",
    }) as session:
        async with session.get(json_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                logger.warning(f"Reddit scrape échoué ({resp.status}): {url}")
                return ""

            data = await resp.json()

    # Extraire le post principal et les commentaires
    parts = []

    try:
        # Post principal
        post = data[0]["data"]["children"][0]["data"]
        parts.append(f"TITRE: {post.get('title', '')}")
        parts.append(f"CONTENU: {post.get('selftext', '')}")
        parts.append(f"SCORE: {post.get('score', 0)}")
        parts.append("")

        # Commentaires (top-level seulement)
        comments = data[1]["data"]["children"]
        for comment in comments[:15]:  # Max 15 commentaires
            if comment.get("kind") == "t1":
                c = comment["data"]
                body = c.get("body", "")
                score = c.get("score", 0)
                if body and score > 1:  # Ignorer les commentaires négatifs
                    parts.append(f"[+{score}] {body[:500]}")
                    parts.append("")

    except (KeyError, IndexError, TypeError) as e:
        logger.warning(f"Erreur parsing Reddit: {e}")

    return "\n".join(parts)
