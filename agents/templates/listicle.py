"""Listicle template — numbered cards, modern layout."""
from datetime import datetime


def build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang, tx):
    today = datetime.utcnow().strftime("%B %d, %Y")
    headline = content.get("headline", "")

    body_parts = []
    offer_section = None
    cta_section = None
    card_num = 0

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

        card_num += 1
        img_html = ""
        if img_url:
            img_html = f'<img src="{img_url}" alt="{heading}" style="width:100%;border-radius:10px;margin-bottom:14px;">'
        elif placeholder.get("description"):
            p_type = placeholder.get("type", "product").upper().replace("_", " / ")
            img_html = f'<div class="placeholder"><span class="tag">{p_type}</span>{placeholder["description"]}</div>'

        body_parts.append(f'''<div class="card">
  <div class="card-num">{card_num}</div>
  <div class="card-body">
    {img_html}
    {"<h2>" + heading + "</h2>" if heading else ""}
    {body_html}
  </div>
</div>''')

    article_body = "\n".join(body_parts)
    cta_body = cta_section.get("body_html", "") if cta_section else ""

    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<title>{seo.get("meta_title", headline)}</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{seo.get("meta_description", "")}">
<meta name="robots" content="noindex, nofollow">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Poppins',sans-serif;color:#1e1e2e;background:#f4f4f8;font-size:16px;line-height:1.7;padding-bottom:60px}}
.hero{{background:linear-gradient(135deg,#1e1e2e 0%,#2d2d44 100%);color:#fff;padding:48px 24px 40px;text-align:center}}
.hero h1{{font-size:32px;font-weight:800;line-height:1.2;margin-bottom:10px;max-width:700px;margin-left:auto;margin-right:auto}}
.hero .byline{{font-size:13px;color:rgba(255,255,255,.6);margin-top:6px}}
.container{{max-width:760px;margin:0 auto;padding:28px 20px}}
.card{{display:flex;gap:18px;background:#fff;border-radius:14px;padding:24px;margin-bottom:16px;box-shadow:0 2px 12px rgba(0,0,0,.06);transition:transform .15s}}
.card:hover{{transform:translateY(-2px);box-shadow:0 4px 20px rgba(0,0,0,.1)}}
.card-num{{width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,#6c5ce7,#a855f7);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px;flex-shrink:0}}
.card-body{{flex:1;min-width:0}}
.card-body h2{{font-size:19px;font-weight:700;margin-bottom:6px;color:#1e1e2e;line-height:1.3}}
.card-body p{{font-size:15px;color:#444;margin-bottom:6px}}
.placeholder{{background:#f0f0f4;padding:30px 16px;text-align:center;color:#999;border-radius:10px;margin-bottom:12px;font-style:italic;font-size:13px;border:1px dashed #ddd}}
.placeholder .tag{{display:inline-block;background:#6c5ce7;color:#fff;font-size:9px;padding:2px 8px;border-radius:8px;margin-bottom:6px;font-style:normal;text-transform:uppercase;letter-spacing:.6px;font-weight:600}}
.offer-card{{background:linear-gradient(135deg,#6c5ce7 0%,#a855f7 100%);border-radius:16px;padding:32px 28px;margin:24px 0;color:#fff;text-align:center}}
.offer-card h3{{font-size:22px;font-weight:800;margin-bottom:10px}}
.offer-card p{{font-size:14px;opacity:.9;margin-bottom:16px}}
.steps{{display:flex;gap:10px;margin:18px 0;flex-wrap:wrap;justify-content:center}}
.step-pill{{background:rgba(255,255,255,.2);border-radius:20px;padding:8px 16px;font-size:13px;font-weight:600;backdrop-filter:blur(4px)}}
.cta-btn{{display:inline-block;padding:16px 44px;background:#fff;color:#6c5ce7;font-size:17px;font-weight:700;border-radius:10px;text-decoration:none;transition:all .2s;box-shadow:0 4px 16px rgba(0,0,0,.2)}}
.cta-btn:hover{{transform:scale(1.03);box-shadow:0 6px 24px rgba(0,0,0,.3)}}
.badges{{display:flex;gap:16px;justify-content:center;margin-top:14px;font-size:12px;opacity:.85}}
.badges span::before{{content:"✓ "}}
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:linear-gradient(135deg,#6c5ce7,#a855f7);padding:12px 20px;text-align:center;z-index:100;box-shadow:0 -2px 12px rgba(0,0,0,.2)}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:700;font-size:15px}}
ul,ol{{padding-left:24px;margin-bottom:12px}}li{{margin-bottom:6px}}
@media(max-width:640px){{
.hero{{padding:32px 16px 28px}}.hero h1{{font-size:24px}}
.card{{flex-direction:column;gap:10px}}.card-num{{align-self:flex-start}}
.container{{padding:16px 14px}}.steps{{flex-direction:column}}
}}
</style>
</head>
<body>
<div class="hero">
  <h1>{headline}</h1>
  <div class="byline">{tx["byline_by"]} {author_name} &middot; {today}</div>
</div>
<div class="container">
  {article_body}
  <div class="offer-card">
    <h3>{product_name}</h3>
    <p>{tx.get("offer_desc","")}</p>
    <div class="steps">
      <div class="step-pill">{tx["step1_title"]}</div>
      <div class="step-pill">{tx["step2_title"]}</div>
      <div class="step-pill">{tx["step3_title"]}</div>
    </div>
    {cta_body}
    <a href="{product_url}" class="cta-btn">{tx["cta"]}</a>
    <div class="badges"><span>{tx["badge1"]}</span><span>{tx["badge2"]}</span></div>
  </div>
</div>
<div class="sticky-footer">
  <a href="{product_url}">{tx["cta_footer"]}</a>
</div>
</body>
</html>'''
