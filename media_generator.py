"""
Media Library Generator
========================
Génère une bibliothèque complète de médias par produit via Kie.ai (nano-banana-pro).
Upload sur Cloudflare R2 et indexe dans media_index.json.

Usage:
    python media_generator.py --product-id washer-seese-pro \
        --product-ref "https://cdn.shopify.com/.../product.jpg" \
        --r2-bucket my-bucket \
        --count 30

Ou programmatique:
    gen = MediaLibraryGenerator(r2_config={...})
    await gen.generate_library(product_id, product_ref_url, count=30)
"""

import asyncio
import json
import logging
import os
import time
import uuid
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

# Kie.ai API
KIE_BASE = "https://api.kie.ai/api/v1"
KIE_MODEL = "nano-banana-pro"
KIE_COST_PER_IMAGE = 18
KIE_POLL_INTERVAL = 5
KIE_POLL_TIMEOUT = 180

# Load API keys from mission-control .env or local .env
def _load_kie_keys():
    keys = []
    for env_path in ["/root/mission-control/.env", ".env"]:
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("KIE_API_KEY="):
                        keys.append(line.split("=", 1)[1].strip().strip('"').strip("'"))
                    elif line.startswith("KIE_API_KEY_SECONDARY="):
                        keys.append(line.split("=", 1)[1].strip().strip('"').strip("'"))
    return keys if keys else [os.environ.get("KIE_API_KEY", "")]


# ============================================================
# MEDIA TYPES & PROMPT TEMPLATES
# ============================================================

MEDIA_TYPES = {
    "hero": {
        "label": "Product Hero",
        "needs_product_ref": True,
        "count": 3,
        "aspect_ratios": ["16:9", "16:9", "4:3"],
    },
    "lifestyle": {
        "label": "Product In-Use / Lifestyle",
        "needs_product_ref": True,
        "count": 6,
        "aspect_ratios": ["16:9", "16:9", "16:9", "4:3", "16:9", "4:3"],
    },
    "before_after": {
        "label": "Before/After Comparison",
        "needs_product_ref": False,
        "count": 3,
        "aspect_ratios": ["16:9", "16:9", "4:3"],
    },
    "testimonial": {
        "label": "Testimonial Portrait",
        "needs_product_ref": False,
        "count": 4,
        "aspect_ratios": ["1:1", "1:1", "1:1", "4:3"],
    },
    "infographic": {
        "label": "Infographic / Specs",
        "needs_product_ref": True,
        "count": 2,
        "aspect_ratios": ["4:3", "16:9"],
    },
    "closeup": {
        "label": "Close-up / Detail Shot",
        "needs_product_ref": True,
        "count": 3,
        "aspect_ratios": ["16:9", "4:3", "16:9"],
    },
    "environment": {
        "label": "Environment / Scene",
        "needs_product_ref": False,
        "count": 4,
        "aspect_ratios": ["16:9", "16:9", "16:9", "4:3"],
    },
    "bundle": {
        "label": "Bundle / Unboxing",
        "needs_product_ref": True,
        "count": 2,
        "aspect_ratios": ["16:9", "1:1"],
    },
}

# Rotating settings for variety
SETTINGS = [
    "suburban front yard", "backyard patio", "driveway",
    "garden path", "deck surrounded by trees", "garage area",
    "sidewalk near home", "peaceful backyard", "front porch area",
    "manicured lawn",
]

FRAMING = {
    "16:9": "Wide cinematic framing, horizontal composition",
    "1:1": "Square crop, centered subject, symmetrical composition",
    "4:3": "Classic photo framing, slightly tighter composition",
    "9:16": "Vertical mobile framing, tall composition, subject centered",
    "3:2": "Standard editorial framing, balanced composition",
}

# ============================================================
# DEVICE FIDELITY BLOCK (proven to work)
# ============================================================

DEVICE_FIDELITY = """
CRITICAL — DEVICE FIDELITY (MOST IMPORTANT):

The device must remain IDENTICAL to the reference image (image_input[0]).
- Same exact shape, same proportions, same structure
- Same colors, same body design
- Same nozzle size and shape — do NOT modify
- Same battery size and placement
- Same logo placement
- Same details (buttons, vents, edges, grip texture)
- Same materials and surface finish

FRONT-HEAD GEOMETRY LOCK (CRITICAL):
The front head / nozzle area must be preserved EXACTLY as in the reference:
- No extra nozzle or front attachment
- No tube extension beyond what the reference shows
- No leaf-blower style front cone or fan guard
- Preserve the exact front opening shape from the reference
- Preserve the exact front diameter — do not widen or narrow
- Preserve the exact front proportions — same length, same taper, same angle
- The nozzle must not be elongated, widened, or reshaped in any way

Do NOT redesign the device.
Do NOT change the device shape.
Do NOT add attachments or extra parts.
Do NOT change proportions.
Do NOT transform or modify the device in any way.
The device from the reference is a REAL photographed object — preserve it exactly.

Think: "Same device, new scene."
"""

NEGATIVE_PROMPTS = """
NEGATIVE PROMPTS:
- No redesign, no transformation, no extra nozzle, no new attachments
- No front attachment, no tube extension, no leaf-blower front cone
- No product modification, no different device
- No text overlays, no watermarks, no logos overlaid
- No AI artifacts, no cartoons
- No cinematic lighting or dramatic shadows
"""

VISUAL_STYLE = """
VISUAL STYLE:
- Ultra realistic, commercial photography
- Natural outdoor daylight
- Slight depth of field on background
- Clean composition, sharp focus on subject and device
- Natural skin tones, no heavy color grading
- Premium, clean, high-tech aesthetic
"""


# ============================================================
# SCENE TEMPLATES
# ============================================================

def _build_scene_prompt(media_type: str, variant: int, setting: str, product_name: str) -> str:
    """Build the scene description for a media type."""

    scenes = {
        "hero": [
            f"A homeowner (45-60) proudly holding the {product_name} device from the reference image in their {setting}. The device is clearly visible and centered in the frame. Hero banner composition with warm natural lighting.",
            f"The {product_name} device from the reference image displayed prominently in a {setting}. Clean hero product shot with natural golden hour lighting. Device is the focal point.",
            f"Close-up hero shot of a person's hands holding the {product_name} device from the reference image, with a blurred {setting} in the background. The device fills 40% of the frame.",
        ],
        "lifestyle": [
            f"A homeowner (45-60) actively using the {product_name} device from the reference image in their {setting}. Device in action, natural action pose showing ease of use. Bright daylight, lifestyle product photography.",
            f"A woman (40-55) using the {product_name} device from the reference image with one hand in her {setting}, smiling while working. Effortless one-handed use demonstration.",
            f"A couple (50s) doing outdoor cleanup together, one person using the {product_name} device from the reference image in their {setting}. Weekend lifestyle scene, relaxed and happy.",
            f"A senior (60+) effortlessly using the {product_name} device from the reference image with ONE hand in their {setting}. Demonstrating lightweight design. Bright daylight.",
            f"Action shot of the {product_name} device from the reference image in use at a {setting}. Visible movement and action. Dynamic composition, fast-action photography.",
            f"A homeowner (45-60) casually using the {product_name} device from the reference image while chatting with a neighbor at their {setting}. Candid lifestyle moment.",
        ],
        "before_after": [
            f"Split comparison image: LEFT side shows a messy {setting} covered in leaves, debris, and dirt (muted tones). RIGHT side shows the exact same {setting} perfectly clean and pristine (bright, vibrant). Clear before/after visual divide.",
            f"Split comparison: LEFT shows a dirty driveway with mud, leaves, and grime (grey tones). RIGHT shows the same driveway sparkling clean (warm tones). Sharp vertical divide.",
            f"Split comparison: LEFT shows a dusty, cluttered garage workspace (dim, messy). RIGHT shows the same space clean and organized (bright, tidy). Clear before/after divide.",
        ],
        "testimonial": [
            f"Warm portrait of a friendly senior man (60+) in his {setting}. Genuine smile, casual clothing, soft bokeh background. Natural daylight, candid lifestyle portrait. No product visible.",
            f"Close-up portrait of a happy woman (50s) standing in her clean {setting}. Warm expression, relaxed posture. Natural light, shallow depth of field. No product visible.",
            f"A satisfied homeowner (55+) standing confidently in front of their pristine {setting}. Arms casually crossed, genuine smile. Environmental portrait style. No product visible.",
            f"A couple (50s-60s) relaxing in their clean {setting}, looking content and happy. Candid moment, natural light, warm tones. No product visible.",
        ],
        "infographic": [
            f"Extreme close-up beauty shot of the {product_name} device from the reference image on a clean white surface. Showing build quality, details, and construction. Macro product photography with shallow depth of field.",
            f"Flat lay of the {product_name} device from the reference image with all its accessories neatly arranged on a clean surface. Bird's eye view, organized product photography.",
        ],
        "closeup": [
            f"Extreme close-up of the {product_name} device from the reference image focusing on the nozzle area and front head. Showing precision engineering. Macro photography, studio-quality detail shot.",
            f"Close-up of hands gripping the {product_name} device from the reference image, showing the ergonomic design and grip texture. Natural lighting, detail shot.",
            f"Beauty shot of the {product_name} device from the reference image from a 3/4 angle on a clean surface. Showing overall design and build quality. Product photography, clean background.",
        ],
        "environment": [
            f"A beautiful {setting} in fall/autumn with orange and brown leaves scattered everywhere. No person, no product. Establishing shot, natural daylight. Suburban American neighborhood.",
            f"A messy {setting} before cleanup — leaves piled up, debris scattered. Slightly muted tones, problem visualization. No person, no product.",
            f"A pristine, perfectly clean {setting} in warm golden hour light. Everything spotless and inviting. No person, no product. After cleanup beauty shot.",
            f"A typical suburban American {setting} with houses visible in the background. Natural autumn setting with trees and leaves. No person, no product.",
        ],
        "bundle": [
            f"The {product_name} device from the reference image displayed with its complete bundle — device, battery, charger, carry case — all neatly arranged on a clean surface. Unboxing product photography, premium feel.",
            f"An open premium carry case with the {product_name} device from the reference image nestled inside, alongside accessories. Gift-worthy unboxing presentation. Clean photography.",
        ],
    }

    templates = scenes.get(media_type, scenes["lifestyle"])
    return templates[variant % len(templates)]


# ============================================================
# KIE.AI CLIENT
# ============================================================

class KieClient:
    """Async client for Kie.ai API with dual key rotation."""

    def __init__(self):
        self.keys = _load_kie_keys()
        self.call_count = 0

    def _get_key(self) -> str:
        key = self.keys[self.call_count % len(self.keys)]
        self.call_count += 1
        return key

    async def check_credits(self) -> float:
        async with aiohttp.ClientSession() as session:
            for key in self.keys:
                async with session.get(
                    f"{KIE_BASE}/chat/credit",
                    headers={"Authorization": f"Bearer {key}"},
                ) as resp:
                    data = await resp.json()
                    credits = data.get("data", 0)
                    logger.info(f"Credits for key ...{key[-6:]}: {credits}")
        return credits

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        image_ref: Optional[str] = None,
    ) -> Optional[str]:
        """Generate one image. Returns the image URL or None."""
        key = self._get_key()
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": KIE_MODEL,
            "input": {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "resolution": "1K",
                "output_format": "jpg",
            },
        }
        if image_ref:
            payload["input"]["image_input"] = [image_ref]

        async with aiohttp.ClientSession() as session:
            # Create task
            async with session.post(
                f"{KIE_BASE}/jobs/createTask",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    logger.error(f"Kie.ai create failed: HTTP {resp.status}")
                    return None
                result = await resp.json()
                task_id = result.get("data", {}).get("taskId")
                if not task_id:
                    logger.error(f"No taskId in response: {result}")
                    return None

            logger.info(f"Task created: {task_id}")

            # Poll for result
            for attempt in range(KIE_POLL_TIMEOUT // KIE_POLL_INTERVAL):
                await asyncio.sleep(KIE_POLL_INTERVAL)

                async with session.get(
                    f"{KIE_BASE}/playground/recordInfo?taskId={task_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    data = await resp.json()
                    state = data.get("data", {}).get("state", "unknown")

                    if state == "success":
                        result_json = json.loads(data["data"]["resultJson"])
                        url = result_json["resultUrls"][0]
                        logger.info(f"✅ Generated: {url[:80]}...")
                        return url

                    elif state in ("fail", "failed"):
                        fail_msg = data.get("data", {}).get("failMsg", "unknown")
                        logger.error(f"❌ Generation failed: {fail_msg}")
                        return None

                    logger.debug(f"  ... {state} ({(attempt+1)*KIE_POLL_INTERVAL}s)")

            logger.error(f"❌ Timeout after {KIE_POLL_TIMEOUT}s")
            return None


# ============================================================
# R2 UPLOADER
# ============================================================

class R2Uploader:
    """Upload images to Cloudflare R2 (S3-compatible)."""

    def __init__(self, bucket: str, account_id: str, access_key: str, secret_key: str, public_url: str = ""):
        self.bucket = bucket
        self.public_url = public_url
        # S3-compatible endpoint for R2
        self.endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
        self.access_key = access_key
        self.secret_key = secret_key

    async def upload(self, image_url: str, r2_key: str) -> str:
        """Download image from URL and upload to R2. Returns public URL."""
        import boto3

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                image_data = await resp.read()
                content_type = resp.headers.get("Content-Type", "image/png")

        # Upload via boto3 (sync, but fast)
        s3 = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="auto",
        )

        s3.put_object(
            Bucket=self.bucket,
            Key=r2_key,
            Body=image_data,
            ContentType=content_type,
        )

        if self.public_url:
            return f"{self.public_url}/{r2_key}"
        return f"{self.endpoint}/{self.bucket}/{r2_key}"


# ============================================================
# MEDIA LIBRARY GENERATOR
# ============================================================

class MediaLibraryGenerator:
    """Generates a complete media library for a product."""

    def __init__(
        self,
        output_dir: str = "data/output/media",
        r2_config: Optional[dict] = None,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.kie = KieClient()
        self.r2 = R2Uploader(**r2_config) if r2_config else None

    async def generate_library(
        self,
        product_id: str,
        product_name: str,
        product_ref_url: str = "",
        types: Optional[list] = None,
        on_progress: Optional[callable] = None,
    ) -> dict:
        """
        Generate a full media library for a product.

        Returns media_index dict with all generated images.
        """
        if types is None:
            types = list(MEDIA_TYPES.keys())

        # Check credits first
        await self.kie.check_credits()

        # Calculate total images
        total = sum(MEDIA_TYPES[t]["count"] for t in types if t in MEDIA_TYPES)
        logger.info(f"Generating {total} images for {product_name} ({total * KIE_COST_PER_IMAGE} credits)")

        media_index = {
            "product_id": product_id,
            "product_name": product_name,
            "product_ref_url": product_ref_url,
            "generated_at": datetime.utcnow().isoformat(),
            "total_images": 0,
            "media": [],
        }

        generated = 0
        setting_counter = 0

        for media_type in types:
            config = MEDIA_TYPES.get(media_type)
            if not config:
                continue

            for variant in range(config["count"]):
                setting = SETTINGS[setting_counter % len(SETTINGS)]
                setting_counter += 1
                aspect_ratio = config["aspect_ratios"][variant % len(config["aspect_ratios"])]

                # Build prompt
                scene = _build_scene_prompt(media_type, variant, setting, product_name)
                prompt = self._assemble_prompt(
                    scene=scene,
                    media_type=media_type,
                    aspect_ratio=aspect_ratio,
                    needs_ref=config["needs_product_ref"],
                )

                # Generate
                image_ref = product_ref_url if config["needs_product_ref"] and product_ref_url else None
                image_url = await self.kie.generate_image(prompt, aspect_ratio, image_ref)

                if not image_url:
                    logger.warning(f"Failed: {media_type} variant {variant}")
                    continue

                # Build filename
                filename = f"{media_type}-{variant+1:02d}-{aspect_ratio.replace(':','x')}.jpg"
                r2_key = f"media/{product_id}/{filename}"

                # Upload to R2 if configured
                public_url = image_url  # fallback to Kie CDN URL
                if self.r2:
                    try:
                        public_url = await self.r2.upload(image_url, r2_key)
                        logger.info(f"Uploaded to R2: {r2_key}")
                    except Exception as e:
                        logger.error(f"R2 upload failed: {e}")

                # Also save locally
                local_dir = self.output_dir / product_id
                local_dir.mkdir(parents=True, exist_ok=True)
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_url) as resp:
                            img_data = await resp.read()
                            (local_dir / filename).write_bytes(img_data)
                except Exception as e:
                    logger.warning(f"Local save failed: {e}")

                # Index entry
                entry = {
                    "id": str(uuid.uuid4())[:8],
                    "type": media_type,
                    "type_label": config["label"],
                    "variant": variant + 1,
                    "filename": filename,
                    "url": public_url,
                    "r2_key": r2_key,
                    "aspect_ratio": aspect_ratio,
                    "setting": setting,
                    "prompt": prompt[:200] + "...",
                    "generated_at": datetime.utcnow().isoformat(),
                }
                media_index["media"].append(entry)

                generated += 1
                media_index["total_images"] = generated

                if on_progress:
                    on_progress(generated, total, media_type, filename)

                logger.info(f"[{generated}/{total}] {media_type}/{filename}")

                # Small delay between requests
                await asyncio.sleep(1)

        # Save index
        index_path = self.output_dir / product_id / "media_index.json"
        with open(index_path, "w") as f:
            json.dump(media_index, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Library complete: {generated}/{total} images for {product_name}")
        return media_index

    def _assemble_prompt(self, scene: str, media_type: str, aspect_ratio: str, needs_ref: bool) -> str:
        """Assemble the full prompt with all blocks."""

        framing = FRAMING.get(aspect_ratio, "")

        if needs_ref:
            return f"""Generate a photorealistic advertising scene with a person holding the handheld device from the reference image.

SCENE:
{scene}

--------------------------------------------------
{DEVICE_FIDELITY}
--------------------------------------------------

COMPOSITION:
- Person aged 45-65, casual comfortable clothing
- Setting: suburban American neighborhood
- Medium shot preferred (waist up or full body), eye level
- Hands visible, natural grip on device
- Realistic commercial photography, natural daylight
{VISUAL_STYLE}
{NEGATIVE_PROMPTS}
--------------------------------------------------

VALIDATION:
Before finalizing, verify:
- Is the device identical to the reference? (shape, colors, nozzle, battery)
- Is the front head geometry exactly preserved?
- Are all proportions correct?
If NOT → regenerate.

Aspect ratio: {aspect_ratio}. {framing}."""

        else:
            return f"""{scene}

COMPOSITION:
- Person aged 45-65, casual comfortable clothing
- Setting: suburban American neighborhood
- Realistic commercial photography, natural daylight

Photorealistic, professional advertising photography, natural lighting,
clean composition, slight depth of field, high dynamic range.

No text overlays, no watermarks, no logos, no AI artifacts, no cartoons.
No product should appear in this image.

Aspect ratio: {aspect_ratio}. {framing}."""


# ============================================================
# CLI
# ============================================================

async def main():
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

    parser = argparse.ArgumentParser(description="Generate media library for a product")
    parser.add_argument("--product-id", required=True)
    parser.add_argument("--product-name", required=True)
    parser.add_argument("--product-ref", default="", help="Product reference image URL")
    parser.add_argument("--types", nargs="*", default=None, help="Media types to generate")
    parser.add_argument("--output-dir", default="data/output/media")
    # R2 config (optional)
    parser.add_argument("--r2-bucket", default="")
    parser.add_argument("--r2-account-id", default="")
    parser.add_argument("--r2-access-key", default="")
    parser.add_argument("--r2-secret-key", default="")
    parser.add_argument("--r2-public-url", default="")
    args = parser.parse_args()

    r2_config = None
    if args.r2_bucket:
        r2_config = {
            "bucket": args.r2_bucket,
            "account_id": args.r2_account_id,
            "access_key": args.r2_access_key,
            "secret_key": args.r2_secret_key,
            "public_url": args.r2_public_url,
        }

    gen = MediaLibraryGenerator(output_dir=args.output_dir, r2_config=r2_config)

    def progress(done, total, mtype, fname):
        pct = int(done / total * 100)
        print(f"  [{pct:3d}%] {done}/{total} — {mtype}/{fname}")

    result = await gen.generate_library(
        product_id=args.product_id,
        product_name=args.product_name,
        product_ref_url=args.product_ref,
        types=args.types,
        on_progress=progress,
    )

    print(f"\n✅ Generated {result['total_images']} images")
    print(f"   Index: {args.output_dir}/{args.product_id}/media_index.json")


if __name__ == "__main__":
    asyncio.run(main())
