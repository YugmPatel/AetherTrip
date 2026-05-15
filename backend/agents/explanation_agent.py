"""
ExplanationAgent: generates human-friendly explanations of the trip plan.
"""

import logging
from typing import Dict, Any

from backend.state import TripState

logger = logging.getLogger(__name__)


class ExplanationAgent:
    """Generates explanations for the final trip plan."""
    
    def run(self, state: TripState) -> Dict[str, Any]:
        """
        Generate explanation of why the trip works.
        
        Returns:
            Updated state with final_explanation
        """
        logger.info("ExplanationAgent: generating explanation")
        
        feasibility_score = state.feasibility_score or {}
        budget_report = state.budget_report or {}
        itinerary = state.itinerary or {}
        days = itinerary.get("days", []) if isinstance(itinerary, dict) else []
        item_count = sum(len(day.get("items", []) or []) for day in days)
        if not days or item_count == 0:
            return {
                "final_explanation": "Why this trip works is unavailable because the itinerary was not generated.",
                "why_this_trip_works": "Why this trip works is unavailable because the itinerary was not generated.",
            }
        
        # Build explanation from components
        parts = []
        
        # Score intro
        score = feasibility_score.get("overall_score", 0)
        grade = feasibility_score.get("grade", "?")
        parts.append(f"**Trip Feasibility: Grade {grade} ({score}/100)**")
        
        # Itinerary
        if itinerary:
            destination = itinerary.get("destination", "Destination")
            parts.append(f"\n**Itinerary:** {len(days)}-day trip to {destination}")
        
        # Budget
        if budget_report:
            total = budget_report.get("total_per_person", 0)
            over = budget_report.get("is_over_budget", False)
            if over:
                parts.append(f"\n⚠️ **Budget Status:** Over budget at ${total:.2f}/person")
            else:
                remaining = budget_report.get("budget_remaining_per_person", 0)
                if remaining is None:
                    parts.append(f"\n**Budget Status:** ${total:.2f}/person estimated; no budget limit provided")
                else:
                    parts.append(f"\n**Budget Status:** ${total:.2f}/person (${remaining:.2f} remaining)")
        
        # Warnings
        warnings = feasibility_score.get("warnings", [])
        if warnings:
            parts.append(f"\n**Notes:**")
            for warning in warnings[:3]:
                parts.append(f"- {warning}")
        
        # Explanation from score
        score_explanation = feasibility_score.get("explanation", "")
        if score_explanation:
            parts.append(f"\n{score_explanation}")
        
        final_explanation = "\n".join(parts)
        
        logger.info(f"Explanation generated ({len(final_explanation)} chars)")
        
        return {"final_explanation": final_explanation, "why_this_trip_works": final_explanation}
