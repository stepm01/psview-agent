from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

class CompanyContext(BaseModel):
    name: str
    description: str = ""
    culture: str = ""
    hiring_profiles: str = ""
    tone: str = ""

class Persona(BaseModel):
    agent_name: str
    role: str
    voice: str
    values: List[str] = []
    vocabulary: List[str] = []
    boundaries: List[str] = []
    self_description: str = ""

class PlanStep(BaseModel):
    order: int
    objective: str
    angle: str

class OutreachPlan(BaseModel):
    goal: str
    steps: List[PlanStep] = []

class Intent(str, Enum):
    INTERESTED = "interested"
    QUESTION = "question"
    OBJECTION = "objection"
    NOT_INTERESTED = "not_interested"
    NEEDS_INFO = "needs_info"
    AMBIGUOUS = "ambiguous"

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class Action(str, Enum):
    OPEN = "open"
    ANSWER_QUESTION = "answer_question"
    ADDRESS_OBJECTION = "address_objection"
    PROVIDE_INFO = "provide_info"
    BUILD_MOMENTUM = "build_momentum"
    PROPOSE_NEXT_STEP = "propose_next_step"
    CLARIFY = "clarify"
    BACK_OFF = "back_off"

class Stage(str, Enum):
    INTRO = "intro"
    ENGAGING = "engaging"
    HANDLING_OBJECTION = "handling_objection"
    CLOSING = "closing"
    CLOSED = "closed"

class Message(BaseModel):
    sender: str
    text: str

class CandidateProfile(BaseModel):
    name: str = "the candidate"
    role: str = ""
    note: str = ""

class ConversationState(BaseModel):
    company: CompanyContext
    persona: Persona
    plan: OutreachPlan
    candidate: CandidateProfile
    history: List[Message] = []
    stage: Stage = Stage.INTRO
    sentiment: Sentiment = Sentiment.NEUTRAL
    objections: List[str] = []
    turn_count: int = 0

class ReplyAnalysis(BaseModel):
    intent: Intent
    sentiment: Sentiment
    reasoning: str

class Decision(BaseModel):
    action: Action
    strategy: str
    next_stage: Stage

class ScheduleSlot(BaseModel):
    label: str
    start_iso: str
    end_iso: str

class Schedule(BaseModel):
    title: str
    duration_minutes: int = 15
    agenda: str = ""
    slots: List[ScheduleSlot] = []

class AgentTurn(BaseModel):
    analysis: ReplyAnalysis
    decision: Decision
    message: str
    state: ConversationState
    schedule: Optional[Schedule] = None