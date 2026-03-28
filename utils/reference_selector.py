"""
Sélecteur d'advertoriaux de référence — adapté au VPS OpenClaw.

Sources de données sur le VPS :
1. ADVERTORIAL_DB.json — 417 entrées avec métadonnées (headline, angle, score, audience...)
2. ADVERTORIAL_CONTENT_READY.json — 205 advertoriaux avec contenu texte
3. ADVERTORIAL_STRUCTURES.json — analyses structurées (en cours de génération)

Stratégie de sélection :
- Matching par mots-clés sur les métadonnées (angle, audience, produit, headline)
- Scoring par adv_score (qualité intrinsèque de l'advertorial)
- Contenu texte chargé depuis CONTENT_READY quand disponible
"""

import re
import json
import logging
from pathlib import Path
from typing import Optional
from collections import Counter

logger = logging.getLogger(__name__)

# Chemins par défaut sur le VPS
DEFAULT_DB_PATH = "/root/.openclaw/workspace-anstrex-scraper/ADVERTORIAL_DB.json"
DEFAULT_CONTENT_PATH = "/root/.openclaw/workspace-anstrex-scraper/ADVERTORIAL_CONTENT_READY.json"
DEFAULT_STRUCTURES_PATH = "/root/.openclaw/workspace-anstrex-scraper/ADVERTORIAL_STRUCTURES.json"


class ReferenceSelector:
    """
    Sélectionne les advertoriaux de référence les plus pertinents
    depuis la base de données du VPS.
    """

    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        content_path: str = DEFAULT_CONTENT_PATH,
        structures_path: str = DEFAULT_STRUCTURES_PATH,
    ):
        self.db_path = Path(db_path)
        self.content_path = Path(content_path)
        self.structures_path = Path(structures_path)

        self._db: Optional[dict] = None
        self._content: Optional[dict] = None
        self._structures: Optional[dict] = None

    def _load_db(self) -> dict:
        """Charge la base de métadonnées (417 entrées)."""
        if self._db is not None:
            return self._db

        if not self.db_path.exists():
            logger.warning(f"ADVERTORIAL_DB.json introuvable : {self.db_path}")
            self._db = {}
            return self._db

        with open(self.db_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._db = data.get("advertorials", {})
        logger.info(f"Base advertoriaux chargée : {len(self._db)} entrées")
        return self._db

    def _load_content(self) -> dict:
        """Charge les contenus texte (205 advertoriaux avec texte)."""
        if self._content is not None:
            return self._content

        if not self.content_path.exists():
            logger.warning(f"ADVERTORIAL_CONTENT_READY.json introuvable : {self.content_path}")
            self._content = {}
            return self._content

        with open(self.content_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            self._content = data
        elif isinstance(data, list):
            self._content = {item.get("url", f"entry_{i}"): item for i, item in enumerate(data)}
        else:
            self._content = {}

        logger.info(f"Contenus advertoriaux chargés : {len(self._content)} avec texte")
        return self._content

    def _load_structures(self) -> dict:
        """Charge les analyses structurées (si disponibles)."""
        if self._structures is not None:
            return self._structures

        if not self.structures_path.exists():
            logger.info("ADVERTORIAL_STRUCTURES.json pas encore disponible")
            self._structures = {}
            return self._structures

        with open(self.structures_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._structures = data if isinstance(data, dict) else {}
        logger.info(f"Structures advertoriaux chargées : {len(self._structures)}")
        return self._structures

    def find_best_references(
        self,
        product_category: str = "",
        product_name: str = "",
        problem_solved: str = "",
        angle: str = "",
        target_audience: str = "",
        max_results: int = 5,
    ) -> list[dict]:
        """
        Trouve les advertoriaux les plus pertinents.
        Scoring multi-critères :
        - Angle marketing (+10)
        - Audience cible (+8)
        - Produit/catégorie (+5)
        - Headline (+3 par match)
        - adv_score intrinsèque (+0 à +5 bonus)
        - Contenu disponible (+3 bonus)
        """
        db = self._load_db()
        content = self._load_content()

        if not db:
            return []

        search_terms = set()
        for text in [product_category, product_name, problem_solved, angle, target_audience]:
            if text:
                words = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', text.lower())
                search_terms.update(words)

        scored = []

        for url, entry in db.items():
            score = 0

            e_angle = (entry.get("angle") or "").lower()
            e_audience = (entry.get("target_audience") or "").lower()
            e_headline = (entry.get("headline") or "").lower()
            e_product = (entry.get("product_name") or "").lower()
            e_adv_score = entry.get("adv_score", 0)

            if angle:
                for word in re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', angle.lower()):
                    if word in e_angle:
                        score += 10
                        break

            if target_audience:
                for word in re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', target_audience.lower()):
                    if word in e_audience:
                        score += 8
                        break

            for term in [product_name.lower(), product_category.lower()]:
                if term:
                    for word in re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', term):
                        if word in e_product or word in e_headline:
                            score += 5
                            break

            for term in search_terms:
                if term in e_headline:
                    score += 3

            if isinstance(e_adv_score, (int, float)) and e_adv_score > 0:
                score += min(e_adv_score / 2, 5)

            has_content = url in content
            if has_content:
                score += 3

            if score > 0:
                scored.append({
                    "url": url,
                    "headline": entry.get("headline", ""),
                    "angle": entry.get("angle", ""),
                    "target_audience": entry.get("target_audience", ""),
                    "product_name": entry.get("product_name", ""),
                    "adv_score": e_adv_score,
                    "word_count": entry.get("word_count", 0),
                    "domain": entry.get("domain", ""),
                    "relevance_score": round(score, 1),
                    "has_content": has_content,
                })

        scored.sort(key=lambda x: (x["has_content"], x["relevance_score"]), reverse=True)

        results = scored[:max_results]
        if len(results) < max_results:
            remaining = max_results - len(results)
            used_urls = {r["url"] for r in results}
            fillers = []
            for url, entry in db.items():
                if url not in used_urls and url in content:
                    fillers.append({
                        "url": url,
                        "headline": entry.get("headline", ""),
                        "angle": entry.get("angle", ""),
                        "target_audience": entry.get("target_audience", ""),
                        "product_name": entry.get("product_name", ""),
                        "adv_score": entry.get("adv_score", 0),
                        "word_count": entry.get("word_count", 0),
                        "domain": entry.get("domain", ""),
                        "relevance_score": 0,
                        "has_content": True,
                    })
            fillers.sort(key=lambda x: x.get("adv_score", 0), reverse=True)
            results.extend(fillers[:remaining])

        return results

    def load_reference_content(self, url: str, max_chars: int = 8000) -> str:
        """Charge le contenu texte d'un advertorial depuis CONTENT_READY."""
        content = self._load_content()
        entry = content.get(url, {})
        if not entry:
            return ""

        text = ""
        if isinstance(entry, dict):
            for key in ["content", "text", "body", "full_text", "html_content"]:
                if entry.get(key):
                    text = entry[key]
                    break
            if text and "<" in text:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(text, "html.parser")
                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()
                parts = []
                for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
                    el_text = el.get_text(strip=True)
                    if el_text:
                        if el.name.startswith("h"):
                            parts.append(f"\n## {el_text}\n")
                        elif el.name == "li":
                            parts.append(f"  - {el_text}")
                        else:
                            parts.append(el_text)
                text = "\n".join(parts)
        elif isinstance(entry, str):
            text = entry

        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[... tronqué]"

        return text

    def get_reference_examples_for_prompt(
        self,
        product_category: str = "",
        product_name: str = "",
        problem_solved: str = "",
        angle: str = "",
        target_audience: str = "",
        max_examples: int = 3,
        max_chars_per_example: int = 6000,
    ) -> str:
        """Retourne un bloc formaté prêt pour le prompt du copywriter."""
        refs = self.find_best_references(
            product_category=product_category,
            product_name=product_name,
            problem_solved=problem_solved,
            angle=angle,
            target_audience=target_audience,
            max_results=max_examples,
        )

        if not refs:
            return "\n(Aucun advertorial de référence disponible)\n"

        parts = []
        examples_with_content = 0

        for i, ref in enumerate(refs, 1):
            content = self.load_reference_content(ref["url"], max_chars=max_chars_per_example)

            header = (
                f"\n### EXEMPLE {i} : {ref['headline']}\n"
                f"Angle: {ref['angle']} | Audience: {ref['target_audience']} | "
                f"Score: {ref['adv_score']} | Pertinence: {ref['relevance_score']}\n"
            )
            parts.append(header)

            if content:
                parts.append(content)
                examples_with_content += 1
            else:
                parts.append(
                    f"(Contenu texte non disponible — métadonnées uniquement)\n"
                    f"Produit: {ref['product_name']} | Mots: {ref['word_count']} | "
                    f"Domaine: {ref['domain']}"
                )
            parts.append("\n---\n")

        logger.info(f"{len(refs)} réfs sélectionnées, {examples_with_content} avec contenu")
        return "\n".join(parts)

    def get_db_stats(self) -> dict:
        """Statistiques sur la base."""
        db = self._load_db()
        content = self._load_content()
        structures = self._load_structures()

        if not db:
            return {"total": 0}

        angles = Counter()
        audiences = Counter()
        scores = []

        for entry in db.values():
            if entry.get("angle"):
                angles[entry["angle"]] += 1
            if entry.get("target_audience"):
                audiences[entry["target_audience"]] += 1
            if isinstance(entry.get("adv_score"), (int, float)):
                scores.append(entry["adv_score"])

        return {
            "total_entries": len(db),
            "with_content": len(content),
            "with_structures": len(structures),
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "top_angles": dict(angles.most_common(10)),
            "top_audiences": dict(audiences.most_common(10)),
        }
