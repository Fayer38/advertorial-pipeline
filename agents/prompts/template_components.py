"""
Template-specific HTML component instructions for the copywriter.
Each template has a set of rich HTML components the copywriter MUST use in body_html.
"""

TEMPLATE_COMPONENTS = {
    "editorial": {
        "name": "Editorial",
        "description": "Blog-style article with sticky sidebar. Roboto + Montserrat. Orange #f26722 accent.",
        "components": """
## COMPOSANTS HTML DISPONIBLES — Template Editorial

Tu DOIS utiliser ces composants HTML dans le `body_html` de tes sections pour rendre l'article visuellement riche et professionnel. Ne te contente PAS de paragraphes <p> et <h2>. Varie les formats.

### 1. Stat Row (chiffres clés) — OBLIGATOIRE au moins 1x
Affiche 3-4 stats dans des cards oranges alignées. Parfait après une section problème ou données.
```html
<div class="stat-row">
  <div class="stat-box"><span class="stat-num">47,000</span><div class="stat-label">Back injuries per year</div></div>
  <div class="stat-box"><span class="stat-num">23 lbs</span><div class="stat-label">Average gas blower weight</div></div>
  <div class="stat-box"><span class="stat-num">$1,200+</span><div class="stat-label">Annual service cost</div></div>
  <div class="stat-box"><span class="stat-num">#1</span><div class="stat-label">Cause: starter cord pull</div></div>
</div>
```

### 2. Comparison Table — OBLIGATOIRE au moins 1x
Tableau comparatif avec classes .good (vert) et .bad (rouge). Parfait pour la section solution.
```html
<table class="comparison-table">
  <thead><tr><th>Feature</th><th>Old Solution</th><th>Our Product</th></tr></thead>
  <tbody>
    <tr><td>Weight</td><td class="bad">23 lbs</td><td class="good">2.1 lbs</td></tr>
    <tr><td>Start Method</td><td class="bad">Cord pull (injury risk)</td><td class="good">Button press (safe)</td></tr>
    <tr><td>Noise</td><td class="bad">90+ decibels</td><td class="good">64 decibels</td></tr>
    <tr><td>Annual Cost</td><td class="bad">$150-200 maintenance</td><td class="good">$0</td></tr>
  </tbody>
</table>
```

### 3. Testimonial Block — OBLIGATOIRE au moins 2x
Citations de clients. Fond rosé, bordure orange gauche.
```html
<div class="testimonial">
  <div class="quote">"The quote from the customer goes here. Make it specific, emotional, and believable."</div>
  <div class="attribution">Robert Martinez, 67, Phoenix, Arizona ★★★★★</div>
</div>
```

### 4. Warning Box — Recommandé 1x
Encadré d'alerte avec icône SVG. Parfait pour la section problème.
```html
<div class="warning-box">
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke="#f26722" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="9" x2="12" y2="13" stroke="#f26722" stroke-width="2" stroke-linecap="round"/><line x1="12" y1="17" x2="12.01" y2="17" stroke="#f26722" stroke-width="2" stroke-linecap="round"/></svg>
  <div><strong>Warning:</strong> Description of the risk or important fact that adds urgency.</div>
</div>
```

### 5. Tip Box
```html
<div class="tip"><svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#f26722" stroke-width="2"/><line x1="12" y1="8" x2="12" y2="12" stroke="#f26722" stroke-width="2" stroke-linecap="round"/><line x1="12" y1="16" x2="12.01" y2="16" stroke="#f26722" stroke-width="2" stroke-linecap="round"/></svg> <div><strong>Tip:</strong> Useful advice that builds trust.</div></div>
```

### RÈGLES D'UTILISATION
- Tu DOIS utiliser **au minimum** : 1 stat-row, 1 comparison-table, 2 testimonials
- Les testimonials doivent avoir des noms réalistes, des âges, des villes US, et ★★★★★
- Le comparison-table doit comparer le produit à l'ancienne solution (pas à des concurrents nommés)
- Les stat-box doivent contenir des chiffres spécifiques et crédibles (pas inventés à la légère)
- Le warning-box est idéal après la section problème pour renforcer l'urgence
- NE PAS mettre ces composants dans le heading des sections — UNIQUEMENT dans body_html
""",
    },

    "health-journal": {
        "name": "Health Journal",
        "description": "Medical/wellness single-column. Merriweather serif + Inter. Green #3d8b6e accent.",
        "components": """
## COMPOSANTS HTML DISPONIBLES — Template Health Journal

Tu DOIS utiliser ces composants dans le `body_html`. Ce template est sobre et médical — les composants renforcent la crédibilité.

### 1. Blockquote / Pullquote — OBLIGATOIRE au moins 2x
Citation mise en valeur avec bordure verte gauche. Fond crème.
```html
<blockquote>"A compelling medical-style quote from a doctor, expert, or patient testimony."</blockquote>
```

### 2. Highlight Box — Recommandé 1x
Encadré vert clair pour les données scientifiques ou résultats d'études.
```html
<div class="highlight"><strong>Clinical Finding:</strong> In a 12-week study, participants using the product reported 73% improvement in symptoms compared to the control group.</div>
```

### 3. Step Cards — dans la section offer (auto-injecté)
Les steps sont auto-injectés par le template dans la section offer. Pas besoin de les écrire.

### 4. Tip Box
```html
<div class="tip-box">💡 <strong>Doctor's Advice:</strong> Useful medical-sounding tip.</div>
```

### RÈGLES D'UTILISATION
- Au minimum : 2 blockquotes, 1 highlight
- Les blockquotes doivent ressembler à des citations de médecins ou patients
- Le ton doit rester éditorial-médical : sérieux, factuel, pas vendeur
- Utiliser des termes médicaux accessibles (pas de jargon opaque)
- Les paragraphes doivent être plus longs et journalistiques que dans le template Editorial
""",
    },

    "listicle": {
        "name": "Listicle",
        "description": "Numbered cards with purple gradient. Poppins font. Modern & airy.",
        "components": """
## COMPOSANTS HTML DISPONIBLES — Template Listicle

Ce template affiche CHAQUE section comme une card numérotée. La structure est cruciale.

### Structure des sections
Chaque section (sauf offer/cta) sera rendue comme une card numérotée automatiquement.
Tu dois écrire **exactement 5 à 7 sections** de contenu (hors offer/cta).
Chaque section = 1 card = 1 point de la liste.

### Format des headings
Les headings doivent être des phrases courtes et percutantes, style listicle :
- ✅ "It Weighs Less Than a Bag of Sugar"
- ✅ "Zero Maintenance, Zero Hassle"
- ❌ "Product Benefits" (trop générique)
- ❌ "Introduction" (pas de méta-titres)

### body_html dans chaque card
Chaque card doit contenir 1-2 paragraphes courts + optionnellement une image placeholder.
PAS de composants complexes dans les cards (pas de tableaux, pas de stat-row).
Le Listicle est minimaliste — le contenu est dans les mots, pas dans les widgets.

### RÈGLES D'UTILISATION
- Exactement 5-7 sections de contenu (chaque = 1 card numérotée)
- Headings courts et punchy (max 8 mots)
- Paragraphes courts (2-3 phrases max par card)
- Le hook doit être intégré dans la section hero (le template l'affiche en grand)
- L'offer et le CTA sont auto-gérés par le template
""",
    },
}


def get_template_instructions(template_id: str) -> str:
    """Return the HTML component instructions for a given template."""
    tmpl = TEMPLATE_COMPONENTS.get(template_id, TEMPLATE_COMPONENTS["editorial"])
    return tmpl["components"]
