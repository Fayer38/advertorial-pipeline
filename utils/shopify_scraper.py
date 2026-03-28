"""
Utilitaires de scraping spécialisés Shopify.
Deux méthodes complémentaires :
  1. API .json native (données structurées gratuites)
  2. Scraping HTML (FAQ, ingrédients, études, sections custom)
"""

import re
import logging
from urllib.parse import urlparse
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Headers réalistes pour éviter les blocages
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
}


def extract_shopify_handle(url: str) -> str:
    """
    Extrait le handle produit depuis une URL Shopify.
    Ex: https://store.com/products/super-serum → super-serum
    Ex: https://store.com/products/super-serum?variant=123 → super-serum
    """
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")

    # Pattern : /products/handle ou /collections/xxx/products/handle
    match = re.search(r"/products/([^/?#]+)", path)
    if match:
        return match.group(1)

    raise ValueError(f"Impossible d'extraire le handle produit de l'URL: {url}")


def extract_store_domain(url: str) -> str:
    """Extrait le domaine de la boutique."""
    parsed = urlparse(url)
    return parsed.netloc


def build_json_url(url: str) -> str:
    """
    Construit l'URL de l'API JSON native Shopify.
    Ex: https://store.com/products/serum → https://store.com/products/serum.json
    """
    handle = extract_shopify_handle(url)
    domain = extract_store_domain(url)
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    return f"{scheme}://{domain}/products/{handle}.json"


async def fetch_shopify_json(url: str) -> dict:
    """
    Récupère les données produit via l'endpoint .json natif de Shopify.
    Retourne le JSON brut tel que fourni par Shopify.

    Contient : title, body_html, vendor, product_type, tags,
               variants (prix, SKU, stock), images, options, etc.
    """
    json_url = build_json_url(url)
    logger.info(f"Fetching Shopify JSON: {json_url}")

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(json_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 404:
                raise ValueError(
                    f"Produit introuvable (404). Vérifiez l'URL: {url}\n"
                    f"URL JSON testée: {json_url}"
                )
            if resp.status == 403:
                raise PermissionError(
                    f"Accès refusé (403). La boutique bloque peut-être les requêtes: {url}"
                )
            if resp.status != 200:
                raise RuntimeError(f"Erreur HTTP {resp.status} pour {json_url}")

            data = await resp.json()

            # Shopify enveloppe le produit dans {"product": {...}}
            if "product" in data:
                return data["product"]
            return data


async def fetch_page_html(url: str) -> str:
    """
    Récupère le HTML brut de la page produit.
    Utilisé pour extraire les éléments non disponibles via le JSON :
    FAQ, ingrédients, études cliniques, badges, etc.
    """
    logger.info(f"Fetching page HTML: {url}")

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                logger.warning(f"Erreur HTTP {resp.status} pour le HTML de {url}")
                return ""
            return await resp.text()


def parse_html_sections(html: str) -> dict:
    """
    Parse le HTML de la page produit et extrait les sections pertinentes
    qui ne sont pas dans le JSON natif Shopify.

    Retourne un dict avec les sections trouvées.
    """
    soup = BeautifulSoup(html, "html.parser")
    sections = {
        "faq_raw": "",
        "ingredients_raw": "",
        "how_it_works_raw": "",
        "testimonials_raw": "",
        "clinical_studies_raw": "",
        "badges_certifications_raw": "",
        "comparison_raw": "",
        "meta_title": "",
        "meta_description": "",
        "og_image": "",
        "full_text": "",
    }

    # ── Meta SEO ──
    title_tag = soup.find("title")
    if title_tag:
        sections["meta_title"] = title_tag.get_text(strip=True)

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc:
        sections["meta_description"] = meta_desc.get("content", "")

    og_image = soup.find("meta", attrs={"property": "og:image"})
    if og_image:
        sections["og_image"] = og_image.get("content", "")

    # ── FAQ (patterns courants sur Shopify) ──
    faq_content = _extract_faq(soup)
    if faq_content:
        sections["faq_raw"] = faq_content

    # ── Ingrédients / Composition ──
    ingredients = _extract_section_by_keywords(
        soup,
        keywords=["ingredient", "composition", "formul", "actif", "what's inside",
                   "key ingredients", "ingrédient", "active"],
    )
    if ingredients:
        sections["ingredients_raw"] = ingredients

    # ── Comment ça marche ──
    how_it_works = _extract_section_by_keywords(
        soup,
        keywords=["how it works", "comment ça marche", "how to use", "mode d'emploi",
                   "utilisation", "directions"],
    )
    if how_it_works:
        sections["how_it_works_raw"] = how_it_works

    # ── Études cliniques / Preuves ──
    studies = _extract_section_by_keywords(
        soup,
        keywords=["clinical", "study", "studies", "proven", "research", "scientif",
                   "étude", "clinique", "tested", "dermatologist"],
    )
    if studies:
        sections["clinical_studies_raw"] = studies

    # ── Comparatif ──
    comparison = _extract_section_by_keywords(
        soup,
        keywords=["compare", "comparison", "vs", "versus", "alternative", "why choose",
                   "pourquoi choisir", "difference"],
    )
    if comparison:
        sections["comparison_raw"] = comparison

    # ── Texte complet de la page (fallback pour le LLM) ──
    # On nettoie le HTML pour ne garder que le contenu textuel pertinent
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    sections["full_text"] = soup.get_text(separator="\n", strip=True)

    # Limiter la taille du texte complet (Claude a des limites)
    max_chars = 30000
    if len(sections["full_text"]) > max_chars:
        sections["full_text"] = sections["full_text"][:max_chars] + "\n[... tronqué]"

    return sections


def _extract_faq(soup: BeautifulSoup) -> str:
    """Extrait les FAQ — cherche les accordéons et patterns FAQ courants."""
    faq_parts = []

    # Pattern 1 : éléments avec "faq" dans l'id, la classe, ou un data-attribute
    faq_containers = soup.find_all(
        attrs=lambda attrs: attrs and any(
            "faq" in str(v).lower()
            for v in attrs.values()
        )
    )
    for container in faq_containers:
        text = container.get_text(separator="\n", strip=True)
        if len(text) > 20:  # Ignorer les éléments trop courts
            faq_parts.append(text)

    # Pattern 2 : éléments <details>/<summary> (accordéons natifs)
    details = soup.find_all("details")
    for detail in details:
        summary = detail.find("summary")
        if summary:
            q = summary.get_text(strip=True)
            # Le contenu après le summary
            a = detail.get_text(strip=True).replace(q, "", 1).strip()
            if q and a:
                faq_parts.append(f"Q: {q}\nA: {a}")

    # Pattern 3 : Schema.org FAQPage JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            import json
            ld_data = json.loads(script.string)
            if isinstance(ld_data, dict) and ld_data.get("@type") == "FAQPage":
                for item in ld_data.get("mainEntity", []):
                    q = item.get("name", "")
                    a_obj = item.get("acceptedAnswer", {})
                    a = a_obj.get("text", "") if isinstance(a_obj, dict) else ""
                    if q and a:
                        faq_parts.append(f"Q: {q}\nA: {a}")
        except (json.JSONDecodeError, TypeError):
            continue

    return "\n\n".join(faq_parts) if faq_parts else ""


def _extract_section_by_keywords(soup: BeautifulSoup, keywords: list[str]) -> str:
    """
    Cherche des sections dans le HTML dont les titres/id/classes
    correspondent aux mots-clés donnés.
    """
    results = []

    # Chercher dans les headings (h1-h6)
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        heading_text = heading.get_text(strip=True).lower()
        if any(kw in heading_text for kw in keywords):
            # Récupérer le contenu suivant le heading
            content_parts = [heading.get_text(strip=True)]
            for sibling in heading.find_next_siblings():
                # S'arrêter au prochain heading de même niveau ou supérieur
                if sibling.name and sibling.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    break
                text = sibling.get_text(strip=True)
                if text:
                    content_parts.append(text)
            if len(content_parts) > 1:
                results.append("\n".join(content_parts))

    # Chercher dans les sections/divs par classe ou id
    for el in soup.find_all(["section", "div"]):
        el_id = (el.get("id") or "").lower()
        el_classes = " ".join(el.get("class", [])).lower()
        el_attrs = f"{el_id} {el_classes}"

        if any(kw in el_attrs for kw in keywords):
            text = el.get_text(separator="\n", strip=True)
            if len(text) > 30 and text not in results:
                results.append(text)

    return "\n\n---\n\n".join(results) if results else ""
