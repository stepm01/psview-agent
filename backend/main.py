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
import engine

app = FastAPI(title="PSVIEW Engagement Agent")

# Dev only: lets the Vite dev server call the API cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"], allow_headers=["*"],
)

class ConfigureRequest(BaseModel):
    company: CompanyContext
    candidate: CandidateProfile = CandidateProfile()

class ConfigureResponse(BaseModel):
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
    """Agent configures itself: persona -> plan -> opening message."""
    try:
        persona = persona_mod.synthesize_persona(req.company)
        plan = planner_mod.plan_outreach(req.company, persona, req.candidate)
        state = ConversationState(company=req.company, persona=persona,
                                  plan=plan, candidate=req.candidate)
        turn = engine.open_conversation(state)
        return ConfigureResponse(persona=persona, plan=plan,
                                 state=turn.state, opener=turn.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reply", response_model=AgentTurn)
def reply(req: ReplyRequest):
    """One autonomous agent turn: perceive -> reason -> act. Stateless."""
    try:
        return engine.step(req.state, req.reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/critique")
def critique(req: CritiqueRequest):
    """Agent reflects on its own last message and revises it."""
    try:
        return engine.critique_message(req.state, req.draft)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
def health():
    return {"status": "ok"}

# serve the built React app (one process for the live demo)
DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST, "assets")), name="assets")
    @app.get("/")
    def index():
        return FileResponse(os.path.join(DIST, "index.html"))