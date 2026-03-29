"""
HTML Templates for advertorials.
Each template is a function: build_html(content, seo, image_map, product_url, product_name, product_image_url, author_name, lang, tx) -> str
"""

TEMPLATES = {
    "editorial": {
        "name": "Editorial",
        "description": "Blog-style article with sticky sidebar. Classic advertorial look.",
        "icon": "📰",
    },
    "health-journal": {
        "name": "Health Journal",
        "description": "Medical/wellness style. Clean, no sidebar, cream tones, blockquotes.",
        "icon": "🏥",
    },
    "listicle": {
        "name": "Listicle",
        "description": "Numbered cards, modern & airy. Great for '5 reasons why' angles.",
        "icon": "📋",
    },
}

def get_template_list():
    return [{"id": k, **v} for k, v in TEMPLATES.items()]
