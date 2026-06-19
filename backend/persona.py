from llm import chat, parse_json
from schemas import CompanyContext, Persona

PERSONA_SYSTEM = """You are an agent that configures its OWN personality to represent a company when reaching out to candidates.
Given the company context, design a coherent recruiter persona: give yourself a name, a role, a distinct voice, core values, signature vocabulary, and firm boundaries (things you will never do, e.g. fabricate, pressure, overpromise).
The persona MUST reflect THIS company's culture and tone, not a generic recruiter.
Respond ONLY with valid JSON:
{
 "agent_name": "...",
 "role": "...",
 "voice": "<2-3 sentences on tone and style>",
 "values": ["..."],
 "vocabulary": ["<signature words/phrases>"],
 "boundaries": ["<things it will never do>"],
 "self_description": "<1 sentence the agent would say about itself>"
}"""

def synthesize_persona(company: CompanyContext) -> Persona:
    user = (f"COMPANY CONTEXT:\nName: {company.name}\nWho it is: {company.description}\n"
            f"Culture: {company.culture}\nProfiles it hires: {company.hiring_profiles}\n"
            f"Desired tone: {company.tone}")
    return Persona(**parse_json(chat(PERSONA_SYSTEM, user, temperature=0.5)))