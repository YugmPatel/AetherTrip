from backend.validators.weather_validator import WeatherValidator
from backend.schemas.itinerary import Itinerary, DayPlan, ItineraryItem


def test_weather_risk_flags_outdoor(sample_places, weather_data):
    places_map = sample_places
    # Build itinerary with outdoor place p1
    item = ItineraryItem(day=1, start_time="09:00", end_time="10:00", place_id="p1", place_name="Open Attraction", category="attraction", description="", estimated_cost=0, travel_time_from_previous_minutes=0, source_confidence=0.95)
    day_key = list(weather_data.keys())[0]
    day = DayPlan(day=1, date=day_key, items=[item])
    itin = Itinerary(destination="X", start_date=day_key, end_date=day_key, days=[day], total_estimated_cost_per_person=0)

    validator = WeatherValidator(places_map, weather_data)
    report = validator.validate(itin)
    assert any(i.type == "weather_risk" for i in report.issues)
