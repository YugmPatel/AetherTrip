"""
Feasibility score schema: weighted accuracy assessment of itinerary.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional
from datetime import datetime


class FeasibilityScore(BaseModel):
    """Feasibility score with weighted breakdown."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_score": 82,
                "grade": "B",
                "breakdown": {
                    "opening_hours": 100,
                    "travel_time": 85,
                    "budget": 90,
                    "source_confidence": 75,
                    "constraint_satisfaction": 100,
                    "weather_risk": 80,
                    "repair_stability": 100
                },
                "weights": {
                    "opening_hours": 0.25,
                    "travel_time": 0.20,
                    "budget": 0.20,
                    "source_confidence": 0.15,
                    "constraint_satisfaction": 0.10,
                    "weather_risk": 0.05,
                    "repair_stability": 0.05
                },
                "generated_at": "2026-05-07T10:15:30Z",
                "explanation": "This trip is well-planned. All attractions are verified open at scheduled times. Routes have sufficient travel buffers. Cost is within budget. One minor weather risk for Day 2 outdoor activities.",
                "warnings": [
                    "Some place sources have moderate confidence (0.7–0.8).",
                    "Day 2 has chance of rain; indoor backup recommended."
                ],
                "detailed_notes": {
                    "opening_hours": "All attractions verified open; no conflicts.",
                    "travel_time": "Most segments have 15+ min buffer; Day 3 segment tight but feasible.",
                    "budget": "Total $1190/person, $10 remaining vs $1200 budget.",
                    "source_confidence": "73% of places high confidence (>0.9); 27% moderate (0.7–0.9).",
                    "constraint_satisfaction": "All hard constraints met.",
                    "weather_risk": "Clear forecast Days 1–3 except Day 2 evening rain.",
                    "repair_stability": "No repairs needed on first iteration."
                }
            }
        }
    )
    
    overall_score: int = Field(ge=0, le=100, description="Overall feasibility score 0–100")
    grade: str = Field(description="Letter grade: A (90–100), B (80–89), C (70–79), D (60–69), F (<60)")
    
    breakdown: Dict[str, int] = Field(
        ...,
        description="Component scores (e.g., {'opening_hours': 100, 'travel_time': 85, ...})"
    )
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "opening_hours": 0.25,
            "travel_time": 0.20,
            "budget": 0.20,
            "source_confidence": 0.15,
            "constraint_satisfaction": 0.10,
            "weather_risk": 0.05,
            "repair_stability": 0.05,
        },
        description="Weights used for scoring"
    )
    
    generated_at: str = Field(..., description="ISO 8601 timestamp")
    
    explanation: str = Field(..., description="Human-readable summary of score")
    warnings: List[str] = Field(default_factory=list, description="Key warnings affecting score")
    
    detailed_notes: Optional[Dict[str, str]] = Field(
        None,
        description="Detailed notes per component"
    )
    
