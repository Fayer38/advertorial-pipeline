"""Medical Authority template — clinical blue/white, doctor byline, study citations, IBM Plex fonts."""
from datetime import datetime


def build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang, tx):
    today = datetime.utcnow().strftime("%B %d, %Y")
    headline = content.get("headline", "")
    subheadline = content.get("subheadline", "")

    body_parts = []
    offer_section = None
    cta_section = None
    sec_count = 0

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
            caption = placeholder.get("description", "") or heading
            parts.append(f'''<figure class="med-figure">
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

        if heading:
            parts.append(f'<h2 class="med-h2">{heading}</h2>')
        if body_html:
            parts.append(f'<div class="med-prose">{body_html}</div>')

        # Insert a study citation box every 2 sections
        if sec_count > 0 and sec_count % 2 == 0:
            parts.append(f'''<div class="study-cite">
  <strong>&#128202; Clinical Note:</strong> Research published in peer-reviewed literature supports the efficacy of approaches described in this analysis. Individual results may vary. Consult your healthcare provider before starting any new wellness regimen.
</div>''')

        if parts:
            body_parts.append("\n".join(parts))

        sec_count += 1

    article_body = "\n\n".join(body_parts)
    cta_body = cta_section.get("body_html", "") if cta_section else ""

    doc_initial = author_name[0].upper() if author_name else "D"

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
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'IBM Plex Sans',sans-serif;background:#f0f4f8;color:#1a1a1a;font-size:17px;line-height:1.78;padding-bottom:68px}}

/* TRUST CREDENTIAL BAR */
.trust-bar{{background:#1a3c6e;color:#fff;padding:10px 20px;display:flex;justify-content:center;align-items:center;gap:0;flex-wrap:wrap}}
.trust-item{{display:flex;align-items:center;gap:6px;font-size:12px;font-weight:600;letter-spacing:.2px;padding:4px 16px}}
.trust-item + .trust-item{{border-left:1px solid rgba(255,255,255,.25)}}

/* JOURNAL STRIP */
.journal-strip{{background:#e8f0f8;border-bottom:2px solid #c8d8ec;padding:7px 20px;text-align:center;font-size:12px;color:#1a3c6e;font-weight:600;letter-spacing:.5px;text-transform:uppercase}}

/* PAGE CONTAINER */
.med-container{{max-width:780px;margin:24px auto;background:#fff;border-radius:6px;box-shadow:0 2px 20px rgba(26,60,110,.08);overflow:hidden}}

/* ARTICLE HEADER */
.med-header{{padding:36px 44px 0}}
.source-label{{font-size:11px;color:#1a3c6e;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:14px}}
h1{{font-family:'IBM Plex Serif',serif;font-weight:700;font-size:31px;line-height:1.2;color:#0a2540;margin-bottom:12px}}
.med-subtitle{{font-family:'IBM Plex Serif',serif;font-size:17px;color:#4a6080;line-height:1.55;margin-bottom:20px}}

/* DOCTOR AUTHOR CARD */
.author-card{{display:flex;align-items:center;gap:18px;padding:18px 0;border-top:1px solid #d8e8f4;border-bottom:2px solid #1a3c6e;margin-bottom:4px}}
.doc-avatar{{width:56px;height:56px;border-radius:50%;background:#1a3c6e;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:20px;flex-shrink:0;font-family:'IBM Plex Sans',sans-serif}}
.author-details .doc-name{{font-weight:700;font-size:16px;color:#0a2540;margin-bottom:2px}}
.author-details .doc-creds{{font-size:12px;color:#4a6080;margin-bottom:2px;font-style:italic}}
.author-details .doc-date{{font-size:11px;color:#9ab0c8}}

/* CONTENT */
.med-content{{padding:30px 44px 44px}}

.med-h2{{font-family:'IBM Plex Serif',serif;font-weight:600;font-size:22px;line-height:1.3;color:#0a2540;margin:32px 0 13px;padding-left:14px;border-left:3px solid #1a3c6e}}

.med-prose p{{font-size:17px;line-height:1.78;margin-bottom:15px;color:#2a3a4a}}
.med-prose strong{{color:#0a2540}}
.med-prose em{{color:#4a6080;font-style:italic}}
.med-prose blockquote{{background:#e8f4f8;border-left:3px solid #1a3c6e;margin:18px 0;padding:14px 18px;font-size:15px;color:#2a3a4a;font-style:italic;border-radius:0 4px 4px 0}}
.med-prose ul,.med-prose ol{{padding-left:26px;margin-bottom:15px}}
.med-prose li{{margin-bottom:6px;line-height:1.65}}

/* STUDY CITATION BOX */
.study-cite{{background:#e8f4f8;border-left:4px solid #1a3c6e;border-radius:0 6px 6px 0;padding:14px 18px;margin:18px 0;font-size:14px;color:#2a3a4a;line-height:1.6}}
.study-cite strong{{color:#1a3c6e;font-size:13px}}

/* FIGURES */
.med-figure{{margin:22px 0}}
.med-figure img{{width:100%;display:block;border-radius:4px;border:1px solid #d8e8f4}}
.med-figure figcaption{{font-size:12px;color:#6a8aa0;font-style:italic;padding:7px 4px;line-height:1.4}}
.video-ph{{background:#0a2540;color:#4a6080;padding:56px 20px;text-align:center;border-radius:4px;margin:22px 0}}
.play-icon{{font-size:42px;color:#fff;opacity:.6;display:block;margin:0 0 12px}}
.video-ph p{{font-size:13px;color:#4a6080}}
.placeholder{{background:#f0f4f8;padding:36px 20px;text-align:center;color:#9ab0c8;border:1px dashed #c8d8ec;border-radius:4px;margin:22px 0;font-size:14px;font-style:italic}}
.tbadge{{display:inline-block;background:#1a3c6e;color:#fff;font-size:10px;padding:3px 10px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700;border-radius:3px}}

/* STAT ROW */
.stat-row{{display:flex;gap:12px;margin:20px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:130px;background:#f0f4f8;border:1px solid #c8d8ec;border-radius:6px;padding:14px;text-align:center}}
.stat-box .stat-num{{font-family:'IBM Plex Serif',serif;font-weight:700;font-size:28px;color:#1a3c6e;display:block}}
.stat-box .stat-label{{font-size:13px;color:#6a8aa0;margin-top:4px}}

/* COMPARISON */
.comparison-table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:15px}}
.comparison-table th{{background:#0a2540;color:#fff;padding:12px 14px;text-align:left;font-size:12px;font-weight:600;letter-spacing:.3px}}
.comparison-table td{{padding:11px 14px;border-bottom:1px solid #e8ecf0}}
.comparison-table .good{{color:#1a7a3c;font-weight:700}}
.comparison-table .bad{{color:#b02020;font-weight:700}}

/* TESTIMONIAL */
.testimonial{{background:#f0f4f8;border-left:3px solid #1a3c6e;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0}}
.testimonial .quote{{font-size:16px;line-height:1.65;color:#2a3a4a;font-style:italic;margin-bottom:6px}}
.testimonial .attribution{{font-size:12px;color:#6a8aa0;font-weight:600}}
.warning-box{{background:#fef3c7;border:1px solid #fbbf24;border-radius:4px;padding:14px 18px;margin:14px 0;font-size:15px;display:flex;gap:10px}}
.step{{margin-bottom:12px;display:flex;gap:10px;align-items:flex-start}}
.step .step-title{{font-weight:600;font-size:16px;margin-bottom:2px;color:#0a2540}}
.step p{{font-size:16px;margin-bottom:0}}
.tip{{background:#f0f4f8;border-left:3px solid #1a3c6e;padding:12px 16px;margin:12px 0;font-size:15px;border-radius:0 4px 4px 0;display:flex;gap:8px}}
.accent{{color:#1a3c6e;font-weight:600}}

/* CLINICAL RECOMMENDATION OFFER BOX */
.clinical-rec{{border:2px solid #1a3c6e;border-radius:8px;padding:32px;margin:36px 0;background:#f0f4f8}}
.rec-header{{display:flex;align-items:center;gap:12px;margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid #c8d8ec}}
.rec-badge{{background:#1a3c6e;color:#fff;font-size:10px;font-weight:700;padding:5px 14px;text-transform:uppercase;letter-spacing:1.5px;border-radius:3px;white-space:nowrap}}
.rec-title-text{{font-family:'IBM Plex Serif',serif;font-weight:700;font-size:18px;color:#0a2540}}
.clinical-rec h2{{font-family:'IBM Plex Serif',serif;font-weight:700;font-size:22px;color:#0a2540;margin-bottom:12px}}
.clinical-rec p{{font-size:16px;color:#2a3a4a;margin-bottom:12px}}
.clinical-rec strong{{color:#0a2540}}
.rec-checks{{list-style:none;margin:12px 0 20px;padding:0}}
.rec-checks li{{display:flex;align-items:flex-start;gap:10px;font-size:15px;color:#2a3a4a;margin-bottom:8px}}
.rec-checks li::before{{content:"&#10003;";color:#1a7a3c;font-weight:700;font-size:16px;flex-shrink:0}}
.cta-clinical{{display:block;width:100%;padding:17px 24px;background:#1a3c6e;color:#fff;text-align:center;font-family:'IBM Plex Sans',sans-serif;font-size:17px;font-weight:700;text-decoration:none;border-radius:5px;margin:16px 0 12px;transition:background .2s;letter-spacing:.2px}}
.cta-clinical:hover{{background:#0f2a52}}
.offer-badges{{font-size:13px;color:#6a8aa0}}
.offer-badges div{{margin-bottom:4px;display:flex;align-items:center;gap:6px}}

/* STICKY FOOTER */
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#1a3c6e;padding:13px 20px;text-align:center;z-index:300}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:700;font-size:16px;font-family:'IBM Plex Sans',sans-serif}}

/* RESPONSIVE */
@media(max-width:780px){{
  .med-container{{margin:0;border-radius:0}}
  .med-header,.med-content{{padding:20px 18px}}
  h1{{font-size:24px}}
  .med-h2{{font-size:19px}}
  .trust-bar{{gap:0}}
  .trust-item{{padding:4px 10px;font-size:11px}}
  .clinical-rec{{padding:20px 16px}}
  .author-card{{gap:12px}}
}}
</style>
</head>
<body>

<div class="trust-bar">
  <div class="trust-item">&#128300; Peer-Reviewed</div>
  <div class="trust-item">&#128104;&#8205;&#9877;&#65039; Doctor-Verified</div>
  <div class="trust-item">&#10003; Evidence-Based</div>
  <div class="trust-item">&#127973; FDA-Registered Facility</div>
</div>
<div class="journal-strip">Medical Review &nbsp;|&nbsp; Sponsored Content &nbsp;|&nbsp; Medically Reviewed</div>

<div class="med-container">
  <div class="med-header">
    <div class="source-label">Clinical Analysis &middot; {today}</div>
    <h1>{headline}</h1>
    {"<p class='med-subtitle'>" + subheadline + "</p>" if subheadline else ""}
    <div class="author-card">
      <div class="doc-avatar">{doc_initial}</div>
      <div class="author-details">
        <div class="doc-name">{author_name}</div>
        <div class="doc-creds">Board-Certified Specialist &middot; 25+ Years Clinical Experience</div>
        <div class="doc-date">Published {today} &nbsp;&middot;&nbsp; Medically Reviewed &amp; Verified</div>
      </div>
    </div>
  </div>

  <div class="med-content">
    {article_body}

    <div class="clinical-rec">
      <div class="rec-header">
        <span class="rec-badge">Clinical Recommendation</span>
        <span class="rec-title-text">Based on Available Evidence</span>
      </div>
      <h2>{tx["offer_title"]}</h2>
      <p>{tx["offer_desc"]}</p>
      {'<img src="' + product_image_url + '" alt="' + product_name + '" style="width:100%;border-radius:4px;margin:12px 0 16px;border:1px solid #c8d8ec;">' if product_image_url else '<div class="placeholder"><div class="tbadge">' + tx.get("bundle_badge","PRODUCT") + '</div><br>' + tx.get("bundle_desc","Product image") + '</div>'}
      {cta_body}
      <ul class="rec-checks">
        <li>{tx["badge1"]}</li>
        <li>{tx["badge2"]}</li>
        <li>{tx.get("badge3","Clinically formulated for optimal results")}</li>
      </ul>
      <a href="{product_url}" class="cta-clinical">{tx["cta"]}</a>
      <div class="offer-badges">
        <div>&#128274; Secure &amp; Confidential</div>
        <div>&#128200; Satisfaction Guarantee</div>
      </div>
    </div>
  </div>
</div>

<div class="sticky-footer">
  <a href="{product_url}">{tx["cta_footer"]}</a>
</div>

</body>
</html>'''
