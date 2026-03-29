"""Personal Story template — first-person narrative, magazine-style with pull quotes and hero images."""
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
            parts.append(f'<div class="full-img"><img src="{img_url}" alt="{heading}"></div>')
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
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;color:#1a1a1a;background:#fff;font-size:18px;line-height:1.8;padding-bottom:56px}}
.hero{{background:linear-gradient(135deg,#0a0a0a 0%,#1a1a2e 100%);color:#fff;padding:60px 20px 48px;text-align:center}}
.hero .tag{{display:inline-block;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);padding:4px 14px;border-radius:20px;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:18px}}
.hero h1{{font-family:'DM Serif Display',serif;font-size:38px;line-height:1.2;max-width:720px;margin:0 auto 12px}}
.hero .sub{{font-size:17px;color:rgba(255,255,255,.7);max-width:600px;margin:0 auto 20px;line-height:1.5}}
.hero .meta{{font-size:13px;color:rgba(255,255,255,.4)}}
.article-content{{max-width:680px;margin:0 auto;padding:36px 20px}}
h2{{font-family:'DM Serif Display',serif;font-size:26px;line-height:1.3;margin-top:32px;margin-bottom:14px;color:#0a0a0a}}
p{{margin-bottom:14px;color:#333}}
strong{{color:#0a0a0a}}
.pull-quote{{font-family:'DM Serif Display',serif;font-size:24px;line-height:1.4;color:#0a0a0a;text-align:center;padding:28px 32px;margin:28px -20px;border-top:2px solid #0a0a0a;border-bottom:2px solid #0a0a0a;font-style:italic}}
.full-img{{margin:20px -20px}}
.full-img img{{width:100%;display:block}}
.placeholder{{background:#f5f5f5;padding:36px 20px;text-align:center;color:#999;border-radius:6px;margin:16px 0;font-style:italic;font-size:14px;border:1px dashed #ddd}}
.placeholder .tbadge{{display:inline-block;background:#0a0a0a;color:#fff;font-size:10px;padding:3px 10px;border-radius:10px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700}}
.stat-row{{display:flex;gap:14px;margin:18px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:130px;background:#f5f5f5;border-radius:8px;padding:16px;text-align:center}}
.stat-box .stat-num{{font-family:'DM Serif Display',serif;font-size:28px;color:#0a0a0a;display:block}}
.stat-box .stat-label{{font-size:13px;color:#777;margin-top:4px}}
.comparison-table{{width:100%;border-collapse:collapse;margin:18px 0;font-size:16px}}
.comparison-table th{{background:#f5f5f5;padding:11px 14px;text-align:left;font-size:13px;font-weight:700;border-bottom:2px solid #ddd}}
.comparison-table td{{padding:11px 14px;border-bottom:1px solid #eee}}
.comparison-table .good{{color:#16a34a;font-weight:700}}
.comparison-table .bad{{color:#dc2626;font-weight:700}}
.testimonial{{background:#f5f5f5;border-radius:12px;padding:20px 24px;margin:18px 0}}
.testimonial .quote{{font-size:17px;line-height:1.7;color:#333;font-style:italic;margin-bottom:6px}}
.testimonial .attribution{{font-size:13px;color:#888;font-weight:700}}
.warning-box{{background:#fef3c7;border:1px solid #fbbf24;border-radius:8px;padding:14px 18px;margin:14px 0;font-size:16px;display:flex;gap:10px}}
.offer-box{{background:#0a0a0a;color:#fff;border-radius:12px;padding:32px;margin:36px 0}}
.offer-box h2{{color:#fff;margin-top:0;font-size:24px}}
.offer-box p{{color:rgba(255,255,255,.8)}}
.offer-box strong{{color:#fff}}
.step{{margin-bottom:12px;display:flex;gap:10px;align-items:flex-start}}
.step .step-title{{font-weight:700;font-size:16px;margin-bottom:2px;color:#fff}}
.step p{{font-size:16px;margin-bottom:0;color:rgba(255,255,255,.8)}}
.tip{{background:rgba(255,255,255,.05);border-left:3px solid rgba(255,255,255,.2);padding:12px 16px;margin:12px 0;font-size:16px;border-radius:0 6px 6px 0;display:flex;gap:8px;color:rgba(255,255,255,.8)}}
.cta-bottom{{display:block;width:100%;padding:18px;background:#fff;color:#0a0a0a;text-align:center;font-size:18px;font-weight:700;border-radius:8px;text-decoration:none;margin:20px 0 10px;transition:background .2s}}
.cta-bottom:hover{{background:#f0f0f0}}
.cta-badges{{font-size:14px;color:rgba(255,255,255,.5);margin-bottom:8px}}
.cta-badges>div{{margin-bottom:4px;display:flex;align-items:center;gap:6px}}
.accent{{color:#0a0a0a}}
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#0a0a0a;padding:12px 20px;text-align:center;z-index:100}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:700;font-size:16px}}
ul,ol{{padding-left:24px;margin-bottom:14px}}
li{{margin-bottom:6px}}
@media(max-width:700px){{
.hero{{padding:36px 16px 32px}}
.hero h1{{font-size:28px}}
.article-content{{padding:24px 16px}}
h2{{font-size:22px}}
.pull-quote{{font-size:20px;padding:20px 16px;margin:20px 0}}
.full-img{{margin:16px -16px}}
}}
</style>
</head>
<body>
<div class="hero">
  <div class="tag">Personal Story</div>
  <h1>{headline}</h1>
  {"<p class='sub'>" + subheadline + "</p>" if subheadline else ""}
  <div class="meta">By {author_name} · {today}</div>
</div>
<div class="article-content">
  {article_body}

  <div class="offer-box">
    <h2>{tx["offer_title"].replace("#f26722","#fff")}</h2>
    <p><strong>{product_name}</strong><br>{tx["offer_desc"]}</p>
    {'<img src="' + product_image_url + '" alt="' + product_name + '" style="width:100%;border-radius:8px;margin:8px 0 16px;">' if product_image_url else '<div class="placeholder" style="background:rgba(255,255,255,.05);border-color:rgba(255,255,255,.15);color:rgba(255,255,255,.4)"><div class="tbadge" style="background:#fff;color:#0a0a0a">' + tx.get("bundle_badge","PRODUCT") + '</div><br>' + tx.get("bundle_desc","Product image") + '</div>'}
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
