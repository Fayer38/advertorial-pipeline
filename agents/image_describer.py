"""
Agent 3 : Descripteur Image
=============================
Input  : Image(s) produit (URL ou fichier local)
Output : image_description.json (schéma ImageDescription)

Processus :
1. Charge l'image (depuis URL ou fichier local)
2. Encode en base64 pour l'API Claude (vision)
3. Envoie à Claude avec le prompt de description détaillée
4. Valide et sauvegarde en JSON

Cet agent tourne EN PARALLÈLE des Agents 1 et 2 dans le pipeline.

Voir PROJECT_BIBLE.md section 3.3 pour le schéma de sortie.
"""

import json
import asyncio
import base64
import logging
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Optional

import aiohttp

from agents.base_agent import BaseAgent
from utils.llm_client import LLMClient
from models.schemas import ImageDescription, ImageDescriptionMeta

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "image_describer_system_prompt.txt"

# Types MIME supportés par Claude Vision
SUPPORTED_MIMES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


class ImageDescriberAgent(BaseAgent):
    """
    Agent de description d'images produit.
    Utilise Claude Vision pour analyser les images et produire
    des descriptions détaillées exploitables pour la génération de visuels.
    """

    def __init__(self, output_dir: str = "data/output"):
        super().__init__(name="image_describer", output_dir=output_dir)
        self.system_prompt = self._load_system_prompt()

        # Client Anthropic direct (on a besoin de l'API vision, pas du wrapper)
        import os
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY manquante")
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    def _load_system_prompt(self) -> str:
        """Charge le prompt système."""
        if PROMPT_PATH.exists():
            return PROMPT_PATH.read_text(encoding="utf-8")
        logger.warning(f"Prompt système introuvable: {PROMPT_PATH}")
        return ""

    async def run(
        self,
        image_source: str,
        product_name: str = "",
    ) -> dict:
        """
        Pipeline principal de description d'image.

        Args:
            image_source: URL de l'image OU chemin vers un fichier local
            product_name: Nom du produit (optionnel, pour le nommage du fichier)

        Returns:
            dict conforme au schéma ImageDescription
        """
        self.log_start(image_source=image_source, product_name=product_name)

        # ── Étape 1 : Charger et encoder l'image ──
        image_data, media_type = await self._load_image(image_source)

        # ── Étape 2 : Analyser avec Claude Vision ──
        description_data = await self._describe_with_vision(
            image_data, media_type, image_source
        )

        # ── Étape 3 : Assembler et valider ──
        result = self._assemble_result(image_source, description_data)

        # Sauvegarder
        safe_name = product_name or self._safe_filename(image_source)
        output = result.model_dump(mode="json")
        self.save_output(output, f"image_description_{safe_name}.json")

        self.log_done(f"Description: {result.description.short[:80]}...")
        return output

    async def run_batch(
        self,
        image_sources: list[str],
        product_name: str = "",
    ) -> list[dict]:
        """
        Décrit plusieurs images en parallèle.
        Utile quand on a plusieurs photos du même produit.

        Args:
            image_sources: Liste d'URLs ou chemins fichiers
            product_name: Nom du produit

        Returns:
            Liste de dicts conformes au schéma ImageDescription
        """
        self.logger.info(f"Batch de {len(image_sources)} images à décrire...")

        tasks = [
            self.run(source, product_name=f"{product_name}_{i}")
            for i, source in enumerate(image_sources)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filtrer les erreurs
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.log_error(result, f"Image {i}: {image_sources[i]}")
            else:
                valid_results.append(result)

        self.logger.info(
            f"Batch terminé: {len(valid_results)}/{len(image_sources)} images décrites"
        )
        return valid_results

    async def _load_image(self, source: str) -> tuple[str, str]:
        """
        Charge une image depuis une URL ou un fichier local.
        Retourne (base64_data, media_type).
        """
        if source.startswith(("http://", "https://")):
            return await self._load_image_from_url(source)
        else:
            return self._load_image_from_file(source)

    async def _load_image_from_url(self, url: str) -> tuple[str, str]:
        """Télécharge une image depuis une URL et la convertit en base64."""
        self.logger.info(f"Téléchargement de l'image: {url[:80]}...")

        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(
                        f"Impossible de télécharger l'image ({resp.status}): {url}"
                    )

                content_type = resp.content_type or ""
                image_bytes = await resp.read()

        # Déterminer le type MIME
        media_type = self._resolve_media_type(content_type, url)

        # Encoder en base64
        b64_data = base64.b64encode(image_bytes).decode("utf-8")

        size_kb = len(image_bytes) / 1024
        self.logger.info(f"Image chargée: {size_kb:.0f} KB, type: {media_type}")

        return b64_data, media_type

    def _load_image_from_file(self, filepath: str) -> tuple[str, str]:
        """Charge une image depuis un fichier local."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Image introuvable: {filepath}")

        # Déterminer le type MIME
        mime, _ = mimetypes.guess_type(str(path))
        media_type = mime or "image/jpeg"

        if media_type not in SUPPORTED_MIMES:
            raise ValueError(
                f"Type d'image non supporté: {media_type}. "
                f"Supportés: {SUPPORTED_MIMES}"
            )

        # Lire et encoder
        with open(path, "rb") as f:
            image_bytes = f.read()

        b64_data = base64.b64encode(image_bytes).decode("utf-8")

        size_kb = len(image_bytes) / 1024
        self.logger.info(f"Image locale chargée: {size_kb:.0f} KB, type: {media_type}")

        return b64_data, media_type

    def _resolve_media_type(self, content_type: str, url: str) -> str:
        """Détermine le type MIME de l'image."""
        # Essayer le content-type de la réponse
        if content_type and content_type in SUPPORTED_MIMES:
            return content_type

        # Essayer depuis l'extension de l'URL
        url_clean = url.split("?")[0].lower()
        if url_clean.endswith(".png"):
            return "image/png"
        elif url_clean.endswith((".jpg", ".jpeg")):
            return "image/jpeg"
        elif url_clean.endswith(".webp"):
            return "image/webp"
        elif url_clean.endswith(".gif"):
            return "image/gif"

        # Défaut
        return "image/jpeg"

    async def _describe_with_vision(
        self,
        image_b64: str,
        media_type: str,
        source: str,
    ) -> dict:
        """
        Envoie l'image à Claude Vision pour description détaillée.
        """
        self.logger.info("Analyse de l'image par Claude Vision...")

        user_content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": image_b64,
                },
            },
            {
                "type": "text",
                "text": (
                    "Analyse cette image produit en détail et produis la description "
                    "structurée en JSON comme demandé dans tes instructions. "
                    "Réponds UNIQUEMENT avec le JSON, sans texte autour."
                ),
            },
        ]

        message = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            temperature=0.1,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )

        # Extraire le texte de la réponse
        raw_text = ""
        for block in message.content:
            if block.type == "text":
                raw_text += block.text

        # Parser le JSON
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError as e:
            self.log_error(e, "JSON parsing de la description image")
            raise ValueError(f"Réponse non-JSON de Claude Vision: {e}")

        self.logger.info("Description image générée")
        return result

    def _assemble_result(
        self, image_source: str, description_data: dict
    ) -> ImageDescription:
        """Assemble et valide le résultat avec Pydantic."""
        meta = ImageDescriptionMeta(image_url=image_source)

        result_dict = {"meta": meta.model_dump(mode="json")}

        # Le LLM peut retourner le contenu directement ou dans une clé "description"
        if "description" in description_data:
            result_dict["description"] = description_data["description"]
        else:
            # Le LLM a peut-être retourné les champs au top level
            result_dict["description"] = description_data

        return ImageDescription(**result_dict)

    def _safe_filename(self, source: str) -> str:
        """Crée un nom de fichier sûr depuis une source."""
        import hashlib
        return hashlib.md5(source.encode()).hexdigest()[:12]


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
        print("Usage: python -m agents.image_describer <IMAGE_URL_OU_FICHIER>")
        print("")
        print("Exemples :")
        print("  python -m agents.image_describer https://cdn.shopify.com/.../product.jpg")
        print("  python -m agents.image_describer ./images/product_photo.png")
        print("  python -m agents.image_describer image1.jpg image2.jpg image3.jpg")
        sys.exit(1)

    sources = sys.argv[1:]

    agent = ImageDescriberAgent()

    if len(sources) == 1:
        result = await agent.run(sources[0])
        desc = result.get("description", {})
        print("\n" + "=" * 60)
        print("DESCRIPTION IMAGE")
        print("=" * 60)
        print(f"\n📸 Court : {desc.get('short', 'N/A')}")
        print(f"\n📝 Détail : {desc.get('detailed', 'N/A')}")
        print(f"\n🎨 Couleurs : {', '.join(desc.get('colors', []))}")
        print(f"\n📦 Packaging : {desc.get('packaging', 'N/A')}")
        print(f"\n🌿 Contexte : {desc.get('lifestyle_context', 'N/A')}")
    else:
        results = await agent.run_batch(sources)
        for i, result in enumerate(results):
            desc = result.get("description", {})
            print(f"\n--- Image {i+1} ---")
            print(f"  Court : {desc.get('short', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())
