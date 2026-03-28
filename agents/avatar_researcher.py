"""
Agent 2 : Chercheur Avatar
===========================
Input  : URL produit + données produit (sortie Agent 1)
Output : avatar_research.json (schéma AvatarResearch)

Processus :
1. Analyse les données produit pour comprendre la catégorie et le problème résolu
2. Lance des recherches web ciblées (Reddit, forums, avis)
3. Envoie tout au LLM pour construire l'avatar, les pain points et les angles
4. Valide et sauvegarde en JSON

Cet agent tourne EN PARALLÈLE de l'Agent 1 dans le pipeline.
Mais il peut aussi recevoir la sortie de l'Agent 1 pour enrichir sa recherche.

Voir PROJECT_BIBLE.md section 3.2 pour le schéma de sortie.
"""

import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from agents.base_agent import BaseAgent
from utils.llm_client import get_llm_client
from utils.web_researcher import WebResearcher
from models.schemas import AvatarResearch, AvatarMeta

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "avatar_system_prompt.txt"


class AvatarResearcherAgent(BaseAgent):
    """
    Agent de recherche d'avatar client.
    Analyse le produit, recherche sur le web, et construit un profil
    client détaillé avec pain points et angles marketing.
    """

    def __init__(self, output_dir: str = "data/output"):
        super().__init__(name="avatar_researcher", output_dir=output_dir)
        self.llm = get_llm_client()
        self.web = WebResearcher()
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Charge le prompt système."""
        if PROMPT_PATH.exists():
            return PROMPT_PATH.read_text(encoding="utf-8")
        logger.warning(f"Prompt système introuvable: {PROMPT_PATH}")
        return ""

    async def run(
        self,
        url: str,
        product_data: Optional[dict] = None,
    ) -> dict:
        """
        Pipeline principal de recherche avatar.

        Args:
            url: URL du produit Shopify
            product_data: (optionnel) sortie de l'Agent 1 si déjà disponible.
                          Si None, l'agent extrait un résumé basique du produit.

        Returns:
            dict conforme au schéma AvatarResearch
        """
        self.log_start(url=url, has_product_data=bool(product_data))

        # ── Étape 1 : Comprendre le produit ──
        product_context = self._build_product_context(product_data, url)

        # ── Étape 2 : Recherche web ciblée ──
        research_results = await self._research_web(product_context)

        # ── Étape 3 : Analyse LLM → avatar + pain points + angles ──
        avatar_data = await self._analyze_with_llm(product_context, research_results)

        # ── Étape 4 : Validation et sauvegarde ──
        result = self._assemble_avatar_research(url, avatar_data, research_results)

        # Sauvegarder
        from utils.shopify_scraper import extract_shopify_handle
        handle = extract_shopify_handle(url)
        output = result.model_dump(mode="json")
        self.save_output(output, f"avatar_research_{handle}.json")

        self.log_done(f"Avatar: {result.avatar.demographics[:80]}...")
        return output

    def _build_product_context(
        self, product_data: Optional[dict], url: str
    ) -> dict:
        """
        Construit un résumé du contexte produit pour guider la recherche.
        Utilise les données de l'Agent 1 si disponibles, sinon un minimum.
        """
        if product_data:
            # Extraire les infos clés pour la recherche
            info = product_data.get("product_info", {})
            benefits = product_data.get("benefits", {})
            composition = product_data.get("composition", {})

            return {
                "product_name": info.get("title", ""),
                "product_category": info.get("product_type", ""),
                "description": info.get("description_clean", "")[:500],
                "problem_solved": benefits.get("problem_solved", ""),
                "target_need": benefits.get("target_need", ""),
                "main_benefits": benefits.get("main_benefits", []),
                "key_ingredients": [
                    ing.get("name", "")
                    for ing in composition.get("ingredients", [])[:5]
                ],
                "price": info.get("price", {}).get("amount", 0),
                "tags": info.get("tags", []),
                "url": url,
            }
        else:
            # Mode dégradé — juste l'URL
            return {
                "product_name": "",
                "product_category": "",
                "description": "",
                "problem_solved": "",
                "target_need": "",
                "main_benefits": [],
                "key_ingredients": [],
                "price": 0,
                "tags": [],
                "url": url,
            }

    async def _research_web(self, product_context: dict) -> dict:
        """
        Étape 2 : Lance les recherches web ciblées.
        """
        self.logger.info("Étape 2 : Recherche web en cours...")

        product_name = product_context.get("product_name", "")
        category = product_context.get("product_category", "")
        problem = product_context.get("problem_solved", "")

        # Si on n'a pas assez de contexte, utiliser des termes génériques
        if not category and not problem:
            # Essayer de déduire de l'URL ou du nom
            category = product_name
            problem = "related issues"

        results = await self.web.research_product_category(
            product_name=product_name,
            product_category=category,
            problem_solved=problem,
            max_queries=6,
        )

        successful = results.get("successful_queries", 0)
        total = results.get("total_queries", 0)
        self.logger.info(f"Recherche web : {successful}/{total} requêtes réussies")

        return results

    async def _analyze_with_llm(
        self, product_context: dict, research_results: dict
    ) -> dict:
        """
        Étape 3 : Envoie le contexte produit + résultats de recherche
        au LLM pour construire l'avatar et identifier les angles.
        """
        self.logger.info("Étape 3 : Analyse LLM en cours...")

        user_prompt = self._build_user_prompt(product_context, research_results)

        avatar_data = await self.llm.ask(
            user_prompt=user_prompt,
            system_prompt=self.system_prompt,
            max_tokens=4096,
            temperature=0.4,  # Un peu de créativité pour les angles
            response_format="json",
        )

        self.logger.info("Analyse LLM terminée")
        return avatar_data

    def _build_user_prompt(
        self, product_context: dict, research_results: dict
    ) -> str:
        """Construit le prompt utilisateur avec le contexte et la recherche."""

        # Formater le contexte produit
        product_section = f"""## DONNÉES PRODUIT

- **Nom** : {product_context.get('product_name', 'Non disponible')}
- **Catégorie** : {product_context.get('product_category', 'Non disponible')}
- **Prix** : {product_context.get('price', 'N/A')}
- **Problème résolu** : {product_context.get('problem_solved', 'Non identifié')}
- **Besoin cible** : {product_context.get('target_need', 'Non identifié')}
- **Bénéfices principaux** : {', '.join(product_context.get('main_benefits', [])) or 'Non disponibles'}
- **Ingrédients clés** : {', '.join(product_context.get('key_ingredients', [])) or 'Non disponibles'}
- **Tags** : {', '.join(product_context.get('tags', [])) or 'Aucun'}

### Description
{product_context.get('description', 'Non disponible')[:1000]}
"""

        # Formater les résultats de recherche
        research_section = self.web.format_results_for_llm(research_results)

        prompt = f"""{product_section}

{research_section}

---

À partir de toutes ces données, construis l'avatar client, identifie les pain points avec leurs verbatims, et propose les meilleurs angles marketing pour un advertorial.

Rappel : réponds UNIQUEMENT en JSON valide, sans texte autour."""

        return prompt

    def _assemble_avatar_research(
        self,
        url: str,
        avatar_data: dict,
        research_results: dict,
    ) -> AvatarResearch:
        """
        Assemble le résultat final validé par Pydantic.
        """
        self.logger.info("Étape 4 : Assemblage et validation...")

        # Collecter les sources utilisées
        sources = []
        if research_results.get("method") == "serpapi":
            for group in research_results.get("results", []):
                for r in group.get("results", []):
                    if r.get("link"):
                        sources.append(r["link"])

        meta = AvatarMeta(
            product_url=url,
            sources=sources[:20],  # Max 20 sources
        )

        # Construire le dict pour Pydantic
        result_dict = {
            "meta": meta.model_dump(mode="json"),
        }

        # Injecter les données du LLM
        for key in ["avatar", "pain_points", "angles", "competitors_mentioned",
                     "reddit_insights"]:
            if key in avatar_data:
                result_dict[key] = avatar_data[key]

        # Valider avec Pydantic
        result = AvatarResearch(**result_dict)

        return result


# ============================================================
# UTILISATION STANDALONE
# ============================================================

async def main():
    """Point d'entrée pour tester l'agent en standalone."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python -m agents.avatar_researcher <URL_PRODUIT>")
        print("")
        print("Options :")
        print("  --with-product-data <path>   Utiliser la sortie de l'Agent 1")
        print("")
        print("Exemple :")
        print("  python -m agents.avatar_researcher https://store.com/products/serum")
        print("  python -m agents.avatar_researcher https://store.com/products/serum \\")
        print("    --with-product-data data/output/product_data_serum.json")
        sys.exit(1)

    url = sys.argv[1]

    # Charger les données produit si fournies
    product_data = None
    if "--with-product-data" in sys.argv:
        idx = sys.argv.index("--with-product-data")
        if idx + 1 < len(sys.argv):
            with open(sys.argv[idx + 1], "r") as f:
                product_data = json.load(f)
            print(f"Données produit chargées: {sys.argv[idx + 1]}")

    agent = AvatarResearcherAgent()
    result = await agent.run(url=url, product_data=product_data)

    print("\n" + "=" * 60)
    print("RÉSULTAT RECHERCHE AVATAR")
    print("=" * 60)

    # Afficher un résumé lisible
    avatar = result.get("avatar", {})
    print(f"\n👤 AVATAR : {avatar.get('demographics', 'N/A')}")
    print(f"   Psycho : {avatar.get('psychographics', 'N/A')[:100]}...")

    print(f"\n🎯 PAIN POINTS :")
    for pp in result.get("pain_points", [])[:5]:
        print(f"   [{pp.get('intensity', '?').upper()}] {pp.get('pain', '')}")

    print(f"\n📐 ANGLES MARKETING :")
    for angle in result.get("angles", [])[:5]:
        print(f"   [{angle.get('strength', '?').upper()}] {angle.get('angle_name', '')}")
        print(f"      Hook : {angle.get('hook_idea', '')[:80]}...")

    print(f"\n🏷️  CONCURRENTS : {', '.join(result.get('competitors_mentioned', []))}")


if __name__ == "__main__":
    asyncio.run(main())
