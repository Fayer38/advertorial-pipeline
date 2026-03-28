"""
Media Library API endpoints.
Add these to the main FastAPI app in routes.py.
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form, Body
from pydantic import BaseModel

router = APIRouter(prefix="/media", tags=["media"])

MEDIA_DIR = Path("data/output/media")


# ── MODELS ──

class MediaGenerateRequest(BaseModel):
    product_id: str
    product_name: str
    product_ref_url: str = ""
    types: Optional[list] = None  # None = all 8 types


# ── ENDPOINTS ──

@router.get("/{product_id}")
async def list_product_media(product_id: str, media_type: Optional[str] = None):
    """List all media for a product, optionally filtered by type."""
    index_path = MEDIA_DIR / product_id / "media_index.json"
    if not index_path.exists():
        return {"product_id": product_id, "total": 0, "media": []}

    with open(index_path) as f:
        index = json.load(f)

    media = index.get("media", [])
    if media_type:
        media = [m for m in media if m["type"] == media_type]

    return {
        "product_id": product_id,
        "total": len(media),
        "types": list(set(m["type"] for m in index.get("media", []))),
        "media": media,
    }


@router.post("/generate")
async def generate_media_library(req: MediaGenerateRequest, bg: BackgroundTasks):
    """Trigger media library generation for a product (background task)."""
    bg.add_task(_generate_bg, req.product_id, req.product_name, req.product_ref_url, req.types)
    return {
        "status": "generating",
        "product_id": req.product_id,
        "message": f"Media generation started for {req.product_name}",
    }


@router.get("/{product_id}/status")
async def media_generation_status(product_id: str):
    """Check generation status by looking at the index."""
    index_path = MEDIA_DIR / product_id / "media_index.json"
    if not index_path.exists():
        return {"product_id": product_id, "status": "not_started", "total": 0}

    with open(index_path) as f:
        index = json.load(f)

    return {
        "product_id": product_id,
        "status": "completed" if index.get("total_images", 0) > 0 else "in_progress",
        "total": index.get("total_images", 0),
        "generated_at": index.get("generated_at", ""),
    }


@router.post("/{product_id}/upload")
async def upload_manual_media(
    product_id: str,
    media_type: str = Form(...),
    file: UploadFile = File(...),
):
    """Manually upload a media file to a product's library."""
    product_dir = MEDIA_DIR / product_id
    product_dir.mkdir(parents=True, exist_ok=True)

    # Save file
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{media_type}-manual-{datetime.utcnow().strftime('%H%M%S')}.{ext}"
    filepath = product_dir / filename

    content = await file.read()
    filepath.write_bytes(content)

    # Update index
    index_path = product_dir / "media_index.json"
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)
    else:
        index = {"product_id": product_id, "media": [], "total_images": 0}

    entry = {
        "id": datetime.utcnow().strftime("%H%M%S"),
        "type": media_type,
        "type_label": media_type.replace("_", " ").title(),
        "variant": 0,
        "filename": filename,
        "url": f"/media-files/{product_id}/{filename}",
        "aspect_ratio": "unknown",
        "setting": "manual upload",
        "generated_at": datetime.utcnow().isoformat(),
    }
    index["media"].append(entry)
    index["total_images"] = len(index["media"])

    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    return {"uploaded": filename, "media_type": media_type, "total": index["total_images"]}


@router.delete("/{product_id}/bulk")
async def bulk_delete_media(product_id: str, ids: list[str] = Body(...)):
    """Delete multiple media items at once."""
    index_path = MEDIA_DIR / product_id / "media_index.json"
    if not index_path.exists():
        raise HTTPException(404, "No media library found")

    with open(index_path) as f:
        index = json.load(f)

    media = index.get("media", [])
    to_delete = [m for m in media if m.get("id") in ids]
    for m in to_delete:
        filepath = MEDIA_DIR / product_id / m.get("filename", "")
        if filepath.exists():
            filepath.unlink()

    index["media"] = [m for m in media if m.get("id") not in ids]
    index["total_images"] = len(index["media"])

    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    return {"deleted": len(to_delete), "remaining": len(index["media"])}


@router.delete("/{product_id}/{media_id}")
async def delete_media(product_id: str, media_id: str):
    """Delete a single media from the library."""
    index_path = MEDIA_DIR / product_id / "media_index.json"
    if not index_path.exists():
        raise HTTPException(404, "No media library found")

    with open(index_path) as f:
        index = json.load(f)

    media = index.get("media", [])
    new_media = [m for m in media if m.get("id") != media_id]

    if len(new_media) == len(media):
        raise HTTPException(404, "Media not found")

    # Delete file
    deleted = [m for m in media if m.get("id") == media_id][0]
    filepath = MEDIA_DIR / product_id / deleted.get("filename", "")
    if filepath.exists():
        filepath.unlink()

    index["media"] = new_media
    index["total_images"] = len(new_media)

    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    return {"deleted": media_id, "remaining": len(new_media)}


# ── BACKGROUND ──

async def _generate_bg(product_id, product_name, product_ref_url, types):
    """Run media generation in background."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        from media_generator import MediaLibraryGenerator
        gen = MediaLibraryGenerator(output_dir=str(MEDIA_DIR))
        await gen.generate_library(
            product_id=product_id,
            product_name=product_name,
            product_ref_url=product_ref_url,
            types=types,
        )
    except Exception as e:
        logger.error(f"Media generation failed: {e}", exc_info=True)
