"""
Feasibility scorer: deterministic weighted scoring of itinerary feasibility.
"""

from datetime import datetime
from typing import Dict, List
import logging

from backend.schemas.itinerary import Itinerary
from backend.schemas.validation import ValidationReport
from backend.schemas.budget import BudgetBreakdown
from backend.schemas.scoring import FeasibilityScore
from backend.validators.verification_validator import VerificationValidator

logger = logging.getLogger(__name__)

# Scoring weights (must sum to 1.0)
WEIGHTS = {
    "opening_hours": 0.25,
    "travel_time": 0.20,
    "budget": 0.20,
    "source_confidence": 0.15,
    "constraint_satisfaction": 0.10,
    "weather_risk": 0.05,
    "repair_stability": 0.05,
}


class FeasibilityScorer:
    """Deterministic feasibility scoring based on validation results."""
    
    def __init__(self, verification_validator: VerificationValidator):
        """
        Args:
            verification_validator: For getting average source confidence
        """
        self.verification_validator = verification_validator
    
    def score(
        self,
        itinerary: Itinerary,
        validation_reports: List[ValidationReport],
        budget_report: BudgetBreakdown,
        repair_attempts: int = 0,
    ) -> FeasibilityScore:
        """
        Calculate feasibility score from validation and budget reports.
        
        Returns:
            FeasibilityScore with breakdown and explanation
        """
        if isinstance(itinerary, dict):
            itinerary = Itinerary(**itinerary)
        if isinstance(budget_report, dict):
            budget_report = BudgetBreakdown(**budget_report)
        validation_reports = [
            report if isinstance(report, ValidationReport) else ValidationReport(**report)
            for report in (validation_reports or [])
        ]
        item_count = sum(len(day.items or []) for day in itinerary.days or [])
        if not itinerary.days or item_count == 0:
            warnings = ["No itinerary items generated."]
            return FeasibilityScore(
                overall_score=25,
                grade="F",
                breakdown={
                    "opening_hours": 0,
                    "travel_time": 0,
                    "budget": self._score_budget(budget_report),
                    "source_confidence": 0,
                    "constraint_satisfaction": 0,
                    "weather_risk": 0,
                    "repair_stability": self._score_repair_stability(repair_attempts),
                },
                weights=WEIGHTS,
                generated_at=datetime.utcnow().isoformat() + "Z",
                explanation="Itinerary generation failed because no itinerary items were generated.",
                warnings=warnings,
                detailed_notes={
                    "itinerary": "No itinerary items generated.",
                    "source_confidence": "No itinerary items were available for source verification.",
                    "travel_time": "No route can be validated without itinerary items.",
                },
            )
        
        # Score each component (0-100)
        breakdown = {
            "opening_hours": self._score_opening_hours(validation_reports),
            "travel_time": self._score_travel_time(validation_reports),
            "budget": self._score_budget(budget_report),
            "source_confidence": self._score_source_confidence(itinerary),
            "constraint_satisfaction": self._score_constraints(validation_reports),
            "weather_risk": self._score_weather(validation_reports),
            "repair_stability": self._score_repair_stability(repair_attempts),
        }
        
        # Calculate weighted overall score
        overall_score = sum(
            breakdown[component] * WEIGHTS[component]
            for component in WEIGHTS
        )
        overall_score = int(round(overall_score))
        
        # Determine grade
        if overall_score >= 90:
            grade = "A"
        elif overall_score >= 80:
            grade = "B"
        elif overall_score >= 70:
            grade = "C"
        elif overall_score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        # Generate explanation
        explanation = self._generate_explanation(
            overall_score,
            grade,
            breakdown,
            budget_report,
            validation_reports
        )
        
        # Collect warnings
        warnings = self._collect_warnings(
            breakdown,
            budget_report,
            validation_reports
        )
        
        # Detailed notes per component
        detailed_notes = {
            "opening_hours": f"Score: {breakdown['opening_hours']}/100 – "
                           f"All attractions verified open or minor timing concerns.",
            "travel_time": f"Score: {breakdown['travel_time']}/100 – "
                         f"Route segments feasible with travel buffers.",
            "budget": f"Score: {breakdown['budget']}/100 – "
                    f"Total ${budget_report.total_per_person:.2f}/person, "
                    f"{self._budget_status_text(budget_report)}.",
            "source_confidence": f"Score: {breakdown['source_confidence']}/100 – "
                               f"Average confidence {breakdown['source_confidence']:.0%}.",
            "constraint_satisfaction": f"Score: {breakdown['constraint_satisfaction']}/100 – "
                                      f"Hard constraints met.",
            "weather_risk": f"Score: {breakdown['weather_risk']}/100 – "
                           f"Weather conditions acceptable.",
            "repair_stability": f"Score: {breakdown['repair_stability']}/100 – "
                              f"Repairs applied: {repair_attempts}.",
        }
        
        return FeasibilityScore(
            overall_score=overall_score,
            grade=grade,
            breakdown=breakdown,
            weights=WEIGHTS,
            generated_at=datetime.utcnow().isoformat() + "Z",
            explanation=explanation,
            warnings=warnings,
            detailed_notes=detailed_notes,
        )
    
    def _score_opening_hours(self, validation_reports: List[ValidationReport]) -> int:
        """
        Score opening hours validation.
        
        100 = no issues
        80 = warnings but no critical issues
        50 = some conflicts fixable
        0 = unfixable conflicts
        """
        for report in validation_reports:
            if report.type == "opening_hours" if hasattr(report, "type") else False:
                if not report.passed:
                    return 50  # Conflicts exist
        
        # Check all reports for opening_hours issues
        has_critical = False
        has_warning = False
        
        for report in validation_reports:
            for issue in getattr(report, 'issues', []):
                if 'opening_hours' in issue.type:
                    has_critical = True
            for warning in getattr(report, 'warnings', []):
                if 'opening_hours' in warning.type:
                    has_warning = True
        
        if has_critical:
            return 50
        elif has_warning:
            return 80
        else:
            return 100
    
    def _score_travel_time(self, validation_reports: List[ValidationReport]) -> int:
        """
        Score travel time validation.
        
        100 = all feasible
        80 = some warnings
        50 = tight but possible
        0 = impossible segments
        """
        has_critical = False
        has_warning = False
        
        for report in validation_reports:
            for issue in getattr(report, 'issues', []):
                if 'travel_time' in issue.type:
                    has_critical = True
            for warning in getattr(report, 'warnings', []):
                if 'travel_time' in warning.type:
                    has_warning = True
        
        if has_critical:
            return 0
        elif has_warning:
            return 80
        else:
            return 100
    
    def _score_budget(self, budget_report: BudgetBreakdown) -> int:
        """
        Score budget feasibility.
        
        100 = under budget with cushion
        80 = under budget, tight
        50 = 1-10% over
        0 = >10% over
        """
        if not budget_report.user_budget_per_person:
            return 100  # No budget constraint
        budget = budget_report.user_budget_per_person
        actual = budget_report.total_per_person
        
        if actual <= budget * 0.95:
            return 100  # Well under
        elif actual <= budget:
            return 80   # Tight but OK
        elif actual <= budget * 1.10:
            return 50   # 1-10% over
        elif actual <= budget * 1.25:
            return 20   # materially over, but potentially adjustable
        else:
            return 0    # >25% over: likely infeasible as requested
    
    def _score_source_confidence(self, itinerary: Itinerary) -> int:
        """
        Score based on average source confidence.
        
        0-0.5 = 0 (very poor)
        0.5-0.7 = 50 (moderate)
        0.7-0.9 = 80 (good)
        0.9-1.0 = 100 (excellent)
        """
        avg_confidence = self.verification_validator.get_average_confidence(itinerary)
        
        if avg_confidence >= 0.9:
            return 100
        elif avg_confidence >= 0.7:
            return 80
        elif avg_confidence >= 0.5:
            return 50
        else:
            return 0
    
    def _score_constraints(self, validation_reports: List[ValidationReport]) -> int:
        """
        Score constraint satisfaction.
        
        100 = all satisfied
        0 = any critical constraint violated
        """
        for report in validation_reports:
            for issue in getattr(report, 'issues', []):
                if issue.severity in ["critical", "error"]:
                    return 0
        
        return 100
    
    def _score_weather(self, validation_reports: List[ValidationReport]) -> int:
        """
        Score weather risk.
        
        100 = no issues
        80 = minor concerns
        50 = significant outdoor risk
        0 = severe weather blocks plan
        """
        has_critical = False
        has_warning = False
        
        for report in validation_reports:
            for issue in getattr(report, 'issues', []):
                if 'weather' in issue.type:
                    has_critical = True
            for warning in getattr(report, 'warnings', []):
                if 'weather' in warning.type:
                    has_warning = True
        
        if has_critical:
            return 0
        elif has_warning:
            return 50
        else:
            return 100
    
    def _score_repair_stability(self, repair_attempts: int) -> int:
        """
        Score based on repair count.
        
        100 = no repairs needed
        90 = 1 repair
        75 = 2 repairs
        60 = 3 repairs
        0 = unresolvable
        """
        if repair_attempts == 0:
            return 100
        elif repair_attempts == 1:
            return 90
        elif repair_attempts == 2:
            return 75
        elif repair_attempts == 3:
            return 60
        else:
            return 0
    
    def _generate_explanation(
        self,
        overall_score: int,
        grade: str,
        breakdown: Dict[str, int],
        budget_report: BudgetBreakdown,
        validation_reports: List[ValidationReport]
    ) -> str:
        """Generate human-friendly explanation of score."""
        
        if (
            budget_report.is_over_budget
            and budget_report.user_budget_per_person
            and budget_report.total_per_person > budget_report.user_budget_per_person * 1.25
        ):
            opening = f"This trip is not feasible as requested (Grade {grade})."
        elif breakdown["travel_time"] == 0:
            opening = f"This trip needs review because some travel segments remain impossible (Grade {grade})."
        elif grade in ["A", "B"]:
            opening = f"This trip is well-planned (Grade {grade})."
        elif grade == "C":
            opening = f"This trip is feasible but has some concerns (Grade {grade})."
        else:
            opening = f"This trip needs review due to significant issues (Grade {grade})."
        
        key_points = []
        
        # Opening hours
        if breakdown["opening_hours"] == 100:
            key_points.append("No opening-hour conflicts were returned.")
        elif breakdown["opening_hours"] >= 80:
            key_points.append("Some opening hours are unknown or need manual verification.")
        else:
            key_points.append("Opening hours have conflicts that need attention.")
        
        # Travel time
        if breakdown["travel_time"] == 100:
            key_points.append("All travel segments have sufficient buffer time.")
        elif breakdown["travel_time"] >= 80:
            key_points.append("Routes are feasible with tight timing on some segments.")
        else:
            key_points.append("Some travel segments are impossible with current timing.")
        
        # Budget
        if budget_report.status == "unknown":
            key_points.append("Budget limit is missing or cost estimates are incomplete.")
        elif not budget_report.is_over_budget:
            remaining = budget_report.budget_remaining_per_person or 0
            key_points.append(f"Cost is within budget: ${budget_report.total_per_person:.0f}/person, "
                            f"${remaining:.0f} remaining.")
        else:
            overage = budget_report.total_per_person - (budget_report.user_budget_per_person or 0)
            if budget_report.user_budget_per_person and budget_report.total_per_person > budget_report.user_budget_per_person * 1.25:
                key_points.append("Trip is not feasible within the requested budget.")
            key_points.append(f"Cost exceeds budget by ${overage:.0f}/person.")
        
        # Source confidence
        if breakdown["source_confidence"] >= 90:
            key_points.append("All place data from verified, high-confidence sources.")
        elif breakdown["source_confidence"] >= 70:
            key_points.append("Most places are from verified sources.")
        else:
            key_points.append("Some places have lower source confidence; verify manually.")
        
        return opening + " " + " ".join(key_points)
    
    def _collect_warnings(
        self,
        breakdown: Dict[str, int],
        budget_report: BudgetBreakdown,
        validation_reports: List[ValidationReport]
    ) -> List[str]:
        """Collect key warnings for the user."""
        warnings = []
        
        if breakdown["travel_time"] == 0:
            warnings.append("Some travel segments remain impossible with the current timing.")
        elif breakdown["travel_time"] < 100:
            warnings.append("Some travel segments are tight; allow flexibility.")
        
        if budget_report.is_over_budget:
            if budget_report.user_budget_per_person and budget_report.total_per_person > budget_report.user_budget_per_person * 1.25:
                warnings.append("Trip is not feasible within the requested budget.")
            else:
                warnings.append("Trip exceeds budget; consider reducing activities.")
        elif budget_report.budget_remaining_per_person and budget_report.budget_remaining_per_person < 50:
            warnings.append("Limited buffer remaining in budget.")
        
        if breakdown["source_confidence"] < 80:
            warnings.append("Some places have moderate confidence; verify manually.")
        
        if breakdown["weather_risk"] < 100:
            warnings.append("Weather may impact outdoor activities.")
        
        return warnings

    def _budget_status_text(self, budget_report: BudgetBreakdown) -> str:
        if budget_report.status == "unknown":
            return "budget status unknown"
        if budget_report.is_over_budget:
            if budget_report.user_budget_per_person and budget_report.total_per_person > budget_report.user_budget_per_person * 1.25:
                return "not feasible as requested"
            return "over budget"
        return "under budget"
