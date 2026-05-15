from backend.graph import AetherTripGraph
from backend.state import TripState


def test_grounding_data_fetcher_monkeypatch(monkeypatch, sample_places, weather_data, route_matrix):
    graph = AetherTripGraph()

    # Monkeypatch services to return deterministic fixtures
    monkeypatch.setattr(graph.places_service, "get_place_candidates", lambda destination, interests, constraints: list(sample_places.values()))
    monkeypatch.setattr(graph.places_service, "geocode_destination", lambda destination: (34.0, -118.0))
    monkeypatch.setattr(graph.weather_service, "get_forecast", lambda lat, lon, days: weather_data)
    monkeypatch.setattr(graph.routing_service, "get_route_matrix", lambda locations, profile: {"distances": route_matrix, "durations": route_matrix})

    # Prepare state with constraints
    state = TripState(user_input="", constraints={"hard": {"destination": "Test City", "interests": ["beach"]}})

    result = graph._node_grounding_data_fetcher(state)
    assert "place_candidates" in result
    assert isinstance(result["place_candidates"], list)
    assert "weather_data" in result
    assert "route_matrix" in result


def test_geoapify_places_non_empty_with_mocked_response(monkeypatch, tmp_path):
    from backend.services.cache_service import CacheService
    from backend.services.places_service import PlacesService

    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    def fake_get(url, params=None, timeout=10.0):
        if "geocode" in url:
            return FakeResponse({
                "features": [{
                    "properties": {"lat": 34.0522, "lon": -118.2437},
                    "geometry": {"coordinates": [-118.2437, 34.0522]},
                }]
            })

        return FakeResponse({
            "features": [
                {
                    "properties": {
                        "place_id": "geoapify_grand_central_market",
                        "name": "Grand Central Market",
                        "categories": ["catering.restaurant"],
                        "formatted": "317 S Broadway, Los Angeles, CA",
                    },
                    "geometry": {"coordinates": [-118.2487, 34.0505]},
                },
                {
                    "properties": {
                        "place_id": "geoapify_the_broad",
                        "name": "The Broad",
                        "categories": ["tourism.museum"],
                        "formatted": "221 S Grand Ave, Los Angeles, CA",
                    },
                    "geometry": {"coordinates": [-118.2500, 34.0544]},
                },
            ]
        })

    monkeypatch.setattr("backend.services.places_service.httpx.get", fake_get)
    service = PlacesService(CacheService(tmp_path))
    service.api_key = "test-key"
    service.base_url = "https://api.geoapify.com/v1"

    places = service.get_place_candidates("Los Angeles", ["food", "museum"], {})

    assert places
    assert {place.name for place in places} >= {"Grand Central Market", "The Broad"}
    assert all(place.source_provider == "geoapify" for place in places)
    assert all(place.source == "geoapify" for place in places)
    assert all(place.source_confidence > 0 for place in places)
    assert all(place.latitude and place.longitude for place in places)
    assert service.last_places_status["count"] == 2


def test_places_pipeline_returns_candidates_with_coordinates(monkeypatch, tmp_path):
    test_geoapify_places_non_empty_with_mocked_response(monkeypatch, tmp_path)
