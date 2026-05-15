from backend.validators.budget_validator import BudgetValidator
from backend.schemas.itinerary import Itinerary, DayPlan, ItineraryItem
from backend.schemas.constraints import HardConstraints
from backend.schemas.budget import BudgetBreakdown


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


def test_budget_is_over_budget_always_boolean():
    item = ItineraryItem(day=1, start_time="09:00", end_time="10:00", place_id="p1", place_name="A", category="attraction", description="", estimated_cost=25, travel_time_from_previous_minutes=0, source_confidence=0.9)
    day = DayPlan(day=1, date="2026-01-01", items=[item], estimated_day_cost=25)
    itin = Itinerary(destination="X", start_date="2026-01-01", end_date="2026-01-01", days=[day], total_estimated_cost_per_person=25)
    constraints = HardConstraints(origin="SF", destination="X", duration_days=1, travelers=2, budget_per_person=None, currency="USD", transport_mode="no_car")

    breakdown, report = BudgetValidator().validate(itin, constraints, num_days=1)

    assert isinstance(breakdown.is_over_budget, bool)
    assert breakdown.is_over_budget is False
    assert breakdown.status == "unknown"
    assert "Budget limit missing" in breakdown.warnings[0]
    assert any(w.type == "budget_unknown" for w in report.warnings)


def test_budget_report_no_none_booleans():
    test_budget_is_over_budget_always_boolean()


def test_budget_report_has_numeric_defaults():
    item = ItineraryItem(day=1, start_time="09:00", end_time="10:00", place_id="p1", place_name="A", category="attraction", description="", estimated_cost=0, travel_time_from_previous_minutes=0, source_confidence=0.9)
    day = DayPlan(day=1, date="2026-01-01", items=[item], estimated_day_cost=0)
    itin = Itinerary(destination="X", start_date="2026-01-01", end_date="2026-01-01", days=[day], total_estimated_cost_per_person=0)
    constraints = HardConstraints(origin="SF", destination="X", duration_days=1, travelers=2, budget_per_person=200, currency="USD", transport_mode="no_car")

    breakdown, _ = BudgetValidator().validate(itin, constraints, num_days=1)

    assert isinstance(breakdown.total_estimated_cost, (int, float))
    assert isinstance(breakdown.per_person_cost, (int, float))
    assert isinstance(breakdown.emergency_buffer, (int, float))
    assert isinstance(breakdown.base_costs, dict)
    assert isinstance(breakdown.hidden_costs, dict)


def test_budget_over_limit_not_within_budget():
    breakdown = BudgetBreakdown(
        per_person_cost=1119,
        total_per_person=1119,
        budget_limit=500,
        user_budget_per_person=500,
        is_over_budget=False,
        status="within_budget",
    )

    assert breakdown.is_over_budget is True
    assert breakdown.status == "over_budget"
    assert breakdown.budget_remaining_per_person == -619
