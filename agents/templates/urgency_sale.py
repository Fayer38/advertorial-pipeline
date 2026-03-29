"""Urgency/Sale template — countdown feel, bold colors, scarcity messaging, flash sale aesthetic."""
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
            parts.append(f'<img src="{img_url}" alt="{heading}" style="width:100%;border-radius:8px;margin:14px 0;">')
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
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Open Sans',sans-serif;color:#1a1a1a;background:#fff;font-size:17px;line-height:1.7;padding-bottom:56px}}
.countdown-bar{{background:linear-gradient(90deg,#dc2626,#ea580c);color:#fff;text-align:center;padding:10px 16px;font-size:14px;font-weight:700}}
.countdown-bar .timer{{font-family:'Montserrat',sans-serif;font-size:20px;margin-left:8px;letter-spacing:2px}}
.hero-sale{{background:#111;color:#fff;padding:40px 20px;text-align:center}}
.hero-sale .discount-badge{{display:inline-block;background:#dc2626;color:#fff;font-family:'Montserrat',sans-serif;font-weight:900;font-size:48px;padding:12px 28px;border-radius:8px;margin-bottom:16px;line-height:1}}
.hero-sale .discount-badge small{{font-size:18px;display:block;font-weight:700}}
h1{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:32px;line-height:1.2;margin-bottom:10px;max-width:700px;margin-left:auto;margin-right:auto}}
.hero-sale .sub{{font-size:16px;color:rgba(255,255,255,.7);max-width:600px;margin:0 auto}}
.article-content{{max-width:720px;margin:0 auto;padding:32px 20px}}
h2{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:22px;line-height:1.3;margin-top:28px;margin-bottom:12px;color:#111}}
p{{margin-bottom:13px;color:#333}}
strong{{color:#111}}
.stock-alert{{background:#fef2f2;border:2px solid #dc2626;border-radius:8px;padding:16px 20px;margin:18px 0;text-align:center}}
.stock-alert .stock-title{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:16px;color:#dc2626;margin-bottom:4px}}
.stock-bar{{height:8px;background:#fee2e2;border-radius:4px;overflow:hidden;margin:8px 0}}
.stock-bar .fill{{height:100%;background:#dc2626;border-radius:4px;width:23%;animation:stock-pulse 2s ease-in-out infinite}}
@keyframes stock-pulse{{0%,100%{{opacity:1}}50%{{opacity:.7}}}}
.placeholder{{background:#f5f5f5;padding:36px 20px;text-align:center;color:#999;border-radius:8px;margin:14px 0;font-style:italic;font-size:14px;border:1px dashed #ddd}}
.placeholder .tbadge{{display:inline-block;background:#dc2626;color:#fff;font-size:10px;padding:3px 10px;border-radius:10px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700}}
.stat-row{{display:flex;gap:12px;margin:18px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:130px;background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:14px;text-align:center}}
.stat-box .stat-num{{font-family:'Montserrat',sans-serif;font-weight:900;font-size:28px;color:#dc2626;display:block}}
.stat-box .stat-label{{font-size:13px;color:#666;margin-top:4px}}
.comparison-table{{width:100%;border-collapse:collapse;margin:18px 0;font-size:16px}}
.comparison-table th{{background:#111;color:#fff;padding:11px 14px;text-align:left;font-family:'Montserrat',sans-serif;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.5px}}
.comparison-table td{{padding:11px 14px;border-bottom:1px solid #eee}}
.comparison-table .good{{color:#16a34a;font-weight:700}}
.comparison-table .bad{{color:#dc2626;font-weight:700}}
.testimonial{{background:#f5f5f5;border-radius:8px;padding:16px 20px;margin:16px 0;border-left:4px solid #dc2626}}
.testimonial .quote{{font-size:16px;line-height:1.65;color:#333;font-style:italic;margin-bottom:6px}}
.testimonial .attribution{{font-size:13px;color:#888;font-weight:700}}
.warning-box{{background:#fef2f2;border:1px solid #fecaca;border-radius:6px;padding:14px 18px;margin:14px 0;font-size:16px;display:flex;gap:10px}}
.offer-box{{background:#111;color:#fff;border-radius:12px;padding:32px;margin:32px 0}}
.offer-box h2{{color:#fff;margin-top:0}}
.offer-box p{{color:rgba(255,255,255,.85)}}
.offer-box strong{{color:#fff}}
.step{{margin-bottom:12px;display:flex;gap:10px;align-items:flex-start}}
.step .step-title{{font-weight:700;font-size:16px;margin-bottom:2px;color:#fff}}
.step p{{font-size:16px;margin-bottom:0;color:rgba(255,255,255,.8)}}
.tip{{background:rgba(255,255,255,.05);border-left:3px solid #dc2626;padding:12px 16px;margin:12px 0;font-size:16px;border-radius:0 6px 6px 0;display:flex;gap:8px;color:rgba(255,255,255,.7)}}
.cta-bottom{{display:block;width:100%;padding:18px;background:#dc2626;color:#fff;text-align:center;font-size:20px;font-weight:800;border-radius:8px;text-decoration:none;margin:18px 0 10px;transition:background .2s;font-family:'Montserrat',sans-serif;text-transform:uppercase;letter-spacing:.5px}}
.cta-bottom:hover{{background:#b91c1c}}
.cta-badges{{font-size:14px;color:rgba(255,255,255,.5);margin-bottom:8px}}
.cta-badges>div{{margin-bottom:4px;display:flex;align-items:center;gap:6px}}
.accent{{color:#dc2626}}
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#dc2626;padding:12px 20px;text-align:center;z-index:100}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:700;font-size:16px}}
ul,ol{{padding-left:24px;margin-bottom:14px}}
li{{margin-bottom:6px}}
@media(max-width:740px){{
.hero-sale{{padding:28px 16px}}
.hero-sale .discount-badge{{font-size:36px;padding:10px 20px}}
h1{{font-size:26px}}
.article-content{{padding:24px 16px}}
h2{{font-size:20px}}
}}
</style>
</head>
<body>
<div class="countdown-bar">
  ⏰ SALE ENDS SOON — <span class="timer">LIMITED STOCK</span>
</div>
<div class="hero-sale">
  <div class="discount-badge">55% OFF<small>LIQUIDATION SALE</small></div>
  <h1>{headline}</h1>
  {"<p class='sub'>" + subheadline + "</p>" if subheadline else ""}
</div>
<div class="article-content">
  <div class="stock-alert">
    <div class="stock-title">⚠️ Only 23% of inventory remaining</div>
    <div class="stock-bar"><div class="fill"></div></div>
    <div style="font-size:13px;color:#666">Once it's gone, it's gone forever</div>
  </div>

  {article_body}

  <div class="offer-box">
    <h2>{tx["offer_title"].replace("#f26722","#dc2626")}</h2>
    <p><strong>{product_name}</strong><br>{tx["offer_desc"]}</p>
    {'<img src="' + product_image_url + '" alt="' + product_name + '" style="width:100%;border-radius:8px;margin:8px 0 16px;">' if product_image_url else '<div class="placeholder" style="background:rgba(255,255,255,.05);border-color:rgba(255,255,255,.15);color:rgba(255,255,255,.4)"><div class="tbadge">' + tx.get("bundle_badge","PRODUCT") + '</div><br>' + tx.get("bundle_desc","Product image") + '</div>'}
    {cta_body}
    <a href="{product_url}" class="cta-bottom">{tx["cta"]}</a>
    <div class="cta-badges">
      <div>✓ {tx["badge1"]}</div>
      <div>✓ {tx["badge2"]}</div>
      <div>✓ {tx.get("badge3","")}</div>
    </div>
  </div>
</div>
<div class="sticky-footer">
  <a href="{product_url}">{tx["cta_footer"]}</a>
</div>
</body>
</html>'''
