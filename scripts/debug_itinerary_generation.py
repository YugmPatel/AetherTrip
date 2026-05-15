"""Debug AetherTrip itinerary generation for short and fully specified prompts."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.graph import AetherTripGraph  # noqa: E402
from backend.state import TripState  # noqa: E402


PROMPTS = [
    "Vegetarian NYC itinerary",
    "Budget LA trip",
    "No-car San Francisco weekend",
    "Plan a 3-day Los Angeles trip from San Jose for 4 friends under $400 each, vegetarian, no car.",
]


def _state_to_dict(raw_state: Any) -> Dict[str, Any]:
    if isinstance(raw_state, TripState):
        return raw_state.model_dump()
    if hasattr(raw_state, "model_dump"):
        return raw_state.model_dump()
    return dict(raw_state or {})


def _hard_constraints(state: Dict[str, Any]) -> Dict[str, Any]:
    constraints = state.get("constraints") or {}
    return constraints.get("hard") or {}


def _itinerary_items(itinerary: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = []
    for day in itinerary.get("days", []) or []:
        items.extend(day.get("items", []) or [])
    return items


def _print_json(label: str, value: Any) -> None:
    print(f"{label}:")
    print(json.dumps(value, indent=2, default=str))


def _prompt_failures(state: Dict[str, Any]) -> List[str]:
    hard = _hard_constraints(state)
    candidates = state.get("place_candidates") or []
    itinerary = state.get("itinerary") or {}
    items = _itinerary_items(itinerary)
    failures = []

    if hard.get("destination") and not itinerary.get("days"):
        failures.append("destination prompt returned zero itinerary days")
    if hard.get("destination") and candidates and not items:
        failures.append("destination prompt returned zero itinerary items despite candidates")
    for item in items:
        if not item.get("place_name"):
            failures.append(f"item missing place_name: {item.get('place_id')}")
        if item.get("latitude") is None or item.get("longitude") is None:
            failures.append(f"item missing coordinates: {item.get('place_id')}")
        if item.get("place_id") == "unknown_day_1" or item.get("place_name") == "Your Trip":
            failures.append(f"invalid placeholder item: {item.get('place_id')}")
    return failures


def _print_prompt_result(prompt: str, state: Dict[str, Any]) -> None:
    hard = _hard_constraints(state)
    candidates = state.get("place_candidates") or []
    itinerary = state.get("itinerary") or {}
    items = _itinerary_items(itinerary)

    print("=" * 72)
    print(f"prompt: {prompt}")
    print(f"destination: {hard.get('destination')}")
    print(f"duration_days: {hard.get('duration_days')}")
    print(f"travelers: {hard.get('travelers')}")
    print(f"budget: {hard.get('budget_per_person')}")
    print(f"diet: {hard.get('diet')}")
    print(f"transport_mode: {hard.get('transport_mode')}")
    _print_json("service_status", state.get("service_status") or {})
    print(f"place_candidates count: {len(candidates)}")
    print(f"first 5 candidate names: {[candidate.get('name') for candidate in candidates[:5]]}")
    print(f"itinerary.days count: {len(itinerary.get('days') or [])}")
    print(f"item count: {len(items)}")
    print(f"item names: {[item.get('place_name') for item in items]}")
    print(f"generation_method: {itinerary.get('generation_method')}")
    _print_json("errors", state.get("errors") or [])
    _print_json("warnings", state.get("warnings") or [])


def main() -> None:
    graph = AetherTripGraph().compile()
    failures = []

    for prompt in PROMPTS:
        final_state = _state_to_dict(graph.invoke(TripState(user_input=prompt)))
        _print_prompt_result(prompt, final_state)
        for failure in _prompt_failures(final_state):
            failures.append(f"{prompt}: {failure}")

    if failures:
        _print_json("debug failures", failures)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
