"""
Validation schema: issues found during validation checks.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal


class ValidationIssue(BaseModel):
    """A single validation problem found during checks."""
    
    type: str = Field(
        ...,
        description="Issue type (e.g., 'opening_hours_conflict', 'travel_time_impossible', 'over_budget')"
    )
    severity: Literal["info", "warning", "error", "critical"] = Field(
        default="warning",
        description="Severity level"
    )
    
    day: Optional[int] = Field(None, ge=1, description="Day number if applicable")
    item_id: Optional[str] = Field(None, description="Itinerary item ID if applicable")
    place_id: Optional[str] = Field(None, description="Place ID if applicable")
    
    message: str = Field(..., description="Human-readable issue description")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix or action")
    
    evidence: Optional[str] = Field(None, description="Supporting details (e.g., 'Place closes at 5:30 PM')")


class ValidationReport(BaseModel):
    """Result of validation check on an itinerary."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "passed": False,
                "issues": [
                    {
                        "type": "opening_hours_conflict",
                        "severity": "critical",
                        "day": 2,
                        "place_id": "gp_getty",
                        "message": "The Getty closes at 5:30 PM, but scheduled visit is 5:10 PM to 6:30 PM.",
                        "suggested_fix": "Move The Getty to morning slot.",
                        "evidence": "Getty hours: 9:30 AM – 5:30 PM"
                    }
                ],
                "warnings": [
                    {
                        "type": "low_confidence",
                        "severity": "warning",
                        "place_id": "gp_unknown_cafe",
                        "message": "This cafe has low verification (0.4 confidence).",
                        "suggested_fix": "Consider alternative nearby restaurants."
                    }
                ],
                "summary": "1 critical issue, 1 warning.",
                "checked_at": "2026-05-07T10:00:00Z"
            }
        }
    )
    
    passed: bool = Field(
        ...,
        description="True if validation passed completely, False if critical issues found"
    )
    issues: List[ValidationIssue] = Field(
        default_factory=list,
        description="List of error/critical issues"
    )
    warnings: List[ValidationIssue] = Field(
        default_factory=list,
        description="List of warnings and info messages"
    )
    
    summary: Optional[str] = Field(None, description="Text summary of validation results")
    
    checked_at: Optional[str] = Field(None, description="ISO 8601 timestamp")
    
    def total_critical_issues(self) -> int:
        """Count critical issues."""
        return len([i for i in self.issues if i.severity in ["error", "critical"]])
    
    def total_warnings(self) -> int:
        """Count warnings."""
        return len(self.warnings)
    
