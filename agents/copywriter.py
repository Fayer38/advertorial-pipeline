"""
Agent 5 : Expert Copywriting
===============================
Input  : structured_brief.json (sortie Agent 4)
Output : advertorial_draft.json (schéma AdvertorialDraft)

C'est le CŒUR du pipeline — l'agent qui rédige l'advertorial.

Processus :
1. Charge le brief structuré (Agent 4)
2. Sélectionne les meilleurs advertoriaux de référence dans la base de 417
3. Construit un prompt enrichi : brief + exemples de référence
4. Envoie au LLM pour rédaction
5. Post-traitement : comptage de mots, validation structure
6. Sauvegarde le draft

L'agent peut être appelé plusieurs fois en itération (feedback QA → réécriture).

Voir PROJECT_BIBLE.md section 3.5 pour le schéma de sortie.
"""

import json
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from agents.base_agent import BaseAgent
from utils.llm_client import get_llm_client
from utils.reference_selector import ReferenceSelector
from models.schemas import AdvertorialDraft, DraftMeta

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "copywriter_system_prompt.txt"


class CopywriterAgent(BaseAgent):
    """
    Agent expert en rédaction d'advertoriaux.
    Utilise le brief structuré et des exemples de référence
    pour produire un advertorial complet et persuasif.
    """

    def __init__(
        self,
        output_dir: str = "data/output",
        reference_dir: str = "data/reference_advertorials",
    ):
        super().__init__(name="copywriter", output_dir=output_dir)
        self.llm = get_llm_client()
        self.reference_selector = ReferenceSelector()
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Charge le prompt système."""
        if PROMPT_PATH.exists():
            return PROMPT_PATH.read_text(encoding="utf-8")
        logger.warning(f"Prompt système introuvable: {PROMPT_PATH}")
        return ""

    async def run(
        self,
        structured_brief: dict,
        qa_feedback: Optional[dict] = None,
        version: int = 1,
    ) -> dict:
        """
        Pipeline principal de rédaction.

        Args:
            structured_brief: Sortie de l'Agent 4 (brief de copywriting)
            qa_feedback: (optionnel) Feedback de l'Agent 9 pour itération
            version: Numéro de version (incrémenté à chaque itération QA)

        Returns:
            dict conforme au schéma AdvertorialDraft
        """
        self.log_start(
            product=structured_brief.get("product_summary", {}).get("name", "?"),
            version=version,
            has_feedback=bool(qa_feedback),
        )

        # ── Étape 1 : Sélectionner les exemples de référence ──
        reference_examples = self._get_reference_examples(structured_brief)

        # ── Étape 2 : Construire le prompt de rédaction ──
        user_prompt = self._build_writing_prompt(
            structured_brief, reference_examples, qa_feedback, version
        )

        # ── Étape 3 : Rédaction par le LLM ──
        self.logger.info(f"Rédaction en cours (version {version})...")
        draft_data = await self.llm.ask(
            user_prompt=user_prompt,
            system_prompt=self.system_prompt,
            max_tokens=8192,  # Advertoriaux longs
            temperature=0.7,  # Créativité élevée pour le copywriting
            response_format="json",
        )

        # ── Étape 4 : Post-traitement ──
        result = self._post_process(draft_data, version)

        # Sauvegarder
        product_name = structured_brief.get("product_summary", {}).get("name", "unknown")
        safe_name = re.sub(r'[^\w\-]', '_', product_name)[:40]
        output = result.model_dump(mode="json")
        self.save_output(output, f"advertorial_draft_{safe_name}_v{version}.json")

        word_count = result.meta.word_count
        self.log_done(f"v{version} — {word_count} mots — {len(result.content.sections)} sections")
        return output

    def _get_reference_examples(self, brief: dict) -> str:
        """
        Sélectionne les meilleurs advertoriaux de référence
        en fonction du brief.
        """
        self.logger.info("Sélection des advertoriaux de référence...")

        summary = brief.get("product_summary", {})
        avatar = brief.get("avatar_profile", {})
        ammo = brief.get("copy_ammunition", {})
        primary_angle = ammo.get("primary_angle", {})

        # Pass additional brief for brief-aware reference selection
        cfg = brief.get("_config", {})
        additional_brief = cfg.get("brief", "")
        config_angle = cfg.get("angle", "")
        
        # Combine angle from brief + config override
        angle_query = primary_angle.get("angle_name", "")
        if config_angle and config_angle != angle_query:
            angle_query = f"{config_angle} {angle_query}"

        examples = self.reference_selector.get_reference_examples_for_prompt(
            product_category=summary.get("category", ""),
            product_name=summary.get("name", ""),
            problem_solved=avatar.get("main_problem", ""),
            angle=angle_query,
            target_audience=avatar.get("who", ""),
            additional_brief=additional_brief,
            max_examples=3,
            max_chars_per_example=6000,
        )

        ref_count = examples.count("EXEMPLE")
        self.logger.info(f"{ref_count} advertoriaux de référence sélectionnés")

        return examples

    def _build_writing_prompt(
        self,
        brief: dict,
        reference_examples: str,
        qa_feedback: Optional[dict],
        version: int,
    ) -> str:
        """
        Construit le prompt de rédaction complet.
        Combine le brief, les exemples de référence, et le feedback QA si c'est une itération.
        """
        parts = []

        # ── BRIEF DE COPYWRITING ──
        parts.append("# BRIEF DE COPYWRITING\n")

        # Produit
        summary = brief.get("product_summary", {})
        parts.append(f"## Produit")
        parts.append(f"- **Nom** : {summary.get('name', 'N/A')}")
        parts.append(f"- **One-liner** : {summary.get('one_liner', 'N/A')}")
        parts.append(f"- **Catégorie** : {summary.get('category', 'N/A')}")
        parts.append(f"- **Prix** : {summary.get('price_point', 'N/A')}")

        # Avatar
        avatar = brief.get("avatar_profile", {})
        parts.append(f"\n## Avatar Client")
        parts.append(f"- **Qui** : {avatar.get('who', 'N/A')}")
        parts.append(f"- **Problème principal** : {avatar.get('main_problem', 'N/A')}")
        parts.append(f"- **Désir profond** : {avatar.get('desired_outcome', 'N/A')}")
        parts.append(f"- **État émotionnel AVANT** : {avatar.get('emotional_state_before', 'N/A')}")
        parts.append(f"- **État émotionnel APRÈS** : {avatar.get('emotional_state_after', 'N/A')}")

        # Munitions de copywriting
        ammo = brief.get("copy_ammunition", {})

        # Angle principal
        primary = ammo.get("primary_angle", {})
        parts.append(f"\n## Angle Principal")
        parts.append(f"- **Angle** : {primary.get('angle_name', 'N/A')}")
        parts.append(f"- **Pourquoi** : {primary.get('why', 'N/A')}")
        parts.append(f"- **Hook template** : {primary.get('hook_template', 'N/A')}")

        # Angles secondaires
        secondary = ammo.get("secondary_angles", [])
        if secondary:
            parts.append(f"\n## Angles Secondaires")
            for a in secondary:
                parts.append(f"- {a.get('angle_name', '')}: {a.get('hook_template', '')}")

        # Hooks
        hooks = ammo.get("hooks", [])
        if hooks:
            parts.append(f"\n## Hooks Proposés (du plus fort au plus faible)")
            for i, hook in enumerate(hooks, 1):
                parts.append(f"  {i}. {hook}")

        # Bénéfices
        benefits = ammo.get("key_benefits_ranked", [])
        if benefits:
            parts.append(f"\n## Bénéfices Classés (par impact émotionnel)")
            for i, b in enumerate(benefits, 1):
                parts.append(f"  {i}. {b}")

        # Preuves
        proofs = ammo.get("proof_elements", [])
        if proofs:
            parts.append(f"\n## Éléments de Preuve")
            for p in proofs:
                parts.append(f"  - {p}")

        # Objection handlers
        handlers = ammo.get("objection_handlers", [])
        if handlers:
            parts.append(f"\n## Objection Handlers")
            for h in handlers:
                if isinstance(h, dict):
                    parts.append(f"  - Objection : {h.get('objection', '')}")
                    parts.append(f"    Réponse : {h.get('response', '')}")
                else:
                    parts.append(f"  - {h}")

        # Urgence
        urgency = ammo.get("urgency_elements", [])
        if urgency:
            parts.append(f"\n## Éléments d'Urgence")
            for u in urgency:
                parts.append(f"  - {u}")

        # CTA
        ctas = ammo.get("cta_options", [])
        if ctas:
            parts.append(f"\n## Options CTA")
            for c in ctas:
                parts.append(f"  - {c}")

        # Notes visuelles
        visual = brief.get("visual_notes", {})
        if visual:
            parts.append(f"\n## Notes Visuelles")
            parts.append(f"- **Produit** : {visual.get('product_description', 'N/A')}")
            parts.append(f"- **Mood** : {visual.get('mood', 'N/A')}")
            if visual.get("suggested_scenes"):
                parts.append("- **Scènes suggérées** :")
                for s in visual["suggested_scenes"]:
                    parts.append(f"    - {s}")

        # ── EXEMPLES DE RÉFÉRENCE ──
        if reference_examples and "(Aucun" not in reference_examples:
            parts.append(f"\n\n---\n# ADVERTORIAUX DE RÉFÉRENCE\n")
            parts.append(
                "Voici des exemples d'advertoriaux similaires qui ont bien fonctionné. "
                "Analyse leur structure, leur ton, leurs transitions. "
                "Inspire-toi de ce qui fonctionne, adapte au produit actuel."
            )
            parts.append(reference_examples)

        # ── FEEDBACK QA (si itération) ──
        if qa_feedback:
            parts.append(f"\n\n---\n# FEEDBACK QUALITÉ (version précédente)\n")
            parts.append(
                "L'advertorial précédent a reçu les retours suivants. "
                "Corrige SPÉCIFIQUEMENT ces points dans cette nouvelle version."
            )

            overall = qa_feedback.get("overall_score", 0)
            parts.append(f"\n**Score global** : {overall}/10")

            criteria = qa_feedback.get("criteria", {})
            for name, data in criteria.items():
                if isinstance(data, dict):
                    score = data.get("score", 0)
                    feedback = data.get("feedback", "")
                    if score < 7 and feedback:
                        parts.append(f"- **{name}** ({score}/10) : {feedback}")

            improvements = qa_feedback.get("improvements", [])
            if improvements:
                parts.append(f"\n**Améliorations demandées** :")
                for imp in improvements:
                    parts.append(f"  - {imp}")

        # ── CONFIG OVERRIDES (langue, angle, ton, etc.) ──
        cfg = brief.get("_config", {})
        lang_name = cfg.get("language_name", "")
        lang_code = cfg.get("language", "en")

        if lang_name:
            parts.append(f"\n\n---\n# ⚠️ DIRECTIVES OBLIGATOIRES\n")
            parts.append(f"**LANGUE** : Rédige TOUT l'advertorial en **{lang_name}** ({lang_code}). Titres, body, CTA — tout doit être en {lang_name}.")
            if cfg.get("tone"):
                parts.append(f"**TON** : {cfg['tone']}")
            if cfg.get("angle"):
                parts.append(f"**ANGLE** : {cfg['angle']}")
            if cfg.get("structure"):
                parts.append(f"**STRUCTURE** : {cfg['structure']}")
            if cfg.get("persona"):
                parts.append(f"**PERSONA CIBLE** : {cfg['persona']}")
            if cfg.get("brief"):
                parts.append(f"""
# 🔴 BRIEF CRÉATIF — PRIORITÉ ABSOLUE

Le brief ci-dessous est la directive créative principale donnée par le client. 
Il PRIME sur toutes les autres instructions (angle, structure, exemples de référence).

**Tu DOIS suivre ce brief à la lettre :**
- Le CONCEPT, le STORYLINE et le MESSAGE doivent correspondre exactement à ce qui est décrit
- N'invente PAS un angle différent — adapte ton écriture pour servir CE brief
- Si le brief demande une histoire spécifique (ex: message du fondateur, liquidation, etc.), c'est LE cœur de l'advertorial
- Les exemples de référence servent pour le STYLE d'écriture uniquement, PAS pour le contenu/angle — le contenu vient du brief

**BRIEF DU CLIENT :**
\"\"\"{cfg['brief']}\"\"\"

Rappel : cet advertorial doit raconter EXACTEMENT l'histoire décrite dans le brief ci-dessus. Pas une variation. Pas une réinterprétation. LE brief.
""")

        # ── COMPOSANTS HTML DU TEMPLATE ──
        template_id = cfg.get("template", "editorial")
        try:
            from agents.prompts.template_components import get_template_instructions
            template_instructions = get_template_instructions(template_id)
            parts.append(f"\n\n---\n{template_instructions}")
        except Exception as e:
            self.logger.warning(f"Could not load template instructions: {e}")

        # ── INSTRUCTION FINALE ──
        parts.append(f"\n\n---\n")
        if qa_feedback:
            parts.append(
                f"Rédige la VERSION {version} de l'advertorial en corrigeant "
                f"les points soulevés par le contrôle qualité. "
                f"Garde ce qui était bon, améliore ce qui était faible."
            )
        else:
            parts.append(
                "Rédige maintenant l'advertorial complet. "
                "Utilise l'angle principal et les hooks fournis. "
                "Chaque section doit avoir un visual_placeholder décrivant l'image souhaitée. "
                "L'advertorial doit faire MINIMUM 1200 mots et idéalement 1400-1800 mots. "
                "C'est une EXIGENCE — même pour les templates courts (urgency-sale, listicle), "
                "tu dois atteindre au moins 1200 mots en développant chaque section suffisamment."
            )
        if lang_name:
            parts.append(f"\n⚠️ RAPPEL : TOUT le contenu (headline, sections, CTA) DOIT être en {lang_name}.")
        parts.append("\nRéponds UNIQUEMENT en JSON valide, sans texte autour.")

        return "\n".join(parts)

    def _post_process(self, draft_data: dict, version: int) -> AdvertorialDraft:
        """
        Post-traitement du draft :
        - Comptage de mots
        - Validation de la structure
        - Nettoyage HTML
        """
        self.logger.info("Post-traitement du draft...")

        # Compter les mots dans le body_html de toutes les sections
        total_words = 0
        content = draft_data.get("content", {})
        for section in content.get("sections", []):
            body = section.get("body_html", "")
            # Nettoyer le HTML pour compter les mots
            clean = re.sub(r'<[^>]+>', '', body)
            total_words += len(clean.split())

        # Construire le meta
        meta = DraftMeta(
            version=version,
            word_count=total_words,
        )

        result_dict = {"meta": meta.model_dump(mode="json")}

        # Injecter le contenu et le SEO
        if "content" in draft_data:
            result_dict["content"] = draft_data["content"]
        if "seo" in draft_data:
            result_dict["seo"] = draft_data["seo"]

        # Valider avec Pydantic
        result = AdvertorialDraft(**result_dict)

        # Vérifications de qualité basiques
        sections = result.content.sections
        if len(sections) < 4:
            self.logger.warning(
                f"Seulement {len(sections)} sections — un bon advertorial en a 6-9"
            )
        if total_words < 500:
            self.logger.warning(
                f"Seulement {total_words} mots — un bon advertorial fait 800-1500 mots"
            )
        elif total_words > 2000:
            self.logger.warning(
                f"{total_words} mots — c'est peut-être trop long (cible: 800-1500)"
            )

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
        print("Usage: python -m agents.copywriter <structured_brief.json> [qa_feedback.json]")
        print("")
        print("Exemples :")
        print("  python -m agents.copywriter data/output/structured_brief_serum.json")
        print("  python -m agents.copywriter data/output/structured_brief_serum.json data/output/qa_report_serum.json")
        sys.exit(1)

    # Charger le brief
    with open(sys.argv[1], "r") as f:
        brief = json.load(f)

    # Charger le feedback QA si fourni
    qa_feedback = None
    version = 1
    if len(sys.argv) > 2:
        with open(sys.argv[2], "r") as f:
            qa_feedback = json.load(f)
        version = qa_feedback.get("version", 1) + 1
        print(f"Mode itération — version {version} (feedback QA chargé)")

    agent = CopywriterAgent()
    result = await agent.run(
        structured_brief=brief,
        qa_feedback=qa_feedback,
        version=version,
    )

    print("\n" + "=" * 60)
    print(f"ADVERTORIAL v{version}")
    print("=" * 60)

    content = result.get("content", {})
    print(f"\n📰 {content.get('headline', 'N/A')}")
    print(f"   {content.get('subheadline', 'N/A')}")

    print(f"\n📄 Structure ({len(content.get('sections', []))} sections) :")
    for i, section in enumerate(content.get("sections", []), 1):
        s_type = section.get("type", "?")
        heading = section.get("heading", "(sans titre)")
        body = re.sub(r'<[^>]+>', '', section.get("body_html", ""))
        words = len(body.split())
        print(f"   {i}. [{s_type.upper()}] {heading} ({words} mots)")

    meta = result.get("meta", {})
    print(f"\n📊 Total : {meta.get('word_count', 0)} mots")

    seo = result.get("seo", {})
    print(f"\n🔍 SEO : {seo.get('meta_title', 'N/A')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
