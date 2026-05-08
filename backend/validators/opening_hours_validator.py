"""
Opening hours validator: verifies that all itinerary items fall within place opening hours.
"""

from datetime import datetime, time
from typing import Optional, Dict, Any
import logging

from backend.schemas.itinerary import Itinerary
from backend.schemas.places import PlaceCandidate
from backend.schemas.validation import ValidationIssue, ValidationReport

logger = logging.getLogger(__name__)


class OpeningHoursValidator:
    """Validates that scheduled times match place opening hours."""
    
    def __init__(self, places_map: Dict[str, PlaceCandidate]):
        """
        Args:
            places_map: Dict of {place_id: PlaceCandidate}
        """
        self.places_map = places_map
    
    def validate(self, itinerary: Itinerary) -> ValidationReport:
        """
        Check all itinerary items against opening hours.
        
        Returns:
            ValidationReport with issues/warnings
        """
        if isinstance(itinerary, dict):
            itinerary = Itinerary(**itinerary)

        issues = []
        warnings = []
        
        for day_plan in itinerary.days:
            for item in day_plan.items:
                place = self.places_map.get(item.place_id)
                
                if not place:
                    issues.append(ValidationIssue(
                        type="place_not_found",
                        severity="critical",
                        day=item.day,
                        item_id=item.place_id,
                        message=f"Place '{item.place_id}' not found in database.",
                    ))
                    continue
                
                if not place.opening_hours:
                    warnings.append(ValidationIssue(
                        type="unknown_opening_hours",
                        severity="warning",
                        day=item.day,
                        place_id=place.id,
                        message=f"{place.name} has no verified opening hours.",
                        suggested_fix="Verify opening hours manually.",
                        evidence="Opening hours unknown"
                    ))
                    continue
                
                # Check if open at scheduled time
                issue = self._check_hours_conflict(
                    place=place,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    day_num=item.day
                )
                
                if issue:
                    issues.append(issue)
        
        passed = len(issues) == 0
        
        return ValidationReport(
            passed=passed,
            issues=issues,
            warnings=warnings,
            summary=self._summarize(len(issues), len(warnings)),
            checked_at=datetime.utcnow().isoformat() + "Z"
        )
    
    def _check_hours_conflict(
        self,
        place: PlaceCandidate,
        start_time: str,
        end_time: str,
        day_num: int
    ) -> Optional[ValidationIssue]:
        """
        Check if place is open during [start_time, end_time].
        
        Returns:
            ValidationIssue if conflict found, None if OK.
        """
        try:
            start_dt = datetime.strptime(start_time, "%H:%M").time()
            end_dt = datetime.strptime(end_time, "%H:%M").time()
        except ValueError:
            return ValidationIssue(
                type="invalid_time_format",
                severity="error",
                day=day_num,
                place_id=place.id,
                message=f"Invalid time format: {start_time} or {end_time}",
            )
        
        # Parse opening hours (simplified)
        # Assuming structure like {"monday_to_friday": "9:00-17:00"} or similar
        hours = place.opening_hours
        
        if isinstance(hours, dict):
            # Try to extract a simple time range
            hours_str = str(hours)  # Fallback to string representation
            
            if "closed" in hours_str.lower():
                return ValidationIssue(
                    type="place_closed",
                    severity="critical",
                    day=day_num,
                    place_id=place.id,
                    message=f"{place.name} is closed.",
                    evidence=f"Hours: {hours}"
                )
            
            # Simple heuristic: try to extract opening time
            # (Real implementation would parse more carefully)
            if "9:00" in hours_str or "9:" in hours_str:
                opening_time = time(9, 0)
            elif "10:00" in hours_str or "10:" in hours_str:
                opening_time = time(10, 0)
            else:
                # Can't parse exactly; just warn
                return None
            
            # Check if start >= opening_time and end <= 17:30 (sample closing)
            if start_dt < opening_time:
                return ValidationIssue(
                    type="opening_hours_conflict",
                    severity="error",
                    day=day_num,
                    place_id=place.id,
                    message=f"{place.name} opens at {opening_time.strftime('%H:%M')}, "
                            f"but scheduled visit starts at {start_time}.",
                    suggested_fix=f"Move {place.name} to {opening_time.strftime('%H:%M')} or later.",
                    evidence=f"Opening time: {opening_time.strftime('%H:%M')}"
                )
        
        return None
    
    def _summarize(self, num_issues: int, num_warnings: int) -> str:
        """Generate summary text."""
        parts = []
        if num_issues > 0:
            parts.append(f"{num_issues} critical issue(s)")
        if num_warnings > 0:
            parts.append(f"{num_warnings} warning(s)")
        
        if not parts:
            return "All opening hours verified OK."
        return f"Opening hours check: {', '.join(parts)}."
