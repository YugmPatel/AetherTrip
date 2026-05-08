"""
Budget Service: estimate and calculate budget-related costs.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BudgetService:
    """Provides budget estimation utilities."""
    
    # Estimation defaults
    DEFAULT_HOTEL_NIGHT = 150  # USD per night
    DEFAULT_MEAL = 50  # USD per day
    DEFAULT_ATTRACTION = 30  # USD per attraction
    DEFAULT_LOCAL_TRANSPORT_DAY = 20  # USD per day
    
    @staticmethod
    def estimate_base_costs(
        num_days: int,
        num_travelers: int,
        has_flights: bool = True,
        transport_mode: str = "mixed"
    ) -> Dict[str, float]:
        """
        Estimate base trip costs.
        
        Returns:
            Dict with cost categories
        """
        # Lodging (fewer nights than days)
        lodging = BudgetService.DEFAULT_HOTEL_NIGHT * (num_days - 1)
        
        # Flights (if applicable)
        flights = 300 if has_flights else 0
        
        # Food
        food = BudgetService.DEFAULT_MEAL * num_days
        
        # Local transport based on mode
        if transport_mode == "no_car":
            local_transport = 30 * num_days  # Transit pass
        elif transport_mode == "car":
            local_transport = 50 * num_days  # Rental
        else:
            local_transport = BudgetService.DEFAULT_LOCAL_TRANSPORT_DAY * num_days
        
        # Attractions (estimate)
        attractions = BudgetService.DEFAULT_ATTRACTION * 5  # 5 activities
        
        return {
            "lodging": lodging,
            "flights": flights,
            "food": food,
            "local_transport": local_transport,
            "attractions": attractions,
            "total_base": lodging + flights + food + local_transport + attractions,
        }
    
    @staticmethod
    def estimate_hidden_costs(base_total: float) -> Dict[str, float]:
        """
        Estimate hidden costs as percentage of base.
        
        Returns:
            Dict with hidden cost categories
        """
        return {
            "taxes_fees": base_total * 0.15,  # 15% of base
            "tips": base_total * 0.05,  # 5% of base (additional to food tips)
            "currency_fees": base_total * 0.02,  # 2% of base
            "emergency_buffer": base_total * 0.05,  # 5% of base
            "misc": base_total * 0.03,  # 3% miscellaneous
        }
    
    @staticmethod
    def calculate_per_person_cost(
        total_base: float,
        total_hidden: float,
        num_travelers: int
    ) -> Dict[str, float]:
        """Calculate per-person costs."""
        total = total_base + total_hidden
        return {
            "base_per_person": total_base / num_travelers,
            "hidden_per_person": total_hidden / num_travelers,
            "total_per_person": total / num_travelers,
            "total_for_group": total,
        }
