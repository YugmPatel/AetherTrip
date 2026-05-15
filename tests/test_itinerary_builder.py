from backend.agents.itinerary_builder import ItineraryBuilderAgent
from backend.state import TripState


def _state(sample_places):
    return TripState(
        user_input="Plan a 3-day Los Angeles trip",
        constraints={"hard": {"destination": "Los Angeles", "duration_days": 3}},
        place_candidates=[place.model_dump() for place in sample_places.values()],
    )


def test_itinerary_builder_uses_only_candidate_place_ids(sample_places):
    state = _state(sample_places)
    agent = ItineraryBuilderAgent()
    agent.use_llm = False
    result = agent.run(state)
    valid_ids = set(sample_places.keys())

    assert "itinerary" in result
    for day in result["itinerary"]["days"]:
        for item in day["items"]:
            assert item["place_id"] in valid_ids
            assert item["place_name"] == sample_places[item["place_id"]].name
            assert item["latitude"] == sample_places[item["place_id"]].latitude
            assert item["longitude"] == sample_places[item["place_id"]].longitude


def test_itinerary_rejects_unknown_place_ids(monkeypatch, sample_places):
    agent = ItineraryBuilderAgent()
    agent.use_llm = True

    monkeypatch.setattr(agent, "_generate_llm_itinerary", lambda *args, **kwargs: {
        "destination": "Los Angeles",
        "days": [{
            "day": 1,
            "items": [{
                "place_id": "unknown_day_1",
                "start_time": "09:00",
                "end_time": "10:00",
                "description": "Bad LLM stop",
                "estimated_cost": 0,
            }],
        }],
    })

    result = agent.run(_state(sample_places))
    valid_ids = set(sample_places.keys())
    returned_ids = {
        item["place_id"]
        for day in result["itinerary"]["days"]
        for item in day["items"]
    }

    assert "unknown_day_1" not in returned_ids
    assert returned_ids <= valid_ids
    assert result["service_status"]["llm"]["status"] == "rejected_invalid_place_ids"


def test_trip_response_contains_coordinates_for_map_when_places_available(sample_places):
    agent = ItineraryBuilderAgent()
    agent.use_llm = False
    result = agent.run(_state(sample_places))
    items = [item for day in result["itinerary"]["days"] for item in day["items"]]

    assert items
    assert all(isinstance(item.get("latitude"), float) for item in items)
    assert all(isinstance(item.get("longitude"), float) for item in items)


def test_itinerary_builder_only_uses_candidate_place_ids(sample_places):
    test_itinerary_builder_uses_only_candidate_place_ids(sample_places)


def test_itinerary_builder_hydrates_items_with_coordinates(sample_places):
    test_trip_response_contains_coordinates_for_map_when_places_available(sample_places)


def test_itinerary_builder_rejects_unknown_place_ids(monkeypatch, sample_places):
    test_itinerary_rejects_unknown_place_ids(monkeypatch, sample_places)
