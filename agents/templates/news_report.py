"""News Report template — fake news site look with view counter, urgency bar, medical authority."""
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
            parts.append(f'<img src="{img_url}" alt="{heading}" style="width:100%;border-radius:4px;margin:14px 0;">')
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
<link href="https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700;900&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Source Sans 3',sans-serif;color:#222;background:#f4f4f4;font-size:18px;line-height:1.75;padding-bottom:56px}}
.top-bar{{background:#1a1a2e;color:#fff;padding:8px 20px;font-size:13px;display:flex;justify-content:space-between;align-items:center}}
.top-bar .site-name{{font-weight:700;font-size:15px;letter-spacing:1px;text-transform:uppercase}}
.top-bar .date{{color:#aaa;font-size:12px}}
.urgency-bar{{background:#e74c3c;color:#fff;text-align:center;padding:8px 16px;font-size:14px;font-weight:700;letter-spacing:.5px}}
.urgency-bar span{{animation:pulse-urgency 2s ease-in-out infinite}}
@keyframes pulse-urgency{{0%,100%{{opacity:1}}50%{{opacity:.6}}}}
.container{{max-width:740px;margin:0 auto;background:#fff;box-shadow:0 2px 20px rgba(0,0,0,.08)}}
.article-header{{padding:32px 32px 0}}
.article-header .category{{display:inline-block;background:#e74c3c;color:#fff;font-size:11px;font-weight:700;padding:4px 12px;border-radius:3px;text-transform:uppercase;letter-spacing:1px;margin-bottom:14px}}
h1{{font-family:'Merriweather',serif;font-weight:900;font-size:30px;line-height:1.25;margin-bottom:10px;color:#111}}
.subtitle{{font-size:17px;color:#555;line-height:1.5;margin-bottom:16px;font-style:italic}}
.meta-bar{{display:flex;align-items:center;gap:12px;padding:12px 0;border-top:1px solid #eee;border-bottom:1px solid #eee;font-size:13px;color:#777;flex-wrap:wrap}}
.meta-bar .author{{font-weight:700;color:#333}}
.meta-bar .views{{color:#e74c3c;font-weight:700}}
.meta-bar .reading-time{{color:#999}}
.article-content{{padding:24px 32px 32px}}
h2{{font-family:'Merriweather',serif;font-weight:700;font-size:22px;line-height:1.3;margin-top:28px;margin-bottom:12px;color:#111;border-left:4px solid #e74c3c;padding-left:14px}}
p{{font-size:18px;line-height:1.75;margin-bottom:14px;color:#333}}
strong{{color:#111}}
blockquote{{border-left:4px solid #e74c3c;margin:18px 0;padding:14px 20px;background:#fef5f5;font-style:italic;color:#444;border-radius:0 6px 6px 0}}
.placeholder{{background:#f7f7f7;padding:36px 20px;text-align:center;color:#aaa;border-radius:4px;margin:14px 0;font-style:italic;font-size:14px;border:1px dashed #ddd}}
.placeholder .tbadge{{display:inline-block;background:#e74c3c;color:#fff;font-size:10px;padding:3px 10px;border-radius:3px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700}}
.stat-row{{display:flex;gap:12px;margin:18px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:130px;background:#fef5f5;border:1px solid #f5c6c6;border-radius:6px;padding:14px;text-align:center}}
.stat-box .stat-num{{font-family:'Merriweather',serif;font-weight:900;font-size:26px;color:#e74c3c;display:block}}
.stat-box .stat-label{{font-size:13px;color:#666;margin-top:4px}}
.comparison-table{{width:100%;border-collapse:collapse;margin:18px 0;font-size:16px}}
.comparison-table th{{background:#1a1a2e;color:#fff;padding:12px 14px;text-align:left;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}}
.comparison-table td{{padding:11px 14px;border-bottom:1px solid #eee}}
.comparison-table .good{{color:#27ae60;font-weight:700}}
.comparison-table .bad{{color:#e74c3c;font-weight:700}}
.testimonial{{background:#fef5f5;border-left:4px solid #e74c3c;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0}}
.testimonial .quote{{font-size:17px;line-height:1.65;color:#333;font-style:italic;margin-bottom:6px}}
.testimonial .attribution{{font-size:13px;color:#888;font-weight:700}}
.warning-box{{background:#fff8e1;border:1px solid #ffe082;border-radius:6px;padding:14px 18px;margin:14px 0;font-size:16px;display:flex;gap:10px}}
.offer-box{{border:2px solid #e74c3c;border-radius:8px;padding:28px;margin:28px 0;background:#fef5f5}}
.offer-box h2{{border:none;padding-left:0;margin-top:0;color:#111}}
.step{{margin-bottom:12px;display:flex;gap:10px;align-items:flex-start}}
.step .step-title{{font-weight:700;font-size:16px;margin-bottom:2px;color:#111}}
.step p{{font-size:16px;margin-bottom:0}}
.tip{{background:#fff;border-left:3px solid #e74c3c;padding:12px 16px;margin:12px 0;font-size:16px;border-radius:0 6px 6px 0;display:flex;gap:8px}}
.cta-bottom{{display:block;width:100%;padding:18px;background:#e74c3c;color:#fff;text-align:center;font-size:18px;font-weight:700;border-radius:6px;text-decoration:none;margin:16px 0 10px;transition:background .2s;text-transform:uppercase;letter-spacing:.5px}}
.cta-bottom:hover{{background:#c0392b}}
.cta-badges{{font-size:14px;color:#555;margin-bottom:8px}}
.cta-badges>div{{margin-bottom:4px;display:flex;align-items:center;gap:6px}}
.accent{{color:#e74c3c}}
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#e74c3c;padding:12px 20px;text-align:center;z-index:100}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:700;font-size:16px}}
ul,ol{{padding-left:24px;margin-bottom:14px}}
li{{margin-bottom:6px}}
@media(max-width:740px){{
.article-header,.article-content{{padding:18px 16px}}
h1{{font-size:24px}}
h2{{font-size:20px}}
.meta-bar{{gap:8px}}
.stat-row{{gap:8px}}
}}
</style>
</head>
<body>
<div class="top-bar">
  <div class="site-name">Health News Today</div>
  <div class="date">{today}</div>
</div>
<div class="urgency-bar">
  <span>⚠️ TRENDING — This article has been shared over 50,000 times this week</span>
</div>
<div class="container">
  <div class="article-header">
    <div class="category">Investigation</div>
    <h1>{headline}</h1>
    {"<p class='subtitle'>" + subheadline + "</p>" if subheadline else ""}
    <div class="meta-bar">
      <span class="author">By {author_name}</span>
      <span>|</span>
      <span>{today}</span>
      <span>|</span>
      <span class="views">2,194,477 Views</span>
      <span>|</span>
      <span class="reading-time">8 min read</span>
    </div>
  </div>
  <div class="article-content">
    {article_body}

    <div class="offer-box">
      <h2>{tx["offer_title"]}</h2>
      <p><strong>{product_name}</strong><br>{tx["offer_desc"]}</p>
      <div class="offer-product">
        {'<img src="' + product_image_url + '" alt="' + product_name + '" style="width:100%;border-radius:6px;margin:8px 0 16px;">' if product_image_url else '<div class="placeholder"><div class="tbadge">' + tx.get("bundle_badge","PRODUCT") + '</div><br>' + tx.get("bundle_desc","Product image") + '</div>'}
      </div>
      {cta_body}
      <a href="{product_url}" class="cta-bottom">{tx["cta"]}</a>
      <div class="cta-badges">
        <div>✓ {tx["badge1"]}</div>
        <div>✓ {tx["badge2"]}</div>
        <div>✓ {tx.get("badge3","")}</div>
      </div>
    </div>
  </div>
</div>
<div class="sticky-footer">
  <a href="{product_url}">{tx["cta_footer"]}</a>
</div>
</body>
</html>'''
