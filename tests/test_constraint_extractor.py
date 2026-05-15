from backend.agents.constraint_extractor import ConstraintExtractorAgent
from backend.state import TripState


def test_constraint_extractor_basic():
    agent = ConstraintExtractorAgent()
    state = TripState(user_input="Plan a 3-day trip", parsed_request={
        "origin": "NYC",
        "destination": ["Los Angeles"],
        "dates": "3 days",
        "travelers": 2,
        "budget_per_person": 400,
        "interests": ["beaches"],
    })

    result = agent.run(state)
    assert "constraints" in result
    constraints = result["constraints"]
    assert constraints["hard"]["origin"] == "NYC"
    assert constraints["hard"]["destination"] == "Los Angeles"
    assert constraints["hard"]["duration_days"] == 3
    assert constraints["soft"]["interests"] == ["beaches"]


def test_constraints_extract_la_prompt():
    from backend.agents.input_analyzer import InputAnalyzerAgent

    prompt = "Plan a 3-day Los Angeles trip from San Jose for 4 friends under $400 each, vegetarian, no car."
    parsed = InputAnalyzerAgent().run(TripState(user_input=prompt))["parsed_request"]

    result = ConstraintExtractorAgent().run(TripState(user_input=prompt, parsed_request=parsed))
    constraints = result["constraints"]
    hard = constraints["hard"]

    assert hard["origin"] == "San Jose"
    assert hard["destination"] == "Los Angeles"
    assert hard["duration_days"] == 3
    assert hard["travelers"] == 4
    assert hard["budget_per_person"] == 400
    assert "vegetarian" in hard["diet"]
    assert hard["transport_mode"] in {"no_car", "public_transit"}


def test_extract_la_prompt_constraints():
    test_constraints_extract_la_prompt()
