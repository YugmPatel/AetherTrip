from backend.validators.budget_validator import BudgetValidator
from backend.schemas.itinerary import Itinerary, DayPlan, ItineraryItem
from backend.schemas.constraints import HardConstraints


def test_hidden_costs_and_over_budget():
    # Create a simple itinerary with base costs
    item = ItineraryItem(day=1, start_time="09:00", end_time="10:00", place_id="p1", place_name="A", category="attraction", description="", estimated_cost=100, travel_time_from_previous_minutes=0, source_confidence=0.9)
    day = DayPlan(day=1, date="2026-01-01", items=[item], estimated_day_cost=100)
    itin = Itinerary(destination="X", start_date="2026-01-01", end_date="2026-01-01", days=[day], total_estimated_cost_per_person=100)

    constraints = HardConstraints(origin="SF", destination="X", duration_days=1, travelers=1, budget_per_person=50, currency="USD", transport_mode="car")

    validator = BudgetValidator()
    breakdown, report = validator.validate(itin, constraints, num_days=1)

    # Hidden costs should be included
    assert breakdown.total_hidden_costs > 0
    # Should be over budget
    assert any(i.type == "over_budget" for i in report.issues)
