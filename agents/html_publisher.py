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
    ) -> dict:
        self.log_start()

        content = advertorial_draft.get("content", {})
        seo = advertorial_draft.get("seo", {})
        if not product_name:
            product_name = content.get("headline", "Product")[:60]
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

        html = self._build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang=lang)

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

    def _build_html(self, content, seo, image_map, product_url, product_name, product_image_url, author_name, lang="en"):
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

        offer_box = f'''<div class="offer-box">
      <h2>⚠️ Special Offer: <span class="accent">50% Off</span> — Limited Stock</h2>
      <p><strong>{product_name}</strong><br>Available <strong>ONLY</strong> on the official store — at the lowest price of the year.</p>
      <div class="offer-product">
        {'<img src="' + product_image_url + '" alt="' + product_name + '" style="width:100%;border-radius:8px;margin:8px 0 16px;">' if product_image_url else '<div class="placeholder"><div class="tbadge">product bundle</div><br>Product hero image with all accessories, price badge showing discount</div>'}
      </div>
      <div class="step"><div class="step-title">✅ Step 1</div><p>Order yours today to lock in the exclusive discount — only while supplies last.</p></div>
      <div class="step"><div class="step-title">✅ Step 2</div><p>When it arrives (2-5 business days from US warehouses), unbox it and start using it immediately. No setup, no tools, no experience needed.</p></div>
      <div class="step"><div class="step-title">✅ Step 3</div><p>Make it part of your routine. See the difference in minutes — <strong>without any effort</strong>.</p></div>
      <div class="tip">💡 <strong>Useful tip:</strong><br>Know someone who would love this? It makes an incredible, actually-useful gift — the kind that gets used every week, not stored away.</div>
      <div class="tip">🎁 <strong>Gift idea:</strong> Get the bundle and save even more. Perfect for birthdays, holidays, or just treating yourself.</div>
      {cta_body}
      <a href="{product_url}" class="cta-bottom">Check Availability</a>
      <div class="cta-badges"><div><span class="chk">✔</span> 30-day money-back guarantee</div><div><span class="chk">✔</span> Free shipping from US warehouses</div></div>
    </div>'''

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
.sidebar-card{{border:1px solid #e5e5e5;border-radius:10px;overflow:hidden;background:#fff}}
.sidebar-card .sb-title{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:17px;text-align:center;padding:14px 16px 10px;color:#111;line-height:1.3}}
.sidebar-card .sb-img{{width:100%;height:200px;background:#f0f0f0;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:13px;font-style:italic}}
.sidebar-card .sb-cta{{display:block;margin:14px 16px;padding:14px;background:#f26722;color:#fff;text-align:center;font-size:16px;font-weight:700;border-radius:8px;text-decoration:none;transition:background .2s}}
.sidebar-card .sb-cta:hover{{background:#d85a1b}}
.sidebar-card .sb-badges{{padding:0 16px 14px;font-size:13px;color:#555}}
.sidebar-card .sb-badges div{{margin-bottom:4px}}
.chk{{color:#2eaa4f;margin-right:4px}}
.byline{{font-size:14px;color:#888;margin-bottom:16px}}
h1{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:32px;line-height:1.2;margin-bottom:12px;color:#111}}
h2{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:28px;line-height:1.25;margin-top:24px;margin-bottom:12px;color:#111}}
p{{font-size:18px;line-height:1.7;margin-bottom:6px;color:#222}}
strong{{color:#111}}
em{{color:#444}}
.accent{{color:#f26722}}
.placeholder{{background:#f7f7f7;padding:40px 20px;text-align:center;color:#aaa;border-radius:8px;margin:10px 0 14px;font-style:italic;font-size:14px;border:1px dashed #ddd}}
.placeholder .tbadge{{display:inline-block;background:#f26722;color:#fff;font-size:10px;padding:3px 10px;border-radius:10px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700}}
.offer-box{{border:2px solid #e5e5e5;border-radius:12px;padding:28px 24px;margin:32px 0 16px;background:#fff}}
.offer-box h2{{margin-top:0;font-size:24px}}
.step{{margin-bottom:12px}}
.step-title{{font-weight:700;font-size:16px;margin-bottom:2px}}
.step p{{font-size:16px;margin-bottom:4px}}
.tip{{background:#faf8f5;border-left:3px solid #f26722;padding:12px 16px;margin:16px 0;font-size:16px}}
.cta-bottom{{display:block;width:100%;padding:18px;background:#f26722;color:#fff;text-align:center;font-size:18px;font-weight:700;border-radius:8px;text-decoration:none;margin:20px 0 10px;transition:background .2s}}
.cta-bottom:hover{{background:#d85a1b}}
.cta-badges{{text-align:center;font-size:14px;color:#555;margin-bottom:8px}}
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#f26722;padding:12px 20px;text-align:center;z-index:100}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:700;font-size:16px}}
ul,ol{{padding-left:24px;margin-bottom:12px;overflow-wrap:break-word}}
li{{margin-bottom:6px}}
@media(max-width:840px){{
.page-wrapper{{flex-direction:column;padding:16px}}
.sidebar{{width:100%;position:relative;top:0;order:1;margin-top:24px}}
.article-content{{order:0}}
h1{{font-size:26px}}h2{{font-size:22px}}
ul,ol{{padding-left:20px;padding-right:8px}}
}}
</style>
</head>
<body>
<div class="page-wrapper">
  <div class="article-content">
    <h1>{headline}</h1>
    <p class="byline">By {author_name}&nbsp;&nbsp;|&nbsp;&nbsp;{today}&nbsp;&nbsp;|&nbsp;&nbsp;10:15 am</p>
    {article_body}
    {offer_box}
  </div>
  <div class="sidebar">
    <div class="sidebar-card">
      <div class="sb-title">{product_name}</div>
      {'<img src="' + product_image_url + '" alt="' + product_name + '" style="width:100%;">' if product_image_url else '<div class="sb-img">[Product image]</div>'}
      <a href="{product_url}" class="sb-cta">Check Availability</a>
      <div class="sb-badges">
        <div><span class="chk">✔</span> 30-day money-back guarantee</div>
        <div><span class="chk">✔</span> Free shipping (2-5 days)</div>
      </div>
    </div>
  </div>
</div>
<div class="sticky-footer">
  <a href="{product_url}">👉 Skip to offer — Check availability</a>
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
