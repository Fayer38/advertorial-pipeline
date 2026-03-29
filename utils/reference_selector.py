"""
Sélecteur d'advertoriaux de référence v2 — scoring sémantique + diversité.

Sources :
1. ADVERTORIAL_DB.json — 417 entrées avec métadonnées
2. ADVERTORIAL_CONTENT_READY.json — 205 advertoriaux avec contenu texte
3. ADVERTORIAL_STRUCTURES.json — analyses structurées

Améliorations v2 :
- Brief-aware: utilise le brief additionnel pour la sélection
- Scoring sémantique: TF-IDF-like sur les n-grams, pas juste des mots exacts
- Diversité: ne sélectionne pas 3 refs du même angle/produit
- Quality gate: filtre les refs avec contenu trop court ou score trop bas
- Smart extraction: extrait les meilleurs passages (hook, CTA, transitions)
"""

import re
import json
import logging
import math
from pathlib import Path
from typing import Optional
from collections import Counter

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "/root/.openclaw/workspace-anstrex-scraper/ADVERTORIAL_DB.json"
DEFAULT_CONTENT_PATH = "/root/.openclaw/workspace-anstrex-scraper/ADVERTORIAL_CONTENT_READY.json"
DEFAULT_STRUCTURES_PATH = "/root/.openclaw/workspace-anstrex-scraper/ADVERTORIAL_STRUCTURES.json"

# Stop words to ignore in matching
STOP_WORDS = {
    "the", "and", "for", "that", "this", "with", "from", "your", "are", "was",
    "has", "have", "will", "can", "but", "not", "all", "she", "her", "his",
    "they", "them", "been", "being", "about", "more", "than", "just", "also",
    "into", "over", "after", "before", "only", "very", "most", "some", "such",
    "what", "when", "where", "which", "while", "who", "how", "out", "its",
    "you", "our", "their", "would", "could", "should", "does", "did", "had",
    "one", "two", "three", "first", "new", "way", "may", "use", "each",
}


def _tokenize(text: str) -> list[str]:
    """Extract meaningful words from text, excluding stop words."""
    words = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', text.lower())
    return [w for w in words if w not in STOP_WORDS]


def _bigrams(tokens: list[str]) -> list[str]:
    """Generate bigrams from token list."""
    return [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens)-1)]


def _compute_similarity(query_tokens: list[str], target_tokens: list[str]) -> float:
    """TF-IDF-like similarity between two token sets."""
    if not query_tokens or not target_tokens:
        return 0.0
    query_set = set(query_tokens)
    target_set = set(target_tokens)
    # Include bigrams for phrase matching
    query_bi = set(_bigrams(query_tokens))
    target_bi = set(_bigrams(target_tokens))
    
    word_overlap = len(query_set & target_set)
    bigram_overlap = len(query_bi & target_bi)
    
    # Normalize by query size
    word_score = word_overlap / max(len(query_set), 1)
    bigram_score = bigram_overlap / max(len(query_bi), 1) * 1.5  # Bigrams weighted more
    
    return word_score + bigram_score


class ReferenceSelector:

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
        if self._structures is not None:
            return self._structures
        if not self.structures_path.exists():
            self._structures = {}
            return self._structures
        with open(self.structures_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._structures = data if isinstance(data, dict) else {}
        return self._structures

    def find_best_references(
        self,
        product_category: str = "",
        product_name: str = "",
        problem_solved: str = "",
        angle: str = "",
        target_audience: str = "",
        additional_brief: str = "",
        max_results: int = 5,
    ) -> list[dict]:
        """
        Scoring amélioré v2 :
        1. Semantic similarity (angle + headline + audience)
        2. Brief-aware matching (if additional_brief provided)
        3. Content quality bonus
        4. Diversity penalty (don't pick 3 of the same thing)
        """
        db = self._load_db()
        content = self._load_content()

        if not db:
            return []

        # Build query tokens from all inputs
        query_parts = [product_category, product_name, problem_solved, angle, target_audience]
        query_tokens = []
        for part in query_parts:
            if part:
                query_tokens.extend(_tokenize(part))

        # Brief tokens (weighted separately, higher importance)
        brief_tokens = _tokenize(additional_brief) if additional_brief else []

        scored = []

        for url, entry in db.items():
            score = 0.0

            e_angle = entry.get("angle") or ""
            e_audience = entry.get("target_audience") or ""
            e_headline = entry.get("headline") or ""
            e_product = entry.get("product_name") or ""
            e_adv_score = entry.get("adv_score", 0) or 0
            e_word_count = entry.get("word_count", 0) or 0

            # Combine all target text
            target_text = f"{e_angle} {e_headline} {e_audience} {e_product}"
            target_tokens = _tokenize(target_text)

            # 1. Semantic similarity with query (0-2 range)
            sim = _compute_similarity(query_tokens, target_tokens)
            score += sim * 15  # Scale to ~0-15

            # 2. Brief-aware matching (if brief provided, this is HIGH weight)
            if brief_tokens:
                brief_sim = _compute_similarity(brief_tokens, target_tokens)
                score += brief_sim * 20  # Brief match is most important

                # Also check content text for brief keywords (deeper match)
                has_content = url in content
                if has_content:
                    content_entry = content[url]
                    content_text = ""
                    if isinstance(content_entry, dict):
                        for k in ["content", "text", "body", "full_text", "html_content"]:
                            if content_entry.get(k):
                                content_text = content_entry[k]
                                break
                    elif isinstance(content_entry, str):
                        content_text = content_entry
                    
                    if content_text:
                        content_tokens = _tokenize(content_text[:3000])  # First 3000 chars
                        content_brief_sim = _compute_similarity(brief_tokens, content_tokens)
                        score += content_brief_sim * 10  # Content-brief match

            # 3. Quality score bonus
            if isinstance(e_adv_score, (int, float)) and e_adv_score > 0:
                score += min(e_adv_score, 8)  # Up to +8

            # 4. Content availability (strong bonus — we need the text)
            has_content = url in content
            if has_content:
                score += 8
            else:
                score -= 5  # Penalize entries without content

            # 5. Word count sweet spot (1000-3000 is ideal for references)
            if e_word_count:
                if 1000 <= e_word_count <= 3000:
                    score += 3
                elif 500 <= e_word_count <= 5000:
                    score += 1
                # Very short or very long = less useful as reference

            # 6. Specific angle matching patterns
            angle_lower = angle.lower() if angle else ""
            e_angle_lower = e_angle.lower()
            
            # Check for structural angle matches (testimonial, founder story, liquidation, etc.)
            angle_keywords = {
                "testimonial": ["testimonial", "review", "story", "experience", "journey"],
                "founder": ["founder", "creator", "inventor", "built", "started", "company"],
                "liquidation": ["liquidation", "clearance", "closing", "sell off", "inventory", "discount", "% off"],
                "urgency": ["limited", "last chance", "running out", "hurry", "deadline", "expire"],
                "health": ["doctor", "surgeon", "medical", "health", "pain", "relief", "clinical"],
                "comparison": ["vs", "versus", "compared", "alternative", "better than", "unlike"],
                "emotional": ["emotional", "heartbreak", "tears", "touching", "moving", "tragic"],
            }
            
            for angle_type, keywords in angle_keywords.items():
                if angle_type in angle_lower or any(kw in angle_lower for kw in keywords):
                    if any(kw in e_angle_lower or kw in e_headline.lower() for kw in keywords):
                        score += 8  # Strong angle type match

            if score > 0:
                scored.append({
                    "url": url,
                    "headline": e_headline,
                    "angle": e_angle,
                    "target_audience": e_audience,
                    "product_name": e_product,
                    "adv_score": e_adv_score,
                    "word_count": e_word_count,
                    "domain": entry.get("domain", ""),
                    "relevance_score": round(score, 1),
                    "has_content": has_content,
                })

        scored.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Diversity selection: don't pick refs with the same product/domain
        selected = []
        seen_domains = set()
        seen_products = set()
        
        for ref in scored:
            if len(selected) >= max_results:
                break
            
            domain = ref.get("domain", "").lower()
            product = ref.get("product_name", "").lower()[:20]
            
            # Allow first ref always, then enforce diversity
            if len(selected) > 0:
                if domain and domain in seen_domains:
                    # Same domain — apply penalty, still allow if score is much higher
                    if ref["relevance_score"] < selected[-1]["relevance_score"] * 0.7:
                        continue
                if product and product in seen_products:
                    if ref["relevance_score"] < selected[-1]["relevance_score"] * 0.7:
                        continue
            
            selected.append(ref)
            if domain:
                seen_domains.add(domain)
            if product:
                seen_products.add(product)

        # If we don't have enough, fill with highest-scored content entries
        if len(selected) < max_results:
            remaining = max_results - len(selected)
            used_urls = {r["url"] for r in selected}
            fillers = []
            for url, entry in db.items():
                if url not in used_urls and url in content:
                    e_adv_score = entry.get("adv_score", 0) or 0
                    fillers.append({
                        "url": url,
                        "headline": entry.get("headline", ""),
                        "angle": entry.get("angle", ""),
                        "target_audience": entry.get("target_audience", ""),
                        "product_name": entry.get("product_name", ""),
                        "adv_score": e_adv_score,
                        "word_count": entry.get("word_count", 0),
                        "domain": entry.get("domain", ""),
                        "relevance_score": 0,
                        "has_content": True,
                    })
            fillers.sort(key=lambda x: x.get("adv_score", 0) or 0, reverse=True)
            selected.extend(fillers[:remaining])

        return selected

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
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(text, "html.parser")
                    for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
                        tag.decompose()
                    parts = []
                    for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "blockquote"]):
                        el_text = el.get_text(strip=True)
                        if el_text and len(el_text) > 20:  # Skip tiny fragments
                            if el.name.startswith("h"):
                                parts.append(f"\n## {el_text}\n")
                            elif el.name == "li":
                                parts.append(f"  - {el_text}")
                            elif el.name == "blockquote":
                                parts.append(f'> "{el_text}"')
                            else:
                                parts.append(el_text)
                    text = "\n".join(parts)
                except ImportError:
                    # No BeautifulSoup — strip tags manually
                    text = re.sub(r'<[^>]+>', ' ', text)
                    text = re.sub(r'\s+', ' ', text).strip()
        elif isinstance(entry, str):
            text = entry

        # Smart truncation: try to cut at a paragraph boundary
        if len(text) > max_chars:
            # Find last paragraph break before limit
            cutoff = text[:max_chars].rfind('\n\n')
            if cutoff > max_chars * 0.6:
                text = text[:cutoff] + "\n\n[... suite tronquée]"
            else:
                cutoff = text[:max_chars].rfind('\n')
                if cutoff > max_chars * 0.8:
                    text = text[:cutoff] + "\n\n[... suite tronquée]"
                else:
                    text = text[:max_chars] + "\n\n[... tronqué]"

        return text

    def _extract_key_passages(self, text: str, max_chars: int = 4000) -> str:
        """Extract the most valuable passages: hook, transitions, CTA, emotional peaks."""
        if not text or len(text) < 200:
            return text
        
        lines = text.split('\n')
        scored_lines = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped or len(line_stripped) < 15:
                continue
            
            line_score = 0
            line_lower = line_stripped.lower()
            
            # Headers are always important
            if line_stripped.startswith('##'):
                line_score += 5
            
            # First 5 lines (hook/opening)
            if i < 5:
                line_score += 4
            
            # CTA / offer indicators
            cta_words = ["order", "buy", "check availability", "limited", "discount", "% off", "free shipping", "guarantee", "try it", "get yours"]
            if any(w in line_lower for w in cta_words):
                line_score += 3
            
            # Emotional language
            emotion_words = ["finally", "changed", "never again", "transformed", "miracle", "couldn't believe", "tears", "relieved", "desperate", "frustrated", "amazed"]
            if any(w in line_lower for w in emotion_words):
                line_score += 3
            
            # Testimonial / quote indicators
            if '"' in line_stripped or line_stripped.startswith('>') or "said" in line_lower or "told" in line_lower:
                line_score += 2
            
            # Data / proof points
            if re.search(r'\d+%|\$\d+|\d+\s*(lbs?|kg|mph|hours?|minutes?|days?)', line_lower):
                line_score += 2
            
            # Transition words (structural)
            transitions = ["but here's", "that's when", "turns out", "the truth is", "what happened next", "here's why"]
            if any(t in line_lower for t in transitions):
                line_score += 3
            
            if line_score > 0:
                scored_lines.append((line_score, line_stripped))
        
        # Sort by score but keep some order
        # Take top passages up to max_chars
        scored_lines.sort(key=lambda x: x[0], reverse=True)
        
        result_parts = []
        total_chars = 0
        for score, line in scored_lines:
            if total_chars + len(line) > max_chars:
                break
            result_parts.append(line)
            total_chars += len(line) + 1
        
        return "\n".join(result_parts)

    def get_reference_examples_for_prompt(
        self,
        product_category: str = "",
        product_name: str = "",
        problem_solved: str = "",
        angle: str = "",
        target_audience: str = "",
        additional_brief: str = "",
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
            additional_brief=additional_brief,
            max_results=max_examples * 2,  # Get more, then filter for content
        )

        if not refs:
            return "\n(Aucun advertorial de référence disponible)\n"

        parts = []
        examples_with_content = 0
        used = 0

        for ref in refs:
            if used >= max_examples:
                break

            content = self.load_reference_content(ref["url"], max_chars=max_chars_per_example)
            
            # Skip refs without meaningful content (unless we have no alternatives)
            if not content or len(content) < 200:
                if examples_with_content > 0 or used > 0:
                    continue

            used += 1
            header = (
                f"\n### EXEMPLE {used} : {ref['headline']}\n"
                f"Angle: {ref['angle'][:100]}{'...' if len(ref['angle']) > 100 else ''}\n"
                f"Audience: {ref['target_audience']} | Score: {ref['adv_score']} | "
                f"Pertinence: {ref['relevance_score']}\n"
            )
            parts.append(header)

            if content and len(content) > 200:
                # Use smart extraction for long content
                if len(content) > max_chars_per_example:
                    key_passages = self._extract_key_passages(content, max_chars=max_chars_per_example)
                    parts.append(key_passages)
                else:
                    parts.append(content)
                examples_with_content += 1
            else:
                parts.append(
                    f"(Contenu texte non disponible — métadonnées uniquement)\n"
                    f"Produit: {ref['product_name']} | Mots: {ref['word_count']} | "
                    f"Domaine: {ref['domain']}"
                )
            parts.append("\n---\n")

        # Add instruction on how to use references
        intro = f"""# ADVERTORIAUX DE RÉFÉRENCE ({used} exemples sélectionnés sur 417)

Ces exemples ont été sélectionnés pour leur PERTINENCE avec ton brief.
Utilise-les pour le STYLE, le RYTHME et les TECHNIQUES d'écriture :
- Comment ils ouvrent (hook)
- Comment ils construisent la tension
- Comment ils intègrent les preuves/témoignages
- Comment ils transitionnent vers l'offre

⚠️ NE COPIE PAS leur contenu — inspire-toi de leur CRAFT.
Si un brief additionnel est fourni, le CONTENU vient du brief, le STYLE vient des exemples.

"""
        return intro + "\n".join(parts)

    def get_db_stats(self) -> dict:
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
                angles[entry["angle"][:50]] += 1
            if entry.get("target_audience"):
                audiences[entry["target_audience"][:50]] += 1
            if isinstance(entry.get("adv_score"), (int, float)) and entry.get("adv_score"):
                scores.append(entry["adv_score"])
        return {
            "total_entries": len(db),
            "with_content": len(content),
            "with_structures": len(structures),
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "top_angles": dict(angles.most_common(10)),
            "top_audiences": dict(audiences.most_common(10)),
        }
