"""Health Journal template — medical/wellness single-column layout."""
from datetime import datetime


def build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang, tx):
    today = datetime.utcnow().strftime("%B %d, %Y")
    headline = content.get("headline", "")

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
            parts.append(f'<img src="{img_url}" alt="{heading}" style="width:100%;border-radius:12px;margin:16px 0;">')
        elif placeholder.get("description"):
            p_type = placeholder.get("type", "product").upper().replace("_", " / ")
            parts.append(f'<div class="placeholder"><span class="tag">{p_type}</span>{placeholder["description"]}</div>')

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
<link href="https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Merriweather',Georgia,serif;color:#2c2c2c;background:#faf9f6;font-size:17px;line-height:1.8;padding-bottom:60px}}
.wrapper{{max-width:720px;margin:0 auto;padding:32px 24px}}
.top-bar{{text-align:center;padding:8px 0;font-size:11px;color:#999;letter-spacing:1px;text-transform:uppercase;font-family:'Inter',sans-serif;border-bottom:1px solid #e8e4df}}
.byline{{text-align:center;font-size:13px;color:#999;margin:12px 0 28px;font-family:'Inter',sans-serif}}
h1{{font-size:34px;line-height:1.25;margin-bottom:8px;color:#1a1a1a;text-align:center;font-weight:900}}
h2{{font-size:22px;line-height:1.3;margin:28px 0 12px;color:#1a1a1a;font-weight:700;border-left:4px solid #3d8b6e;padding-left:14px}}
p{{margin-bottom:8px;color:#333}}
blockquote,.pullquote{{border-left:4px solid #3d8b6e;margin:24px 0;padding:16px 20px;background:#f0ede8;border-radius:0 8px 8px 0;font-style:italic;color:#444}}
.highlight{{background:#e8f5e9;padding:20px;border-radius:10px;margin:20px 0;border:1px solid #c8e6c9}}
.placeholder{{background:#f0ede8;padding:36px 20px;text-align:center;color:#999;border-radius:10px;margin:16px 0;font-style:italic;font-size:14px;border:1px dashed #d4cfc8;font-family:'Inter',sans-serif}}
.placeholder .tag{{display:inline-block;background:#3d8b6e;color:#fff;font-size:9px;padding:2px 8px;border-radius:8px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.6px;font-weight:600}}
.cta-section{{background:#fff;border:2px solid #3d8b6e;border-radius:14px;padding:28px;margin:32px 0;text-align:center}}
.cta-section h3{{font-size:20px;margin-bottom:10px;color:#1a1a1a}}
.cta-btn{{display:inline-block;padding:16px 40px;background:#3d8b6e;color:#fff;font-size:17px;font-weight:700;border-radius:8px;text-decoration:none;transition:background .2s;font-family:'Inter',sans-serif}}
.cta-btn:hover{{background:#2d7359}}
.badges{{display:flex;gap:16px;justify-content:center;margin-top:14px;font-size:13px;color:#666;font-family:'Inter',sans-serif}}
.badges span::before{{content:"✓ ";color:#3d8b6e;font-weight:700}}
.steps{{display:flex;flex-direction:column;gap:12px;margin:20px 0}}
.step-card{{display:flex;align-items:flex-start;gap:14px;padding:14px 18px;background:#fff;border-radius:10px;border:1px solid #e8e4df}}
.step-num{{width:32px;height:32px;border-radius:50%;background:#3d8b6e;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;flex-shrink:0;font-family:'Inter',sans-serif}}
.tip-box{{background:#fff8e1;border-left:4px solid #f9a825;padding:14px 18px;margin:16px 0;border-radius:0 8px 8px 0;font-size:15px}}
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#3d8b6e;padding:12px 20px;text-align:center;z-index:100}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:700;font-size:15px;font-family:'Inter',sans-serif}}
ul,ol{{padding-left:24px;margin-bottom:12px}}li{{margin-bottom:6px}}
@media(max-width:640px){{
.wrapper{{padding:20px 16px}}h1{{font-size:26px}}h2{{font-size:19px}}
.badges{{flex-direction:column;gap:6px}}
}}
</style>
</head>
<body>
<div class="top-bar">Health & Wellness Journal</div>
<div class="wrapper">
  <h1>{headline}</h1>
  <p class="byline">{tx["byline_by"]} {author_name} &middot; {today}</p>
  {article_body}
  <div class="cta-section">
    <h3>{product_name}</h3>
    <p style="font-size:15px;color:#555;margin-bottom:14px">{tx.get("offer_desc","")}</p>
    <div class="steps">
      <div class="step-card"><div class="step-num">1</div><div>{tx["step1"]}</div></div>
      <div class="step-card"><div class="step-num">2</div><div>{tx["step2"]}</div></div>
      <div class="step-card"><div class="step-num">3</div><div>{tx["step3"]}</div></div>
    </div>
    {cta_body}
    <a href="{product_url}" class="cta-btn">{tx["cta"]}</a>
    <div class="badges"><span>{tx["badge1"]}</span><span>{tx["badge2"]}</span></div>
  </div>
  <div class="tip-box">💡 {tx["tip"]}</div>
</div>
<div class="sticky-footer">
  <a href="{product_url}">{tx["cta_footer"]}</a>
</div>
</body>
</html>'''
