"""Urgency/Sale template — dark aggressive, fixed countdown, multiple CTAs, Montserrat font."""
from datetime import datetime


def build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang, tx):
    today = datetime.utcnow().strftime("%B %d, %Y")
    headline = content.get("headline", "")
    subheadline = content.get("subheadline", "")

    body_parts = []
    offer_section = None
    cta_section = None
    body_sec_idx = 0

    # Mini CTA inserted every 3 body sections
    def mini_cta():
        return f'''<div class="mid-cta">
  <a href="{product_url}" class="cta-mid">{tx["cta"]} &#8594;</a>
  <div class="mid-cta-sub">&#9201; Limited stock — act now</div>
</div>'''

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
            caption = placeholder.get("description", "") or ""
            parts.append(f'''<figure class="sale-fig">
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
            parts.append(f'<h2 class="sale-h2">{heading}</h2>')
        if body_html:
            parts.append(f'<div class="sale-prose">{body_html}</div>')

        if parts:
            body_parts.append("\n".join(parts))

        # Insert mid-page CTA every 3rd section
        body_sec_idx += 1
        if body_sec_idx % 3 == 0:
            body_parts.append(mini_cta())

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
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700;800;900&family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Open Sans',sans-serif;background:#111;color:#f0f0f0;font-size:18px;line-height:1.72;padding-top:56px;padding-bottom:68px}}

/* FIXED COUNTDOWN BAR */
.countdown-bar{{position:fixed;top:0;left:0;right:0;z-index:500;background:linear-gradient(90deg,#b91c1c,#dc2626);padding:0 20px;height:56px;display:flex;align-items:center;justify-content:center;gap:14px;box-shadow:0 2px 16px rgba(220,38,38,.5)}}
.cd-label{{font-family:'Montserrat',sans-serif;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:1.2px;color:rgba(255,255,255,.85)}}
.cd-timer{{font-family:'Montserrat',sans-serif;font-size:26px;font-weight:900;color:#fff;letter-spacing:3px;min-width:90px;text-align:center}}
.cd-suffix{{font-size:12px;color:rgba(255,255,255,.75);font-weight:700}}

/* HERO SALE HEADER */
.sale-hero{{background:#1a1a1a;padding:44px 20px 36px;text-align:center;border-bottom:3px solid #dc2626}}
.discount-badge{{display:inline-block;background:#dc2626;color:#fff;font-family:'Montserrat',sans-serif;font-weight:900;font-size:52px;padding:14px 32px;border-radius:6px;margin-bottom:18px;line-height:1;box-shadow:0 4px 24px rgba(220,38,38,.4)}}
.discount-badge small{{font-size:16px;display:block;font-weight:800;opacity:.9;margin-top:4px;letter-spacing:1px}}
h1{{font-family:'Montserrat',sans-serif;font-weight:900;font-size:34px;line-height:1.15;color:#fff;max-width:740px;margin:0 auto 12px}}
.sale-sub{{font-size:17px;color:rgba(255,255,255,.65);max-width:600px;margin:0 auto}}

/* TRUST BADGES */
.trust-row{{background:#1a1a1a;border-bottom:2px solid #2a2a2a;padding:14px 20px;display:flex;justify-content:center;gap:24px;flex-wrap:wrap}}
.trust-item{{display:flex;align-items:center;gap:6px;font-size:13px;color:rgba(255,255,255,.75);font-weight:600}}
.trust-item span{{font-size:18px}}

/* CONTENT WRAPPER */
.sale-wrap{{max-width:740px;margin:0 auto;padding:32px 20px}}

/* STOCK ALERT */
.stock-alert{{background:#1e0a0a;border:2px solid #dc2626;border-radius:8px;padding:18px 22px;margin:0 0 28px;text-align:center}}
.stock-title{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:15px;color:#dc2626;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px}}
.stock-bar{{height:10px;background:#2a1010;border-radius:5px;overflow:hidden;margin:8px 0}}
.stock-fill{{height:100%;background:linear-gradient(90deg,#dc2626,#ef4444);border-radius:5px;width:23%;animation:stock-shrink 8s ease-in-out forwards}}
@keyframes stock-shrink{{0%{{width:27%}}100%{{width:19%}}}}
.stock-note{{font-size:13px;color:rgba(255,255,255,.5);margin-top:6px}}

/* SECTION HEADINGS */
.sale-h2{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:23px;line-height:1.25;color:#fff;margin:32px 0 14px}}

/* BODY PROSE */
.sale-prose p{{font-size:18px;line-height:1.75;margin-bottom:16px;color:#d4d4d4}}
.sale-prose strong{{color:#fff}}
.sale-prose em{{color:#f0a0a0}}
.sale-prose blockquote{{border-left:3px solid #dc2626;margin:20px 0;padding:12px 20px;background:#1e1e1e;font-style:italic;color:#c0c0c0;border-radius:0 4px 4px 0}}
.sale-prose ul,.sale-prose ol{{padding-left:28px;margin-bottom:16px}}
.sale-prose li{{margin-bottom:7px;line-height:1.65;color:#d4d4d4}}

/* STAT ROW */
.stat-row{{display:flex;gap:12px;margin:20px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:130px;background:#1e1e1e;border:1px solid #dc2626;border-radius:6px;padding:16px;text-align:center}}
.stat-box .stat-num{{font-family:'Montserrat',sans-serif;font-weight:900;font-size:30px;color:#dc2626;display:block}}
.stat-box .stat-label{{font-size:13px;color:#888;margin-top:4px}}

/* COMPARISON */
.comparison-table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:16px}}
.comparison-table th{{background:#dc2626;color:#fff;padding:12px 14px;text-align:left;font-family:'Montserrat',sans-serif;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.5px}}
.comparison-table td{{padding:11px 14px;border-bottom:1px solid #2a2a2a;color:#d4d4d4}}
.comparison-table .good{{color:#22c55e;font-weight:700}}
.comparison-table .bad{{color:#dc2626;font-weight:700}}

/* TESTIMONIAL */
.testimonial{{background:#1e1e1e;border-left:4px solid #dc2626;border-radius:0 6px 6px 0;padding:16px 20px;margin:16px 0}}
.testimonial .quote{{font-size:17px;line-height:1.65;color:#d0d0d0;font-style:italic;margin-bottom:6px}}
.testimonial .attribution{{font-size:13px;color:#666;font-weight:700}}
.warning-box{{background:#1e0a0a;border:1px solid #dc2626;border-radius:4px;padding:14px 18px;margin:14px 0;font-size:16px;display:flex;gap:10px;color:#d4d4d4}}
.step{{margin-bottom:12px;display:flex;gap:10px;align-items:flex-start}}
.step .step-title{{font-weight:700;font-size:16px;margin-bottom:2px;color:#fff}}
.step p{{font-size:16px;margin-bottom:0;color:#d4d4d4}}
.tip{{background:#1e1e1e;border-left:3px solid #dc2626;padding:12px 16px;margin:12px 0;font-size:16px;border-radius:0 4px 4px 0;display:flex;gap:8px;color:#d4d4d4}}
.accent{{color:#dc2626;font-weight:700}}

/* FIGURES */
.sale-fig{{margin:22px 0}}
.sale-fig img{{width:100%;display:block;border-radius:6px}}
.sale-fig figcaption{{font-size:12px;color:#666;font-style:italic;padding:6px 2px}}
.video-ph{{background:#0a0a0a;color:#444;padding:60px 20px;text-align:center;border-radius:6px;margin:22px 0}}
.play-icon{{font-size:48px;color:#dc2626;opacity:.8;display:block;margin:0 0 12px}}
.video-ph p{{font-size:13px;color:#444}}
.placeholder{{background:#1a1a1a;padding:36px 20px;text-align:center;color:#555;border:1px dashed #333;border-radius:6px;margin:22px 0;font-size:14px;font-style:italic}}
.tbadge{{display:inline-block;background:#dc2626;color:#fff;font-size:10px;padding:3px 10px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700;border-radius:10px}}

/* MID-PAGE CTA */
.mid-cta{{text-align:center;padding:20px 0;margin:8px 0}}
.cta-mid{{display:inline-block;padding:14px 32px;background:#dc2626;color:#fff;font-family:'Montserrat',sans-serif;font-size:16px;font-weight:800;text-decoration:none;border-radius:6px;text-transform:uppercase;letter-spacing:.5px;transition:background .2s;box-shadow:0 3px 16px rgba(220,38,38,.3)}}
.cta-mid:hover{{background:#b91c1c}}
.mid-cta-sub{{font-size:12px;color:#666;margin-top:8px}}

/* PRICE COMPARISON */
.price-block{{background:#1e1e1e;border:2px solid #dc2626;border-radius:8px;padding:24px;margin:24px 0;text-align:center}}
.old-price{{font-family:'Montserrat',sans-serif;font-size:22px;color:#666;text-decoration:line-through;margin-bottom:4px}}
.new-price{{font-family:'Montserrat',sans-serif;font-size:52px;font-weight:900;color:#dc2626;line-height:1}}
.new-price-note{{font-size:14px;color:#888;margin-top:6px}}

/* MASSIVE OFFER BOX */
.offer-mega{{background:#1a0505;border:3px solid #dc2626;border-radius:12px;padding:36px;margin:36px 0;text-align:center}}
.offer-mega-badge{{background:#dc2626;color:#fff;font-family:'Montserrat',sans-serif;font-size:11px;font-weight:900;padding:6px 18px;text-transform:uppercase;letter-spacing:2px;border-radius:3px;display:inline-block;margin-bottom:18px}}
.offer-mega h2{{font-family:'Montserrat',sans-serif;font-weight:900;font-size:28px;color:#fff;margin-bottom:14px;text-transform:uppercase}}
.offer-mega p{{font-size:17px;color:rgba(255,255,255,.8);margin-bottom:14px}}
.offer-mega strong{{color:#fff}}
.offer-stock-bar{{height:10px;background:#2a0808;border-radius:5px;overflow:hidden;margin:16px 0 6px}}
.offer-stock-fill{{height:100%;background:linear-gradient(90deg,#dc2626,#ef4444);border-radius:5px;width:21%;animation:stock-shrink2 10s ease-in-out forwards}}
@keyframes stock-shrink2{{0%{{width:25%}}100%{{width:16%}}}}
.offer-stock-note{{font-size:13px;color:rgba(255,255,255,.45);margin-bottom:18px}}
.cta-mega{{display:block;width:100%;padding:22px 24px;background:#dc2626;color:#fff;text-align:center;font-family:'Montserrat',sans-serif;font-size:22px;font-weight:900;text-transform:uppercase;letter-spacing:.8px;text-decoration:none;border-radius:8px;margin:20px 0 14px;transition:background .2s;box-shadow:0 6px 28px rgba(220,38,38,.5)}}
.cta-mega:hover{{background:#b91c1c}}
.cta-sub{{font-size:13px;color:rgba(255,255,255,.45);margin-top:8px}}
.offer-badges{{font-size:14px;color:rgba(255,255,255,.5);text-align:left;margin-top:14px}}
.offer-badges div{{margin-bottom:6px;display:flex;align-items:center;gap:8px}}

/* STICKY FOOTER */
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#dc2626;padding:14px 20px;text-align:center;z-index:400;box-shadow:0 -3px 20px rgba(220,38,38,.4)}}
.sticky-footer a{{color:#fff;text-decoration:none;font-family:'Montserrat',sans-serif;font-weight:800;font-size:16px;text-transform:uppercase;letter-spacing:.5px}}

/* RESPONSIVE */
@media(max-width:740px){{
  .sale-hero{{padding:32px 16px 28px}}
  .discount-badge{{font-size:38px;padding:10px 22px}}
  h1{{font-size:26px}}
  .sale-wrap{{padding:24px 16px}}
  .sale-h2{{font-size:20px}}
  .trust-row{{gap:12px}}
  .trust-item{{font-size:12px}}
  .offer-mega{{padding:24px 16px}}
  .offer-mega h2{{font-size:22px}}
  .cta-mega{{font-size:18px;padding:18px}}
  .new-price{{font-size:40px}}
}}
</style>
</head>
<body>

<!-- FIXED COUNTDOWN TIMER -->
<div class="countdown-bar">
  <span class="cd-label">&#9201; Sale Ends In:</span>
  <span class="cd-timer" id="cdown">23:00</span>
  <span class="cd-suffix">minutes</span>
</div>

<div class="sale-hero">
  <div class="discount-badge">67% OFF<small>FLASH SALE</small></div>
  <h1>{headline}</h1>
  {"<p class='sale-sub'>" + subheadline + "</p>" if subheadline else ""}
</div>

<div class="trust-row">
  <div class="trust-item"><span>&#128274;</span> Secure Checkout</div>
  <div class="trust-item"><span>&#128176;</span> Money-Back Guarantee</div>
  <div class="trust-item"><span>&#128666;</span> Free Shipping</div>
  <div class="trust-item"><span>&#11088;</span> 4.9/5 Rating</div>
</div>

<div class="sale-wrap">
  <div class="stock-alert">
    <div class="stock-title">&#9888;&#65039; Only 23% of inventory remaining</div>
    <div class="stock-bar"><div class="stock-fill"></div></div>
    <div class="stock-note">Once it&#39;s gone, it&#39;s gone. No restocks planned.</div>
  </div>

  {article_body}

  <div class="price-block">
    <div class="old-price">Regular Price: $199.99</div>
    <div class="new-price">$67.99</div>
    <div class="new-price-note">You save $132.00 &mdash; 67% off today only</div>
  </div>

  <div class="offer-mega">
    <div class="offer-mega-badge">&#128293; Limited Time Offer</div>
    <h2>{tx["offer_title"]}</h2>
    <p>{tx["offer_desc"]}</p>
    {'<img src="' + product_image_url + '" alt="' + product_name + '" style="width:100%;border-radius:8px;margin:12px 0 16px;">' if product_image_url else '<div class="placeholder" style="background:#0f0f0f;border-color:#333;color:#555"><div class="tbadge">' + tx.get("bundle_badge","PRODUCT") + '</div><br>' + tx.get("bundle_desc","Product image") + '</div>'}
    {cta_body}
    <div class="offer-stock-bar"><div class="offer-stock-fill"></div></div>
    <div class="offer-stock-note">&#9888;&#65039; Only 21 units left at this price</div>
    <a href="{product_url}" class="cta-mega">{tx["cta"]} &#8594;</a>
    <div class="cta-sub">&#128274; Secure 256-bit encrypted checkout &nbsp;|&nbsp; Ships same day</div>
    <div class="offer-badges">
      <div>&#10003; {tx["badge1"]}</div>
      <div>&#10003; {tx["badge2"]}</div>
      <div>&#10003; {tx.get("badge3","60-Day money-back guarantee")}</div>
    </div>
  </div>
</div>

<div class="sticky-footer">
  <a href="{product_url}">{tx["cta_footer"]} &#8594;</a>
</div>

<script>
(function() {{
  var end = Date.now() + 23 * 60 * 1000;
  function pad(n) {{ return n < 10 ? '0' + n : '' + n; }}
  function tick() {{
    var rem = Math.max(0, end - Date.now());
    var m = Math.floor(rem / 60000);
    var s = Math.floor((rem % 60000) / 1000);
    var el = document.getElementById('cdown');
    if (el) {{ el.textContent = pad(m) + ':' + pad(s); }}
    if (rem > 0) {{ setTimeout(tick, 1000); }}
  }}
  tick();
}})();
</script>

</body>
</html>'''
