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
