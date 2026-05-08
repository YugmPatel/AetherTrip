"""
LangGraph state for AetherTrip workflow.
"""

from typing import List, Dict, Optional, Any, Annotated
import operator
from pydantic import BaseModel, Field, ConfigDict


def overwrite(left: Any, right: Any) -> Any:
    """Simple reducer that overwrites left with right."""
    return right


class TripState(BaseModel):
    """Complete trip planning state for LangGraph workflow."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Input
    user_input: str = Field(..., description="User's raw trip request")
    
    # Parsing
    parsed_request: Optional[Dict[str, Any]] = Field(
        None,
        description="Parsed user request (origin, destination, dates, interests)"
    )
    constraints: Optional[Dict[str, Any]] = Field(
        None,
        description="Extracted TripConstraints"
    )
    
    # Data Fetching
    place_candidates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of verified PlaceCandidate options"
    )
    
    weather_data: Annotated[Optional[Dict[str, Any]], overwrite] = Field(
        None,
        description="Weather data by date"
    )
    route_matrix: Annotated[Optional[Dict[str, Any]], overwrite] = Field(
        None,
        description="Travel time matrix {origin_id: {dest_id: minutes}}"
    )
    
    # Itinerary
    itinerary: Optional[Dict[str, Any]] = Field(
        None,
        description="Generated Itinerary object"
    )
    
    # Validation & Repair
    validation_reports: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of ValidationReport objects"
    )
    repair_attempts: int = Field(default=0, ge=0, description="Number of repairs applied")
    repair_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="History of repairs: [{issue_type, fix_applied, passed}]"
    )
    
    # Budget & Scoring
    budget_report: Optional[Dict[str, Any]] = Field(
        None,
        description="BudgetBreakdown object"
    )
    feasibility_score: Optional[Dict[str, Any]] = Field(
        None,
        description="FeasibilityScore object"
    )
    
    # Explanation
    final_explanation: Optional[str] = Field(
        None,
        description="Why this trip works (human-friendly text)"
    )
    
    # Errors
    errors: Annotated[List[str], operator.add] = Field(
        default_factory=list,
        description="Accumulated error messages"
    )

