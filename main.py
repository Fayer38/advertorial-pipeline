"""
Orchestrateur Principal du Pipeline Advertorial
=================================================
Connecte les 10 agents en un pipeline complet.

Phases :
1. COLLECTE (parallèle) : Agents 1, 2, 3
2. STRUCTURATION : Agent 4
3. RÉDACTION : Agent 5
4. VISUELS (parallèle) : Agents 6, 7, 8
5. CONTRÔLE QUALITÉ : Agent 9 (avec boucle d'itération vers Agent 5)
6. EXPORT : Agent 10

Usage :
    python main.py <URL_PRODUIT_SHOPIFY> [--image <IMAGE_URL>] [--platform <midjourney|leonardo|flux>]
"""

import json
import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Import des agents
from agents.extractor import ExtractorAgent
from agents.avatar_researcher import AvatarResearcherAgent
from agents.image_describer import ImageDescriberAgent
from agents.info_organizer import InfoOrganizerAgent
from agents.copywriter import CopywriterAgent
from agents.visual_strategist import VisualStrategistAgent
from agents.image_prompter import ImagePrompterAgent
from agents.video_prompter import VideoPrompterAgent
from agents.qa_checker import QACheckerAgent
from agents.html_publisher import HTMLPublisherAgent

logger = logging.getLogger(__name__)


class AdvertorialPipeline:
    """
    Orchestre l'exécution complète du pipeline advertorial.
    Du produit URL à une page HTML publiée sur le domaine externe.
    """

    def __init__(
        self,
        output_dir: str = "data/output",
        reference_dir: str = "data/reference_advertorials",
        image_platform: str = "midjourney",
        video_platform: str = "kling",
    ):
        self.output_dir = output_dir
        self.image_platform = image_platform
        self.video_platform = video_platform

        # Initialiser les agents
        self.extractor = ExtractorAgent(output_dir=output_dir)
        self.avatar_researcher = AvatarResearcherAgent(output_dir=output_dir)
        self.image_describer = ImageDescriberAgent(output_dir=output_dir)
        self.info_organizer = InfoOrganizerAgent(output_dir=output_dir)
        self.copywriter = CopywriterAgent(
            output_dir=output_dir,
            reference_dir=reference_dir,
        )
        self.visual_strategist = VisualStrategistAgent(output_dir=output_dir)
        self.image_prompter = ImagePrompterAgent(output_dir=output_dir)
        self.video_prompter = VideoPrompterAgent(output_dir=output_dir)
        self.qa_checker = QACheckerAgent(
            output_dir=output_dir,
            reference_dir=reference_dir,
        )
        self.html_publisher = HTMLPublisherAgent(output_dir=output_dir)

    async def run(
        self,
        product_url: str,
        image_url: str = "",
    ) -> dict:
        """
        Exécute le pipeline complet.

        Args:
            product_url: URL du produit Shopify
            image_url: URL de l'image produit (optionnel — sinon prend la première du JSON Shopify)

        Returns:
            dict — template GemPage final
        """
        start_time = datetime.utcnow()
        logger.info("=" * 60)
        logger.info("PIPELINE ADVERTORIAL — DÉMARRAGE")
        logger.info(f"  Produit : {product_url}")
        logger.info(f"  Image   : {image_url or '(auto depuis Shopify)'}")
        logger.info("=" * 60)

        # ══════════════════════════════════════════════════════════
        # PHASE 1 : COLLECTE (parallèle)
        # ══════════════════════════════════════════════════════════
        logger.info("\n📥 PHASE 1 — COLLECTE (parallèle)")

        # L'Agent 1 et l'Agent 2 tournent en parallèle
        # L'Agent 3 tourne aussi en parallèle si on a une image
        phase1_tasks = [
            self.extractor.run(url=product_url),
            self.avatar_researcher.run(url=product_url),
        ]

        if image_url:
            phase1_tasks.append(
                self.image_describer.run(image_source=image_url)
            )

        results = await asyncio.gather(*phase1_tasks, return_exceptions=True)

        # Traiter les résultats
        product_data = self._handle_result(results[0], "Extracteur Produit")
        avatar_research = self._handle_result(results[1], "Chercheur Avatar")

        image_description = None
        if len(results) > 2:
            image_description = self._handle_result(results[2], "Descripteur Image")

        # Si pas d'image fournie, prendre la première du JSON Shopify
        if not image_description and product_data:
            images = product_data.get("images", [])
            if images:
                first_image_url = images[0].get("url", "")
                if first_image_url:
                    logger.info(f"Image auto-détectée depuis Shopify : {first_image_url[:60]}...")
                    try:
                        image_description = await self.image_describer.run(
                            image_source=first_image_url
                        )
                    except Exception as e:
                        logger.warning(f"Impossible de décrire l'image auto : {e}")

        # Relancer Agent 2 avec les données produit pour enrichissement
        if product_data and avatar_research:
            try:
                logger.info("Enrichissement de la recherche avatar avec les données produit...")
                avatar_research = await self.avatar_researcher.run(
                    url=product_url,
                    product_data=product_data,
                )
            except Exception as e:
                logger.warning(f"Enrichissement avatar échoué : {e}")

        # ══════════════════════════════════════════════════════════
        # PHASE 2 : STRUCTURATION
        # ══════════════════════════════════════════════════════════
        logger.info("\n📋 PHASE 2 — STRUCTURATION")

        structured_brief = await self.info_organizer.run(
            product_data=product_data or {},
            avatar_research=avatar_research or {},
            image_description=image_description,
        )

        # ══════════════════════════════════════════════════════════
        # PHASE 3 : RÉDACTION
        # ══════════════════════════════════════════════════════════
        logger.info("\n✍️  PHASE 3 — RÉDACTION")

        advertorial_draft = await self.copywriter.run(
            structured_brief=structured_brief,
        )

        # ══════════════════════════════════════════════════════════
        # PHASE 4 : VISUELS (parallèle)
        # ══════════════════════════════════════════════════════════
        logger.info("\n🎨 PHASE 4 — VISUELS (parallèle)")

        # D'abord le stratège visuel
        visual_plan = await self.visual_strategist.run(
            advertorial_draft=advertorial_draft,
            image_description=image_description,
            structured_brief=structured_brief,
        )

        # Puis les prompteurs en parallèle
        image_prompts, video_prompts = await asyncio.gather(
            self.image_prompter.run(
                visual_plan=visual_plan,
                image_description=image_description,
                platform=self.image_platform,
            ),
            self.video_prompter.run(
                visual_plan=visual_plan,
                image_description=image_description,
                platform=self.video_platform,
            ),
        )

        # ══════════════════════════════════════════════════════════
        # PHASE 5 : CONTRÔLE QUALITÉ (avec itération)
        # ══════════════════════════════════════════════════════════
        logger.info("\n🔍 PHASE 5 — CONTRÔLE QUALITÉ")

        advertorial_final, qa_report = await self.qa_checker.run_with_iteration(
            advertorial_draft=advertorial_draft,
            structured_brief=structured_brief,
            copywriter_agent=self.copywriter,
        )

        # ══════════════════════════════════════════════════════════
        # PHASE 6 : EXPORT
        # ══════════════════════════════════════════════════════════
        logger.info("\n🏗️  PHASE 6 — PUBLICATION HTML")

        result = await self.html_publisher.run(
            advertorial_draft=advertorial_final,
            image_prompts=image_prompts,
            video_prompts=video_prompts,
            product_url=product_url,
        )

        # ══════════════════════════════════════════════════════════
        # RÉSUMÉ
        # ══════════════════════════════════════════════════════════
        duration = (datetime.utcnow() - start_time).total_seconds()
        self._print_summary(result, qa_report, duration)

        return result

    def _handle_result(self, result, agent_name: str):
        """Gère un résultat d'agent (succès ou erreur)."""
        if isinstance(result, Exception):
            logger.error(f"❌ {agent_name} a échoué : {result}")
            return None
        logger.info(f"✅ {agent_name} terminé")
        return result

    def _print_summary(self, result: dict, qa_report: dict, duration: float):
        """Affiche un résumé du pipeline."""
        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE TERMINÉ")
        logger.info("=" * 60)

        logger.info(f"  📰 Slug     : {result.get('slug', 'N/A')}")
        logger.info(f"  📝 Mots     : {result.get('word_count', '?')}")
        logger.info(f"  📊 Score QA : {qa_report.get('overall_score', '?')}/10")
        logger.info(f"  ⏱️  Durée    : {duration:.0f}s")
        logger.info(f"  📄 HTML     : {result.get('html_file', 'N/A')}")
        if result.get("url"):
            logger.info(f"  🌐 URL      : {result['url']}")
        logger.info(f"\n  📁 Fichiers dans : {self.output_dir}/")


# ============================================================
# CLI
# ============================================================

def main():
    """Point d'entrée CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Pipeline de création d'advertoriaux Shopify",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python main.py https://store.com/products/super-serum
  python main.py https://store.com/products/serum --image https://cdn.shopify.com/image.jpg
  python main.py https://store.com/products/serum --platform leonardo --video-platform runway
        """,
    )

    parser.add_argument("url", help="URL du produit Shopify")
    parser.add_argument("--image", default="", help="URL de l'image produit (optionnel)")
    parser.add_argument("--platform", default="midjourney", choices=["midjourney", "leonardo", "flux"],
                        help="Plateforme de génération d'images (défaut: midjourney)")
    parser.add_argument("--video-platform", default="kling", choices=["kling", "runway", "sora"],
                        help="Plateforme de génération vidéo (défaut: kling)")
    parser.add_argument("--output", default="data/output", help="Répertoire de sortie")
    parser.add_argument("--references", default="data/reference_advertorials",
                        help="Répertoire des advertoriaux de référence")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mode verbeux")

    args = parser.parse_args()

    # Configuration du logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Vérifier la clé API
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY non définie.")
        print("   Créez un fichier .env avec : ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    # Lancer le pipeline
    pipeline = AdvertorialPipeline(
        output_dir=args.output,
        reference_dir=args.references,
        image_platform=args.platform,
        video_platform=args.video_platform,
    )

    result = asyncio.run(pipeline.run(
        product_url=args.url,
        image_url=args.image,
    ))

    print("\n✅ Advertorial publié dans :", args.output)


if __name__ == "__main__":
    main()
