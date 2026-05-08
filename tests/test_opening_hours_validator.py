from backend.validators.opening_hours_validator import OpeningHoursValidator
from backend.schemas.itinerary import Itinerary, DayPlan, ItineraryItem


def test_unknown_opening_hours_warns(sample_places, simple_itinerary):
    places_map = sample_places
    # Use place p2 which has unknown opening_hours
    validator = OpeningHoursValidator(places_map)
    report = validator.validate(simple_itinerary)
    # Should produce a warning for unknown opening hours
    assert any(w.type == "unknown_opening_hours" or "unknown_opening_hours" in w.type for w in report.warnings)


def test_closed_place_creates_critical(sample_places):
    places_map = sample_places
    # Build itinerary item for closed museum p3
    item = ItineraryItem(
        day=1,
        start_time="10:00",
        end_time="11:00",
        place_id="p3",
        place_name="Closed Museum",
        category="attraction",
        description="Visit",
        estimated_cost=0,
        travel_time_from_previous_minutes=0,
        source_confidence=0.3,
    )
    day = DayPlan(day=1, date="2026-01-01", items=[item])
    itin = Itinerary(destination="X", start_date="2026-01-01", end_date="2026-01-01", days=[day], total_estimated_cost_per_person=0)
    validator = OpeningHoursValidator(places_map)
    report = validator.validate(itin)
    assert any(i.type == "place_closed" for i in report.issues)
