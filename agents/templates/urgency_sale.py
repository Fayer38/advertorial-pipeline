"""Urgency Sale template — aggressive red/dark, JS countdown timer, multiple CTAs throughout,
animated stock bar, price strikethrough, trust badges, impossible-to-miss offer box."""
from datetime import datetime


def build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang, tx):
    today = datetime.utcnow().strftime("%B %d, %Y")
    headline = content.get("headline", "")
    subheadline = content.get("subheadline", "")

    body_parts = []
    offer_section = None
    cta_section = None
    cta_counter = 0

    sections = content.get("sections", [])
    body_sections = [s for s in sections if s.get("type") not in ("offer", "cta")]
    cta_interval = max(2, len(body_sections) // 3)

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
            parts.append(
                f'<img src="{img_url}" alt="{heading}" style="width:100%;border-radius:8px;margin:14px 0;display:block;">'
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

        if parts:
            body_parts.append("\n".join(parts))

        # Insert inline CTAs at regular intervals
        body_idx = sum(1 for s in sections[:i+1] if s.get("type") not in ("offer","cta"))
        if body_idx > 0 and body_idx % cta_interval == 0 and body_idx < len(body_sections):
            cta_counter += 1
            body_parts.append(
                f'<div class="inline-urgency-cta">'
                f'<div class="iuc-left">'
                f'<div class="iuc-fire">🔥</div>'
                f'<div>'
                f'<div class="iuc-title">Limited Time Offer</div>'
                f'<div class="iuc-sub">Join {3200 + cta_counter * 847:,} happy customers</div>'
                f'</div>'
                f'</div>'
                f'<a href="{product_url}" class="iuc-btn">{tx.get("cta","Claim Deal")} →</a>'
                f'</div>'
            )

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
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&family=Open+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Open Sans',sans-serif;color:#1a1a1a;background:#0d0d0d;font-size:17px;line-height:1.72;padding-bottom:72px}}

/* ── COUNTDOWN TICKER ── */
.countdown-ticker{{background:linear-gradient(90deg,#b91c1c 0%,#dc2626 50%,#b91c1c 100%);color:#fff;text-align:center;padding:0;overflow:hidden}}
.countdown-ticker-inner{{display:flex;align-items:center;justify-content:center;gap:20px;padding:10px 16px;flex-wrap:wrap}}
.countdown-label{{font-family:'Montserrat',sans-serif;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:2px;opacity:.85}}
.countdown-timer{{display:flex;align-items:center;gap:4px}}
.cd-block{{display:flex;flex-direction:column;align-items:center;background:rgba(0,0,0,.3);border-radius:4px;padding:6px 10px;min-width:48px}}
.cd-num{{font-family:'Montserrat',sans-serif;font-size:22px;font-weight:900;line-height:1;letter-spacing:1px}}
.cd-unit{{font-size:9px;text-transform:uppercase;letter-spacing:1px;opacity:.7;margin-top:2px}}
.cd-colon{{font-family:'Montserrat',sans-serif;font-size:22px;font-weight:900;opacity:.6;margin:0 2px;margin-bottom:14px}}

/* ── HERO ── */
.sale-hero{{background:#1a0000;padding:48px 20px 40px;text-align:center;position:relative;border-bottom:3px solid #dc2626}}
.sale-hero::before{{content:'';position:absolute;top:0;left:0;right:0;bottom:0;background:radial-gradient(ellipse at center,rgba(220,38,38,.15) 0%,transparent 70%)}}
.sale-badge{{display:inline-flex;align-items:center;gap:10px;background:#dc2626;border-radius:6px;padding:10px 24px;margin-bottom:22px}}
.sale-badge-pct{{font-family:'Montserrat',sans-serif;font-weight:900;font-size:52px;color:#fff;line-height:1}}
.sale-badge-text{{text-align:left}}
.sale-badge-off{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:16px;color:#fff;text-transform:uppercase;display:block}}
.sale-badge-type{{font-family:'Montserrat',sans-serif;font-weight:700;font-size:11px;color:rgba(255,255,255,.7);text-transform:uppercase;letter-spacing:1px;display:block}}
h1{{font-family:'Montserrat',sans-serif;font-weight:900;font-size:34px;line-height:1.18;color:#fff;max-width:720px;margin:0 auto 12px;position:relative}}
.hero-sub{{font-size:16px;color:rgba(255,255,255,.65);max-width:580px;margin:0 auto;line-height:1.55;position:relative}}

/* ── SOCIAL PROOF BAR ── */
.social-proof-bar{{background:#111;border-bottom:1px solid #1e1e1e;padding:10px 20px}}
.social-proof-bar-inner{{max-width:740px;margin:0 auto;display:flex;align-items:center;justify-content:center;gap:24px;flex-wrap:wrap}}
.sp-item{{display:flex;align-items:center;gap:6px;font-size:13px;color:rgba(255,255,255,.6)}}
.sp-item strong{{color:#fff}}

/* ── ARTICLE CONTENT ── */
.article-content{{max-width:740px;margin:0 auto;padding:28px 20px;background:#fff}}

/* ── STOCK ALERT ── */
.stock-alert{{background:#1a0000;border:2px solid #dc2626;border-radius:8px;padding:16px 20px;margin:0 0 24px;text-align:center;color:#fff}}
.stock-alert-title{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:15px;color:#dc2626;margin-bottom:8px}}
.stock-bar{{height:12px;background:#333;border-radius:6px;overflow:hidden;margin:8px 0}}
.stock-fill{{height:100%;background:linear-gradient(90deg,#dc2626,#f97316);border-radius:6px;width:23%;animation:stock-deplete 8s ease-in-out infinite alternate}}
@keyframes stock-deplete{{0%{{width:28%}} 100%{{width:18%}}}}
.stock-alert-sub{{font-size:13px;color:rgba(255,255,255,.6);margin-top:4px}}

/* ── TYPOGRAPHY ── */
h2{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:22px;line-height:1.3;margin:32px 0 12px;color:#111}}
p{{margin-bottom:14px;color:#2c2c2c;font-size:17px;line-height:1.72}}
strong{{color:#111;font-weight:700}}
blockquote{{border-left:4px solid #dc2626;margin:20px 0;padding:14px 20px;background:#fef2f2;color:#444;font-style:italic;font-size:17px;line-height:1.65;border-radius:0 6px 6px 0}}
ul,ol{{padding-left:24px;margin-bottom:14px}}
li{{margin-bottom:9px;font-size:17px;line-height:1.7}}

/* ── INLINE URGENCY CTA ── */
.inline-urgency-cta{{background:#1a0000;border:1px solid #dc2626;border-radius:8px;padding:16px 20px;margin:24px 0;display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}}
.iuc-left{{display:flex;align-items:center;gap:12px}}
.iuc-fire{{font-size:28px}}
.iuc-title{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:15px;color:#fff}}
.iuc-sub{{font-size:13px;color:rgba(255,255,255,.5)}}
.iuc-btn{{background:#dc2626;color:#fff;text-decoration:none;font-family:'Montserrat',sans-serif;font-weight:700;font-size:14px;padding:10px 22px;border-radius:6px;white-space:nowrap;transition:background .2s}}
.iuc-btn:hover{{background:#b91c1c}}

/* ── INLINE ELEMENTS ── */
.placeholder{{background:#f5f5f5;padding:40px 20px;text-align:center;color:#bbb;border-radius:8px;margin:14px 0;font-style:italic;font-size:14px;border:1px dashed #ddd}}
.placeholder .tbadge{{display:inline-block;background:#dc2626;color:#fff;font-size:10px;padding:3px 10px;border-radius:10px;margin-bottom:8px;font-style:normal;text-transform:uppercase;letter-spacing:.8px;font-weight:700}}
.stat-row{{display:flex;gap:12px;margin:20px 0;flex-wrap:wrap}}
.stat-box{{flex:1;min-width:130px;background:#fef2f2;border:1px solid #fecaca;border-top:3px solid #dc2626;border-radius:6px;padding:14px;text-align:center}}
.stat-box .stat-num{{font-family:'Montserrat',sans-serif;font-weight:900;font-size:30px;color:#dc2626;display:block;line-height:1}}
.stat-box .stat-label{{font-size:13px;color:#666;margin-top:6px}}
.comparison-table{{width:100%;border-collapse:collapse;margin:18px 0;font-size:16px}}
.comparison-table th{{background:#111;color:#fff;padding:12px 16px;text-align:left;font-family:'Montserrat',sans-serif;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.5px}}
.comparison-table tr:nth-child(even) td{{background:#fafafa}}
.comparison-table td{{padding:11px 16px;border-bottom:1px solid #eee}}
.comparison-table .good{{color:#16a34a;font-weight:700}}
.comparison-table .bad{{color:#dc2626;font-weight:700}}
.testimonial{{background:#fafafa;border-radius:8px;padding:18px 20px;margin:16px 0;border-left:4px solid #dc2626}}
.testimonial .stars{{color:#f59e0b;font-size:16px;letter-spacing:2px;margin-bottom:6px}}
.testimonial .quote{{font-size:16px;line-height:1.65;color:#333;font-style:italic;margin-bottom:8px}}
.testimonial .attribution{{font-size:13px;color:#888;font-weight:700}}
.warning-box{{background:#fef2f2;border:1px solid #fecaca;border-radius:6px;padding:14px 18px;margin:16px 0;font-size:16px;display:flex;gap:10px;align-items:flex-start}}
.step{{margin-bottom:12px;display:flex;gap:10px;align-items:flex-start}}
.step .step-title{{font-weight:700;font-size:16px;margin-bottom:2px;color:#111}}
.step p{{font-size:16px;margin-bottom:0}}
.tip{{background:#fef2f2;border-left:3px solid #dc2626;padding:12px 16px;margin:12px 0;font-size:16px;border-radius:0 6px 6px 0}}

/* ── MEGA OFFER BOX ── */
.mega-offer{{background:#0d0d0d;border-radius:0;margin:0 -20px;padding:40px 20px}}
.mega-offer-inner{{max-width:700px;margin:0 auto}}
.mega-offer-eyebrow{{text-align:center;margin-bottom:20px}}
.mega-offer-badge{{display:inline-block;background:#dc2626;color:#fff;font-family:'Montserrat',sans-serif;font-weight:900;font-size:13px;padding:6px 18px;border-radius:20px;text-transform:uppercase;letter-spacing:1px}}
.mega-offer-title{{font-family:'Montserrat',sans-serif;font-weight:900;font-size:28px;color:#fff;text-align:center;margin-bottom:8px}}
.mega-offer-sub{{font-size:15px;color:rgba(255,255,255,.6);text-align:center;margin-bottom:24px}}
.mega-offer-product{{display:flex;gap:20px;align-items:center;background:#1a1a1a;border-radius:10px;padding:20px;margin-bottom:20px;flex-wrap:wrap}}
.mega-offer-img{{width:130px;height:130px;object-fit:cover;border-radius:8px;flex-shrink:0;border:2px solid #dc2626}}
.mega-offer-img-placeholder{{width:130px;height:130px;background:#111;border:1px dashed #444;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:12px;color:#666;text-align:center;flex-shrink:0}}
.mega-offer-product-name{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:18px;color:#fff;margin-bottom:8px}}
.price-row{{display:flex;align-items:center;gap:12px;margin-bottom:8px}}
.price-original{{font-size:18px;color:rgba(255,255,255,.35);text-decoration:line-through}}
.price-sale{{font-family:'Montserrat',sans-serif;font-weight:900;font-size:32px;color:#dc2626;line-height:1}}
.price-save{{background:#dc2626;color:#fff;font-size:12px;font-weight:700;padding:3px 10px;border-radius:20px;font-family:'Montserrat',sans-serif}}
.mega-offer-product-desc{{font-size:14px;color:rgba(255,255,255,.55);line-height:1.6}}
.mega-stock-alert{{background:#1a0000;border:1px solid rgba(220,38,38,.4);border-radius:8px;padding:14px 18px;margin-bottom:20px;text-align:center}}
.mega-stock-title{{font-family:'Montserrat',sans-serif;font-weight:800;font-size:14px;color:#dc2626;margin-bottom:8px}}
.mega-stock-bar{{height:10px;background:#333;border-radius:5px;overflow:hidden;margin:8px 0}}
.mega-stock-fill{{height:100%;background:linear-gradient(90deg,#dc2626,#f97316);border-radius:5px;width:23%;animation:stock-deplete 8s ease-in-out infinite alternate}}
.mega-countdown-row{{display:flex;justify-content:center;gap:8px;margin-bottom:20px}}
.mega-cd-block{{background:#1a1a1a;border:1px solid #333;border-radius:6px;padding:10px 14px;text-align:center;min-width:58px}}
.mega-cd-num{{font-family:'Montserrat',sans-serif;font-weight:900;font-size:26px;color:#dc2626;line-height:1;display:block}}
.mega-cd-unit{{font-size:10px;text-transform:uppercase;color:rgba(255,255,255,.35);letter-spacing:1px;display:block;margin-top:3px}}
.mega-cd-sep{{font-family:'Montserrat',sans-serif;font-size:26px;font-weight:900;color:rgba(255,255,255,.2);display:flex;align-items:center;padding-bottom:16px}}
.cta-mega{{display:block;width:100%;padding:20px;background:#dc2626;color:#fff;text-align:center;font-family:'Montserrat',sans-serif;font-size:20px;font-weight:900;border-radius:8px;text-decoration:none;margin:8px 0;transition:background .2s;text-transform:uppercase;letter-spacing:.5px;animation:pulse-cta 3s ease-in-out infinite}}
@keyframes pulse-cta{{0%,100%{{box-shadow:0 0 0 0 rgba(220,38,38,.4)}} 50%{{box-shadow:0 0 0 12px rgba(220,38,38,.0)}}}}
.cta-mega:hover{{background:#b91c1c}}
.cta-guarantee{{text-align:center;font-size:13px;color:rgba(255,255,255,.4);margin:8px 0 16px}}
.trust-badges-row{{display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin-top:14px}}
.trust-badge-item{{display:flex;align-items:center;gap:5px;background:#1a1a1a;border:1px solid #2a2a2a;border-radius:6px;padding:8px 14px;font-size:13px;color:rgba(255,255,255,.6);font-weight:600}}
.recent-buyers{{background:#1a1a1a;border-radius:8px;padding:14px 18px;margin-top:16px;display:flex;align-items:center;gap:10px}}
.buyers-avatars{{display:flex}}
.buyer-avatar{{width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#dc2626,#f97316);border:2px solid #0d0d0d;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:10px;color:#fff;margin-left:-8px}}
.buyer-avatar:first-child{{margin-left:0}}
.buyers-text{{font-size:14px;color:rgba(255,255,255,.6)}}
.buyers-text strong{{color:#fff}}

/* ── STICKY FOOTER ── */
.sticky-footer{{position:fixed;bottom:0;left:0;right:0;background:#dc2626;padding:0;text-align:center;z-index:100;display:flex;align-items:stretch}}
.sticky-footer a{{flex:1;color:#fff;text-decoration:none;font-family:'Montserrat',sans-serif;font-weight:800;font-size:15px;padding:14px 20px;display:flex;align-items:center;justify-content:center;gap:8px;text-transform:uppercase;letter-spacing:.5px}}
.sticky-footer-timer{{background:#b91c1c;padding:14px 20px;display:flex;align-items:center;gap:6px;font-size:13px;font-family:'Montserrat',sans-serif;font-weight:700;color:rgba(255,255,255,.8)}}
.sticky-timer-val{{font-size:16px;font-weight:900;color:#fff;letter-spacing:1px}}

/* ── RESPONSIVE ── */
@media(max-width:740px){{
h1{{font-size:26px}}
h2{{font-size:20px}}
.sale-hero{{padding:32px 16px}}
.sale-badge-pct{{font-size:40px}}
.article-content{{padding:20px 16px}}
.mega-offer{{padding:32px 16px}}
.mega-offer-title{{font-size:23px}}
.mega-cd-num{{font-size:22px}}
.mega-offer-product{{flex-direction:column}}
.mega-offer-img,.mega-offer-img-placeholder{{width:100%;height:200px}}
.cta-mega{{font-size:17px;padding:17px}}
.inline-urgency-cta{{flex-direction:column;align-items:flex-start}}
.iuc-btn{{width:100%;text-align:center}}
.sticky-footer-timer{{display:none}}
}}
</style>
</head>
<body>

<!-- COUNTDOWN TICKER -->
<div class="countdown-ticker">
  <div class="countdown-ticker-inner">
    <span class="countdown-label">⚡ Sale Ends In:</span>
    <div class="countdown-timer">
      <div class="cd-block"><span class="cd-num" id="cd-h">00</span><span class="cd-unit">Hrs</span></div>
      <span class="cd-colon">:</span>
      <div class="cd-block"><span class="cd-num" id="cd-m">14</span><span class="cd-unit">Min</span></div>
      <span class="cd-colon">:</span>
      <div class="cd-block"><span class="cd-num" id="cd-s">47</span><span class="cd-unit">Sec</span></div>
    </div>
    <span class="countdown-label">⚡ Before Price Goes Up</span>
  </div>
</div>

<!-- HERO -->
<div class="sale-hero">
  <div class="sale-badge">
    <div class="sale-badge-pct">55%</div>
    <div class="sale-badge-text">
      <span class="sale-badge-off">OFF</span>
      <span class="sale-badge-type">Flash Sale</span>
    </div>
  </div>
  <h1>{headline}</h1>
  {"<p class='hero-sub'>" + subheadline + "</p>" if subheadline else ""}
</div>

<!-- SOCIAL PROOF BAR -->
<div class="social-proof-bar">
  <div class="social-proof-bar-inner">
    <div class="sp-item">🔥 <strong>4,847</strong> bought today</div>
    <div class="sp-item">⭐ <strong>4.9/5</strong> stars (2,341 reviews)</div>
    <div class="sp-item">📦 <strong>Ships Free</strong> — Today Only</div>
  </div>
</div>

<!-- ARTICLE -->
<div class="article-content">

  <!-- STOCK ALERT -->
  <div class="stock-alert">
    <div class="stock-alert-title">⚠️ INVENTORY ALERT: Only 23% Remaining</div>
    <div class="stock-bar"><div class="stock-fill"></div></div>
    <div class="stock-alert-sub">We cannot guarantee availability after this sale ends</div>
  </div>

  {article_body}

  <!-- MEGA OFFER BOX -->
  <div class="mega-offer">
    <div class="mega-offer-inner">

      <div class="mega-offer-eyebrow">
        <span class="mega-offer-badge">🔥 Today Only — Flash Sale</span>
      </div>
      <div class="mega-offer-title">{tx["offer_title"]}</div>
      <div class="mega-offer-sub">{tx["offer_desc"]}</div>

      <!-- COUNTDOWN -->
      <div class="mega-countdown-row">
        <div class="mega-cd-block"><span class="mega-cd-num" id="mcd-h">00</span><span class="mega-cd-unit">Hours</span></div>
        <div class="mega-cd-sep">:</div>
        <div class="mega-cd-block"><span class="mega-cd-num" id="mcd-m">14</span><span class="mega-cd-unit">Minutes</span></div>
        <div class="mega-cd-sep">:</div>
        <div class="mega-cd-block"><span class="mega-cd-num" id="mcd-s">47</span><span class="mega-cd-unit">Seconds</span></div>
      </div>

      <!-- PRODUCT ROW -->
      <div class="mega-offer-product">
        {'<img src="' + product_image_url + '" alt="' + product_name + '" class="mega-offer-img">' if product_image_url else '<div class="mega-offer-img-placeholder"><div class="tbadge">' + tx.get("bundle_badge","PRODUCT") + '</div></div>'}
        <div>
          <div class="mega-offer-product-name">{product_name}</div>
          <div class="price-row">
            <span class="price-original">$199.99</span>
            <span class="price-sale">$89.99</span>
            <span class="price-save">SAVE 55%</span>
          </div>
          <div class="mega-offer-product-desc">{cta_body}</div>
        </div>
      </div>

      <!-- STOCK -->
      <div class="mega-stock-alert">
        <div class="mega-stock-title">⚠️ ALMOST GONE — Only 23% of inventory left</div>
        <div class="mega-stock-bar"><div class="mega-stock-fill"></div></div>
      </div>

      <a href="{product_url}" class="cta-mega">{tx["cta"]} — Save 55% NOW</a>
      <div class="cta-guarantee">🔒 100% Money-Back Guarantee · No questions asked</div>

      <!-- TRUST BADGES -->
      <div class="trust-badges-row">
        <div class="trust-badge-item">🔒 {tx["badge1"]}</div>
        <div class="trust-badge-item">✅ {tx["badge2"]}</div>
        {"<div class='trust-badge-item'>📦 " + tx.get("badge3","") + "</div>" if tx.get("badge3") else ""}
      </div>

      <!-- RECENT BUYERS -->
      <div class="recent-buyers">
        <div class="buyers-avatars">
          <div class="buyer-avatar">S</div>
          <div class="buyer-avatar">M</div>
          <div class="buyer-avatar">R</div>
          <div class="buyer-avatar">J</div>
          <div class="buyer-avatar">+</div>
        </div>
        <div class="buyers-text"><strong>4,847 people</strong> bought this today — don't miss out!</div>
      </div>

    </div><!-- /mega-offer-inner -->
  </div><!-- /mega-offer -->

</div><!-- /article-content -->

<div class="sticky-footer">
  <div class="sticky-footer-timer">
    ⏱ <span class="sticky-timer-val" id="sticky-timer">00:14:47</span>
  </div>
  <a href="{product_url}">🔥 {tx["cta_footer"]} — 55% OFF</a>
</div>

<script>
(function() {{
  // Countdown timer — starts from 14min47sec from page load
  var endTime = Date.now() + (14 * 60 + 47) * 1000;

  function pad(n) {{ return String(Math.floor(n)).padStart(2, '0'); }}

  function tick() {{
    var now = Date.now();
    var diff = Math.max(0, endTime - now);
    var h = diff / 3600000;
    var m = (diff % 3600000) / 60000;
    var s = (diff % 60000) / 1000;

    var hStr = pad(h);
    var mStr = pad(m);
    var sStr = pad(s);

    // Top ticker
    var cdH = document.getElementById('cd-h');
    var cdM = document.getElementById('cd-m');
    var cdS = document.getElementById('cd-s');
    if (cdH) cdH.textContent = hStr;
    if (cdM) cdM.textContent = mStr;
    if (cdS) cdS.textContent = sStr;

    // Mega box
    var mH = document.getElementById('mcd-h');
    var mM = document.getElementById('mcd-m');
    var mS = document.getElementById('mcd-s');
    if (mH) mH.textContent = hStr;
    if (mM) mM.textContent = mStr;
    if (mS) mS.textContent = sStr;

    // Sticky footer
    var st = document.getElementById('sticky-timer');
    if (st) st.textContent = hStr + ':' + mStr + ':' + sStr;

    if (diff > 0) {{
      setTimeout(tick, 1000);
    }}
  }}

  tick();
}})();
</script>

</body>
</html>'''
