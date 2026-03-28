"""
API REST FastAPI v2 — Products + Advertorials flow.
"""
import asyncio, json, logging, uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
app = FastAPI(title="Advertorial Pipeline API", version="2.0.0")
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
        h.append({"id": plid, "product_id": s["product_id"], "product_name": s.get("product_name",""), "product_url": s["product_url"], "status": s["status"], "started_at": s["started_at"], "completed_at": s.get("completed_at",""), "headline": s["results"].get("headline",""), "qa_score": s["results"].get("qa_score",0), "config": s["config"]})
    h.sort(key=lambda x: x["started_at"], reverse=True)
    return {"pipelines": h}

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
        s["results"] = {"headline": result.get("slug",""), "qa_score": 0, "html_file": result.get("html_file","")}
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
