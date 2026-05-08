"""
Trip request/response schemas for API endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

from .constraints import TripConstraints
from .itinerary import Itinerary
from .budget import BudgetBreakdown
from .validation import ValidationReport
from .scoring import FeasibilityScore


class TripRequest(BaseModel):
    """POST request for trip planning."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_input": "Plan a 3-day LA trip from San Jose for 4 friends under $400 each, vegetarian, no car."
            }
        }
    )
    
    user_input: str = Field(
        ...,
        description="Free-form user request (e.g., 'Plan a 3-day LA trip from San Jose for 4 friends under $400 each')"
    )
    
class TripResponse(BaseModel):
    """Complete trip plan response."""
    
    trip_id: Optional[str] = Field(None, description="Unique trip ID for storage/retrieval")
    
    # Input processing
    user_input: str = Field(..., description="Original user request")
    parsed_request: Optional[dict] = Field(None, description="Parsed request details")
    constraints: Optional[TripConstraints] = Field(None, description="Extracted constraints")
    
    # Results
    itinerary: Optional[Itinerary] = Field(None, description="Generated itinerary")
    budget_report: Optional[BudgetBreakdown] = Field(None, description="Budget breakdown")
    validation_reports: List[ValidationReport] = Field(
        default_factory=list,
        description="Validation checks performed"
    )
    repair_history: List[dict] = Field(
        default_factory=list,
        description="History of repairs applied"
    )
    feasibility_score: Optional[FeasibilityScore] = Field(None, description="Feasibility score and breakdown")
    
    # Explanations
    why_this_trip_works: Optional[str] = Field(
        None,
        description="Human-friendly explanation of why the plan is solid"
    )
    
    # Status
    status: str = Field(
        default="pending",
        description="Status: 'pending', 'processing', 'completed', 'failed', 'needs_review'"
    )
    warnings: List[str] = Field(default_factory=list, description="High-level warnings for user")
    errors: List[str] = Field(default_factory=list, description="Error messages if generation failed")
    
    # Metadata
    created_at: Optional[str] = Field(None, description="ISO 8601 timestamp")
    completed_at: Optional[str] = Field(None, description="ISO 8601 timestamp when completed")
    processing_time_seconds: Optional[float] = Field(None, description="Time to generate plan")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "trip_id": "trip_abc123",
                "user_input": "Plan a 3-day LA trip from San Jose for 4 friends under $400 each, vegetarian, no car.",
                "constraints": {
                    "hard": {
                        "origin": "San Jose",
                        "destination": "Los Angeles",
                        "duration_days": 3,
                        "travelers": 4,
                        "budget_per_person": 400,
                        "currency": "USD",
                        "transport_mode": "no_car",
                        "diet": ["vegetarian"]
                    }
                },
                "itinerary": {
                    "destination": "Los Angeles",
                    "days": []
                },
                "budget_report": {
                    "total_per_person": 385,
                    "is_over_budget": False
                },
                "validation_reports": [
                    {
                        "passed": True,
                        "issues": [],
                        "warnings": []
                    }
                ],
                "feasibility_score": {
                    "overall_score": 82,
                    "grade": "B"
                },
                "why_this_trip_works": "All attractions open at scheduled times. Routes feasible. Under budget.",
                "status": "completed",
                "warnings": [],
                "errors": [],
                "created_at": "2026-05-07T10:00:00Z",
                "completed_at": "2026-05-07T10:15:00Z",
                "processing_time_seconds": 15.2
            }
        }
    )
