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
    "product_demo": {
        "label": "Product Demo",
        "source_image_types": ["lifestyle", "hero"],
        "prompts": [
            "The person activates the device and begins using it. Leaves and debris blow away powerfully from the surface. Natural wind movement, device vibrates slightly with power. Smooth camera, realistic motion.",
            "The person sweeps the device across the area in a steady horizontal motion. Debris clears in real-time, revealing clean surface underneath. Natural body movement, slight hair movement from wind.",
            "Close-up of the device in action — air stream visible blowing dust and small debris. The nozzle area glows with power. Subtle hand movements, steady grip. Photorealistic motion.",
        ],
    },
    "before_after": {
        "label": "Before/After Transition",
        "source_image_types": ["before_after", "environment"],
        "prompts": [
            "Slow transition from dirty to clean. Leaves and debris gradually disappear from left to right, revealing a pristine surface. Smooth wipe effect, natural lighting shift from cool to warm tones.",
            "Time-lapse style cleanup. The messy area rapidly becomes clean as if swept by an invisible force. Fast but smooth motion, satisfying transformation.",
        ],
    },
    "lifestyle": {
        "label": "Lifestyle Scene",
        "source_image_types": ["lifestyle", "testimonial"],
        "prompts": [
            "The person smiles and looks around their clean yard with satisfaction. Gentle breeze moves their hair and nearby tree leaves. Birds in background. Relaxed, peaceful atmosphere. Slow natural movement.",
            "The person walks through their clean patio, touches a surface approvingly, and looks content. Natural walking motion, casual body language. Warm golden hour light shifts subtly.",
            "The person casually demonstrates the lightweight device, lifting it with one hand effortlessly. Shows it to camera with a confident smile. Natural gesture, product clearly visible throughout.",
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

        # Build video tasks
        tasks = []
        for scene_type in scene_types:
            scene = VIDEO_SCENES.get(scene_type)
            if not scene:
                continue

            # Find best source image
            source_image = None
            for img_type in scene["source_image_types"]:
                candidates = images_by_type.get(img_type, [])
                if candidates:
                    # Prefer 16:9 for videos
                    wide = [c for c in candidates if c["aspect_ratio"] == "16:9"]
                    source_image = wide[0] if wide else candidates[0]
                    break

            if not source_image:
                logger.warning(f"No source image for {scene_type}, skipping")
                continue

            # One video per model, using first prompt
            prompt = scene["prompts"][0]
            for model_name in models:
                tasks.append({
                    "scene_type": scene_type,
                    "scene_label": scene["label"],
                    "model": model_name,
                    "model_label": MODELS[model_name]["label"],
                    "source_image": source_image,
                    "prompt": prompt,
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
            filename = f"video-{task['scene_type']}-{task['model']}-5s.mp4"
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
