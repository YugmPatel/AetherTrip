"""
ConstraintExtractorAgent: converts parsed input to TripConstraints schema.
"""

import logging
from typing import Dict, Any

from backend.state import TripState
from backend.schemas.constraints import HardConstraints, SoftPreferences, TripConstraints
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ConstraintExtractorAgent:
    """Extracts structured constraints from parsed request."""
    
    def __init__(self):
        self.llm = LLMService()
    
    def run(self, state: TripState) -> Dict[str, Any]:
        """
        Convert parsed_request to TripConstraints schema.
        
        Returns:
            Updated state with constraints
        """
        if not state.parsed_request:
            return {"errors": ["No parsed request available"]}
        
        logger.info("ConstraintExtractorAgent: extracting constraints")
        
        try:
            parsed = state.parsed_request
            
            # Build hard constraints from parsed request
            hard = HardConstraints(
                origin=parsed.get("origin", "New York"),
                destination=parsed.get("destination", ["Unknown"])[0] if parsed.get("destination") else "Unknown",
                duration_days=self._extract_duration_days(parsed.get("dates", "")),
                travelers=parsed.get("travelers", 1),
                budget_per_person=parsed.get("budget_per_person"),
                currency=parsed.get("currency", "USD"),
                transport_mode=parsed.get("transport_mode", "mixed"),
                diet=parsed.get("diet", []),
                must_visit=parsed.get("must_visit", []),
                avoid=parsed.get("avoid", []),
            )
            
            # Build soft preferences
            soft = SoftPreferences(
                pace="balanced",
                interests=parsed.get("interests", []),
                trip_style=parsed.get("trip_style"),
                food_style=parsed.get("food_style"),
                hotel_style=parsed.get("hotel_style"),
            )
            
            constraints = TripConstraints(hard=hard, soft=soft)
            
            logger.info(f"Constraints extracted: {hard.destination}, {hard.duration_days} days, {hard.travelers} travelers")
            
            return {"constraints": constraints.model_dump()}
        
        except Exception as e:
            logger.error(f"Constraint extraction failed: {e}")
            return {"errors": [f"Constraint extraction failed: {e}"]}
    
    def _extract_duration_days(self, dates_str: str) -> int:
        """Extract number of days from duration string."""
        import re
        
        match = re.search(r"(\d+)\s*days?", dates_str, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Default
        return 3
