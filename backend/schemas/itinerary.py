"""
Itinerary schema: day-by-day activity plans with timing and cost.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List


class ItineraryItem(BaseModel):
    """Single activity/visit in an itinerary."""
    
    day: int = Field(..., ge=1, description="Day number (1-indexed)")
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")
    
    place_id: str = Field(..., description="Reference to verified PlaceCandidate.id")
    place_name: str = Field(..., description="Place name for display")
    category: str = Field(..., description="Place category (e.g., 'restaurant', 'attraction')")
    
    description: str = Field(..., description="Activity description (e.g., 'Lunch at...')")
    estimated_cost: float = Field(default=0, ge=0, description="Estimated cost for this activity")
    
    travel_time_from_previous_minutes: Optional[int] = Field(
        None,
        ge=0,
        description="Travel time from previous location in minutes"
    )
    source_confidence: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Confidence in place data (inherited from PlaceCandidate)"
    )
    
    notes: Optional[str] = Field(None, description="Additional notes or tips for this activity")


class DayPlan(BaseModel):
    """Plan for a single day of travel."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "day": 1,
                "date": "2026-06-15",
                "items": [
                    {
                        "day": 1,
                        "start_time": "09:00",
                        "end_time": "11:30",
                        "place_id": "gp_getty",
                        "place_name": "The Getty Museum",
                        "category": "attraction",
                        "description": "Explore the art museum",
                        "estimated_cost": 15,
                        "travel_time_from_previous_minutes": 30,
                        "source_confidence": 0.95
                    }
                ],
                "estimated_day_cost": 45,
                "estimated_walking_miles": 1.5,
                "weather_summary": "Sunny, 72°F"
            }
        }
    )
    
    day: int = Field(..., ge=1, description="Day number (1-indexed)")
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format (if known)")
    
    items: List[ItineraryItem] = Field(
        default_factory=list,
        description="Ordered list of activities for the day"
    )
    estimated_day_cost: float = Field(default=0, ge=0, description="Total cost for day activities")
    estimated_walking_miles: Optional[float] = Field(None, ge=0, description="Total walking distance for the day")
    
    weather_summary: Optional[str] = Field(None, description="Expected weather (e.g., 'Sunny, 72°F')")
    
class Itinerary(BaseModel):
    """Complete travel itinerary across multiple days."""
    
    destination: str = Field(..., description="Destination city/region")
    start_date: Optional[str] = Field(None, description="Trip start date YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="Trip end date YYYY-MM-DD")
    
    days: List[DayPlan] = Field(
        default_factory=list,
        description="List of day plans in order"
    )
    
    total_estimated_cost_per_person: float = Field(
        default=0,
        ge=0,
        description="Total estimated cost per person (activities only, not hidden costs)"
    )
    
    total_estimated_travel_time_hours: Optional[float] = Field(
        None,
        ge=0,
        description="Total travel time across all days"
    )
    
    notes: Optional[str] = Field(None, description="Overall itinerary notes or summary")
