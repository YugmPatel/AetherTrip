from backend.agents.repair_agent import RepairAgent
from backend.state import TripState


def test_repair_loop_stops_after_max_attempts():
    agent = RepairAgent()
    state = TripState(user_input="", validation_reports=[{"passed": False, "issues": [{"type": "x"}]}])

    # Apply repairs repeatedly
    for i in range(3):
        out = agent.run(state)
        assert out.get("repair_history")
        assert state.repair_attempts == i + 1

    # Next run should not apply any more repairs
    out2 = agent.run(state)
    assert out2.get("repair_history") == []
    assert state.repair_attempts >= 3
