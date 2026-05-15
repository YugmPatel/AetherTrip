"""
Budget schema: detailed cost breakdown including hidden costs.
"""

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, Dict, List


class BudgetCategory(BaseModel):
    """Single budget category breakdown."""
    
    category: str = Field(
        ...,
        description="Category name (e.g., 'lodging_base', 'local_transport', 'tips')"
    )
    amount: float = Field(default=0, ge=0, description="Amount in specified currency")
    count: Optional[int] = Field(None, ge=1, description="Number of items (e.g., 2 nights)")
    per_unit: Optional[float] = Field(None, ge=0, description="Per-unit cost if applicable")
    notes: Optional[str] = Field(None, description="Notes on estimation")


class BudgetBreakdown(BaseModel):
    """Complete budget breakdown including base and hidden costs."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "currency": "USD",
                "travelers": 4,
                "lodging_base": 300,
                "intercity_transport": 400,
                "local_transport": 50,
                "food": 200,
                "attraction_tickets": 100,
                "lodging_taxes": 30,
                "lodging_fees": 20,
                "tips": 30,
                "currency_fees": 10,
                "emergency_buffer": 50,
                "total_base_cost": 1050,
                "total_hidden_costs": 140,
                "total_per_person": 1190,
                "total_for_group": 4760,
                "user_budget_per_person": 1200,
                "is_over_budget": False,
                "budget_remaining_per_person": 10,
                "notes": "Emergency buffer = 5% of total. Tips estimated at 15% of food."
            }
        }
    )
    
    currency: str = Field(default="USD", description="Currency code")
    travelers: int = Field(default=1, ge=1, description="Number of travelers")
    
    # Base costs
    lodging_base: float = Field(default=0, ge=0, description="Accommodation base price")
    intercity_transport: float = Field(default=0, ge=0, description="Flights, trains, etc.")
    local_transport: float = Field(default=0, ge=0, description="Transit within destination")
    food: float = Field(default=0, ge=0, description="Meals and dining")
    attraction_tickets: float = Field(default=0, ge=0, description="Entry fees, tickets")
    
    # Hidden costs
    lodging_taxes: float = Field(default=0, ge=0, description="Hotel taxes")
    lodging_fees: float = Field(default=0, ge=0, description="Resort/cleaning fees")
    booking_fees: float = Field(default=0, ge=0, description="Booking platform fees")
    baggage_fees: float = Field(default=0, ge=0, description="Luggage fees")
    seat_selection: float = Field(default=0, ge=0, description="Seat selection fees")
    parking: float = Field(default=0, ge=0, description="Parking charges")
    tolls: float = Field(default=0, ge=0, description="Road tolls")
    tips: float = Field(default=0, ge=0, description="Gratuities (~15% of food)")
    currency_fees: float = Field(default=0, ge=0, description="Foreign transaction fees")
    emergency_buffer: float = Field(default=0, ge=0, description="Emergency contingency (5%)")
    
    # Totals
    total_base_cost: float = Field(default=0, ge=0, description="Sum of base costs per person")
    total_hidden_costs: float = Field(default=0, ge=0, description="Sum of hidden costs per person")
    total_per_person: float = Field(default=0, ge=0, description="Total per person (base + hidden)")
    total_for_group: float = Field(default=0, ge=0, description="Total for all travelers")
    total_estimated_cost: float = Field(default=0, ge=0, description="Total estimated cost for the group")
    per_person_cost: float = Field(default=0, ge=0, description="Total estimated cost per person")
    budget_limit: Optional[float] = Field(None, ge=0, description="Budget limit per person, if supplied")
    base_costs: Dict[str, float] = Field(default_factory=dict, description="Base cost categories")
    hidden_costs: Dict[str, float] = Field(default_factory=dict, description="Hidden cost categories")
    
    # Validation
    user_budget_per_person: Optional[float] = Field(None, ge=0, description="User's stated budget per person")
    is_over_budget: bool = Field(default=False, description="True if total exceeds user budget")
    budget_remaining_per_person: Optional[float] = Field(None, description="Budget remaining per person")
    status: str = Field(default="unknown", description="Budget status: unknown, within_budget, or over_budget")
    warnings: List[str] = Field(default_factory=list, description="Budget warnings")
    
    breakdown_detail: Optional[Dict[str, BudgetCategory]] = Field(
        None,
        description="Detailed breakdown of each category (optional)"
    )
    
    notes: Optional[str] = Field(None, description="Budget notes and assumptions")

    @model_validator(mode="after")
    def normalize_budget_status(self) -> "BudgetBreakdown":
        """Keep budget status derived from the canonical is_over_budget field."""
        per_person = self.per_person_cost or self.total_per_person
        budget_limit = self.budget_limit if self.budget_limit is not None else self.user_budget_per_person

        if self.per_person_cost == 0 and per_person:
            self.per_person_cost = per_person
        if self.total_per_person == 0 and per_person:
            self.total_per_person = per_person
        if self.budget_limit is None and budget_limit is not None:
            self.budget_limit = budget_limit
        if self.user_budget_per_person is None and budget_limit is not None:
            self.user_budget_per_person = budget_limit

        if budget_limit is None:
            self.is_over_budget = bool(self.is_over_budget)
            self.status = "over_budget" if self.is_over_budget else "unknown"
            return self

        self.is_over_budget = bool(per_person > budget_limit)
        self.budget_remaining_per_person = budget_limit - per_person
        self.status = "over_budget" if self.is_over_budget else "within_budget"
        return self
    
