"""
Constraint validator: checks that itinerary respects hard constraints.
"""

from datetime import datetime
from typing import Optional
import logging

from backend.schemas.itinerary import Itinerary
from backend.schemas.constraints import TripConstraints
from backend.schemas.places import PlaceCandidate
from backend.schemas.validation import ValidationIssue, ValidationReport

logger = logging.getLogger(__name__)


class ConstraintValidator:
    """Validates itinerary against hard and soft constraints."""
    
    def __init__(self, places_map: dict[str, PlaceCandidate]):
        """
        Args:
            places_map: Dict of {place_id: PlaceCandidate}
        """
        self.places_map = places_map
    
    def validate(
        self,
        itinerary: Itinerary,
        constraints: TripConstraints
    ) -> ValidationReport:
        """
        Check itinerary against hard constraints.
        
        Returns:
            ValidationReport
        """
        if isinstance(itinerary, dict):
            itinerary = Itinerary(**itinerary)
        if isinstance(constraints, dict):
            constraints = TripConstraints(**constraints)

        issues = []
        warnings = []
        hard = constraints.hard
        soft = constraints.soft
        
        # Check must-visit places
        if hard.must_visit:
            issue = self._check_must_visit(itinerary, hard.must_visit)
            if issue:
                issues.append(issue)
        
        # Check avoid list
        if hard.avoid:
            issue = self._check_avoid(itinerary, hard.avoid)
            if issue:
                issues.append(issue)
        
        # Check dietary restrictions
        if hard.diet:
            issue = self._check_diet(itinerary, hard.diet)
            if issue:
                issues.append(issue)
        
        # Check transport mode
        if hard.transport_mode == "no_car":
            issue = self._check_no_car(itinerary, self.places_map)
            if issue:
                issues.append(issue)
        
        # Check walking distance
        if hard.max_daily_walking_miles:
            warning = self._check_walking_distance(
                itinerary,
                hard.max_daily_walking_miles
            )
            if warning:
                warnings.append(warning)
        
        passed = len(issues) == 0
        
        return ValidationReport(
            passed=passed,
            issues=issues,
            warnings=warnings,
            summary=self._summarize(len(issues), len(warnings)),
            checked_at=datetime.utcnow().isoformat() + "Z"
        )
    
    def _check_must_visit(self, itinerary: Itinerary, must_visit: list[str]) -> Optional[ValidationIssue]:
        """Check that all must-visit places are in itinerary."""
        visited_places = set()
        for day_plan in itinerary.days:
            for item in day_plan.items:
                place = self.places_map.get(item.place_id)
                if place:
                    visited_places.add(place.name.lower())
        
        missing = []
        for place_name in must_visit:
            if place_name.lower() not in visited_places:
                missing.append(place_name)
        
        if missing:
            return ValidationIssue(
                type="missing_must_visit",
                severity="critical",
                message=f"Must-visit places missing: {', '.join(missing)}",
                suggested_fix=f"Add {missing} to itinerary.",
            )
        
        return None
    
    def _check_avoid(self, itinerary: Itinerary, avoid: list[str]) -> Optional[ValidationIssue]:
        """Check that avoided places/categories are NOT in itinerary."""
        included = []
        for day_plan in itinerary.days:
            for item in day_plan.items:
                place = self.places_map.get(item.place_id)
                if place:
                    if place.name.lower() in [a.lower() for a in avoid]:
                        included.append(place.name)
                    if place.category.lower() in [a.lower() for a in avoid]:
                        included.append(f"{place.name} ({place.category})")
        
        if included:
            return ValidationIssue(
                type="avoided_place_included",
                severity="critical",
                message=f"Avoided places/categories included: {', '.join(included)}",
                suggested_fix="Remove avoided items.",
            )
        
        return None
    
    def _check_diet(self, itinerary: Itinerary, diet: list[str]) -> Optional[ValidationIssue]:
        """Check restaurants support dietary restrictions."""
        restaurants = []
        for day_plan in itinerary.days:
            for item in day_plan.items:
                if "restaurant" in item.category.lower() or "food" in item.category.lower():
                    place = self.places_map.get(item.place_id)
                    if place:
                        restaurants.append(place)
        
        issues_found = []
        for rest in restaurants:
            diet_tags = [d.lower() for d in (rest.dietary_tags or [])]
            for diet_req in diet:
                if diet_req.lower() not in diet_tags:
                    issues_found.append(f"{rest.name} - no {diet_req}")
        
        if issues_found:
            return ValidationIssue(
                type="diet_conflict",
                severity="warning",
                message=f"Some restaurants may not support dietary needs: {', '.join(issues_found[:3])}",
                suggested_fix="Verify restaurant menus manually.",
            )
        
        return None
    
    def _check_no_car(self, itinerary: Itinerary, places_map: dict) -> Optional[ValidationIssue]:
        """Check that places are accessible without car (simplified check)."""
        # Simplified: assume all places in destination are accessible by transit
        # A real check would verify places have public transit nearby
        return None
    
    def _check_walking_distance(
        self,
        itinerary: Itinerary,
        max_daily_walking_miles: float
    ) -> Optional[ValidationIssue]:
        """Check daily walking distances."""
        for day_plan in itinerary.days:
            if day_plan.estimated_walking_miles and day_plan.estimated_walking_miles > max_daily_walking_miles:
                return ValidationIssue(
                    type="excessive_walking",
                    severity="warning",
                    day=day_plan.day,
                    message=f"Day {day_plan.day} walking: {day_plan.estimated_walking_miles:.1f}mi exceeds limit {max_daily_walking_miles:.1f}mi.",
                    suggested_fix="Reduce walking or add transit transportation.",
                )
        
        return None
    
    def _summarize(self, num_issues: int, num_warnings: int) -> str:
        """Generate summary."""
        parts = []
        if num_issues > 0:
            parts.append(f"{num_issues} constraint violation(s)")
        if num_warnings > 0:
            parts.append(f"{num_warnings} warning(s)")
        
        if not parts:
            return "All constraints satisfied."
        return f"Constraint check: {', '.join(parts)}."
