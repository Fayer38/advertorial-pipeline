"""Medical Authority template — clinical look, doctor byline, study citations, trust badges."""
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
            parts.append(f'<img src="{img_url}" alt="{heading}" style="width:100%;border-radius:6px;margin:14px 0;">')
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
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'IBM Plex Sans',sans-serif;color:#1a1a1a;background:#f0f4f8;font-size:17px;line-height:1.75;padding-bottom:56px}}
.trust-bar{{background:#0f4c75;color:#fff;padding:8px 20px;font-size:12px;display:flex;justify-content:center;gap:20px;flex-wrap:wrap}}
.trust-bar span{{display:flex;align-items:center;gap:5px}}
.container{{max-width:760px;margin:20px auto;background:#fff;border-radius:8px;box-shadow:0 2px 16px rgba(0,0,0,.06);overflow:hidden}}
.article-header{{padding:32px 36px 0}}
.article-header .source{{font-size:12px;color:#0f4c75;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}}
h1{{font-family:'IBM Plex Serif',serif;font-weight:700;font-size:30px;line-height:1.25;margin-bottom:10px;color:#0a2540}}
.subtitle{{font-size:16px;color:#555;line-height:1.55;margin-bottom:18px}}
.author-box{{display:flex;align-items:center;gap:14px;padding:14px 0;border-top:1px solid #e8ecf0;border-bottom:1px solid #e8ecf0}}
.author-avatar{{width:48px;height:48px;border-radius:50%;background:#0f4c75;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:18px}}
.author-info .name{{font-weight:700;font-size:15px;color:#0a2540}}
.author-info .credentials{{font-size:12px;color:#777}}
.author-info .date{{font-size:12px;color:#aaa}}
.article-content{{padding:28px 36px 36px}}
h2{{font-family:'IBM Plex Serif',serif;font-weight:600;font-size:22px;line-height:1.3;margin-top:28px;margin-bottom:12px;color:#0a2540}}
p{{margin-bottom:13px;color:#333}}
strong{{color:#0a2540}}
.study-cite{{background:#f0f4f8;border-left:3px solid #0f4c75;padding:12px 16px;margin:14px 0;font-size:14px;color:#555;border-radius:0 6px 6px 0}}
.study-cite strong{{color:#0f4c75}}
.placeholder{{background:#f0f4f8;padding:36px 20px;text-align:center;color:#aaa;border-radius:6px;margin:14px 0;font-style:italic;font-size:14px;border:1px dashed #c8d6e0}}
.placeholder .tbadge{{display:inline-block;background:#0f4c75;color:#fff;font-size:10px;padding:3px 10px;border-radius:10px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700}}
.stat-row{{display:flex;gap:12px;margin:18px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:130px;background:#f0f4f8;border:1px solid #d4dfe8;border-radius:8px;padding:14px;text-align:center}}
.stat-box .stat-num{{font-family:'IBM Plex Serif',serif;font-weight:700;font-size:26px;color:#0f4c75;display:block}}
.stat-box .stat-label{{font-size:13px;color:#666;margin-top:4px}}
.comparison-table{{width:100%;border-collapse:collapse;margin:18px 0;font-size:16px}}
.comparison-table th{{background:#0a2540;color:#fff;padding:11px 14px;text-align:left;font-size:13px;font-weight:600;letter-spacing:.3px}}
.comparison-table td{{padding:11px 14px;border-bottom:1px solid #e8ecf0}}
.comparison-table .good{{color:#059669;font-weight:700}}
.comparison-table .bad{{color:#dc2626;font-weight:700}}
.testimonial{{background:#f0f4f8;border-left:4px solid #0f4c75;border-radius:0 8px 8px 0;padding:16px 20px;margin:16px 0}}
.testimonial .quote{{font-size:16px;line-height:1.65;color:#333;font-style:italic;margin-bottom:6px}}
.testimonial .attribution{{font-size:13px;color:#888;font-weight:600}}
.warning-box{{background:#fef3c7;border:1px solid #fbbf24;border-radius:6px;padding:14px 18px;margin:14px 0;font-size:16px;display:flex;gap:10px}}
.offer-box{{border:2px solid #0f4c75;border-radius:10px;padding:28px;margin:32px 0;background:#f0f4f8}}
.offer-box h2{{margin-top:0;color:#0a2540}}
.step{{margin-bottom:12px;display:flex;gap:10px;align-items:flex-start}}
.step .step-title{{font-weight:700;font-size:16px;margin-bottom:2px;color:#0a2540}}
.step p{{font-size:16px;margin-bottom:0}}
.tip{{background:#fff;border-left:3px solid #0f4c75;padding:12px 16px;margin:12px 0;font-size:16px;border-radius:0 6px 6px 0;display:flex;gap:8px}}
.cta-bottom{{display:block;width:100%;padding:18px;background:#0f4c75;color:#fff;text-align:center;font-size:18px;font-weight:700;border-radius:8px;text-decoration:none;margin:16px 0 10px;transition:background .2s}}
.cta-bottom:hover{{background:#0a3a5c}}
.cta-badges{{font-size:14px;color:#666;margin-bottom:8px}}
.cta-badges>div{{margin-bottom:4px;display:flex;align-items:center;gap:6px}}
.accent{{color:#0f4c75}}
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#0f4c75;padding:12px 20px;text-align:center;z-index:100}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:700;font-size:16px}}
ul,ol{{padding-left:24px;margin-bottom:14px}}
li{{margin-bottom:6px}}
@media(max-width:760px){{
.container{{margin:0;border-radius:0}}
.article-header,.article-content{{padding:20px 16px}}
h1{{font-size:24px}}
.trust-bar{{gap:10px;font-size:11px}}
}}
</style>
</head>
<body>
<div class="trust-bar">
  <span>🔬 Peer-Reviewed Research</span>
  <span>👨‍⚕️ Doctor-Verified</span>
  <span>📋 Clinical Studies</span>
  <span>🏥 FDA-Registered Facility</span>
</div>
<div class="container">
  <div class="article-header">
    <div class="source">Medical Review · Sponsored Content</div>
    <h1>{headline}</h1>
    {"<p class='subtitle'>" + subheadline + "</p>" if subheadline else ""}
    <div class="author-box">
      <div class="author-avatar">{author_name[0].upper() if author_name else "D"}</div>
      <div class="author-info">
        <div class="name">{author_name}</div>
        <div class="credentials">Board-Certified Specialist · 25+ Years Experience</div>
        <div class="date">Published {today} · Medically Reviewed</div>
      </div>
    </div>
  </div>
  <div class="article-content">
    {article_body}

    <div class="offer-box">
      <h2>{tx["offer_title"].replace("#f26722","#0f4c75")}</h2>
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
  </div>
</div>
<div class="sticky-footer">
  <a href="{product_url}">{tx["cta_footer"]}</a>
</div>
</body>
</html>'''
