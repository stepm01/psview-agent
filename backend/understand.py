from llm import chat, parse_json
from schemas import CompanyContext

UNDERSTAND_SYSTEM = """You are an agent that researches a company from limited input
(a website's text, a URL, or a one-line description) and produces a structured profile.
Infer sensibly from what you're given. If something isn't stated, make a reasonable, grounded
inference — but never invent specific facts (no fake funding, headcount, or client names).
Never invent specific numbers, percentages, metrics, or claims that aren't in the company context — if you don't have a real figure, speak qualitatively instead.
Respond ONLY with valid JSON:
{
 "name": "<company name>",
 "description": "<1-2 sentences on what it does>",
 "culture": "<short phrase on the culture/vibe>",
 "hiring_profiles": "<the kind of people it hires>",
 "tone": "<the outreach tone that fits this company>"
}"""

def understand_company(raw: str) -> CompanyContext:
    return CompanyContext(**parse_json(chat(UNDERSTAND_SYSTEM, f"INPUT:\n{raw}", temperature=0.4)))