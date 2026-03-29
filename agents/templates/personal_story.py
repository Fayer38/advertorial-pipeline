"""Personal Story template — magazine editorial, dark hero, pull quotes, airy white layout."""
from datetime import datetime


def build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang, tx):
    today = datetime.utcnow().strftime("%B %d, %Y")
    headline = content.get("headline", "")
    subheadline = content.get("subheadline", "")

    body_parts = []
    offer_section = None
    cta_section = None
    section_count = 0

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

        # Insert pull quote divider every 3rd section (use heading as pull quote)
        if section_count > 0 and section_count % 3 == 0 and heading:
            parts.append(f'<div class="pull-quote"><p class="pq-text">&#8220;{heading}&#8221;</p></div>')

        if heading:
            parts.append(f'<h2 class="story-h2">{heading}</h2>')
        if body_html:
            parts.append(f'<div class="story-prose">{body_html}</div>')

        # Image after text, full-width
        if img_url:
            caption = placeholder.get("description", "") or ""
            parts.append(f'''<figure class="story-fig">
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

        section_count += 1

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
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;background:#ffffff;color:#111;font-size:18px;line-height:1.8;padding-bottom:68px}}

/* DARK HERO BANNER */
.hero-banner{{background:linear-gradient(160deg,#0a0a0f 0%,#1a1a2a 60%,#0d0d12 100%);color:#fff;padding:72px 24px 60px;text-align:center;position:relative;overflow:hidden}}
.hero-banner::after{{content:'';position:absolute;bottom:0;left:0;right:0;height:60px;background:linear-gradient(to top,#fff,transparent)}}
.hero-tag{{display:inline-block;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);padding:5px 16px;border-radius:20px;font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-bottom:22px;font-family:'Inter',sans-serif;color:rgba(255,255,255,.8)}}
h1{{font-family:'DM Serif Display',serif;font-size:44px;line-height:1.12;max-width:740px;margin:0 auto 16px;color:#fff}}
.hero-sub{{font-size:18px;color:rgba(255,255,255,.65);max-width:600px;margin:0 auto 22px;line-height:1.55}}
.hero-meta{{font-size:12px;color:rgba(255,255,255,.38);letter-spacing:.5px}}

/* STORY CONTENT */
.story-wrap{{max-width:680px;margin:0 auto;padding:48px 24px 40px}}

/* INTRO NAME LINE */
.intro-line{{font-family:'DM Serif Display',serif;font-size:22px;color:#111;margin-bottom:28px;font-style:italic;border-left:3px solid #111;padding-left:18px}}

/* SECTION HEADINGS */
.story-h2{{font-family:'DM Serif Display',serif;font-size:28px;line-height:1.25;color:#111;margin:40px 0 16px}}

/* BODY PROSE */
.story-prose p{{font-size:18px;line-height:1.82;margin-bottom:18px;color:#333}}
.story-prose strong{{color:#111}}
.story-prose em{{color:#555}}
.story-prose blockquote{{border-left:none;margin:24px 0;padding:0;font-family:'DM Serif Display',serif;font-size:22px;color:#111;font-style:italic;text-align:center}}
.story-prose ul,.story-prose ol{{padding-left:28px;margin-bottom:16px}}
.story-prose li{{margin-bottom:7px;line-height:1.7}}

/* PULL QUOTE */
.pull-quote{{padding:36px 0;margin:8px 0 16px;border-top:2px solid #111;border-bottom:2px solid #111;text-align:center}}
.pq-text{{font-family:'DM Serif Display',serif;font-size:26px;line-height:1.35;color:#111;font-style:italic;max-width:560px;margin:0 auto}}

/* FIGURES */
.story-fig{{margin:32px -24px}}
.story-fig img{{width:100%;display:block}}
.story-fig figcaption{{font-size:12px;color:#888;font-style:italic;padding:8px 24px 4px;line-height:1.4}}
.video-ph{{background:#0a0a0f;color:#666;padding:60px 20px;text-align:center;border-radius:4px;margin:28px 0}}
.play-icon{{font-size:48px;color:#fff;opacity:.6;display:block;margin:0 0 12px}}
.video-ph p{{font-size:13px;color:#555}}
.placeholder{{background:#f5f5f5;padding:36px 20px;text-align:center;color:#999;border:1px dashed #ddd;border-radius:6px;margin:24px 0;font-size:14px;font-style:italic}}
.tbadge{{display:inline-block;background:#111;color:#fff;font-size:10px;padding:3px 10px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700;border-radius:10px}}

/* STAT ROW */
.stat-row{{display:flex;gap:14px;margin:24px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:130px;background:#f5f5f5;border-radius:10px;padding:18px;text-align:center}}
.stat-box .stat-num{{font-family:'DM Serif Display',serif;font-size:30px;color:#111;display:block;margin-bottom:4px}}
.stat-box .stat-label{{font-size:13px;color:#777}}

/* COMPARISON */
.comparison-table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:16px}}
.comparison-table th{{background:#111;color:#fff;padding:12px 14px;text-align:left;font-size:13px;font-weight:600}}
.comparison-table td{{padding:11px 14px;border-bottom:1px solid #eee}}
.comparison-table .good{{color:#16a34a;font-weight:700}}
.comparison-table .bad{{color:#dc2626;font-weight:700}}

/* TESTIMONIAL */
.testimonial{{background:#f9f9f9;border-radius:12px;padding:22px 26px;margin:20px 0}}
.testimonial .quote{{font-size:17px;line-height:1.7;color:#333;font-style:italic;margin-bottom:8px}}
.testimonial .attribution{{font-size:13px;color:#888;font-weight:600}}
.warning-box{{background:#fef3c7;border:1px solid #fbbf24;border-radius:8px;padding:14px 18px;margin:14px 0;font-size:16px;display:flex;gap:10px}}
.step{{margin-bottom:12px;display:flex;gap:10px;align-items:flex-start}}
.step .step-title{{font-weight:700;font-size:16px;margin-bottom:2px;color:#111}}
.step p{{font-size:16px;margin-bottom:0}}
.tip{{background:#f9f9f9;border-left:3px solid #111;padding:12px 16px;margin:12px 0;font-size:16px;border-radius:0 6px 6px 0;display:flex;gap:8px}}
.accent{{color:#111;font-weight:600}}

/* SECTION DIVIDER */
.section-divider{{text-align:center;margin:36px 0;color:#ccc;letter-spacing:8px;font-size:18px}}

/* OFFER BOX — narrative style */
.offer-story{{background:#f5f5f5;border-radius:14px;padding:36px;margin:40px 0}}
.offer-story .offer-intro{{font-family:'DM Serif Display',serif;font-size:22px;color:#111;font-style:italic;margin-bottom:18px;line-height:1.35}}
.offer-story h2{{font-family:'DM Serif Display',serif;font-size:26px;color:#111;margin-bottom:12px}}
.offer-story p{{font-size:17px;color:#333;margin-bottom:12px}}
.offer-story strong{{color:#111}}
.cta-story{{display:block;width:100%;padding:18px 24px;background:#111;color:#fff;text-align:center;font-size:18px;font-weight:700;text-decoration:none;border-radius:10px;margin:20px 0 12px;transition:background .2s}}
.cta-story:hover{{background:#333}}
.offer-badges{{font-size:13px;color:#777}}
.offer-badges div{{margin-bottom:4px;display:flex;align-items:center;gap:6px}}

/* STICKY FOOTER */
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#111;padding:13px 20px;text-align:center;z-index:300}}
.sticky-footer a{{color:#fff;text-decoration:none;font-weight:700;font-size:16px}}

/* RESPONSIVE */
@media(max-width:700px){{
  .hero-banner{{padding:48px 18px 44px}}
  h1{{font-size:30px}}
  .story-wrap{{padding:32px 18px 32px}}
  .story-h2{{font-size:24px}}
  .pull-quote{{padding:24px 0}}
  .pq-text{{font-size:21px}}
  .story-fig{{margin:24px -18px}}
  .story-fig figcaption{{padding:6px 18px 4px}}
  .offer-story{{padding:24px 18px}}
}}
</style>
</head>
<body>

<div class="hero-banner">
  <div class="hero-tag">Personal Story</div>
  <h1>{headline}</h1>
  {"<p class='hero-sub'>" + subheadline + "</p>" if subheadline else ""}
  <div class="hero-meta">By {author_name} &nbsp;&middot;&nbsp; {today}</div>
</div>

<div class="story-wrap">
  <p class="intro-line">My name is {author_name}, and this is my story.</p>

  {article_body}

  <div class="section-divider">&#9670; &nbsp; &#9670; &nbsp; &#9670;</div>

  <div class="offer-story">
    <p class="offer-intro">&#8220;After everything I went through, I finally found something that actually worked.&#8221;</p>
    <h2>{tx["offer_title"]}</h2>
    <p>{tx["offer_desc"]}</p>
    {'<img src="' + product_image_url + '" alt="' + product_name + '" style="width:100%;border-radius:10px;margin:12px 0 18px;">' if product_image_url else '<div class="placeholder"><div class="tbadge">' + tx.get("bundle_badge","PRODUCT") + '</div><br>' + tx.get("bundle_desc","Product image") + '</div>'}
    {cta_body}
    <a href="{product_url}" class="cta-story">{tx["cta"]}</a>
    <div class="offer-badges">
      <div>&#10003; {tx["badge1"]}</div>
      <div>&#10003; {tx["badge2"]}</div>
      <div>&#10003; {tx.get("badge3","")}</div>
    </div>
  </div>
</div>

<div class="sticky-footer">
  <a href="{product_url}">{tx["cta_footer"]}</a>
</div>

</body>
</html>'''
