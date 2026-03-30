"""
Video Library Generator
========================
Prend les images de la bibliothèque média et les anime via Kie.ai.
Supporte Kling 2.6, Wan 2.6, Sora 2 (image-to-video).

Usage:
    python video_generator.py --product-id seese-pro-v9 --model kling
    python video_generator.py --product-id seese-pro-v9 --model all  # teste les 3
"""

import asyncio
import json
import logging
import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

KIE_BASE = "https://api.kie.ai/api/v1"
POLL_INTERVAL = 8  # vidéos = plus long que images
POLL_TIMEOUT = 600  # 10 min max par vidéo

MEDIA_DIR = Path("data/output/media")

# ============================================================
# MODEL CONFIGS
# ============================================================

MODELS = {
    "kling": {
        "model_id": "kling-2.6/image-to-video",
        "label": "Kling 2.6",
        "duration": "5",
        "image_key": "image_urls",  # array
        "extra_params": {"sound": False},
    },
    "wan": {
        "model_id": "wan/2-6-image-to-video",
        "label": "Wan 2.6",
        "duration": "5",
        "image_key": "image_urls",  # array
        "extra_params": {"resolution": "1080p"},
    },
    "sora": {
        "model_id": "sora-2-image-to-video",
        "label": "Sora 2",
        "duration": None,  # Sora uses n_frames
        "image_key": "image_urls",  # array
        "extra_params": {
            "n_frames": "10",
            "aspect_ratio": "landscape",
            "remove_watermark": True,
            "upload_method": "s3",
        },
    },
    "hailuo": {
        "model_id": "hailuo/2-3-image-to-video-pro",
        "label": "Hailuo 2.3 Pro",
        "duration": "6",
        "image_key": "image_url",  # string, NOT array
        "extra_params": {"resolution": "768P"},
    },
    "grok": {
        "model_id": "grok-imagine/image-to-video",
        "label": "Grok Imagine",
        "duration": "6",
        "image_key": "image_urls",  # array
        "extra_params": {"resolution": "720p", "mode": "normal"},
    },
}

# ============================================================
# VIDEO SCENE PROMPTS (motion descriptions for image-to-video)
# ============================================================

VIDEO_SCENES = {
    "leaf_blowing": {
        "label": "Leaf Blowing",
        "source_image_types": ["lifestyle", "hero", "environment"],
        "prompts": [
            "The person points the blower at a pile of dry autumn leaves on the patio. They press the button and a powerful stream of air scatters the leaves in all directions. Leaves fly and tumble across the ground naturally. The person sweeps the blower in a steady left-to-right motion. Hair and loose clothing move from the airflow. Bright natural daylight.",
            "Steady medium shot. The person walks slowly along a garden path covered in fallen leaves, blowing them off to the side with the device. Leaves swirl and dance in the air before settling on the grass. Trees sway gently in the background. Smooth natural walking motion.",
            "Close shot of dry colorful autumn leaves on a wooden deck. Suddenly a powerful gust from the device enters frame from the right, blasting the leaves off the deck in a satisfying sweep. The wood surface is revealed clean underneath. Quick, powerful, satisfying motion.",
        ],
    },
    "grass_blowing": {
        "label": "Grass Clippings Cleanup",
        "source_image_types": ["lifestyle", "environment"],
        "prompts": [
            "The person stands on a driveway edge where fresh grass clippings are scattered from mowing. They aim the blower and the green clippings fly off the concrete back onto the lawn in a clean sweep. Natural body posture, casual one-handed operation. Bright midday sun.",
            "After mowing, the person uses the blower to clean up grass clippings from the sidewalk and porch steps. Green debris flies off the steps one by one as they move upward. Effortless one-handed movement. Slight wind in nearby bushes.",
            "Top-down angle: fresh grass clippings on a grey driveway. The blower's airstream enters frame and pushes the green debris in a clean line across the surface. Fast, powerful, satisfying cleanup. No person visible, just the device and the result.",
        ],
    },
    "lightweight_demo": {
        "label": "Lightweight & Easy Demo",
        "source_image_types": ["lifestyle", "hero", "closeup"],
        "prompts": [
            "A senior woman picks up the small blower from a table with one hand, effortlessly. She lifts it up and down a few times to show how light it is, smiling at the camera. Her arm shows zero strain. She then casually points it and blows a few leaves. Natural, relaxed body language. Warm afternoon light.",
            "The person holds the blower in one hand while holding a cup of coffee in the other. They casually activate the blower one-handed and clear a few leaves from the porch, then take a sip of coffee. Relaxed, everyday morning routine feel. Gentle natural movement.",
            "Close-up of a hand picking up the blower from a shelf. The hand lifts it easily, rotates it, shows it from different angles. The device looks small and lightweight in the hand. Smooth rotation, studio-quality product motion. Clean background.",
        ],
    },
    "car_drying": {
        "label": "Car Drying",
        "source_image_types": ["lifestyle", "hero"],
        "prompts": [
            "The person stands next to a freshly washed wet car in a driveway. They aim the blower at the car's roof and water droplets blast off the surface in sheets, leaving a dry streak-free finish. The person moves the blower along the car body steadily. Water spray catches the sunlight. Bright daylight.",
            "Close-up of a wet car hood with water beading on the paint. The blower's airstream enters frame and pushes water droplets across the surface in a satisfying wave, revealing the dry glossy paint underneath. Slow motion feel, water droplets glinting in sunlight.",
            "The person crouches to dry the car's wheel wells and rims with the blower. Water sprays out from the tight spaces. They move around the car with ease, one-handed operation. The car transforms from wet to dry as they work. Natural motion, outdoor setting.",
        ],
    },
}


# ============================================================
# KIE VIDEO CLIENT
# ============================================================

def _load_kie_keys():
    keys = []
    for env_path in ["/root/mission-control/.env", "/root/advertorial-pipeline/.env", ".env"]:
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("KIE_API_KEY="):
                        keys.append(line.split("=", 1)[1].strip().strip('"').strip("'"))
                    elif line.startswith("KIE_API_KEY_SECONDARY="):
                        keys.append(line.split("=", 1)[1].strip().strip('"').strip("'"))
    return keys if keys else [os.environ.get("KIE_API_KEY", "")]


class KieVideoClient:

    def __init__(self):
        self.keys = _load_kie_keys()
        self.call_count = 0

    def _get_key(self):
        key = self.keys[self.call_count % len(self.keys)]
        self.call_count += 1
        return key

    async def generate_video(
        self,
        model_name: str,
        prompt: str,
        image_url: str,
    ) -> Optional[str]:
        """Generate a video from an image. Returns video URL or None."""
        config = MODELS.get(model_name)
        if not config:
            raise ValueError(f"Unknown model: {model_name}. Available: {list(MODELS.keys())}")

        key = self._get_key()
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

        # Build input
        inp = {"prompt": prompt, **config["extra_params"]}

        # Handle image input (array vs string)
        if config["image_key"] == "image_url":
            inp["image_url"] = image_url
        else:
            inp["image_urls"] = [image_url]

        # Duration (Sora uses n_frames instead)
        if config["duration"]:
            inp["duration"] = config["duration"]

        payload = {"model": config["model_id"], "input": inp}

        async with aiohttp.ClientSession() as session:
            # Create task
            async with session.post(
                f"{KIE_BASE}/jobs/createTask",
                headers=headers, json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error(f"Create failed: HTTP {resp.status} — {body[:200]}")
                    return None
                result = await resp.json()
                task_id = result.get("data", {}).get("taskId")
                if not task_id:
                    logger.error(f"No taskId: {result}")
                    return None

            logger.info(f"[{config['label']}] Task: {task_id}")

            # Poll — videos use /jobs/recordInfo
            for attempt in range(POLL_TIMEOUT // POLL_INTERVAL):
                await asyncio.sleep(POLL_INTERVAL)

                async with session.get(
                    f"{KIE_BASE}/jobs/recordInfo?taskId={task_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    data = await resp.json()
                    state = data.get("data", {}).get("state", "unknown")

                    if state == "success":
                        result_json = json.loads(data["data"]["resultJson"])
                        url = result_json["resultUrls"][0]
                        logger.info(f"✅ [{config['label']}] Video ready: {url[:80]}...")
                        return url

                    elif state in ("fail", "failed"):
                        fail_msg = data.get("data", {}).get("failMsg", "unknown")
                        logger.error(f"❌ [{config['label']}] Failed: {fail_msg}")
                        return None

                    logger.debug(f"  [{config['label']}] {state} ({(attempt+1)*POLL_INTERVAL}s)")

            logger.error(f"❌ [{config['label']}] Timeout after {POLL_TIMEOUT}s")
            return None


# ============================================================
# VIDEO LIBRARY GENERATOR
# ============================================================

class VideoLibraryGenerator:

    def __init__(self, output_dir: str = "data/output/media"):
        self.output_dir = Path(output_dir)
        self.client = KieVideoClient()

    async def generate_videos(
        self,
        product_id: str,
        models: list = None,
        scene_types: list = None,
        on_progress: Optional[callable] = None,
    ) -> dict:
        """
        Generate video library from existing images.
        Uses images from the product's media library as input frames.
        """
        if models is None:
            models = ["kling", "wan", "sora"]
        if scene_types is None:
            scene_types = list(VIDEO_SCENES.keys())

        # Load media index to find source images
        index_path = self.output_dir / product_id / "media_index.json"
        if not index_path.exists():
            raise FileNotFoundError(f"No media library for {product_id}. Generate images first.")

        with open(index_path) as f:
            media_index = json.load(f)

        images_by_type = {}
        for m in media_index.get("media", []):
            t = m["type"]
            if t not in images_by_type:
                images_by_type[t] = []
            images_by_type[t].append(m)

        # Build video tasks — all prompts × all models
        tasks = []
        for scene_type in scene_types:
            scene = VIDEO_SCENES.get(scene_type)
            if not scene:
                continue

            # Find source images (pick different ones for variety)
            source_images = []
            for img_type in scene["source_image_types"]:
                candidates = images_by_type.get(img_type, [])
                wide = [c for c in candidates if c["aspect_ratio"] == "16:9"]
                source_images.extend(wide if wide else candidates)

            if not source_images:
                logger.warning(f"No source image for {scene_type}, skipping")
                continue

            # Each prompt variant × each model
            for prompt_idx, prompt in enumerate(scene["prompts"]):
                source_image = source_images[prompt_idx % len(source_images)]
                for model_name in models:
                    tasks.append({
                        "scene_type": scene_type,
                        "scene_label": scene["label"],
                        "model": model_name,
                        "model_label": MODELS[model_name]["label"],
                        "source_image": source_image,
                        "prompt": prompt,
                        "variant": prompt_idx + 1,
                    })

        total = len(tasks)
        logger.info(f"Generating {total} videos for {product_id} ({len(models)} models × {len(scene_types)} scenes)")

        # Video index
        video_index = {
            "product_id": product_id,
            "generated_at": datetime.utcnow().isoformat(),
            "total_videos": 0,
            "videos": [],
        }

        generated = 0

        for i, task in enumerate(tasks):
            logger.info(f"[{i+1}/{total}] {task['scene_label']} via {task['model_label']}...")

            video_url = await self.client.generate_video(
                model_name=task["model"],
                prompt=task["prompt"],
                image_url=task["source_image"]["url"],
            )

            if not video_url:
                logger.warning(f"  Failed: {task['scene_type']}/{task['model']}")
                continue

            # Download video
            filename = f"video-{task['scene_type']}-v{task.get('variant',1)}-{task['model']}-5s.mp4"
            local_dir = self.output_dir / product_id / "videos"
            local_dir.mkdir(parents=True, exist_ok=True)

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(video_url, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                        video_data = await resp.read()
                        (local_dir / filename).write_bytes(video_data)
                        logger.info(f"  Saved: {filename} ({len(video_data):,} bytes)")
            except Exception as e:
                logger.warning(f"  Download failed: {e}")

            entry = {
                "id": str(uuid.uuid4())[:8],
                "scene_type": task["scene_type"],
                "scene_label": task["scene_label"],
                "model": task["model"],
                "model_label": task["model_label"],
                "source_image_id": task["source_image"]["id"],
                "source_image_url": task["source_image"]["url"],
                "filename": filename,
                "url": video_url,
                "duration": "5s",
                "prompt": task["prompt"][:200],
                "generated_at": datetime.utcnow().isoformat(),
            }
            video_index["videos"].append(entry)
            generated += 1
            video_index["total_videos"] = generated

            if on_progress:
                on_progress(generated, total, task["scene_type"], task["model"])

            # Delay between requests
            await asyncio.sleep(2)

        # Save video index
        video_index_path = self.output_dir / product_id / "video_index.json"
        with open(video_index_path, "w") as f:
            json.dump(video_index, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Video library: {generated}/{total} videos for {product_id}")
        return video_index


# ============================================================
# CLI
# ============================================================

async def main():
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

    parser = argparse.ArgumentParser(description="Generate video library from images")
    parser.add_argument("--product-id", required=True)
    parser.add_argument("--models", nargs="*", default=["kling", "wan", "sora"],
                        help="Models to use: kling, wan, sora, hailuo, grok")
    parser.add_argument("--scenes", nargs="*", default=None,
                        help="Scene types: product_demo, before_after, lifestyle")
    parser.add_argument("--output-dir", default="data/output/media")
    args = parser.parse_args()

    gen = VideoLibraryGenerator(output_dir=args.output_dir)

    def progress(done, total, scene, model):
        print(f"  [{done}/{total}] {scene} via {model}")

    result = await gen.generate_videos(
        product_id=args.product_id,
        models=args.models,
        scene_types=args.scenes,
        on_progress=progress,
    )

    print(f"\n✅ Generated {result['total_videos']} videos")
    print(f"   Index: {args.output_dir}/{args.product_id}/video_index.json")


if __name__ == "__main__":
    asyncio.run(main())
