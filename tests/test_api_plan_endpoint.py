import json
from fastapi.testclient import TestClient
import backend.main as main_mod
from backend.state import TripState


class DummyGraph:
    def compile(self):
        class C:
            def invoke(self, state: TripState):
                # Return a final state dict that matches expected response shape
                return {
                    "trip_id": "trip123",
                    "constraints": state.constraints,
                    "itinerary": {"destination": "X"},
                    "budget_report": {"total_per_person": 100},
                    "validation_reports": [],
                    "repair_history": [],
                    "feasibility_score": {
                        "overall_score": 90,
                        "grade": "A",
                        "breakdown": {
                            "opening_hours": 100,
                            "travel_time": 90,
                            "budget": 90,
                            "source_confidence": 90,
                            "constraint_satisfaction": 100,
                            "weather_risk": 100,
                            "repair_stability": 100
                        },
                        "weights": {
                            "opening_hours": 0.25,
                            "travel_time": 0.20,
                            "budget": 0.20,
                            "source_confidence": 0.15,
                            "constraint_satisfaction": 0.10,
                            "weather_risk": 0.05,
                            "repair_stability": 0.05
                        },
                        "generated_at": "2026-05-07T00:00:00Z",
                        "explanation": "Auto-generated dummy score",
                        "warnings": []
                    },
                    "final_explanation": "Works",
                    "warnings": []
                }
        return C()


def test_plan_endpoint_monkeypatched(monkeypatch):
    # Replace the graph used in main with dummy
    monkeypatch.setattr(main_mod, "graph", DummyGraph())
    client = TestClient(main_mod.app)

    payload = {"user_input": "Plan a day trip to Test City"}
    r = client.post("/api/trips/plan", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Ensure required keys
    for key in ["trip_id", "constraints", "itinerary", "budget_report", "validation_reports", "repair_history", "feasibility_score", "why_this_trip_works", "warnings"]:
        assert key in data
