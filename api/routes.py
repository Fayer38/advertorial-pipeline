"""
API REST FastAPI v2 — Products + Advertorials flow.
"""
import asyncio, json, logging, re, uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import re as _re

logger = logging.getLogger(__name__)

def _extract_thumbnail(html_path: Path, product_id: str = "") -> str:
    """Extract thumbnail: first <img src> from HTML, or first media library image for the product."""
    # 1. Try extracting from HTML
    try:
        html = html_path.read_text(encoding="utf-8", errors="ignore")[:50000]
        for m in _re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', html, _re.IGNORECASE):
            src = m.group(1)
            if not src or src.startswith("data:"):
                continue
            lower = src.lower()
            if any(skip in lower for skip in ["logo", "icon", "pixel", "tracking", "favicon", "badge", "star", "rating"]):
                continue
            return src
    except Exception:
        pass
    # 2. Fallback: first image from product media library
    search_ids = [product_id] if product_id else []
    # Also search all media libraries as fallback
    media_root = Path("data/output/media")
    if media_root.exists():
        for d in media_root.iterdir():
            if d.is_dir() and d.name not in search_ids:
                search_ids.append(d.name)
    for pid in search_ids:
        try:
            media_index = media_root / pid / "media_index.json"
            if media_index.exists():
                mi = json.loads(media_index.read_text())
                for item in mi.get("media", []):
                    url = item.get("url", "")
                    if url and not url.startswith("data:"):
                        return url
        except Exception:
            pass
    return ""
app = FastAPI(title="Advertorial Pipeline API", version="2.0.0")

from api.media_routes import router as media_router
app.include_router(media_router)

from starlette.staticfiles import StaticFiles
import os
_media_dir = os.path.join(os.path.dirname(__file__), "..", "data", "output", "media")
os.makedirs(_media_dir, exist_ok=True)
app.mount("/media-files", StaticFiles(directory=_media_dir), name="media-files")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── MODELS ──
class ProductAnalyzeReq(BaseModel):
    product_url: str

class PipelineStartReq(BaseModel):
    product_id: str
    angle: str = "testimonial"
    structure: str = "pas"
    persona: str = ""
    tone: str = "conversational"
    language: str = "en"
    brief: str = ""

class AdvUpdateReq(BaseModel):
    headline: Optional[str] = None
    sections: Optional[list] = None
    product_url: Optional[str] = None
    product_image_url: Optional[str] = None

class AgentRunReq(BaseModel):
    agent_name: str
    input_data: dict = {}

# ── STORAGE ──
products = {}   # id -> dict
pipelines = {}  # id -> dict
pipeline_events = {}  # id -> asyncio.Queue

# ── LOAD EXISTING PRODUCTS ON STARTUP ──
@app.on_event("startup")
async def _load_existing_products():
    prod_dir = Path("data/output/products")
    if not prod_dir.exists():
        return
    for f in prod_dir.glob("product_data_*.json"):
        try:
            data = json.loads(f.read_text())
            pid = f.stem.replace("product_data_", "")
            pi = data.get("product_info", {})
            pr = pi.get("price", {})
            bn = data.get("benefits", {})
            products[pid] = {
                "id": pid,
                "url": pi.get("url", ""),
                "name": pi.get("title", pid),
                "category": pi.get("product_type", ""),
                "price": f"${pr.get('amount', 0)}" if isinstance(pr, dict) else str(pr),
                "compare_price": f"${pr.get('compare_at_price', 0)}" if isinstance(pr, dict) and pr.get("compare_at_price") else "",
                "benefits": bn.get("main_benefits", [])[:4] if isinstance(bn, dict) else [],
                "problem": bn.get("problem_solved", "") if isinstance(bn, dict) else "",
                "audience": "",
                "status": "ready",
                "analyzed_at": datetime.utcnow().isoformat(),
                "data": data,
                "suggested_angle": "testimonial",
                "suggested_structure": "pas",
                "suggested_tone": "conversational",
                "suggested_persona": "",
            }
            logger.info(f"Loaded product: {pid} ({products[pid]['name']})")
        except Exception as e:
            logger.error(f"Failed to load {f}: {e}")

# ── LOAD EXISTING PIPELINES ON STARTUP ──
@app.on_event("startup")
async def _load_existing_pipelines():
    out_dir = Path("data/output")
    if not out_dir.exists():
        return
    for d in out_dir.iterdir():
        if not d.is_dir() or d.name == "products":
            continue
        plid = d.name
        # Check if there's a draft or HTML
        drafts = list(d.glob("advertorial_draft*.json"))
        htmls = list(d.glob("*.html"))
        briefs = list(d.glob("structured_brief*.json"))
        if not drafts and not htmls:
            continue  # empty/incomplete pipeline
        try:
            # Determine status
            status = "completed" if htmls else "failed"
            headline = ""
            qa_score = 0
            html_file = ""
            thumbnail = ""
            config = {}
            product_id = ""
            product_name = ""
            started_at = ""

            thumbnail = ""
            if htmls:
                html_file = htmls[0].name
                headline = htmls[0].stem.replace("-", " ").title()[:80]
                try:
                    html_content = htmls[0].read_text()
                    m = re.search(r'<img[^>]+src=["\']([^"\']+)', html_content)
                    if m:
                        thumbnail = m.group(1)
                except Exception:
                    pass
                thumbnail = _extract_thumbnail(htmls[0])

            if drafts:
                draft = json.loads(drafts[0].read_text())
                content = draft.get("content", {})
                headline = content.get("headline", headline)

            # Try to get QA score
            qa_files = list(d.glob("qa_report*.json"))
            if qa_files:
                qa = json.loads(qa_files[0].read_text())
                qa_score = qa.get("overall_score", 0)

            # Try to get config from brief
            if briefs:
                brief = json.loads(briefs[0].read_text())
                cfg = brief.get("_config", {})
                config = cfg if cfg else {"angle": "testimonial", "structure": "pas", "tone": "conversational", "language": "en"}
                ps = brief.get("product_summary", {})
                product_name = ps.get("name", "")

            # Extract thumbnail
            if htmls:
                thumbnail = _extract_thumbnail(htmls[0], product_id)

            # Use dir mtime as timestamp
            import os as _os
            mtime = datetime.fromtimestamp(_os.path.getmtime(str(d)))
            started_at = mtime.isoformat()

            pipelines[plid] = {
                "id": plid, "status": status, "started_at": started_at,
                "completed_at": started_at if status == "completed" else "",
                "product_id": product_id, "product_url": "",
                "product_name": product_name,
                "config": config,
                "current_phase": "", "current_agent": "", "progress": 1.0 if status == "completed" else 0,
                "error": "", "results": {"headline": headline, "qa_score": qa_score, "html_file": html_file, "thumbnail": thumbnail},
            }
            logger.info(f"Loaded pipeline: {plid} ({status}) — {headline[:50]}")
        except Exception as e:
            logger.error(f"Failed to load pipeline {plid}: {e}")

# ── RESOLVE product_id for disk-loaded pipelines ──
@app.on_event("startup")
async def _resolve_pipeline_products():
    """Match pipelines to products by name when product_id is missing."""
    for plid, pl in pipelines.items():
        if pl["product_id"]:
            continue
        pname = pl.get("product_name", "").lower()
        if not pname:
            continue
        for pid, prod in products.items():
            prod_name = prod.get("name", "").lower()
            if prod_name == pname or prod_name in pname or pname in prod_name:
                pl["product_id"] = pid
                logger.info(f"Resolved pipeline {plid} → product {pid} (by name match)")
                break
        # Keyword fallback
        if not pl["product_id"]:
            for pid, prod in products.items():
                pn = prod.get("name","").lower()
                for kw in ["washer","blower","pressure"]:
                    if kw in pname and kw in pn:
                        pl["product_id"] = pid
                        logger.info(f"Resolved pipeline {plid} → product {pid} (by keyword '{kw}')")
                        break
                if pl["product_id"]:
                    break

# ── PRODUCTS ──
@app.post("/products/analyze")
async def analyze_product(req: ProductAnalyzeReq, bg: BackgroundTasks):
    pid = str(uuid.uuid4())[:8]
    products[pid] = {"id": pid, "url": req.product_url, "name": "Analyzing...", "status": "analyzing", "analyzed_at": datetime.utcnow().isoformat(), "data": {}, "suggested_angle": "", "suggested_structure": "", "suggested_tone": "", "suggested_persona": ""}
    bg.add_task(_analyze_product_bg, pid, req.product_url)
    return {"product_id": pid, "status": "analyzing"}

@app.get("/products")
async def list_products():
    return {"products": sorted(products.values(), key=lambda x: x.get("analyzed_at",""), reverse=True)}

@app.get("/products/{pid}")
async def get_product(pid: str):
    if pid not in products: raise HTTPException(404, "Product not found")
    return products[pid]

@app.delete("/products/{pid}")
async def delete_product(pid: str):
    if pid not in products: raise HTTPException(404, "Product not found")
    del products[pid]
    return {"deleted": pid}

# ── PIPELINE ──
@app.post("/pipeline/start")
async def start_pipeline(req: PipelineStartReq, bg: BackgroundTasks):
    if req.product_id not in products: raise HTTPException(404, "Product not found")
    product = products[req.product_id]
    plid = str(uuid.uuid4())[:8]
    pipelines[plid] = {"id": plid, "status": "pending", "started_at": datetime.utcnow().isoformat(), "completed_at": "", "product_id": req.product_id, "product_url": product["url"], "product_name": product.get("name",""), "config": {"angle": req.angle, "structure": req.structure, "persona": req.persona, "tone": req.tone, "language": req.language, "brief": req.brief}, "current_phase": "", "current_agent": "", "progress": 0.0, "error": "", "results": {}}
    pipeline_events[plid] = asyncio.Queue()
    bg.add_task(_run_pipeline_bg, plid, req)
    return {"pipeline_id": plid, "status": "pending", "product": product.get("name","")}

@app.get("/pipeline/{plid}/status")
async def get_status(plid: str):
    if plid not in pipelines: raise HTTPException(404)
    return pipelines[plid]

@app.get("/pipeline/{plid}/stream")
async def stream_events(plid: str):
    if plid not in pipelines: raise HTTPException(404)
    async def gen():
        q = pipeline_events.get(plid)
        if not q: return
        yield f"data: {json.dumps(pipelines[plid], default=str)}\n\n"
        while True:
            try:
                ev = await asyncio.wait_for(q.get(), timeout=60)
                yield f"data: {json.dumps(ev, default=str)}\n\n"
                if ev.get("status") in ("completed","failed"): break
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type':'heartbeat'})}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control":"no-cache","Connection":"keep-alive"})

@app.get("/pipeline/{plid}/results")
async def get_results(plid: str):
    if plid not in pipelines: raise HTTPException(404)
    out = Path(f"data/output/{plid}")
    results = {}
    if out.exists():
        for f in out.glob("*.json"):
            try: results[f.stem] = json.loads(f.read_text())
            except: results[f.stem] = {"error": "parse failed"}
        for f in out.glob("*.html"):
            results["html_file"] = str(f)
    return {"pipeline_id": plid, "status": pipelines[plid]["status"], "config": pipelines[plid]["config"], "results": results}

@app.put("/pipeline/{plid}/update")
async def update_adv(plid: str, req: AdvUpdateReq):
    if plid not in pipelines: raise HTTPException(404)
    out = Path(f"data/output/{plid}")
    drafts = list(out.glob("advertorial_draft*.json"))
    if not drafts: raise HTTPException(404, "No draft found")
    draft = json.loads(drafts[0].read_text())
    if req.headline: draft["content"]["headline"] = req.headline
    if req.product_url: draft.setdefault("meta",{})["product_url"] = req.product_url
    if req.sections:
        for su in req.sections:
            idx = su.get("index", -1)
            secs = draft["content"].get("sections", [])
            if 0 <= idx < len(secs):
                if "heading" in su: secs[idx]["heading"] = su["heading"]
                if "body_html" in su: secs[idx]["body_html"] = su["body_html"]
    drafts[0].write_text(json.dumps(draft, ensure_ascii=False, indent=2))
    try:
        from agents.html_publisher import HTMLPublisherAgent
        pub = HTMLPublisherAgent(output_dir=str(out))
        r = await pub.run(advertorial_draft=draft, product_url=req.product_url or "", product_image_url=req.product_image_url or "")
        return {"updated": True, "html_file": r.get("html_file"), "slug": r.get("slug")}
    except Exception as e:
        return {"updated": True, "draft_saved": True, "html_error": str(e)}

@app.post("/pipeline/{plid}/agent")
async def run_agent(plid: str, req: AgentRunReq, bg: BackgroundTasks):
    if plid not in pipelines: raise HTTPException(404)
    bg.add_task(_run_agent_bg, plid, req.agent_name, req.input_data)
    return {"launched": req.agent_name}

@app.get("/pipeline/history")
async def history():
    h = []
    for plid, s in pipelines.items():
        hf = s["results"].get("html_file","")
        pub_url = f"https://dailybloginfo.com/a/{hf}" if hf else ""
        h.append({"id": plid, "product_id": s["product_id"], "product_name": s.get("product_name",""), "product_url": s["product_url"], "status": s["status"], "started_at": s["started_at"], "completed_at": s.get("completed_at",""), "headline": s["results"].get("headline",""), "qa_score": s["results"].get("qa_score",0), "thumbnail": s["results"].get("thumbnail",""), "config": s["config"], "progress": s.get("progress",0), "current_phase": s.get("current_phase",""), "current_agent": s.get("current_agent",""), "published_url": pub_url, "results": {"headline": s["results"].get("headline",""), "qa_score": s["results"].get("qa_score",0), "thumbnail": s["results"].get("thumbnail",""), "html_file": hf}})
    h.sort(key=lambda x: x["started_at"], reverse=True)
    return {"pipelines": h}

# ── UPDATE SLUG + TITLE ──
class UpdateMetaReq(BaseModel):
    slug: Optional[str] = None
    title: Optional[str] = None

@app.put("/pipeline/{plid}/meta")
async def update_meta(plid: str, req: UpdateMetaReq):
    if plid not in pipelines: raise HTTPException(404)
    out = Path(f"data/output/{plid}")
    htmls = list(out.glob("*.html"))
    if not htmls: raise HTTPException(404, "No HTML file")
    html_path = htmls[0]
    html = html_path.read_text(encoding="utf-8")
    pub_dir = Path("/var/www/advertorials")

    # Update title in HTML
    if req.title:
        html = _re.sub(r'<title>[^<]*</title>', f'<title>{req.title}</title>', html)
        # Also update og:title if present
        html = _re.sub(r'(<meta\s+property="og:title"\s+content=")[^"]*(")', f'\\g<1>{req.title}\\2', html)
        pipelines[plid]["results"]["headline"] = req.title

    # Rename slug (rename file)
    old_name = html_path.name
    if req.slug:
        # Sanitize slug
        import unicodedata
        slug = req.slug.strip().lower()
        slug = _re.sub(r'[^a-z0-9\-]', '-', slug)
        slug = _re.sub(r'-+', '-', slug).strip('-')
        if not slug: raise HTTPException(400, "Invalid slug")
        new_name = f"{slug}.html"
        # Write updated HTML to new filename
        new_path = out / new_name
        new_path.write_text(html, encoding="utf-8")
        # Remove old file if different name
        if old_name != new_name and html_path.exists():
            html_path.unlink()
        # Update published copy
        old_pub = pub_dir / old_name
        if old_pub.exists(): old_pub.unlink()
        (pub_dir / new_name).write_text(html, encoding="utf-8")
        pipelines[plid]["results"]["html_file"] = new_name
        return {"updated": True, "old_slug": old_name.replace(".html",""), "new_slug": slug, "url": f"https://dailybloginfo.com/a/{new_name}"}
    else:
        # Just title update, save in place
        html_path.write_text(html, encoding="utf-8")
        (pub_dir / old_name).write_text(html, encoding="utf-8")
        return {"updated": True, "slug": old_name.replace(".html",""), "url": f"https://dailybloginfo.com/a/{old_name}"}

# ── SAVE EDITED HTML ──
class SaveHtmlReq(BaseModel):
    html: str

@app.put("/pipeline/{plid}/save-html")
async def save_html(plid: str, req: SaveHtmlReq):
    out = Path(f"data/output/{plid}")
    if not out.exists():
        raise HTTPException(404, "Pipeline not found")
    htmls = list(out.glob("*.html"))
    if not htmls:
        raise HTTPException(404, "No HTML file")
    # Strip the edit script before saving
    import re
    clean = re.sub(r'<script>\s*\(function\(\)\s*\{.*?</script>', '', req.html, flags=re.DOTALL)
    # Also remove data-editable and data-img-idx and data-media-idx attributes
    clean = re.sub(r'\s+data-editable="[^"]*"', '', clean)
    clean = re.sub(r'\s+data-img-idx="[^"]*"', '', clean)
    clean = re.sub(r'\s+data-media-idx="[^"]*"', '', clean)
    clean = re.sub(r'\s+contenteditable="[^"]*"', '', clean)
    # Strip editor artifacts
    clean = re.sub(r'<div id="edit-toolbar".*?</div>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<div id="img-panel".*?</div>\s*</div>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<div class="block-controls">.*?</div>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<div class="drop-indicator">.*?</div>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'\s+class="img-selected"', '', clean)
    clean = re.sub(r'\s+class="dragging"', '', clean)
    # Ensure header logo is present
    clean = _inject_header_logo(clean)
    htmls[0].write_text(clean, encoding="utf-8")
    # Also copy to published dir
    pub = Path("/var/www/advertorials") / htmls[0].name
    pub.write_text(clean, encoding="utf-8")
    return {"saved": True, "file": htmls[0].name}

# ── EDITABLE PREVIEW ──
EDIT_SCRIPT = """
<script>
(function() {
  // ── STYLES ──
  var style = document.createElement('style');
  style.textContent = `
    [data-editable] { transition: outline .15s; cursor: pointer; position: relative; }
    [data-editable]:hover { outline: 1px dashed rgba(242,103,34,0.4) !important; outline-offset: 2px; }
    [data-editable][contenteditable="true"] { outline: 2px solid #f26722 !important; outline-offset: 3px; cursor: text; }

    /* Block controls (drag + duplicate) */
    [data-editable], .img-set, .placeholder[data-media-idx], img[data-img-idx] { position: relative; }
    [data-editable]::before, .img-set::before, .placeholder[data-media-idx]::before, img[data-img-idx]::before {
      content: ''; position: absolute; left: -42px; top: 0; width: 42px; height: 100%;
      pointer-events: auto;
    }
    .block-controls {
      position: absolute; left: -36px; top: 50%; transform: translateY(-50%);
      display: flex; flex-direction: column; gap: 3px;
      opacity: 0; transition: opacity .15s; z-index: 9990;
    }
    [data-editable]:hover > .block-controls,
    .img-set:hover > .block-controls,
    .placeholder:hover > .block-controls,
    img[data-img-idx]:hover > .block-controls { opacity: 1; }
    .block-controls button {
      width: 26px; height: 26px; border-radius: 6px; border: 1px solid #ddd;
      background: #fff; color: #666; font-size: 12px; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 1px 4px rgba(0,0,0,.12); transition: all .15s;
      padding: 0; line-height: 1;
    }
    .block-controls button:hover { background: #f26722; color: #fff; border-color: #f26722; }
    .block-ctrl-drag { cursor: grab !important; }
    .block-ctrl-drag:active { cursor: grabbing !important; }
    .block-ctrl-del:hover { background: #ef4444 !important; border-color: #ef4444 !important; }

    /* Drag state */
    .dragging { opacity: 0.4 !important; }
    .drop-indicator {
      height: 3px; background: #f26722; border-radius: 2px; margin: 2px 0;
      box-shadow: 0 0 8px rgba(242,103,34,0.5);
      pointer-events: none;
    }
    img[data-img-idx] { position: relative; }
    .placeholder[data-media-idx] { position: relative; }
    .placeholder[data-media-idx]:hover::after { content: '📷 Click to replace'; position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); background: #f26722; color: #fff; padding: 6px 14px; border-radius: 6px; font-size: 13px; font-style: normal; font-weight: 700; z-index: 9999; }

    /* Image click highlight */
    img[data-img-idx] { cursor: pointer; transition: outline .15s; }
    img[data-img-idx]:hover { outline: 2px dashed rgba(242,103,34,0.4); outline-offset: 3px; }
    img[data-img-idx].img-selected { outline: 2px solid #f26722 !important; outline-offset: 3px; }

    /* Side panel for image device settings */
    #img-panel {
      position: fixed; top: 0; right: -320px; width: 310px; height: 100vh;
      background: #111114; border-left: 1px solid #2a2a30; z-index: 99990;
      transition: right .25s ease; overflow-y: auto;
      font-family: system-ui, -apple-system, sans-serif;
      box-shadow: -8px 0 30px rgba(0,0,0,.5);
    }
    #img-panel.open { right: 0; }
    #img-panel .panel-header {
      padding: 16px 18px; border-bottom: 1px solid #1f1f23;
      display: flex; align-items: center; justify-content: space-between;
    }
    #img-panel .panel-title { font-size: 14px; font-weight: 700; color: #f0f0f0; }
    #img-panel .panel-close {
      background: none; border: none; color: #8b8b92; font-size: 18px;
      cursor: pointer; padding: 4px 8px; border-radius: 6px; line-height: 1;
    }
    #img-panel .panel-close:hover { background: #1f1f23; color: #f0f0f0; }
    #img-panel .device-slot {
      padding: 14px 18px; border-bottom: 1px solid #1f1f23;
      cursor: pointer; transition: background .15s;
    }
    #img-panel .device-slot:hover { background: rgba(242,103,34,0.05); }
    #img-panel .device-label {
      font-size: 12px; font-weight: 700; color: #f0f0f0;
      display: flex; align-items: center; gap: 6px; margin-bottom: 8px;
    }
    #img-panel .device-label .badge {
      font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 600;
    }
    #img-panel .badge-default { background: rgba(139,139,146,0.15); color: #8b8b92; }
    #img-panel .badge-custom { background: rgba(34,197,94,0.15); color: #22c55e; }
    #img-panel .device-thumb {
      width: 100%; height: 80px; border-radius: 8px; overflow: hidden;
      border: 1px solid #1f1f23; display: flex; align-items: center; justify-content: center;
      position: relative;
    }
    #img-panel .device-thumb img {
      width: 100%; height: 100%; object-fit: cover; display: block;
    }
    #img-panel .device-thumb .placeholder-msg {
      color: #55555e; font-size: 11px; font-style: italic;
    }
    #img-panel .device-thumb .remove-btn {
      position: absolute; top: 4px; right: 4px;
      background: rgba(0,0,0,.7); color: #ef4444; border: 1px solid rgba(239,68,68,.3);
      border-radius: 50%; width: 22px; height: 22px; font-size: 11px;
      cursor: pointer; display: none; align-items: center; justify-content: center; line-height: 1;
    }
    #img-panel .device-slot:hover .remove-btn.visible { display: flex; }

    /* Responsive image sets */
    .img-set { position: relative; width: 100%; }
    .img-set .for-desktop, .img-set .for-tablet, .img-set .for-mobile { width: 100%; border-radius: 8px; }
    .img-set .for-tablet, .img-set .for-mobile { display: none; }
    @media (min-width: 769px) and (max-width: 1024px) {
      .img-set.has-tablet .for-desktop { display: none !important; }
      .img-set.has-tablet .for-tablet { display: block !important; }
    }
    @media (max-width: 768px) {
      .img-set.has-mobile .for-desktop { display: none !important; }
      .img-set.has-mobile .for-mobile { display: block !important; }
    }

    /* ── TOOLBAR ── */
    #edit-toolbar {
      position: fixed; display: none;
      background: #1a1a1a; border: 1px solid #333; border-radius: 10px;
      padding: 4px 6px; gap: 2px; align-items: center;
      z-index: 99999; box-shadow: 0 8px 30px rgba(0,0,0,.6);
      flex-wrap: wrap; max-width: min(95vw, 460px); touch-action: none;
      user-select: none; -webkit-user-select: none;
    }
    #edit-toolbar.visible { display: flex; }
    #edit-toolbar .tb-drag {
      cursor: grab; padding: 2px 6px; color: #888; font-size: 16px; letter-spacing: 1px;
      display: flex; align-items: center; flex-shrink: 0;
    }
    #edit-toolbar .tb-drag:active { cursor: grabbing; }
    #edit-toolbar .tb-sep { width: 1px; height: 22px; background: #333; margin: 0 3px; flex-shrink: 0; }
    #edit-toolbar button {
      background: none; border: 1px solid transparent; color: #eee; cursor: pointer;
      min-width: 28px; height: 28px; border-radius: 6px; font-size: 13px;
      display: flex; align-items: center; justify-content: center; transition: all .1s;
      padding: 0 4px; font-family: inherit; flex-shrink: 0;
    }
    #edit-toolbar button:hover { background: #2a2a2a; color: #fff; border-color: #444; }
    #edit-toolbar button.active { background: #f26722; color: #000; border-color: #f26722; }
    #edit-toolbar select {
      background: #111; color: #eee; border: 1px solid #333; border-radius: 6px;
      padding: 3px 4px; font-size: 11px; cursor: pointer; height: 28px; outline: none;
      max-width: 70px; flex-shrink: 0;
    }
    #edit-toolbar select:hover { border-color: #555; }
    #edit-toolbar input[type="color"] {
      width: 24px; height: 24px; border: 1px solid #333; border-radius: 6px;
      background: #111; cursor: pointer; padding: 1px; flex-shrink: 0;
    }
    @media (max-width: 480px) {
      #edit-toolbar { max-width: 98vw; padding: 3px 4px; gap: 1px; border-radius: 8px; }
      #edit-toolbar button { min-width: 26px; height: 26px; font-size: 12px; }
      #edit-toolbar select { font-size: 10px; max-width: 58px; height: 26px; padding: 2px 3px; }
      #edit-toolbar input[type="color"] { width: 22px; height: 22px; }
      #edit-toolbar .tb-sep { height: 18px; margin: 0 2px; }
    }
  `;
  document.head.appendChild(style);

  // ── CREATE TOOLBAR ──
  var tb = document.createElement('div');
  tb.id = 'edit-toolbar';
  tb.innerHTML = `
    <span class="tb-drag" data-drag="true" title="Drag to move">⠿</span>
    <button data-cmd="bold" title="Bold"><b>B</b></button>
    <button data-cmd="italic" title="Italic"><i>I</i></button>
    <button data-cmd="underline" title="Underline"><u>U</u></button>
    <button data-cmd="strikeThrough" title="Strikethrough"><s>S</s></button>
    <div class="tb-sep"></div>
    <select data-action="fontSize" title="Font Size">
      <option value="" disabled selected>Size</option>
      <option value="12">12</option><option value="14">14</option>
      <option value="16">16</option><option value="18">18</option>
      <option value="20">20</option><option value="22">22</option>
      <option value="24">24</option><option value="28">28</option>
      <option value="32">32</option><option value="36">36</option>
      <option value="48">48</option>
    </select>
    <select data-action="fontName" title="Font">
      <option value="" disabled selected>Font</option>
      <option value="Roboto">Roboto</option>
      <option value="Montserrat">Montserrat</option>
      <option value="Georgia">Georgia</option>
      <option value="Arial">Arial</option>
      <option value="Helvetica">Helvetica</option>
      <option value="Times New Roman">Times</option>
      <option value="Verdana">Verdana</option>
      <option value="Courier New">Courier</option>
    </select>
    <div class="tb-sep"></div>
    <input type="color" data-action="foreColor" value="#111111" title="Text Color">
    <input type="color" data-action="hiliteColor" value="#ffffff" title="Highlight">
    <div class="tb-sep"></div>
    <button data-cmd="justifyLeft" title="Align Left"><svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><rect x="1" y="2" width="14" height="2"/><rect x="1" y="6" width="10" height="2"/><rect x="1" y="10" width="14" height="2"/><rect x="1" y="14" width="8" height="2"/></svg></button>
    <button data-cmd="justifyCenter" title="Center"><svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><rect x="1" y="2" width="14" height="2"/><rect x="3" y="6" width="10" height="2"/><rect x="1" y="10" width="14" height="2"/><rect x="4" y="14" width="8" height="2"/></svg></button>
    <button data-cmd="justifyRight" title="Align Right"><svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><rect x="1" y="2" width="14" height="2"/><rect x="5" y="6" width="10" height="2"/><rect x="1" y="10" width="14" height="2"/><rect x="7" y="14" width="8" height="2"/></svg></button>
    <div class="tb-sep"></div>
    <button data-cmd="removeFormat" title="Clear Formatting" style="font-size:11px;text-decoration:line-through;opacity:.7">T</button>
    <button data-action="link" title="Link">🔗</button>
    <div class="tb-sep"></div>
    <button data-action="titleCase" title="Title Case" style="font-size:10px;font-weight:700">Aa</button>
    <button data-action="uppercase" title="UPPERCASE" style="font-size:10px;font-weight:700">AA</button>
    <button data-action="lowercase" title="lowercase" style="font-size:10px;font-weight:700">aa</button>
  `;
  document.body.appendChild(tb);

  // ── DRAG LOGIC ──
  var isDragging = false, dragOffX = 0, dragOffY = 0, tbManualPos = false;

  function onDragStart(clientX, clientY) {
    var r = tb.getBoundingClientRect();
    dragOffX = clientX - r.left;
    dragOffY = clientY - r.top;
    isDragging = true;
    tb.querySelector('.tb-drag').style.cursor = 'grabbing';
  }
  function onDragMove(clientX, clientY) {
    if (!isDragging) return;
    var x = clientX - dragOffX;
    var y = clientY - dragOffY;
    // Clamp to viewport
    x = Math.max(0, Math.min(x, window.innerWidth - tb.offsetWidth));
    y = Math.max(0, Math.min(y, window.innerHeight - tb.offsetHeight));
    tb.style.left = x + 'px';
    tb.style.top = y + 'px';
    tbManualPos = true;
  }
  function onDragEnd() {
    isDragging = false;
    var drag = tb.querySelector('.tb-drag');
    if (drag) drag.style.cursor = 'grab';
  }

  // Mouse drag
  tb.addEventListener('mousedown', function(e) {
    if (e.target.closest('[data-drag]')) {
      e.preventDefault();
      onDragStart(e.clientX, e.clientY);
    }
  });
  document.addEventListener('mousemove', function(e) { onDragMove(e.clientX, e.clientY); });
  document.addEventListener('mouseup', onDragEnd);

  // Touch drag
  tb.addEventListener('touchstart', function(e) {
    if (e.target.closest('[data-drag]')) {
      var t = e.touches[0];
      onDragStart(t.clientX, t.clientY);
    }
  }, { passive: true });
  document.addEventListener('touchmove', function(e) {
    if (isDragging) {
      var t = e.touches[0];
      onDragMove(t.clientX, t.clientY);
      e.preventDefault();
    }
  }, { passive: false });
  document.addEventListener('touchend', onDragEnd);

  // ── SELECTION SAVE/RESTORE ──
  var savedSel = null;
  function saveSel() {
    var s = window.getSelection();
    if (s && s.rangeCount > 0) savedSel = s.getRangeAt(0).cloneRange();
  }
  function restoreSel() {
    if (!savedSel || !activeEdit) return;
    activeEdit.focus();
    var s = window.getSelection();
    s.removeAllRanges();
    s.addRange(savedSel);
  }

  // Save selection before any toolbar interaction steals focus
  tb.addEventListener('mousedown', function(e) {
    saveSel();
    // Prevent focus loss on buttons (NOT on selects/inputs — they need native focus)
    if (!e.target.closest('select') && !e.target.closest('input[type="color"]') && !e.target.closest('[data-drag]')) {
      e.preventDefault();
    }
  });

  // ── BUTTON COMMANDS ──
  tb.addEventListener('click', function(e) {
    var btn = e.target.closest('button[data-cmd]');
    if (btn) {
      restoreSel();
      var cmd = btn.dataset.cmd;
      // For bold: if CSS makes it bold (font-weight >= 700), use inline style override
      if (cmd === 'bold') {
        var sel = window.getSelection();
        var node = sel.focusNode; if (node && node.nodeType === 3) node = node.parentElement;
        if (node) {
          var cw = parseInt(window.getComputedStyle(node).fontWeight);
          if (cw >= 700 && document.queryCommandState('bold') === false) {
            // CSS-bold — wrap in span with font-weight:normal
            if (!sel.isCollapsed) {
              var range = sel.getRangeAt(0);
              var span = document.createElement('span');
              span.style.fontWeight = 'normal';
              range.surroundContents(span);
              sel.removeAllRanges(); var r2 = document.createRange(); r2.selectNodeContents(span); sel.addRange(r2);
            } else {
              node.style.fontWeight = node.style.fontWeight === 'normal' ? '' : 'normal';
            }
            updateToolbarState(); saveSel(); return;
          }
        }
      }
      document.execCommand(cmd, false, null);
      updateToolbarState();
      saveSel();
      return;
    }
    // ── TEXT CASE TRANSFORMS ──
    var caseAction = e.target.closest('[data-action="titleCase"],[data-action="uppercase"],[data-action="lowercase"]');
    if (caseAction) {
      restoreSel();
      var sel = window.getSelection();
      if (sel && sel.rangeCount > 0 && !sel.isCollapsed) {
        var text = sel.toString();
        var act = caseAction.getAttribute('data-action');
        var result = text;
        if (act === 'uppercase') result = text.toUpperCase();
        else if (act === 'lowercase') result = text.toLowerCase();
        else if (act === 'titleCase') result = text.replace(/\\S+/g, function(w) { return w.charAt(0).toUpperCase() + w.slice(1).toLowerCase(); });
        document.execCommand('insertText', false, result);
      }
      return;
    }

    var linkBtn = e.target.closest('[data-action="link"]');
    if (linkBtn) {
      restoreSel();
      var url = prompt('URL:', 'https://');
      if (url) document.execCommand('createLink', false, url);
      return;
    }
  });

  // ── FONT SIZE (execCommand fontSize + convert <font> to <span>) ──
  var sizeMap = {'12':'1','14':'2','16':'3','18':'4','20':'4','22':'5','24':'5','28':'6','32':'6','36':'7','48':'7'};
  var lastRequestedPx = '18px';

  function applyFontSize(px) {
    restoreSel();
    var cmdVal = sizeMap[px] || '4';
    lastRequestedPx = px + 'px';
    document.execCommand('fontSize', false, cmdVal);
    // Convert <font size=X> to <span style="font-size:Xpx"> while preserving selection
    if (activeEdit) {
      activeEdit.querySelectorAll('font[size]').forEach(function(f) {
        var span = document.createElement('span');
        span.style.fontSize = lastRequestedPx;
        while (f.firstChild) span.appendChild(f.firstChild);
        f.parentNode.replaceChild(span, f);
        // Re-select the span contents
        var range = document.createRange();
        range.selectNodeContents(span);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
      });
    }
    saveSel();
    updateToolbarState();
  }

  // ── FONT NAME (execCommand fontName + convert <font> to <span>) ──
  function applyFontName(font) {
    restoreSel();
    document.execCommand('fontName', false, font);
    if (activeEdit) {
      activeEdit.querySelectorAll('font[face]').forEach(function(f) {
        var span = document.createElement('span');
        span.style.fontFamily = f.getAttribute('face');
        while (f.firstChild) span.appendChild(f.firstChild);
        f.parentNode.replaceChild(span, f);
        var range = document.createRange();
        range.selectNodeContents(span);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
      });
    }
    saveSel();
    updateToolbarState();
  }

  // ── SELECT CHANGE HANDLERS ──
  // Must save selection on focus (before change fires)
  tb.querySelectorAll('select').forEach(function(s) {
    s.addEventListener('focus', function() { saveSel(); });
  });

  tb.addEventListener('change', function(e) {
    var sel = e.target;
    if (sel.dataset.action === 'fontSize' && sel.value) {
      applyFontSize(sel.value);
    }
    if (sel.dataset.action === 'fontName' && sel.value) {
      applyFontName(sel.value);
    }
    // Reset to placeholder after a short delay (so user sees what they picked)
    setTimeout(function() { sel.selectedIndex = 0; }, 300);
  });

  // ── COLOR INPUTS ──
  tb.querySelectorAll('input[type="color"]').forEach(function(inp) {
    inp.addEventListener('focus', function() { saveSel(); });
  });
  tb.addEventListener('input', function(e) {
    var inp = e.target;
    if (!activeEdit) return;
    if (inp.dataset.action === 'foreColor') {
      restoreSel();
      document.execCommand('foreColor', false, inp.value);
      saveSel();
    }
    if (inp.dataset.action === 'hiliteColor') {
      restoreSel();
      document.execCommand('hiliteColor', false, inp.value);
      saveSel();
    }
  });

  function updateToolbarState() {
    // Bold, italic, underline, strikethrough, align states
    tb.querySelectorAll('button[data-cmd]').forEach(function(btn) {
      try { btn.classList.toggle('active', document.queryCommandState(btn.dataset.cmd)); } catch(e) {}
    });
    // Font size — detect current size and show in dropdown
    try {
      var szSel = tb.querySelector('select[data-action="fontSize"]');
      var el = window.getSelection().focusNode;
      if (el && el.nodeType === 3) el = el.parentElement;
      if (el) {
        var cs = window.getComputedStyle(el);
        var px = Math.round(parseFloat(cs.fontSize));
        var found = false;
        for (var i = 0; i < szSel.options.length; i++) {
          if (parseInt(szSel.options[i].value) === px) { szSel.selectedIndex = i; found = true; break; }
        }
        if (!found) szSel.selectedIndex = 0;
        // Font name
        var fnSel = tb.querySelector('select[data-action="fontName"]');
        var fontFamily = cs.fontFamily.replace(/['"]/g, '').split(',')[0].trim();
        var fnFound = false;
        for (var j = 0; j < fnSel.options.length; j++) {
          if (fnSel.options[j].value.toLowerCase() === fontFamily.toLowerCase()) { fnSel.selectedIndex = j; fnFound = true; break; }
        }
        if (!fnFound) fnSel.selectedIndex = 0;
        // Text color
        var fcInp = tb.querySelector('input[data-action="foreColor"]');
        if (fcInp) {
          var rgb = cs.color;
          var m = rgb.match(/(\d+),\s*(\d+),\s*(\d+)/);
          if (m) fcInp.value = '#' + ((1<<24) + (parseInt(m[1])<<16) + (parseInt(m[2])<<8) + parseInt(m[3])).toString(16).slice(1);
        }
      }
    } catch(e) {}
  }

  function positionToolbar(el) {
    if (tbManualPos) { tb.classList.add('visible'); return; } // user dragged it, keep position
    var rect = el.getBoundingClientRect();
    var tbH = 44;
    var top = rect.top - tbH - 10;
    if (top < 4) top = rect.bottom + 8; // below if no room above
    var left = rect.left + (rect.width / 2) - 200;
    if (left < 4) left = 4;
    if (left + 400 > window.innerWidth) left = window.innerWidth - 404;
    tb.style.top = Math.max(0, top) + 'px';
    tb.style.left = Math.max(0, left) + 'px';
    tb.classList.add('visible');
  }
  function hideToolbar() { tb.classList.remove('visible'); tbManualPos = false; }

  // ── UNDO/REDO HISTORY (page-level, 15 snapshots) ──
  var undoStack = [];
  var redoStack = [];
  var initialHtml = document.body.innerHTML;
  undoStack.push(initialHtml);

  function snapshotForUndo() {
    var html = document.body.innerHTML;
    if (undoStack.length === 0 || undoStack[undoStack.length - 1] !== html) {
      undoStack.push(html);
      if (undoStack.length > 16) undoStack.shift(); // keep 15 + current
      redoStack = [];
    }
  }

  function globalUndo() {
    if (undoStack.length <= 1) return;
    finishEdit();
    redoStack.push(undoStack.pop());
    document.body.innerHTML = undoStack[undoStack.length - 1];
    document.body.appendChild(tb);
    reMarkElements();
  }

  function globalRedo() {
    if (redoStack.length === 0) return;
    finishEdit();
    var html = redoStack.pop();
    undoStack.push(html);
    document.body.innerHTML = html;
    document.body.appendChild(tb);
    reMarkElements();
  }

  // Take snapshot when finishing an edit
  var origFinishEdit;

  // Expose undo/redo to parent
  window._advUndo = globalUndo;
  window._advRedo = globalRedo;
  window._advResetAll = function() {
    finishEdit();
    document.body.innerHTML = initialHtml;
    document.body.appendChild(tb);
    undoStack = [initialHtml];
    redoStack = [];
    reMarkElements();
  };

  function reMarkElements() {
    document.querySelectorAll(BLOCK_SELECTOR).forEach(function(el, i) { el.setAttribute('data-editable', 'text-' + i); });
    document.querySelectorAll('img').forEach(function(img, i) { img.setAttribute('data-img-idx', i); });
    var mi = 0;
    document.querySelectorAll('.placeholder, .sb-img').forEach(function(el) { el.setAttribute('data-media-idx', mi++); });
    addBlockControls();
  }

  // ── MARK ELEMENTS ──
  var BLOCK_SELECTOR = 'h1, h2, h3, p, li, .step p, .step-title, .tip, .sb-title, .offer-box h2, .offer-box p, a.cta-bottom, a.sb-cta, .cta-badges div, .sb-badges div, .byline, .sticky-footer a';
  var editable = document.querySelectorAll(BLOCK_SELECTOR);
  editable.forEach(function(el, i) { el.setAttribute('data-editable', 'text-' + i); });
  document.querySelectorAll('img').forEach(function(img, i) { img.setAttribute('data-img-idx', i); });
  var mediaIdx = 0;
  document.querySelectorAll('.placeholder, .sb-img').forEach(function(el) { el.setAttribute('data-media-idx', mediaIdx++); });

  // ── BLOCK CONTROLS (drag + duplicate) ──
  function addBlockControls() {
    // Remove old controls
    document.querySelectorAll('.block-controls').forEach(function(c) { c.remove(); });
    // Get all draggable blocks: editable text, images, img-sets, placeholders
    var blocks = document.querySelectorAll('[data-editable], img[data-img-idx]:not(#adv-header-logo img), .img-set, .placeholder[data-media-idx]');
    blocks.forEach(function(block) {
      if (block.closest('#adv-header-logo') || block.closest('#img-panel') || block.closest('#edit-toolbar')) return;
      if (block.querySelector('.block-controls')) return;
      var ctrl = document.createElement('div');
      ctrl.className = 'block-controls';
      ctrl.innerHTML =
        '<button class="block-ctrl-drag" title="Drag to reorder" draggable="false">⠿</button>' +
        '<button class="block-ctrl-dup" title="Duplicate">⧉</button>' +
        '<button class="block-ctrl-del" title="Delete">🗑</button>';
      block.style.position = 'relative';
      block.insertBefore(ctrl, block.firstChild);
    });
  }
  addBlockControls();

  // ── DRAG & DROP ──
  var dragEl = null;
  var dropIndicator = document.createElement('div');
  dropIndicator.className = 'drop-indicator';
  var dragTimeout = null;

  function getBlockParent(el) {
    // Get the nearest draggable block
    return el.closest('[data-editable], .img-set, .placeholder[data-media-idx], img[data-img-idx]');
  }

  function getAllBlocks() {
    return Array.from(document.querySelectorAll('.article-content > *, .page-wrapper > .article-content > *')).filter(function(el) {
      return !el.matches('#adv-header-logo, #img-panel, #edit-toolbar, style, script, .drop-indicator');
    });
  }

  // Long press to start drag (300ms hold)
  document.addEventListener('mousedown', function(e) {
    var dragBtn = e.target.closest('.block-ctrl-drag');
    if (!dragBtn) return;
    e.preventDefault();
    var block = dragBtn.closest('[data-editable], .img-set, .placeholder, img[data-img-idx]');
    if (!block) return;
    dragTimeout = setTimeout(function() { startDrag(block, e); }, 150);
  });
  document.addEventListener('mouseup', function() {
    if (dragTimeout) { clearTimeout(dragTimeout); dragTimeout = null; }
    if (dragEl) finishDrag();
  });

  function startDrag(el, e) {
    dragEl = el;
    dragEl.classList.add('dragging');
    document.addEventListener('mousemove', onDragMove);
  }

  function onDragMove(e) {
    if (!dragEl) return;
    // Find closest block to insert before/after
    dropIndicator.remove();
    var allBlocks = getAllBlocks();
    var closest = null;
    var closestDist = Infinity;
    var insertBefore = true;

    allBlocks.forEach(function(b) {
      if (b === dragEl) return;
      var rect = b.getBoundingClientRect();
      var midY = rect.top + rect.height / 2;
      var dist = Math.abs(e.clientY - midY);
      if (dist < closestDist) {
        closestDist = dist;
        closest = b;
        insertBefore = e.clientY < midY;
      }
    });

    if (closest) {
      if (insertBefore) {
        closest.parentNode.insertBefore(dropIndicator, closest);
      } else {
        closest.parentNode.insertBefore(dropIndicator, closest.nextSibling);
      }
    }
  }

  function finishDrag() {
    document.removeEventListener('mousemove', onDragMove);
    if (dragEl && dropIndicator.parentNode) {
      dropIndicator.parentNode.insertBefore(dragEl, dropIndicator);
      dragEl.classList.remove('dragging');
      snapshotForUndo();
    }
    dropIndicator.remove();
    dragEl = null;
    reMarkElements();
  }

  // ── DUPLICATE ──
  document.addEventListener('click', function(e) {
    var dupBtn = e.target.closest('.block-ctrl-dup');
    if (!dupBtn) return;
    e.preventDefault();
    e.stopPropagation();
    var block = dupBtn.closest('[data-editable], .img-set, .placeholder, img[data-img-idx]');
    if (!block) return;
    var clone = block.cloneNode(true);
    // Remove controls from clone (will be re-added)
    clone.querySelectorAll('.block-controls').forEach(function(c) { c.remove(); });
    clone.classList.remove('img-selected');
    block.parentNode.insertBefore(clone, block.nextSibling);
    snapshotForUndo();
    reMarkElements();
  }, true);

  // ── DELETE ──
  document.addEventListener('click', function(e) {
    var delBtn = e.target.closest('.block-ctrl-del');
    if (!delBtn) return;
    e.preventDefault();
    e.stopPropagation();
    var block = delBtn.closest('[data-editable], .img-set, .placeholder, img[data-img-idx]');
    if (!block) return;
    block.remove();
    closePanel();
    snapshotForUndo();
    reMarkElements();
  }, true);

  // ── IMAGE SIDE PANEL ──
  var panel = document.createElement('div');
  panel.id = 'img-panel';
  panel.innerHTML = '<div class="panel-header"><span class="panel-title">Image Settings</span><button class="panel-close" id="panel-close-btn">✕</button></div><div id="panel-slots"></div>';
  document.body.appendChild(panel);

  var currentImgIdx = null;
  document.getElementById('panel-close-btn').addEventListener('click', function() { closePanel(); });

  function closePanel() {
    panel.classList.remove('open');
    document.querySelectorAll('.img-selected').forEach(function(el) { el.classList.remove('img-selected'); });
    currentImgIdx = null;
  }

  function openPanel(imgIdx) {
    currentImgIdx = imgIdx;
    var imgs = document.querySelectorAll('img[data-img-idx]');
    var mainImg = imgs[imgIdx];
    if (!mainImg) return;

    // Highlight selected image
    document.querySelectorAll('.img-selected').forEach(function(el) { el.classList.remove('img-selected'); });
    mainImg.classList.add('img-selected');

    // Find img-set if it exists
    var setEl = mainImg.closest('.img-set');
    var desktopSrc = mainImg.src;
    var tabletSrc = setEl ? (setEl.querySelector('.for-tablet') || {}).src || '' : '';
    var mobileSrc = setEl ? (setEl.querySelector('.for-mobile') || {}).src || '' : '';

    var slots = document.getElementById('panel-slots');
    slots.innerHTML = '';

    var devices = [
      { key: 'desktop', icon: '🖥', label: 'Desktop', src: desktopSrc, required: true },
      { key: 'tablet', icon: '📱', label: 'Tablet', src: tabletSrc, required: false },
      { key: 'mobile', icon: '📲', label: 'Mobile', src: mobileSrc, required: false },
    ];

    devices.forEach(function(d) {
      var slot = document.createElement('div');
      slot.className = 'device-slot';
      slot.setAttribute('data-device', d.key);

      var hasCustom = d.key !== 'desktop' && d.src;
      var displaySrc = d.src || desktopSrc;
      var badgeClass = d.key === 'desktop' ? 'badge-custom' : (hasCustom ? 'badge-custom' : 'badge-default');
      var badgeText = d.key === 'desktop' ? 'main' : (hasCustom ? 'custom' : 'using desktop');

      slot.innerHTML =
        '<div class="device-label">' + d.icon + ' ' + d.label +
        ' <span class="badge ' + badgeClass + '">' + badgeText + '</span></div>' +
        '<div class="device-thumb">' +
        '<img src="' + displaySrc + '">' +
        ((!d.required && hasCustom) ? '<button class="remove-btn visible" data-remove="' + d.key + '" title="Remove custom image">✕</button>' : '') +
        '</div>';

      slot.addEventListener('click', function(ev) {
        if (ev.target.closest('[data-remove]')) return; // handled separately
        window.parent.postMessage({ type: 'edit-image', src: displaySrc, index: imgIdx, kind: 'img', device: d.key }, '*');
      });

      slots.appendChild(slot);
    });

    // Remove custom image handlers
    slots.querySelectorAll('[data-remove]').forEach(function(btn) {
      btn.addEventListener('click', function(ev) {
        ev.stopPropagation();
        var device = btn.getAttribute('data-remove');
        removeDeviceImage(imgIdx, device);
      });
    });

    panel.classList.add('open');
  }

  function removeDeviceImage(imgIdx, device) {
    var imgs = document.querySelectorAll('img[data-img-idx]');
    var mainImg = imgs[imgIdx];
    if (!mainImg) return;
    var setEl = mainImg.closest('.img-set');
    if (!setEl) return;
    var devImg = setEl.querySelector('.for-' + device);
    if (devImg) { devImg.remove(); }
    setEl.classList.remove('has-' + device);
    snapshotForUndo();
    openPanel(imgIdx); // refresh panel
  }

  // ── EDIT LOGIC ──
  var activeEdit = null;
  function finishEdit() {
    if (activeEdit) {
      activeEdit.contentEditable = 'false';
      activeEdit.style.outline = '';
      activeEdit.style.outlineOffset = '';
      activeEdit.style.background = '';
      activeEdit.style.minHeight = '';
      activeEdit = null;
      hideToolbar();
      snapshotForUndo();
    }
  }

  document.addEventListener('click', function(e) {
    if (e.target.closest('#edit-toolbar')) return; // don't interfere with toolbar clicks
    var el = e.target.closest('[data-editable]');
    if (el) {
      e.preventDefault();
      e.stopPropagation();
      if (activeEdit === el) return;
      finishEdit();
      activeEdit = el;
      el.contentEditable = 'true';
      el.style.outline = '2px solid #f26722';
      el.style.outlineOffset = '3px';
      el.style.background = 'rgba(242,103,34,0.05)';
      el.style.minHeight = '1em';
      el.focus();
      var range = document.createRange();
      range.selectNodeContents(el);
      var sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
      positionToolbar(el);
      updateToolbarState();
      return;
    }
    // ── Block controls take priority ──
    if (e.target.closest('.block-controls')) return;
    // ── Image click → open side panel ──
    var img = e.target.closest('img[data-img-idx]');
    if (img && !img.closest('#adv-header-logo') && !img.closest('#img-panel')) {
      e.preventDefault();
      openPanel(parseInt(img.getAttribute('data-img-idx')));
      return;
    }
    // Click on panel → don't close
    if (e.target.closest('#img-panel')) return;
    var media = e.target.closest('[data-media-idx]');
    if (media) {
      e.preventDefault();
      window.parent.postMessage({ type: 'edit-image', src: '', alt: '', index: parseInt(media.getAttribute('data-media-idx')), kind: 'placeholder' }, '*');
      return;
    }
    // Click outside → finish
    finishEdit();
  }, true);

  // Update toolbar state on selection change + reposition on scroll
  document.addEventListener('selectionchange', function() {
    if (activeEdit) updateToolbarState();
  });
  window.addEventListener('scroll', function() {
    if (activeEdit) positionToolbar(activeEdit);
  }, { passive: true });

  document.addEventListener('keydown', function(e) {
    // Ctrl+Z / Cmd+Z — undo
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
      if (activeEdit) {
        // Let browser handle native contenteditable undo
        return;
      }
      e.preventDefault();
      globalUndo();
      return;
    }
    // Ctrl+Shift+Z / Cmd+Shift+Z — redo
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey) {
      if (activeEdit) return; // native redo
      e.preventDefault();
      globalRedo();
      return;
    }
    // Ctrl+Y — redo
    if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
      if (activeEdit) return;
      e.preventDefault();
      globalRedo();
      return;
    }
    if (!activeEdit) return;
    if (e.key === 'Escape') { finishEdit(); e.preventDefault(); }
    var tag = activeEdit.tagName.toLowerCase();
    if (e.key === 'Enter' && !e.shiftKey && (tag === 'h1' || tag === 'h2' || tag === 'h3' || tag === 'a' || tag === 'div')) {
      finishEdit(); e.preventDefault();
    }
  });

  // ── MESSAGES ──
  window.addEventListener('message', function(e) {
    if (e.data && e.data.type === 'update-field') {
      var el = document.querySelector('[data-editable="' + e.data.field + '"]');
      if (el) el.innerHTML = e.data.value;
    }
    if (e.data && e.data.type === 'undo') {
      if (activeEdit) { document.execCommand('undo'); } else { globalUndo(); }
      return;
    }
    if (e.data && e.data.type === 'redo') {
      if (activeEdit) { document.execCommand('redo'); } else { globalRedo(); }
      return;
    }
    if (e.data && e.data.type === 'reset-all') { if(window._advResetAll) window._advResetAll(); return; }
    if (e.data && e.data.type === 'get-html') {
      finishEdit();
      // Remove toolbar from DOM before capturing
      var tbEl = document.getElementById('edit-toolbar');
      if (tbEl) tbEl.remove();
      // Remove editor artifacts before capturing
      var panelEl = document.getElementById('img-panel');
      if (panelEl) panelEl.remove();
      document.querySelectorAll('.img-selected').forEach(function(el) { el.classList.remove('img-selected'); });
      document.querySelectorAll('.block-controls').forEach(function(c) { c.remove(); });
      document.querySelectorAll('.drop-indicator').forEach(function(c) { c.remove(); });
      document.querySelectorAll('.dragging').forEach(function(c) { c.classList.remove('dragging'); });
      window.parent.postMessage({ type: 'current-html', html: document.documentElement.outerHTML }, '*');
      // Re-add toolbar + re-wrap images
      document.body.appendChild(tb);
      reMarkElements();
    }
    if (e.data && e.data.type === 'update-image') {
      if (e.data.kind === 'placeholder') {
        var placeholders = document.querySelectorAll('[data-media-idx]');
        var ph = placeholders[e.data.index];
        if (ph) {
          var img = document.createElement('img');
          img.src = e.data.value;
          img.alt = e.data.alt || '';
          img.style.cssText = 'width:100%;border-radius:8px;margin:8px 0';
          img.setAttribute('data-img-idx', document.querySelectorAll('img').length);
          ph.replaceWith(img);
          reMarkElements();
        }
      } else {
        var device = e.data.device || 'all';
        var imgs = document.querySelectorAll('img[data-img-idx]');
        var targetImg = imgs[e.data.index];
        if (!targetImg) return;

        if (device === 'all' || device === 'desktop') {
          // Replace/set the main (desktop) image
          targetImg.src = e.data.value;
        }
        if (device === 'tablet' || device === 'mobile') {
          // Find or create responsive set
          var wrap = targetImg.closest('.img-wrap');
          var setEl = targetImg.closest('.img-set');
          if (!setEl) {
            // Convert single img to img-set
            setEl = document.createElement('div');
            setEl.className = 'img-set';
            targetImg.classList.add('for-desktop');
            targetImg.parentNode.insertBefore(setEl, targetImg);
            setEl.appendChild(targetImg);
          }
          var cls = 'for-' + device;
          var existing = setEl.querySelector('.' + cls);
          if (existing) {
            existing.src = e.data.value;
          } else {
            var devImg = document.createElement('img');
            devImg.src = e.data.value;
            devImg.className = cls;
            devImg.style.cssText = 'width:100%;border-radius:8px;';
            setEl.appendChild(devImg);
          }
          setEl.classList.add('has-' + device);
          // Rebuild overlay to show ✓
          if (wrap) {
            var ov = wrap.querySelector('.img-overlay');
            if (ov) ov.remove();
          }
          // Re-wrap
          reMarkElements();
        }
        snapshotForUndo();
        // Refresh panel if open
        if (currentImgIdx !== null) openPanel(currentImgIdx);
      }
    }
  });
})();
</script>
"""

from fastapi.responses import HTMLResponse

HEADER_LOGO_URL = "https://cdn.shopify.com/s/files/1/0600/8527/2619/files/Design_sans_titre_15.png?v=1774625309"
HEADER_LOGO_HTML = f'''<div id="adv-disclosure" style="text-align:center;padding:3px 0;background:#fafafa;border-bottom:1px solid #f0f0f0;font-size:9px;color:#c0c0c0;letter-spacing:0.03em;font-family:system-ui,sans-serif;">This is an advertorial</div>
<div id="adv-header-logo" style="text-align:center;padding:14px 0 10px;background:#fff;border-bottom:1px solid #eee;">
  <img src="{HEADER_LOGO_URL}" alt="Logo" style="height:52px;max-width:260px;object-fit:contain;">
</div>'''

def _inject_header_logo(html: str) -> str:
    """Inject the disclosure bar + header logo at the top of <body>."""
    # If both already present, skip
    if "adv-header-logo" in html and "adv-disclosure" in html:
        return html
    # If logo exists but no disclosure, inject disclosure before logo
    if "adv-header-logo" in html and "adv-disclosure" not in html:
        disclosure = '<div id="adv-disclosure" style="text-align:center;padding:3px 0;background:#fafafa;border-bottom:1px solid #f0f0f0;font-size:9px;color:#c0c0c0;letter-spacing:0.03em;font-family:system-ui,sans-serif;">This is an advertorial</div>'
        return html.replace('<div id="adv-header-logo"', disclosure + '\n<div id="adv-header-logo"')
    # Neither present — inject both after <body>
    m = _re.search(r'(<body[^>]*>)', html, _re.IGNORECASE)
    if m:
        pos = m.end()
        return html[:pos] + "\n" + HEADER_LOGO_HTML + "\n" + html[pos:]
    return HEADER_LOGO_HTML + "\n" + html

@app.get("/pipeline/{plid}/editable", response_class=HTMLResponse)
async def editable_preview(plid: str):
    """Serve the published HTML with edit script injected — avoids cross-origin iframe issues."""
    out = Path(f"data/output/{plid}")
    if not out.exists():
        raise HTTPException(404, "Pipeline not found")
    htmls = list(out.glob("*.html"))
    if not htmls:
        raise HTTPException(404, "No HTML file found")
    html = htmls[0].read_text(encoding="utf-8")
    # Inject header logo if not already present
    html = _inject_header_logo(html)
    # Inject edit script before </body>
    if "</body>" in html:
        html = html.replace("</body>", EDIT_SCRIPT + "\n</body>")
    else:
        html += EDIT_SCRIPT
    return HTMLResponse(content=html)

# ── SYSTEM ──
@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "products": len(products), "pipelines": len(pipelines), "ts": datetime.utcnow().isoformat()}

@app.get("/references/stats")
async def ref_stats():
    from utils.reference_selector import ReferenceSelector
    return ReferenceSelector().get_db_stats()

# ── BACKGROUND ──
async def _analyze_product_bg(pid, url):
    try:
        from agents.extractor import ExtractorAgent
        from agents.avatar_researcher import AvatarResearcherAgent
        out = f"data/output/products/{pid}"
        Path(out).mkdir(parents=True, exist_ok=True)
        ext = ExtractorAgent(output_dir=out)
        pd = await ext.run(product_url=url)
        av = AvatarResearcherAgent(output_dir=out)
        ad = await av.run(product_data=pd, product_url=url)
        if pid in products:
            p = products[pid]
            pi = pd.get("product_info",{})
            bn = pd.get("benefits",{})
            pr = pi.get("price",{})
            p["name"] = pi.get("title","Unknown")
            p["category"] = pi.get("product_type","")
            p["price"] = f"${pr.get('amount',0)}"
            p["compare_price"] = f"${pr.get('compare_at_price',0)}" if pr.get("compare_at_price") else ""
            p["benefits"] = bn.get("main_benefits",[])[:4]
            p["problem"] = bn.get("problem_solved","")
            p["audience"] = ad.get("avatar",{}).get("demographics","")
            p["data"] = pd
            p["status"] = "ready"
            angles = ad.get("marketing_angles",[])
            p["suggested_angle"] = angles[0].get("angle_id","testimonial") if angles else "testimonial"
            p["suggested_structure"] = "pas"
            p["suggested_tone"] = "conversational"
            p["suggested_persona"] = ad.get("avatar",{}).get("demographics","")
    except Exception as e:
        logger.error(f"Product analysis failed: {e}", exc_info=True)
        if pid in products: products[pid]["name"] = f"ERROR: {str(e)[:60]}"
        if pid in products: products[pid]["status"] = "error"

async def _run_pipeline_bg(plid, req):
    from main import AdvertorialPipeline
    s = pipelines[plid]; q = pipeline_events[plid]; out = f"data/output/{plid}"
    try:
        s["status"] = "running"
        await _emit(q, plid, "running", "Phase 1", "Starting", 0.0)
        product = products.get(req.product_id)
        if not product: raise ValueError(f"Product {req.product_id} not found")
        pipeline = AdvertorialPipeline(output_dir=out)
        _patch(pipeline, q, plid)
        run_config = {"angle":req.angle,"structure":req.structure,"persona":req.persona,"tone":req.tone,"language":req.language,"brief":req.brief}
        result = await pipeline.run(
            product_url=product.get("url", ""),
            product_data=product.get("data") if product.get("data") else None,
            config=run_config,
        )
        s["status"] = "completed"; s["completed_at"] = datetime.utcnow().isoformat(); s["progress"] = 1.0
        # Extract thumbnail from generated HTML
        _thumbnail = ""
        try:
            _html_fname = result.get("html_file", "")
            if _html_fname:
                _html_path = Path(f"data/output/{plid}") / Path(_html_fname).name
                if _html_path.exists():
                    _html_content = _html_path.read_text()
                    _m = re.search(r'<img[^>]+src=["\']([^"\']+)', _html_content)
                    if _m:
                        _thumbnail = _m.group(1)
        except Exception:
            pass
        s["results"] = {"headline": result.get("slug",""), "qa_score": 0, "html_file": result.get("html_file",""), "thumbnail": _thumbnail}
        await _emit(q, plid, "completed", "Done", "", 1.0)
    except Exception as e:
        s["status"] = "failed"; s["error"] = str(e); s["completed_at"] = datetime.utcnow().isoformat()
        logger.error(f"Pipeline {plid} failed: {e}", exc_info=True)
        await _emit(q, plid, "failed", "Error", str(e), s["progress"])

async def _run_agent_bg(plid, name, data):
    try:
        agent = _agent(name, f"data/output/{plid}")
        await agent.run(**data)
    except Exception as e:
        logger.error(f"Agent {name} failed: {e}", exc_info=True)

def _agent(name, out):
    from agents.extractor import ExtractorAgent
    from agents.avatar_researcher import AvatarResearcherAgent
    from agents.image_describer import ImageDescriberAgent
    from agents.info_organizer import InfoOrganizerAgent
    from agents.copywriter import CopywriterAgent
    from agents.visual_strategist import VisualStrategistAgent
    from agents.image_prompter import ImagePrompterAgent
    from agents.video_prompter import VideoPrompterAgent
    from agents.qa_checker import QACheckerAgent
    from agents.html_publisher import HTMLPublisherAgent
    m = {"extractor":ExtractorAgent,"avatar_researcher":AvatarResearcherAgent,"image_describer":ImageDescriberAgent,"info_organizer":InfoOrganizerAgent,"copywriter":CopywriterAgent,"visual_strategist":VisualStrategistAgent,"image_prompter":ImagePrompterAgent,"video_prompter":VideoPrompterAgent,"qa_checker":QACheckerAgent,"html_publisher":HTMLPublisherAgent}
    if name not in m: raise ValueError(f"Unknown: {name}")
    return m[name](output_dir=out)

def _patch(pipeline, q, plid):
    ph = {"extractor":("Phase 1 — Collection",.1),"avatar_researcher":("Phase 1 — Collection",.15),"image_describer":("Phase 1 — Collection",.2),"info_organizer":("Phase 2 — Structuring",.3),"copywriter":("Phase 3 — Writing",.5),"visual_strategist":("Phase 4 — Visuals",.6),"image_prompter":("Phase 4 — Visuals",.65),"video_prompter":("Phase 4 — Visuals",.7),"qa_checker":("Phase 5 — QA",.85),"html_publisher":("Phase 6 — Publishing",.95)}
    for a in dir(pipeline):
        ag = getattr(pipeline, a, None)
        if hasattr(ag,"log_start") and hasattr(ag,"name"):
            info = ph.get(ag.name)
            if info:
                phase, prog = info; orig = ag.log_start
                def mk(n,p,pr,o):
                    def f(**kw): o(**kw); asyncio.create_task(_emit(q,plid,"running",p,n,pr))
                    return f
                ag.log_start = mk(ag.name, phase, prog, orig)

async def _emit(q, plid, status, phase, agent, progress):
    if plid in pipelines:
        pipelines[plid]["status"]=status; pipelines[plid]["current_phase"]=phase; pipelines[plid]["current_agent"]=agent; pipelines[plid]["progress"]=progress
    ev = {"type":"progress","pipeline_id":plid,"status":status,"current_phase":phase,"current_agent":agent,"progress":progress,"timestamp":datetime.utcnow().isoformat()}
    try: await q.put(ev)
    except: pass

if __name__ == "__main__":
    import uvicorn; uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
