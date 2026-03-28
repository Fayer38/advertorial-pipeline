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
            config = {}
            product_id = ""
            product_name = ""
            started_at = ""

            if htmls:
                html_file = htmls[0].name
                headline = htmls[0].stem.replace("-", " ").title()[:80]

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
                "error": "", "results": {"headline": headline, "qa_score": qa_score, "html_file": html_file},
            }
            logger.info(f"Loaded pipeline: {plid} ({status}) — {headline[:50]}")
        except Exception as e:
            logger.error(f"Failed to load pipeline {plid}: {e}")

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
        h.append({"id": plid, "product_id": s["product_id"], "product_name": s.get("product_name",""), "product_url": s["product_url"], "status": s["status"], "started_at": s["started_at"], "completed_at": s.get("completed_at",""), "headline": s["results"].get("headline",""), "qa_score": s["results"].get("qa_score",0), "config": s["config"], "progress": s.get("progress",0), "current_phase": s.get("current_phase",""), "current_agent": s.get("current_agent","")})
    h.sort(key=lambda x: x["started_at"], reverse=True)
    return {"pipelines": h}

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
    [data-editable] { transition: outline .15s; cursor: pointer; }
    [data-editable]:hover { outline: 1px dashed rgba(242,103,34,0.4) !important; outline-offset: 2px; }
    [data-editable][contenteditable="true"] { outline: 2px solid #f26722 !important; outline-offset: 3px; cursor: text; }
    img[data-img-idx]:hover { outline: 2px dashed #f26722 !important; outline-offset: 3px; cursor: pointer; }
    .placeholder[data-media-idx]:hover { outline: 2px dashed #f26722 !important; outline-offset: 3px; cursor: pointer; }
    .placeholder[data-media-idx] { position: relative; }
    .placeholder[data-media-idx]:hover::after { content: '📷 Click to replace'; position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); background: #f26722; color: #fff; padding: 6px 14px; border-radius: 6px; font-size: 13px; font-style: normal; font-weight: 700; z-index: 9999; }
    .sb-img[data-media-idx]:hover { outline: 2px dashed #f26722 !important; outline-offset: 3px; cursor: pointer; }

    /* ── TOOLBAR ── */
    #edit-toolbar {
      position: absolute; display: none;
      background: #1a1a1a; border: 1px solid #333; border-radius: 10px;
      padding: 6px 8px; display: none; gap: 2px; align-items: center;
      z-index: 99999; box-shadow: 0 8px 30px rgba(0,0,0,.6);
      flex-wrap: wrap; max-width: 95vw;
    }
    #edit-toolbar.visible { display: flex; }
    #edit-toolbar .tb-sep { width: 1px; height: 22px; background: #333; margin: 0 4px; }
    #edit-toolbar button {
      background: none; border: 1px solid transparent; color: #ccc; cursor: pointer;
      width: 32px; height: 32px; border-radius: 6px; font-size: 14px;
      display: flex; align-items: center; justify-content: center; transition: all .1s;
      padding: 0; font-family: inherit;
    }
    #edit-toolbar button:hover { background: #2a2a2a; color: #fff; border-color: #444; }
    #edit-toolbar button.active { background: #f26722; color: #000; border-color: #f26722; }
    #edit-toolbar select {
      background: #111; color: #ccc; border: 1px solid #333; border-radius: 6px;
      padding: 4px 6px; font-size: 12px; cursor: pointer; height: 32px; outline: none;
    }
    #edit-toolbar select:hover { border-color: #555; }
    #edit-toolbar input[type="color"] {
      width: 28px; height: 28px; border: 1px solid #333; border-radius: 6px;
      background: #111; cursor: pointer; padding: 2px;
    }
  `;
  document.head.appendChild(style);

  // ── CREATE TOOLBAR ──
  var tb = document.createElement('div');
  tb.id = 'edit-toolbar';
  tb.innerHTML = `
    <button data-cmd="undo" title="Undo">↩</button>
    <button data-cmd="redo" title="Redo">↪</button>
    <div class="tb-sep"></div>
    <button data-cmd="bold" title="Bold"><b>B</b></button>
    <button data-cmd="italic" title="Italic"><i>I</i></button>
    <button data-cmd="underline" title="Underline"><u>U</u></button>
    <button data-cmd="strikeThrough" title="Strikethrough"><s>S</s></button>
    <div class="tb-sep"></div>
    <select data-action="fontSize" title="Font Size">
      <option value="">Size</option>
      <option value="1">12px</option>
      <option value="2">14px</option>
      <option value="3">16px</option>
      <option value="4">18px</option>
      <option value="5">22px</option>
      <option value="6">28px</option>
      <option value="7">36px</option>
    </select>
    <select data-action="fontName" title="Font">
      <option value="">Font</option>
      <option value="Roboto, sans-serif">Roboto</option>
      <option value="Montserrat, sans-serif">Montserrat</option>
      <option value="Georgia, serif">Georgia</option>
      <option value="Arial, sans-serif">Arial</option>
      <option value="Helvetica, sans-serif">Helvetica</option>
      <option value="Times New Roman, serif">Times</option>
      <option value="Verdana, sans-serif">Verdana</option>
      <option value="Courier New, monospace">Courier</option>
    </select>
    <div class="tb-sep"></div>
    <input type="color" data-action="foreColor" value="#111111" title="Text Color">
    <input type="color" data-action="hiliteColor" value="#ffffff" title="Highlight">
    <div class="tb-sep"></div>
    <button data-cmd="justifyLeft" title="Align Left">⫷</button>
    <button data-cmd="justifyCenter" title="Center">⫿</button>
    <button data-cmd="justifyRight" title="Align Right">⫸</button>
    <div class="tb-sep"></div>
    <button data-cmd="removeFormat" title="Clear Formatting">✕</button>
    <button data-action="link" title="Link">🔗</button>
  `;
  document.body.appendChild(tb);

  // Toolbar click handlers
  tb.addEventListener('mousedown', function(e) { e.preventDefault(); }); // prevent losing selection
  tb.addEventListener('click', function(e) {
    var btn = e.target.closest('button[data-cmd]');
    if (btn) {
      document.execCommand(btn.dataset.cmd, false, null);
      updateToolbarState();
      return;
    }
    var linkBtn = e.target.closest('[data-action="link"]');
    if (linkBtn) {
      var url = prompt('URL:', 'https://');
      if (url) document.execCommand('createLink', false, url);
      return;
    }
  });
  tb.addEventListener('change', function(e) {
    var sel = e.target;
    if (!activeEdit) return;
    activeEdit.focus(); // re-focus to restore selection
    if (sel.dataset.action === 'fontSize') {
      if (sel.value) document.execCommand('fontSize', false, sel.value);
    }
    if (sel.dataset.action === 'fontName') {
      if (sel.value) document.execCommand('fontName', false, sel.value);
    }
  });
  tb.addEventListener('input', function(e) {
    var inp = e.target;
    if (inp.dataset.action === 'foreColor') {
      document.execCommand('foreColor', false, inp.value);
    }
    if (inp.dataset.action === 'hiliteColor') {
      document.execCommand('hiliteColor', false, inp.value);
    }
  });

  function updateToolbarState() {
    tb.querySelectorAll('button[data-cmd]').forEach(function(btn) {
      var on = document.queryCommandState(btn.dataset.cmd);
      btn.classList.toggle('active', on);
    });
  }

  function positionToolbar(el) {
    var rect = el.getBoundingClientRect();
    var tbH = 44;
    var top = rect.top - tbH - 8 + window.scrollY;
    if (top < window.scrollY + 4) top = rect.bottom + 8 + window.scrollY; // below if no room above
    var left = rect.left + (rect.width / 2) - 200;
    if (left < 8) left = 8;
    if (left + 400 > window.innerWidth) left = window.innerWidth - 408;
    tb.style.top = top + 'px';
    tb.style.left = left + 'px';
    tb.classList.add('visible');
  }
  function hideToolbar() { tb.classList.remove('visible'); }

  // ── MARK ELEMENTS ──
  var editable = document.querySelectorAll('h1, h2, h3, p, li, .step p, .step-title, .tip, .sb-title, .offer-box h2, .offer-box p, a.cta-bottom, a.sb-cta, .cta-badges div, .sb-badges div, .byline, .sticky-footer a');
  editable.forEach(function(el, i) { el.setAttribute('data-editable', 'text-' + i); });
  document.querySelectorAll('img').forEach(function(img, i) { img.setAttribute('data-img-idx', i); });
  var mediaIdx = 0;
  document.querySelectorAll('.placeholder, .sb-img').forEach(function(el) { el.setAttribute('data-media-idx', mediaIdx++); });

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
    var img = e.target.closest('img[data-img-idx]');
    if (img) {
      e.preventDefault();
      window.parent.postMessage({ type: 'edit-image', src: img.src, alt: img.alt || '', index: parseInt(img.getAttribute('data-img-idx')), kind: 'img' }, '*');
      return;
    }
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
    if (e.data && e.data.type === 'get-html') {
      finishEdit();
      // Remove toolbar from DOM before capturing
      var tbEl = document.getElementById('edit-toolbar');
      if (tbEl) tbEl.remove();
      window.parent.postMessage({ type: 'current-html', html: document.documentElement.outerHTML }, '*');
      // Re-add toolbar
      document.body.appendChild(tb);
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
        }
      } else {
        var imgs = document.querySelectorAll('img[data-img-idx]');
        if (imgs[e.data.index]) imgs[e.data.index].src = e.data.value;
      }
    }
  });
})();
</script>
"""

from fastapi.responses import HTMLResponse

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
