import pytest
from datetime import datetime

from backend.schemas.places import PlaceCandidate, SourceRef
from backend.schemas.itinerary import Itinerary, DayPlan, ItineraryItem
from backend.schemas.constraints import HardConstraints


@pytest.fixture
def sample_places():
    now = datetime.utcnow().isoformat() + "Z"
    p1 = PlaceCandidate(
        id="p1",
        name="Open Attraction",
        category="attraction",
        address="1 Main St",
        latitude=34.0,
        longitude=-118.0,
        rating=4.5,
        estimated_cost=10,
        opening_hours={"monday_to_friday": "9:00-17:00"},
        sources=[SourceRef(name="Geoapify", fetched_at=now, confidence=0.95)],
        verification_status="verified",
        confidence=0.95,
    )
    p2 = PlaceCandidate(
        id="p2",
        name="Unknown Hours Cafe",
        category="restaurant",
        address="2 Market St",
        latitude=34.01,
        longitude=-118.01,
        rating=4.0,
        estimated_cost=20,
        opening_hours=None,
        sources=[SourceRef(name="Mock", fetched_at=now, confidence=0.5)],
        verification_status="partially_verified",
        confidence=0.5,
    )
    p3 = PlaceCandidate(
        id="p3",
        name="Closed Museum",
        category="attraction",
        address="3 Museum Rd",
        latitude=34.02,
        longitude=-118.02,
        rating=4.2,
        estimated_cost=15,
        opening_hours={"closed": True},
        sources=[SourceRef(name="Mock", fetched_at=now, confidence=0.3)],
        verification_status="unverified",
        confidence=0.3,
    )
    return {p.id: p for p in (p1, p2, p3)}


@pytest.fixture
def simple_itinerary():
    # Two items on same day with a short gap to test route validator
    item1 = ItineraryItem(
        day=1,
        start_time="09:00",
        end_time="10:00",
        place_id="p1",
        place_name="Open Attraction",
        category="attraction",
        description="Visit open attraction",
        estimated_cost=10,
        travel_time_from_previous_minutes=0,
        source_confidence=0.95,
    )
    item2 = ItineraryItem(
        day=1,
        start_time="10:15",
        end_time="11:15",
        place_id="p2",
        place_name="Unknown Hours Cafe",
        category="restaurant",
        description="Lunch",
        estimated_cost=20,
        travel_time_from_previous_minutes=10,
        source_confidence=0.5,
    )
    day1 = DayPlan(day=1, date=(datetime.utcnow().strftime("%Y-%m-%d")), items=[item1, item2], estimated_day_cost=30)
    itin = Itinerary(destination="Test City", start_date=day1.date, end_date=day1.date, days=[day1], total_estimated_cost_per_person=30)
    return itin


@pytest.fixture
def route_matrix():
    # Travel times in minutes between place ids
    return {
        "p1": {"p2": 20},  # 20 minutes travel
        "p2": {"p1": 20},
    }


@pytest.fixture
def weather_data():
    # Provide weather strings keyed by date
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return {
        today: {"weather_code": 95, "precipitation_probability_max": 90, "summary": "storm"}
    }


@pytest.fixture
def sample_constraints():
    return HardConstraints(
        origin="SF",
        destination="Test City",
        duration_days=1,
        travelers=2,
        budget_per_person=200,
        currency="USD",
        transport_mode="car",
    )
