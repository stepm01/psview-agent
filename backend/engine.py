from llm import chat, parse_json
import tools
from schemas import (ConversationState, ReplyAnalysis, Decision, AgentTurn,
                     Intent, Sentiment, Action, Stage, Message)

# ---------- PERCEIVE (LLM) ----------
CLASSIFY_SYSTEM = """You analyze a candidate's reply in a recruiting conversation and classify it.

Choose the MOST ACTIONABLE intent:
- interested: shows openness, curiosity, or willingness to keep talking
- objection: hesitation, reluctance, satisfaction with their current role, doubt, or pushback — EVEN IF phrased as a question ("I'm happy where I am", "why would I leave?", "sounds risky")
- question: a genuine info request with NO pushback ("what's the stack?", "where are you based?")
- needs_info: asks for specific details before deciding (comp, location, scope)
- not_interested: clearly declines or asks to stop
- ambiguous: too short or unclear to tell

Tie-breaker: if the reply mixes pushback with a question, classify it as objection.

sentiment must be one of: positive, neutral, negative
Respond ONLY with valid JSON: {"intent": "...", "sentiment": "...", "reasoning": "<1-2 sentences>"}"""

def classify_reply(state: ConversationState, reply: str) -> ReplyAnalysis:
    convo = "\n".join(f"{m.sender}: {m.text}" for m in state.history)
    user = f"CONVERSATION SO FAR:\n{convo}\n\nCANDIDATE'S LATEST REPLY:\n{reply}"
    return ReplyAnalysis(**parse_json(chat(CLASSIFY_SYSTEM, user, temperature=0.1)))

# ---------- REASON (deterministic policy: real code, not an LLM call) ----------
def decide_action(analysis: ReplyAnalysis, state: ConversationState) -> Decision:
    intent, stage = analysis.intent, state.stage
    if intent == Intent.NOT_INTERESTED:
        return Decision(action=Action.BACK_OFF,
                        strategy="Acknowledge gracefully, leave the door open, do not push.",
                        next_stage=Stage.CLOSED)
    if intent == Intent.OBJECTION:
        if len(state.objections) >= 2:
            return Decision(action=Action.BACK_OFF,
                            strategy="Respect the repeated hesitation; offer to reconnect later.",
                            next_stage=Stage.CLOSED)
        return Decision(action=Action.ADDRESS_OBJECTION,
                        strategy="Acknowledge the concern, reframe with a concrete company value, no pressure.",
                        next_stage=Stage.HANDLING_OBJECTION)
    if intent == Intent.QUESTION:
        return Decision(action=Action.ANSWER_QUESTION,
                        strategy="Answer concretely from the real company context, then invite the next step.",
                        next_stage=Stage.ENGAGING)
    if intent == Intent.NEEDS_INFO:
        return Decision(action=Action.PROVIDE_INFO,
                        strategy="Provide the specific information, grounded in company context.",
                        next_stage=Stage.ENGAGING)
    if intent == Intent.INTERESTED:
        if stage in (Stage.ENGAGING, Stage.HANDLING_OBJECTION, Stage.CLOSING):
            return Decision(action=Action.PROPOSE_NEXT_STEP,
                            strategy="Build on the momentum and propose a concrete next step (a short call).",
                            next_stage=Stage.CLOSING)
        return Decision(action=Action.BUILD_MOMENTUM,
                        strategy="Reinforce why they're a fit, deepen interest before proposing a step.",
                        next_stage=Stage.ENGAGING)
    return Decision(action=Action.CLARIFY,
                    strategy="Ask one clarifying question to understand where they stand.",
                    next_stage=state.stage)

# ---------- ACT (LLM, in persona) ----------
GENERATE_SYSTEM = """You are {agent_name}, {role}, reaching out on behalf of {company_name}.
VOICE: {voice}
VALUES: {values}
SIGNATURE VOCABULARY (use naturally, never forced): {vocabulary}
BOUNDARIES (never violate): {boundaries}

Write the NEXT message to the candidate, following this strategy exactly: {strategy}
Stay fully in persona, reflect the REAL company context, be concise and human. No subject lines, no placeholders.
Respond ONLY with valid JSON: {{"message": "<the message text>"}}"""

def generate_message(state: ConversationState, decision: Decision, reply: str = None) -> str:
    p = state.persona
    system = GENERATE_SYSTEM.format(
        agent_name=p.agent_name, role=p.role, company_name=state.company.name,
        voice=p.voice, values=", ".join(p.values), vocabulary=", ".join(p.vocabulary),
        boundaries=", ".join(p.boundaries), strategy=decision.strategy)
    convo = "\n".join(f"{m.sender}: {m.text}" for m in state.history) or "(no messages yet)"
    extra = f"\nCANDIDATE JUST SAID: {reply}" if reply else ""
    user = (f"COMPANY CONTEXT: {state.company.description} | CULTURE: {state.company.culture}\n"
            f"CANDIDATE: {state.candidate.name}, {state.candidate.role}\n"
            f"CONVERSATION:\n{convo}{extra}")
    return parse_json(chat(system, user, temperature=0.6)).get("message", "")

# ---------- ORCHESTRATION ----------
def open_conversation(state: ConversationState) -> AgentTurn:
    first = state.plan.steps[0] if state.plan.steps else None
    strategy = (f"Opening message. Objective: {first.objective}. Angle: {first.angle}."
                if first else "Send a warm, specific opening that reflects the company.")
    decision = Decision(action=Action.OPEN, strategy=strategy, next_stage=Stage.ENGAGING)
    analysis = ReplyAnalysis(intent=Intent.AMBIGUOUS, sentiment=Sentiment.NEUTRAL,
                             reasoning="No candidate reply yet, initiating outreach from the plan.")
    msg = generate_message(state, decision)
    state.history.append(Message(sender="agent", text=msg))
    state.stage = decision.next_stage
    state.turn_count += 1
    return AgentTurn(analysis=analysis, decision=decision, message=msg, state=state)

def step(state: ConversationState, candidate_reply: str) -> AgentTurn:
    state.history.append(Message(sender="candidate", text=candidate_reply))
    analysis = classify_reply(state, candidate_reply)                 # perceive
    if analysis.intent == Intent.OBJECTION:
        state.objections.append(candidate_reply)
    decision = decide_action(analysis, state)                         # reason (code)
    msg = generate_message(state, decision, candidate_reply)          # act
    state.history.append(Message(sender="agent", text=msg))
    state.sentiment = analysis.sentiment
    state.stage = decision.next_stage
    state.turn_count += 1
    schedule = tools.build_schedule(state) if decision.action == Action.PROPOSE_NEXT_STEP else None
    return AgentTurn(analysis=analysis, decision=decision, message=msg, state=state, schedule=schedule)

# ---------- SELF-CRITIQUE (reflection: the agent reviews its own draft) ----------
CRITIQUE_SYSTEM = """You are a strict reviewer of a recruiting agent's own draft message.
Given the agent's persona (voice, values, boundaries) and its draft, critique it honestly:
- Does it stay in persona and honor EVERY boundary?
- Is it specific to the company, not generic?
- Any overpromising, pressure, or fabrication?
Then produce an improved version fixing the issues. If already strong, make minimal edits.
Respond ONLY with valid JSON: {"issues": ["..."], "critique": "<2-3 sentences>", "revised": "<improved message>"}"""

def critique_message(state: ConversationState, draft: str) -> dict:
    p = state.persona
    user = (f"PERSONA VOICE: {p.voice}\nVALUES: {', '.join(p.values)}\nBOUNDARIES: {', '.join(p.boundaries)}\n"
            f"COMPANY: {state.company.name} - {state.company.description}\n\nDRAFT MESSAGE:\n{draft}")
    return parse_json(chat(CRITIQUE_SYSTEM, user, temperature=0.3))