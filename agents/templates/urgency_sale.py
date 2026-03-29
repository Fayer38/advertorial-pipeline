"""Urgency/Sale template — JS countdown timer, mid-article CTA, price comparison,
SVG trust badges, flashing offer box, stock-drain animation, aggressive red/dark theme."""
from datetime import datetime


def build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang, tx):
    today = datetime.utcnow().strftime("%B %d, %Y")
    headline = content.get("headline", "")
    subheadline = content.get("subheadline", "")

    sections = content.get("sections", [])

    # SVG trust icons (inline, no external dependency)
    lock_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="vertical-align:middle"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>'
    shield_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="vertical-align:middle"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
    check_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="vertical-align:middle"><polyline points="20 6 9 17 4 12"/></svg>'

    body_parts = []
    offer_section = None
    cta_section = None
    body_section_count = 0
    mid_cta_inserted = False

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
            parts.append(f'<h2 class="art-h2">{heading}</h2>')

        if body_html:
            parts.append(body_html)

        # Image AFTER body — editorial placement
        if img_url:
            parts.append(
                f'<div class="article-img">'
                f'<img src="{img_url}" alt="{heading}" loading="lazy">'
                f'</div>'
            )
        elif placeholder.get("description"):
            p_type = placeholder.get("type", "photo").upper()
            parts.append(
                f'<div class="placeholder">'
                f'<div class="tbadge">{p_type}</div>'
                f'<span class="ph-desc">{placeholder["description"]}</span>'
                f'</div>'
            )

        if parts:
            body_parts.append("\n".join(parts))

        body_section_count += 1

        # Inject mid-article CTA after section 3
        if not mid_cta_inserted and body_section_count >= 3:
            mid_cta_inserted = True
            body_parts.append(
                f'<div class="mid-cta">'
                f'<div class="mid-cta-eyebrow">&#9889; LIMITED TIME — SALE ENDS WHEN TIMER HITS ZERO</div>'
                f'<div class="mid-cta-timer-row"><span class="mid-timer" id="mid-cts">04:23:47</span></div>'
                f'<p class="mid-cta-title">Thousands already grabbed <strong>{product_name}</strong> this week.</p>'
                f'<p class="mid-cta-sub">Only <strong>23 units left</strong> at the discounted price.</p>'
                f'<a href="{product_url}" class="mid-cta-btn">{tx.get("cta", "Claim Your Discount")} &#8594;</a>'
                f'<div class="mid-cta-badges">'
                f'<span>{lock_svg} Secure Checkout</span>'
                f'<span>{shield_svg} 30-Day Guarantee</span>'
                f'<span>{check_svg} Free Shipping</span>'
                f'</div>'
                f'</div>'
            )

    article_body = "\n\n".join(body_parts)
    cta_body = cta_section.get("body_html", "") if cta_section else ""

    if product_image_url:
        prod_img_html = f'<img src="{product_image_url}" alt="{product_name}" class="offer-product-img">'
    else:
        prod_img_html = (
            f'<div class="placeholder" style="background:#1a1a1a;border-color:#444;height:200px;'
            f'display:flex;flex-direction:column;align-items:center;justify-content:center;">'
            f'<div class="tbadge">{tx.get("bundle_badge","PRODUCT")}</div>'
            f'<span class="ph-desc" style="margin-top:8px">{tx.get("bundle_desc","Product image")}</span>'
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
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800;900&family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Open Sans',sans-serif;color:#e8e8e8;background:#0f0f0f;font-size:17px;line-height:1.72;padding-bottom:72px}}

/* COUNTDOWN TOP BAR */
.countdown-topbar{{background:linear-gradient(90deg,#7f1d1d,#dc2626,#7f1d1d);color:#fff;text-align:center;padding:11px 16px;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;gap:12px;flex-wrap:wrap}}
.cdb-label{{text-transform:uppercase;letter-spacing:1px;opacity:.85}}
.cdb-timer{{font-family:'Montserrat',sans-serif;font-size:22px;font-weight:900;letter-spacing:4px;background:rgba(0,0,0,.3);padding:4px 14px;border-radius:4px;min-width:110px;display:inline-block;text-align:center}}

/* HERO */
.hero-sale{{background:#111;color:#fff;padding:44px 20px 36px;text-align:center;border-bottom:3px solid #dc2626}}
.discount-badge{{display:inline-flex;flex-direction:column;align-items:center;background:#dc2626;color:#fff;font-family:'Montserrat',sans-serif;font-weight:900;font-size:52px;padding:14px 32px;border-radius:6px;margin-bottom:20px;line-height:1;box-shadow:0 4px 24px rgba(220,38,38,.5)}}
.discount-badge small{{font-size:13px;font-weight:700;letter-spacing:2px;opacity:.85;margin-top:4px;text-transform:uppercase}}
h1{{font-family:'Montserrat',sans-serif;font-weight:900;font-size:34px;line-height:1.18;margin-bottom:12px;max-width:720px;margin-left:auto;margin-right:auto;color:#fff}}
.hero-sub{{font-size:16px;color:rgba(255,255,255,.65);max-width:580px;margin:0 auto 18px;line-height:1.55}}
.hero-price-row{{display:flex;align-items:center;justify-content:center;gap:14px;flex-wrap:wrap}}
.price-was{{font-size:22px;color:#888;text-decoration:line-through;font-family:'Montserrat',sans-serif}}
.price-now{{font-size:38px;color:#dc2626;font-family:'Montserrat',sans-serif;font-weight:900}}
.price-save{{background:#dc2626;color:#fff;font-size:13px;font-weight:800;padding:4px 12px;border-radius:20px;text-transform:uppercase;letter-spacing:.5px}}

/* LAYOUT */
.article-content{{max-width:740px;margin:0 auto;padding:32px 20px}}

/* STOCK ALERT */
.stock-alert{{background:#1a0a0a;border:2px solid #dc2626;border-radius:6px;padding:18px 22px;margin:0 0 28px;text-align:center}}
.stock-title{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:15px;color:#dc2626;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px}}
.stock-bar-wrap{{background:#2a0a0a;border-radius:4px;height:10px;overflow:hidden;margin:8px 0}}
.stock-bar-fill{{height:100%;border-radius:4px;background:linear-gradient(90deg,#dc2626,#ef4444);width:23%;animation:stock-drain 8s ease-in-out forwards}}
@keyframes stock-drain{{0%{{width:31%}}100%{{width:17%}}}}
.stock-label{{font-size:12px;color:#888;margin-top:6px}}

/* TYPOGRAPHY */
.art-h2{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:22px;line-height:1.28;margin:32px 0 13px;color:#fff}}
p{{margin-bottom:14px;color:#ccc;font-size:17px;line-height:1.72}}
strong{{color:#fff;font-weight:700}}
ul,ol{{padding-left:22px;margin-bottom:16px;color:#ccc}}
li{{margin-bottom:8px;font-size:17px;line-height:1.7}}
blockquote{{border-left:4px solid #dc2626;margin:22px 0;padding:14px 20px;background:#1a1a1a;color:#bbb;font-style:italic;font-size:17px;border-radius:0 4px 4px 0}}

/* IMAGES */
.article-img{{margin:18px -20px}}
.article-img img{{width:100%;display:block}}

/* PLACEHOLDERS */
.placeholder{{background:#181818;border:1px dashed #444;border-radius:6px;padding:32px 20px;text-align:center;margin:14px 0}}
.tbadge{{display:inline-block;background:#dc2626;color:#fff;font-size:10px;padding:3px 10px;border-radius:3px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700}}
.ph-desc{{color:#666;font-size:13px;font-style:italic;display:block;margin-top:4px}}

/* INLINE ELEMENTS */
.stat-row{{display:flex;gap:12px;margin:22px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:130px;background:#1a1a1a;border:1px solid #333;border-radius:6px;padding:16px;text-align:center}}
.stat-box .stat-num{{font-family:'Montserrat',sans-serif;font-weight:900;font-size:30px;color:#dc2626;display:block;line-height:1}}
.stat-box .stat-label{{font-size:12px;color:#888;margin-top:6px;text-transform:uppercase;letter-spacing:.5px}}
.comparison-table{{display:block;overflow-x:auto;-webkit-overflow-scrolling:touch;width:100%;border-collapse:collapse;margin:20px 0;font-size:15px}}
.comparison-table th{{background:#1a1a1a;color:#fff;padding:12px 14px;text-align:left;font-family:'Montserrat',sans-serif;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.8px;border-bottom:2px solid #dc2626}}
.comparison-table tr:nth-child(even) td{{background:#141414}}
.comparison-table td{{padding:11px 14px;border-bottom:1px solid #222;color:#ccc}}
.comparison-table .good{{color:#22c55e;font-weight:700}}
.comparison-table .bad{{color:#dc2626;font-weight:700}}
.testimonial{{background:#1a1a1a;border-left:4px solid #dc2626;border-radius:0 6px 6px 0;padding:16px 20px;margin:18px 0}}
.testimonial .quote{{font-size:16px;line-height:1.65;color:#ccc;font-style:italic;margin-bottom:6px}}
.testimonial .attribution{{font-size:13px;color:#666;font-weight:700}}
.warning-box{{background:#1a0a0a;border:1px solid #7f1d1d;border-radius:6px;padding:14px 18px;margin:14px 0;font-size:16px;display:flex;gap:10px;align-items:flex-start;color:#ccc}}
.step{{margin-bottom:14px;display:flex;gap:12px;align-items:flex-start}}
.step-num{{width:28px;height:28px;background:#dc2626;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:13px;flex-shrink:0;margin-top:2px;font-family:'Montserrat',sans-serif}}
.step .step-title{{font-weight:700;font-size:16px;margin-bottom:3px;color:#fff}}
.step p{{font-size:16px;margin-bottom:0;color:#ccc}}
.tip{{background:#1a1a1a;border-left:3px solid #dc2626;padding:12px 16px;margin:14px 0;font-size:16px;border-radius:0 4px 4px 0;display:flex;gap:8px;color:#ccc}}

/* MID-ARTICLE CTA */
.mid-cta{{background:linear-gradient(135deg,#1a0000,#2d0000);border:2px solid #dc2626;border-radius:8px;padding:24px 28px;margin:36px 0;text-align:center}}
.mid-cta-eyebrow{{font-family:'Montserrat',sans-serif;font-size:10px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:#dc2626;margin-bottom:10px}}
.mid-cta-timer-row{{margin-bottom:12px}}
.mid-timer{{font-family:'Montserrat',sans-serif;font-size:32px;font-weight:900;color:#fff;letter-spacing:4px;background:#111;padding:6px 18px;border-radius:4px;display:inline-block}}
.mid-cta-title{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:19px;color:#fff;margin-bottom:6px}}
.mid-cta-sub{{font-size:14px;color:#999;margin-bottom:16px}}
.mid-cta-btn{{display:inline-block;background:#dc2626;color:#fff;text-decoration:none;font-family:'Montserrat',sans-serif;font-weight:900;font-size:16px;padding:14px 32px;border-radius:5px;text-transform:uppercase;letter-spacing:.5px;transition:background .2s;margin-bottom:14px}}
.mid-cta-btn:hover{{background:#b91c1c}}
.mid-cta-badges{{display:flex;justify-content:center;gap:16px;flex-wrap:wrap;font-size:12px;color:#666}}
.mid-cta-badges span{{display:flex;align-items:center;gap:4px}}

/* OFFER BOX with flashing border */
@keyframes flash-border{{
  0%,100%{{border-color:#dc2626;box-shadow:0 0 0 rgba(220,38,38,0)}}
  50%{{border-color:#ff4444;box-shadow:0 0 28px rgba(220,38,38,.45)}}
}}
.offer-box{{background:#111;border:3px solid #dc2626;border-radius:10px;padding:32px;margin:36px 0;animation:flash-border 2.2s ease-in-out infinite}}
.offer-box-header{{display:flex;align-items:center;gap:10px;margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid #2a2a2a}}
.offer-box-badge{{background:#dc2626;color:#fff;font-family:'Montserrat',sans-serif;font-weight:900;font-size:11px;padding:4px 12px;border-radius:3px;text-transform:uppercase;letter-spacing:1.5px}}
.offer-box-title{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:18px;color:#fff}}
.offer-product-img{{width:100%;border-radius:8px;margin-bottom:20px;display:block}}
.price-comparison{{display:flex;align-items:center;gap:14px;margin:16px 0;flex-wrap:wrap}}
.price-original{{font-size:20px;color:#666;text-decoration:line-through;font-family:'Montserrat',sans-serif}}
.price-sale{{font-size:38px;color:#dc2626;font-family:'Montserrat',sans-serif;font-weight:900;line-height:1}}
.price-pct{{background:#dc2626;color:#fff;font-family:'Montserrat',sans-serif;font-weight:800;font-size:13px;padding:5px 12px;border-radius:4px;text-transform:uppercase}}
.offer-desc-text{{font-size:16px;color:#bbb;margin:12px 0 20px;line-height:1.65}}
.offer-countdown-row{{background:#1a0000;border:1px solid #7f1d1d;border-radius:6px;padding:12px 16px;margin:14px 0;text-align:center}}
.offer-countdown-label{{font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}}
.offer-countdown-timer{{font-family:'Montserrat',sans-serif;font-size:28px;font-weight:900;color:#dc2626;letter-spacing:4px}}
.offer-stock-bar{{background:#1a1a1a;border-radius:4px;height:8px;overflow:hidden;margin:10px 0 4px}}
.offer-stock-fill{{height:100%;background:linear-gradient(90deg,#dc2626,#ef4444);width:23%;animation:stock-drain 8s ease-in-out forwards}}
.offer-stock-label{{font-size:11px;color:#666;text-align:center;margin-bottom:12px}}
.offer-cta{{display:block;width:100%;padding:18px;background:#dc2626;color:#fff;text-align:center;font-size:20px;font-weight:900;border-radius:6px;text-decoration:none;margin:14px 0 10px;transition:all .2s;font-family:'Montserrat',sans-serif;text-transform:uppercase;letter-spacing:.5px;box-shadow:0 4px 20px rgba(220,38,38,.4)}}
.offer-cta:hover{{background:#b91c1c;box-shadow:0 6px 28px rgba(220,38,38,.55);transform:translateY(-1px)}}
.trust-badges{{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px;justify-content:center}}
.trust-badge{{display:flex;align-items:center;gap:6px;background:#1a1a1a;border:1px solid #333;border-radius:20px;padding:6px 14px;font-size:12px;color:#999;font-weight:600}}
.cta-sub-text{{font-size:13px;color:#666;text-align:center;margin-top:8px}}
.cta-body-html{{color:#bbb;font-size:15px;line-height:1.6;margin:10px 0}}

/* STICKY FOOTER */
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:linear-gradient(90deg,#7f1d1d,#dc2626);padding:0;z-index:100;display:flex;align-items:stretch}}
.sticky-footer a{{flex:1;display:flex;align-items:center;justify-content:center;gap:10px;color:#fff;text-decoration:none;font-family:'Montserrat',sans-serif;font-weight:800;font-size:15px;text-transform:uppercase;letter-spacing:.5px;padding:13px 20px}}
.sf-timer{{font-size:16px;letter-spacing:3px;background:rgba(0,0,0,.25);padding:3px 10px;border-radius:3px}}

/* RESPONSIVE */
@media(max-width:640px){{
.article-content{{padding:20px 14px}}
.article-img{{margin:14px -14px}}
h1{{font-size:27px}}
.art-h2{{font-size:19px}}
.discount-badge{{font-size:40px;padding:12px 24px}}
.hero-sale{{padding:32px 14px 26px}}
.cdb-timer{{font-size:18px}}
.mid-timer{{font-size:26px}}
.price-now,.price-sale{{font-size:30px}}
.offer-countdown-timer{{font-size:22px}}
.offer-cta{{font-size:17px;padding:15px}}
.mid-cta{{padding:18px 16px}}
}}
</style>
</head>
<body>

<!-- HERO SALE -->
<div class="hero-sale">
  <div class="discount-badge">55% OFF<small>Flash Sale Price</small></div>
  <h1>{headline}</h1>
  {"<p class='hero-sub'>" + subheadline + "</p>" if subheadline else ""}
  <div class="hero-price-row">
    <span class="price-was">$267.00</span>
    <span class="price-now">$119.99</span>
    <span class="price-save">Save $147</span>
  </div>
</div>

<!-- ARTICLE BODY -->
<div class="article-content">

  <!-- STOCK ALERT -->
  <div class="stock-alert">
    <div class="stock-title">&#9888; Warning: Only 23% of inventory remaining</div>
    <div class="stock-bar-wrap"><div class="stock-bar-fill"></div></div>
    <div class="stock-label">Inventory is draining fast — once gone, price resets permanently</div>
  </div>

  {article_body}

  <!-- OFFER BOX -->
  <div class="offer-box">
    <div class="offer-box-header">
      <span class="offer-box-badge">&#128293; Flash Offer</span>
      <span class="offer-box-title">{tx.get("offer_title", "Limited-Time Deal")}</span>
    </div>

    {prod_img_html}

    <div class="price-comparison">
      <span class="price-original">$267.00</span>
      <span class="price-sale">$119.99</span>
      <span class="price-pct">55% OFF</span>
    </div>

    <div class="offer-desc-text">
      <strong>{product_name}</strong> — {tx.get("offer_desc", "")}
    </div>

    <div class="offer-countdown-row">
      <div class="offer-countdown-label">&#9200; This Price Expires In</div>
      <div class="offer-countdown-timer" id="offer-cts">04:23:47</div>
    </div>

    <div class="offer-stock-bar"><div class="offer-stock-fill"></div></div>
    <div class="offer-stock-label">&#128308; Only 23 units remain at this price</div>

    <div class="cta-body-html">{cta_body}</div>

    <a href="{product_url}" class="offer-cta">{tx.get("cta", "Claim My 55% Discount")}</a>
    <div class="cta-sub-text">&#10003; Secure Checkout &nbsp;|&nbsp; &#10003; Ships Today &nbsp;|&nbsp; &#10003; 30-Day Guarantee</div>

    <div class="trust-badges">
      <span class="trust-badge">{lock_svg} 256-bit SSL</span>
      <span class="trust-badge">{shield_svg} {tx.get("badge1", "Money-Back Guarantee")}</span>
      <span class="trust-badge">{check_svg} {tx.get("badge2", "Free Fast Shipping")}</span>
      {"<span class='trust-badge'>" + check_svg + " " + tx.get("badge3","") + "</span>" if tx.get("badge3") else ""}
    </div>
  </div>

</div><!-- /article-content -->

<!-- STICKY FOOTER -->
<div class="sticky-footer">
  <a href="{product_url}">
    &#128293; {tx.get("cta_footer", "Claim My Discount")}
    &nbsp;&nbsp;<span class="sf-timer" id="sf-cts">04:23:47</span>
  </a>
</div>

<script>
(function() {{
  var totalSeconds = 4 * 3600 + 23 * 60 + 47;
  var ids = ['top-cts', 'mid-cts', 'offer-cts', 'sf-cts'];
  function fmt(n) {{ return String(n).padStart(2, '0'); }}
  function tick() {{
    if (totalSeconds <= 0) {{
      ids.forEach(function(id) {{ var el = document.getElementById(id); if (el) el.textContent = '00:00:00'; }});
      return;
    }}
    totalSeconds--;
    var h = Math.floor(totalSeconds / 3600);
    var m = Math.floor((totalSeconds % 3600) / 60);
    var s = totalSeconds % 60;
    var display = fmt(h) + ':' + fmt(m) + ':' + fmt(s);
    ids.forEach(function(id) {{ var el = document.getElementById(id); if (el) el.textContent = display; }});
    setTimeout(tick, 1000);
  }}
  tick();
}})();
</script>

</body>
</html>'''
