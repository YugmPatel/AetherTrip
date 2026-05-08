"""
Verification validator: checks data source confidence and quality.
"""

from datetime import datetime
from typing import Optional
import logging

from backend.schemas.itinerary import Itinerary
from backend.schemas.places import PlaceCandidate
from backend.schemas.validation import ValidationIssue, ValidationReport

logger = logging.getLogger(__name__)


class VerificationValidator:
    """Validates source confidence and data quality."""
    
    def __init__(self, places_map: dict[str, PlaceCandidate]):
        """
        Args:
            places_map: Dict of {place_id: PlaceCandidate}
        """
        self.places_map = places_map
    
    def validate(
        self,
        itinerary: Itinerary,
        confidence_threshold: float = 0.7
    ) -> ValidationReport:
        """
        Check that all places meet confidence thresholds.
        
        Returns:
            ValidationReport
        """
        if isinstance(itinerary, dict):
            itinerary = Itinerary(**itinerary)

        issues = []
        warnings = []
        
        low_confidence_places = []
        
        for day_plan in itinerary.days:
            for item in day_plan.items:
                place = self.places_map.get(item.place_id)
                
                if not place:
                    issues.append(ValidationIssue(
                        type="place_not_found",
                        severity="critical",
                        day=day_plan.day,
                        item_id=item.place_id,
                        message=f"Place '{item.place_id}' not in verified database.",
                    ))
                    continue
                
                if place.confidence < confidence_threshold:
                    low_confidence_places.append((place.name, place.confidence))
                    
                    if place.confidence < 0.5:
                        issues.append(ValidationIssue(
                            type="very_low_confidence",
                            severity="warning",
                            day=day_plan.day,
                            place_id=place.id,
                            message=f"{place.name} has very low confidence ({place.confidence:.0%}). Data may be unreliable.",
                            suggested_fix="Replace with higher-confidence alternative if available.",
                        ))
        
        # Generate summary
        if low_confidence_places:
            confidence_text = ", ".join([f"{n} ({c:.0%})" for n, c in low_confidence_places[:3]])
            if len(low_confidence_places) > 3:
                confidence_text += f"... and {len(low_confidence_places) - 3} more"
            
            warnings.append(ValidationIssue(
                type="low_confidence_data",
                severity="warning",
                message=f"Some places have low confidence: {confidence_text}",
                suggested_fix="Verify details manually or request high-confidence alternatives.",
            ))
        
        passed = len(issues) == 0
        
        return ValidationReport(
            passed=passed,
            issues=issues,
            warnings=warnings,
            summary=self._summarize(len(low_confidence_places)),
            checked_at=datetime.utcnow().isoformat() + "Z"
        )
    
    def get_average_confidence(self, itinerary: Itinerary) -> float:
        """Calculate average confidence across all places."""
        total = 0
        count = 0
        
        for day_plan in itinerary.days:
            for item in day_plan.items:
                place = self.places_map.get(item.place_id)
                if place:
                    total += place.confidence
                    count += 1
        
        return total / count if count > 0 else 0.0
    
    def _summarize(self, num_low_confidence: int) -> str:
        """Generate summary."""
        if num_low_confidence == 0:
            return "All places have verified sources."
        return f"{num_low_confidence} place(s) with low confidence."
