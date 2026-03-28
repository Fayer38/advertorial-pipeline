"""
Agent 4 : Organisateur d'Infos
================================
Input  : Sorties des Agents 1 (product_data), 2 (avatar_research), 3 (image_description)
Output : structured_brief.json (schéma StructuredBrief)

Processus :
1. Charge les trois sources de données
2. Formate un prompt consolidé avec toutes les infos
3. Envoie au LLM pour synthèse, filtrage et hiérarchisation
4. Valide et sauvegarde le brief de copywriting

C'est l'agent charnière entre la Phase 1 (Collecte) et la Phase 3 (Rédaction).

Voir PROJECT_BIBLE.md section 3.4 pour le schéma de sortie.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from agents.base_agent import BaseAgent
from utils.llm_client import get_llm_client
from models.schemas import StructuredBrief, BriefMeta

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "organizer_system_prompt.txt"


class InfoOrganizerAgent(BaseAgent):
    """
    Agent d'organisation et de synthèse des données.
    Reçoit les sorties brutes des 3 agents de collecte,
    les filtre, hiérarchise et produit un brief de copywriting actionnable.
    """

    def __init__(self, output_dir: str = "data/output"):
        super().__init__(name="info_organizer", output_dir=output_dir)
        self.llm = get_llm_client()
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Charge le prompt système."""
        if PROMPT_PATH.exists():
            return PROMPT_PATH.read_text(encoding="utf-8")
        logger.warning(f"Prompt système introuvable: {PROMPT_PATH}")
        return ""

    async def run(
        self,
        product_data: dict,
        avatar_research: dict,
        image_description: Optional[dict] = None,
    ) -> dict:
        """
        Pipeline principal d'organisation.

        Args:
            product_data: Sortie de l'Agent 1 (Extracteur Produit)
            avatar_research: Sortie de l'Agent 2 (Chercheur Avatar)
            image_description: Sortie de l'Agent 3 (Descripteur Image) — optionnel

        Returns:
            dict conforme au schéma StructuredBrief
        """
        self.log_start(
            product=product_data.get("product_info", {}).get("title", "?"),
            has_avatar=bool(avatar_research),
            has_image=bool(image_description),
        )

        # ── Étape 1 : Construire le prompt consolidé ──
        user_prompt = self._build_consolidated_prompt(
            product_data, avatar_research, image_description
        )

        # ── Étape 2 : Synthèse LLM ──
        self.logger.info("Synthèse et hiérarchisation par LLM...")
        brief_data = await self.llm.ask(
            user_prompt=user_prompt,
            system_prompt=self.system_prompt,
            max_tokens=4096,
            temperature=0.3,
            response_format="json",
        )

        # ── Étape 3 : Assembler et valider ──
        result = self._assemble_brief(product_data, brief_data)

        # Sauvegarder
        product_url = product_data.get("meta", {}).get("source_url", "")
        handle = product_data.get("meta", {}).get("shopify_handle", "unknown")
        output = result.model_dump(mode="json")
        self.save_output(output, f"structured_brief_{handle}.json")

        confidence = result.meta.confidence_score
        self.log_done(f"Brief créé (confiance: {confidence})")
        return output

    def _build_consolidated_prompt(
        self,
        product_data: dict,
        avatar_research: dict,
        image_description: Optional[dict],
    ) -> str:
        """
        Construit un prompt unique qui consolide les 3 sources.
        Formate les données de façon lisible pour le LLM.
        """
        sections = []

        # ── SOURCE 1 : Données produit (Agent 1) ──
        sections.append("## SOURCE 1 : DONNÉES PRODUIT (Agent Extracteur)\n")
        info = product_data.get("product_info", {})
        sections.append(f"**Titre** : {info.get('title', 'N/A')}")
        sections.append(f"**Type** : {info.get('product_type', 'N/A')}")
        sections.append(f"**Vendeur** : {info.get('vendor', 'N/A')}")
        sections.append(f"**Prix** : {info.get('price', {}).get('amount', 'N/A')} {info.get('price', {}).get('currency', '')}")

        compare = info.get("price", {}).get("compare_at_price")
        if compare:
            sections.append(f"**Prix barré** : {compare}")

        sections.append(f"**Tags** : {', '.join(info.get('tags', []))}")
        sections.append(f"\n**Description** :\n{info.get('description_clean', 'N/A')[:2000]}")

        # Composition
        comp = product_data.get("composition", {})
        if comp.get("ingredients"):
            sections.append("\n**Ingrédients** :")
            for ing in comp["ingredients"][:15]:
                role = f" — {ing['role']}" if ing.get("role") else ""
                dosage = f" ({ing['dosage']})" if ing.get("dosage") else ""
                sections.append(f"  - {ing.get('name', '')}{role}{dosage}")

        if comp.get("key_actives"):
            sections.append(f"**Actifs clés** : {', '.join(comp['key_actives'])}")

        if comp.get("certifications"):
            sections.append(f"**Certifications** : {', '.join(comp['certifications'])}")

        # Bénéfices
        ben = product_data.get("benefits", {})
        if ben.get("main_benefits"):
            sections.append("\n**Bénéfices** :")
            for b in ben["main_benefits"]:
                sections.append(f"  - {b}")

        if ben.get("features"):
            sections.append("\n**Features** :")
            for f in ben["features"]:
                sections.append(f"  - {f}")

        if ben.get("problem_solved"):
            sections.append(f"\n**Problème résolu** : {ben['problem_solved']}")
        if ben.get("target_need"):
            sections.append(f"**Besoin cible** : {ben['target_need']}")

        if ben.get("use_cases"):
            sections.append("\n**Cas d'usage** :")
            for uc in ben["use_cases"][:5]:
                sections.append(f"  - {uc.get('scenario', '')} → {uc.get('outcome', '')}")

        # Preuves
        proof = product_data.get("social_proof", {})
        if proof.get("clinical_studies"):
            sections.append("\n**Études cliniques** :")
            for study in proof["clinical_studies"]:
                sections.append(f"  - {study.get('claim', '')} (Source: {study.get('source', 'N/A')})")

        # FAQ
        faq = product_data.get("faq", [])
        if faq:
            sections.append(f"\n**FAQ** ({len(faq)} questions) :")
            for item in faq[:8]:
                sections.append(f"  Q: {item.get('question', '')}")
                sections.append(f"  R: {item.get('answer', '')[:200]}")
                sections.append("")

        # Offre
        offer = product_data.get("offer", {})
        if any(offer.get(k) for k in ["bundles", "discounts", "guarantees"]):
            sections.append("\n**Offre commerciale** :")
            if offer.get("guarantees"):
                sections.append(f"  Garanties : {', '.join(offer['guarantees'])}")
            if offer.get("discounts"):
                sections.append(f"  Promos : {', '.join(offer['discounts'])}")
            if offer.get("bundles"):
                sections.append(f"  Bundles : {', '.join(offer['bundles'])}")
            if offer.get("shipping_info"):
                sections.append(f"  Livraison : {offer['shipping_info']}")

        # Compétitif
        comp_data = product_data.get("competitive", {})
        if comp_data.get("unique_selling_points"):
            sections.append(f"\n**USP** : {', '.join(comp_data['unique_selling_points'])}")

        # ── SOURCE 2 : Recherche Avatar (Agent 2) ──
        sections.append("\n\n---\n## SOURCE 2 : RECHERCHE AVATAR (Agent Chercheur)\n")

        avatar = avatar_research.get("avatar", {})
        sections.append(f"**Démographie** : {avatar.get('demographics', 'N/A')}")
        sections.append(f"**Psychographie** : {avatar.get('psychographics', 'N/A')}")
        sections.append(f"**Vie quotidienne** : {avatar.get('daily_life', 'N/A')}")

        if avatar.get("frustrations"):
            sections.append("\n**Frustrations** :")
            for f in avatar["frustrations"]:
                sections.append(f"  - {f}")

        if avatar.get("desires"):
            sections.append("\n**Désirs** :")
            for d in avatar["desires"]:
                sections.append(f"  - {d}")

        if avatar.get("objections"):
            sections.append("\n**Objections** :")
            for o in avatar["objections"]:
                sections.append(f"  - {o}")

        if avatar.get("language_patterns"):
            sections.append(f"\n**Langage de la cible** : {', '.join(avatar['language_patterns'])}")

        # Pain points
        pains = avatar_research.get("pain_points", [])
        if pains:
            sections.append("\n**Pain Points** :")
            for pp in pains:
                sections.append(f"  [{pp.get('intensity', '?').upper()}] {pp.get('pain', '')}")
                for v in pp.get("verbatim_examples", [])[:2]:
                    sections.append(f"    > \"{v}\"")

        # Angles
        angles = avatar_research.get("angles", [])
        if angles:
            sections.append("\n**Angles marketing identifiés** :")
            for a in angles:
                sections.append(f"  [{a.get('strength', '?').upper()}] {a.get('angle_name', '')}")
                sections.append(f"    Hook : {a.get('hook_idea', '')}")
                sections.append(f"    Trigger : {a.get('emotional_trigger', '')}")

        # Concurrents
        competitors = avatar_research.get("competitors_mentioned", [])
        if competitors:
            sections.append(f"\n**Concurrents mentionnés** : {', '.join(competitors)}")

        # ── SOURCE 3 : Description Image (Agent 3) ──
        if image_description:
            sections.append("\n\n---\n## SOURCE 3 : DESCRIPTION IMAGE (Agent Descripteur)\n")
            desc = image_description.get("description", {})
            sections.append(f"**Court** : {desc.get('short', 'N/A')}")
            sections.append(f"**Détail** : {desc.get('detailed', 'N/A')}")
            sections.append(f"**Apparence** : {desc.get('product_appearance', 'N/A')}")
            sections.append(f"**Packaging** : {desc.get('packaging', 'N/A')}")
            sections.append(f"**Couleurs** : {', '.join(desc.get('colors', []))}")
            sections.append(f"**Texture** : {desc.get('texture_material', 'N/A')}")
            sections.append(f"**Taille** : {desc.get('size_impression', 'N/A')}")
            sections.append(f"**Contexte** : {desc.get('lifestyle_context', 'N/A')}")

        # ── INSTRUCTION FINALE ──
        sections.append("\n\n---\n")
        sections.append(
            "À partir de TOUTES ces données, produis le brief de copywriting structuré "
            "en JSON comme demandé. Hiérarchise impitoyablement : UN angle principal, "
            "les hooks classés, les bénéfices ordonnés par impact émotionnel."
        )
        sections.append("Réponds UNIQUEMENT en JSON valide, sans texte autour.")

        return "\n".join(sections)

    def _assemble_brief(
        self, product_data: dict, brief_data: dict
    ) -> StructuredBrief:
        """Assemble et valide le brief avec Pydantic."""
        product_url = product_data.get("meta", {}).get("source_url", "")

        # Extraire le score de confiance
        meta_data = brief_data.get("meta", {})
        confidence = meta_data.get("confidence_score", 0.5)

        meta = BriefMeta(
            product_url=product_url,
            confidence_score=confidence,
        )

        result_dict = {"meta": meta.model_dump(mode="json")}

        # Injecter les sections du LLM
        for key in ["product_summary", "avatar_profile", "copy_ammunition", "visual_notes"]:
            if key in brief_data:
                result_dict[key] = brief_data[key]

        return StructuredBrief(**result_dict)


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

    if len(sys.argv) < 3:
        print("Usage: python -m agents.info_organizer <product_data.json> <avatar_research.json> [image_description.json]")
        sys.exit(1)

    # Charger les fichiers d'entrée
    with open(sys.argv[1], "r") as f:
        product_data = json.load(f)
    with open(sys.argv[2], "r") as f:
        avatar_research = json.load(f)

    image_description = None
    if len(sys.argv) > 3:
        with open(sys.argv[3], "r") as f:
            image_description = json.load(f)

    agent = InfoOrganizerAgent()
    result = await agent.run(
        product_data=product_data,
        avatar_research=avatar_research,
        image_description=image_description,
    )

    print("\n" + "=" * 60)
    print("BRIEF DE COPYWRITING")
    print("=" * 60)

    summary = result.get("product_summary", {})
    print(f"\n📦 {summary.get('name', 'N/A')} — {summary.get('one_liner', 'N/A')}")

    avatar = result.get("avatar_profile", {})
    print(f"\n👤 Avatar : {avatar.get('who', 'N/A')}")
    print(f"   Problème : {avatar.get('main_problem', 'N/A')}")

    ammo = result.get("copy_ammunition", {})
    primary = ammo.get("primary_angle", {})
    print(f"\n🎯 Angle principal : {primary.get('angle_name', 'N/A')}")
    print(f"   Raison : {primary.get('why', 'N/A')}")

    print(f"\n📝 Hooks :")
    for i, hook in enumerate(ammo.get("hooks", [])[:5], 1):
        print(f"   {i}. {hook}")

    confidence = result.get("meta", {}).get("confidence_score", 0)
    print(f"\n📊 Score de confiance : {confidence}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
