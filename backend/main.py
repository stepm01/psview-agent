import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from schemas import (CompanyContext, CandidateProfile, ConversationState,
                     AgentTurn, Persona, OutreachPlan)
import persona as persona_mod
import planner as planner_mod
import understand as understand_mod
import engine
import web

app = FastAPI(title="PSVIEW Engagement Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"], allow_headers=["*"],
)

class ConfigureRequest(BaseModel):
    source: str               # a company URL, or a line about the company
    candidate_role: str = ""  # optional override

class ConfigureResponse(BaseModel):
    company: CompanyContext   # what the agent inferred (shown to the user)
    persona: Persona
    plan: OutreachPlan
    state: ConversationState
    opener: str

class ReplyRequest(BaseModel):
    state: ConversationState
    reply: str

class CritiqueRequest(BaseModel):
    state: ConversationState
    draft: str

@app.post("/api/configure", response_model=ConfigureResponse)
def configure(req: ConfigureRequest):
    """One input -> agent understands the company -> configures itself -> opens."""
    try:
        src = req.source.strip()
        if web.is_url(src):
            scraped = web.fetch_company_text(src)
            basis = scraped if len(scraped) > 40 else f"Company website: {src}"
        else:
            basis = src
        company = understand_mod.understand_company(basis)
        persona = persona_mod.synthesize_persona(company)
        role = req.candidate_role.strip() or company.hiring_profiles or "a strong candidate"
        candidate = CandidateProfile(name="there", role=role)
        plan = planner_mod.plan_outreach(company, persona, candidate)
        state = ConversationState(company=company, persona=persona, plan=plan, candidate=candidate)
        turn = engine.open_conversation(state)
        return ConfigureResponse(company=company, persona=persona, plan=plan,
                                 state=turn.state, opener=turn.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reply", response_model=AgentTurn)
def reply(req: ReplyRequest):
    try:
        return engine.step(req.state, req.reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/critique")
def critique(req: CritiqueRequest):
    try:
        return engine.critique_message(req.state, req.draft)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health():
    return {"status": "ok"}

DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")
    @app.get("/")
    def index():
        return FileResponse(os.path.join(DIST, "index.html"))