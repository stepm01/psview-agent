from llm import chat, parse_json
from schemas import CompanyContext, Persona, CandidateProfile, OutreachPlan

PLAN_SYSTEM = """You are a recruiting strategist agent. Plan a short outreach message sequence (2-4 messages) to engage a candidate.
For each step give a clear objective and the persuasive angle, grounded in the company's real context. This is STRATEGY, not the message text.
Respond ONLY with valid JSON:
{"goal": "<overall goal>", "steps": [{"order": 1, "objective": "...", "angle": "..."}]}"""

def plan_outreach(company: CompanyContext, persona: Persona,
                  candidate: CandidateProfile,
                  intent: str = "get the candidate interested in a conversation") -> OutreachPlan:
    user = (f"COMPANY: {company.name} - {company.description}\nCULTURE: {company.culture}\n"
            f"PERSONA VOICE: {persona.voice}\n"
            f"CANDIDATE: {candidate.name}, {candidate.role}. {candidate.note}\nINTENT: {intent}")
    return OutreachPlan(**parse_json(chat(PLAN_SYSTEM, user, temperature=0.4)))