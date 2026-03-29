"""Founder Letter template — personal letter from the founder/creator, emotional, handwritten feel."""
from datetime import datetime


def build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang, tx):
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
            parts.append(f'<img src="{img_url}" alt="{heading}" style="width:100%;border-radius:8px;margin:16px 0;">')
        elif placeholder.get("description"):
            p_type = placeholder.get("type", "").upper()
            parts.append(f'<div class="placeholder"><div class="tbadge">{p_type}</div><br>{placeholder["description"]}</div>')

        if heading:
            parts.append(f"<h2>{heading}</h2>")
        if body_html:
            parts.append(body_html)
        if parts:
            body_parts.append("\n".join(parts))

    article_body = "\n\n".join(body_parts)
    cta_body = cta_section.get("body_html", "") if cta_section else ""

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
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Lora:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Lora',serif;color:#2c2c2c;background:#faf8f5;font-size:18px;line-height:1.85;padding-bottom:56px}}
.letter-container{{max-width:680px;margin:40px auto;background:#fff;padding:48px 44px;box-shadow:0 4px 30px rgba(0,0,0,.06);border-radius:2px;border-top:4px solid #8b4513}}
.letter-date{{font-size:14px;color:#999;margin-bottom:24px;text-align:right;font-style:italic}}
h1{{font-family:'Playfair Display',serif;font-weight:800;font-size:32px;line-height:1.25;margin-bottom:8px;color:#1a1a1a}}
.subtitle{{font-size:17px;color:#666;line-height:1.5;margin-bottom:24px;font-style:italic;border-bottom:1px solid #e8e2da;padding-bottom:18px}}
h2{{font-family:'Playfair Display',serif;font-weight:700;font-size:23px;line-height:1.3;margin-top:32px;margin-bottom:12px;color:#1a1a1a}}
p{{margin-bottom:14px;color:#333}}
strong{{color:#1a1a1a}}
.signature{{margin-top:32px;padding-top:24px;border-top:1px solid #e8e2da}}
.signature .name{{font-family:'Playfair Display',serif;font-weight:700;font-size:22px;color:#1a1a1a;margin-bottom:4px}}
.signature .title{{font-size:14px;color:#888;font-style:italic}}
.ps{{background:#faf8f5;border-left:3px solid #8b4513;padding:16px 20px;margin:24px 0;font-style:italic;font-size:16px;color:#555;border-radius:0 6px 6px 0}}
.placeholder{{background:#faf8f5;padding:36px 20px;text-align:center;color:#aaa;border-radius:4px;margin:16px 0;font-style:italic;font-size:14px;border:1px dashed #d4c9bb}}
.placeholder .tbadge{{display:inline-block;background:#8b4513;color:#fff;font-size:10px;padding:3px 10px;border-radius:10px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700}}
.stat-row{{display:flex;gap:14px;margin:18px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:120px;background:#faf8f5;border:1px solid #e8e2da;border-radius:8px;padding:14px;text-align:center}}
.stat-box .stat-num{{font-family:'Playfair Display',serif;font-weight:800;font-size:26px;color:#8b4513;display:block}}
.stat-box .stat-label{{font-size:13px;color:#888;margin-top:4px}}
.comparison-table{{width:100%;border-collapse:collapse;margin:18px 0;font-size:16px}}
.comparison-table th{{background:#faf8f5;padding:11px 14px;text-align:left;font-family:'Playfair Display',serif;font-size:13px;font-weight:700;border-bottom:2px solid #e8e2da}}
.comparison-table td{{padding:11px 14px;border-bottom:1px solid #eee}}
.comparison-table .good{{color:#27ae60;font-weight:700}}
.comparison-table .bad{{color:#c0392b;font-weight:700}}
.testimonial{{background:#faf8f5;border-left:4px solid #8b4513;border-radius:0 8px 8px 0;padding:16px 20px;margin:16px 0}}
.testimonial .quote{{font-size:17px;line-height:1.7;color:#444;font-style:italic;margin-bottom:6px}}
.testimonial .attribution{{font-size:13px;color:#888;font-weight:700}}
.warning-box{{background:#fef9f0;border:1px solid #f0d9a8;border-radius:6px;padding:14px 18px;margin:14px 0;font-size:16px;display:flex;gap:10px}}
.offer-box{{border:2px solid #8b4513;border-radius:8px;padding:28px;margin:32px 0;background:#fef9f0}}
.offer-box h2{{margin-top:0}}
.step{{margin-bottom:12px;display:flex;gap:10px;align-items:flex-start}}
.step .step-title{{font-weight:700;font-size:16px;margin-bottom:2px;color:#1a1a1a}}
.step p{{font-size:16px;margin-bottom:0}}
.tip{{background:#fff;border-left:3px solid #8b4513;padding:12px 16px;margin:12px 0;font-size:16px;border-radius:0 6px 6px 0;display:flex;gap:8px}}
.cta-bottom{{display:block;width:100%;padding:18px;background:#8b4513;color:#fff;text-align:center;font-size:18px;font-weight:700;border-radius:6px;text-decoration:none;margin:16px 0 10px;transition:background .2s;font-family:'Lora',serif}}
.cta-bottom:hover{{background:#6d3510}}
.cta-badges{{font-size:14px;color:#777;margin-bottom:8px}}
.cta-badges>div{{margin-bottom:4px;display:flex;align-items:center;gap:6px}}
.accent{{color:#8b4513}}
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#8b4513;padding:12px 20px;text-align:center;z-index:100}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:700;font-size:16px}}
ul,ol{{padding-left:24px;margin-bottom:14px}}
li{{margin-bottom:6px}}
@media(max-width:700px){{
.letter-container{{margin:0;padding:24px 18px;border-radius:0}}
h1{{font-size:26px}}
h2{{font-size:20px}}
}}
</style>
</head>
<body>
<div class="letter-container">
  <div class="letter-date">{today}</div>
  <h1>{headline}</h1>
  {"<p class='subtitle'>" + subheadline + "</p>" if subheadline else ""}

  {article_body}

  <div class="signature">
    <div class="name">{author_name}</div>
    <div class="title">Founder, {product_name}</div>
  </div>

  <div class="offer-box">
    <h2>{tx["offer_title"]}</h2>
    <p><strong>{product_name}</strong><br>{tx["offer_desc"]}</p>
    {'<img src="' + product_image_url + '" alt="' + product_name + '" style="width:100%;border-radius:6px;margin:8px 0 16px;">' if product_image_url else '<div class="placeholder"><div class="tbadge">' + tx.get("bundle_badge","PRODUCT") + '</div><br>' + tx.get("bundle_desc","Product image") + '</div>'}
    {cta_body}
    <a href="{product_url}" class="cta-bottom">{tx["cta"]}</a>
    <div class="cta-badges">
      <div>✓ {tx["badge1"]}</div>
      <div>✓ {tx["badge2"]}</div>
      <div>✓ {tx.get("badge3","")}</div>
    </div>
  </div>

  <div class="ps">
    <strong>P.S.</strong> — This offer won't last. Once our inventory is gone, it's gone. Don't wait until it's too late.
  </div>
</div>
<div class="sticky-footer">
  <a href="{product_url}">{tx["cta_footer"]}</a>
</div>
</body>
</html>'''
