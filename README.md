# Engagement Agent

An autonomous recruiting agent that configures its own personality from a company's
context and reasons through a candidate conversation. Built for the PSVIEW technical test.

**Live:** https://psview-agent.onrender.com

## What it does
1. **Configure** — describe a company (who it is, culture, who it hires, tone).
2. **Self-configuration** — the agent designs its own persona (name, voice, values,
   signature vocabulary, boundaries), plans a strategic outreach sequence, and opens.
3. **Test area** — preview every message it *would* send (nothing is sent for real).
   Type a candidate reply by hand and watch the agent react in real time.

## Architecture — perceive → reason → act
- **Perceive (LLM):** classifies the candidate's intent and sentiment.
- **Reason (code):** a deterministic decision policy maps intent + conversation state →
  a strategy and next action. Plain Python, fully unit-tested.
- **Act (LLM):** generates the next message strictly in persona, and calls a `schedule_call`
  tool when it decides to propose a meeting.

State (stage, sentiment, objections) persists across turns, so behavior is driven by the
agent's evolving model of the conversation — not a single prompt.

## Extras
- **A/B persona morph** — same candidate reply through two different companies, side by side.
- **Self-critique** — the agent reviews its own draft against its persona and boundaries, then revises.
- **Schedule tool** — produces real "Add to Google Calendar" links (simulated, nothing sent).

## Choices
- FastAPI + React (Vite) + Framer Motion, one Docker image (FastAPI serves the built frontend and API).
- **Stateless API:** full conversation state travels with each request, so it scales horizontally — no shared session store.
- **Groq (gpt-oss-120b)** via the OpenAI-compatible API — swapping to Claude/GPT is a one-line change.
- **Tested where it matters:** the decision policy, schema validation, and JSON parsing are covered by pytest with no LLM needed.

## Run locally
- Backend: `cd backend && pip install -r requirements.txt && uvicorn main:app --port 8000`
- Frontend: `cd frontend && npm install && npm run dev`
- Tests: `cd backend && python -m pytest tests/ -q`

## What makes it intelligent and not just an LLM call
Its decisions live in code, not in a prompt. The LLM perceives language and produces
language, but the agent chooses its strategy through an explicit, testable policy over
evolving conversation state — reasoning over a state machine, not a single generation.