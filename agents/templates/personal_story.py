"""Personal Story template — magazine editorial layout, pull quotes, hero image,
before/after visual structure, images distributed throughout, clean modern wide layout."""
from datetime import datetime


def build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang, tx):
    today = datetime.utcnow().strftime("%B %d, %Y")
    headline = content.get("headline", "")
    subheadline = content.get("subheadline", "")

    sections = content.get("sections", [])

    body_parts = []
    offer_section = None
    cta_section = None
    body_section_count = 0

    # Pull quotes — extracted from body sections periodically
    PULL_QUOTE_INTERVAL = 3  # inject after every Nth body section

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

        if heading:
            parts.append(f'<h2 class="section-h2">{heading}</h2>')

        if body_html:
            parts.append(body_html)

        # Image AFTER body — editorial image placement
        if img_url:
            caption = placeholder.get("description", heading) or heading
            if i == 0:
                # First image: large hero-style within content
                parts.append(
                    f'<div class="content-hero-img">'
                    f'<img src="{img_url}" alt="{heading}" loading="lazy">'
                    f'{"<p class=\\'img-caption\\'>" + caption + "</p>" if caption else ""}'
                    f'</div>'
                )
            else:
                # Subsequent images: full-width editorial
                parts.append(
                    f'<figure class="editorial-figure">'
                    f'<img src="{img_url}" alt="{heading}" loading="lazy">'
                    f'{"<figcaption>" + caption + "</figcaption>" if caption else ""}'
                    f'</figure>'
                )
        elif placeholder.get("description"):
            p_type = placeholder.get("type", "photo").upper()
            parts.append(
                f'<div class="placeholder">'
                f'<div class="tbadge">{p_type}</div>'
                f'<div class="ph-desc">{placeholder["description"]}</div>'
                f'</div>'
            )

        if parts:
            body_parts.append("\n".join(parts))

        body_section_count += 1

        # Inject pull quote after every PULL_QUOTE_INTERVAL sections
        if body_section_count % PULL_QUOTE_INTERVAL == 0 and heading:
            body_parts.append(
                f'<div class="pull-quote">'
                f'<span class="pq-mark">&ldquo;</span>'
                f'<p class="pq-text">{heading}</p>'
                f'<span class="pq-author">— {author_name}</span>'
                f'</div>'
            )

    article_body = "\n\n".join(body_parts)
    cta_body = cta_section.get("body_html", "") if cta_section else ""

    # Hero image from section 0
    hero_img_url = image_map.get(0, "")
    if hero_img_url:
        hero_img_html = f'<div class="hero-image-full"><img src="{hero_img_url}" alt="{headline}" loading="eager"></div>'
    else:
        first_ph = sections[0].get("visual_placeholder", {}) if sections else {{}}
        hero_img_html = (
            f'<div class="placeholder hero-ph">'
            f'<div class="tbadge">HERO</div>'
            f'<div class="ph-desc">{first_ph.get("description","Hero image")}</div>'
            f'</div>'
        )

    # Product image in offer
    if product_image_url:
        offer_img_html = f'<img src="{product_image_url}" alt="{product_name}" class="offer-product-img">'
    else:
        offer_img_html = (
            f'<div class="placeholder" style="margin:14px 0;">'
            f'<div class="tbadge">{tx.get("bundle_badge","PRODUCT")}</div>'
            f'<div class="ph-desc">{tx.get("bundle_desc","Product image")}</div>'
            f'</div>'
        )

    author_initial = author_name[0].upper() if author_name else "A"

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
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,700;1,400&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'DM Sans',sans-serif;color:#111;background:#fff;font-size:18px;line-height:1.78;padding-bottom:64px}}

/* ── MAGAZINE TOP BAR ── */
.mag-topbar{{background:#111;color:#fff;padding:10px 24px;display:flex;align-items:center;justify-content:space-between;font-size:12px;letter-spacing:.8px;text-transform:uppercase}}
.mag-name{{font-family:'DM Serif Display',serif;font-size:16px;letter-spacing:1px;text-transform:uppercase;color:#fff}}
.mag-section-tag{{color:#aaa;font-weight:500}}
.mag-date{{color:#666}}

/* ── HERO ── */
.article-hero{{background:#0a0a0a;color:#fff;padding:52px 24px 44px}}
.hero-tag{{display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15);color:rgba(255,255,255,.7);font-size:11px;letter-spacing:2px;text-transform:uppercase;padding:5px 14px;border-radius:20px;margin-bottom:20px}}
h1{{font-family:'DM Serif Display',serif;font-size:44px;line-height:1.1;margin-bottom:14px;color:#fff;max-width:760px}}
.hero-sub{{font-size:18px;color:rgba(255,255,255,.65);max-width:640px;line-height:1.5;margin-bottom:22px}}
.hero-byline{{display:flex;align-items:center;gap:12px;padding-top:18px;border-top:1px solid rgba(255,255,255,.1)}}
.hero-avatar{{width:38px;height:38px;border-radius:50%;background:#444;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;color:#fff;font-family:'DM Serif Display',serif;flex-shrink:0}}
.hero-byline-text .author-name{{font-size:14px;font-weight:600;color:#fff}}
.hero-byline-text .author-meta{{font-size:12px;color:#888}}

/* ── HERO IMAGE ── */
.hero-image-full{{max-height:520px;overflow:hidden}}
.hero-image-full img{{width:100%;display:block;object-fit:cover;max-height:520px}}
.hero-ph{{border-radius:0;height:260px;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#f0f0f0;border:none}}

/* ── MAIN LAYOUT ── */
.article-layout{{max-width:1060px;margin:0 auto;padding:0 24px;display:grid;grid-template-columns:1fr 260px;gap:56px;align-items:start}}
.article-body-col{{padding:44px 0}}
.article-aside{{padding:44px 0}}

/* ── BODY TYPOGRAPHY ── */
.section-h2{{font-family:'DM Serif Display',serif;font-size:28px;line-height:1.22;margin:40px 0 16px;color:#111}}
p{{margin-bottom:16px;color:#2a2a2a;font-size:18px;line-height:1.78}}
strong{{color:#111;font-weight:700}}
ul,ol{{padding-left:24px;margin-bottom:16px}}
li{{margin-bottom:8px;font-size:17px;line-height:1.7;color:#2a2a2a}}
blockquote{{border-left:4px solid #111;margin:24px 0;padding:16px 22px;background:#f7f7f7;font-family:'DM Serif Display',serif;font-size:20px;line-height:1.5;color:#333;font-style:italic;border-radius:0 4px 4px 0}}

/* ── PULL QUOTE ── */
.pull-quote{{border-top:3px solid #111;border-bottom:3px solid #111;padding:28px 0;margin:36px 0;text-align:center}}
.pq-mark{{font-family:'DM Serif Display',serif;font-size:80px;line-height:.6;color:#ddd;display:block;margin-bottom:8px}}
.pq-text{{font-family:'DM Serif Display',serif;font-style:italic;font-size:26px;line-height:1.35;color:#111;max-width:540px;margin:0 auto 12px}}
.pq-author{{font-size:13px;color:#888;text-transform:uppercase;letter-spacing:1.5px;font-weight:500}}

/* ── IMAGES ── */
.content-hero-img{{margin:24px -24px}}
.content-hero-img img{{width:100%;display:block}}
.content-hero-img .img-caption{{padding:8px 24px;font-size:13px;color:#888;font-style:italic;background:#fafafa;border-bottom:1px solid #eee}}
.editorial-figure{{margin:28px -24px}}
.editorial-figure img{{width:100%;display:block}}
.editorial-figure figcaption{{padding:8px 24px;font-size:13px;color:#888;font-style:italic;border-bottom:1px solid #f0f0f0}}

/* ── PLACEHOLDER ── */
.placeholder{{background:#f5f5f5;border:1px dashed #ddd;border-radius:4px;padding:36px 20px;text-align:center;margin:18px 0}}
.tbadge{{display:inline-block;background:#111;color:#fff;font-size:10px;padding:3px 10px;border-radius:10px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700;font-family:sans-serif}}
.ph-desc{{color:#aaa;font-size:13px;font-style:italic;margin-top:4px}}

/* ── STATS / ELEMENTS ── */
.stat-row{{display:flex;gap:14px;margin:22px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:130px;background:#f5f5f5;border-radius:8px;padding:16px;text-align:center}}
.stat-box .stat-num{{font-family:'DM Serif Display',serif;font-size:30px;color:#111;display:block;line-height:1}}
.stat-box .stat-label{{font-size:13px;color:#777;margin-top:6px}}
.comparison-table{{display:block;overflow-x:auto;-webkit-overflow-scrolling:touch;width:100%;border-collapse:collapse;margin:20px 0;font-size:15px}}
.comparison-table th{{background:#111;color:#fff;padding:11px 14px;text-align:left;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.8px}}
.comparison-table tr:nth-child(even) td{{background:#fafafa}}
.comparison-table td{{padding:11px 14px;border-bottom:1px solid #eee;color:#2a2a2a}}
.comparison-table .good{{color:#16a34a;font-weight:700}}
.comparison-table .bad{{color:#dc2626;font-weight:700}}
.testimonial{{background:#f7f7f7;border-radius:10px;padding:20px 24px;margin:20px 0}}
.testimonial .quote{{font-family:'DM Serif Display',serif;font-size:18px;line-height:1.65;color:#222;font-style:italic;margin-bottom:8px}}
.testimonial .attribution{{font-size:13px;color:#888;font-weight:600;font-family:sans-serif}}
.warning-box{{background:#fef3c7;border:1px solid #fbbf24;border-radius:8px;padding:14px 18px;margin:14px 0;font-size:16px;display:flex;gap:10px;color:#78350f}}
.step{{margin-bottom:14px;display:flex;gap:12px;align-items:flex-start}}
.step-num{{width:28px;height:28px;background:#111;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0;margin-top:2px;font-family:sans-serif}}
.step .step-title{{font-weight:700;font-size:16px;margin-bottom:3px;color:#111}}
.step p{{font-size:16px;margin-bottom:0;color:#2a2a2a}}
.tip{{background:#f7f7f7;border-left:3px solid #111;padding:12px 16px;margin:14px 0;font-size:16px;border-radius:0 6px 6px 0;color:#2a2a2a}}

/* ── ASIDE ── */
.aside-card{{background:#f7f7f7;border-radius:6px;padding:22px;margin-bottom:20px}}
.aside-card h3{{font-family:'DM Serif Display',serif;font-size:17px;color:#111;margin-bottom:14px;padding-bottom:8px;border-bottom:2px solid #111}}
.aside-card p{{font-size:14px;color:#555;line-height:1.6;margin-bottom:12px}}
.aside-cta{{display:block;background:#111;color:#fff;text-decoration:none;text-align:center;padding:12px;border-radius:4px;font-weight:700;font-size:14px;margin-top:4px}}

/* ── OFFER BOX ── */
.offer-section-heading{{font-family:'DM Serif Display',serif;font-size:22px;color:#111;margin:44px 0 6px;padding-top:32px;border-top:2px solid #111}}
.offer-narrative{{font-size:17px;color:#555;font-style:italic;margin-bottom:20px}}
.offer-box{{background:#111;color:#fff;border-radius:10px;padding:32px;margin:0 0 28px}}
.offer-box h2{{font-family:'DM Serif Display',serif;color:#fff;margin:0 0 8px;font-size:24px}}
.offer-box p{{color:rgba(255,255,255,.8);margin-bottom:16px}}
.offer-box strong{{color:#fff}}
.offer-product-img{{width:100%;border-radius:8px;margin:12px 0 20px;display:block}}
.offer-cta{{display:block;width:100%;padding:18px;background:#fff;color:#111;text-align:center;font-size:18px;font-weight:700;border-radius:6px;text-decoration:none;margin:16px 0 10px;transition:background .2s}}
.offer-cta:hover{{background:#f0f0f0}}
.offer-badges{{font-size:13px;color:rgba(255,255,255,.5)}}
.offer-badges div{{margin-bottom:4px;display:flex;align-items:center;gap:6px}}
.cta-body-html{{color:rgba(255,255,255,.75);font-size:15px;line-height:1.6;margin:10px 0}}

/* ── STICKY FOOTER ── */
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#111;padding:13px 20px;text-align:center;z-index:100}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:700;font-size:15px;font-family:'DM Sans',sans-serif}}

/* ── RESPONSIVE ── */
@media(max-width:860px){{
.article-layout{{grid-template-columns:1fr;gap:0;padding:0 16px}}
.article-aside{{display:none}}
.article-body-col{{padding:28px 0}}
.content-hero-img,.editorial-figure{{margin:18px -16px}}
.content-hero-img .img-caption,.editorial-figure figcaption{{padding:8px 16px}}
h1{{font-size:32px}}
.section-h2{{font-size:23px}}
.pull-quote .pq-text{{font-size:22px}}
.pq-mark{{font-size:60px}}
}}
</style>
</head>
<body>

<!-- ARTICLE HERO -->
<div class="article-hero">
  <div class="hero-tag">✦ Personal Story</div>
  <h1>{headline}</h1>
  {"<p class='hero-sub'>" + subheadline + "</p>" if subheadline else ""}
  <div class="hero-byline">
    <div class="hero-avatar">{author_initial}</div>
    <div class="hero-byline-text">
      <div class="author-name">{author_name}</div>
      <div class="author-meta">{today} · Personal Account</div>
    </div>
  </div>
</div>

<!-- HERO IMAGE -->
{hero_img_html}

<!-- MAIN LAYOUT -->
<div class="article-layout">
  <div class="article-body-col">

    {article_body}

    <!-- OFFER SECTION -->
    <div class="offer-section-heading">{tx.get("offer_title","Here's Exactly What I Ordered")}</div>
    <p class="offer-narrative">After everything I'd been through, I finally decided to try it for myself. Here's what I found and what I recommend:</p>

    <div class="offer-box">
      <h2>{product_name}</h2>
      {offer_img_html}
      <p>{tx.get("offer_desc","")}</p>
      <div class="cta-body-html">{cta_body}</div>
      <a href="{product_url}" class="offer-cta">{tx.get("cta","I Want This →")}</a>
      <div class="offer-badges">
        <div>✓ {tx.get("badge1","")}</div>
        <div>✓ {tx.get("badge2","")}</div>
        {"<div>✓ " + tx.get("badge3","") + "</div>" if tx.get("badge3") else ""}
      </div>
    </div>

  </div><!-- /article-body-col -->

  <!-- SIDEBAR -->
  <div class="article-aside">
    <div class="aside-card">
      <h3>My Top Pick</h3>
      <p>After months of searching, this is the one product that actually changed things for me.</p>
      <a href="{product_url}" class="aside-cta">{tx.get("cta_footer","See It Here")}</a>
    </div>
    <div class="aside-card" style="background:#111;color:#fff;">
      <h3 style="color:#fff;border-bottom-color:#fff">Don't Wait</h3>
      <p style="color:rgba(255,255,255,.7)">What worked for me might work for you too. Here's what to try first.</p>
      <a href="{product_url}" style="background:#fff;color:#111;display:block;text-decoration:none;text-align:center;padding:12px;border-radius:4px;font-weight:700;font-size:14px;margin-top:4px">{tx.get("cta_footer","Learn More")}</a>
    </div>
  </div>

</div><!-- /article-layout -->

<div class="sticky-footer">
  <a href="{product_url}">{tx.get("cta_footer","Read My Story & Get Yours →")}</a>
</div>
</body>
</html>'''
