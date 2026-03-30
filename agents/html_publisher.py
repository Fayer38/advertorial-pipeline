"""
Agent 10 : HTML Publisher (remplace l'assembleur GemPage)
==========================================================
Input  : advertorial_draft.json + image_prompts.json (optionnel)
Output : fichier HTML complet déposé dans le dossier Nginx

Template validé : Roboto 18px, Montserrat ExtraBold, #111/#fff/#f26722,
sidebar sticky, offer box, sticky footer, responsive.
"""

import json
import re
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

DEFAULT_PUBLISH_DIR = "/var/www/advertorials"


class HTMLPublisherAgent(BaseAgent):

    def __init__(self, output_dir: str = "data/output", publish_dir: str = DEFAULT_PUBLISH_DIR):
        super().__init__(name="html_publisher", output_dir=output_dir)
        self.publish_dir = Path(publish_dir)

    async def run(
        self,
        advertorial_draft: dict,
        image_prompts: Optional[dict] = None,
        video_prompts: Optional[dict] = None,
        product_url: str = "",
        product_name: str = "",
        product_image_url: str = "",
        author_name: str = "",
        slug: str = "",
        lang: str = "en",
        template: str = "editorial",
    ) -> dict:
        self.log_start()

        content = advertorial_draft.get("content", {})
        seo = advertorial_draft.get("seo", {})
        if not product_name:
            # Try to get actual product name from draft metadata, NOT the headline
            product_name = (
                advertorial_draft.get("product_name", "") or
                advertorial_draft.get("metadata", {}).get("product_name", "") or
                advertorial_draft.get("_config", {}).get("product_name", "") or
                content.get("product_name", "") or
                "Seese Pro™"
            )
        if not author_name:
            author_name = "Editorial Team"
        if not slug:
            slug = re.sub(r'[^a-z0-9]+', '-', content.get("headline", "article").lower())[:60].strip('-')

        image_map = {}
        if image_prompts:
            for p in image_prompts.get("prompts", []):
                url = p.get("generated_image_url", "")
                if url:
                    image_map[p.get("scene_index", -1)] = url

        html = self._build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang=lang, template=template)

        # Inject testimonial avatars
        html = self._inject_avatars(html)
        # Inject branding elements (logo header, announcement bar, footer)
        html = self._inject_branding(html, product_name, product_url)

        output_path = self.output_dir / f"{slug}.html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        publish_path = None
        if self.publish_dir.exists():
            publish_path = self.publish_dir / f"{slug}.html"
            shutil.copy2(output_path, publish_path)
            self.logger.info(f"Publié : {publish_path}")

        self.log_done(f"{slug}.html")

        return {
            "html_file": str(output_path),
            "published_path": str(publish_path) if publish_path else None,
            "slug": slug,
            "url": f"/articles/{slug}" if publish_path else None,
            "word_count": advertorial_draft.get("meta", {}).get("word_count", 0),
        }

    def _inject_avatars(self, html: str) -> str:
        """Inject realistic avatar images into testimonial attribution divs."""
        import hashlib

        male_names = ["Robert","James","David","Michael","John","William","Richard","Thomas","Charles","Joseph",
                       "George","Edward","Albert","Frank","Harold","Walter","Raymond","Lawrence","Eugene","Ralph",
                       "Carl","Arthur","Fred","Henry","Ernest","Roy","Louis","Donald","Kenneth","Paul","Jerry",
                       "Dennis","Gerald","Bruce","Roger","Wayne","Dale","Gary","Larry","Terry","Bobby","Jim","Bob"]
        female_names = ["Margaret","Patricia","Linda","Barbara","Elizabeth","Jennifer","Maria","Susan","Dorothy",
                         "Lisa","Nancy","Karen","Betty","Helen","Sandra","Ashley","Kimberly","Emily","Donna",
                         "Michelle","Carol","Amanda","Melissa","Deborah","Stephanie","Rebecca","Sharon","Laura",
                         "Cynthia","Kathleen","Amy","Angela","Shirley","Anna","Brenda","Pamela","Janet","Mary","Sarah"]

        def add_avatar(m):
            attribution = m.group(1)
            seed = hashlib.md5(attribution.encode()).hexdigest()[:8]
            gender = "men" if any(n in attribution for n in male_names) else "women"
            num = int(seed, 16) % 99
            avatar_url = f"https://randomuser.me/api/portraits/{gender}/{num}.jpg"
            avatar_html = f'<img src="{avatar_url}" style="width:44px;height:44px;border-radius:50%;object-fit:cover;flex-shrink:0;margin-right:10px">'
            return f'<div class="attribution" style="display:flex;align-items:center">{avatar_html}<span>{attribution}</span></div>'

        html = re.sub(r'<div class="attribution">(.*?)</div>', add_avatar, html, flags=re.DOTALL)
        return html

    def _inject_branding(self, html: str, product_name: str = "", product_url: str = "") -> str:
        """Inject logo header, announcement bar, and footer into any template HTML."""
        LOGO_URL = "https://cdn.shopify.com/s/files/1/0600/8527/2619/files/Design_sans_titre_15.png?v=1774625309"
        
        # Standard header: Disclaimer + Logo ONLY (no announcement bar)
        header = f'''<div id="adv-disclosure" style="text-align:center;padding:3px 0;background:#fafafa;border-bottom:1px solid #f0f0f0;font-size:9px;color:#c0c0c0;letter-spacing:0.03em;font-family:system-ui,sans-serif;">Advertorial</div>
<div id="adv-header-logo" style="text-align:center;padding:14px 0 10px;background:#fff;border-bottom:1px solid #eee;">
  <a href="{product_url}" style="text-decoration:none;"><img src="{LOGO_URL}" alt="{product_name}" style="height:52px;max-width:260px;object-fit:contain;"></a>
</div>'''
        
        # Footer
        footer = f'''<footer id="adv-footer" style="background:#f5f5f5;border-top:1px solid #e5e5e5;padding:30px 20px;text-align:center;margin-top:40px;">
  <img src="{LOGO_URL}" alt="Logo" style="height:36px;max-width:180px;object-fit:contain;margin-bottom:12px;opacity:0.7;">
  <p style="font-size:10px;color:#999;line-height:1.6;max-width:700px;margin:0 auto;">&copy; 2026 All rights reserved. All content, images, and materials on this website are protected by international copyright and intellectual property laws. Unauthorized reproduction, distribution, or modification of any materials is strictly prohibited.</p>
</footer>'''
        
        # Inject disclaimer + logo after <body>
        if "adv-disclosure" not in html:
            body_match = re.search(r'(<body[^>]*>)', html, re.IGNORECASE)
            if body_match:
                pos = body_match.end()
                html = html[:pos] + "\n" + header + "\n" + html[pos:]
        
        # Inject footer before </body>
        if "adv-footer" not in html:
            if "</body>" in html:
                html = html.replace("</body>", footer + "\n</body>")
            else:
                html += "\n" + footer
        
        return html

    def _build_html(self, content, seo, image_map, product_url, product_name, product_image_url, author_name, lang="en", template="editorial"):
        today = datetime.utcnow().strftime("%B %d, %Y")
        headline = content.get("headline", "")
        subheadline = content.get("subheadline", "")

        body_parts = []
        offer_section = None
        cta_section = None

        for i, sec in enumerate(content.get("sections", [])):
            s_type = sec.get("type", "")
            if s_type == "offer":
                offer_section = sec
                continue
            if s_type == "cta":
                cta_section = sec
                continue

            heading = sec.get("heading", "")
            body_html = sec.get("body_html", "")
            placeholder = sec.get("visual_placeholder", {})
            img_url = image_map.get(i, "")
            parts = []

            if img_url:
                parts.append(f'<img src="{img_url}" alt="{heading}" style="width:100%;border-radius:8px;margin:10px 0 14px;">')
            elif placeholder.get("description"):
                p_type = placeholder.get("type", "product").upper().replace("_", " / ")
                parts.append(f'<div class="placeholder"><div class="tbadge">{p_type}</div><br>{placeholder["description"]}</div>')

            if heading:
                parts.append(f"<h2>{heading}</h2>")
            if body_html:
                parts.append(body_html)
            if parts:
                body_parts.append("\n".join(parts))

        article_body = "\n\n".join(body_parts)
        cta_body = cta_section.get("body_html", "") if cta_section else ""

        # Translations for static template text
        i18n = {
            "en": {
                "offer_title": '⚠️ Special Offer: <span class="accent">50% Off</span> — Limited Stock',
                "offer_desc": 'Available <strong>ONLY</strong> on the official store — at the lowest price of the year.',
                "step1_title": "✅ Step 1", "step1": "Order yours today to lock in the exclusive discount — only while supplies last.",
                "step2_title": "✅ Step 2", "step2": "When it arrives (2-5 business days), unbox it and start using it immediately. No setup needed.",
                "step3_title": "✅ Step 3", "step3": "Make it part of your routine. See the difference in minutes — <strong>without any effort</strong>.",
                "tip": '<strong>Useful tip:</strong><br>Know someone who would love this? It makes an incredible gift — the kind that gets used every week.',
                "gift": '<strong>Gift idea:</strong> Get the bundle and save even more. Perfect for birthdays, holidays, or just treating yourself.',
                "cta": "Check Availability", "cta_footer": "👉 Skip to offer — Check availability",
                "badge1": "30-day money-back guarantee", "badge2": "Free shipping (2–5 days)", "badge3": "10-year lifetime warranty", "badge4": "Ships in 2-5 business days",
                "byline_by": "By", "product_img_alt": "Product image", "bundle_badge": "PRODUCT BUNDLE", "bundle_desc": "Product hero image with all accessories and price badge", "sb_hook": "Limited offer — order now",
            },
            "fr": {
                "offer_title": '⚠️ Offre Spéciale : <span class="accent">-50%</span> — Stock Limité',
                "offer_desc": 'Disponible <strong>UNIQUEMENT</strong> sur le site officiel — au prix le plus bas de l\'année.',
                "step1_title": "✅ Étape 1", "step1": "Commandez aujourd'hui pour bénéficier de la réduction exclusive — jusqu'à épuisement des stocks.",
                "step2_title": "✅ Étape 2", "step2": "Dès réception (2-5 jours ouvrés), déballez et utilisez immédiatement. Aucune installation nécessaire.",
                "step3_title": "✅ Étape 3", "step3": "Intégrez-le à votre routine. Voyez la différence en quelques minutes — <strong>sans aucun effort</strong>.",
                "tip": '<strong>Astuce :</strong><br>Vous connaissez quelqu\'un qui adorerait ? C\'est le cadeau idéal — celui qu\'on utilise chaque semaine.',
                "gift": '<strong>Idée cadeau :</strong> Prenez le pack et économisez encore plus. Parfait pour un anniversaire ou se faire plaisir.',
                "cta": "Vérifier la Disponibilité", "cta_footer": "👉 Voir l'offre — Vérifier la disponibilité",
                "badge1": "Satisfait ou remboursé 30 jours", "badge2": "Livraison gratuite (2-5 jours)", "badge3": "Garantie 10 ans", "badge4": "Expédition sous 2-5 jours",
                "byline_by": "Par", "product_img_alt": "Image produit", "bundle_badge": "PACK PRODUIT", "bundle_desc": "Image du pack complet avec tous les accessoires et prix remisé", "sb_hook": "Offre limitée — commandez maintenant",
            },
            "es": {
                "offer_title": '⚠️ Oferta Especial: <span class="accent">-50%</span> — Stock Limitado',
                "offer_desc": 'Disponible <strong>SOLO</strong> en la tienda oficial — al precio más bajo del año.',
                "step1_title": "✅ Paso 1", "step1": "Pide el tuyo hoy para asegurar el descuento exclusivo — hasta agotar existencias.",
                "step2_title": "✅ Paso 2", "step2": "Cuando llegue (2-5 días hábiles), ábrelo y úsalo de inmediato. Sin instalación.",
                "step3_title": "✅ Paso 3", "step3": "Hazlo parte de tu rutina. Nota la diferencia en minutos — <strong>sin ningún esfuerzo</strong>.",
                "tip": '<strong>Consejo:</strong><br>¿Conoces a alguien que lo adoraría? Es el regalo perfecto — de los que se usan cada semana.',
                "gift": '<strong>Idea de regalo:</strong> Llévate el pack y ahorra aún más.',
                "cta": "Ver Disponibilidad", "cta_footer": "👉 Ir a la oferta — Ver disponibilidad",
                "badge1": "Garantía de devolución 30 días", "badge2": "Envío gratuito (2-5 días)", "badge3": "Garantía de 10 años", "badge4": "Envío en 2-5 días",
                "byline_by": "Por", "product_img_alt": "Imagen del producto", "bundle_badge": "PACK PRODUCTO", "bundle_desc": "Imagen del pack completo con accesorios y precio con descuento", "sb_hook": "Oferta limitada — pide ahora",
            },
            "de": {
                "offer_title": '⚠️ Sonderangebot: <span class="accent">-50%</span> — Begrenzter Vorrat',
                "offer_desc": '<strong>NUR</strong> im offiziellen Shop erhältlich — zum niedrigsten Preis des Jahres.',
                "step1_title": "✅ Schritt 1", "step1": "Bestellen Sie noch heute und sichern Sie sich den exklusiven Rabatt — solange der Vorrat reicht.",
                "step2_title": "✅ Schritt 2", "step2": "Nach Erhalt (2-5 Werktage) sofort auspacken und loslegen. Keine Installation nötig.",
                "step3_title": "✅ Schritt 3", "step3": "Machen Sie es zu Ihrer Routine. Sehen Sie den Unterschied in Minuten — <strong>ohne Aufwand</strong>.",
                "tip": '<strong>Tipp:</strong><br>Kennen Sie jemanden, der das lieben würde? Ein perfektes Geschenk — eins, das jede Woche benutzt wird.',
                "gift": '<strong>Geschenkidee:</strong> Holen Sie sich das Bundle und sparen Sie noch mehr.',
                "cta": "Verfügbarkeit prüfen", "cta_footer": "👉 Zum Angebot — Verfügbarkeit prüfen",
                "badge1": "30 Tage Geld-zurück-Garantie", "badge2": "Kostenloser Versand (2-5 Tage)", "badge3": "10-Jahres-Garantie", "badge4": "Versand in 2-5 Tagen",
                "byline_by": "Von", "product_img_alt": "Produktbild", "bundle_badge": "PRODUKT-BUNDLE", "bundle_desc": "Produktbild mit allem Zubehör und Rabattpreis", "sb_hook": "Begrenztes Angebot — jetzt bestellen",
            },
        }
        tx = i18n.get(lang, i18n["en"])

        # Dispatch to alternative templates
        # Dispatch to template modules
        _template_modules = {
            "health-journal": "agents.templates.health_journal",
            "listicle": "agents.templates.listicle",
            "news-report": "agents.templates.news_report",
            "founder-letter": "agents.templates.founder_letter",
            "personal-story": "agents.templates.personal_story",
            "medical-authority": "agents.templates.medical_authority",
            "urgency-sale": "agents.templates.urgency_sale",
        }
        if template in _template_modules:
            import importlib
            mod = importlib.import_module(_template_modules[template])
            return mod.build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang, tx)

        # Custom imported template — use editorial renderer with custom structural guidance
        # The copywriter already received custom instructions via get_template_instructions()
        # so the content structure matches the imported template's pattern
        if template.startswith("custom-"):
            pass  # fall through to editorial renderer below

        # Default: editorial template (v2 — enhanced with stat-row, comparison table, testimonials, warning boxes, SVG icons)
        SVG_CHECK = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#f26722" stroke-width="2"/><path d="M9 12l2 2 4-4" stroke="#f26722" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        SVG_CHECK_GREEN = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#2eaa4f" stroke-width="2"/><path d="M9 12l2 2 4-4" stroke="#2eaa4f" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        SVG_TIP = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#f26722" stroke-width="2"/><line x1="12" y1="8" x2="12" y2="12" stroke="#f26722" stroke-width="2" stroke-linecap="round"/><line x1="12" y1="16" x2="12.01" y2="16" stroke="#f26722" stroke-width="2" stroke-linecap="round"/></svg>'

        offer_box = f'''<div class="offer-box">
      <h2>{tx["offer_title"]}</h2>
      <p><strong>{product_name}</strong><br>{tx["offer_desc"]}</p>
      <div class="offer-product">
        {'<img src="' + product_image_url + '" alt="' + product_name + '" style="width:100%;border-radius:8px;margin:8px 0 16px;">' if product_image_url else '<div class="placeholder"><div class="tbadge">' + tx.get("bundle_badge","PRODUCT BUNDLE") + '</div><br>' + tx.get("bundle_desc","Product hero image with all accessories and price badge") + '</div>'}
      </div>
      <div class="step">{SVG_CHECK} <div><div class="step-title">{tx["step1_title"]}</div><p>{tx["step1"]}</p></div></div>
      <div class="step">{SVG_CHECK} <div><div class="step-title">{tx["step2_title"]}</div><p>{tx["step2"]}</p></div></div>
      <div class="step">{SVG_CHECK} <div><div class="step-title">{tx["step3_title"]}</div><p>{tx["step3"]}</p></div></div>
      <div class="tip">{SVG_TIP} <div>{tx["tip"]}</div></div>
      <div class="tip">{SVG_TIP} <div>{tx["gift"]}</div></div>
      {cta_body}
      <a href="{product_url}" class="cta-bottom">{tx["cta"]}</a>
      <div class="cta-badges">
        <div>{SVG_CHECK_GREEN} {tx["badge1"]}</div>
        <div>{SVG_CHECK_GREEN} {tx["badge2"]}</div>
        <div>{SVG_CHECK_GREEN} {tx.get("badge3", "")}</div>
        <div>{SVG_CHECK_GREEN} {tx.get("badge4", "")}</div>
      </div>
    </div>'''

        product_price = product_image_url and "$119.99" or ""
        product_price_old = product_image_url and "$249.99" or ""

        return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<title>{seo.get("meta_title", headline)}</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{seo.get("meta_description", "")}">
<meta name="robots" content="noindex, nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@800&family=Roboto:wght@400;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Roboto',sans-serif;color:#111;background:#fff;font-size:18px;line-height:1.7;padding-bottom:56px}}
.page-wrapper{{max-width:1100px;margin:0 auto;padding:24px 20px;display:flex;gap:32px;align-items:flex-start}}
.article-content{{flex:1;min-width:0}}
.sidebar{{width:300px;flex-shrink:0;position:sticky;top:20px}}
.sidebar-card{{border:1px solid #e5e5e5;border-radius:10px;overflow:hidden;background:#fff;box-shadow:0 2px 12px rgba(0,0,0,0.06)}}
.sidebar-card .sb-title{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:17px;text-align:center;padding:14px 16px 10px;color:#111;line-height:1.3}}
.sidebar-card .sb-img{{width:100%;height:200px;background:#f0f0f0;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:13px;font-style:italic;text-align:center;padding:16px}}
.sidebar-card .sb-price{{text-align:center;padding:8px 16px 0;font-size:14px;color:#666}}
.sidebar-card .sb-price strong{{font-size:22px;color:#111}}
.sidebar-card .sb-rating{{text-align:center;padding:8px 16px 4px;font-size:13px;color:#f26722;letter-spacing:1px}}
.sidebar-card .sb-cta{{display:block;margin:12px 16px;padding:14px;background:#f26722;color:#111;text-align:center;font-size:16px;font-weight:700;border-radius:8px;text-decoration:none;transition:background .2s}}
.sidebar-card .sb-cta:hover{{background:#d85a1b}}
.sidebar-card .sb-badges{{padding:0 16px 14px;font-size:13px;color:#555}}
.sidebar-card .sb-badges div{{margin-bottom:6px;display:flex;align-items:center;gap:6px}}
.chk{{color:#2eaa4f;margin-right:4px}}
.byline{{font-size:14px;color:#888;margin-bottom:14px;border-bottom:1px solid #eee;padding-bottom:12px}}
h1{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:32px;line-height:1.2;margin-bottom:14px;color:#111}}
h2{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:24px;line-height:1.25;margin-top:28px;margin-bottom:12px;color:#111}}
p{{font-size:18px;line-height:1.7;margin-bottom:12px;color:#222}}
p:last-child{{margin-bottom:0}}
strong{{color:#111}}
em{{color:#444;font-style:italic}}
.accent{{color:#f26722}}
.placeholder{{background:#f7f7f7;padding:36px 20px;text-align:center;color:#aaa;border-radius:8px;margin:12px 0;font-style:italic;font-size:14px;border:1px dashed #ddd;line-height:1.6}}
.placeholder .tbadge{{display:inline-block;background:#f26722;color:#fff;font-size:10px;padding:3px 10px;border-radius:10px;margin-bottom:10px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700}}
.stat-row{{display:flex;gap:14px;margin:16px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:130px;background:#fff5f0;border:1px solid #f9cdb8;border-radius:8px;padding:14px;text-align:center}}
.stat-box .stat-num{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:26px;color:#f26722;display:block}}
.stat-box .stat-label{{font-size:13px;color:#666;margin-top:4px;line-height:1.4}}
.comparison-table{{width:100%;border-collapse:collapse;margin:14px 0;font-size:15px;display:block;overflow-x:auto;-webkit-overflow-scrolling:touch}}
.comparison-table th{{background:#f7f7f7;padding:11px 14px;text-align:left;font-family:'Montserrat',sans-serif;font-size:13px;font-weight:800;border-bottom:2px solid #eee}}
.comparison-table td{{padding:11px 14px;border-bottom:1px solid #eee;vertical-align:top}}
.comparison-table tr:last-child td{{border-bottom:none}}
.comparison-table .good{{color:#2eaa4f;font-weight:700}}
.comparison-table .bad{{color:#e53e3e;font-weight:700}}
.testimonial{{background:#fff5f0;border-left:4px solid #f26722;border-radius:0 8px 8px 0;padding:16px 20px;margin:12px 0}}
.testimonial .quote{{font-size:17px;line-height:1.65;color:#333;font-style:italic;margin-bottom:8px}}
.testimonial .attribution{{font-size:14px;color:#888;font-weight:700}}
.warning-box{{background:#fff5f0;border:1px solid #f9cdb8;border-radius:8px;padding:14px 18px;margin:12px 0;font-size:16px;display:flex;gap:10px;align-items:flex-start}}
.warning-box svg{{flex-shrink:0;margin-top:2px}}
.warning-box strong{{color:#c04a0a;display:block;margin-bottom:4px}}
.offer-box{{border:2px solid #f26722;border-radius:12px;padding:24px;margin:28px 0 14px;background:#fff5f0}}
.offer-box h2{{margin-top:0;margin-bottom:12px;font-size:22px;color:#111}}
.step{{margin-bottom:12px;display:flex;flex-direction:row;gap:10px;align-items:flex-start}}
.step svg{{flex-shrink:0;margin-top:3px}}
.step .step-title{{font-weight:700;font-size:16px;margin-bottom:2px;color:#111}}
.step p{{font-size:16px;margin-bottom:0}}
.tip{{background:#fff;border-left:3px solid #f26722;padding:12px 16px;margin:12px 0;font-size:16px;border-radius:0 6px 6px 0;display:flex;gap:8px;align-items:flex-start}}
.tip svg{{flex-shrink:0;margin-top:2px}}
.cta-bottom{{display:block;width:100%;padding:17px;background:#f26722;color:#111;text-align:center;font-size:18px;font-weight:700;border-radius:8px;text-decoration:none;margin:16px 0 10px;transition:background .2s}}
.cta-bottom:hover{{background:#d85a1b}}
.cta-badges{{font-size:14px;color:#555;margin-bottom:8px}}
.cta-badges>div{{margin-bottom:4px;display:flex;align-items:center;gap:6px}}
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#f26722;padding:12px 20px;text-align:center;z-index:100}}
.sticky-footer a{{color:#111;text-decoration:none;font-weight:700;font-size:16px}}
.stars{{color:#f26722;font-size:14px}}
ul,ol{{padding-left:24px;margin-bottom:12px;overflow-wrap:break-word}}
li{{margin-bottom:6px}}
@media(max-width:840px){{
.page-wrapper{{flex-direction:column;padding:14px}}
.sidebar{{width:100%;position:relative;top:0;order:2;margin-top:24px}}
.article-content{{order:1}}
h1{{font-size:28px}}h2{{font-size:24px}}p{{font-size:16px}}
.stat-row{{gap:10px}}.stat-box .stat-num{{font-size:22px}}
ul,ol{{padding-left:20px;padding-right:8px}}
}}
</style>
</head>
<body>
<div class="page-wrapper">
  <div class="article-content">
    <h1>{headline}</h1>
    <p class="byline">{tx["byline_by"]} {author_name} | {today}</p>
    {article_body}
    {offer_box}
  </div>
  <div class="sidebar">
    <div class="sidebar-card">
      <div class="sb-title">{product_name}</div>
      {'<img src="' + product_image_url + '" alt="' + product_name + '" style="width:100%;">' if product_image_url else '<div class="sb-img">[' + tx["product_img_alt"] + ']</div>'}
      <div class="sb-rating">★★★★★ &nbsp;4.9/5</div>
      <div class="sb-price"><strong>{product_price}</strong> <span style="color:#aaa;font-size:14px;text-decoration:line-through;margin-left:6px">{product_price_old}</span></div>
      <a href="{product_url}" class="sb-cta">{tx["cta"]}</a>
      <div class="sb-badges">
        <div>✓ {tx["badge1"]}</div>
        <div>✓ {tx["badge2"]}</div>
        <div>✓ {tx.get("badge3", "")}</div>
        <div>✓ {tx.get("badge4", "")}</div>
      </div>
    </div>
  </div>
</div>
<div class="sticky-footer">
  <a href="{product_url}">{tx["cta_footer"]}</a>
</div>
</body>
</html>'''


async def main():
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    if len(sys.argv) < 2:
        print("Usage: python -m agents.html_publisher <draft.json> [--product-url URL] [--product-name NAME] [--slug SLUG]")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        draft = json.load(f)

    kw = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--product-url": kw["product_url"] = sys.argv[i+1]; i += 2
        elif sys.argv[i] == "--product-name": kw["product_name"] = sys.argv[i+1]; i += 2
        elif sys.argv[i] == "--slug": kw["slug"] = sys.argv[i+1]; i += 2
        elif sys.argv[i] == "--author": kw["author_name"] = sys.argv[i+1]; i += 2
        else: i += 1

    agent = HTMLPublisherAgent()
    r = await agent.run(draft, **kw)
    print(f"\n✅ {r['html_file']} ({r['word_count']} mots)")
    if r.get("url"): print(f"🌐 {r['url']}")

if __name__ == "__main__":
    import asyncio; asyncio.run(main())
