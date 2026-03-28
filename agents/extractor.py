"""
Agent 1 : Extracteur Produit Shopify
=====================================
Input  : URL produit Shopify
Output : product_data.json (schéma ProductData)

Processus :
1. Appel GET sur {url}.json → données structurées Shopify natives
2. Scraping HTML de la page → FAQ, ingrédients, études, sections custom
3. Envoi des deux sources à Claude → extraction intelligente en JSON normalisé

Voir PROJECT_BIBLE.md section 5 pour les détails.
"""

import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from agents.base_agent import BaseAgent
from utils.llm_client import get_llm_client
from utils.shopify_scraper import (
    extract_shopify_handle,
    extract_store_domain,
    fetch_shopify_json,
    fetch_page_html,
    parse_html_sections,
)
from models.schemas import ProductData, ProductMeta, ProductImage

logger = logging.getLogger(__name__)

# Chemin du prompt système
PROMPT_PATH = Path(__file__).parent / "prompts" / "extractor_system_prompt.txt"


class ExtractorAgent(BaseAgent):
    """
    Agent d'extraction de données produit depuis une URL Shopify.
    Combine l'API JSON native et le scraping HTML pour une extraction complète,
    puis utilise Claude pour structurer intelligemment les données.
    """

    def __init__(self, output_dir: str = "data/output"):
        super().__init__(name="extractor", output_dir=output_dir)
        self.llm = get_llm_client()
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Charge le prompt système depuis le fichier."""
        if PROMPT_PATH.exists():
            return PROMPT_PATH.read_text(encoding="utf-8")
        logger.warning(f"Prompt système introuvable: {PROMPT_PATH}")
        return ""

    async def run(self, url: str) -> dict:
        """
        Pipeline principal d'extraction.

        Args:
            url: URL du produit Shopify

        Returns:
            dict conforme au schéma ProductData
        """
        self.log_start(url=url)

        # ── Étape 1 : Extraction parallèle des données brutes ──
        shopify_json, html_sections = await self._fetch_raw_data(url)

        # ── Étape 2 : Extraction intelligente par LLM ──
        extracted = await self._extract_with_llm(shopify_json, html_sections)

        # ── Étape 3 : Assemblage du ProductData final ──
        product_data = self._assemble_product_data(
            url=url,
            shopify_json=shopify_json,
            extracted=extracted,
        )

        # ── Sauvegarde ──
        handle = extract_shopify_handle(url)
        output = product_data.model_dump(mode="json")
        self.save_output(output, f"product_data_{handle}.json")

        self.log_done(f"Produit: {product_data.product_info.title}")
        return output

    async def _fetch_raw_data(self, url: str) -> tuple[dict, dict]:
        """
        Étape 1 : Récupère les données brutes en parallèle.
        - JSON natif Shopify (toujours disponible)
        - HTML de la page (pour les sections custom)
        """
        self.logger.info("Étape 1 : Récupération des données brutes...")

        # Lancement parallèle des deux requêtes
        shopify_json_task = fetch_shopify_json(url)
        html_task = fetch_page_html(url)

        try:
            shopify_json, raw_html = await asyncio.gather(
                shopify_json_task,
                html_task,
                return_exceptions=True,
            )
        except Exception as e:
            self.log_error(e, "fetch_raw_data")
            raise

        # Gérer les erreurs individuelles
        if isinstance(shopify_json, Exception):
            self.log_error(shopify_json, "shopify_json")
            raise shopify_json

        if isinstance(raw_html, Exception):
            self.logger.warning(f"HTML non récupéré: {raw_html}. Continuation sans HTML.")
            raw_html = ""

        # Parser le HTML
        html_sections = parse_html_sections(raw_html) if raw_html else {}

        self.logger.info(
            f"Données brutes récupérées: "
            f"JSON={bool(shopify_json)}, "
            f"HTML sections={len([v for v in html_sections.values() if v])}"
        )

        return shopify_json, html_sections

    async def _extract_with_llm(self, shopify_json: dict, html_sections: dict) -> dict:
        """
        Étape 2 : Envoie les données brutes au LLM pour extraction intelligente.
        Claude identifie et structure : bénéfices, ingrédients, études, FAQ, offre, etc.
        """
        self.logger.info("Étape 2 : Extraction intelligente par LLM...")

        # Construire le prompt utilisateur avec les deux sources
        user_prompt = self._build_user_prompt(shopify_json, html_sections)

        # Appel LLM
        extracted = await self.llm.ask(
            user_prompt=user_prompt,
            system_prompt=self.system_prompt,
            max_tokens=4096,
            temperature=0.1,  # Très peu de créativité pour l'extraction
            response_format="json",
        )

        self.logger.info("Extraction LLM terminée")
        return extracted

    def _build_user_prompt(self, shopify_json: dict, html_sections: dict) -> str:
        """Construit le prompt utilisateur avec les données brutes formatées."""

        # Nettoyer le JSON Shopify pour ne garder que l'essentiel
        # (éviter d'envoyer des données trop volumineuses)
        clean_shopify = {
            "title": shopify_json.get("title", ""),
            "body_html": shopify_json.get("body_html", "")[:5000],
            "vendor": shopify_json.get("vendor", ""),
            "product_type": shopify_json.get("product_type", ""),
            "tags": shopify_json.get("tags", ""),
            "variants": [
                {
                    "title": v.get("title", ""),
                    "price": v.get("price", ""),
                    "compare_at_price": v.get("compare_at_price"),
                    "sku": v.get("sku", ""),
                    "available": v.get("available", True),
                }
                for v in shopify_json.get("variants", [])
            ],
            "images": [
                {"src": img.get("src", ""), "alt": img.get("alt", "")}
                for img in shopify_json.get("images", [])[:5]  # Max 5 images
            ],
        }

        # Filtrer les sections HTML vides
        html_content = {k: v for k, v in html_sections.items() if v}

        prompt = f"""Voici les données brutes d'un produit Shopify. Analyse-les et extrais toutes les informations pertinentes.

## SOURCE 1 : JSON SHOPIFY NATIF
```json
{json.dumps(clean_shopify, ensure_ascii=False, indent=2)}
```

## SOURCE 2 : CONTENU HTML EXTRAIT DE LA PAGE
"""
        for section_name, content in html_content.items():
            if content and section_name != "full_text":
                # Limiter chaque section à 3000 caractères
                truncated = content[:3000]
                prompt += f"\n### {section_name}\n{truncated}\n"

        # Ajouter le texte complet en dernier recours
        if html_content.get("full_text"):
            prompt += f"\n### TEXTE COMPLET DE LA PAGE (fallback)\n{html_content['full_text'][:8000]}\n"

        prompt += "\n\nExtrais maintenant toutes les informations en suivant le format JSON demandé."

        return prompt

    def _assemble_product_data(
        self,
        url: str,
        shopify_json: dict,
        extracted: dict,
    ) -> ProductData:
        """
        Étape 3 : Assemble le ProductData final en combinant
        les données Shopify natives et l'extraction LLM.
        """
        self.logger.info("Étape 3 : Assemblage du ProductData final...")

        # Créer le meta
        meta = ProductMeta(
            source_url=url,
            shopify_handle=extract_shopify_handle(url),
            store_domain=extract_store_domain(url),
        )

        # Extraire les images depuis le JSON Shopify (source fiable)
        images = [
            ProductImage(
                url=img.get("src", ""),
                alt=img.get("alt", ""),
                position=img.get("position", i),
            )
            for i, img in enumerate(shopify_json.get("images", []))
        ]

        # Fusionner : les données LLM enrichissent les données Shopify
        product_data_dict = {
            "meta": meta.model_dump(mode="json"),
            "images": [img.model_dump() for img in images],
        }

        # Injecter les sections extraites par le LLM
        for key in ["product_info", "composition", "benefits", "social_proof",
                     "faq", "offer", "competitive"]:
            if key in extracted:
                product_data_dict[key] = extracted[key]

        # Valider avec Pydantic
        product_data = ProductData(**product_data_dict)

        return product_data


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
        print("Usage: python -m agents.extractor <URL_PRODUIT_SHOPIFY>")
        print("Exemple: python -m agents.extractor https://store.com/products/super-serum")
        sys.exit(1)

    url = sys.argv[1]
    agent = ExtractorAgent()
    result = await agent.run(url)

    print("\n" + "=" * 60)
    print("RÉSULTAT EXTRACTION")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2)[:3000])
    print("...")


if __name__ == "__main__":
    asyncio.run(main())
