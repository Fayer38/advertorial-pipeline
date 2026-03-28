"""
Agent 9 : Contrôle Qualité (QA)
==================================
Input  : advertorial_draft.json (Agent 5) + structured_brief.json (Agent 4)
Output : qa_report.json (schéma QAReport)

Processus :
1. Charge l'advertorial et le brief original
2. Optionnel : charge des advertoriaux de référence pour comparaison
3. Envoie au LLM pour évaluation sur 7 critères
4. Si score < seuil → feedback renvoyé à l'Agent 5 pour itération

Voir PROJECT_BIBLE.md section 3.8 pour le schéma de sortie.
"""

import json
import re
import logging
from pathlib import Path
from typing import Optional

from agents.base_agent import BaseAgent
from utils.llm_client import get_llm_client
from utils.reference_selector import ReferenceSelector
from models.schemas import QAReport

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "qa_system_prompt.txt"

# Score minimum pour passer (configurable dans config.yaml)
DEFAULT_MIN_SCORE = 7
DEFAULT_MAX_ITERATIONS = 3


class QACheckerAgent(BaseAgent):

    def __init__(
        self,
        output_dir: str = "data/output",
        reference_dir: str = "data/reference_advertorials",
        min_score: int = DEFAULT_MIN_SCORE,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ):
        super().__init__(name="qa_checker", output_dir=output_dir)
        self.llm = get_llm_client()
        self.reference_selector = ReferenceSelector(reference_dir=reference_dir)
        self.system_prompt = self._load_system_prompt()
        self.min_score = min_score
        self.max_iterations = max_iterations

    def _load_system_prompt(self) -> str:
        if PROMPT_PATH.exists():
            return PROMPT_PATH.read_text(encoding="utf-8")
        return ""

    async def run(
        self,
        advertorial_draft: dict,
        structured_brief: dict,
        version: int = 1,
    ) -> dict:
        """
        Évalue l'advertorial et retourne un rapport de qualité.

        Args:
            advertorial_draft: Sortie de l'Agent 5
            structured_brief: Sortie de l'Agent 4 (pour vérifier la cohérence)
            version: Numéro de version de l'advertorial

        Returns:
            dict conforme au schéma QAReport
        """
        self.log_start(version=version)

        user_prompt = self._build_prompt(advertorial_draft, structured_brief, version)

        self.logger.info(f"Évaluation qualité v{version}...")
        qa_data = await self.llm.ask(
            user_prompt=user_prompt,
            system_prompt=self.system_prompt,
            max_tokens=3000,
            temperature=0.2,  # Évaluation objective
            response_format="json",
        )

        # Injecter la version
        qa_data["version"] = version

        # Calculer le score global si pas déjà fait
        if "overall_score" not in qa_data:
            criteria = qa_data.get("criteria", {})
            scores = [
                c.get("score", 0) for c in criteria.values()
                if isinstance(c, dict)
            ]
            qa_data["overall_score"] = round(sum(scores) / len(scores)) if scores else 0

        # Déterminer si ça passe
        qa_data["passed"] = qa_data["overall_score"] >= self.min_score

        # Valider avec Pydantic
        result = QAReport(**qa_data)
        output = result.model_dump(mode="json")
        self.save_output(output, f"qa_report_v{version}.json")

        status = "✅ PASS" if result.passed else "❌ FAIL"
        self.log_done(f"{status} — Score: {result.overall_score}/10 (seuil: {self.min_score})")

        return output

    async def run_with_iteration(
        self,
        advertorial_draft: dict,
        structured_brief: dict,
        copywriter_agent,
        version: int = 1,
    ) -> tuple[dict, dict]:
        """
        Évalue et itère automatiquement si le score est insuffisant.
        Relance le copywriter avec le feedback jusqu'à satisfaction ou max_iterations.

        Args:
            advertorial_draft: Premier draft
            structured_brief: Brief original
            copywriter_agent: Instance de CopywriterAgent pour la réécriture
            version: Version de départ

        Returns:
            tuple (advertorial_final, qa_report_final)
        """
        current_draft = advertorial_draft
        current_version = version

        for iteration in range(self.max_iterations):
            # Évaluer
            qa_report = await self.run(current_draft, structured_brief, current_version)

            if qa_report.get("passed", False):
                self.logger.info(
                    f"Advertorial validé en v{current_version} "
                    f"(score: {qa_report['overall_score']}/10)"
                )
                return current_draft, qa_report

            # Score insuffisant → réécrire
            current_version += 1
            self.logger.info(
                f"Score insuffisant ({qa_report['overall_score']}/10). "
                f"Réécriture → v{current_version}..."
            )

            current_draft = await copywriter_agent.run(
                structured_brief=structured_brief,
                qa_feedback=qa_report,
                version=current_version,
            )

        # Max itérations atteintes
        self.logger.warning(
            f"Max itérations ({self.max_iterations}) atteintes. "
            f"Dernier score: {qa_report['overall_score']}/10"
        )
        return current_draft, qa_report

    def _build_prompt(
        self,
        draft: dict,
        brief: dict,
        version: int,
    ) -> str:
        parts = []

        # Brief original (pour vérifier la cohérence)
        parts.append("# BRIEF ORIGINAL\n")
        summary = brief.get("product_summary", {})
        parts.append(f"- **Produit** : {summary.get('name', '')}")
        parts.append(f"- **One-liner** : {summary.get('one_liner', '')}")

        avatar = brief.get("avatar_profile", {})
        parts.append(f"- **Avatar** : {avatar.get('who', '')}")
        parts.append(f"- **Problème** : {avatar.get('main_problem', '')}")

        ammo = brief.get("copy_ammunition", {})
        primary = ammo.get("primary_angle", {})
        parts.append(f"- **Angle principal** : {primary.get('angle_name', '')}")
        parts.append(f"- **Hooks prévus** : {', '.join(ammo.get('hooks', [])[:3])}")

        # Advertorial à évaluer
        parts.append(f"\n\n# ADVERTORIAL À ÉVALUER (VERSION {version})\n")
        content = draft.get("content", {})
        parts.append(f"## {content.get('headline', '')}")
        parts.append(f"### {content.get('subheadline', '')}\n")

        for section in content.get("sections", []):
            s_type = section.get("type", "")
            heading = section.get("heading", "")
            body = section.get("body_html", "")
            if heading:
                parts.append(f"### [{s_type.upper()}] {heading}")
            else:
                parts.append(f"### [{s_type.upper()}]")
            parts.append(body)
            parts.append("")

        # Méta
        meta = draft.get("meta", {})
        parts.append(f"\n**Nombre de mots** : {meta.get('word_count', '?')}")
        parts.append(f"**Version** : {version}")

        # Référence (optionnel)
        ref_examples = self.reference_selector.get_reference_examples_for_prompt(
            product_category=summary.get("category", ""),
            max_examples=1,
            max_chars_per_example=3000,
        )
        if ref_examples and "(Aucun" not in ref_examples:
            parts.append("\n\n# ADVERTORIAL DE RÉFÉRENCE (pour comparaison)\n")
            parts.append(ref_examples)

        parts.append("\n---\nÉvalue cet advertorial sur les 7 critères. Réponds en JSON uniquement.")

        return "\n".join(parts)


async def main():
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    if len(sys.argv) < 3:
        print("Usage: python -m agents.qa_checker <advertorial_draft.json> <structured_brief.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        draft = json.load(f)
    with open(sys.argv[2]) as f:
        brief = json.load(f)

    agent = QACheckerAgent()
    result = await agent.run(draft, brief)

    status = "✅ PASS" if result["passed"] else "❌ FAIL"
    print(f"\n{status} — Score global : {result['overall_score']}/10\n")

    for name, data in result.get("criteria", {}).items():
        score = data.get("score", 0)
        indicator = "🟢" if score >= 7 else "🟡" if score >= 5 else "🔴"
        print(f"  {indicator} {name}: {score}/10")
        if score < 7 and data.get("feedback"):
            print(f"     → {data['feedback'][:100]}...")

    if result.get("improvements"):
        print(f"\n📋 Améliorations suggérées :")
        for imp in result["improvements"]:
            print(f"  - {imp}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
