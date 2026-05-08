from backend.validators.route_time_validator import RouteTimeValidator
from backend.schemas.itinerary import Itinerary, DayPlan, ItineraryItem


def test_impossible_travel_gap(route_matrix):
    # Create two items with only 5 minutes gap but travel_time 20
    item1 = ItineraryItem(day=1, start_time="09:00", end_time="09:55", place_id="p1", place_name="A", category="attraction", description="", estimated_cost=0, travel_time_from_previous_minutes=0, source_confidence=0.9)
    item2 = ItineraryItem(day=1, start_time="10:00", end_time="11:00", place_id="p2", place_name="B", category="attraction", description="", estimated_cost=0, travel_time_from_previous_minutes=20, source_confidence=0.8)
    day = DayPlan(day=1, date="2026-01-01", items=[item1, item2])
    itin = Itinerary(destination="X", start_date="2026-01-01", end_date="2026-01-01", days=[day], total_estimated_cost_per_person=0)

    validator = RouteTimeValidator(route_matrix=route_matrix, transport_mode="walking")
    report = validator.validate(itin)
    assert any(i.type == "travel_time_conflict" for i in report.issues)
