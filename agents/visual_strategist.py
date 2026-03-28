"""
Agent 6 : Stratège Visuel
===========================
Input  : advertorial_draft.json (Agent 5) + image_description (Agent 3) + brief (Agent 4)
Output : visual_plan.json (schéma VisualPlan)

Processus :
1. Analyse l'advertorial section par section
2. Détermine les visuels nécessaires (type, format, mood, priorité)
3. Produit un plan visuel complet

Voir PROJECT_BIBLE.md section 3.6 pour le schéma de sortie.
"""

import json
import re
import logging
from pathlib import Path
from typing import Optional

from agents.base_agent import BaseAgent
from utils.llm_client import get_llm_client
from models.schemas import VisualPlan

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "visual_strategist_system_prompt.txt"


class VisualStrategistAgent(BaseAgent):

    def __init__(self, output_dir: str = "data/output"):
        super().__init__(name="visual_strategist", output_dir=output_dir)
        self.llm = get_llm_client()
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        if PROMPT_PATH.exists():
            return PROMPT_PATH.read_text(encoding="utf-8")
        return ""

    async def run(
        self,
        advertorial_draft: dict,
        image_description: Optional[dict] = None,
        structured_brief: Optional[dict] = None,
    ) -> dict:
        self.log_start()

        user_prompt = self._build_prompt(
            advertorial_draft, image_description, structured_brief
        )

        self.logger.info("Analyse visuelle en cours...")
        plan_data = await self.llm.ask(
            user_prompt=user_prompt,
            system_prompt=self.system_prompt,
            max_tokens=3000,
            temperature=0.4,
            response_format="json",
        )

        result = VisualPlan(**plan_data)
        output = result.model_dump(mode="json")
        self.save_output(output, "visual_plan.json")

        self.log_done(f"{len(result.scenes)} scènes planifiées")
        return output

    def _build_prompt(
        self,
        draft: dict,
        image_desc: Optional[dict],
        brief: Optional[dict],
    ) -> str:
        parts = []

        # Advertorial
        parts.append("# ADVERTORIAL À ILLUSTRER\n")
        content = draft.get("content", {})
        parts.append(f"**Titre** : {content.get('headline', '')}")
        parts.append(f"**Sous-titre** : {content.get('subheadline', '')}\n")

        for i, section in enumerate(content.get("sections", [])):
            s_type = section.get("type", "?")
            heading = section.get("heading", "")
            body = re.sub(r'<[^>]+>', '', section.get("body_html", ""))
            placeholder = section.get("visual_placeholder", {})

            parts.append(f"### Section {i} [{s_type.upper()}] : {heading}")
            parts.append(body[:500])
            if placeholder.get("description"):
                parts.append(f"  (suggestion visuelle du copywriter : {placeholder['description']})")
            parts.append("")

        # Description image produit
        if image_desc:
            desc = image_desc.get("description", {})
            parts.append("\n# DESCRIPTION VISUELLE DU PRODUIT\n")
            parts.append(f"- **Court** : {desc.get('short', '')}")
            parts.append(f"- **Détail** : {desc.get('detailed', '')}")
            parts.append(f"- **Packaging** : {desc.get('packaging', '')}")
            parts.append(f"- **Couleurs** : {', '.join(desc.get('colors', []))}")

        # Avatar
        if brief:
            avatar = brief.get("avatar_profile", {})
            parts.append("\n# PROFIL AVATAR\n")
            parts.append(f"- **Qui** : {avatar.get('who', '')}")
            parts.append(f"- **Avant** : {avatar.get('emotional_state_before', '')}")
            parts.append(f"- **Après** : {avatar.get('emotional_state_after', '')}")

            mood = brief.get("visual_notes", {}).get("mood", "")
            if mood:
                parts.append(f"- **Mood souhaité** : {mood}")

        parts.append("\n---\nProduis le plan visuel complet en JSON.")

        return "\n".join(parts)


async def main():
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python -m agents.visual_strategist <advertorial_draft.json> [image_description.json] [structured_brief.json]")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        draft = json.load(f)

    image_desc = None
    if len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            image_desc = json.load(f)

    brief = None
    if len(sys.argv) > 3:
        with open(sys.argv[3]) as f:
            brief = json.load(f)

    agent = VisualStrategistAgent()
    result = await agent.run(draft, image_desc, brief)

    print(f"\n🎨 {len(result.get('scenes', []))} scènes planifiées :")
    for s in result.get("scenes", []):
        print(f"  [{s['priority'].upper()}] Section {s['section_index']} — {s['scene_type']} ({s['format']}) : {s['description'][:80]}...")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
