"""
Schémas Pydantic pour tous les contrats de données inter-agents.
Chaque agent produit et consomme des modèles définis ici.
Source de vérité : PROJECT_BIBLE.md section 3.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime
from enum import Enum


# ============================================================
# ENUMS PARTAGÉS
# ============================================================

class Intensity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class SceneType(str, Enum):
    PRODUCT = "product"
    LIFESTYLE = "lifestyle"
    BEFORE_AFTER = "before_after"
    INFOGRAPHIC = "infographic"
    TESTIMONIAL = "testimonial"

class SectionType(str, Enum):
    HOOK = "hook"
    STORY = "story"
    PROBLEM = "problem"
    SOLUTION = "solution"
    PROOF = "proof"
    OFFER = "offer"
    CTA = "cta"

class VisualFormat(str, Enum):
    IMAGE = "image"
    VIDEO = "video"

class AspectRatio(str, Enum):
    SIXTEEN_NINE = "16:9"
    ONE_ONE = "1:1"
    FOUR_FIVE = "4:5"
    NINE_SIXTEEN = "9:16"

class Priority(str, Enum):
    HERO = "hero"
    SUPPORTING = "supporting"
    OPTIONAL = "optional"

class PromptPlatform(str, Enum):
    MIDJOURNEY = "midjourney"
    LEONARDO = "leonardo"
    FLUX = "flux"
    KLING = "kling"
    RUNWAY = "runway"
    SORA = "sora"


# ============================================================
# AGENT 1 : EXTRACTEUR PRODUIT → product_data.json
# ============================================================

class ProductMeta(BaseModel):
    source_url: str
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    shopify_handle: str = ""
    store_domain: str = ""

class ProductPrice(BaseModel):
    amount: float = 0.0
    currency: str = "USD"
    compare_at_price: Optional[float] = None

class ProductVariant(BaseModel):
    title: str = ""
    price: float = 0.0
    sku: str = ""
    available: bool = True

class ProductInfo(BaseModel):
    title: str = ""
    description_html: str = ""
    description_clean: str = ""
    price: ProductPrice = Field(default_factory=ProductPrice)
    variants: list[ProductVariant] = []
    vendor: str = ""
    product_type: str = ""
    tags: list[str] = []

class Ingredient(BaseModel):
    name: str = ""
    role: str = ""
    dosage: str = ""

class Composition(BaseModel):
    ingredients: list[Ingredient] = []
    key_actives: list[str] = []
    certifications: list[str] = []
    warnings: list[str] = []

class UseCase(BaseModel):
    scenario: str = ""
    outcome: str = ""

class Benefits(BaseModel):
    main_benefits: list[str] = []
    features: list[str] = []
    use_cases: list[UseCase] = []
    problem_solved: str = ""
    target_need: str = ""

class ClinicalStudy(BaseModel):
    claim: str = ""
    source: str = ""
    result: str = ""

class SocialProof(BaseModel):
    clinical_studies: list[ClinicalStudy] = []
    certifications: list[str] = []
    press_mentions: list[str] = []

class FAQItem(BaseModel):
    question: str = ""
    answer: str = ""

class Offer(BaseModel):
    bundles: list[str] = []
    discounts: list[str] = []
    guarantees: list[str] = []
    shipping_info: str = ""
    cta_text: str = ""

class Competitive(BaseModel):
    unique_selling_points: list[str] = []
    vs_alternatives: list[str] = []
    market_positioning: str = ""

class ProductImage(BaseModel):
    url: str = ""
    alt: str = ""
    position: int = 0

class ProductData(BaseModel):
    """Sortie de l'Agent 1 : Extracteur Produit"""
    meta: ProductMeta
    product_info: ProductInfo = Field(default_factory=ProductInfo)
    composition: Composition = Field(default_factory=Composition)
    benefits: Benefits = Field(default_factory=Benefits)
    social_proof: SocialProof = Field(default_factory=SocialProof)
    faq: list[FAQItem] = []
    offer: Offer = Field(default_factory=Offer)
    competitive: Competitive = Field(default_factory=Competitive)
    images: list[ProductImage] = []


# ============================================================
# AGENT 2 : CHERCHEUR AVATAR → avatar_research.json
# ============================================================

class AvatarMeta(BaseModel):
    product_url: str = ""
    researched_at: datetime = Field(default_factory=datetime.utcnow)
    sources: list[str] = []

class AvatarProfile(BaseModel):
    demographics: str = ""
    psychographics: str = ""
    daily_life: str = ""
    frustrations: list[str] = []
    desires: list[str] = []
    objections: list[str] = []
    language_patterns: list[str] = []

class PainPoint(BaseModel):
    pain: str = ""
    intensity: Intensity = Intensity.MEDIUM
    verbatim_examples: list[str] = []

class MarketingAngle(BaseModel):
    angle_name: str = ""
    hook_idea: str = ""
    emotional_trigger: str = ""
    strength: Intensity = Intensity.MEDIUM

class RedditInsights(BaseModel):
    subreddits_explored: list[str] = []
    key_threads: list[str] = []
    sentiment_summary: str = ""

class AvatarResearch(BaseModel):
    """Sortie de l'Agent 2 : Chercheur Avatar"""
    meta: AvatarMeta
    avatar: AvatarProfile = Field(default_factory=AvatarProfile)
    pain_points: list[PainPoint] = []
    angles: list[MarketingAngle] = []
    competitors_mentioned: list[str] = []
    reddit_insights: RedditInsights = Field(default_factory=RedditInsights)


# ============================================================
# AGENT 3 : DESCRIPTEUR IMAGE → image_description.json
# ============================================================

class ImageDescriptionMeta(BaseModel):
    image_url: str = ""
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)

class ImageDescriptionContent(BaseModel):
    short: str = ""
    detailed: str = ""
    product_appearance: str = ""
    packaging: str = ""
    colors: list[str] = []
    texture_material: str = ""
    size_impression: str = ""
    lifestyle_context: str = ""

class ImageDescription(BaseModel):
    """Sortie de l'Agent 3 : Descripteur Image"""
    meta: ImageDescriptionMeta
    description: ImageDescriptionContent = Field(default_factory=ImageDescriptionContent)


# ============================================================
# AGENT 4 : ORGANISATEUR → structured_brief.json
# ============================================================

class BriefMeta(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    product_url: str = ""
    confidence_score: float = 0.0

class ProductSummary(BaseModel):
    name: str = ""
    one_liner: str = ""
    category: str = ""
    price_point: str = ""

class AvatarBrief(BaseModel):
    who: str = ""
    main_problem: str = ""
    desired_outcome: str = ""
    emotional_state_before: str = ""
    emotional_state_after: str = ""

class CopyAmmunition(BaseModel):
    primary_angle: dict = {}
    secondary_angles: list[dict] = []
    hooks: list[str] = []
    key_benefits_ranked: list[str] = []
    proof_elements: list[str] = []
    objection_handlers: list[str] = []
    urgency_elements: list[str] = []
    cta_options: list[str] = []

class VisualNotes(BaseModel):
    product_description: str = ""
    suggested_scenes: list[str] = []
    mood: str = ""

class StructuredBrief(BaseModel):
    """Sortie de l'Agent 4 : Organisateur d'Infos"""
    meta: BriefMeta
    product_summary: ProductSummary = Field(default_factory=ProductSummary)
    avatar_profile: AvatarBrief = Field(default_factory=AvatarBrief)
    copy_ammunition: CopyAmmunition = Field(default_factory=CopyAmmunition)
    visual_notes: VisualNotes = Field(default_factory=VisualNotes)


# ============================================================
# AGENT 5 : EXPERT COPYWRITING → advertorial_draft.json
# ============================================================

class DraftMeta(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    word_count: int = 0

class VisualPlaceholder(BaseModel):
    description: str = ""
    type: SceneType = SceneType.PRODUCT

class AdvertorialSection(BaseModel):
    type: SectionType
    heading: str = ""
    body_html: str = ""
    visual_placeholder: VisualPlaceholder = Field(default_factory=VisualPlaceholder)

class AdvertorialSEO(BaseModel):
    meta_title: str = ""
    meta_description: str = ""
    keywords: list[str] = []

class AdvertorialContent(BaseModel):
    headline: str = ""
    subheadline: str = ""
    sections: list[AdvertorialSection] = []

class AdvertorialDraft(BaseModel):
    """Sortie de l'Agent 5 : Expert Copywriting"""
    meta: DraftMeta
    content: AdvertorialContent = Field(default_factory=AdvertorialContent)
    seo: AdvertorialSEO = Field(default_factory=AdvertorialSEO)


# ============================================================
# AGENT 6 : STRATÈGE VISUEL → visual_plan.json
# ============================================================

class VisualScene(BaseModel):
    section_index: int = 0
    scene_type: SceneType = SceneType.PRODUCT
    description: str = ""
    mood: str = ""
    format: VisualFormat = VisualFormat.IMAGE
    aspect_ratio: AspectRatio = AspectRatio.SIXTEEN_NINE
    priority: Priority = Priority.SUPPORTING

class VisualPlan(BaseModel):
    """Sortie de l'Agent 6 : Stratège Visuel"""
    scenes: list[VisualScene] = []


# ============================================================
# AGENT 7/8 : GÉNÉRATEURS DE PROMPTS → image/video_prompts.json
# ============================================================

class GeneratedPrompt(BaseModel):
    scene_index: int = 0
    platform: PromptPlatform = PromptPlatform.MIDJOURNEY
    prompt: str = ""
    negative_prompt: str = ""
    parameters: dict = {}
    generated_image_url: Optional[str] = None

class PromptCollection(BaseModel):
    """Sortie des Agents 7/8 : Générateurs de Prompts"""
    prompts: list[GeneratedPrompt] = []


# ============================================================
# AGENT 9 : QA → qa_report.json
# ============================================================

class QACriterion(BaseModel):
    score: int = 0  # 0-10
    feedback: str = ""

class QAReport(BaseModel):
    """Sortie de l'Agent 9 : Contrôle Qualité"""
    overall_score: int = 0
    passed: bool = True
    criteria: dict[str, QACriterion] = {
        "hook_strength": QACriterion(),
        "story_flow": QACriterion(),
        "proof_density": QACriterion(),
        "cta_clarity": QACriterion(),
        "emotional_arc": QACriterion(),
        "readability": QACriterion(),
        "similarity_to_best": QACriterion(),
    }
    improvements: list[str] = []
    version: int = 1
