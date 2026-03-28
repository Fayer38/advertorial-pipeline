"""
Agent 7 : Générateur de Prompts Image
========================================
Input  : visual_plan.json (Agent 6) + image_description (Agent 3)
Output : image_prompts.json (schéma PromptCollection)

Processus :
1. Filtre les scènes de type "image" dans le plan visuel
2. Enrichit chaque scène avec la description produit
3. Génère des prompts optimisés pour la plateforme cible (MJ/Leonardo/Flux)

Voir PROJECT_BIBLE.md section 3.7 pour le schéma de sortie.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from agents.base_agent import BaseAgent
from utils.llm_client import get_llm_client
from models.schemas import PromptCollection

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "image_prompter_system_prompt.txt"

# Plateformes par défaut, configurable
DEFAULT_PLATFORM = "midjourney"


class ImagePrompterAgent(BaseAgent):

    def __init__(self, output_dir: str = "data/output"):
        super().__init__(name="image_prompter", output_dir=output_dir)
        self.llm = get_llm_client()
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        if PROMPT_PATH.exists():
            return PROMPT_PATH.read_text(encoding="utf-8")
        return ""

    async def run(
        self,
        visual_plan: dict,
        image_description: Optional[dict] = None,
        platform: str = DEFAULT_PLATFORM,
    ) -> dict:
        self.log_start(platform=platform)

        # Filtrer les scènes image uniquement
        all_scenes = visual_plan.get("scenes", [])
        image_scenes = [s for s in all_scenes if s.get("format", "image") == "image"]

        if not image_scenes:
            self.logger.warning("Aucune scène image dans le plan visuel")
            result = PromptCollection(prompts=[])
            output = result.model_dump(mode="json")
            self.save_output(output, "image_prompts.json")
            return output

        self.logger.info(f"{len(image_scenes)} scènes image à prompter...")

        user_prompt = self._build_prompt(image_scenes, image_description, platform)

        prompts_data = await self.llm.ask(
            user_prompt=user_prompt,
            system_prompt=self.system_prompt,
            max_tokens=4096,
            temperature=0.5,
            response_format="json",
        )

        result = PromptCollection(**prompts_data)
        output = result.model_dump(mode="json")
        self.save_output(output, "image_prompts.json")

        self.log_done(f"{len(result.prompts)} prompts image générés pour {platform}")
        return output

    def _build_prompt(
        self,
        scenes: list[dict],
        image_desc: Optional[dict],
        platform: str,
    ) -> str:
        parts = []

        parts.append(f"# PLATEFORME CIBLE : {platform.upper()}\n")

        # Description produit
        if image_desc:
            desc = image_desc.get("description", {})
            parts.append("# DESCRIPTION DU PRODUIT (à intégrer dans les visuels)\n")
            parts.append(f"- **Apparence** : {desc.get('short', '')}")
            parts.append(f"- **Détail** : {desc.get('detailed', '')}")
            parts.append(f"- **Packaging** : {desc.get('packaging', '')}")
            parts.append(f"- **Couleurs** : {', '.join(desc.get('colors', []))}")
            parts.append(f"- **Texture** : {desc.get('texture_material', '')}")
            parts.append(f"- **Taille** : {desc.get('size_impression', '')}")
            parts.append("")

        # Scènes à prompter
        parts.append("# SCÈNES À GÉNÉRER\n")
        for i, scene in enumerate(scenes):
            parts.append(f"## Scène {scene.get('section_index', i)}")
            parts.append(f"- **Type** : {scene.get('scene_type', 'product')}")
            parts.append(f"- **Description** : {scene.get('description', '')}")
            parts.append(f"- **Mood** : {scene.get('mood', '')}")
            parts.append(f"- **Ratio** : {scene.get('aspect_ratio', '16:9')}")
            parts.append(f"- **Priorité** : {scene.get('priority', 'supporting')}")
            parts.append("")

        parts.append("---\nGénère un prompt optimisé pour chaque scène. Réponds en JSON uniquement.")

        return "\n".join(parts)


async def main():
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    if len(sys.argv) < 2:
        print("Usage: python -m agents.image_prompter <visual_plan.json> [image_description.json] [--platform midjourney|leonardo|flux]")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        plan = json.load(f)

    image_desc = None
    platform = DEFAULT_PLATFORM

    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == "--platform" and i + 1 < len(sys.argv):
            platform = sys.argv[i + 1]
        elif not arg.startswith("--"):
            with open(arg) as f:
                image_desc = json.load(f)

    agent = ImagePrompterAgent()
    result = await agent.run(plan, image_desc, platform)

    print(f"\n🖼️  {len(result.get('prompts', []))} prompts générés pour {platform} :")
    for p in result.get("prompts", []):
        print(f"\n  Scene {p['scene_index']} :")
        print(f"    {p['prompt'][:120]}...")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
