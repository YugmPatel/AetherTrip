from backend.graph import AetherTripGraph
from backend.state import TripState


def test_grounding_data_fetcher_monkeypatch(monkeypatch, sample_places, weather_data, route_matrix):
    graph = AetherTripGraph()

    # Monkeypatch services to return deterministic fixtures
    monkeypatch.setattr(graph.places_service, "get_place_candidates", lambda destination, interests, constraints: list(sample_places.values()))
    monkeypatch.setattr(graph.weather_service, "get_forecast", lambda lat, lon, days: weather_data)
    monkeypatch.setattr(graph.routing_service, "get_route_matrix", lambda locations, profile: {"distances": route_matrix, "durations": route_matrix})

    # Prepare state with constraints
    state = TripState(user_input="", constraints={"hard": {"destination": "Test City", "interests": ["beach"]}})

    result = graph._node_grounding_data_fetcher(state)
    assert "place_candidates" in result
    assert isinstance(result["place_candidates"], list)
    assert "weather_data" in result
    assert "route_matrix" in result
