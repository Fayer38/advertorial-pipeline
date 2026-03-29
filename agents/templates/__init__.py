"""
HTML Templates for advertorials.
Each template is a function: build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang, tx) -> str

8 templates based on analysis of 417 real-world advertorials:
- editorial: Classic blog with sidebar (existing)
- health-journal: Medical/wellness clean style (existing)
- listicle: Numbered cards (existing)
- news-report: Fake news site with view counter, urgency bar (NEW — 118 advs use this pattern)
- founder-letter: Personal letter from founder (NEW — 22 advs, high emotional impact)
- personal-story: First-person narrative, magazine hero (NEW — 85 advs use this)
- medical-authority: Clinical look, doctor byline, trust badges (NEW — 118 advs)
- urgency-sale: Flash sale, countdown, scarcity (NEW — 182 advs, most common pattern)
"""

TEMPLATES = {
    "editorial": {
        "name": "Editorial",
        "description": "Blog-style article with sticky sidebar. Classic advertorial look.",
        "icon": "📰",
        "best_for": "General product reviews, testimonials, comparison articles",
    },
    "health-journal": {
        "name": "Health Journal",
        "description": "Medical/wellness style. Clean, no sidebar, cream tones, blockquotes.",
        "icon": "🏥",
        "best_for": "Health products, supplements, wellness devices",
    },
    "listicle": {
        "name": "Listicle",
        "description": "Numbered cards, modern & airy. Great for '5 reasons why' angles.",
        "icon": "📋",
        "best_for": "Comparison articles, 'X reasons to switch', benefit-focused",
    },
    "news-report": {
        "name": "News Report",
        "description": "Breaking news style with view counter, urgency bar, investigation feel. Merriweather serif + red accents.",
        "icon": "🗞️",
        "best_for": "Exposé angles, 'doctors reveal', 'investigation finds', authority-driven",
    },
    "founder-letter": {
        "name": "Founder Letter",
        "description": "Personal letter from the founder. Warm serif fonts, handwritten feel, P.S. section. Playfair Display + earth tones.",
        "icon": "✉️",
        "best_for": "Founder stories, brand origin, liquidation/closing sales, emotional narratives",
    },
    "personal-story": {
        "name": "Personal Story",
        "description": "First-person narrative with dark hero, pull quotes, full-width images. Magazine editorial feel. DM Serif + Inter.",
        "icon": "📖",
        "best_for": "Customer journeys, 'I tried X and...', transformation stories",
    },
    "medical-authority": {
        "name": "Medical Authority",
        "description": "Clinical look with doctor avatar, credentials, trust badges, study citations. IBM Plex + navy tones.",
        "icon": "⚕️",
        "best_for": "Medical devices, health supplements, doctor-endorsed products",
    },
    "urgency-sale": {
        "name": "Urgency Sale",
        "description": "Flash sale with countdown bar, stock alerts, bold discount badge. Montserrat Black + red/black.",
        "icon": "🔥",
        "best_for": "Clearance, liquidation, limited-time offers, inventory closeout",
    },
}

def get_template_list():
    return [{"id": k, **v} for k, v in TEMPLATES.items()]
