"""News Report template — investigative newspaper look, navy header, red breaking banner, article card layout."""
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

        # Image BEFORE heading with caption
        if img_url:
            caption = placeholder.get("description", "") or heading
            parts.append(f'''<figure class="art-figure">
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
            parts.append(f'<h2 class="sec-head">{heading}</h2>')
        if body_html:
            parts.append(f'<div class="art-body">{body_html}</div>')

        if parts:
            body_parts.append("\n".join(parts))

    article_body = "\n\n".join(body_parts)
    cta_body = cta_section.get("body_html", "") if cta_section else ""

    initials = "".join(w[0].upper() for w in author_name.split()[:2]) if author_name else "N"

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
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;0,8..60,900;1,8..60,400;1,8..60,600&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Source Sans 3',sans-serif;background:#e8e5de;color:#1a1a1a;font-size:18px;line-height:1.75;padding-bottom:68px}}

/* TOP NAV */
.top-nav{{background:#0d1f38;color:#fff;height:50px;display:flex;align-items:center;justify-content:space-between;padding:0 24px;position:sticky;top:0;z-index:300;box-shadow:0 2px 12px rgba(0,0,0,.35)}}
.pub-name{{font-family:'Source Serif 4',serif;font-weight:900;font-size:21px;letter-spacing:-0.5px;color:#fff;text-decoration:none}}
.nav-links{{display:flex;gap:20px;list-style:none;font-size:11px;text-transform:uppercase;letter-spacing:.8px}}
.nav-links a{{color:#9ab;text-decoration:none}}
.nav-links a:hover{{color:#fff}}
.nav-date{{font-size:11px;color:#9ab;white-space:nowrap}}

/* BREAKING BANNER */
.breaking-banner{{background:#c8111a;color:#fff;text-align:center;padding:9px 16px;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;gap:12px;flex-wrap:wrap}}
.brk-pill{{background:#fff;color:#c8111a;font-size:10px;font-weight:900;padding:3px 10px;text-transform:uppercase;letter-spacing:1.2px;border-radius:2px}}
.brk-text{{animation:blink 2.8s ease-in-out infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.7}}}}

/* PAGE WRAP */
.page-wrap{{max-width:760px;margin:28px auto;padding:0 16px}}

/* ARTICLE CARD */
.article-card{{background:#fff;box-shadow:0 2px 28px rgba(0,0,0,.12);border-radius:2px}}
.art-header{{padding:32px 40px 0}}
.cat-badge{{display:inline-block;background:#c8111a;color:#fff;font-size:10px;font-weight:900;padding:4px 12px;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:16px}}
h1{{font-family:'Source Serif 4',serif;font-weight:900;font-size:36px;line-height:1.15;color:#090909;margin-bottom:14px}}
.art-subtitle{{font-family:'Source Serif 4',serif;font-size:19px;color:#555;line-height:1.5;margin-bottom:20px;font-style:italic}}

/* BYLINE */
.byline{{display:flex;align-items:center;gap:12px;padding:14px 0;flex-wrap:wrap}}
.auth-avatar{{width:44px;height:44px;border-radius:50%;background:#0d1f38;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;flex-shrink:0}}
.byline-info .auth-name{{font-weight:700;font-size:14px;color:#0d1f38}}
.byline-info .by-meta{{font-size:12px;color:#888;margin-top:2px}}
.views-badge{{color:#c8111a;font-weight:700}}

/* SHARE BAR */
.share-bar{{display:flex;gap:8px;align-items:center;padding:12px 0;border-top:1px solid #eee;border-bottom:3px double #ddd;margin-bottom:20px;flex-wrap:wrap}}
.share-lbl{{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#888;font-weight:700}}
.s-btn{{display:inline-flex;align-items:center;gap:4px;padding:5px 12px;border-radius:2px;font-size:12px;font-weight:700;cursor:default}}
.s-fb{{background:#1877f2;color:#fff}}
.s-tw{{background:#111;color:#fff}}
.s-rd{{background:#ff4500;color:#fff}}
.s-em{{background:#ea4335;color:#fff}}

/* CONTENT */
.art-content{{padding:4px 40px 40px}}
.sec-head{{font-family:'Source Serif 4',serif;font-weight:700;font-size:24px;line-height:1.3;color:#090909;margin:30px 0 14px;padding-left:14px;border-left:4px solid #c8111a}}
.art-body p{{font-size:18px;line-height:1.78;margin-bottom:18px;color:#222}}
.art-body strong{{color:#000}}
.art-body blockquote{{border-left:3px solid #c8111a;margin:20px 0;padding:12px 20px;background:#fff8f8;font-style:italic;color:#444;font-family:'Source Serif 4',serif;font-size:17px;border-radius:0 4px 4px 0}}
.art-body ul,.art-body ol{{padding-left:28px;margin-bottom:16px}}
.art-body li{{margin-bottom:6px;line-height:1.6}}

/* STAT ROW */
.stat-row{{display:flex;gap:12px;margin:20px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:130px;background:#f8f5f0;border:1px solid #e0d8cc;border-radius:4px;padding:14px;text-align:center}}
.stat-box .stat-num{{font-family:'Source Serif 4',serif;font-weight:900;font-size:28px;color:#c8111a;display:block}}
.stat-box .stat-label{{font-size:13px;color:#666;margin-top:4px}}

/* COMPARISON TABLE */
.comparison-table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:16px}}
.comparison-table th{{background:#0d1f38;color:#fff;padding:12px 14px;text-align:left;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}}
.comparison-table td{{padding:11px 14px;border-bottom:1px solid #eee}}
.comparison-table .good{{color:#1a8f3a;font-weight:700}}
.comparison-table .bad{{color:#c8111a;font-weight:700}}

/* TESTIMONIAL / WARNING */
.testimonial{{background:#f8f5f0;border-left:4px solid #c8111a;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0}}
.testimonial .quote{{font-size:17px;line-height:1.65;color:#333;font-style:italic;margin-bottom:6px}}
.testimonial .attribution{{font-size:13px;color:#888;font-weight:700}}
.warning-box{{background:#fff8e1;border:1px solid #ffe082;border-radius:4px;padding:14px 18px;margin:14px 0;font-size:16px;display:flex;gap:10px}}
.step{{margin-bottom:12px;display:flex;gap:10px;align-items:flex-start}}
.step .step-title{{font-weight:700;font-size:16px;margin-bottom:2px}}
.step p{{font-size:16px;margin-bottom:0}}
.tip{{background:#f8f5f0;border-left:3px solid #c8111a;padding:12px 16px;margin:12px 0;font-size:16px;border-radius:0 4px 4px 0;display:flex;gap:8px}}
.accent{{color:#c8111a}}

/* FIGURES */
.art-figure{{margin:24px 0}}
.art-figure img{{width:100%;display:block;border-radius:2px}}
.art-figure figcaption{{font-size:12px;color:#666;font-style:italic;padding:7px 2px;border-bottom:1px solid #eee;line-height:1.4}}
.video-ph{{background:#111;color:#888;padding:60px 20px;text-align:center;border-radius:4px;margin:24px 0}}
.play-icon{{font-size:48px;color:#fff;opacity:.7;margin:0 0 12px;display:block}}
.video-ph p{{color:#666;font-size:13px}}
.placeholder{{background:#f5f3ee;padding:36px 20px;text-align:center;color:#aaa;border:1px dashed #ccc;border-radius:4px;margin:24px 0;font-size:14px;font-style:italic}}
.tbadge{{display:inline-block;background:#c8111a;color:#fff;font-size:10px;padding:3px 10px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700;border-radius:2px}}

/* OFFER BOX */
.offer-verdict{{background:#f8f5f0;border:2px solid #0d1f38;border-radius:4px;padding:32px;margin:36px 0}}
.verdict-label{{display:inline-block;background:#0d1f38;color:#fff;font-size:10px;font-weight:900;padding:5px 14px;letter-spacing:2px;text-transform:uppercase;margin-bottom:16px}}
.offer-verdict h2{{font-family:'Source Serif 4',serif;font-weight:700;font-size:24px;color:#090909;margin-bottom:12px}}
.offer-verdict p{{font-size:17px;color:#333;margin-bottom:12px}}
.offer-verdict strong{{color:#090909}}
.cta-main{{display:block;width:100%;padding:18px 24px;background:#c8111a;color:#fff;text-align:center;font-size:18px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;text-decoration:none;border-radius:3px;margin:20px 0 12px;transition:background .2s}}
.cta-main:hover{{background:#a30e14}}
.offer-badges{{font-size:13px;color:#666}}
.offer-badges div{{margin-bottom:4px;display:flex;align-items:center;gap:6px}}

/* RELATED */
.related-sec{{padding:28px 40px;background:#f5f3ee;border-top:3px double #ddd}}
.related-sec h3{{font-family:'Source Serif 4',serif;font-size:13px;text-transform:uppercase;letter-spacing:1.5px;color:#888;margin-bottom:16px;font-weight:700}}
.related-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.rel-item{{border-top:2px solid #c8111a;padding-top:10px}}
.rel-cat{{font-size:10px;color:#c8111a;font-weight:700;text-transform:uppercase;letter-spacing:.8px;margin-bottom:4px}}
.rel-title{{font-family:'Source Serif 4',serif;font-size:15px;font-weight:600;line-height:1.3;color:#090909}}

/* STICKY FOOTER */
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#0d1f38;padding:13px 20px;text-align:center;z-index:400;box-shadow:0 -3px 16px rgba(0,0,0,.25)}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:700;font-size:16px}}
.sticky-footer a .arr{{color:#ff8080}}

/* RESPONSIVE */
@media(max-width:740px){{
  .page-wrap{{margin:0;padding:0}}
  .article-card{{border-radius:0}}
  .art-header,.art-content{{padding:18px 16px}}
  .related-sec{{padding:20px 16px}}
  h1{{font-size:26px}}
  .sec-head{{font-size:20px}}
  .top-nav .nav-links{{display:none}}
  .related-grid{{grid-template-columns:1fr}}
  .offer-verdict{{padding:20px 16px}}
}}
</style>
</head>
<body>

<nav class="top-nav">
  <a href="#" class="pub-name">THE DAILY HEALTH REPORT</a>
  <ul class="nav-links">
    <li><a href="#">Health</a></li>
    <li><a href="#">Science</a></li>
    <li><a href="#">Investigations</a></li>
    <li><a href="#">Reviews</a></li>
  </ul>
  <span class="nav-date">{today}</span>
</nav>

<div class="breaking-banner">
  <span class="brk-pill">INVESTIGATION</span>
  <span class="brk-text">⚠️ This report has been independently verified — share before it's removed</span>
</div>

<div class="page-wrap">
  <article class="article-card">
    <div class="art-header">
      <div class="cat-badge">Health Investigation</div>
      <h1>{headline}</h1>
      {"<p class='art-subtitle'>" + subheadline + "</p>" if subheadline else ""}
      <div class="byline">
        <div class="auth-avatar">{initials}</div>
        <div class="byline-info">
          <div class="auth-name">{author_name}</div>
          <div class="by-meta">{today} · 8 min read · <span class="views-badge">2,194,477 views</span></div>
        </div>
      </div>
      <div class="share-bar">
        <span class="share-lbl">Share:</span>
        <span class="s-btn s-fb">f&nbsp;Facebook</span>
        <span class="s-btn s-tw">&#120143;&nbsp;Twitter</span>
        <span class="s-btn s-rd">Reddit</span>
        <span class="s-btn s-em">&#9993;&nbsp;Email</span>
      </div>
    </div>

    <div class="art-content">
      {article_body}

      <div class="offer-verdict">
        <div class="verdict-label">Investigation Verdict</div>
        <h2>{tx["offer_title"]}</h2>
        <p><strong>{product_name}</strong><br>{tx["offer_desc"]}</p>
        {'<img src="' + product_image_url + '" alt="' + product_name + '" style="width:100%;border-radius:3px;margin:12px 0 20px;">' if product_image_url else '<div class="placeholder"><div class="tbadge">' + tx.get("bundle_badge","PRODUCT") + '</div><br>' + tx.get("bundle_desc","Product image") + '</div>'}
        {cta_body}
        <a href="{product_url}" class="cta-main">{tx["cta"]}</a>
        <div class="offer-badges">
          <div>&#10003; {tx["badge1"]}</div>
          <div>&#10003; {tx["badge2"]}</div>
          <div>&#10003; {tx.get("badge3","")}</div>
        </div>
      </div>
    </div>

    <div class="related-sec">
      <h3>Related Investigations</h3>
      <div class="related-grid">
        <div class="rel-item">
          <div class="rel-cat">Health</div>
          <div class="rel-title">Doctors Alarmed as Major Study Reveals Hidden Danger in Common Supplement</div>
        </div>
        <div class="rel-item">
          <div class="rel-cat">Science</div>
          <div class="rel-title">The Sleep Secret 4 Million Americans Are Using — And Why Big Pharma Hates It</div>
        </div>
        <div class="rel-item">
          <div class="rel-cat">Investigations</div>
          <div class="rel-title">Inside the $87B Wellness Industry: Who's Really Profiting From Your Pain?</div>
        </div>
        <div class="rel-item">
          <div class="rel-cat">Reviews</div>
          <div class="rel-title">We Tested 11 "Natural" Pain Relief Products — Here Are the Shocking Results</div>
        </div>
      </div>
    </div>
  </article>
</div>

<div class="sticky-footer">
  <a href="{product_url}">{tx["cta_footer"]} <span class="arr">&#8594;</span></a>
</div>

</body>
</html>'''
