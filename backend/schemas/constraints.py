"""
Trip constraints schema: hard constraints and soft preferences.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import date


class HardConstraints(BaseModel):
    """Non-negotiable trip requirements."""
    
    origin: str = Field(..., description="Starting city/location")
    destination: str = Field(..., description="Target destination")
    start_date: Optional[date] = Field(None, description="Trip start date (YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="Trip end date (YYYY-MM-DD)")
    duration_days: Optional[int] = Field(None, description="Trip duration in days")
    
    travelers: int = Field(default=1, ge=1, description="Number of travelers")
    budget_per_person: Optional[float] = Field(None, ge=0, description="Budget per person in specified currency")
    currency: str = Field(default="USD", description="Currency code")
    
    transport_mode: Literal["car", "public_transit", "walking", "mixed", "no_car"] = Field(
        default="mixed",
        description="Primary transport mode"
    )
    
    diet: List[str] = Field(default_factory=list, description="Dietary restrictions (e.g., ['vegetarian', 'gluten-free'])")
    must_visit: List[str] = Field(default_factory=list, description="Places/attractions that must be included")
    avoid: List[str] = Field(default_factory=list, description="Places/types to avoid")
    
    max_daily_walking_miles: Optional[float] = Field(None, ge=0, description="Max walking distance per day")
    safety_preference: Optional[str] = Field(None, description="Safety/safety-index preference")


class SoftPreferences(BaseModel):
    """Optional preferences that should be respected but don't break plan."""
    
    pace: Literal["relaxed", "balanced", "packed"] = Field(
        default="balanced",
        description="Trip pace: relaxed (few activities), balanced, or packed (many activities)"
    )
    interests: List[str] = Field(default_factory=list, description="Interest tags (e.g., ['hiking', 'food', 'culture'])")
    trip_style: Optional[str] = Field(None, description="Trip style (e.g., adventure, luxury, budget)")
    food_style: Optional[str] = Field(None, description="Food preference (e.g., street food, fine dining)")
    hotel_style: Optional[str] = Field(None, description="Accommodation preference (e.g., luxury, boutique, budget)")
    avoid_crowds: bool = Field(default=False, description="Prefer less touristy spots")
    prefer_outdoor: bool = Field(default=False, description="Prefer outdoor activities")


class TripConstraints(BaseModel):
    """Complete trip constraint specification."""
    
    hard: HardConstraints = Field(..., description="Hard constraints")
    soft: SoftPreferences = Field(default_factory=SoftPreferences, description="Soft preferences")
