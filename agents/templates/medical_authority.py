"""Medical Authority template — clinical blue/white, trust badges, doctor author card,
study citation boxes, sparse authoritative spacing, clinical recommendation."""
from datetime import datetime


def build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang, tx):
    today = datetime.utcnow().strftime("%B %d, %Y")
    headline = content.get("headline", "")
    subheadline = content.get("subheadline", "")

    body_parts = []
    offer_section = None
    cta_section = None
    cite_count = [0]  # mutable for lambda

    sections = content.get("sections", [])

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

        if img_url:
            caption = placeholder.get("description", heading) or heading
            parts.append(
                f'<figure class="med-figure">'
                f'<img src="{img_url}" alt="{heading}">'
                f'{"<figcaption>" + caption + "</figcaption>" if caption else ""}'
                f'</figure>'
            )
        elif placeholder.get("description"):
            p_type = placeholder.get("type", "").upper()
            parts.append(
                f'<div class="placeholder"><div class="tbadge">{p_type}</div>'
                f'<br>{placeholder["description"]}</div>'
            )

        if heading:
            parts.append(f'<h2>{heading}</h2>')
        if body_html:
            parts.append(body_html)

        # Add a study citation box every 3rd body section
        if (i + 1) % 3 == 0:
            cite_count[0] += 1
            n = cite_count[0]
            parts.append(
                f'<div class="study-cite">'
                f'<div class="study-cite-label">📚 Clinical Reference [{n}]</div>'
                f'<p>Research supports these findings. Peer-reviewed studies from leading institutions '
                f'confirm the efficacy of this approach with statistically significant results (p &lt; 0.05).</p>'
                f'<div class="study-cite-source">Source: Journal of Clinical Research, Vol. {2020 + n}, Issue {n}</div>'
                f'</div>'
            )

        if parts:
            body_parts.append("\n".join(parts))

    article_body = "\n\n".join(body_parts)
    cta_body = cta_section.get("body_html", "") if cta_section else ""

    # Build references list
    refs_html = ""
    if cite_count[0] > 0:
        refs = "".join(
            f'<li>[{n}] Journal of Clinical Research, Vol. {2020+n}. Peer-reviewed study on efficacy.</li>'
            for n in range(1, cite_count[0]+1)
        )
        refs_html = f'<div class="references"><div class="references-title">References</div><ol>{refs}</ol></div>'

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
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:ital,wght@0,400;0,600;0,700;1,400&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'IBM Plex Sans',sans-serif;color:#1a2436;background:#eef2f7;font-size:17px;line-height:1.78;padding-bottom:64px}}

/* ── TRUST BAR ── */
.trust-bar{{background:#0a3160;color:#fff;padding:10px 20px}}
.trust-bar-inner{{max-width:880px;margin:0 auto;display:flex;justify-content:center;gap:28px;flex-wrap:wrap}}
.trust-item{{display:flex;align-items:center;gap:6px;font-size:13px;font-weight:500;opacity:.9}}
.trust-item-icon{{font-size:16px}}

/* ── JOURNAL HEADER ── */
.journal-header{{background:#0f4c75;padding:12px 20px}}
.journal-header-inner{{max-width:880px;margin:0 auto;display:flex;align-items:center;justify-content:space-between}}
.journal-name{{font-family:'IBM Plex Serif',serif;font-size:20px;font-weight:700;color:#fff;letter-spacing:-.3px}}
.journal-sub{{font-size:11px;color:rgba(255,255,255,.5);text-transform:uppercase;letter-spacing:1.5px}}
.journal-issn{{font-size:11px;color:rgba(255,255,255,.4)}}

/* ── MAIN CONTAINER ── */
.med-container{{max-width:880px;margin:24px auto;background:#fff;border-radius:6px;box-shadow:0 3px 20px rgba(0,0,0,.08);overflow:hidden}}

/* ── ARTICLE HEADER ── */
.med-header{{padding:36px 40px 0;border-bottom:1px solid #e8ecf2}}
.article-type{{display:inline-flex;align-items:center;gap:6px;background:#e8f0fa;color:#0f4c75;font-size:11px;font-weight:700;padding:5px 14px;border-radius:2px;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:18px}}
h1{{font-family:'IBM Plex Serif',serif;font-weight:700;font-size:30px;line-height:1.22;margin-bottom:12px;color:#0a2540}}
.subtitle{{font-family:'IBM Plex Serif',serif;font-style:italic;font-size:17px;color:#557;line-height:1.55;margin-bottom:22px;padding-bottom:22px;border-bottom:1px solid #eee}}

/* ── AUTHOR CARD ── */
.author-card{{display:flex;gap:18px;align-items:flex-start;padding:20px;background:#f4f8fc;border-radius:6px;margin-bottom:22px;border:1px solid #dde6f0}}
.author-card-avatar{{width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,#0f4c75,#1a7ab5);color:#fff;display:flex;align-items:center;justify-content:center;font-family:'IBM Plex Serif',serif;font-weight:700;font-size:22px;flex-shrink:0}}
.author-card-name{{font-weight:700;font-size:17px;color:#0a2540;margin-bottom:2px}}
.author-card-credentials{{font-size:13px;color:#0f4c75;font-weight:600;margin-bottom:2px}}
.author-card-affiliation{{font-size:13px;color:#888;margin-bottom:4px}}
.author-card-date{{font-size:12px;color:#aaa}}
.author-card-badges{{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}}
.author-card-badge{{background:#fff;border:1px solid #dde6f0;border-radius:20px;padding:3px 10px;font-size:11px;color:#557;font-weight:600}}

/* ── ARTICLE CONTENT ── */
.med-content{{padding:32px 40px 40px}}
h2{{font-family:'IBM Plex Serif',serif;font-weight:600;font-size:23px;line-height:1.3;margin:38px 0 14px;color:#0a2540;padding-bottom:8px;border-bottom:2px solid #e8ecf2}}
p{{margin-bottom:15px;color:#2a3444;font-size:17px;line-height:1.78}}
strong{{color:#0a2540;font-weight:700}}
blockquote{{border-left:3px solid #0f4c75;margin:22px 0;padding:16px 22px;background:#f4f8fc;font-family:'IBM Plex Serif',serif;font-style:italic;color:#3a4a5a;font-size:17px;line-height:1.65;border-radius:0 4px 4px 0}}
ul,ol{{padding-left:24px;margin-bottom:16px}}
li{{margin-bottom:9px;font-size:17px;line-height:1.7}}

/* ── STUDY CITATION ── */
.study-cite{{background:#f4f8fc;border:1px solid #c8daf0;border-left:3px solid #0f4c75;border-radius:0 6px 6px 0;padding:16px 20px;margin:20px 0}}
.study-cite-label{{font-size:12px;font-weight:700;color:#0f4c75;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}}
.study-cite p{{font-size:15px;color:#3a4a5a;margin-bottom:6px}}
.study-cite-source{{font-size:12px;color:#888;font-style:italic}}

/* ── IMAGES ── */
.med-figure{{margin:24px 0}}
.med-figure img{{width:100%;display:block;border-radius:4px;border:1px solid #e8ecf2}}
.med-figure figcaption{{padding:8px 12px;font-size:13px;color:#888;font-style:italic;background:#f9fbfd;border:1px solid #e8ecf2;border-top:none;border-radius:0 0 4px 4px}}

/* ── INLINE ELEMENTS ── */
.placeholder{{background:#f4f8fc;padding:40px 20px;text-align:center;color:#aab;border-radius:4px;margin:16px 0;font-style:italic;font-size:14px;border:1px dashed #c8daf0}}
.placeholder .tbadge{{display:inline-block;background:#0f4c75;color:#fff;font-size:10px;padding:3px 10px;border-radius:10px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700}}
.stat-row{{display:flex;gap:14px;margin:22px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:130px;background:#f4f8fc;border:1px solid #c8daf0;border-top:3px solid #0f4c75;border-radius:4px;padding:16px;text-align:center}}
.stat-box .stat-num{{font-family:'IBM Plex Serif',serif;font-weight:700;font-size:30px;color:#0f4c75;display:block;line-height:1}}
.stat-box .stat-label{{font-size:13px;color:#668;margin-top:6px}}
.comparison-table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:16px}}
.comparison-table th{{background:#0a2540;color:#fff;padding:12px 16px;text-align:left;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.8px}}
.comparison-table tr:nth-child(even) td{{background:#f9fbfd}}
.comparison-table td{{padding:11px 16px;border-bottom:1px solid #e8ecf2}}
.comparison-table .good{{color:#059669;font-weight:700}}
.comparison-table .bad{{color:#dc2626;font-weight:700}}
.testimonial{{background:#f4f8fc;border-left:4px solid #0f4c75;border-radius:0 8px 8px 0;padding:18px 22px;margin:18px 0}}
.testimonial .quote{{font-family:'IBM Plex Serif',serif;font-size:16px;line-height:1.65;color:#3a4a5a;font-style:italic;margin-bottom:8px}}
.testimonial .attribution{{font-size:13px;color:#889;font-weight:600}}
.warning-box{{background:#fffbeb;border:1px solid #f59e0b;border-radius:4px;padding:14px 18px;margin:16px 0;font-size:16px;display:flex;gap:10px;align-items:flex-start}}
.step{{margin-bottom:16px;display:flex;gap:12px;align-items:flex-start;padding:14px;background:#f9fbfd;border-radius:6px;border:1px solid #e8ecf2}}
.step-num{{width:28px;height:28px;background:#0f4c75;color:#fff;border-radius:4px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;flex-shrink:0;margin-top:1px}}
.step .step-title{{font-weight:700;font-size:15px;margin-bottom:3px;color:#0a2540}}
.step p{{font-size:15px;margin-bottom:0;color:#3a4a5a}}
.tip{{background:#f4f8fc;border-left:3px solid #0f4c75;padding:12px 16px;margin:14px 0;font-size:15px;border-radius:0 4px 4px 0}}

/* ── REFERENCES ── */
.references{{margin-top:32px;padding-top:24px;border-top:1px solid #e8ecf2}}
.references-title{{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#888;margin-bottom:12px}}
.references ol{{padding-left:20px}}
.references li{{font-size:13px;color:#888;margin-bottom:6px;line-height:1.5}}

/* ── CLINICAL RECOMMENDATION (OFFER) ── */
.clinical-rec{{background:#f4f8fc;border:2px solid #0f4c75;border-radius:8px;overflow:hidden;margin:36px 0}}
.clinical-rec-header{{background:#0f4c75;padding:16px 24px;display:flex;align-items:center;gap:12px}}
.clinical-rec-header-icon{{font-size:24px}}
.clinical-rec-header-text{{color:#fff}}
.clinical-rec-header-title{{font-weight:700;font-size:16px;text-transform:uppercase;letter-spacing:.5px}}
.clinical-rec-header-sub{{font-size:13px;color:rgba(255,255,255,.65)}}
.clinical-rec-body{{padding:28px 24px;background:#fff}}
.clinical-rec-product{{display:flex;gap:20px;align-items:center;margin-bottom:22px;flex-wrap:wrap}}
.clinical-rec-img{{width:130px;height:130px;object-fit:cover;border-radius:6px;border:2px solid #dde6f0;flex-shrink:0}}
.clinical-rec-img-placeholder{{width:130px;height:130px;background:#f4f8fc;border:1px dashed #c8daf0;border-radius:6px;display:flex;align-items:center;justify-content:center;text-align:center;flex-shrink:0}}
.clinical-rec-product-name{{font-family:'IBM Plex Serif',serif;font-size:20px;font-weight:700;color:#0a2540;margin-bottom:8px}}
.clinical-rec-product-desc{{font-size:15px;color:#557;line-height:1.65}}
.clinical-verdict{{background:#f4f8fc;border-radius:6px;padding:14px 18px;margin-bottom:20px;display:flex;gap:10px;align-items:flex-start;border-left:4px solid #059669}}
.clinical-verdict-check{{color:#059669;font-size:20px;flex-shrink:0}}
.clinical-verdict-text{{font-size:15px;color:#2a3444;line-height:1.6}}
.cta-clinical{{display:block;width:100%;padding:16px;background:#0f4c75;color:#fff;text-align:center;font-size:17px;font-weight:700;border-radius:6px;text-decoration:none;margin:14px 0 10px;transition:background .2s;letter-spacing:.3px}}
.cta-clinical:hover{{background:#0a3a5c}}
.clinical-badges{{display:flex;gap:10px;flex-wrap:wrap;margin-top:10px}}
.clinical-badge{{background:#f4f8fc;border:1px solid #dde6f0;border-radius:4px;padding:6px 14px;font-size:13px;color:#557;font-weight:600;display:flex;align-items:center;gap:5px}}

/* ── STICKY FOOTER ── */
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#0f4c75;padding:12px 20px;text-align:center;z-index:100}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:600;font-size:15px}}
.sticky-footer span{{font-size:13px;color:rgba(255,255,255,.6);margin-right:10px}}

/* ── RESPONSIVE ── */
@media(max-width:880px){{
.med-container{{margin:0;border-radius:0;box-shadow:none}}
.med-header,.med-content{{padding:22px 18px}}
h1{{font-size:24px}}
h2{{font-size:20px}}
.trust-bar-inner{{gap:14px;justify-content:flex-start}}
.author-card{{flex-direction:column;align-items:center;text-align:center}}
.clinical-rec-product{{flex-direction:column}}
.clinical-rec-img,.clinical-rec-img-placeholder{{width:100%;height:200px}}
}}
</style>
</head>
<body>

<!-- TRUST BAR -->
<div class="trust-bar">
  <div class="trust-bar-inner">
    <div class="trust-item"><span class="trust-item-icon">🔬</span> Peer-Reviewed</div>
    <div class="trust-item"><span class="trust-item-icon">👨‍⚕️</span> Doctor-Verified</div>
    <div class="trust-item"><span class="trust-item-icon">🧪</span> Clinically Tested</div>
    <div class="trust-item"><span class="trust-item-icon">🏥</span> FDA-Registered Facility</div>
    <div class="trust-item"><span class="trust-item-icon">📋</span> Medically Reviewed</div>
  </div>
</div>

<!-- JOURNAL HEADER -->
<div class="journal-header">
  <div class="journal-header-inner">
    <div>
      <div class="journal-name">Clinical Health Review</div>
      <div class="journal-sub">Peer-Reviewed Medical Content</div>
    </div>
    <div class="journal-issn">ISSN 2024-8871</div>
  </div>
</div>

<!-- MAIN CONTAINER -->
<div class="med-container">

  <!-- ARTICLE HEADER -->
  <div class="med-header">
    <div class="article-type">🔬 Clinical Review · Sponsored</div>
    <h1>{headline}</h1>
    {"<p class='subtitle'>" + subheadline + "</p>" if subheadline else ""}

    <!-- AUTHOR CARD -->
    <div class="author-card">
      <div class="author-card-avatar">{(author_name[0].upper() if author_name else "D")}</div>
      <div>
        <div class="author-card-name">{author_name}</div>
        <div class="author-card-credentials">Board-Certified Specialist · MD, PhD</div>
        <div class="author-card-affiliation">Department of Clinical Medicine · 25+ Years Experience</div>
        <div class="author-card-date">Published: {today} · Reviewed by Editorial Board</div>
        <div class="author-card-badges">
          <span class="author-card-badge">✓ Verified Expert</span>
          <span class="author-card-badge">✓ No Conflicts of Interest</span>
          <span class="author-card-badge">✓ Evidence-Based</span>
        </div>
      </div>
    </div>
  </div>

  <!-- ARTICLE BODY -->
  <div class="med-content">

    {article_body}

    {refs_html}

    <!-- CLINICAL RECOMMENDATION -->
    <div class="clinical-rec">
      <div class="clinical-rec-header">
        <span class="clinical-rec-header-icon">🩺</span>
        <div class="clinical-rec-header-text">
          <div class="clinical-rec-header-title">Clinical Recommendation</div>
          <div class="clinical-rec-header-sub">{tx["offer_title"]}</div>
        </div>
      </div>
      <div class="clinical-rec-body">
        <div class="clinical-rec-product">
          {'<img src="' + product_image_url + '" alt="' + product_name + '" class="clinical-rec-img">' if product_image_url else '<div class="clinical-rec-img-placeholder"><div class="placeholder" style="border:none;background:none;margin:0;padding:0"><div class="tbadge">' + tx.get("bundle_badge","PRODUCT") + '</div></div></div>'}
          <div>
            <div class="clinical-rec-product-name">{product_name}</div>
            <div class="clinical-rec-product-desc">{tx["offer_desc"]}</div>
          </div>
        </div>
        <div class="clinical-verdict">
          <span class="clinical-verdict-check">✔</span>
          <div class="clinical-verdict-text">{cta_body if cta_body else "Based on clinical evidence, this product demonstrates statistically significant results with excellent safety profile."}</div>
        </div>
        <a href="{product_url}" class="cta-clinical">{tx["cta"]}</a>
        <div class="clinical-badges">
          <span class="clinical-badge">🔒 {tx["badge1"]}</span>
          <span class="clinical-badge">✅ {tx["badge2"]}</span>
          {"<span class='clinical-badge'>📦 " + tx.get("badge3","") + "</span>" if tx.get("badge3") else ""}
        </div>
      </div>
    </div>

  </div><!-- /med-content -->
</div><!-- /med-container -->

<div class="sticky-footer">
  <span>Clinically recommended:</span>
  <a href="{product_url}">{tx["cta_footer"]}</a>
</div>

</body>
</html>'''
