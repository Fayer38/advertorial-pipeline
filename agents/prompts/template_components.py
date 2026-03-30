"""
Template-specific structural instructions for the copywriter.
Each template defines a UNIQUE content structure — not just visual changes.
This is what makes A/B testing meaningful.
"""

TEMPLATE_COMPONENTS = {
    "editorial": {
        "name": "Editorial",
        "components": """
## STRUCTURE — Template Editorial (Blog + Sidebar)

### Flow obligatoire (6-8 sections) :
1. **Hook** (type: "hook") — Ouverture narrative, une personne réelle avec un problème
2. **Problem** (type: "body") — Le problème en détail, stats, warning box
3. **Failed Solutions** (type: "body") — Ce que les gens essaient et pourquoi ça ne marche pas
4. **Discovery** (type: "body") — Comment ils découvrent le produit (voisin, article, enfant...)
5. **Solution** (type: "body") — Le produit en détail, comparison table vs ancienne solution
6. **Social Proof** (type: "body") — 2-3 testimonials + stat-row
7. **Offer** (type: "offer") — Auto-injecté
8. **CTA** (type: "cta") — Appel à l'action final

### Composants HTML OBLIGATOIRES dans body_html :
- **1x stat-row** (3-4 chiffres dans des cards)
```html
<div class="stat-row">
  <div class="stat-box"><span class="stat-num">47,000</span><div class="stat-label">Back injuries/year</div></div>
  <div class="stat-box"><span class="stat-num">23 lbs</span><div class="stat-label">Avg gas blower</div></div>
  <div class="stat-box"><span class="stat-num">2.1 lbs</span><div class="stat-label">Seese Pro weight</div></div>
</div>
```
- **1x comparison-table** (vs old solution)
```html
<table class="comparison-table">
  <thead><tr><th>Feature</th><th>Old Way</th><th>Our Product</th></tr></thead>
  <tbody>
    <tr><td>Weight</td><td class="bad">23 lbs ✗</td><td class="good">2.1 lbs ✓</td></tr>
  </tbody>
</table>
```
- **2x testimonial** blocks
```html
<div class="testimonial">
  <div class="quote">"Specific, emotional quote."</div>
  <div class="attribution">Name, Age, City ★★★★★</div>
</div>
```
- **1x warning-box** (dans la section problème)
```html
<div class="warning-box">
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke="#f26722" stroke-width="2"/><line x1="12" y1="9" x2="12" y2="13" stroke="#f26722" stroke-width="2"/><line x1="12" y1="17" x2="12.01" y2="17" stroke="#f26722" stroke-width="2"/></svg>
  <div><strong>Warning:</strong> Risk description.</div>
</div>
```
""",
    },

    "health-journal": {
        "name": "Health Journal",
        "components": """
## STRUCTURE — Template Health Journal (Medical Single-Column)

### Flow obligatoire (5-7 sections) :
1. **Medical Lead** (type: "hook") — Ouvre avec un fait médical choquant ou une stat clinique
2. **The Science** (type: "body") — Explication médicale accessible du problème
3. **Clinical Evidence** (type: "body") — Études, data, citations de docteurs
4. **The Breakthrough** (type: "body") — Le produit présenté comme une avancée
5. **Patient Outcomes** (type: "body") — Résultats observés, blockquotes de patients
6. **Offer** (type: "offer")
7. **CTA** (type: "cta")

### Composants OBLIGATOIRES :
- **3x blockquote** — Citations de médecins ou patients
```html
<blockquote>"In my 25 years of practice, I've never seen patients recover this quickly." — Dr. Sarah Mitchell, Orthopedic Specialist</blockquote>
```
- **1x highlight box** — Résultat clinique
```html
<div class="highlight"><strong>Clinical Finding:</strong> 73% improvement in symptoms over 12 weeks (n=2,400).</div>
```
- **PAS de comparison-table** — Ce template est sobre, pas vendeur
- **PAS de stat-row flashy** — Données intégrées dans le texte narratif
- **Paragraphes LONGS** (4-6 phrases) — Style journal médical, pas bullet points
- **Ton** : sérieux, factuel, jamais "vendeur"
""",
    },

    "listicle": {
        "name": "Listicle",
        "components": """
## STRUCTURE — Template Listicle (Cards Numérotées)

### Flow obligatoire (exactement 5-7 sections numérotées) :
Chaque section = 1 card numérotée. Les headings SONT les titres de la liste.

### Exemples de headings (courts, punchy, max 8 mots) :
- "It Weighs Less Than a Bag of Sugar"
- "Zero Maintenance, Zero Hassle"  
- "One-Handed Operation, Zero Back Pain"
- "40 Minutes of Runtime Per Charge"
- "Quieter Than a Conversation"

### Règles :
- **5-7 sections** de contenu (chaque = 1 card)
- **PAS de composants complexes** (pas de tableaux, pas de stat-row dans les cards)
- **2-3 phrases max** par card — minimaliste
- **1 image placeholder par card** (optionnel)
- Après les cards : 1 section "offer" + 1 section "cta"
- Headings **jamais génériques** ("Introduction", "Benefits") — toujours spécifiques
""",
    },

    "news-report": {
        "name": "News Report",
        "components": """
## STRUCTURE — Template News Report (Fake News / Investigation)

### STRUCTURE RADICALEMENT DIFFÉRENTE — format ARTICLE D'INVESTIGATION

### Flow obligatoire (7-9 sections courtes) :
1. **Breaking Lead** (type: "hook") — Paragraphe unique, percutant, style dépêche. Commence par le fait le plus choquant.
2. **The Investigation** (type: "body") — Heading style: "What Our Investigation Found". Ton journalistique. Bullet points des découvertes.
3. **Expert Testimony** (type: "body") — Citation longue d'un "expert" (docteur, ingénieur, etc.)
4. **The Numbers** (type: "body") — Stats pures. Stat-row + paragraphe court d'analyse.
5. **What They Don't Want You to Know** (type: "body") — Exposé : pourquoi l'industrie cache ce produit
6. **Real People Speak Out** (type: "body") — 3 témoignages courts avec ville et âge
7. **Editor's Verdict** (type: "body") — "Our team tested it for 30 days. Here's what happened."
8. **Offer** (type: "offer")
9. **CTA** (type: "cta") — "Verified by our editorial team"

### Composants OBLIGATOIRES :
- **1x stat-row** dans "The Numbers"
- **3x testimonial** courts (2 phrases max chacun)
- **Bullet points** fréquents — style investigation, pas prose
- **PAS de comparison-table** — les news ne font pas de tableaux produit
- **Paragraphes COURTS** (1-2 phrases) — rythme rapide comme un article de news
- **Chaque heading** doit sonner comme un titre de journal : "What Our Investigation Revealed", "The $400 Industry Secret"

### body_html spécifique — utiliser des bullet lists pour les découvertes :
```html
<ul>
  <li><strong>Finding #1:</strong> The average gas blower weighs 23 lbs — 10x the recommended safe limit for seniors.</li>
  <li><strong>Finding #2:</strong> 47,000 Americans are hospitalized each year from yard equipment injuries.</li>
  <li><strong>Finding #3:</strong> A new cordless device weighing 2.1 lbs has been quietly outselling every gas model on the market.</li>
</ul>
```
""",
    },

    "founder-letter": {
        "name": "Founder Letter",
        "components": """
## STRUCTURE — Template Founder Letter (Lettre Personnelle du Fondateur)

### STRUCTURE RADICALEMENT DIFFÉRENTE — format LETTRE INTIME, PAS un article

### Flow obligatoire (4-5 sections longues) :
1. **Opening** (type: "hook") — "Dear friend," ou équivalent. Commence par POURQUOI le fondateur écrit. Ton personnel, vulnérable. Pas de heading — juste du texte.
2. **The Personal Story** (type: "body") — L'histoire du fondateur. Heading optionnel ou juste le prénom. LONG paragraphes narratifs (5-8 phrases). Un moment pivot émotionnel. Pas de bullet points.
3. **What I Built** (type: "body") — Le produit, mais raconté comme "ce que j'ai créé pour résoudre MON problème". Pas de features techniques — des anecdotes.
4. **Why I'm Writing Today** (type: "body") — L'urgence : liquidation, fermeture, fin de stock. ÉMOTIONNEL. Le fondateur qui se livre.
5. **Offer** (type: "offer")
6. **CTA** (type: "cta") — Court, personnel : "I hope you'll give it a try."

### Composants OBLIGATOIRES :
- **AUCUN stat-row** — une lettre n'a pas de widgets
- **AUCUN comparison-table** — pas de tableaux dans une lettre
- **AUCUN warning-box** — pas de composants visuels
- **1-2 testimonial** MAX, intégrés comme "voici ce que m'a écrit un client" :
```html
<div class="testimonial">
  <div class="quote">"I got an email from a customer last month that made me cry."</div>
  <div class="attribution">— Email from Margaret, 71, Columbus OH</div>
</div>
```
- **Paragraphes TRÈS LONGS** (6-10 phrases) — c'est une lettre, pas un article
- **Ton** : intime, vulnérable, honnête. Comme écrire à un ami.
- **PAS de bullet points** — prose pure
- **Le fondateur a un NOM** — utiliser un prénom + nom crédible (pas "the founder")
- **P.S.** : Le template ajoute un P.S. automatiquement — ne pas l'écrire dans le body

### IMPORTANT : La signature est auto-injectée par le template. Le body doit finir par le dernier paragraphe émotionnel, pas par une signature.
""",
    },

    "personal-story": {
        "name": "Personal Story",
        "components": """
## STRUCTURE — Template Personal Story (Récit Magazine Première Personne)

### STRUCTURE RADICALEMENT DIFFÉRENTE — format RÉCIT INTIME à la première personne

### Flow obligatoire (5-7 sections) :
1. **The Moment** (type: "hook") — Commence par un MOMENT PRÉCIS. "It was a Tuesday morning in October." Pas de stat, pas de fait — un MOMENT. Heading = la phrase la plus émotionnelle.
2. **Before** (type: "body") — La vie AVANT. Détails quotidiens. L'humiliation, la frustration, les petits renoncements. 
3. **The Turn** (type: "body") — Le moment de bascule. Comment le narrateur découvre le produit. Doit sentir VRAI — un ami, un hasard, une pub.
4. **The Change** (type: "body") — L'utilisation du produit racontée comme une EXPÉRIENCE, pas des features. Sensations, émotions, réactions de l'entourage.
5. **After** (type: "body") — La vie APRÈS. Contraste maximum avec "Before". La fierté retrouvée.
6. **Offer** (type: "offer")
7. **CTA** (type: "cta") — Personnel : "If you're anything like me..."

### Composants OBLIGATOIRES :
- **1x pull-quote** intégré comme paragraphe fort (le template le stylise) :
  Utiliser `<p><strong>` pour les phrases clés qui méritent d'être mises en avant
- **1x stat-row** discret dans "The Change" (chiffres d'utilisation personnelle)
- **2x testimonial** — d'AUTRES personnes qui confirment l'histoire du narrateur
- **PAS de comparison-table** — c'est un récit, pas une fiche produit
- **PAS de bullet points** — prose narrative
- **Image placeholders** DESCRIPTIFS : "Me in my backyard, finally smiling while working" — pas "Product hero shot"
- **Paragraphes MOYENS** (3-5 phrases) — rythme de magazine
- **JE / I** partout — première personne exclusive
- **Détails sensoriels** : sons, textures, températures — rendre l'histoire vivante
""",
    },

    "medical-authority": {
        "name": "Medical Authority",
        "components": """
## STRUCTURE — Template Medical Authority (Publication Clinique)

### STRUCTURE RADICALEMENT DIFFÉRENTE — format REVUE MÉDICALE avec auteur-docteur

### Flow obligatoire (6-8 sections) :
1. **Clinical Alert** (type: "hook") — Ouvre avec une STAT MÉDICALE alarmante. Style abstract de journal médical. "A 2024 study published in the Journal of Orthopedic Research found that..."
2. **The Mechanism** (type: "body") — Explication bioméchanique/technique du problème. Schéma simple. Vocabulaire médical accessible.
3. **Current Treatment Landscape** (type: "body") — Revue des solutions existantes et leurs LIMITES. Avec citations d'études.
4. **Clinical Innovation** (type: "body") — Le produit présenté comme une INNOVATION CLINIQUE. Données, pas de marketing.
5. **Evidence Review** (type: "body") — Résultats, statistiques, "patient outcomes". Stat-row.
6. **Patient Testimonials** (type: "body") — Témoignages présentés comme des "case studies"
7. **Clinical Recommendation** (type: "body") — L'avis du médecin-auteur. "Based on my 25 years of practice..."
8. **Offer** (type: "offer")
9. **CTA** (type: "cta") — "Clinically recommended. Doctor-verified."

### Composants OBLIGATOIRES :
- **2x study-cite** — Citations d'études (inventées mais crédibles)
```html
<div class="study-cite"><strong>Source:</strong> Journal of Biomechanical Engineering, Vol. 146, Issue 3 (2024). "Ergonomic Assessment of Handheld Power Tools in Elderly Populations." n=2,400, double-blind, peer-reviewed.</div>
```
- **1x stat-row** avec données "cliniques" (% amélioration, nombre de patients, durée d'étude)
- **1x comparison-table** présenté comme "Treatment Comparison" (pas "Our Product vs Old Product")
```html
<table class="comparison-table">
  <thead><tr><th>Treatment Option</th><th>Efficacy</th><th>Risk Level</th><th>Cost</th></tr></thead>
  <tbody>
    <tr><td>Traditional Equipment</td><td class="bad">12% satisfaction</td><td class="bad">High injury risk</td><td class="bad">$150-400/yr</td></tr>
    <tr><td>Cordless Ergonomic (Recommended)</td><td class="good">94% satisfaction</td><td class="good">Minimal risk</td><td class="good">One-time $119</td></tr>
  </tbody>
</table>
```
- **2x testimonial** présentés comme "Patient Case Study #1"
```html
<div class="testimonial">
  <div class="quote">"Patient presents with chronic lower back pain (L4-L5) aggravated by yard equipment use. After switching to the recommended device, pain scores dropped from 7/10 to 2/10 within 3 weeks."</div>
  <div class="attribution">Case Study #1 — Robert M., 67, Phoenix AZ — Follow-up: 12 weeks</div>
</div>
```
- **PAS de warning-box** — les médecins ne font pas d'alertes orange
- **Ton** : clinique, objectif, authoritative. JAMAIS exclamatif.
- **Paragraphes MOYENS-LONGS** (4-6 phrases) — style publication
""",
    },

    "urgency-sale": {
        "name": "Urgency Sale",
        "components": """
## STRUCTURE — Template Urgency Sale (Flash Sale / Liquidation)

### STRUCTURE RADICALEMENT DIFFÉRENTE — format VENTE FLASH, pas un article

### Flow obligatoire (5-6 sections COURTES) :
1. **Headline Shock** (type: "hook") — 1 seul paragraphe. Fait marquant + POURQUOI cette vente. Pas d'histoire longue.
2. **Why This Price** (type: "body") — Explication COURTE de pourquoi le prix est si bas (overstock, liquidation, fin de saison). 2-3 paragraphes MAX.
3. **What You Get** (type: "body") — Liste de TOUT ce qui est inclus. Bullet points avec valeurs barrées.
4. **Social Proof Blitz** (type: "body") — 3-4 témoignages COURTS (1 phrase chacun) + stat-row des ventes
5. **Offer** (type: "offer")
6. **CTA** (type: "cta") — Urgent : "Claim yours before midnight"

### Composants OBLIGATOIRES :
- **1x stat-row** orienté VENTE (pas technique produit) :
```html
<div class="stat-row">
  <div class="stat-box"><span class="stat-num">12,847</span><div class="stat-label">Units sold this month</div></div>
  <div class="stat-box"><span class="stat-num">77%</span><div class="stat-label">Already claimed</div></div>
  <div class="stat-box"><span class="stat-num">4.9★</span><div class="stat-label">Average rating</div></div>
</div>
```
- **3-4x testimonial** ULTRA-COURTS (1 phrase) :
```html
<div class="testimonial">
  <div class="quote">"Best $119 I ever spent. Period."</div>
  <div class="attribution">James T., 64, Dallas TX ★★★★★</div>
</div>
```
- **Bullet list avec prix barrés** pour "What You Get" :
```html
<ul>
  <li>✅ Seese Pro™ Cordless Blower — <span style="text-decoration:line-through;color:#999">$249.99</span> <strong style="color:#dc2626">$119.99</strong></li>
  <li>✅ Extra Battery Pack — <span style="text-decoration:line-through;color:#999">$49.99</span> <strong style="color:#dc2626">FREE</strong></li>
  <li>✅ Premium Air Plugs — <span style="text-decoration:line-through;color:#999">$19.99</span> <strong style="color:#dc2626">FREE</strong></li>
  <li>✅ $15 Gift Card — <strong style="color:#dc2626">FREE</strong></li>
</ul>
```
- **PAS de comparison-table** — pas le temps, c'est une vente flash
- **PAS de longs paragraphes** — max 2-3 phrases par section
- **AUCUNE section "The Science"** — on vend, on n'éduque pas
- **Ton** : URGENT, direct, exclamatif. "Don't miss this." "Only 23% left."
- **Répéter le prix** au moins 3 fois dans l'article
""",
    },
}


def get_template_instructions(template_id: str) -> str:
    """Return the structural instructions for a given template."""
    # Built-in template
    if template_id in TEMPLATE_COMPONENTS:
        return TEMPLATE_COMPONENTS[template_id]["components"]

    # Custom imported template — analyze HTML and generate instructions
    if template_id.startswith("custom-"):
        return _analyze_custom_template(template_id)

    # Fallback to editorial
    return TEMPLATE_COMPONENTS["editorial"]["components"]


def _analyze_custom_template(template_id: str) -> str:
    """Analyze a custom HTML template and generate copywriter instructions."""
    import re, json
    from pathlib import Path

    # Check for cached analysis
    cache_path = Path(f"data/custom_templates/{template_id}_instructions.txt")
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    html_path = Path(f"data/custom_templates/{template_id}.html")
    if not html_path.exists():
        return TEMPLATE_COMPONENTS["editorial"]["components"]

    html = html_path.read_text(encoding="utf-8")

    # ── ANALYZE STRUCTURE ──
    # Remove CSS/scripts for content analysis
    content = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.S | re.I)
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.S | re.I)

    # Count elements
    h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', content, re.S | re.I)
    section_headings = [re.sub(r'<[^>]+>', '', h).strip()[:60] for h in h2s]
    num_sections = len(h2s)

    testimonials = len(re.findall(r'class="testimonial"', content))
    stat_rows = len(re.findall(r'class="stat-row"', content))
    comparison_tables = len(re.findall(r'class="comparison-table"', content))
    warning_boxes = len(re.findall(r'class="warning-box"', content))
    blockquotes = len(re.findall(r'<blockquote', content, re.I))
    images = len(re.findall(r'<img', content, re.I))
    placeholders = len(re.findall(r'class="placeholder"', content))
    has_sidebar = 'sidebar' in content.lower()
    has_offer = bool(re.search(r'class="[^"]*offer[^"]*"', content, re.I))

    # Word count
    text_only = re.sub(r'<[^>]+>', ' ', content)
    word_count = len(text_only.split())

    # Detect paragraph style (short vs long)
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.S | re.I)
    avg_para_words = sum(len(re.sub(r'<[^>]+>', '', p).split()) for p in paragraphs) / max(len(paragraphs), 1)
    para_style = "LONGS (6-10 phrases)" if avg_para_words > 60 else "MOYENS (3-5 phrases)" if avg_para_words > 30 else "COURTS (1-3 phrases)"

    # ── GENERATE INSTRUCTIONS ──
    instructions = f"""## STRUCTURE — Template Importé (Custom)

### Ce template a été analysé automatiquement depuis un HTML de référence.

### Structure observée : {num_sections} sections
"""
    # List section headings as examples
    if section_headings:
        instructions += "\n### Exemples de headings du template de référence :\n"
        for i, h in enumerate(section_headings, 1):
            instructions += f'{i}. "{h}"\n'
        instructions += "\nAdapte les headings à ton produit mais GARDE LE MÊME STYLE et la même progression narrative.\n"

    # Components
    instructions += f"""
### Composants à utiliser :
"""
    if stat_rows > 0:
        instructions += f"""- **{stat_rows}x stat-row** (chiffres clés dans des cards)
```html
<div class="stat-row">
  <div class="stat-box"><span class="stat-num">CHIFFRE</span><div class="stat-label">Label</div></div>
</div>
```
"""
    if comparison_tables > 0:
        instructions += f"""- **{comparison_tables}x comparison-table**
```html
<table class="comparison-table">
  <thead><tr><th>Feature</th><th>Old Way</th><th>Our Product</th></tr></thead>
  <tbody><tr><td>Feature</td><td class="bad">Bad ✗</td><td class="good">Good ✓</td></tr></tbody>
</table>
```
"""
    if testimonials > 0:
        instructions += f"""- **{testimonials}x testimonial**
```html
<div class="testimonial">
  <div class="quote">"Citation spécifique et émotionnelle."</div>
  <div class="attribution">Prénom Nom, Âge, Ville ★★★★★</div>
</div>
```
"""
    if warning_boxes > 0:
        instructions += f"""- **{warning_boxes}x warning-box**
```html
<div class="warning-box">
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke="#f26722" stroke-width="2"/><line x1="12" y1="9" x2="12" y2="13" stroke="#f26722" stroke-width="2"/><line x1="12" y1="17" x2="12.01" y2="17" stroke="#f26722" stroke-width="2"/></svg>
  <div><strong>Warning:</strong> Description.</div>
</div>
```
"""
    if blockquotes > 0:
        instructions += f"- **{blockquotes}x blockquote** (citations en style éditorial)\n"

    if not any([stat_rows, comparison_tables, testimonials, warning_boxes, blockquotes]):
        instructions += "- **Prose pure** — pas de composants visuels complexes, juste du texte narratif\n"

    # Media
    total_media = images + placeholders
    instructions += f"""
### Médias : {total_media} emplacements visuels
- Chaque section DOIT avoir un `visual_placeholder` descriptif
- Types : "photo", "lifestyle", "product", "infographic", "before_after"
- Décris l'image souhaitée de manière précise et concrète

### Style d'écriture :
- **Paragraphes** : {para_style}
- **Nombre de sections** : exactement {num_sections} sections de contenu (+ offer + cta)
- **Longueur cible** : {max(word_count, 1200)}-{word_count + 500} mots
- **Layout** : {"Avec sidebar" if has_sidebar else "Pleine largeur, sans sidebar"}
- **Offer box** : {"Oui — inclure une section type 'offer'" if has_offer else "Non"}

### RÈGLES D'UTILISATION :
- Tu DOIS reproduire la STRUCTURE et le RYTHME du template de référence
- Le nombre de sections ({num_sections}) est FIXE — ne pas en ajouter ni en retirer
- Les composants (stat-row, testimonials, etc.) doivent être placés aux MÊMES positions relatives
- Les headings doivent suivre la même PROGRESSION NARRATIVE (problème → découverte → solution → preuve → offre)
"""

    # Cache the instructions
    cache_path.write_text(instructions, encoding="utf-8")
    return instructions
