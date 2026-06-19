import json
import pytest
from schemas import (CompanyContext, Persona, OutreachPlan, PlanStep, CandidateProfile,
                     ConversationState, ReplyAnalysis, Intent, Sentiment, Action, Stage)
from engine import decide_action
from llm import parse_json


def make_state(stage=Stage.ENGAGING, objections=None):
    return ConversationState(
        company=CompanyContext(name="Acme"),
        persona=Persona(agent_name="Nova", role="Talent", voice="warm"),
        plan=OutreachPlan(goal="engage", steps=[PlanStep(order=1, objective="hook", angle="mission")]),
        candidate=CandidateProfile(name="Sam", role="engineer"),
        stage=stage, objections=objections or [],
    )

def analysis(intent):
    return ReplyAnalysis(intent=intent, sentiment=Sentiment.NEUTRAL, reasoning="x")


# ---- the agent's reasoning, as pure testable code ----
@pytest.mark.parametrize("intent,stage,objections,expected", [
    (Intent.NOT_INTERESTED, Stage.ENGAGING, [], Action.BACK_OFF),
    (Intent.OBJECTION,      Stage.ENGAGING, [], Action.ADDRESS_OBJECTION),
    (Intent.OBJECTION,      Stage.ENGAGING, ["a", "b"], Action.BACK_OFF),
    (Intent.QUESTION,       Stage.ENGAGING, [], Action.ANSWER_QUESTION),
    (Intent.NEEDS_INFO,     Stage.ENGAGING, [], Action.PROVIDE_INFO),
    (Intent.INTERESTED,     Stage.INTRO,    [], Action.BUILD_MOMENTUM),
    (Intent.INTERESTED,     Stage.ENGAGING, [], Action.PROPOSE_NEXT_STEP),
    (Intent.AMBIGUOUS,      Stage.ENGAGING, [], Action.CLARIFY),
])
def test_decision_policy(intent, stage, objections, expected):
    assert decide_action(analysis(intent), make_state(stage, objections)).action == expected

def test_not_interested_closes():
    assert decide_action(analysis(Intent.NOT_INTERESTED), make_state()).next_stage == Stage.CLOSED

def test_repeated_objection_backs_off():
    d = decide_action(analysis(Intent.OBJECTION), make_state(objections=["x", "y"]))
    assert d.action == Action.BACK_OFF and d.next_stage == Stage.CLOSED


# ---- schema validation ----
def test_intent_enum_rejects_garbage():
    with pytest.raises(Exception):
        ReplyAnalysis(intent="banana", sentiment=Sentiment.NEUTRAL, reasoning="x")

def test_persona_requires_name():
    with pytest.raises(Exception):
        Persona(role="x", voice="y")

def test_state_roundtrip():
    s = make_state()
    restored = ConversationState(**json.loads(s.model_dump_json()))
    assert restored.persona.agent_name == "Nova"


# ---- parse_json robustness (protects the live demo from messy LLM output) ----
def test_parse_plain_json():
    assert parse_json('{"a": 1}') == {"a": 1}

def test_parse_fenced_json():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}

def test_parse_json_with_prose():
    assert parse_json('Sure! {"a": 1} hope that helps') == {"a": 1}