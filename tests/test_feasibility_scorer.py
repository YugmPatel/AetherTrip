from backend.scoring.feasibility_scorer import FeasibilityScorer, WEIGHTS
from backend.validators.verification_validator import VerificationValidator
from backend.schemas.itinerary import Itinerary, DayPlan, ItineraryItem
from backend.schemas.validation import ValidationReport, ValidationIssue
from backend.schemas.budget import BudgetBreakdown


def test_feasibility_score_components(sample_places):
    # Create itinerary referencing sample places
    item = ItineraryItem(day=1, start_time="09:00", end_time="10:00", place_id="p1", place_name="Open Attraction", category="attraction", description="", estimated_cost=10, travel_time_from_previous_minutes=0, source_confidence=0.95)
    day = DayPlan(day=1, date="2026-01-01", items=[item])
    itin = Itinerary(destination="X", start_date="2026-01-01", end_date="2026-01-01", days=[day], total_estimated_cost_per_person=10)

    # No validation issues => all components should be high
    verification = VerificationValidator(sample_places)
    scorer = FeasibilityScorer(verification)

    # Create a budget breakdown object (minimal)
    budget = BudgetBreakdown(
        currency="USD",
        travelers=1,
        lodging_base=0,
        intercity_transport=0,
        local_transport=0,
        food=0,
        attraction_tickets=10,
        lodging_taxes=0,
        lodging_fees=0,
        booking_fees=0,
        baggage_fees=0,
        seat_selection=0,
        parking=0,
        tolls=0,
        tips=0,
        currency_fees=0,
        emergency_buffer=0,
        total_base_cost=10,
        total_hidden_costs=0,
        total_per_person=10,
        total_for_group=10,
        user_budget_per_person=None,
        is_over_budget=False,
        budget_remaining_per_person=None,
        notes=""
    )

    score = scorer.score(itin, [], budget, repair_attempts=0)
    # Expect overall score to be 100 since everything is ideal
    assert score.overall_score == 100
    assert score.weights == WEIGHTS


def test_source_confidence_influence(sample_places):
    # Lower confidence should reduce source_confidence score
    # Create itinerary with p3 which has low confidence
    item = ItineraryItem(day=1, start_time="09:00", end_time="10:00", place_id="p3", place_name="Closed Museum", category="attraction", description="", estimated_cost=0, travel_time_from_previous_minutes=0, source_confidence=0.3)
    day = DayPlan(day=1, date="2026-01-01", items=[item])
    itin = Itinerary(destination="X", start_date="2026-01-01", end_date="2026-01-01", days=[day], total_estimated_cost_per_person=0)

    verification = VerificationValidator(sample_places)
    scorer = FeasibilityScorer(verification)

    budget = budget = BudgetBreakdown(
        currency="USD",
        travelers=1,
        lodging_base=0,
        intercity_transport=0,
        local_transport=0,
        food=0,
        attraction_tickets=0,
        lodging_taxes=0,
        lodging_fees=0,
        booking_fees=0,
        baggage_fees=0,
        seat_selection=0,
        parking=0,
        tolls=0,
        tips=0,
        currency_fees=0,
        emergency_buffer=0,
        total_base_cost=0,
        total_hidden_costs=0,
        total_per_person=0,
        total_for_group=0,
        user_budget_per_person=None,
        is_over_budget=False,
        budget_remaining_per_person=None,
        notes=""
    )

    score = scorer.score(itin, [], budget, repair_attempts=0)
    assert score.breakdown["source_confidence"] == 0


def test_empty_itinerary_score_is_not_high(sample_places):
    verification = VerificationValidator(sample_places)
    scorer = FeasibilityScorer(verification)
    itin = Itinerary(destination="X", days=[], total_estimated_cost_per_person=0)
    budget = BudgetBreakdown(is_over_budget=False)

    score = scorer.score(itin, [], budget, repair_attempts=0)

    assert score.overall_score <= 30
    assert "No itinerary items generated." in score.warnings
