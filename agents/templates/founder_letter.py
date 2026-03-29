"""Founder Letter template — warm cream paper look, personal letter style, Lora serif, no chrome."""
from datetime import datetime


def build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang, tx):
    today = datetime.utcnow().strftime("%B %d, %Y")
    headline = content.get("headline", "")
    subheadline = content.get("subheadline", "")

    body_parts = []
    offer_section = None
    cta_section = None
    all_img_urls = []

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

        if heading:
            parts.append(f'<h2 class="letter-h2">{heading}</h2>')
        if body_html:
            parts.append(f'<div class="letter-prose">{body_html}</div>')

        # Image AFTER body text — feels organic in a letter
        if img_url:
            all_img_urls.append(img_url)
            caption = placeholder.get("description", "") or ""
            parts.append(f'''<figure class="letter-fig">
  <img src="{img_url}" alt="{heading}">
  {"<figcaption>" + caption + "</figcaption>" if caption else ""}
</figure>''')
        elif placeholder.get("description"):
            p_type = placeholder.get("type", "image").upper()
            desc = placeholder["description"]
            if p_type == "VIDEO":
                parts.append(f'<div class="placeholder video-ph"><div class="tbadge">VIDEO</div><div class="play-icon">&#9654;</div><p>{desc}</p></div>')
            else:
                parts.append(f'<div class="placeholder"><div class="tbadge">{p_type}</div><br>{desc}</div>')

        if parts:
            body_parts.append("\n".join(parts))

    article_body = "\n\n".join(body_parts)
    cta_body = cta_section.get("body_html", "") if cta_section else ""

    # Gallery grid: show last 2–3 collected images before CTA
    gallery_html = ""
    gallery_imgs = all_img_urls[-3:] if len(all_img_urls) >= 2 else []
    if gallery_imgs:
        items = "".join(
            f'<div class="gal-item"><img src="{url}" alt="Product view"></div>'
            for url in gallery_imgs
        )
        gallery_html = f'<div class="gal-grid gal-{len(gallery_imgs)}">{items}</div>'

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
<link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Playfair+Display:wght@700;800&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Lora',serif;background:#f4efe8;color:#2c2218;font-size:18px;line-height:1.88;padding-bottom:68px}}

/* MAIN LETTER WRAPPER */
.letter-wrap{{max-width:720px;margin:40px auto;background:#fefcf8;box-shadow:0 4px 40px rgba(80,50,20,.1),0 1px 4px rgba(80,50,20,.06);border-radius:2px;overflow:hidden}}

/* HERO IMAGE — full-width at top */
.letter-hero{{width:100%;display:block;max-height:420px;object-fit:cover}}
.letter-hero-ph{{background:#e8e2d8;height:260px;display:flex;align-items:center;justify-content:center;color:#b0a090;font-size:14px;font-style:italic}}

/* LETTER BODY */
.letter-inner{{padding:44px 52px}}

/* DATE LINE */
.letter-date{{text-align:right;font-size:14px;color:#a08060;font-style:italic;margin-bottom:32px}}

/* HEADLINE */
h1{{font-family:'Playfair Display',serif;font-weight:800;font-size:34px;line-height:1.2;color:#1a1208;margin-bottom:10px}}
.letter-sub{{font-family:'Lora',serif;font-size:18px;color:#705840;line-height:1.55;margin-bottom:28px;font-style:italic;padding-bottom:22px;border-bottom:1px solid #e0d5c5}}

/* CONTENT */
.letter-h2{{font-family:'Playfair Display',serif;font-weight:700;font-size:22px;line-height:1.3;color:#1a1208;margin:36px 0 14px}}
.letter-prose p{{font-size:18px;line-height:1.88;margin-bottom:16px;color:#2c2218}}
.letter-prose strong{{color:#1a1208}}
.letter-prose em{{color:#5a4030}}
.letter-prose blockquote{{border-left:3px solid #c8a878;margin:20px 0;padding:14px 22px;background:#faf5ec;font-style:italic;color:#5a4030;border-radius:0 4px 4px 0}}
.letter-prose ul,.letter-prose ol{{padding-left:28px;margin-bottom:16px}}
.letter-prose li{{margin-bottom:7px;line-height:1.7}}

/* FIGURES */
.letter-fig{{margin:28px 0}}
.letter-fig img{{width:100%;display:block;border-radius:3px;box-shadow:0 3px 16px rgba(80,50,20,.12)}}
.letter-fig figcaption{{font-size:13px;color:#a08060;font-style:italic;padding:7px 4px;text-align:center}}
.video-ph{{background:#1a1208;color:#8a7060;padding:60px 20px;text-align:center;border-radius:4px;margin:24px 0}}
.play-icon{{font-size:44px;color:#c8a878;opacity:.8;display:block;margin:0 0 12px}}
.video-ph p{{color:#786050;font-size:13px}}
.placeholder{{background:#f4efe8;padding:36px 20px;text-align:center;color:#b0a090;border:1px dashed #d0c8b8;border-radius:4px;margin:24px 0;font-size:14px;font-style:italic}}
.tbadge{{display:inline-block;background:#8b5e3c;color:#fff;font-size:10px;padding:3px 10px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700;border-radius:10px}}

/* STAT ROW — toned down for letter feel */
.stat-row{{display:flex;gap:14px;margin:20px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:120px;background:#f4efe8;border:1px solid #e0d5c5;border-radius:6px;padding:14px;text-align:center}}
.stat-box .stat-num{{font-family:'Playfair Display',serif;font-weight:800;font-size:28px;color:#8b5e3c;display:block}}
.stat-box .stat-label{{font-size:13px;color:#a08060;margin-top:4px}}

/* Comparison, testimonials, tips — use letter palette */
.comparison-table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:16px}}
.comparison-table th{{background:#f4efe8;padding:11px 14px;text-align:left;font-family:'Playfair Display',serif;font-size:13px;font-weight:700;border-bottom:2px solid #e0d5c5;color:#1a1208}}
.comparison-table td{{padding:11px 14px;border-bottom:1px solid #eee}}
.comparison-table .good{{color:#4a7c3c;font-weight:700}}
.comparison-table .bad{{color:#a0341a;font-weight:700}}
.testimonial{{background:#f9f4ec;border-left:4px solid #c8a878;border-radius:0 6px 6px 0;padding:16px 20px;margin:18px 0}}
.testimonial .quote{{font-size:17px;line-height:1.7;color:#44321e;font-style:italic;margin-bottom:6px}}
.testimonial .attribution{{font-size:13px;color:#a08060;font-weight:700}}
.warning-box{{background:#fdf7ec;border:1px solid #e8c87a;border-radius:4px;padding:14px 18px;margin:14px 0;font-size:16px;display:flex;gap:10px}}
.step{{margin-bottom:12px;display:flex;gap:10px;align-items:flex-start}}
.step .step-title{{font-weight:700;font-size:16px;margin-bottom:2px;color:#1a1208}}
.step p{{font-size:16px;margin-bottom:0}}
.tip{{background:#fefcf8;border-left:3px solid #8b5e3c;padding:12px 16px;margin:12px 0;font-size:16px;border-radius:0 4px 4px 0;display:flex;gap:8px}}
.accent{{color:#8b5e3c}}

/* GALLERY GRID */
.gal-grid{{display:grid;gap:12px;margin:28px 0}}
.gal-3{{grid-template-columns:repeat(3,1fr)}}
.gal-2{{grid-template-columns:repeat(2,1fr)}}
.gal-1{{grid-template-columns:1fr}}
.gal-item img{{width:100%;aspect-ratio:1;object-fit:cover;border-radius:4px;box-shadow:0 2px 10px rgba(80,50,20,.12)}}

/* SIGNATURE */
.signature-block{{margin:36px 0 28px;padding-top:28px;border-top:1px solid #e0d5c5}}
.sig-name{{font-family:'Playfair Display',serif;font-weight:800;font-size:26px;color:#1a1208;margin-bottom:4px}}
.sig-title{{font-size:14px;color:#a08060;font-style:italic}}

/* OFFER BOX */
.offer-box{{border:1px solid #d0c8b8;border-radius:4px;padding:28px 32px;margin:28px 0;background:#f9f4ec}}
.offer-box h2{{font-family:'Playfair Display',serif;font-weight:700;font-size:22px;color:#1a1208;margin-bottom:12px}}
.offer-box p{{font-size:17px;color:#3a2810;margin-bottom:12px}}
.offer-box strong{{color:#1a1208}}
.cta-letter{{display:block;width:100%;padding:17px 24px;background:#8b5e3c;color:#fff;text-align:center;font-family:'Lora',serif;font-size:18px;font-weight:700;text-decoration:none;border-radius:4px;margin:18px 0 12px;transition:background .2s}}
.cta-letter:hover{{background:#6e4a2e}}
.offer-badges{{font-size:14px;color:#a08060}}
.offer-badges div{{margin-bottom:4px;display:flex;align-items:center;gap:6px}}

/* P.S. NOTE */
.ps-note{{background:#f4efe8;border-left:3px solid #8b5e3c;padding:14px 20px;margin:24px 0;font-style:italic;font-size:16px;color:#5a4030;border-radius:0 4px 4px 0}}

/* STICKY FOOTER */
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#8b5e3c;padding:13px 20px;text-align:center;z-index:300}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:700;font-size:16px;font-family:'Lora',serif}}

/* RESPONSIVE */
@media(max-width:720px){{
  .letter-wrap{{margin:0;border-radius:0}}
  .letter-inner{{padding:24px 18px}}
  h1{{font-size:27px}}
  .letter-h2{{font-size:19px}}
  .gal-3{{grid-template-columns:repeat(2,1fr)}}
  .offer-box{{padding:20px 16px}}
}}
</style>
</head>
<body>

<div class="letter-wrap">
  {'<img class="letter-hero" src="' + list(image_map.values())[0] + '" alt="' + product_name + '">' if image_map else '<div class="letter-hero-ph">[ Hero Image — Founder / Product ]</div>'}

  <div class="letter-inner">
    <div class="letter-date">{today}</div>

    <h1>{headline}</h1>
    {"<p class='letter-sub'>" + subheadline + "</p>" if subheadline else ""}

    {article_body}

    <div class="signature-block">
      <div class="sig-name">{author_name}</div>
      <div class="sig-title">Founder, {product_name}</div>
    </div>

    {gallery_html}

    <div class="offer-box">
      <h2>{tx["offer_title"]}</h2>
      <p>{tx["offer_desc"]}</p>
      {'<img src="' + product_image_url + '" alt="' + product_name + '" style="width:100%;border-radius:4px;margin:8px 0 16px;box-shadow:0 2px 12px rgba(80,50,20,.12);">' if product_image_url else '<div class="placeholder"><div class="tbadge">' + tx.get("bundle_badge","PRODUCT") + '</div><br>' + tx.get("bundle_desc","Product image") + '</div>'}
      {cta_body}
      <a href="{product_url}" class="cta-letter">{tx["cta"]}</a>
      <div class="offer-badges">
        <div>&#10003; {tx["badge1"]}</div>
        <div>&#10003; {tx["badge2"]}</div>
        <div>&#10003; {tx.get("badge3","")}</div>
      </div>
    </div>

    <div class="ps-note">
      <strong>P.S.</strong> — Once our current inventory sells out, we cannot guarantee the same price or availability. If you've been thinking about it — now is the time.
    </div>
  </div>
</div>

<div class="sticky-footer">
  <a href="{product_url}">{tx["cta_footer"]}</a>
</div>

</body>
</html>'''
