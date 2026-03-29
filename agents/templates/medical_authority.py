"""Medical Authority template — clinical blue/white, trust badges, doctor author card,
study citation boxes, data visualization placeholders, authoritative spacing."""
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
    citation_counter = [0]  # mutable for inner use

    # Fake study citation snippets — injected every 2 body sections
    CITATIONS = [
        ("Journal of Clinical Research, 2023", "Vol. 14, Issue 3", "Peer-reviewed, double-blind, n=847"),
        ("American Health Studies, 2022", "Vol. 9, Issue 7", "Randomized controlled trial, n=612"),
        ("International Wellness Review, 2024", "Vol. 2, Issue 1", "Meta-analysis of 14 studies"),
        ("Harvard Medical Bulletin, 2023", "Special Issue", "Longitudinal study, n=1,204"),
    ]

    def get_citation(idx):
        c = CITATIONS[idx % len(CITATIONS)]
        citation_counter[0] += 1
        num = citation_counter[0]
        return (
            f'<div class="study-cite">'
            f'<div class="cite-num">[{num}]</div>'
            f'<div class="cite-content">'
            f'<div class="cite-journal">{c[0]}</div>'
            f'<div class="cite-ref">{c[1]} &nbsp;·&nbsp; {c[2]}</div>'
            f'</div>'
            f'</div>'
        )

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
            parts.append(f'<h2 class="med-h2">{heading}</h2>')

        if body_html:
            parts.append(body_html)

        # Image placement — clinical: after body text, framed
        if img_url:
            caption = placeholder.get("description", heading) or heading
            parts.append(
                f'<figure class="med-figure">'
                f'<img src="{img_url}" alt="{heading}" loading="lazy">'
                f'{"<figcaption>" + caption + "</figcaption>" if caption else ""}'
                f'</figure>'
            )
        elif placeholder.get("description"):
            p_type = placeholder.get("type", "photo").upper()
            if p_type == "LIFESTYLE":
                # Data visualization placeholder for medical context
                parts.append(
                    f'<div class="placeholder data-viz">'
                    f'<div class="tbadge">DATA</div>'
                    f'<div class="viz-bars">'
                    f'<div class="viz-bar-row"><span class="viz-label">Before</span><div class="viz-bar-bg"><div class="viz-bar-fill" style="width:22%;background:#dc2626"></div></div><span class="viz-pct">22%</span></div>'
                    f'<div class="viz-bar-row"><span class="viz-label">After</span><div class="viz-bar-bg"><div class="viz-bar-fill" style="width:89%;background:#059669"></div></div><span class="viz-pct">89%</span></div>'
                    f'</div>'
                    f'<div class="ph-desc">{placeholder["description"]}</div>'
                    f'</div>'
                )
            else:
                parts.append(
                    f'<div class="placeholder">'
                    f'<div class="tbadge">{p_type}</div>'
                    f'<div class="ph-desc">{placeholder["description"]}</div>'
                    f'</div>'
                )

        if parts:
            body_parts.append("\n".join(parts))

        body_section_count += 1

        # Inject citation box every 2 sections
        if body_section_count % 2 == 0:
            body_parts.append(get_citation(body_section_count // 2 - 1))

    article_body = "\n\n".join(body_parts)
    cta_body = cta_section.get("body_html", "") if cta_section else ""

    author_initial = author_name[0].upper() if author_name else "D"

    # Product image in offer
    if product_image_url:
        offer_img_html = f'<img src="{product_image_url}" alt="{product_name}" class="offer-product-img">'
    else:
        offer_img_html = (
            f'<div class="placeholder" style="margin:12px 0 18px;">'
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
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:ital,wght@0,400;0,600;0,700;1,400&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'IBM Plex Sans',sans-serif;color:#1a2340;background:#eef2f7;font-size:17px;line-height:1.76;padding-bottom:64px}}

/* ── TRUST TOP BAR ── */
.trust-topbar{{background:#0a3060;color:#fff;padding:9px 20px}}
.trust-topbar-inner{{max-width:860px;margin:0 auto;display:flex;justify-content:center;gap:28px;flex-wrap:wrap;align-items:center}}
.trust-item{{display:flex;align-items:center;gap:6px;font-size:12px;font-weight:500;letter-spacing:.2px}}
.trust-item .t-icon{{font-size:15px}}

/* ── CONTAINER ── */
.med-container{{max-width:860px;margin:24px auto;padding:0 16px}}
.med-card{{background:#fff;border-radius:6px;box-shadow:0 2px 20px rgba(10,48,96,.08);overflow:hidden}}

/* ── ARTICLE HEADER ── */
.med-header{{padding:36px 44px 0}}
.med-source-bar{{display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap}}
.med-source-badge{{font-size:11px;font-weight:700;color:#0a3060;text-transform:uppercase;letter-spacing:1.5px;border:1px solid #c8d6e8;padding:4px 12px;border-radius:3px}}
.med-sponsored{{font-size:11px;color:#aaa;font-weight:400}}
.med-reviewed{{display:flex;align-items:center;gap:5px;font-size:11px;color:#059669;font-weight:600;background:#ecfdf5;padding:4px 10px;border-radius:3px;margin-left:auto}}
h1{{font-family:'IBM Plex Serif',serif;font-weight:700;font-size:31px;line-height:1.22;margin-bottom:10px;color:#0a1a3a}}
.med-deck{{font-size:16px;color:#4a5568;line-height:1.58;margin-bottom:22px;font-style:italic}}

/* ── AUTHOR CARD ── */
.author-card{{display:flex;align-items:center;gap:16px;padding:16px 0;border-top:2px solid #0a3060;border-bottom:1px solid #dde5f0;margin-bottom:0;flex-wrap:wrap}}
.author-avatar-wrap{{position:relative;flex-shrink:0}}
.author-avatar{{width:54px;height:54px;border-radius:50%;background:#0a3060;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:20px;font-family:'IBM Plex Serif',serif}}
.author-verified{{position:absolute;bottom:-2px;right:-2px;background:#059669;border-radius:50%;width:18px;height:18px;display:flex;align-items:center;justify-content:center;font-size:10px;color:#fff;border:2px solid #fff}}
.author-info .a-name{{font-weight:700;font-size:15px;color:#0a1a3a}}
.author-info .a-creds{{font-size:12px;color:#6b7280;margin-top:1px}}
.author-info .a-date{{font-size:11px;color:#aaa;margin-top:2px}}
.author-info .a-badge{{display:inline-flex;align-items:center;gap:4px;background:#eff6ff;color:#1d4ed8;font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px;margin-top:4px;text-transform:uppercase;letter-spacing:.5px}}

/* ── ARTICLE BODY ── */
.med-body{{padding:28px 44px 44px}}
.med-h2{{font-family:'IBM Plex Serif',serif;font-weight:600;font-size:23px;line-height:1.28;margin:34px 0 13px;color:#0a1a3a}}
p{{margin-bottom:14px;color:#2d3748;font-size:17px;line-height:1.76}}
strong{{color:#0a1a3a;font-weight:600}}
ul,ol{{padding-left:24px;margin-bottom:16px}}
li{{margin-bottom:8px;font-size:16px;line-height:1.7;color:#2d3748}}
blockquote{{border-left:4px solid #0a3060;margin:22px 0;padding:14px 20px;background:#f0f5fb;font-family:'IBM Plex Serif',serif;font-style:italic;color:#2d4a6a;font-size:17px;line-height:1.65;border-radius:0 4px 4px 0}}

/* ── MEDICAL IMAGE ── */
.med-figure{{margin:22px -44px}}
.med-figure img{{width:100%;display:block}}
.med-figure figcaption{{padding:8px 44px;font-size:12px;color:#6b7280;font-style:italic;background:#f8fafd;border-bottom:1px solid #e2e8f0}}

/* ── PLACEHOLDER ── */
.placeholder{{background:#f0f4f9;border:1px dashed #b8c8dc;border-radius:6px;padding:36px 20px;text-align:center;margin:16px 0}}
.tbadge{{display:inline-block;background:#0a3060;color:#fff;font-size:10px;padding:3px 10px;border-radius:3px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700;font-family:sans-serif}}
.ph-desc{{color:#8fa3bc;font-size:13px;font-style:italic;margin-top:4px}}

/* ── DATA VIZ ── */
.data-viz{{padding:24px 20px}}
.viz-bars{{margin:12px 0}}
.viz-bar-row{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
.viz-label{{font-size:13px;color:#4a5568;min-width:54px;font-weight:600;font-family:'IBM Plex Sans',sans-serif}}
.viz-bar-bg{{flex:1;background:#e8ecf0;border-radius:4px;height:20px;overflow:hidden}}
.viz-bar-fill{{height:100%;border-radius:4px;transition:width .6s ease}}
.viz-pct{{font-size:13px;font-weight:700;color:#0a1a3a;min-width:36px;text-align:right}}

/* ── CITATION BOX ── */
.study-cite{{display:flex;gap:14px;background:#f0f5fb;border:1px solid #c8d6e8;border-radius:6px;padding:14px 18px;margin:18px 0;align-items:flex-start}}
.cite-num{{font-family:'IBM Plex Serif',serif;font-weight:700;font-size:16px;color:#0a3060;flex-shrink:0;min-width:28px}}
.cite-journal{{font-weight:600;font-size:14px;color:#0a1a3a;margin-bottom:2px}}
.cite-ref{{font-size:12px;color:#6b7280}}

/* ── STATS ── */
.stat-row{{display:flex;gap:12px;margin:20px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:130px;background:#f0f5fb;border:1px solid #c8d6e8;border-radius:6px;padding:16px;text-align:center}}
.stat-box .stat-num{{font-family:'IBM Plex Serif',serif;font-weight:700;font-size:28px;color:#0a3060;display:block;line-height:1}}
.stat-box .stat-label{{font-size:12px;color:#6b7280;margin-top:6px;font-weight:500}}

/* ── TABLE ── */
.comparison-table{{display:block;overflow-x:auto;-webkit-overflow-scrolling:touch;width:100%;border-collapse:collapse;margin:20px 0;font-size:15px}}
.comparison-table th{{background:#0a1a3a;color:#fff;padding:12px 14px;text-align:left;font-size:12px;font-weight:600;letter-spacing:.5px;text-transform:uppercase}}
.comparison-table tr:nth-child(even) td{{background:#f8fafd}}
.comparison-table td{{padding:11px 14px;border-bottom:1px solid #e2e8f0;color:#2d3748}}
.comparison-table .good{{color:#059669;font-weight:700}}
.comparison-table .bad{{color:#dc2626;font-weight:700}}

/* ── TESTIMONIAL ── */
.testimonial{{background:#f0f5fb;border-left:4px solid #0a3060;border-radius:0 8px 8px 0;padding:16px 20px;margin:18px 0}}
.testimonial .quote{{font-family:'IBM Plex Serif',serif;font-size:16px;line-height:1.65;color:#2d4a6a;font-style:italic;margin-bottom:6px}}
.testimonial .attribution{{font-size:12px;color:#6b7280;font-weight:600}}

/* ── WARNING ── */
.warning-box{{background:#fef3c7;border:1px solid #fbbf24;border-radius:6px;padding:14px 18px;margin:14px 0;font-size:16px;display:flex;gap:10px;color:#78350f}}
.step{{margin-bottom:14px;display:flex;gap:12px;align-items:flex-start}}
.step-num{{width:28px;height:28px;background:#0a3060;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0;margin-top:2px;font-family:sans-serif}}
.step .step-title{{font-weight:600;font-size:16px;margin-bottom:3px;color:#0a1a3a}}
.step p{{font-size:16px;margin-bottom:0;color:#2d3748}}
.tip{{background:#f0f5fb;border-left:3px solid #0a3060;padding:12px 16px;margin:14px 0;font-size:16px;border-radius:0 4px 4px 0;color:#2d3748}}

/* ── OFFER BOX (clinical recommendation) ── */
.offer-box{{background:#fff;border:2px solid #0a3060;border-radius:8px;overflow:hidden;margin:36px 0}}
.offer-box-header{{background:#0a3060;color:#fff;padding:14px 24px;display:flex;align-items:center;gap:10px}}
.offer-header-icon{{font-size:20px}}
.offer-header-text{{font-weight:700;font-size:15px;text-transform:uppercase;letter-spacing:.5px}}
.offer-box-body{{padding:26px 28px}}
.offer-box-body h2{{font-family:'IBM Plex Serif',serif;font-weight:600;font-size:21px;color:#0a1a3a;margin-bottom:10px}}
.offer-product-img{{width:100%;border-radius:6px;margin:12px 0 18px;display:block}}
.clinical-checks{{margin:16px 0}}
.clinical-check{{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px;font-size:15px;color:#2d3748}}
.check-icon{{width:20px;height:20px;background:#059669;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;color:#fff;font-size:12px;font-weight:700}}
.offer-cta{{display:block;width:100%;padding:17px;background:#0a3060;color:#fff;text-align:center;font-size:17px;font-weight:700;border-radius:6px;text-decoration:none;margin:18px 0 10px;transition:background .2s;font-family:'IBM Plex Sans',sans-serif;letter-spacing:.2px}}
.offer-cta:hover{{background:#062244}}
.offer-trust-row{{display:flex;flex-wrap:wrap;gap:10px;margin-top:10px}}
.offer-trust-item{{font-size:12px;color:#6b7280;display:flex;align-items:center;gap:5px}}
.cta-body-html{{font-size:15px;color:#4a5568;line-height:1.6;margin:10px 0}}

/* ── STICKY FOOTER ── */
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#0a3060;padding:13px 20px;text-align:center;z-index:100}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:700;font-size:15px}}

/* ── RESPONSIVE ── */
@media(max-width:760px){{
.med-container{{padding:0;margin:0}}
.med-card{{border-radius:0;box-shadow:none}}
.med-header{{padding:24px 16px 0}}
.med-body{{padding:20px 16px 32px}}
.med-figure{{margin:18px -16px}}
.med-figure figcaption{{padding:8px 16px}}
h1{{font-size:25px}}
.med-h2{{font-size:20px}}
.trust-topbar-inner{{gap:12px;justify-content:flex-start;overflow-x:auto;flex-wrap:nowrap;padding-bottom:2px}}
.trust-item{{white-space:nowrap}}
.author-card{{gap:12px}}
.offer-box-body{{padding:18px 16px}}
}}
</style>
</head>
<body>

<div class="med-container">
  <div class="med-card">

    <!-- ARTICLE HEADER -->
    <div class="med-header">
      <div class="med-source-bar">
        <span class="med-source-badge">Medical Review</span>
        <span class="med-sponsored">· Sponsored Content</span>
        <span class="med-reviewed">✓ Medically Reviewed</span>
      </div>
      <h1>{headline}</h1>
      {"<p class='med-deck'>" + subheadline + "</p>" if subheadline else ""}

      <!-- DOCTOR AUTHOR CARD -->
      <div class="author-card">
        <div class="author-avatar-wrap">
          <div class="author-avatar">{author_initial}</div>
          <div class="author-verified">✓</div>
        </div>
        <div class="author-info">
          <div class="a-name">{author_name}</div>
          <div class="a-creds">Board-Certified Specialist · 25+ Years Clinical Experience</div>
          <div class="a-date">Published {today} · Updated Recently</div>
          <div class="a-badge">✓ Verified Medical Author</div>
        </div>
      </div>
    </div><!-- /med-header -->

    <!-- ARTICLE BODY -->
    <div class="med-body">

      {article_body}

      <!-- RECOMMENDATION OFFER BOX -->
      <div class="offer-box">
        <div class="offer-box-header">
          <span class="offer-header-icon">⚕️</span>
          <span class="offer-header-text">Clinical Recommendation</span>
        </div>
        <div class="offer-box-body">
          <h2>{tx.get("offer_title","My Professional Recommendation")}</h2>
          {offer_img_html}
          <p style="font-size:16px;color:#4a5568;margin-bottom:14px;line-height:1.65">{tx.get("offer_desc","")}</p>
          <div class="clinical-checks">
            <div class="clinical-check"><span class="check-icon">✓</span><span>{tx.get("badge1","Clinically Tested")}</span></div>
            <div class="clinical-check"><span class="check-icon">✓</span><span>{tx.get("badge2","Doctor Approved")}</span></div>
            {"<div class='clinical-check'><span class='check-icon'>✓</span><span>" + tx.get("badge3","") + "</span></div>" if tx.get("badge3") else ""}
          </div>
          <div class="cta-body-html">{cta_body}</div>
          <a href="{product_url}" class="offer-cta">{tx.get("cta","Get Clinical-Grade Support →")}</a>
          <div class="offer-trust-row">
            <span class="offer-trust-item">🔒 Secure Checkout</span>
            <span class="offer-trust-item">↩ 30-Day Guarantee</span>
            <span class="offer-trust-item">🚚 Free Shipping</span>
          </div>
        </div>
      </div>

    </div><!-- /med-body -->
  </div><!-- /med-card -->
</div><!-- /med-container -->

<div class="sticky-footer">
  <a href="{product_url}">{tx.get("cta_footer","Get the Clinically-Recommended Solution →")}</a>
</div>
</body>
</html>'''
