from datetime import datetime

from fastapi.testclient import TestClient

import backend.main as main_mod
from backend.agents.constraint_extractor import ConstraintExtractorAgent
from backend.agents.input_analyzer import InputAnalyzerAgent
from backend.agents.itinerary_builder import ItineraryBuilderAgent
from backend.agents.repair_agent import RepairAgent
from backend.graph import AetherTripGraph
from backend.scoring.feasibility_scorer import FeasibilityScorer
from backend.schemas.budget import BudgetBreakdown
from backend.schemas.constraints import HardConstraints
from backend.schemas.itinerary import DayPlan, Itinerary, ItineraryItem
from backend.schemas.places import PlaceCandidate, SourceRef
from backend.schemas.validation import ValidationIssue, ValidationReport
from backend.services.cache_service import CacheService
from backend.services.places_service import PlacesService
from backend.validators.budget_validator import BudgetValidator
from backend.validators.route_time_validator import RouteTimeValidator
from backend.validators.verification_validator import VerificationValidator
from backend.state import TripState


LA_PROMPT = "Plan a 3-day Los Angeles trip from San Jose for 4 friends under $400 each, vegetarian, no car."
VEGETARIAN_NYC_PROMPT = "Vegetarian NYC itinerary"
BUDGET_LA_PROMPT = "Budget LA trip"
NO_CAR_SF_PROMPT = "No-car San Francisco weekend"
RAIN_SAFE_SEATTLE_PROMPT = "Rain-safe Seattle trip"


def _candidate(place_id, name, category, lat, lon, cost=10, rank_score=75):
    return PlaceCandidate(
        id=place_id,
        name=name,
        category=category,
        address=f"{name}, Los Angeles, CA",
        latitude=lat,
        longitude=lon,
        estimated_cost=cost,
        sources=[SourceRef(name="Geoapify", fetched_at=datetime.utcnow().isoformat(), confidence=0.9)],
        source="geoapify",
        source_provider="geoapify",
        verification_status="verified",
        confidence=0.9,
        source_confidence=0.9,
        candidate_rank_score=rank_score,
    )


def _six_candidates():
    return [
        _candidate("geo_griffith", "Griffith Observatory", "attraction", 34.1184, -118.3004, 0),
        _candidate("geo_broad", "The Broad", "museum", 34.0544, -118.2500, 15),
        _candidate("geo_grand_central_market", "Grand Central Market", "restaurant", 34.0505, -118.2487, 25),
        _candidate("geo_echo_park", "Echo Park Lake", "park", 34.0739, -118.2606, 0),
        _candidate("geo_getty", "The Getty", "museum", 34.0780, -118.4741, 20),
        _candidate("geo_veggie_grill", "Veggie Grill", "restaurant", 34.0470, -118.2570, 20),
    ]


def test_extract_la_prompt_constraints():
    parsed = InputAnalyzerAgent().run(TripState(user_input=LA_PROMPT))["parsed_request"]
    result = ConstraintExtractorAgent().run(TripState(user_input=LA_PROMPT, parsed_request=parsed))
    hard = result["constraints"]["hard"]

    assert hard["origin"] == "San Jose"
    assert hard["destination"] == "Los Angeles"
    assert hard["duration_days"] == 3
    assert hard["travelers"] == 4
    assert hard["budget_per_person"] == 400
    assert "vegetarian" in hard["diet"]
    assert hard["transport_mode"] in {"no_car", "public_transit"}


def _extract_constraints(prompt):
    parsed = InputAnalyzerAgent().run(TripState(user_input=prompt))["parsed_request"]
    return ConstraintExtractorAgent().run(TripState(user_input=prompt, parsed_request=parsed))["constraints"]


def test_quick_prompt_vegetarian_nyc_defaults():
    constraints = _extract_constraints(VEGETARIAN_NYC_PROMPT)
    hard = constraints["hard"]
    soft = constraints["soft"]

    assert hard["destination"] == "New York City"
    assert hard["origin"] is None
    assert hard["duration_days"] == 3
    assert hard["travelers"] == 1
    assert hard["budget_per_person"] is None
    assert hard["budget_status"] == "unknown"
    assert "vegetarian" in hard["diet"]
    assert hard["transport_mode"] == "public_transit"
    assert soft["pace"] == "balanced"


def test_quick_prompt_budget_la_defaults():
    constraints = _extract_constraints(BUDGET_LA_PROMPT)
    hard = constraints["hard"]
    soft = constraints["soft"]

    assert hard["destination"] == "Los Angeles"
    assert hard["duration_days"] == 3
    assert hard["travelers"] == 1
    assert hard["budget_per_person"] is None
    assert hard["budget_status"] == "unknown"
    assert hard["transport_mode"] == "public_transit"
    assert soft["budget_style"] == "budget"


def test_quick_prompt_no_car_sf_weekend_defaults():
    constraints = _extract_constraints(NO_CAR_SF_PROMPT)
    hard = constraints["hard"]

    assert hard["destination"] == "San Francisco"
    assert hard["duration_days"] == 2
    assert hard["travelers"] == 1
    assert hard["transport_mode"] in {"no_car", "public_transit"}
    assert hard["no_car"] is True


def test_quick_prompt_rain_safe_seattle_defaults():
    constraints = _extract_constraints(RAIN_SAFE_SEATTLE_PROMPT)
    hard = constraints["hard"]

    assert hard["destination"] == "Seattle"
    assert hard["duration_days"] == 3
    assert hard["travelers"] == 1
    assert hard["weather_preference"] == "rain_safe"
    assert hard["transport_mode"] == "public_transit"


def test_grounding_fetcher_returns_place_candidates_with_coordinates(monkeypatch, tmp_path):
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
            "features": [{
                "properties": {
                    "place_id": "geoapify_the_broad",
                    "name": "The Broad",
                    "categories": ["tourism.museum"],
                    "formatted": "221 S Grand Ave, Los Angeles, CA",
                },
                "geometry": {"coordinates": [-118.2500, 34.0544]},
            }]
        })

    monkeypatch.setattr("backend.services.places_service.httpx.get", fake_get)
    service = PlacesService(CacheService(tmp_path))
    service.api_key = "test-key"

    candidates = service.get_place_candidates("Los Angeles", ["museum"], {})

    assert candidates
    for candidate in candidates:
        assert candidate.id
        assert candidate.name
        assert candidate.latitude is not None
        assert candidate.longitude is not None
        assert candidate.source == "geoapify"
        assert candidate.source_confidence > 0


def test_grounding_destination_only_trip_returns_candidates(monkeypatch, tmp_path):
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
                    "properties": {"lat": 40.7128, "lon": -74.0060},
                    "geometry": {"coordinates": [-74.0060, 40.7128]},
                }]
            })
        return FakeResponse({
            "features": [
                {
                    "properties": {
                        "place_id": "geoapify_met_museum",
                        "name": "The Metropolitan Museum of Art",
                        "categories": ["tourism.museum"],
                        "formatted": "1000 5th Ave, New York, NY",
                    },
                    "geometry": {"coordinates": [-73.9632, 40.7794]},
                },
                {
                    "properties": {
                        "place_id": "geoapify_vegetarian_cafe",
                        "name": "Vegetarian Cafe",
                        "categories": ["catering.restaurant"],
                        "formatted": "New York, NY",
                    },
                    "geometry": {"coordinates": [-73.99, 40.73]},
                },
            ]
        })

    monkeypatch.setattr("backend.services.places_service.httpx.get", fake_get)
    graph = AetherTripGraph()
    graph.places_service = PlacesService(CacheService(tmp_path))
    graph.places_service.api_key = "test-key"
    monkeypatch.setattr(graph.weather_service, "get_forecast", lambda lat, lon, days: {"daily": {"time": []}})
    monkeypatch.setattr(graph.routing_service, "get_route_matrix", lambda locations, profile: {"durations": [], "distances": []})
    state = TripState(
        user_input=VEGETARIAN_NYC_PROMPT,
        constraints=_extract_constraints(VEGETARIAN_NYC_PROMPT),
    )

    result = graph._node_grounding_data_fetcher(state)
    candidates = result["place_candidates"]

    assert result["service_status"]["geocoding"]["status"] == "success"
    assert result["service_status"]["places"]["status"] == "success"
    assert candidates
    assert all(candidate["id"] and candidate["name"] for candidate in candidates)
    assert all(candidate["latitude"] is not None and candidate["longitude"] is not None for candidate in candidates)


def test_itinerary_builder_uses_only_candidate_ids(monkeypatch):
    candidates = _six_candidates()
    agent = ItineraryBuilderAgent()
    agent.use_llm = True
    monkeypatch.setattr(agent, "_generate_llm_itinerary", lambda *args, **kwargs: {
        "destination": "Los Angeles",
        "warnings": [],
        "days": [
            {
                "day_number": 1,
                "title": "Day 1",
                "items": [
                    {
                        "place_id": "geo_griffith",
                        "start_time": "09:00",
                        "end_time": "11:00",
                        "description": "See the city views.",
                        "estimated_cost": 0,
                        "notes": "",
                    }
                ],
            },
            {
                "day_number": 2,
                "title": "Day 2",
                "items": [
                    {
                        "place_id": "geo_broad",
                        "start_time": "09:00",
                        "end_time": "11:00",
                        "description": "Museum visit.",
                        "estimated_cost": 15,
                        "notes": "",
                    }
                ],
            },
            {
                "day_number": 3,
                "title": "Day 3",
                "items": [
                    {
                        "place_id": "geo_grand_central_market",
                        "start_time": "12:00",
                        "end_time": "13:30",
                        "description": "Vegetarian-friendly lunch.",
                        "estimated_cost": 25,
                        "notes": "",
                    }
                ],
            },
        ],
    })
    state = TripState(
        user_input=LA_PROMPT,
        constraints={"hard": {"destination": "Los Angeles", "duration_days": 3}},
        place_candidates=[candidate.model_dump() for candidate in candidates],
    )

    result = agent.run(state)
    valid_ids = {candidate.id for candidate in candidates}
    items = [item for day in result["itinerary"]["days"] for item in day["items"]]

    assert items
    assert {item["place_id"] for item in items} <= valid_ids
    assert all(item["place_name"] for item in items)
    assert all(item["latitude"] is not None and item["longitude"] is not None for item in items)


def test_itinerary_builder_rejects_unknown_ids(monkeypatch):
    candidates = _six_candidates()
    agent = ItineraryBuilderAgent()
    agent.use_llm = True
    monkeypatch.setattr(agent, "_generate_llm_itinerary", lambda *args, **kwargs: {
        "destination": "Los Angeles",
        "warnings": [],
        "days": [{
            "day_number": 1,
            "title": "Bad Day",
            "items": [{
                "place_id": "unknown_day_1",
                "start_time": "09:00",
                "end_time": "11:00",
                "description": "Invented stop.",
                "estimated_cost": 0,
                "notes": "",
            }],
        }],
    })
    state = TripState(
        user_input=LA_PROMPT,
        constraints={"hard": {"destination": "Los Angeles", "duration_days": 3}},
        place_candidates=[candidate.model_dump() for candidate in candidates],
    )

    result = agent.run(state)
    ids = [item["place_id"] for day in result["itinerary"]["days"] for item in day["items"]]

    assert "unknown_day_1" not in ids
    assert result["itinerary"]["generation_method"] == "deterministic_candidate_fallback"
    assert result["service_status"]["itinerary_builder"]["status"] == "fallback"
    assert ids


def test_deterministic_fallback_creates_days_from_candidates():
    candidates = _six_candidates()
    agent = ItineraryBuilderAgent()

    itinerary = agent.build_deterministic_fallback("Los Angeles", 3, candidates, [])

    assert len(itinerary["days"]) == 3
    assert all(len(day["items"]) == 2 for day in itinerary["days"])
    assert all(day["items"] for day in itinerary["days"])
    assert all(item["place_id"] for day in itinerary["days"] for item in day["items"])
    assert all(item["latitude"] is not None and item["longitude"] is not None for day in itinerary["days"] for item in day["items"])


def test_itinerary_builder_falls_back_when_llm_invalid(monkeypatch):
    candidates = _six_candidates()
    agent = ItineraryBuilderAgent()
    agent.use_llm = True
    monkeypatch.setattr(agent, "_generate_llm_itinerary", lambda *args, **kwargs: None)
    state = TripState(
        user_input=VEGETARIAN_NYC_PROMPT,
        constraints={"hard": {"destination": "New York City", "duration_days": 3}},
        place_candidates=[candidate.model_dump() for candidate in candidates],
    )

    result = agent.run(state)

    assert result["itinerary"]["generation_method"] == "deterministic_candidate_fallback"
    assert result["service_status"]["itinerary_builder"]["status"] == "fallback"
    assert len(result["itinerary"]["days"]) == 3
    assert [item for day in result["itinerary"]["days"] for item in day["items"]]


def test_itinerary_items_are_hydrated_with_candidate_data(monkeypatch):
    candidates = _six_candidates()
    agent = ItineraryBuilderAgent()
    agent.use_llm = True
    monkeypatch.setattr(agent, "_generate_llm_itinerary", lambda *args, **kwargs: {
        "destination": "New York City",
        "warnings": [],
        "days": [{
            "day_number": 1,
            "title": "Day 1",
            "items": [{
                "place_id": "geo_getty",
                "start_time": "09:00",
                "end_time": "11:00",
                "description": "Hydrate me.",
                "estimated_cost": 20,
                "notes": "",
            }],
        }, {
            "day_number": 2,
            "title": "Day 2",
            "items": [{
                "place_id": "geo_veggie_grill",
                "start_time": "12:00",
                "end_time": "13:30",
                "description": "Lunch.",
                "estimated_cost": 20,
                "notes": "",
            }],
        }, {
            "day_number": 3,
            "title": "Day 3",
            "items": [{
                "place_id": "geo_broad",
                "start_time": "15:00",
                "end_time": "17:00",
                "description": "Art.",
                "estimated_cost": 15,
                "notes": "",
            }],
        }],
    })
    state = TripState(
        user_input=VEGETARIAN_NYC_PROMPT,
        constraints={"hard": {"destination": "New York City", "duration_days": 3}},
        place_candidates=[candidate.model_dump() for candidate in candidates],
    )

    result = agent.run(state)
    items = [item for day in result["itinerary"]["days"] for item in day["items"]]
    by_id = {candidate.id: candidate for candidate in candidates}

    assert items
    for item in items:
        candidate = by_id[item["place_id"]]
        assert item["place_name"] == candidate.name
        assert item["category"] == candidate.category
        assert item["address"] == candidate.address
        assert item["latitude"] == candidate.latitude
        assert item["longitude"] == candidate.longitude
        assert item["source_confidence"] == candidate.source_confidence
        assert item["verification_status"] == candidate.verification_status


def test_plan_endpoint_returns_itinerary_days_with_mocked_services(monkeypatch):
    graph = AetherTripGraph()
    candidates = _six_candidates()

    def fake_geocode(destination):
        graph.places_service.last_geocoding_status = {
            "provider": "geoapify",
            "status": "success",
            "destination": destination,
            "used_fallback": False,
            "coordinates_found": True,
        }
        return (34.0522, -118.2437)

    def fake_candidates(destination, interests, constraints):
        graph.places_service.last_places_status = {
            "provider": "geoapify",
            "status": "success",
            "destination": destination,
            "count": len(candidates),
            "used_fallback": False,
        }
        return candidates

    monkeypatch.setattr(graph.places_service, "geocode_destination", fake_geocode)
    monkeypatch.setattr(graph.places_service, "get_place_candidates", fake_candidates)
    monkeypatch.setattr(graph.weather_service, "get_forecast", lambda lat, lon, days: {"daily": {"time": []}})
    monkeypatch.setattr(graph.routing_service, "get_route_matrix", lambda locations, profile: {"durations": [], "distances": []})
    graph.itinerary_builder.use_llm = False
    monkeypatch.setattr(main_mod, "graph", graph)

    client = TestClient(main_mod.app)
    response = client.post("/api/trips/plan", json={"user_input": LA_PROMPT})
    data = response.json()

    assert response.status_code == 200
    assert len(data["itinerary"]["days"]) > 0
    assert data["itinerary"]["days"][0]["items"]
    assert data["place_candidates"]


def test_plan_endpoint_vegetarian_nyc_returns_days_with_mocked_services(monkeypatch):
    graph = AetherTripGraph()
    candidates = _six_candidates()

    def fake_geocode(destination):
        graph.places_service.last_geocoding_status = {
            "provider": "geoapify",
            "status": "success",
            "destination": destination,
            "used_fallback": False,
            "coordinates_found": True,
        }
        return (40.7128, -74.0060)

    def fake_candidates(destination, interests, constraints):
        graph.places_service.last_places_status = {
            "provider": "geoapify",
            "status": "success",
            "destination": destination,
            "count": len(candidates),
            "used_fallback": False,
        }
        return candidates

    monkeypatch.setattr(graph.places_service, "geocode_destination", fake_geocode)
    monkeypatch.setattr(graph.places_service, "get_place_candidates", fake_candidates)
    monkeypatch.setattr(graph.weather_service, "get_forecast", lambda lat, lon, days: {"daily": {"time": []}})
    monkeypatch.setattr(graph.routing_service, "get_route_matrix", lambda locations, profile: {"durations": [], "distances": []})
    graph.itinerary_builder.use_llm = False
    monkeypatch.setattr(main_mod, "graph", graph)

    client = TestClient(main_mod.app)
    response = client.post("/api/trips/plan", json={"user_input": VEGETARIAN_NYC_PROMPT})
    data = response.json()

    assert response.status_code == 200
    assert data["constraints"]["hard"]["destination"] == "New York City"
    assert len(data["itinerary"]["days"]) > 0
    assert [item for day in data["itinerary"]["days"] for item in day["items"]]


def test_candidate_ranking_prefers_nature_attractions_over_infrastructure(tmp_path):
    service = PlacesService(CacheService(tmp_path))
    center = (37.7485, -119.5886)

    def ranked(place_id, name, categories, lat=37.75, lon=-119.59):
        category = service._categorize_poi({"categories": categories})
        score = service._score_candidate(
            name=name,
            category=category,
            address=f"{name}, Yosemite National Park",
            latitude=lat,
            longitude=lon,
            confidence=0.9,
            properties={"categories": categories, "formatted": f"{name}, Yosemite National Park"},
            destination_center=center,
            destination="Yosemite National Park",
            constraints={"hard": {"destination": "Yosemite National Park"}},
        )
        return _candidate(place_id, name, category, lat, lon, rank_score=score)

    valley = ranked("yosemite_valley", "Yosemite Valley Viewpoint", ["natural", "tourism.sights"])
    caboose = ranked("rail_caboose_7", "Railroad Caboose Number 7", ["tourism.attraction"])
    road = ranked("el_portal_road", "El Portal Road", ["highway", "road"])
    mining = ranked("mining_museum", "California State Mining and Mineral Museum", ["tourism.museum"])

    ranked_candidates = service._dedupe_and_rank_candidates([caboose, road, valley, mining], "Yosemite National Park", {})

    assert ranked_candidates[0].id == "yosemite_valley"
    assert valley.candidate_rank_score > caboose.candidate_rank_score
    assert valley.candidate_rank_score > road.candidate_rank_score
    assert valley.candidate_rank_score > mining.candidate_rank_score


def test_deterministic_fallback_avoids_duplicate_place_ids():
    agent = ItineraryBuilderAgent()
    itinerary = agent.build_deterministic_fallback("Los Angeles", 3, _six_candidates(), [])

    ids = [item["place_id"] for day in itinerary["days"] for item in day["items"]]

    assert ids
    assert len(ids) == len(set(ids))


def test_deterministic_fallback_downranks_near_duplicate_names(tmp_path):
    service = PlacesService(CacheService(tmp_path))
    center = (37.7485, -119.5886)
    raw = [
        ("falls", "Yosemite Falls Viewpoint", "viewpoint", 37.756, -119.596, ["natural", "tourism.sights"]),
        ("valley", "Yosemite Valley", "park", 37.745, -119.593, ["natural", "leisure.park"]),
        ("tunnel_view", "Tunnel View", "viewpoint", 37.715, -119.677, ["natural", "tourism.sights"]),
        ("glacier_point", "Glacier Point", "viewpoint", 37.727, -119.573, ["natural", "tourism.sights"]),
        ("lower_fall", "Lower Yosemite Fall Trail", "park", 37.748, -119.596, ["natural", "leisure.park"]),
        ("mariposa_grove", "Mariposa Grove", "park", 37.507, -119.599, ["natural", "leisure.park"]),
        ("caboose_1", "Railroad Caboose Number 1", "attraction", 37.80, -119.68, ["tourism.attraction"]),
        ("caboose_2", "Railroad Caboose Number 2", "attraction", 37.81, -119.69, ["tourism.attraction"]),
        ("caboose_3", "Railroad Caboose Number 3", "attraction", 37.82, -119.70, ["tourism.attraction"]),
    ]
    candidates = []
    for place_id, name, category, lat, lon, categories in raw:
        score = service._score_candidate(
            name=name,
            category=category,
            address=f"{name}, Yosemite National Park",
            latitude=lat,
            longitude=lon,
            confidence=0.9,
            properties={"categories": categories, "formatted": f"{name}, Yosemite National Park"},
            destination_center=center,
            destination="Yosemite National Park",
            constraints={"hard": {"destination": "Yosemite National Park"}},
        )
        candidates.append(_candidate(place_id, name, category, lat, lon, rank_score=score))

    ranked_candidates = service._dedupe_and_rank_candidates(candidates, "Yosemite National Park", {})
    first_caboose_index = next(index for index, candidate in enumerate(ranked_candidates) if "Caboose" in candidate.name)

    assert ranked_candidates[0].id in {"falls", "valley", "tunnel_view", "glacier_point", "lower_fall", "mariposa_grove"}
    assert first_caboose_index >= 2
    assert all(candidate.candidate_rank_score < ranked_candidates[0].candidate_rank_score for candidate in ranked_candidates if "Caboose" in candidate.name)

    itinerary = ItineraryBuilderAgent().build_deterministic_fallback("Yosemite National Park", 2, ranked_candidates, [])
    selected_names = [item["place_name"] for day in itinerary["days"] for item in day["items"]]
    assert not any("Caboose" in name for name in selected_names)


def _route_repair_state():
    candidates = [
        _candidate("p1", "High Value First Stop", "attraction", 34.0, -118.0, rank_score=90),
        _candidate("p2", "Middle Value Stop", "museum", 34.1, -118.1, rank_score=80),
        _candidate("p3", "Nearby Viewpoint", "viewpoint", 34.02, -118.02, rank_score=70),
    ]
    items = [
        ItineraryItem(day=1, start_time="09:00", end_time="11:00", place_id="p1", place_name="High Value First Stop", category="attraction", description="", estimated_cost=0, source_confidence=0.9),
        ItineraryItem(day=1, start_time="12:00", end_time="13:30", place_id="p2", place_name="Middle Value Stop", category="museum", description="", estimated_cost=0, source_confidence=0.9),
        ItineraryItem(day=1, start_time="15:00", end_time="17:00", place_id="p3", place_name="Nearby Viewpoint", category="viewpoint", description="", estimated_cost=0, source_confidence=0.9),
    ]
    itinerary = Itinerary(destination="Los Angeles", days=[DayPlan(day=1, day_number=1, items=items)])
    route_matrix = {
        "p1": {"p2": 500, "p3": 10},
        "p2": {"p1": 500, "p3": 10},
        "p3": {"p1": 10, "p2": 10},
    }
    report = ValidationReport(
        passed=False,
        issues=[ValidationIssue(
            type="travel_time_conflict",
            severity="critical",
            day=1,
            place_id="p2",
            message="Need 500 min but only have 60 min.",
            suggested_fix="Reorder stops.",
        )],
        warnings=[],
    )
    return TripState(
        user_input="repair route",
        itinerary=itinerary.model_dump(),
        route_matrix=route_matrix,
        place_candidates=[candidate.model_dump() for candidate in candidates],
        validation_reports=[report.model_dump()],
    )


def test_route_repair_reorders_or_removes_impossible_transition():
    state = _route_repair_state()
    result = RepairAgent().run(state)

    repaired = Itinerary(**result["itinerary"])
    report = RouteTimeValidator(state.route_matrix).validate(repaired)
    repaired_ids = [item.place_id for item in repaired.days[0].items]

    assert any(entry["type"] in {"route_time_reorder", "route_time_remove_stop"} for entry in result["repair_history"])
    assert repaired_ids != ["p1", "p2", "p3"]
    assert not any(issue.type == "travel_time_conflict" for issue in report.issues)


def test_budget_over_25_percent_marks_over_budget_status():
    days = [
        DayPlan(day=day, day_number=day, items=[
            ItineraryItem(day=day, start_time="09:00", end_time="11:00", place_id=f"p{day}", place_name=f"Stop {day}", category="park", description="", estimated_cost=0, source_confidence=0.9)
        ])
        for day in range(1, 11)
    ]
    itinerary = Itinerary(destination="Yosemite National Park", days=days)
    constraints = HardConstraints(
        destination="Yosemite National Park",
        duration_days=10,
        travelers=1,
        budget_per_person=500,
        transport_mode="public_transit",
    )

    breakdown, report = BudgetValidator().validate(itinerary, constraints, num_days=10)

    assert breakdown.status == "over_budget"
    assert breakdown.total_per_person > 625
    assert any(issue.type == "over_budget" and "not feasible" in issue.message.lower() for issue in report.issues)
    assert "Trip is not feasible within the requested budget." in breakdown.warnings


def test_unrepairable_budget_keeps_low_feasibility():
    candidate = _candidate("p1", "Yosemite Valley", "park", 37.745, -119.593)
    item = ItineraryItem(day=1, start_time="09:00", end_time="11:00", place_id="p1", place_name="Yosemite Valley", category="park", description="", estimated_cost=0, source_confidence=0.9)
    itinerary = Itinerary(destination="Yosemite National Park", days=[DayPlan(day=1, day_number=1, items=[item])])
    budget = BudgetBreakdown(
        total_per_person=900,
        total_for_group=900,
        user_budget_per_person=500,
        budget_limit=500,
        per_person_cost=900,
        is_over_budget=True,
        status="over_budget",
    )
    validation_report = ValidationReport(
        passed=False,
        issues=[ValidationIssue(
            type="over_budget",
            severity="critical",
            message="Trip is not feasible within the requested budget.",
        )],
    )

    score = FeasibilityScorer(VerificationValidator({"p1": candidate})).score(
        itinerary,
        [validation_report],
        budget,
        repair_attempts=3,
    )

    assert score.breakdown["budget"] == 0
    assert score.overall_score < 70
    assert "not feasible" in score.explanation.lower()


def test_repair_history_records_changes():
    state = _route_repair_state()
    result = RepairAgent().run(state)
    history = result["repair_history"]

    assert history
    assert all(entry.get("why") for entry in history)
    assert any("before" in entry and "after" in entry for entry in history)
