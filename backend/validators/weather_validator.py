"""
Weather validator: checks for weather risks to outdoor activities.
"""

from datetime import datetime
from typing import Optional, Dict
import logging

from backend.schemas.itinerary import Itinerary
from backend.schemas.places import PlaceCandidate
from backend.schemas.validation import ValidationIssue, ValidationReport

logger = logging.getLogger(__name__)

# Risky weather conditions
RISKY_CONDITIONS = ["rain", "storm", "snow", "extreme", "heat", "cold", "flood"]
OUTDOOR_CATEGORIES = ["attraction", "hiking", "tour", "outdoor", "beach", "park"]


class WeatherValidator:
    """Validates itinerary against weather risks."""
    
    def __init__(self, places_map: dict[str, PlaceCandidate], weather_data: Optional[Dict] = None):
        """
        Args:
            places_map: Dict of {place_id: PlaceCandidate}
            weather_data: Dict of {date: weather_summary}
        """
        self.places_map = places_map
        self.weather_data = weather_data or {}
    
    def validate(self, itinerary: Itinerary) -> ValidationReport:
        """
        Check for weather-related risks.
        
        Returns:
            ValidationReport
        """
        if isinstance(itinerary, dict):
            itinerary = Itinerary(**itinerary)

        issues = []
        warnings = []
        
        for day_plan in itinerary.days:
            weather = self.weather_data.get(day_plan.date, {})
            
            for item in day_plan.items:
                place = self.places_map.get(item.place_id)
                
                if not place:
                    continue
                
                # Check if outdoor activity with risky weather
                if self._is_outdoor_activity(place):
                    issue = self._check_weather_risk(
                        place=place,
                        weather=weather,
                        day_num=day_plan.day
                    )
                    if issue:
                        if issue.severity == "critical":
                            issues.append(issue)
                        else:
                            warnings.append(issue)
        
        passed = len(issues) == 0
        
        return ValidationReport(
            passed=passed,
            issues=issues,
            warnings=warnings,
            summary=self._summarize(len(issues), len(warnings)),
            checked_at=datetime.utcnow().isoformat() + "Z"
        )
    
    def _is_outdoor_activity(self, place: PlaceCandidate) -> bool:
        """Check if place is outdoor category."""
        category = place.category.lower()
        return any(cat in category for cat in OUTDOOR_CATEGORIES)
    
    def _check_weather_risk(
        self,
        place: PlaceCandidate,
        weather: Dict,
        day_num: int
    ) -> Optional[ValidationIssue]:
        """
        Check if weather conditions are risky for this outdoor activity.
        
        Returns:
            ValidationIssue if risk found, None if OK.
        """
        if not weather:
            return None  # No weather data
        
        weather_str = str(weather).lower()
        
        risky = [cond for cond in RISKY_CONDITIONS if cond in weather_str]
        
        if risky:
            severity = "critical" if any(c in ["extreme", "flood", "storm"] for c in risky) else "warning"
            
            return ValidationIssue(
                type="weather_risk",
                severity=severity,
                day=day_num,
                place_id=place.id,
                message=f"{place.name} is outdoor activity, but weather shows: {', '.join(risky)}.",
                suggested_fix=f"Add indoor backup activity or reschedule {place.name}.",
                evidence=f"Weather: {weather_str}"
            )
        
        return None
    
    def _summarize(self, num_issues: int, num_warnings: int) -> str:
        """Generate summary."""
        parts = []
        if num_issues > 0:
            parts.append(f"{num_issues} severe weather risk(s)")
        if num_warnings > 0:
            parts.append(f"{num_warnings} weather concern(s)")
        
        if not parts:
            return "Weather conditions acceptable."
        return f"Weather check: {', '.join(parts)}."
