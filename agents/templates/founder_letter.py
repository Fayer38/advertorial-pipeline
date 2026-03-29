"""Founder Letter template — handwritten/personal feel, cream background, hero image,
images throughout, 'Dear Friend' opening, gallery before CTA, signature with photo."""
from datetime import datetime


def build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang, tx):
    today = datetime.utcnow().strftime("%B %d, %Y")
    headline = content.get("headline", "")
    subheadline = content.get("subheadline", "")

    sections = content.get("sections", [])

    # Extract hero image from section 0 if available
    hero_img_url = image_map.get(0, "")

    body_parts = []
    offer_section = None
    cta_section = None
    gallery_imgs = []  # collect up to 3 images for gallery before offer

    for i, sec in enumerate(sections):
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

        # Collect images for gallery (skip the hero at index 0)
        if img_url and i > 0 and len(gallery_imgs) < 3:
            gallery_imgs.append((img_url, heading or placeholder.get("description", "")))

        if heading:
            parts.append(f'<h2 class="letter-h2">{heading}</h2>')

        if body_html:
            parts.append(body_html)

        # Image AFTER body text — personal/in-context feel
        if img_url and i > 0:
            caption = placeholder.get("description", heading) or heading
            parts.append(
                f'<figure class="letter-figure">'
                f'<img src="{img_url}" alt="{heading}" loading="lazy">'
                f'{"<figcaption>" + caption + "</figcaption>" if caption else ""}'
                f'</figure>'
            )
        elif placeholder.get("description") and i > 0:
            p_type = placeholder.get("type", "photo").upper()
            parts.append(
                f'<div class="placeholder">'
                f'<div class="tbadge">{p_type}</div>'
                f'<div class="ph-desc">{placeholder["description"]}</div>'
                f'</div>'
            )

        if parts:
            body_parts.append("\n".join(parts))

    # Build gallery HTML
    gallery_html = ""
    if gallery_imgs:
        items = "".join(
            f'<div class="gallery-item"><img src="{url}" alt="{alt}" loading="lazy"></div>'
            for url, alt in gallery_imgs
        )
        gallery_html = f'<div class="gallery-grid">{items}</div>'
    elif len([k for k in image_map if k > 0]) == 0:
        # All placeholders — show a row of placeholder boxes
        gallery_html = (
            f'<div class="gallery-grid">'
            f'<div class="placeholder gallery-ph"><div class="tbadge">PHOTO</div><div class="ph-desc">Product photo</div></div>'
            f'<div class="placeholder gallery-ph"><div class="tbadge">LIFESTYLE</div><div class="ph-desc">In-use photo</div></div>'
            f'<div class="placeholder gallery-ph"><div class="tbadge">PHOTO</div><div class="ph-desc">Results photo</div></div>'
            f'</div>'
        )

    article_body = "\n\n".join(body_parts)
    cta_body = cta_section.get("body_html", "") if cta_section else ""

    author_first = author_name.split()[0] if author_name else "Friend"
    author_initial = author_name[0].upper() if author_name else "F"

    # Hero block
    if hero_img_url:
        hero_block = f'<div class="hero-img-wrap"><img src="{hero_img_url}" alt="{headline}" class="hero-img"></div>'
    else:
        hero_block = (
            f'<div class="placeholder hero-placeholder">'
            f'<div class="tbadge">HERO PHOTO</div>'
            f'<div class="ph-desc">{sections[0].get("visual_placeholder", {}).get("description", "Founder or product hero image") if sections else "Founder or product hero image"}</div>'
            f'</div>'
        )

    # Product image in offer
    if product_image_url:
        offer_img_html = f'<img src="{product_image_url}" alt="{product_name}" class="offer-product-img">'
    else:
        offer_img_html = (
            f'<div class="placeholder" style="margin:12px 0 20px;">'
            f'<div class="tbadge">{tx.get("bundle_badge","PRODUCT")}</div>'
            f'<div class="ph-desc">{tx.get("bundle_desc","Product image")}</div>'
            f'</div>'
        )

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
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,800;1,400&family=Lora:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Lora',serif;color:#2a2118;background:#f5f0e8;font-size:18px;line-height:1.88;padding-bottom:64px}}

/* ── OUTER WRAPPER ── */
.page-bg{{background:#f5f0e8;min-height:100vh;padding:0 0 40px}}

/* ── HERO IMAGE ── */
.hero-img-wrap{{width:100%;max-height:480px;overflow:hidden;margin-bottom:0}}
.hero-img{{width:100%;display:block;object-fit:cover;max-height:480px}}
.hero-placeholder{{background:#ece6d9;border:none;height:260px;display:flex;flex-direction:column;align-items:center;justify-content:center;margin-bottom:0;border-radius:0}}

/* ── LETTER CONTAINER ── */
.letter-wrap{{max-width:700px;margin:0 auto;padding:0 20px}}
.letter-card{{background:#fffdf8;margin:-40px auto 0;position:relative;z-index:2;border-radius:3px;box-shadow:0 8px 40px rgba(60,40,10,.1);border-top:4px solid #7c5228;padding:48px 52px 52px}}

/* ── DATE & FROM ── */
.letter-top{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:28px;flex-wrap:wrap;gap:10px}}
.letter-date{{font-size:14px;color:#a08060;font-style:italic}}
.letter-from{{font-size:13px;color:#a08060;text-align:right}}

/* ── HEADLINE ── */
h1{{font-family:'Playfair Display',serif;font-weight:800;font-size:34px;line-height:1.2;margin-bottom:10px;color:#1a1208}}
.letter-deck{{font-size:17px;color:#6b5030;line-height:1.55;margin-bottom:28px;font-style:italic;border-bottom:1px solid #e8e0d0;padding-bottom:22px}}

/* ── DEAR FRIEND ── */
.dear-friend{{font-size:19px;font-style:italic;color:#4a3520;margin-bottom:20px;font-family:'Lora',serif}}

/* ── BODY ── */
.letter-h2{{font-family:'Playfair Display',serif;font-weight:700;font-size:24px;line-height:1.28;margin:36px 0 14px;color:#1a1208}}
p{{margin-bottom:16px;color:#2e2416;font-size:18px;line-height:1.88}}
strong{{color:#1a1208;font-weight:600}}
ul,ol{{padding-left:26px;margin-bottom:16px}}
li{{margin-bottom:8px;font-size:17px;line-height:1.75;color:#2e2416}}
blockquote{{border-left:4px solid #b8844e;margin:24px 0;padding:16px 22px;background:#faf6ee;font-style:italic;color:#5a4030;font-size:18px;line-height:1.7;border-radius:0 4px 4px 0}}

/* ── IMAGES ── */
.letter-figure{{margin:24px -52px}}
.letter-figure img{{width:100%;display:block}}
.letter-figure figcaption{{padding:8px 52px;font-size:13px;color:#a08060;font-style:italic;background:#faf6ee;border-bottom:1px solid #ede5d8}}

/* ── PLACEHOLDER ── */
.placeholder{{background:#faf6ee;border:1px dashed #c8b89a;border-radius:4px;padding:36px 20px;text-align:center;margin:20px 0}}
.tbadge{{display:inline-block;background:#7c5228;color:#fff;font-size:10px;padding:3px 10px;border-radius:10px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700;font-family:sans-serif}}
.ph-desc{{color:#b0947a;font-size:13px;font-style:italic}}

/* ── STATS ── */
.stat-row{{display:flex;gap:14px;margin:22px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:120px;background:#faf6ee;border:1px solid #e8e0d0;border-radius:8px;padding:16px;text-align:center}}
.stat-box .stat-num{{font-family:'Playfair Display',serif;font-weight:800;font-size:28px;color:#7c5228;display:block;line-height:1}}
.stat-box .stat-label{{font-size:13px;color:#a08060;margin-top:6px}}

/* ── TABLE ── */
.comparison-table{{display:block;overflow-x:auto;-webkit-overflow-scrolling:touch;width:100%;border-collapse:collapse;margin:20px 0;font-size:15px}}
.comparison-table th{{background:#faf6ee;padding:11px 14px;text-align:left;font-family:'Playfair Display',serif;font-size:13px;font-weight:700;border-bottom:2px solid #e8e0d0;color:#1a1208}}
.comparison-table td{{padding:11px 14px;border-bottom:1px solid #eee8e0;color:#2e2416}}
.comparison-table .good{{color:#3d7a3d;font-weight:700}}
.comparison-table .bad{{color:#a02020;font-weight:700}}

/* ── TESTIMONIAL ── */
.testimonial{{background:#faf6ee;border-left:4px solid #b8844e;border-radius:0 8px 8px 0;padding:18px 22px;margin:20px 0}}
.testimonial .quote{{font-size:17px;line-height:1.72;color:#4a3520;font-style:italic;margin-bottom:8px}}
.testimonial .attribution{{font-size:13px;color:#a08060;font-weight:700;font-family:sans-serif}}

/* ── WARNING ── */
.warning-box{{background:#fef8ec;border:1px solid #e8c87a;border-radius:6px;padding:14px 18px;margin:14px 0;font-size:16px;display:flex;gap:10px;color:#5a4010}}
.step{{margin-bottom:14px;display:flex;gap:12px;align-items:flex-start}}
.step-num-fl{{width:26px;height:26px;background:#b8844e;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0;margin-top:2px;font-family:sans-serif}}
.step .step-title{{font-weight:700;font-size:16px;margin-bottom:3px;color:#1a1208;font-family:'Lora',serif}}
.step p{{font-size:16px;margin-bottom:0;color:#2e2416}}
.tip{{background:#fff;border-left:3px solid #b8844e;padding:12px 16px;margin:14px 0;font-size:16px;border-radius:0 4px 4px 0;display:flex;gap:8px;color:#2e2416}}

/* ── GALLERY ── */
.gallery-section{{margin:40px 0 32px}}
.gallery-heading{{font-family:'Playfair Display',serif;font-weight:700;font-size:20px;color:#1a1208;margin-bottom:16px;text-align:center}}
.gallery-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:0 -52px}}
.gallery-item img{{width:100%;display:block;aspect-ratio:1;object-fit:cover;border-radius:4px}}
.gallery-ph{{margin:0;padding:24px 8px;min-height:100px;display:flex;flex-direction:column;align-items:center;justify-content:center}}

/* ── SIGNATURE ── */
.signature-block{{border-top:1px solid #e8e0d0;padding-top:28px;margin-top:36px;display:flex;align-items:flex-start;gap:20px}}
.sig-avatar{{width:64px;height:64px;border-radius:50%;background:#e8e0d0;border:2px solid #b8844e;flex-shrink:0;overflow:hidden;display:flex;align-items:center;justify-content:center;font-family:'Playfair Display',serif;font-size:26px;font-weight:700;color:#7c5228}}
.sig-text .sig-name{{font-family:'Playfair Display',serif;font-weight:700;font-size:26px;color:#1a1208;display:block;margin-bottom:2px}}
.sig-text .sig-title{{font-size:14px;color:#a08060;font-style:italic}}

/* ── PS NOTE ── */
.ps-note{{background:#faf6ee;border-left:4px solid #7c5228;padding:16px 22px;margin:28px 0 0;font-style:italic;font-size:16px;color:#5a4030;border-radius:0 6px 6px 0}}

/* ── OFFER BOX ── */
.offer-box{{border:2px solid #b8844e;border-radius:8px;padding:32px;margin:40px 0;background:#fef8f0}}
.offer-box-head{{display:flex;align-items:center;gap:10px;margin-bottom:6px}}
.offer-box-badge{{background:#7c5228;color:#fff;font-family:sans-serif;font-size:11px;font-weight:700;padding:4px 12px;border-radius:10px;text-transform:uppercase;letter-spacing:1px}}
.offer-box h2{{font-family:'Playfair Display',serif;font-weight:700;font-size:22px;color:#1a1208;margin:10px 0 8px}}
.offer-product-img{{width:100%;border-radius:6px;margin:14px 0 20px;display:block}}
.offer-desc-text{{font-size:16px;color:#4a3520;line-height:1.65;margin-bottom:18px}}
.offer-cta{{display:block;width:100%;padding:18px;background:#7c5228;color:#fff;text-align:center;font-size:18px;font-weight:700;border-radius:6px;text-decoration:none;margin:14px 0 10px;transition:background .2s;font-family:'Lora',serif;letter-spacing:.3px}}
.offer-cta:hover{{background:#5e3d1a}}
.offer-badges{{margin-top:12px}}
.offer-badges div{{display:flex;align-items:center;gap:6px;margin-bottom:5px;font-size:14px;color:#7c5228}}

/* ── STICKY FOOTER ── */
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#7c5228;padding:13px 20px;text-align:center;z-index:100}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:700;font-size:16px;font-family:'Lora',serif}}

/* ── RESPONSIVE ── */
@media(max-width:740px){{
.letter-card{{padding:28px 20px 36px}}
.letter-figure{{margin:20px -20px}}
.letter-figure figcaption{{padding:8px 20px}}
.gallery-grid{{grid-template-columns:repeat(3,1fr);gap:6px;margin:0 -20px}}
h1{{font-size:26px}}
.letter-h2{{font-size:21px}}
}}
</style>
</head>
<body>
<div class="page-bg">

  <!-- HERO IMAGE (full width, no container) -->
  {hero_block}

  <div class="letter-wrap">
    <div class="letter-card">

      <!-- DATE & FROM -->
      <div class="letter-top">
        <span class="letter-date">{today}</span>
        <span class="letter-from">From the desk of {author_name}</span>
      </div>

      <!-- HEADLINE -->
      <h1>{headline}</h1>
      {"<p class='letter-deck'>" + subheadline + "</p>" if subheadline else ""}

      <!-- DEAR FRIEND OPENING -->
      <p class="dear-friend">Dear Friend,</p>

      <!-- LETTER BODY -->
      {article_body}

      <!-- GALLERY SECTION BEFORE OFFER -->
      {"<div class='gallery-section'><p class='gallery-heading'>See it for yourself →</p>" + gallery_html + "</div>" if gallery_html else ""}

      <!-- SIGNATURE -->
      <div class="signature-block">
        <div class="sig-avatar">{author_initial}</div>
        <div class="sig-text">
          <span class="sig-name">{author_name}</span>
          <span class="sig-title">Founder, {product_name}</span>
        </div>
      </div>

      <!-- OFFER BOX -->
      <div class="offer-box">
        <div class="offer-box-head">
          <span class="offer-box-badge">✉ Special Offer</span>
        </div>
        <h2>{tx.get("offer_title", "My Personal Recommendation For You")}</h2>
        {offer_img_html}
        <div class="offer-desc-text">
          <strong>{product_name}</strong> — {tx.get("offer_desc", "")}
        </div>
        <div class="offer-desc-text">{cta_body}</div>
        <a href="{product_url}" class="offer-cta">{tx.get("cta", "Yes, I Want This →")}</a>
        <div class="offer-badges">
          <div>✓ {tx.get("badge1", "Money-Back Guarantee")}</div>
          <div>✓ {tx.get("badge2", "Free Shipping")}</div>
          {"<div>✓ " + tx.get("badge3","") + "</div>" if tx.get("badge3") else ""}
        </div>
      </div>

      <!-- PS NOTE -->
      <div class="ps-note">
        <strong>P.S.</strong> — I can only hold this offer for so long. Our inventory is genuinely limited and I'd hate for you to miss it. If it resonates with you, please don't wait.
      </div>

    </div><!-- /letter-card -->
  </div><!-- /letter-wrap -->
</div><!-- /page-bg -->

<div class="sticky-footer">
  <a href="{product_url}">{tx.get("cta_footer", "Get Yours Today →")}</a>
</div>
</body>
</html>'''
