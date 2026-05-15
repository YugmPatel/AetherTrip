"""
Budget validator: checks itinerary cost against constraints and budget.
Includes hidden cost calculation.
"""

from datetime import datetime
from typing import Optional
import logging

from backend.schemas.itinerary import Itinerary
from backend.schemas.budget import BudgetBreakdown
from backend.schemas.constraints import HardConstraints
from backend.schemas.validation import ValidationIssue, ValidationReport

logger = logging.getLogger(__name__)

# Hidden cost percentages (of base costs)
HIDDEN_COST_RATES = {
    "lodging_taxes_percent": 0.10,  # 10% of lodging
    "booking_fees_percent": 0.03,  # 3% of total
    "tips_percent": 0.15,  # 15% of food
    "currency_fees_percent": 0.02,  # 2% of total
    "emergency_buffer_percent": 0.05,  # 5% of total
}


class BudgetValidator:
    """Validates budget constraints and calculates realistic costs including hidden fees."""
    
    def validate(
        self,
        itinerary: Itinerary,
        constraints: HardConstraints,
        num_days: Optional[int] = None
    ) -> tuple[BudgetBreakdown, ValidationReport]:
        """
        Calculate budget breakdown and validate against constraints.
        
        Returns:
            (BudgetBreakdown, ValidationReport)
        """
        if isinstance(itinerary, dict):
            itinerary = Itinerary(**itinerary)
        if isinstance(constraints, dict):
            constraints = HardConstraints(**constraints)

        # Calculate base costs from itinerary
        base_lodging = self._estimate_lodging(constraints, num_days or len(itinerary.days))
        base_intercity = self._estimate_intercity_transport(constraints)
        base_local_transport = self._estimate_local_transport(constraints, itinerary)
        base_food = self._estimate_food(constraints, num_days or len(itinerary.days))
        base_attractions = itinerary.total_estimated_cost_per_person or 0
        
        total_base = (
            base_lodging + base_intercity + base_local_transport +
            base_food + base_attractions
        )
        
        # Calculate hidden costs
        lodging_taxes = base_lodging * HIDDEN_COST_RATES["lodging_taxes_percent"]
        lodging_fees = base_lodging * 0.05  # 5% resort/cleaning fees (fixed estimate)
        booking_fees = total_base * HIDDEN_COST_RATES["booking_fees_percent"]
        tips = base_food * HIDDEN_COST_RATES["tips_percent"]
        currency_fees = total_base * HIDDEN_COST_RATES["currency_fees_percent"]
        emergency_buffer = total_base * HIDDEN_COST_RATES["emergency_buffer_percent"]
        
        # Fixed/conditional estimates
        baggage_fees = 50  # International baggage
        seat_selection = 20  # Seat selection fees
        parking = 0  # No-car mode
        tolls = 0  # Varies, no-car mode
        
        total_hidden = (
            lodging_taxes + lodging_fees + booking_fees + tips +
            currency_fees + emergency_buffer + baggage_fees + seat_selection
        )
        
        total_per_person = total_base + total_hidden
        
        # Check budget. Keep this explicitly boolean; Pydantic must never see None here.
        user_budget = constraints.budget_per_person
        has_budget_limit = user_budget is not None
        is_over_budget = bool(has_budget_limit and total_per_person > user_budget)
        budget_remaining = user_budget - total_per_person if has_budget_limit else None

        base_costs = {
            "lodging_base": base_lodging,
            "intercity_transport": base_intercity,
            "local_transport": base_local_transport,
            "food": base_food,
            "attraction_tickets": base_attractions,
        }
        hidden_costs = {
            "lodging_taxes": lodging_taxes,
            "lodging_fees": lodging_fees,
            "booking_fees": booking_fees,
            "baggage_fees": baggage_fees,
            "seat_selection": seat_selection,
            "parking": parking,
            "tolls": tolls,
            "tips": tips,
            "currency_fees": currency_fees,
            "emergency_buffer": emergency_buffer,
        }
        budget_warnings = []
        if not has_budget_limit:
            budget_warnings.append("Budget limit missing or cost estimate incomplete.")
        over_pct = ((total_per_person - user_budget) / user_budget) if has_budget_limit and user_budget else 0
        far_over_budget = bool(is_over_budget and over_pct > 0.25)
        if far_over_budget:
            budget_warnings.append("Trip is not feasible within the requested budget.")
        status = "unknown" if not has_budget_limit else "over_budget" if is_over_budget else "within_budget"
        
        # Create breakdown
        breakdown = BudgetBreakdown(
            currency=constraints.currency,
            travelers=constraints.travelers,
            lodging_base=base_lodging,
            intercity_transport=base_intercity,
            local_transport=base_local_transport,
            food=base_food,
            attraction_tickets=base_attractions,
            lodging_taxes=lodging_taxes,
            lodging_fees=lodging_fees,
            booking_fees=booking_fees,
            baggage_fees=baggage_fees,
            seat_selection=seat_selection,
            parking=parking,
            tolls=tolls,
            tips=tips,
            currency_fees=currency_fees,
            emergency_buffer=emergency_buffer,
            total_base_cost=total_base,
            total_hidden_costs=total_hidden,
            total_per_person=total_per_person,
            total_for_group=total_per_person * constraints.travelers,
            total_estimated_cost=total_per_person * constraints.travelers,
            per_person_cost=total_per_person,
            budget_limit=user_budget,
            base_costs=base_costs,
            hidden_costs=hidden_costs,
            user_budget_per_person=user_budget,
            is_over_budget=is_over_budget,
            budget_remaining_per_person=budget_remaining,
            status=status,
            warnings=budget_warnings,
            notes="Hidden costs include taxes, fees, tips, currency conversion, and 5% emergency buffer."
        )
        
        # Validate
        issues = []
        warnings = []
        
        if is_over_budget:
            overage = total_per_person - user_budget
            message = (
                f"Trip is not feasible within the requested budget. "
                f"Estimated cost ${total_per_person:.2f}/person exceeds budget ${user_budget:.2f}/person by ${overage:.2f}."
                if far_over_budget
                else f"Trip cost ${total_per_person:.2f}/person exceeds budget ${user_budget:.2f}/person by ${overage:.2f}."
            )
            issues.append(ValidationIssue(
                type="over_budget",
                severity="critical",
                message=message,
                suggested_fix="Reduce duration, increase budget, use cheaper lodging, or remove paid activities.",
            ))
        elif has_budget_limit and total_per_person > user_budget * 0.95:
            warnings.append(ValidationIssue(
                type="budget_tight",
                severity="warning",
                message=f"Only ${budget_remaining:.2f}/person remaining after estimated costs.",
                suggested_fix="Consider adding buffer or removing optional activities."
            ))
        elif not has_budget_limit:
            warnings.append(ValidationIssue(
                type="budget_unknown",
                severity="warning",
                message="Budget limit missing or cost estimate incomplete.",
                suggested_fix="Add a per-person budget to validate affordability."
            ))
        
        passed = len(issues) == 0
        
        validation_report = ValidationReport(
            passed=passed,
            issues=issues,
            warnings=warnings,
            summary=self._summarize(breakdown),
            checked_at=datetime.utcnow().isoformat() + "Z"
        )
        
        return breakdown, validation_report
    
    def _estimate_lodging(self, constraints: HardConstraints, num_days: int) -> float:
        """Estimate lodging cost. Fallback: $150/night (flexible)."""
        return 150 * (num_days - 1)  # Fewer nights than days
    
    def _estimate_intercity_transport(self, constraints: HardConstraints) -> float:
        """Estimate intercity transport. Fallback: $100 if origin != destination."""
        if not constraints.origin or not constraints.destination:
            return 0
        if constraints.origin.lower() != constraints.destination.lower():
            return 100
        return 0
    
    def _estimate_local_transport(self, constraints: HardConstraints, itinerary: Itinerary) -> float:
        """Estimate local transport based on transport mode."""
        num_days = len(itinerary.days)
        
        if constraints.transport_mode == "no_car":
            return 30 * num_days  # Public transit pass
        elif constraints.transport_mode == "car":
            return 50 * num_days  # Car rental / parking
        else:
            return 20 * num_days  # Mixed
    
    def _estimate_food(self, constraints: HardConstraints, num_days: int) -> float:
        """Estimate food costs. Default $50/day."""
        return 50 * num_days
    
    def _summarize(self, breakdown: BudgetBreakdown) -> str:
        """Generate summary."""
        if breakdown.status == "unknown":
            return "Budget status unknown: budget limit missing or cost estimate incomplete."
        if breakdown.is_over_budget:
            return f"OVER BUDGET: ${breakdown.total_per_person:.2f}/person vs ${breakdown.user_budget_per_person:.2f} limit."
        remaining = breakdown.budget_remaining_per_person
        remaining_text = f"${remaining:.2f}" if remaining is not None else "unknown"
        return f"Within budget: ${breakdown.total_per_person:.2f}/person. Remaining: {remaining_text}."
