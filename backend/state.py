"""
LangGraph state for AetherTrip workflow.
"""

from typing import List, Dict, Optional, Any, Annotated
import operator
from pydantic import BaseModel, Field, ConfigDict


def overwrite(left: Any, right: Any) -> Any:
    """Simple reducer that overwrites left with right."""
    return right


def merge_dicts(left: Optional[Dict[str, Any]], right: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge dict state updates while keeping existing service summaries."""
    return {**(left or {}), **(right or {})}


class TripState(BaseModel):
    """Complete trip planning state for LangGraph workflow."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Input
    trip_id: Optional[str] = Field(None, description="Unique trip ID for request tracing")
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
    origin: Optional[str] = Field(None, description="Starting city/location")
    destination: Optional[str] = Field(None, description="Target destination")
    duration_days: Optional[int] = Field(None, description="Trip duration in days")
    travelers: Optional[int] = Field(None, description="Number of travelers")
    budget_per_person: Optional[float] = Field(None, description="Budget per person")
    budget_status: Optional[str] = Field(None, description="Budget status: specified or unknown")
    budget_style: Optional[str] = Field(None, description="Budget preference such as budget")
    dietary_preferences: List[str] = Field(
        default_factory=list,
        description="Dietary restrictions/preferences extracted from the request"
    )
    transport_mode: Optional[str] = Field(None, description="Primary transport mode")
    no_car: bool = Field(default=False, description="Whether the trip should avoid cars")
    weather_preference: Optional[str] = Field(None, description="Weather preference such as rain_safe")
    
    # Data Fetching
    destination_coordinates: Annotated[Optional[Dict[str, float]], overwrite] = Field(
        None,
        description="Geocoded destination coordinates: {latitude, longitude}"
    )
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
    service_status: Annotated[Dict[str, Any], merge_dicts] = Field(
        default_factory=dict,
        description="Non-sensitive status for external service calls"
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
    why_this_trip_works: Optional[str] = Field(
        None,
        description="Alias for final_explanation used by API/debug tooling"
    )
    
    # Errors
    warnings: Annotated[List[str], operator.add] = Field(
        default_factory=list,
        description="Accumulated non-fatal warning messages"
    )
    errors: Annotated[List[str], operator.add] = Field(
        default_factory=list,
        description="Accumulated error messages"
    )

