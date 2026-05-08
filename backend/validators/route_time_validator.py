"""
Route time validator: verifies travel times between consecutive itinerary items.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

from backend.schemas.itinerary import Itinerary
from backend.schemas.validation import ValidationIssue, ValidationReport

logger = logging.getLogger(__name__)

# Buffer time defaults (in minutes)
BUFFER_TIMES = {
    "walking": 15,
    "public_transit": 15,
    "driving": 10,
    "rideshare": 10,
    "airport_transfer": 90,
    "train_station": 60,
}


class RouteTimeValidator:
    """Validates that travel times between items are feasible."""
    
    def __init__(self, route_matrix: Optional[Dict] = None, transport_mode: str = "mixed"):
        """
        Args:
            route_matrix: Dict of travel times {origin_id -> {dest_id -> minutes}}
            transport_mode: Primary transport mode (affects buffer times)
        """
        self.route_matrix = route_matrix or {}
        self.transport_mode = transport_mode
    
    def validate(self, itinerary: Itinerary) -> ValidationReport:
        """
        Check travel times between consecutive items within each day.
        
        Returns:
            ValidationReport with issues/warnings
        """
        if isinstance(itinerary, dict):
            itinerary = Itinerary(**itinerary)

        issues = []
        warnings = []
        
        for day_plan in itinerary.days:
            items = day_plan.items
            
            for i in range(len(items) - 1):
                current_item = items[i]
                next_item = items[i + 1]
                
                # Check transition time
                issue = self._check_transition_feasible(
                    current_item=current_item,
                    next_item=next_item,
                    day_num=day_plan.day,
                    route_matrix=self.route_matrix
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
    
    def _check_transition_feasible(
        self,
        current_item,
        next_item,
        day_num: int,
        route_matrix: Dict
    ) -> Optional[ValidationIssue]:
        """
        Verify that travel time + buffer fits between end_time and next start_time.
        
        Returns:
            ValidationIssue if transition is impossible, None if OK.
        """
        try:
            end_time = datetime.strptime(current_item.end_time, "%H:%M").time()
            start_time = datetime.strptime(next_item.start_time, "%H:%M").time()
        except ValueError:
            return None  # Skip if time parsing fails
        
        # Calculate available time (in minutes)
        end_dt = datetime.combine(datetime.today(), end_time)
        start_dt = datetime.combine(datetime.today(), start_time)
        
        # Handle day wrap (shouldn't happen within same day, but be safe)
        if start_dt < end_dt:
            start_dt = start_dt.replace(day=start_dt.day + 1)
        
        available_minutes = (start_dt - end_dt).total_seconds() / 60
        
        # Get travel time estimate
        travel_time = self._get_travel_time(
            current_item.place_id,
            next_item.place_id,
            route_matrix
        )
        
        if travel_time is None:
            # No route data; assume minimal buffer
            travel_time = 20  # Default assumption
        
        # Determine required buffer
        buffer_time = BUFFER_TIMES.get(self.transport_mode, 15)
        
        required_time = travel_time + buffer_time
        
        if available_minutes < required_time:
            return ValidationIssue(
                type="travel_time_conflict",
                severity="critical",
                day=day_num,
                message=f"Insufficient time to travel from {current_item.place_name} "
                        f"({current_item.end_time}) to {next_item.place_name} ({next_item.start_time}). "
                        f"Need {required_time}min but only have {available_minutes:.0f}min.",
                suggested_fix=f"Add {required_time - available_minutes:.0f}min to gap, "
                             f"or reorder activities.",
                evidence=f"Travel: {travel_time}min, Buffer: {buffer_time}min, Available: {available_minutes:.0f}min"
            )
        
        # Warn if tight
        if available_minutes < required_time + 10:
            warnings = ValidationReport(
                passed=True,
                warnings=[ValidationIssue(
                    type="travel_time_tight",
                    severity="warning",
                    day=day_num,
                    message=f"Tight schedule between {current_item.place_name} "
                            f"and {next_item.place_name}: only {available_minutes:.0f}min available."
                )]
            )
        
        return None
    
    def _get_travel_time(
        self,
        origin_id: str,
        dest_id: str,
        route_matrix: Dict
    ) -> Optional[int]:
        """
        Get travel time in minutes from route_matrix.
        
        Returns:
            Travel time in minutes, or None if not found.
        """
        if not route_matrix:
            return None
        
        if origin_id in route_matrix:
            if dest_id in route_matrix[origin_id]:
                return route_matrix[origin_id][dest_id]
        
        return None
    
    def _summarize(self, num_issues: int, num_warnings: int) -> str:
        """Generate summary text."""
        parts = []
        if num_issues > 0:
            parts.append(f"{num_issues} impossible travel segment(s)")
        if num_warnings > 0:
            parts.append(f"{num_warnings} tight transition(s)")
        
        if not parts:
            return "All travel times feasible with buffer."
        return f"Route time check: {', '.join(parts)}."
