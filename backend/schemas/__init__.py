"""
AetherTrip Pydantic schemas for type-safe data validation across all layers.
"""

from .constraints import HardConstraints, SoftPreferences, TripConstraints
from .places import SourceRef, PlaceCandidate
from .itinerary import ItineraryItem, DayPlan, Itinerary
from .validation import ValidationIssue, ValidationReport
from .scoring import FeasibilityScore
from .budget import BudgetCategory, BudgetBreakdown
from .trip import TripRequest, TripResponse

__all__ = [
    "HardConstraints",
    "SoftPreferences",
    "TripConstraints",
    "SourceRef",
    "PlaceCandidate",
    "ItineraryItem",
    "DayPlan",
    "Itinerary",
    "ValidationIssue",
    "ValidationReport",
    "FeasibilityScore",
    "BudgetCategory",
    "BudgetBreakdown",
    "TripRequest",
    "TripResponse",
]
