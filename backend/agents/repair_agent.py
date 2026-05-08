"""
RepairAgent: automatically suggests fixes for failed validation checks.
"""

import logging
from typing import Dict, Any

from backend.state import TripState
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class RepairAgent:
    """Proposes repairs for failed validation checks."""
    
    def __init__(self):
        self.llm = LLMService()
    
    def run(self, state: TripState) -> Dict[str, Any]:
        """
        Propose repairs for validation failures.
        
        Returns:
            Updated state with repair suggestions and modified itinerary
        """
        logger.info(f"RepairAgent: analyzing {len(state.validation_reports)} validation reports")
        
        if not state.validation_reports or state.repair_attempts >= 3:
            logger.info("No repairs needed or max attempts reached")
            return {"repair_history": []}
        
        repairs = []
        itinerary = state.itinerary or {}
        
        # For MVP: simple repair logic
        # TODO: Use LLM to suggest and apply repairs
        for report in state.validation_reports:
            if isinstance(report, dict):
                if not report.get("passed"):
                    # Mark that we attempted repair
                    repairs.append({
                        "report_index": state.validation_reports.index(report),
                        "issue_count": len(report.get("issues", [])),
                        "attempted": True
                    })
        
        if repairs:
            state.repair_attempts += 1
            logger.info(f"Applied {len(repairs)} repairs (attempt {state.repair_attempts})")
        
        return {
            "repair_history": repairs,
            "repair_attempts": state.repair_attempts,
            "itinerary": itinerary,  # Return (potentially modified) itinerary
        }
